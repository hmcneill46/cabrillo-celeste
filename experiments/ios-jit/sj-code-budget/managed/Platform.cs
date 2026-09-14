using System.Collections;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.CompilerServices;
using System.Runtime.Loader;
using System.Threading;
using Celeste;
using Celeste.Mod;
using CelesteIOSFoundation;
using Monocle;
using MonoMod.RuntimeDetour;
using GameClass = Celeste.Celeste;

namespace CelesteJIT.Game;

public static class Platform
{
    private static readonly FieldInfo threadsField = typeof(RunThread).GetField("threads", BindingFlags.Static | BindingFlags.NonPublic | BindingFlags.Public)
        ?? throw new MissingFieldException("Celeste.RunThread.threads");
    private static readonly FieldInfo audioSystemField = typeof(Audio).GetField("system", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic)
        ?? throw new MissingFieldException("Celeste.Audio.system");
    private static readonly FieldInfo audioReadyField = typeof(Audio).GetField("ready", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic)
        ?? throw new MissingFieldException("Celeste.Audio.ready");
    private static Hook grabHook;
    private static int workers;
    private static bool audioReported;
    private static Type canaryType;
    private static Type helperProbeType;
    private static readonly HashSet<string> helperChecks = new();
    private static bool modExecutionReported;
    private static int modJumpsAtResume = -1;
    public static Exception Failure;
    private delegate bool GrabOriginal();
    private delegate bool GrabDetour(GrabOriginal orig);

    public static string GetContentRoot() => Entry.ContentRoot;
    public static string GetModRoot() => Entry.SaveRoot;
    public static string GetErrorLogPath() => Path.Combine(Entry.SaveRoot, "errorLog.txt");
    public static void PrepareContent() => GameClass.Instance.Content.RootDirectory = Entry.ContentRoot;
    public static int RunThreadActiveCount
    {
        get
        {
            var threads = (ICollection)threadsField.GetValue(null);
            if (threads == null) return 0;
            lock (threads) return threads.Count;
        }
    }

    public static void Initialize()
    {
        Environment.SetEnvironmentVariable("CJIT_EMBEDDED", "1");
        Environment.SetEnvironmentVariable("EVEREST_SAVEPATH", Entry.SaveRoot);
        Environment.SetEnvironmentVariable("EVEREST_TMPDIR", Path.Combine(Entry.SaveRoot, "Cache"));
        Directory.CreateDirectory(Path.Combine(Entry.SaveRoot, "Cache"));
        Directory.CreateDirectory(Path.Combine(Entry.SaveRoot, "Mods"));
        Directory.SetCurrentDirectory(Entry.SaveRoot);
        AppDomain.CurrentDomain.AssemblyResolve += ResolveGeneratedModReference;
        MonoTypeDiscovery.Install();
        CheckFloatBoundary();
        var mainThread = typeof(GameClass).GetField("_mainThreadId", BindingFlags.NonPublic | BindingFlags.Static)
            ?? throw new MissingFieldException("Celeste._mainThreadId");
        mainThread.SetValue(null, Thread.CurrentThread.ManagedThreadId);
        CallEverest("ParseArgs", new object[] { new[] { "--disable-splash" } });
        Everest.Events.Input.OnInitialize += TouchPort.Bind;
        grabHook = new Hook(typeof(Input).GetProperty(nameof(Input.GrabCheck)).GetMethod,
            (GrabDetour)(orig => TouchGrabPolicy.Resolve(TouchPort.Grab, TouchPort.Visible, TouchPort.ControllerConnected, orig())));
        Entry.Mark("everest_platform_ready", "Embedded lifecycle; private profile; shared touch policy through Everest input nodes; desktop updates/Discord disabled.");
    }

    private static object CallEverest(string name, object[] args = null)
    {
        var method = typeof(Everest).GetMethod(name, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static)
            ?? throw new MissingMethodException("Celeste.Mod.Everest", name);
        try { return method.Invoke(null, args); }
        catch (TargetInvocationException ex) { throw ex.InnerException ?? ex; }
    }

    private static Assembly ResolveGeneratedModReference(object sender, ResolveEventArgs args)
    {
        string requester = args.RequestingAssembly?.GetName().Name ?? "none";
        Entry.Mark("everest_assembly_resolution", "requester=" + requester + "; requested=" + args.Name);
        if (!requester.StartsWith("DMD", StringComparison.Ordinal)) return null;
        var matches = AppDomain.CurrentDomain.GetAssemblies().Where(a =>
            a.FullName == args.Name && AssemblyLoadContext.GetLoadContext(a) is EverestModuleAssemblyContext).ToArray();
        if (matches.Length != 1) return null;
        Entry.Mark("everest_generated_mod_reference", "Reused loaded assembly identity " + args.Name + "; context=" + AssemblyLoadContext.GetLoadContext(matches[0]).Name);
        return matches[0];
    }

    [MethodImpl(MethodImplOptions.NoInlining)]
    public static float FloatThird(float a, float b, float c) => c;

    private static void CheckFloatBoundary()
    {
        float Run(bool normalize)
        {
            var method = new DynamicMethod("CjitFloatBoundary" + normalize, typeof(float), new[] { typeof(float) }, typeof(Platform));
            var il = method.GetILGenerator();
            il.Emit(OpCodes.Ldc_R4, 0f);
            il.Emit(OpCodes.Ldc_R4, 160f);
            il.Emit(OpCodes.Ldc_R4, 900f);
            il.Emit(OpCodes.Conv_R8);
            il.Emit(OpCodes.Ldarg_0);
            if (normalize) il.Emit(OpCodes.Conv_R8);
            il.Emit(OpCodes.Mul);
            if (normalize) il.Emit(OpCodes.Conv_R4);
            il.Emit(OpCodes.Call, typeof(Platform).GetMethod(nameof(FloatThird)));
            il.Emit(OpCodes.Ret);
            return ((Func<float, float>)method.CreateDelegate(typeof(Func<float, float>)))(1f / 60f);
        }
        float raw = Run(false), narrowed = Run(true);
        Entry.Mark("everest_float_boundary", "mixedWidth=" + raw + "; explicitSingle=" + narrowed + "; expected=" + (float)(900d * (1f / 60f)));
        if (Math.Abs(narrowed - 15f) > 0.00001f) throw new InvalidOperationException("Explicit float call boundary failed.");
    }

    public static void ApplyScreen()
    {
        Engine.ViewPadding = 0;
        if (Entry.IsPhone) Engine.SetFullscreen();
        else Engine.SetWindowed(960, 540);
    }

    public static void ReportErrorLog()
    {
        string path = GetErrorLogPath();
        string message = File.Exists(path) ? File.ReadAllText(path) : "No error log was written.";
        Failure = new InvalidOperationException(message);
        Entry.Mark("game_error_log", message);
    }

    public static IntPtr WorkerStart()
    {
        IntPtr pool = Entry.CJGameWorkerPoolPush();
        Interlocked.Increment(ref workers);
        Entry.Mark("game_worker_start", Thread.CurrentThread.Name ?? "unnamed");
        return pool;
    }

    public static void WorkerEnd(IntPtr pool)
    {
        try
        {
            Entry.Mark("game_worker_end", Thread.CurrentThread.Name ?? "unnamed");
            Interlocked.Decrement(ref workers);
        }
        finally { Entry.CJGameWorkerPoolPop(pool); }
    }

    public static int LuaCallback(int value) => value + 7;

    public static void CheckEverest()
    {
        if (Everest.Version != new Version(1, 6458, 0)) throw new InvalidOperationException("Unexpected Everest: " + Everest.VersionString);
        // This dedicated test profile uses the native launcher's instructions.
        // Everest's desktop first-run wizard/update screen needs no extra test.
        Celeste.Mod.Core.CoreModule.Settings.CurrentVersion = Everest.Version.ToString();
        Celeste.Mod.Core.CoreModule.Settings.LaunchWithoutIntro = true;
        Celeste.Mod.Core.CoreModule.Settings.AutoUpdateModsOnStartup = false;
        Entry.Mark("everest_boot_pass", Everest.VersionString);
        foreach (var mod in Everest.Modules)
            Entry.Mark("everest_module_registered", mod.Metadata.Name + " " + mod.Metadata.Version);
        var canary = Everest.Modules.Single(m => m.Metadata.Name == "CJITCodeCanary");
        if (!Everest.Modules.Any(m => m.Metadata.Name == "CJITTestMap")) throw new InvalidOperationException("Map ZIP module missing.");
        canaryType = canary.GetType();
        string context = (string)canaryType.GetField("ContextName").GetValue(null);
        if (context != "CJITCodeCanary") throw new InvalidOperationException("Code mod did not load in its real Everest assembly context: " + context);
        Entry.Mark("everest_mod_context_pass", "Normal ZIP loaded by Everest; context=" + context);
        var lua = Everest.LuaLoader.Context ?? throw new InvalidOperationException("Everest Lua context did not initialize.");
        lua.RegisterFunction("cjit_callback", null, typeof(Platform).GetMethod(nameof(LuaCallback)));
        var result = lua.DoString("return cjit_callback(35)", "cjit-managed-callback");
        if (result.Length != 1 || Convert.ToInt64(result[0]) != 42) throw new InvalidOperationException("Lua managed callback failed.");
        Entry.Mark("everest_lua_callback_pass", "Real Everest NLua context called managed C# and returned 42.");
        foreach (var expected in new[] { ("LuaCutscenes", "0.2.13"), ("MaxHelpingHand", "1.40.9"), ("CJITSJHelpers", "1.0.0") })
        {
            var mod = Everest.Modules.Single(m => m.Metadata.Name == expected.Item1);
            string loadedContext = AssemblyLoadContext.GetLoadContext(mod.GetType().Assembly)?.Name;
            if (mod.Metadata.Version != new Version(expected.Item2) || loadedContext != expected.Item1)
                throw new InvalidOperationException("Helper version/context mismatch: " + expected.Item1 + "; context=" + loadedContext);
            Entry.Mark("sj_helper_module_pass", mod.Metadata.Name + " " + mod.Metadata.Version + "; context=" + loadedContext);
            if (expected.Item1 == "CJITSJHelpers") helperProbeType = mod.GetType();
        }
    }

    public static void CheckMod(bool finishing)
    {
        int Count(string name) => (int)canaryType.GetField(name).GetValue(null);
        int hooks = Count("HookJumps"), il = Count("ILJumps"), entities = Count("EntitiesCreated"), rendered = Count("RenderFrames");
        bool executed = hooks > 0 && il == hooks && entities > 0 && rendered >= 120;
        if (executed && !modExecutionReported)
        {
            modExecutionReported = true;
            Entry.Mark("everest_mod_execution_pass", "Custom entity rendered; On and IL hooks executed; hooks=" + hooks + "; IL=" + il);
        }
        if (!finishing) return;
        if (modJumpsAtResume < 0 || hooks <= modJumpsAtResume)
            throw new InvalidOperationException("Code mod needs a hooked jump after resume.");
        Entry.Mark("everest_mod_resume_pass", "before=" + modJumpsAtResume + "; after=" + hooks + "; IL=" + il);
        int loaded = Count("LoadedJumps"), written = Count("WrittenJumps");
        var mod = Everest.Modules.Single(m => m.Metadata.Name == "CJITCodeCanary");
        byte[] bytes = mod.ReadSaveData(0);
        // Exercise the module's genuine YAML reader against its real sidecar.
        // Keep the live object and session counters intact for diagnostics.
        var live = mod._SaveData;
        mod.DeserializeSaveData(0, bytes);
        int readback = (int)mod._SaveData.GetType().GetProperty("Jumps").GetValue(mod._SaveData);
        mod._SaveData = live;
        bool saved = bytes != null && written > loaded && readback == written;
        Entry.Mark(saved ? "everest_mod_save_pass" : "everest_mod_save_fail", "prior=" + loaded + "; written=" + written + "; readback=" + readback + "; bytes=" + (bytes?.Length ?? 0));
        if (!executed || !saved) throw new InvalidOperationException("Code mod execution/save gate failed.");
    }

    public static bool CheckHelpers(bool finishing)
    {
        foreach (string property in new[] { "LuaWalkPassed", "LuaResumePassed", "PlatformPassed" })
            if ((bool)helperProbeType.GetProperty(property).GetValue(null) && helperChecks.Add(property))
                Entry.Mark("sj_helper_check_pass", property);
        if (!finishing) return false;
        string summary = (string)helperProbeType.GetMethod("Summary").Invoke(null, null);
        try
        {
            helperProbeType.GetMethod("Validate").Invoke(null, null);
            Entry.Mark("sj_helper_checks_pass", summary);
            return true;
        }
        catch (TargetInvocationException ex)
        {
            Entry.Mark("sj_helper_checks_incomplete", summary + "; " + (ex.InnerException ?? ex).Message);
            return false;
        }
    }

    public static void MarkModResume()
    {
        modJumpsAtResume = (int)canaryType.GetField("HookJumps").GetValue(null);
        helperProbeType.GetMethod("NotifyResume").Invoke(null, null);
        Entry.Mark("sj_helper_resume_signal", "Resume signalled; the retained Lua coroutine must independently continue and finish.");
    }

    public static void CheckAudio()
    {
        if (audioReported || !(bool)audioReadyField.GetValue(null)) return;
        var system = (FMOD.Studio.System)audioSystemField.GetValue(null);
        CheckFmod(system.getLowLevelSystem(out var core));
        CheckFmod(core.getVersion(out uint version));
        audioReported = true;
        Entry.Mark("game_audio_ready", "FMOD version=" + version.ToString("x") + "; ready=true");
    }

    public static void SuspendAudio(bool suspend)
    {
        if (!(bool)audioReadyField.GetValue(null)) return;
        var system = (FMOD.Studio.System)audioSystemField.GetValue(null);
        CheckFmod(system.getLowLevelSystem(out var core));
        CheckFmod(suspend ? core.mixerSuspend() : core.mixerResume());
        Entry.Mark("game_audio_lifecycle", suspend ? "suspended" : "resumed");
    }

    private static void CheckFmod(FMOD.RESULT result)
    {
        if (result != FMOD.RESULT.OK) throw new InvalidOperationException("FMOD: " + result);
    }

    public static void Shutdown()
    {
        CallEverest("Shutdown");
        Everest.Events.Input.OnInitialize -= TouchPort.Bind;
        grabHook?.Dispose();
        grabHook = null;
        AppDomain.CurrentDomain.AssemblyResolve -= ResolveGeneratedModReference;
        MonoTypeDiscovery.Dispose();
        int remaining = Volatile.Read(ref workers);
        Entry.Mark("everest_shutdown", "Tracked native worker pools remaining=" + remaining);
        if (remaining != 0) throw new InvalidOperationException("Everest workers did not stop: " + remaining);
    }
}

using System.Collections;
using System.IO;
using System.Reflection;
using System.Runtime.ExceptionServices;
using System.Security.Cryptography;
using Mono.Cecil;
using Mono.Cecil.Cil;
using MonoMod.RuntimeDetour;
using Celeste.Mod;

namespace CelesteJIT.Game;

// The original ZIP and Everest's relinked cache stay intact. Only the exact
// supported assembly receives a separate compatibility-cache copy, before load.
public static class GravityOptionalIntegration
{
    private const string ModuleName = "GravityHelper";
    private const string Integration = "Celeste.Mod.GravityHelper.ThirdParty.CelesteNet.CelesteNetModSupport";
    private const string Hooks = "Celeste.Mod.GravityHelper.ThirdParty.ThirdPartyHooks";
    private const string ModuleType = "Celeste.Mod.GravityHelper.GravityHelperModule";
    private const string OriginalZipHash = "d4a40744f4c155d655973754422643980321b6660027bc01b660a71b0d00649b";
    private const string Policy = "gravity-optional-v1";
    private static Hook hook;
    private delegate Assembly Original(EverestModuleAssemblyContext context, string path);
    private delegate Assembly Detour(Original original, EverestModuleAssemblyContext context, string path);

    internal static void Install()
    {
        // Explicit negative control for the desktop harness only.
        if (OperatingSystem.IsMacOS() && Environment.GetEnvironmentVariable("CJIT_TEST_ORIGINAL_GRAVITY") == "1") return;
        var method = typeof(EverestModuleAssemblyContext).GetMethod("LoadRelinkedAssembly", BindingFlags.Instance | BindingFlags.NonPublic)
            ?? throw new MissingMethodException("EverestModuleAssemblyContext.LoadRelinkedAssembly");
        hook = new Hook(method, (Detour)LoadRelinked);
        Entry.Mark("mono_gravity_compatibility_installed", Policy + "; preserve optional integration until its module is present.");
    }

    private static string Hash(byte[] bytes) => Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
    private static Assembly LoadRelinked(Original original, EverestModuleAssemblyContext context, string path)
    {
        if (context.ModuleMeta.Name != ModuleName) return original(context, path);
        if (context.ModuleMeta.Version != new Version(1, 2, 28) || string.IsNullOrEmpty(context.ModuleMeta.PathArchive)
            || Hash(File.ReadAllBytes(context.ModuleMeta.PathArchive)) != OriginalZipHash)
            throw new InvalidOperationException("Gravity compatibility requires the pinned original 1.2.28 ZIP.");
        byte[] input = File.ReadAllBytes(path);
        using var module = ModuleDefinition.ReadModule(new MemoryStream(input));
        if (module.Assembly.Name.Name != ModuleName) return original(context, path);
        int sites = Rewrite(module);
        using var output = new MemoryStream();
        module.Write(output);
        byte[] bytes = output.ToArray();
        string hash = Hash(bytes);
        string directory = Path.Combine(Entry.SaveRoot, "Cache", "CJITCompat", Policy, Hash(input));
        Directory.CreateDirectory(directory);
        string destination = Path.Combine(directory, "GravityHelper.dll");
        bool reused = File.Exists(destination) && Hash(File.ReadAllBytes(destination)) == hash;
        if (!reused)
        {
            string temporary = destination + "." + Guid.NewGuid().ToString("N") + ".tmp";
            try { File.WriteAllBytes(temporary, bytes); File.Move(temporary, destination, true); }
            finally { if (File.Exists(temporary)) File.Delete(temporary); }
        }
        Entry.Mark("mono_gravity_optional_relinked", "policy=" + Policy + "; sites=" + sites + "; reused=" + reused +
            "; originalZipSHA256=" + OriginalZipHash + "; inputSHA256=" + Hash(input) + "; outputSHA256=" + hash);
        // Original loader reads this same file into both retained Cecil metadata
        // and managed IL, so type discovery/DMD resolution still refer to one image.
        return original(context, destination);
    }

    public static int Rewrite(ModuleDefinition module)
    {
        if (module.Assembly.Name.Name != ModuleName) throw new InvalidOperationException("Wrong module for Gravity compatibility.");
        var owner = module.GetType(ModuleType) ?? throw new MissingMemberException(ModuleType);
        int sites = 0;
        foreach (string name in new[] { "Load", "Unload" })
        {
            var method = owner.Methods.Single(m => m.Name == name && m.Parameters.Count == 0);
            var token = method.Body.Instructions.Single(i => i.OpCode == OpCodes.Ldtoken && i.Operand is TypeReference t && t.FullName == Integration);
            var getType = token.Next;
            if (getType.OpCode != OpCodes.Call || getType.Operand is not MethodReference fromHandle || fromHandle.Name != "GetTypeFromHandle")
                throw new InvalidOperationException("Unexpected optional-type instruction pattern.");
            if (name == "Load" && getType.Next.OpCode != OpCodes.Ldc_I4_3)
                throw new InvalidOperationException("Unexpected forced hook level.");
            var invoke = name == "Load" ? getType.Next.Next : getType.Next;
            if (invoke.OpCode != OpCodes.Call || invoke.Operand is not MethodReference target || target.DeclaringType.FullName != Hooks
                || target.Name != (name == "Load" ? "ForceLoadType" : "ForceUnloadType"))
                throw new InvalidOperationException("Unexpected optional-integration call.");
            token.Operand = owner;
            method.Body.GetILProcessor().InsertAfter(getType, Instruction.Create(OpCodes.Callvirt,
                module.ImportReference(typeof(Type).GetProperty(nameof(Type.Assembly)).GetMethod)));
            invoke.Operand = module.ImportReference(typeof(GravityOptionalIntegration).GetMethod(name == "Load" ? nameof(LoadOptional) : nameof(UnloadOptional)));
            sites++;
        }
        if (sites != 2) throw new InvalidOperationException("Expected two optional-integration sites.");
        return sites;
    }

    // Kept separate so tests can prove that absent modules never resolve their
    // unavailable types, while present modules run the original operation/errors.
    public static bool InvokeIfPresent(bool present, Action operation)
    {
        if (!present) return false;
        operation();
        return true;
    }

    public static void LoadOptional(Assembly assembly, int hookLevel)
    {
        bool present = Everest.Modules.Any(m => m.Metadata.Name == "CelesteNet.Client");
        bool invoked = InvokeIfPresent(present, () =>
        {
            Type type = assembly.GetType(Integration, throwOnError: true);
            var method = assembly.GetType(Hooks, throwOnError: true).GetMethod("ForceLoadType");
            Invoke(method, new[] { (object)type, Enum.ToObject(method.GetParameters()[1].ParameterType, hookLevel) });
        });
        Entry.Mark(invoked ? "mono_gravity_optional_loaded" : "mono_gravity_optional_skipped",
            "CelesteNet.Client; operation=Load; modulePresent=" + present);
    }

    public static void UnloadOptional(Assembly assembly)
    {
        Type hooks = assembly.GetType(Hooks, throwOnError: true);
        var loaded = (IDictionary)hooks.GetField("ForceLoadedMods").GetValue(null);
        // Unload an existing integration even if its optional module has already
        // disappeared. Never resolve the unavailable type merely to discover none.
        object instance = loaded.Values.Cast<object>().SingleOrDefault(v => v.GetType().FullName == Integration);
        if (instance != null) Invoke(hooks.GetMethod("ForceUnloadType"), new[] { (object)instance.GetType() });
        Entry.Mark(instance != null ? "mono_gravity_optional_unloaded" : "mono_gravity_optional_skipped",
            "CelesteNet.Client; operation=Unload; existingInstance=" + (instance != null));
    }

    private static void Invoke(MethodInfo method, object[] args)
    {
        try { method.Invoke(null, args); }
        catch (TargetInvocationException ex) when (ex.InnerException != null)
        { ExceptionDispatchInfo.Capture(ex.InnerException).Throw(); throw; }
    }

    internal static void Dispose() { hook?.Dispose(); hook = null; }
}

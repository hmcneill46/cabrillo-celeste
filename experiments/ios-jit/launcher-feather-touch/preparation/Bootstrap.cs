using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Runtime.Loader;
using Cabrillo.Preparation;
using CelesteJIT.Content;

namespace CelesteJIT.Game;

// This assembly has no reference to Celeste, FNA, MMHOOK or the game adapter.
// Native code replaces these entry points after ContentLibrary succeeds, so
// gameplay retains the existing direct native-to-managed calls.
public static class Entry
{
    private static int Unprepared() => throw new InvalidOperationException("Import and prepare your game before starting.");
    public static int Start(int unused) => Unprepared();
    public static int Frame(int unused) => Unprepared();
    public static int Suspend(int unused) => Unprepared();
    public static int Resume(int unused) => Unprepared();
    public static int Stop(int unused) => Unprepared();
}

public static class ContentLibrary
{
    [DllImport("CJGraphicsNative", CallingConvention=CallingConvention.Cdecl)] private static extern int CJContentShouldCancel();
    [DllImport("CJGraphicsNative", CallingConvention=CallingConvention.Cdecl)] private static extern void CJContentProgress(long done, long total, int files);
    [DllImport("CJGraphicsNative", CallingConvention=CallingConvention.Cdecl)] private static extern long CJContentFreeBytes([MarshalAs(UnmanagedType.LPUTF8Str)] string path);
    [DllImport("CJGraphicsNative", CallingConvention=CallingConvention.Cdecl)] private static extern void CJGraphicsMark(string name, string message);
    [DllImport("CJGraphicsNative", CallingConvention=CallingConvention.Cdecl)] private static extern void CJGamePreparationStage(string detail);
    private const string ContentIdentity = "30a1c147d1a3ab0aa45762094e393ed7fd69951dd66e5af063447641e0699c46";
    private static string gameDirectory;
    private static Assembly Resolve(AssemblyLoadContext context, AssemblyName name)
    {
        if (name.Name is not ("Celeste" or "Celeste.Content" or "MMHOOK_Celeste")) return null;
        return context.LoadFromAssemblyPath(Path.Combine(gameDirectory, name.Name + ".dll"));
    }
    private static string Required(string variable)
    {
        string value = Environment.GetEnvironmentVariable(variable);
        if (string.IsNullOrEmpty(value) || !Path.IsPathRooted(value)) throw new InvalidDataException(variable + " was not configured.");
        return value;
    }
    public static int Prepare(int unused)
    {
        var watch = Stopwatch.StartNew(); string lastPhase = null; long lastReport = -2000; bool activating = false;
        try
        {
            string root = Required("CJIT_CONTENT_LIBRARY_ROOT"), codeRoot = Required("CJIT_GAME_CODE_ROOT");
            string archive = Environment.GetEnvironmentVariable("CJIT_CONTENT_ARCHIVE");
            var store = new ContentStore(Required("CJIT_CONTENT_MANIFEST"), ContentIdentity, root,
                (phase, done, total, files) => {
                    CJContentProgress(done, total, files);
                    if (phase != lastPhase || watch.ElapsedMilliseconds - lastReport >= 2000) {
                        CJGraphicsMark("content_import_progress", phase + "; bytes=" + done + "; total=" + total + "; files=" + files);
                        lastPhase = phase; lastReport = watch.ElapsedMilliseconds;
                    }
                }, () => CJContentShouldCancel() != 0, () => CJContentFreeBytes(root));
            var content = store.Prepare(archive);
            CJGraphicsMark("content_library_ready", "reused=" + content.Reused + "; verifiedBytes=" + content.VerifiedBytes + "; content=" + content.ContentRoot);
            double began = watch.Elapsed.TotalSeconds;
            var code = new GameCodeStore(codeRoot, AppContext.BaseDirectory, Required("CJIT_GAME_CODE_RECIPE"),
                text => { CJContentProgress(0, 0, 0); CJGamePreparationStage(text); },
                () => CJContentShouldCancel() != 0, () => CJContentFreeBytes(codeRoot)).Prepare(archive, content.ArchivePrefix);
            CJGraphicsMark("game_code_ready", "reused=" + code.Reused + "; seconds=" + (watch.Elapsed.TotalSeconds - began).ToString("F3", System.Globalization.CultureInfo.InvariantCulture) + "; recipe=" + code.Recipe + "; source=" + code.Source);
            Environment.SetEnvironmentVariable("CJIT_GAME_CONTENT_ROOT", content.ContentRoot);
            Environment.SetEnvironmentVariable("CJIT_PREPARED_GAME_DIRECTORY", code.Directory);
            activating = true; // A partial assembly load requires a fresh process, never another import attempt.
            gameDirectory = code.Directory;
            AssemblyLoadContext.Default.Resolving += Resolve;
            // Load only the fully committed generation. Merely resolving an adapter
            // type before this point can load Celeste through its field signatures.
            AssemblyLoadContext.Default.LoadFromAssemblyPath(Path.Combine(gameDirectory, "Celeste.Content.dll"));
            AssemblyLoadContext.Default.LoadFromAssemblyPath(Path.Combine(gameDirectory, "Celeste.dll"));
            AssemblyLoadContext.Default.LoadFromAssemblyPath(Path.Combine(gameDirectory, "MMHOOK_Celeste.dll"));
            // Release patch metadata and buffers before graphics/mod loading begins.
            if (!code.Reused) { GC.Collect(); GC.WaitForPendingFinalizers(); GC.Collect(); }
            return 1;
        }
        catch (OperationCanceledException) { CJGraphicsMark("content_import_cancelled", "Existing game files and saves preserved."); return 3; }
        catch (Exception e) when (!activating && (GameCodeStore.Recoverable(e) || e is NotSupportedException))
        { CJGraphicsMark("content_import_rejected", e.GetType().Name + ": " + e.Message); return 2; }
    }
}

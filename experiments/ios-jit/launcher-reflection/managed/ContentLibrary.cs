using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using CelesteJIT.Content;
namespace CelesteJIT.Game;

public static class ContentLibrary
{
    [DllImport("CJGraphicsNative", CallingConvention=CallingConvention.Cdecl)] private static extern int CJContentShouldCancel();
    [DllImport("CJGraphicsNative", CallingConvention=CallingConvention.Cdecl)] private static extern void CJContentProgress(long done, long total, int files);
    [DllImport("CJGraphicsNative", CallingConvention=CallingConvention.Cdecl)] private static extern long CJContentFreeBytes([MarshalAs(UnmanagedType.LPUTF8Str)] string path);
    private const string ExpectedIdentity = "30a1c147d1a3ab0aa45762094e393ed7fd69951dd66e5af063447641e0699c46";
    public static int Prepare(int unused)
    {
        string root = Environment.GetEnvironmentVariable("CJIT_CONTENT_LIBRARY_ROOT");
        var watch = Stopwatch.StartNew(); string lastPhase = null; long lastReport = -2000;
        try
        {
            if (string.IsNullOrEmpty(root) || !Path.IsPathRooted(root)) throw new InvalidOperationException("Content library root was not configured.");
            var store = new ContentStore(Environment.GetEnvironmentVariable("CJIT_CONTENT_MANIFEST"), ExpectedIdentity, root,
                (phase,done,total,files) => {
                    CJContentProgress(done,total,files);
                    if (phase != lastPhase || watch.ElapsedMilliseconds - lastReport >= 2000) {
                        Entry.Mark("content_import_progress", phase + "; bytes=" + done + "; total=" + total + "; files=" + files);
                        lastPhase = phase; lastReport = watch.ElapsedMilliseconds;
                    }
                }, () => CJContentShouldCancel() != 0, () => CJContentFreeBytes(root));
            var result = store.Prepare(Environment.GetEnvironmentVariable("CJIT_CONTENT_ARCHIVE"));
            Entry.ContentRoot = result.ContentRoot;
            Entry.Mark("content_library_ready", "reused=" + result.Reused + "; verifiedBytes=" + result.VerifiedBytes + "; seconds=" + watch.Elapsed.TotalSeconds.ToString("F3",System.Globalization.CultureInfo.InvariantCulture) + "; content=" + result.ContentRoot + "; prefix=" + result.ArchivePrefix);
            return 1;
        }
        catch (OperationCanceledException) { Entry.Mark("content_import_cancelled", "Existing game files and saves preserved."); return 3; }
        catch (Exception e) when (e is IOException || e is InvalidDataException || e is UnauthorizedAccessException || e is System.Text.Json.JsonException || e is NotSupportedException)
        { Entry.Mark("content_import_rejected", e.GetType().Name + ": " + e.Message); return 2; }
    }
}

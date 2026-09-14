// Private generated-game replacement: retain asynchronous vanilla loaders while
// giving their Objective-C objects a thread-local pool and persisting failures.
using System;
using System.Collections.Generic;
using System.Threading;
using Monocle;
using CelesteJIT.Game;
namespace Celeste;
public static class RunThread
{
    private static readonly HashSet<Thread> threads = new();
    public static int ActiveCount { get { lock (threads) return threads.Count; } }
    public static Exception Failure { get; private set; }
    public static void Start(Action method, string name, bool highPriority = false)
    {
        Thread thread = new(() => {
            IntPtr pool = Entry.CJGameWorkerPoolPush();
            Entry.Mark("game_worker_start", Thread.CurrentThread.Name ?? "unnamed");
            try { method(); }
            catch (Exception ex) {
                Failure = ex;
                Entry.Mark("game_worker_failed", ex.ToString());
                ErrorLog.Write(ex);
            }
            finally {
                Entry.Mark("game_worker_end", Thread.CurrentThread.Name ?? "unnamed");
                Entry.CJGameWorkerPoolPop(pool);
                lock (threads) threads.Remove(Thread.CurrentThread);
            }
        }) { Name = name, IsBackground = true };
        lock (threads) threads.Add(thread);
        try { thread.Start(); }
        catch { lock (threads) threads.Remove(thread); throw; }
    }
    // The host polls Stop across callbacks; never join a GPU loader on UIKit's
    // rendering thread or dispose its graphics device while it is still using it.
    public static void WaitAll() => throw new InvalidOperationException("Use the retained JIT host shutdown, which waits between native callbacks.");
}

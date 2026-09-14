using System;
using System.Threading;
namespace Celeste
{
    public partial class Celeste
    {
        public static void CJITSetMainThread() => _mainThreadId = Thread.CurrentThread.ManagedThreadId;
    }
    public static partial class Audio
    {
        private static volatile bool cjitSuspended;
        public static void CJITSuspend(bool value) { cjitSuspended = value; CJITApplySuspended(); }
        private static void CJITApplySuspended()
        {
            if (system == null || !ready) return;
            CheckFmod(system.getLowLevelSystem(out var core));
            CheckFmod(cjitSuspended ? core.mixerSuspend() : core.mixerResume());
            CelesteJIT.Game.Entry.Mark("game_audio_lifecycle", cjitSuspended ? "suspended" : "resumed");
        }
    }
}

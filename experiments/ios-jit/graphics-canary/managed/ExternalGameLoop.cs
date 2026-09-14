// Compiled into the private FNA copy; the upstream and AOT trees are untouched.
using System;
using System.Diagnostics;
using System.Runtime.InteropServices;

namespace Microsoft.Xna.Framework
{
    public partial class Game
    {
        private bool cjitExternalLoop;
        public int CJITCallbackFlushCount { get; private set; }
        [DllImport("__Internal", CallingConvention = CallingConvention.Cdecl)]
        private static extern int FNA3D_CJIT_EndCallback(IntPtr device);

        // The pinned Metal backend owns a nested autorelease pool from its first
        // GPU operation until Present. Close unfinished work before UIKit can
        // drain the enclosing callback pool (including skipped Draw/exception).
        public void CJITFinishGraphicsCallback()
        {
            var device = graphicsDeviceService?.GraphicsDevice;
            if (device == null || device.IsDisposed) return;
            int result = FNA3D_CJIT_EndCallback(device.GLDevice);
            if (result < 0) throw new InvalidOperationException("CJIT callback completion requires the paired Metal backend.");
            CJITCallbackFlushCount += result;
        }

        public void CJITBeginExternalLoop()
        {
            AssertNotDisposed();
            if (cjitExternalLoop || hasInitialized)
                throw new InvalidOperationException("The graphics probe starts one game per process.");
            try
            {
                DoInitialize();
                hasInitialized = true;
                BeginRun();
                BeforeLoop();
                gameTimer = Stopwatch.StartNew();
                cjitExternalLoop = true;
            }
            finally { CJITFinishGraphicsCallback(); }
        }

        public bool CJITTickExternalLoop()
        {
            if (!cjitExternalLoop) throw new InvalidOperationException("Game loop has not started.");
            if (!RunApplication) return false;
            try
            {
                RunOneFrame();
                return RunApplication;
            }
            finally { CJITFinishGraphicsCallback(); }
        }

        public void CJITEndExternalLoop()
        {
            if (!cjitExternalLoop) return;
            cjitExternalLoop = false;
            try { OnExiting(this, EventArgs.Empty); }
            finally
            {
                try { EndRun(); }
                finally
                {
                    try { AfterLoop(); }
                    finally { CJITFinishGraphicsCallback(); }
                }
            }
        }
    }
}

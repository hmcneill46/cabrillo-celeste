using System;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using Microsoft.Xna.Framework.Input.Touch;
using MonoMod.Core.Platforms.Systems;
using MonoMod.RuntimeDetour;

namespace CelesteJIT.Graphics;

public static class Entry
{
    [DllImport("CJGraphicsNative")] internal static extern void CJGraphicsMark(
        [MarshalAs(UnmanagedType.LPUTF8Str)] string name,
        [MarshalAs(UnmanagedType.LPUTF8Str)] string message);
    [DllImport("CJGraphicsNative")] internal static extern void CJGraphicsSetWindow(IntPtr window);
    [DllImport("CJGraphicsNative")] internal static extern void CJGraphicsSample(int frames, int contacts, int presses, int releases, int controllers, int resumes);
    private delegate int Orig(int value);
    private delegate int Alter(Orig original, int value);
    private static Hook? hook;
    private static ProbeGame? game;
    private static int state;
    private static int resumes;
    [MethodImpl(MethodImplOptions.NoInlining)] internal static int Tint(int value) => value * 2 + 7;
    [MethodImpl(MethodImplOptions.NoInlining)] private static int CallTint(int value) => Tint(value);
    internal static void Require(bool pass, string name)
    {
        CJGraphicsMark(pass ? "graphics_check_pass" : "graphics_check_fail", name);
        if (!pass) throw new InvalidOperationException(name);
    }

    public static int Start(int unused)
    {
        if (state != 0) throw new InvalidOperationException("Fresh launch required.");
        state = 1;
        CJGraphicsMark("graphics_managed_start", "One FNA game, native display-link frames, variable timestep.");
        // Install before any MonoMod platform is accessed. Serial mutation only.
        AppleJitSystem.Install();
        Require(CallTint(5) == 17, "render_hook_original");
        hook = new Hook(typeof(Entry).GetMethod(nameof(Tint), BindingFlags.Static | BindingFlags.NonPublic)!,
            (Alter)((orig, value) => orig(value) + 41));
        Require(CallTint(5) == 58, "render_hook_installed");
        game = new ProbeGame();
        game.CJITBeginExternalLoop();
        Require(game.CJITCallbackFlushCount == 1, "startup_metal_frame_closed_before_callback_return");
        CJGraphicsSetWindow(game.Window.Handle);
        state = 2;
        return 1;
    }

    public static int Frame(int unused)
    {
        if (state != 2 || game == null) return 0;
        int before = game.CJITCallbackFlushCount;
        bool running = game.CJITTickExternalLoop();
        if (game.SkippedLastUpdate)
            Require(game.CJITCallbackFlushCount == before + 1, "skipped_draw_metal_frame_closed_before_callback_return");
        return running ? 1 : 0;
    }

    public static int Suspend(int unused)
    {
        if (state != 2 || game == null) return 0;
        game.Sample();
        state = 3;
        CJGraphicsMark("graphics_managed_suspended", "No frames until native scene resumes.");
        return 1;
    }

    public static int Resume(int unused)
    {
        if (state != 3 || game == null) return 0;
        GC.Collect(); GC.WaitForPendingFinalizers(); GC.Collect();
        Require(CallTint(5) == 58, "render_hook_survives_resume_gc");
        game.ResetElapsedTime();
        resumes++;
        state = 2;
        CJGraphicsMark("graphics_managed_resumed", "Retained FNA game and hook; frame clock reset.");
        game.Sample();
        return 1;
    }

    public static int Stop(int unused)
    {
        bool checks = false;
        try
        {
            if (game != null)
            {
                game.Sample();
                checks = game.Frames >= 300 && game.Presses > 0 && game.Releases > 0 && resumes > 0 && game.FramesAfterResume >= 120 && game.SkippedDrawRecovered;
                game.CJITEndExternalLoop();
            }
        }
        finally
        {
            try { game?.Dispose(); }
            finally
            {
                game = null;
                hook?.Dispose(); hook = null;
                state = 4;
            }
        }
        Require(CallTint(5) == 17, "render_hook_removed_on_stop");
        CJGraphicsMark(checks ? "graphics_managed_checks_pass" : "graphics_managed_checks_incomplete",
            "Requires 300 frames, touch press/release, resume and 120 more frames; controller is optional.");
        return checks ? 1 : 2;
    }

    private sealed class ProbeGame : Game
    {
        private readonly GraphicsDeviceManager graphics;
        private SpriteBatch? batch;
        private Texture2D? pixel;
        private RenderTarget2D? canvas;
        private Vector2 target = new(160, 90);
        private Vector2 cursor = new(160, 90);
        private float time;
        public int Frames, Presses, Releases, FramesAfterResume;
        public bool SkippedLastUpdate, SkippedDrawRecovered;
        private int updates;
        private int contacts, controllerMask, lastSample, seenResumes;

        public ProbeGame()
        {
            IsFixedTimeStep = false;
            graphics = new GraphicsDeviceManager(this) {
                PreferredBackBufferWidth = 1280, PreferredBackBufferHeight = 720,
                IsFullScreen = !OperatingSystem.IsMacOS(), SynchronizeWithVerticalRetrace = true,
                SupportedOrientations = DisplayOrientation.LandscapeLeft | DisplayOrientation.LandscapeRight
            };
            Window.Title = "Celeste JIT graphics bridge";
        }

        protected override void LoadContent()
        {
            CJGraphicsMark("graphics_load_content", "Creating SpriteBatch, texture and a 320x180 render target.");
            batch = new SpriteBatch(GraphicsDevice);
            pixel = new Texture2D(GraphicsDevice, 1, 1);
            pixel.SetData(new[] { Color.White });
            canvas = new RenderTarget2D(GraphicsDevice, 320, 180, false, SurfaceFormat.Color, DepthFormat.None);
            GraphicsDevice.SetRenderTarget(canvas);
            Color sentinel = new Color(23, 91, 177, 255);
            GraphicsDevice.Clear(sentinel);
            GraphicsDevice.SetRenderTarget(null);
            var readback = new Color[320 * 180];
            canvas.GetData(readback);
            bool match = true;
            foreach (Color value in readback) match &= value == sentinel;
            Require(match, "metal_render_target_clear_and_gpu_readback");
            GraphicsDevice.DeviceResetting += (sender, args) => CJGraphicsMark("graphics_device_resetting", $"frames={Frames}");
            GraphicsDevice.DeviceReset += (sender, args) => CJGraphicsMark("graphics_device_reset", $"{GraphicsDevice.PresentationParameters.BackBufferWidth}x{GraphicsDevice.PresentationParameters.BackBufferHeight}");
            // Exercise pending backbuffer clear -> Reset before the startup
            // callback ends, while the old attachments must still be valid.
            GraphicsDevice.Clear(Color.Black);
            GraphicsDevice.Reset();
            canvas.GetData(readback);
            match = true;
            foreach (Color value in readback) match &= value == sentinel;
            Require(match, "pending_clear_reset_preserves_render_target");
            CJGraphicsMark("graphics_content_ready", $"Backbuffer {GraphicsDevice.PresentationParameters.BackBufferWidth}x{GraphicsDevice.PresentationParameters.BackBufferHeight}");
        }

        protected override void Update(GameTime gameTime)
        {
            updates++;
            SkippedLastUpdate = false;
            if (updates == 120 || updates == 121)
            {
                GraphicsDevice.SetRenderTarget(canvas);
                GraphicsDevice.Clear(new Color(23, 91, 177, 255));
                GraphicsDevice.SetRenderTarget(null);
                var readback = new Color[320 * 180];
                canvas!.GetData(readback);
                bool match = true;
                foreach (Color value in readback) match &= value == new Color(23, 91, 177, 255);
                Require(match, updates == 120 ? "gpu_work_before_suppressed_draw" : "gpu_work_after_suppressed_draw");
                if (updates == 120) { SuppressDraw(); SkippedLastUpdate = true; }
                else SkippedDrawRecovered = true;
            }
            time += (float)gameTime.ElapsedGameTime.TotalSeconds;
            TouchCollection touches = TouchPanel.GetState();
            contacts = touches.Count;
            foreach (TouchLocation touch in touches)
            {
                if (touch.State == TouchLocationState.Pressed) Presses++;
                if (touch.State == TouchLocationState.Released) Releases++;
                if (touch.State != TouchLocationState.Released && touch.State != TouchLocationState.Invalid)
                    target = new Vector2(touch.Position.X * 320 / Math.Max(1, TouchPanel.DisplayWidth), touch.Position.Y * 180 / Math.Max(1, TouchPanel.DisplayHeight));
            }
            controllerMask = 0;
            for (int i=0;i<4;i++)
            {
                GamePadState pad = GamePad.GetState((PlayerIndex)i);
                if (!pad.IsConnected) continue;
                controllerMask |= 1 << i;
                target += new Vector2(pad.ThumbSticks.Left.X, -pad.ThumbSticks.Left.Y) * (float)gameTime.ElapsedGameTime.TotalSeconds * 90;
            }
            target = Vector2.Clamp(target, new Vector2(6, 6), new Vector2(314, 174));
            cursor = Vector2.Lerp(cursor, target, Math.Min(1, (float)gameTime.ElapsedGameTime.TotalSeconds * 12));
            if (resumes != seenResumes) { seenResumes = resumes; FramesAfterResume = 0; }
            if (Frames - lastSample >= 300) { Sample(); lastSample = Frames; }
            base.Update(gameTime);
        }

        protected override void Draw(GameTime gameTime)
        {
            if (batch == null || pixel == null || canvas == null) throw new InvalidOperationException("Content missing");
            if (Tint(5) != 58) throw new InvalidOperationException("Live render hook lost");
            GraphicsDevice.SetRenderTarget(canvas);
            GraphicsDevice.Clear(new Color(12, 17, 31));
            batch.Begin(SpriteSortMode.Deferred, BlendState.AlphaBlend, SamplerState.PointClamp, DepthStencilState.None, RasterizerState.CullNone);
            for (int x=0; x<320; x+=16) batch.Draw(pixel, new Rectangle(x,0,1,180), new Color(26,35,54));
            for (int y=0; y<180; y+=16) batch.Draw(pixel, new Rectangle(0,y,320,1), new Color(26,35,54));
            for (int i=0;i<12;i++)
            {
                float angle = time + i * MathHelper.TwoPi / 12;
                var p = new Vector2(160 + MathF.Cos(angle)*65, 90 + MathF.Sin(angle)*45);
                batch.Draw(pixel, new Rectangle((int)p.X, (int)p.Y, 4, 4), new Color(100, 190, 235));
            }
            batch.Draw(pixel, new Rectangle((int)cursor.X-5,(int)cursor.Y-5,10,10), contacts>0 ? Color.White : new Color(245,Tint(5),100));
            batch.Draw(pixel, new Rectangle(4,174,Math.Min(312,Frames/3),2), new Color(82,210,150));
            batch.End();
            GraphicsDevice.SetRenderTarget(null);
            GraphicsDevice.Clear(Color.Black);
            int w = GraphicsDevice.PresentationParameters.BackBufferWidth, h = GraphicsDevice.PresentationParameters.BackBufferHeight;
            float scale = Math.Min(w/320f,h/180f);
            var destination = new Rectangle((int)((w-320*scale)/2),(int)((h-180*scale)/2),(int)(320*scale),(int)(180*scale));
            batch.Begin(SpriteSortMode.Deferred, BlendState.Opaque, SamplerState.PointClamp, DepthStencilState.None, RasterizerState.CullNone);
            batch.Draw(canvas,destination,Color.White); batch.End();
            Frames++;
            if (resumes>0) FramesAfterResume++;
            if (Frames==1) CJGraphicsMark("graphics_first_draw", "Real FNA draw commands submitted; native presentation follows.");
            base.Draw(gameTime);
        }

        public void Sample() => CJGraphicsSample(Frames,contacts,Presses,Releases,controllerMask,resumes);
        protected override void UnloadContent()
        {
            canvas?.Dispose(); pixel?.Dispose(); batch?.Dispose();
            canvas=null; pixel=null; batch=null;
            CJGraphicsMark("graphics_content_disposed", "FNA graphics resources released.");
            base.UnloadContent();
        }
    }
}

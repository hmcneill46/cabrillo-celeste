using System;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using MonoMod.Core.Platforms.Systems;
using MonoMod.RuntimeDetour;
using Celeste;
using Monocle;
using GameClass = Celeste.Celeste;
namespace CelesteJIT.Game;

public static class Entry
{
    [DllImport("CJGraphicsNative", CallingConvention=CallingConvention.Cdecl)]
    internal static extern void CJGraphicsMark([MarshalAs(UnmanagedType.LPUTF8Str)] string name, [MarshalAs(UnmanagedType.LPUTF8Str)] string message);
    [DllImport("CJGraphicsNative", CallingConvention=CallingConvention.Cdecl)] internal static extern void CJGraphicsSetWindow(IntPtr window);
    [DllImport("CJGraphicsNative", CallingConvention=CallingConvention.Cdecl)] internal static extern void CJGraphicsSample(int frames,int contacts,int presses,int releases,int controllers,int resumes);
    [DllImport("CJGraphicsNative", CallingConvention=CallingConvention.Cdecl)] public static extern IntPtr CJGameWorkerPoolPush();
    [DllImport("CJGraphicsNative", CallingConvention=CallingConvention.Cdecl)] public static extern void CJGameWorkerPoolPop(IntPtr pool);
    [DllImport("CJGraphicsNative", CallingConvention=CallingConvention.Cdecl)] internal static extern int CJGameTakeCommand();
    public static readonly string ContentRoot = RequiredRoot("CJIT_GAME_CONTENT_ROOT");
    public static readonly string SaveRoot = RequiredRoot("CJIT_GAME_SAVE_ROOT");
    public static readonly bool IsPhone = !OperatingSystem.IsMacOS();
    private static JitGame game;
    private static Hook jumpHook;
    private delegate void JumpOriginal(Player player, bool particles, bool playSfx);
    private delegate void JumpDetour(JumpOriginal orig, Player player, bool particles, bool playSfx);
    private static int state, resumes, jumpCalls, jumpsAtResume, framesAfterResume, levelFrames, playerMoves;
    private static bool titleSeen, savePassed, prologueRequested;
    private static Vector2? previousPlayer;
    private static string sceneName, uiName, roomName;
    private static string RequiredRoot(string name)
    {
        string root = Environment.GetEnvironmentVariable(name);
        if (string.IsNullOrEmpty(root) || !Path.IsPathRooted(root)) throw new InvalidOperationException("Missing private root: " + name);
        return root;
    }
    public static void Mark(string name,string message) => CJGraphicsMark(name,message);
    private static void Check(bool value,string name)
    {
        Mark(value ? "graphics_check_pass" : "graphics_check_fail",name);
        if (!value) throw new InvalidOperationException(name);
    }
    public static int Start(int unused)
    {
        if (state != 0) throw new InvalidOperationException("One game per process; relaunch for another run.");
        state = 1;
        Directory.CreateDirectory(SaveRoot);
        if (!Directory.Exists(ContentRoot)) throw new DirectoryNotFoundException(ContentRoot);
        Mark("game_paths", "content=" + ContentRoot + "; profile=" + SaveRoot);
        GameClass.CJITSetMainThread();
        Settings.Initialize();
        Mark("game_settings_loaded", "existing=" + Settings.Existed);
        Settings.Instance.Fullscreen = IsPhone;
        Settings.Instance.VSync = true;
        Settings.Instance.LaunchWithFMODLiveUpdate = false;
        AppleJitSystem.Install();
        jumpHook = new Hook(typeof(Player).GetMethod(nameof(Player.Jump),new[] {typeof(bool),typeof(bool)}),
            (JumpDetour)((orig,player,particles,sfx) => {
                orig(player,particles,sfx);
                jumpCalls++;
                if (jumpCalls <= 12 || jumpCalls % 20 == 0) Mark("game_jump_hook", "calls=" + jumpCalls + "; x=" + player.X + "; y=" + player.Y);
            }));
        Check(jumpHook.IsApplied,"celeste_player_jump_hook_installed");
        game = new JitGame();
        game.Content.RootDirectory = ContentRoot;
        Mark("game_begin_load", "Celeste 1.4.0.0; real content, asynchronous loaders and FMOD");
        game.CJITBeginExternalLoop();
        CJGraphicsSetWindow(game.Window.Handle);
        SaveSettings();
        state = 2;
        Mark("game_start_returned", "Native frame loop owns the retained Celeste instance.");
        return 1;
    }
    private static void SaveSettings()
    {
        byte[] bytes = UserIO.Serialize(Settings.Instance);
        Check(UserIO.Save<Settings>(Settings.Filename,bytes),"jit_xml_settings_write");
        var loaded = UserIO.Load<Settings>(Settings.Filename);
        Check(loaded != null && loaded.Language == Settings.Instance.Language,"jit_xml_settings_readback");
        Mark("game_save_pass","settings; bytes=" + bytes.Length);
    }
    private static void SaveGame()
    {
        SaveSettings();
        if (SaveData.Instance == null) return;
        SaveData.Instance.BeforeSave();
        string name = SaveData.GetFilename();
        byte[] data = UserIO.Serialize(SaveData.Instance);
        Check(UserIO.Save<SaveData>(name,data),"jit_xml_savedata_write");
        var loaded = UserIO.Load<SaveData>(name);
        Check(loaded != null && loaded.Name == SaveData.Instance.Name && loaded.TotalDeaths == SaveData.Instance.TotalDeaths,"jit_xml_savedata_readback");
        savePassed = true;
        Mark("game_save_pass","SaveData slot=" + name + "; bytes=" + data.Length + "; deaths=" + loaded.TotalDeaths);
    }
    public static int Frame(int unused)
    {
        if (state != 2 || game == null) return 0;
        if (RunThread.Failure != null) throw new InvalidOperationException("Celeste loader failed",RunThread.Failure);
        int command = CJGameTakeCommand();
        if (command == 1) prologueRequested = true;
        if (prologueRequested && titleSeen && Engine.Scene is Overworld && RunThread.ActiveCount == 0 && !UserIO.Saving)
        {
            // Dedicated canary profile; retain slot zero if already present.
            var data = UserIO.Load<SaveData>("0") ?? new SaveData { Name="Madeline" };
            SaveData.Start(data,0);
            Engine.Scene = new LevelLoader(new Session(new AreaKey(0)));
            prologueRequested = false;
            Mark("game_prologue_requested","Fresh Prologue session in canary profile slot 0; existing progress retained.");
        }
        bool running = game.CJITTickExternalLoop();
        if (resumes > 0) framesAfterResume++;
        string scene = Engine.Scene?.GetType().FullName ?? "none";
        if (scene != sceneName) { sceneName=scene; Mark("game_scene",scene); }
        if (Engine.Scene is Overworld world)
        {
            string ui = world.Current?.GetType().Name ?? "none";
            if (ui != uiName) { uiName=ui; Mark("game_menu",ui); }
            if (world.Current is OuiTitleScreen) titleSeen=true;
        }
        if (Engine.Scene is Level level)
        {
            levelFrames++;
            if (level.Session.Level != roomName) { roomName=level.Session.Level; Mark("game_room", "area=" + level.Session.Area.ID + "; room=" + roomName); }
            Player p=level.Tracker.GetEntity<Player>();
            if (p != null)
            {
                if (previousPlayer.HasValue && Vector2.DistanceSquared(previousPlayer.Value,p.Position) > 0.01f) playerMoves++;
                previousPlayer = p.Position;
                if (game.Frames % 120 == 0) Mark("game_player","x=" + p.X + "; y=" + p.Y + "; state=" + p.StateMachine.State + "; moves=" + playerMoves + "; jumps=" + jumpCalls);
            }
        }
        if (game.Frames % 180 == 0) Sample();
        return running ? 1 : 0;
    }
    public static int Suspend(int unused)
    {
        if (state != 2 || game == null) return 0;
        TouchPort.Reset();
        Audio.CJITSuspend(true);
        Sample();state=3;
        Mark("game_suspended","Frames stopped; FMOD mixer suspended.");
        return 1;
    }
    public static int Resume(int unused)
    {
        if (state != 3 || game == null) return 0;
        GC.Collect(); GC.WaitForPendingFinalizers();
        Check(jumpHook != null && jumpHook.IsApplied,"celeste_jump_hook_retained_after_resume_gc");
        Audio.CJITSuspend(false);
        game.ResetElapsedTime();jumpsAtResume=jumpCalls;resumes++;state=2;
        Mark("game_resumed","Retained Celeste and FMOD; clock reset.");
        Sample();return 1;
    }
    private static void Sample()
    {
        int controllers=0;
        for(int i=0;i<4;i++) if(GamePad.GetState((PlayerIndex)i).IsConnected) controllers |= 1 << i;
        CJGraphicsSample(game?.Frames ?? 0,0,TouchPort.Presses,TouchPort.Releases,controllers,resumes);
        Mark("game_progress","title=" + titleSeen + "; levelFrames=" + levelFrames + "; moves=" + playerMoves + "; jumps=" + jumpCalls + "; jumpsAfterResume=" + (resumes>0?jumpCalls-jumpsAtResume:0) + "; afterResume=" + framesAfterResume + "; workers=" + RunThread.ActiveCount);
    }
    public static int Stop(int unused)
    {
        // Return control to UIKit while loaders finish. The host keeps driving
        // Frame until the ordinary asynchronous save coroutine also settles.
        if (RunThread.ActiveCount != 0 || UserIO.Saving) return 3;
        bool complete=false;
        try
        {
            if (game != null)
            {
                Sample();
                if (RunThread.Failure == null) SaveGame();
                complete = titleSeen && levelFrames >= 300 && playerMoves >= 20 && jumpCalls > jumpsAtResume && resumes > 0 && framesAfterResume >= 120 && savePassed;
                game.CJITEndExternalLoop();
                Audio.Unload();
                TouchPort.Dispose();
                VirtualContent.Unload();
                game.CJITFinishGraphicsCallback();
                game.Dispose();game=null;
            }
        }
        finally { jumpHook?.Dispose();jumpHook=null;state=4; }
        Mark("game_hook_removed","Player.Jump hook disposed after game stop.");
        Mark(complete ? "game_checks_pass" : "game_checks_incomplete","Requires title, 300 level frames, movement, a hooked jump after resume, 120 more frames and actual XML save/readback.");
        return complete ? 1 : 2;
    }
    private sealed class JitGame : GameClass
    {
        public int Frames;
        protected override void LoadContent()
        {
            base.LoadContent();
            using(var target = new RenderTarget2D(GraphicsDevice,4,4,false,SurfaceFormat.Color,DepthFormat.None))
            {
                GraphicsDevice.SetRenderTarget(target); GraphicsDevice.Clear(new Color(23,91,177,255));
                GraphicsDevice.SetRenderTarget(null);
                var pixels=new Color[16];target.GetData(pixels);
                bool equal=true;foreach(var pixel in pixels)equal &= pixel == new Color(23,91,177,255);
                Check(equal,"metal_render_target_clear_and_gpu_readback");
            }
            Mark("game_content_loaded","Celeste LoadContent returned; real shaders and textures plus GPU readback.");
        }
        protected override void Draw(GameTime time)
        {
            base.Draw(time);TouchPort.Render();Frames++;
            if (Frames==1) Mark("game_first_draw","Celeste draw returned; native Present follows.");
        }
    }
}

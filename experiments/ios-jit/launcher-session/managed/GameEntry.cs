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
using Celeste.Mod;
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
    [DllImport("CJGraphicsNative",CallingConvention=CallingConvention.Cdecl)] private static extern int CJSessionAdvance(int abi,int stage);
    private static int stopStage;
    private static bool stopComplete;
    private static long stageStarted;
    public static string ContentRoot = RequiredRoot("CJIT_GAME_CONTENT_ROOT");
    public static readonly string SaveRoot = RequiredRoot("CJIT_GAME_SAVE_ROOT");
    public static readonly bool VerifySJ = Environment.GetEnvironmentVariable("CJIT_VERIFY_SJ") == "1";
    public static readonly bool IsPhone = !OperatingSystem.IsMacOS();
    private static JitGame game;
    private static Hook jumpHook;
    private delegate void JumpOriginal(Player player, bool particles, bool playSfx);
    private delegate void JumpDetour(JumpOriginal orig, Player player, bool particles, bool playSfx);
    private static int state, resumes, jumpCalls, jumpsAtResume, framesAfterResume, levelFrames, playerMoves;
    private static bool titleSeen, savePassed, saveRequested;
    private static int mapRequested;
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
        AppleJitSystem.Install();
        Platform.Initialize();
        Settings.Initialize();
        Mark("game_settings_loaded", "existing=" + Settings.Existed);
        Settings.Instance.Fullscreen = IsPhone;
        Settings.Instance.VSync = true;
        Settings.Instance.LaunchWithFMODLiveUpdate = false;
        jumpHook = new Hook(typeof(Player).GetMethod(nameof(Player.Jump),new[] {typeof(bool),typeof(bool)}),
            (JumpDetour)((orig,player,particles,sfx) => {
                orig(player,particles,sfx);
                jumpCalls++;
                if (jumpCalls <= 12 || jumpCalls % 20 == 0) Mark("game_jump_hook", "calls=" + jumpCalls + "; x=" + player.X + "; y=" + player.Y);
            }));
        Check(jumpHook.IsApplied,"celeste_player_jump_hook_installed");
        game = new JitGame();
        Platform.CheckEverest();
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
        if (Platform.Failure != null) throw new InvalidOperationException("Celeste loader failed",Platform.Failure);
        int command = CJGameTakeCommand();
        bool hostFixture=!IsPhone && Environment.GetEnvironmentVariable("CJIT_TEST_TOUCH")=="1";
        if(hostFixture && command==5)mapRequested=5;
        if(hostFixture && command==6) {
            UserIO.SaveHandler(SaveData.Instance!=null,true);UserIO.SaveHandler(SaveData.Instance!=null,true);
            game.Exit();game.Exit();Mark("game_test_quit_during_queued_save","saving="+UserIO.Saving+"; queued="+UserIO.SaveQueued);
        }
        if(hostFixture && mapRequested==5 && titleSeen && Platform.RunThreadActiveCount==0 && Engine.Scene is Overworld quitWorld) {
            if(quitWorld.Current is OuiMainMenu menu && menu.Focused) {
                typeof(OuiMainMenu).GetMethod("OnExit",BindingFlags.Instance|BindingFlags.NonPublic).Invoke(menu,null);
                mapRequested=0;Mark("game_test_desktop_menu_quit","Invoked the original main-menu action, including its fade callback.");
            } else if(quitWorld.Current is OuiTitleScreen)quitWorld.Goto<OuiMainMenu>();
        }
        if ((VerifySJ && (command == 1 || command == 2)) || (!IsPhone && Environment.GetEnvironmentVariable("CJIT_TEST_TOUCH") == "1" && (command == 3 || command == 4))) mapRequested = command;
        if (mapRequested is >=1 and <=4 && titleSeen && (Engine.Scene is Overworld || Engine.Scene is Level) && Platform.RunThreadActiveCount == 0 && !UserIO.Saving)
        {
            // Dedicated canary profile; retain slot zero if already present.
            if (SaveData.Instance == null)
            {
            var priorData = UserIO.Load<SaveData>("0");
            Mark("game_slot_loaded", "slot=0; existing=" + (priorData != null) + "; deaths=" + (priorData?.TotalDeaths ?? 0));
            var data = priorData ?? new SaveData { Name="Madeline" };
            SaveData.Start(data,0);
            }
            string sid = mapRequested == 4 ? "StrawberryJam2021/1-Beginner/mosscairn" : mapRequested == 1 ? StrawberryJam.Lobby : StrawberryJam.Bing;
            var area = (mapRequested == 3 ? AreaData.Get(1) : AreaData.Get(sid)) ?? throw new InvalidOperationException("Strawberry Jam map was not loaded from its original ZIP.");
            Engine.Scene = new LevelLoader(new Session(new AreaKey(area.ID)));
            mapRequested = 0;
            Mark("everest_test_map_requested",sid + "; area=" + area.ID + "; retained profile slot 0.");
        }
        bool running = game.CJITTickExternalLoop();
        Platform.CheckAudio();
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
            if (level.Session.Level != roomName) { roomName=level.Session.Level; Mark("game_room", "area=" + level.Session.Area.ID + "; sid=" + level.Session.Area.GetSID() + "; mode=" + level.Session.Area.Mode + "; room=" + roomName); }
            Player p=level.Tracker.GetEntity<Player>();
            if (p != null)
            {
                if (previousPlayer.HasValue && Vector2.DistanceSquared(previousPlayer.Value,p.Position) > 0.01f) playerMoves++;
                previousPlayer = p.Position;
                Platform.CheckMod(false);
                if (VerifySJ) Platform.CheckHelpers(false);
                if (game.Frames % 120 == 0) Mark("game_player","x=" + p.X + "; y=" + p.Y + "; speed=" + p.Speed + "; ground=" + p.OnGround() + "; moveX=" + Input.MoveX.Value + "; jumpHeld=" + Input.Jump.Check + "; disabled=" + MInput.Disabled + "; state=" + p.StateMachine.State + "; moves=" + playerMoves + "; jumps=" + jumpCalls);
            }
        }
        if (game.Frames % 180 == 0) Sample();
        return running ? 1 : 0;
    }
    public static int Suspend(int unused)
    {
        if (state != 2 || game == null) return 0;
        TouchPort.Reset();
        Platform.SuspendAudio(true);
        Sample();state=3;
        Mark("game_suspended","Frames stopped; FMOD mixer suspended.");
        return 1;
    }
    public static int Resume(int unused)
    {
        if (state != 3 || game == null) return 0;
        GC.Collect(); GC.WaitForPendingFinalizers();
        Check(jumpHook != null && jumpHook.IsApplied,"celeste_jump_hook_retained_after_resume_gc");
        Platform.SuspendAudio(false);
        Platform.MarkModResume();
        game.ResetElapsedTime();jumpsAtResume=jumpCalls;resumes++;state=2;
        Mark("game_resumed","Retained Celeste and FMOD; clock reset.");
        Sample();return 1;
    }
    private static void Sample()
    {
        int controllers=0;
        for(int i=0;i<4;i++) if(GamePad.GetState((PlayerIndex)i).IsConnected) controllers |= 1 << i;
        CJGraphicsSample(game?.Frames ?? 0,0,TouchPort.Presses,TouchPort.Releases,controllers,resumes);
        Mark("game_progress","title=" + titleSeen + "; levelFrames=" + levelFrames + "; moves=" + playerMoves + "; jumps=" + jumpCalls + "; jumpsAfterResume=" + (resumes>0?jumpCalls-jumpsAtResume:0) + "; afterResume=" + framesAfterResume + "; workers=" + Platform.RunThreadActiveCount);
    }
    private static int NextStage(int next)
    {
        long now=System.Diagnostics.Stopwatch.GetTimestamp();
        if(stopStage!=0)Mark("game_shutdown_stage_completed","stage="+stopStage+"; seconds="+((now-stageStarted)/(double)System.Diagnostics.Stopwatch.Frequency));
        if(CJSessionAdvance(CelesteIOS.IOSPlatformModule.ABI,next)!=1)throw new InvalidOperationException("Shutdown stage protocol mismatch.");
        stopStage=next;stageStarted=now;
        Mark("game_shutdown_stage_started","stage="+next+"; workers="+Platform.RunThreadActiveCount+"; saving="+UserIO.Saving+"; queued="+UserIO.SaveQueued);
        return 4; // Native yields without drawing once shutdown has advanced.
    }
    public static int Stop(int unused)
    {
        if(state==4)return stopComplete?1:2;
        if(game==null && stopStage<6)throw new InvalidOperationException("No retained game is available for clean shutdown.");
        if(stopStage==0)return NextStage(1);
        switch(stopStage)
        {
            case 1:
                // Keep ordinary Celeste frames alive while all existing and final
                // save requests settle, including mod sidecars and queued saves.
                if(Platform.RunThreadActiveCount!=0 || UserIO.Saving || UserIO.SaveQueued)return 3;
                if(!saveRequested) {
                    saveRequested=true;UserIO.SaveHandler(SaveData.Instance!=null,true);
                    Mark("game_final_save_requested","slot="+(SaveData.Instance?.FileSlot.ToString() ?? "none"));return 3;
                }
                Check(UserIO.SavingResult,"everest_final_save_queue_completed");
                return NextStage(2);
            case 2:
                Sample();
                if(Platform.Failure==null)SaveGame();
                Platform.CheckMod(true);
                if(VerifySJ) {
                    bool helpersPassed=Platform.CheckHelpers(true);
                    stopComplete=helpersPassed && titleSeen && levelFrames>=300 && playerMoves>=20 && jumpCalls>jumpsAtResume && resumes>0 && framesAfterResume>=120 && savePassed;
                } else stopComplete=Platform.Failure==null && game.Frames>0 && (SaveData.Instance==null || savePassed);
                Mark("game_profile_save_verified","slot="+(SaveData.Instance?.FileSlot.ToString() ?? "none")+"; complete="+stopComplete);
                return NextStage(3);
            case 3:
                game.CJITEndExternalLoop();return NextStage(4);
            case 4:
                TouchPort.Dispose();VirtualContent.Unload();game.CJITFinishGraphicsCallback();return NextStage(5);
            case 5:
                // Everest's Disposed handler unloads audio and undoes mod detours.
                // Never move thread-affine game/graphics disposal to a worker.
                game.Dispose();game=null;return NextStage(6);
            case 6:
                Platform.Shutdown();return NextStage(7);
            case 7:
                jumpHook?.Dispose();jumpHook=null;state=4;
                Mark("game_hook_removed","Player.Jump hook disposed after game stop.");
                NextStage(8);
                Mark(stopComplete?"game_checks_pass":"game_checks_incomplete",VerifySJ?"SJ regression: both maps, resume, hooks and save/readback.":"Normal play: pending saves settled, profile readback and complete managed shutdown.");
                return stopComplete?1:2;
            default:throw new InvalidOperationException("Unknown shutdown stage.");
        }
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
                var bindings=new RenderTargetBinding[4];
                Check(GraphicsDevice.GetRenderTargetsNoAllocEXT(null)==1 && GraphicsDevice.GetRenderTargetsNoAllocEXT(bindings)==1 && bindings[0].RenderTarget==target,"fna_render_target_extension_active_binding");
                GraphicsDevice.SetRenderTarget(null);
                Check(GraphicsDevice.GetRenderTargetsNoAllocEXT(null)==0,"fna_render_target_extension_backbuffer");
                var pixels=new Color[16];target.GetData(pixels);
                bool equal=true;foreach(var pixel in pixels)equal &= pixel == new Color(23,91,177,255);
                Check(equal,"metal_render_target_clear_and_gpu_readback");
            }
            Mark("game_content_loaded","Celeste LoadContent returned; real shaders and textures plus GPU readback.");
        }
        protected override void Update(GameTime time)
        {
            TouchPort.Update();
            base.Update(time);
        }
        protected override void Draw(GameTime time)
        {
            base.Draw(time);TouchPort.Render();Frames++;
            // Desktop regression fixture is never bundled or loaded on iOS.
            if (!IsPhone && Engine.Scene is Level && Environment.GetEnvironmentVariable("CJIT_FNA_GRAPHICS_TEST") is string fixture && fixture.Length>0)
            {
                if (graphicsRegression==null) graphicsRegression=(Action<GraphicsDevice>)Delegate.CreateDelegate(typeof(Action<GraphicsDevice>),Assembly.LoadFrom(fixture).GetType("FnaGraphicsTests").GetMethod("Run"));
                graphicsRegression(GraphicsDevice);
            }
            if(!IsPhone && Environment.GetEnvironmentVariable("CJIT_SESSION_TEST") is string sessionFixture && sessionFixture.Length>0) {
                if(sessionRegression==null)sessionRegression=(Action<GraphicsDevice>)Delegate.CreateDelegate(typeof(Action<GraphicsDevice>),Assembly.LoadFrom(sessionFixture).GetType("SessionIntegrationTests").GetMethod("Run"));
                sessionRegression(GraphicsDevice);
            }
            if (Frames==1) Mark("game_first_draw","Celeste draw returned; native Present follows.");
        }
        private Action<GraphicsDevice> graphicsRegression,sessionRegression;
    }
}

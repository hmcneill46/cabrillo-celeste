// Compile the selected ControllerIntegration source unchanged. The controlled
// engine/SDL and hook boundaries below perform no game, native or device work.
global using System;
global using System.Collections.Generic;
global using System.Linq;
using System.Reflection;
using System.Text.Json;
using CelesteJIT.Game;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Input;
using Monocle;

public static class ControllerLifecycleTests
{
    private static readonly List<string> checks = new();
    private static readonly Color Red = new(220, 20, 30), Blue = new(10, 40, 230);
    private static void Check(bool value, string name) {
        if (!value) throw new InvalidOperationException(name);
        checks.Add(name);
    }
    private static void NewSession(bool cache = false) {
        ControllerIntegration.Dispose();
        SDL2_FNAPlatform.SetDevices(new IntPtr(1));
        GamePad.Writes.Clear();
        Engine.Instance.IsActive = true;
        Celeste.Input.Gamepad = 0;
        Celeste.Input.OverrideInputPrefix = null;
        TouchPort.Configuration.ControllerPrompts = "automatic";
        ControllerIntegration.Install();
        ControllerIntegration.Update();
        if (cache) GamePad.SetLightBarEXT(PlayerIndex.One, Red);
        GamePad.Writes.Clear();
    }
    private static void Suspend() {
#if BUILD59
        ControllerIntegration.Suspend();
#endif
    }
    private static void Resume() {
#if BUILD59
        ControllerIntegration.Resume();
#endif
    }
    private static void ExpectWrites(int count, string name) {
        Check(GamePad.Writes.Count == count, name);
    }
    private static void CommonResumeRegression() {
        NewSession(cache: true);
        Suspend();
        // Native58/59 pauses display ticks before Suspend, and restarts them
        // after Resume. SDL may deliver both focus changes before the next Tick.
        Engine.Instance.IsActive = false;
        Engine.Instance.IsActive = true;
        Resume();
        ControllerIntegration.Update();
#if BUILD59
        ExpectWrites(1, "same-controller paused lifecycle replays cached colour");
        Check(GamePad.Writes[0] == (PlayerIndex.One, Red), "resume preserves the exact selected colour/player");
#else
        ExpectWrites(0, "original58 reproduces missing replay after paused lifecycle");
#endif
        GamePad.Writes.Clear();
        Engine.Instance.IsActive = false;
        ControllerIntegration.Update();
        Engine.Instance.IsActive = true;
        ControllerIntegration.Update();
        ExpectWrites(1, "sampled inactive-update positive control still replays");
    }
#if BUILD59
    private static void CurrentLifecycle() {
        NewSession();
        Suspend(); Resume(); ControllerIntegration.Update();
        ExpectWrites(0, "no cached colour causes no resume write");
        GamePad.SetLightBarEXT(PlayerIndex.One, Blue);
        Check(GamePad.Writes.Count == 1 && GamePad.Writes[0].Item2 == Blue, "ordinary game colour still passes through the actual hook");
        GamePad.Writes.Clear(); ControllerIntegration.Update(); Resume(); ControllerIntegration.Update();
        ExpectWrites(0, "an empty-cache resume is consumed without duplicating a later ordinary colour");

        NewSession(cache: true);
        Suspend(); Suspend();
        // Engine.IsActive can still be true until the queued SDL event is polled.
        ControllerIntegration.Update(); ControllerIntegration.Update();
        ExpectWrites(0, "explicit suspension prevents replay while sampled engine focus is still true");
        Resume(); Resume();
        ControllerIntegration.Update(); ControllerIntegration.Update();
        ExpectWrites(1, "repeated suspend/resume and ordinary updates replay only once");
        GamePad.Writes.Clear(); Resume(); ControllerIntegration.Update();
        ExpectWrites(0, "repeated Resume after completion does not schedule another replay");

        NewSession(cache: true);
        Suspend(); Engine.Instance.IsActive = false; Resume();
        ControllerIntegration.Update(); ControllerIntegration.Update();
        ExpectWrites(0, "inactive resumed engine performs no background replay");
        Engine.Instance.IsActive = true; ControllerIntegration.Update();
        ExpectWrites(1, "pending replay survives until the first valid foreground update");
        Check(GamePad.Writes[0].Item2 == Red, "deferred foreground replay keeps original RGB bytes");

        NewSession(cache: true);
        Suspend(); SDL2_FNAPlatform.SetDevices(IntPtr.Zero); ControllerIntegration.Update();
        Resume(); ControllerIntegration.Update(); ControllerIntegration.Update();
        ExpectWrites(0, "missing controller never receives a replay");
        SDL2_FNAPlatform.SetDevices(new IntPtr(2)); ControllerIntegration.Update(); ControllerIntegration.Update();
        ExpectWrites(1, "pending resume replays once on a later controller reconnect");
        Check(GamePad.Writes[0] == (PlayerIndex.One, Red), "reconnected selected controller receives the cached colour");

        NewSession(cache: true);
        Suspend(); SDL2_FNAPlatform.SetDevices(IntPtr.Zero); SDL2_FNAPlatform.SetDevices(new IntPtr(1));
        Resume(); ControllerIntegration.Update();
        ExpectWrites(1, "same-handle reconnect between paused updates still replays");

        NewSession(cache: true);
        Suspend(); SDL2_FNAPlatform.SetDevices(new IntPtr(3)); ControllerIntegration.Update();
        ExpectWrites(0, "controller replacement while explicitly suspended has no background replay");
        Resume(); ControllerIntegration.Update(); ControllerIntegration.Update();
        ExpectWrites(1, "controller replacement while suspended replays once after return");

        NewSession(cache: true);
        GamePad.SetLightBarEXT(PlayerIndex.Two, Blue); GamePad.Writes.Clear();
        Suspend(); Resume(); ControllerIntegration.Update();
        Check(GamePad.Writes.Count == 1 && GamePad.Writes[0] == (PlayerIndex.One, Red), "another player colour does not overwrite the selected player's cached colour");
        GamePad.SetLightBarEXT(PlayerIndex.One, Blue); GamePad.Writes.Clear();
        Suspend(); Resume(); ControllerIntegration.Update();
        Check(GamePad.Writes.Count == 1 && GamePad.Writes[0].Item2 == Blue, "resume uses the most recent ordinary selected-player colour");

        NewSession(cache: true);
        SDL2_FNAPlatform.SetDevices(new IntPtr(1), new IntPtr(4)); Celeste.Input.Gamepad = 1;
        ControllerIntegration.Update(); ControllerIntegration.Update();
        Check(GamePad.Writes.Count == 1 && GamePad.Writes[0] == (PlayerIndex.Two, Red), "existing selected-player change replays once to the exact FNA index");

        NewSession(cache: true);
        Suspend(); Resume(); ControllerIntegration.Dispose(); ControllerIntegration.Dispose();
        Check(MonoMod.RuntimeDetour.Hook.Count == 0, "Dispose removes every installed controller hook idempotently");
        GamePad.Writes.Clear(); ControllerIntegration.Install(); ControllerIntegration.Update();
        ExpectWrites(0, "dispose/new session discards pending replay and previous cached colour");
        GamePad.SetLightBarEXT(PlayerIndex.One, Blue); GamePad.Writes.Clear();
        Suspend(); Resume(); ControllerIntegration.Update(); ControllerIntegration.Update();
        Check(GamePad.Writes.Count == 1 && GamePad.Writes[0].Item2 == Blue, "new session has no stale active flag and can resume with its own colour");

        NewSession(cache: true);
        Suspend(); Resume(); Engine.Instance.IsActive = false; ControllerIntegration.Update();
        ControllerIntegration.Dispose(); ControllerIntegration.Install();
        Engine.Instance.IsActive = true; ControllerIntegration.Update();
        ExpectWrites(0, "disposing while deferred/inactive cannot carry colour into a new session");
        Check(Celeste.Input.GuiInputPrefix(Celeste.Input.PrefixMode.Attached) == "ps4", "automatic SDL controller family remains intact");
        TouchPort.Configuration.ControllerPrompts = "xbox";
        Check(Celeste.Input.GuiInputPrefix(Celeste.Input.PrefixMode.Attached) == "xb1", "manual prompt override remains intact");
        Celeste.Input.OverrideInputPrefix = "ns";
        Check(Celeste.Input.GuiInputPrefix(Celeste.Input.PrefixMode.Attached) == "ns", "explicit mod prompt override remains intact");
    }
#endif
    public static void Main(string[] args) {
        try {
            CommonResumeRegression();
#if BUILD59
            CurrentLifecycle();
            string status = "PASS_CONTROLLER59_LIFECYCLE";
#else
            string status = "REPRODUCED_CONTROLLER58_RESUME_GAP";
#endif
            System.IO.File.WriteAllText(args[0], JsonSerializer.Serialize(new {
                status, checks, actual_production_controller_source_compiled = true,
                engine_sdl_and_hook_boundaries_controlled = true,
                actual_game_or_adapter_loaded = false, physical_device_tested = false
            }, new JsonSerializerOptions { WriteIndented = true }) + "\n");
            Console.WriteLine(status + " checks=" + checks.Count);
        } finally { ControllerIntegration.Dispose(); }
    }
}

namespace Microsoft.Xna.Framework {
    public enum PlayerIndex { One, Two, Three, Four }
    public readonly record struct Color(byte R, byte G, byte B);
    internal static class SDL2_FNAPlatform {
        private static IntPtr[] INTERNAL_devices = new IntPtr[4];
        internal static void SetDevices(params IntPtr[] values) {
            Array.Clear(INTERNAL_devices);
            Array.Copy(values, INTERNAL_devices, values.Length);
        }
    }
}
namespace Microsoft.Xna.Framework.Input {
    public static class GamePad {
        public static readonly List<(PlayerIndex, Color)> Writes = new();
        private static readonly MethodInfo setLight = typeof(GamePad).GetMethod(nameof(SetLightBarEXT));
        private static void OriginalLight(PlayerIndex index, Color color) => Writes.Add((index, color));
        public static void SetLightBarEXT(PlayerIndex index, Color color) =>
            MonoMod.RuntimeDetour.Hook.Invoke(setLight, typeof(GamePad).GetMethod(nameof(OriginalLight), BindingFlags.NonPublic | BindingFlags.Static), index, color);
        public static string GetGUIDEXT(PlayerIndex index) => "synthetic";
        public static Capabilities GetCapabilities(PlayerIndex index) => new();
    }
    public readonly struct Capabilities { public bool HasLightBarEXT => true; }
}
namespace Celeste {
    public static class Input {
        public enum PrefixMode { Latest, Attached }
        public static int Gamepad;
        public static string OverrideInputPrefix;
        private static string OriginalPrefix(PrefixMode mode) => OverrideInputPrefix ?? "xb1";
        public static string GuiInputPrefix(PrefixMode mode) => (string)MonoMod.RuntimeDetour.Hook.Invoke(
            typeof(Input).GetMethod(nameof(GuiInputPrefix)),
            typeof(Input).GetMethod(nameof(OriginalPrefix), BindingFlags.NonPublic | BindingFlags.Static), mode);
    }
}
namespace CelesteIOS { public enum InputSource { Touch, Keyboard, Controller } }
namespace Monocle { public sealed class Engine { public static Engine Instance = new(); public bool IsActive = true; } }
namespace MonoMod.RuntimeDetour {
    public sealed class Hook : IDisposable {
        private static readonly Dictionary<MethodInfo, Delegate> installed = new();
        private readonly MethodInfo method;
        public static int Count => installed.Count;
        public Hook(MethodInfo method, Delegate detour) { this.method = method; installed.Add(method, detour); }
        public static object Invoke(MethodInfo method, MethodInfo original, params object[] args) {
            if (!installed.TryGetValue(method, out var detour)) return original.Invoke(null, args);
            var originalType = detour.GetType().GetMethod("Invoke").GetParameters()[0].ParameterType;
            return detour.DynamicInvoke(new object[] { original.CreateDelegate(originalType) }.Concat(args).ToArray());
        }
        public void Dispose() => installed.Remove(method);
    }
}
namespace SDL2 {
    public static class SDL {
        public enum SDL_GameControllerType {
            SDL_CONTROLLER_TYPE_XBOX360 = 1, SDL_CONTROLLER_TYPE_XBOXONE = 2,
            SDL_CONTROLLER_TYPE_PS3 = 3, SDL_CONTROLLER_TYPE_PS4 = 4,
            SDL_CONTROLLER_TYPE_NINTENDO_SWITCH_PRO = 5, SDL_CONTROLLER_TYPE_PS5 = 7
        }
        public enum SDL_bool { SDL_FALSE, SDL_TRUE }
        public static SDL_GameControllerType SDL_GameControllerGetType(IntPtr device) => SDL_GameControllerType.SDL_CONTROLLER_TYPE_PS5;
        public static string SDL_GameControllerName(IntPtr device) => "synthetic";
        public static SDL_bool SDL_GameControllerHasLED(IntPtr device) => SDL_bool.SDL_TRUE;
    }
}
namespace CelesteJIT.Game {
    public static class Entry { public static void Mark(string key, string value) { } }
    public static class TouchPort {
        public static CelesteIOS.InputSource Source => CelesteIOS.InputSource.Controller;
        public static ConfigurationValue Configuration = new();
    }
    public sealed class ConfigurationValue { public string ControllerPrompts = "automatic"; }
}

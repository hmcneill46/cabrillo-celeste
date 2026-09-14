using System;
using System.Runtime.Loader;
using Celeste;
using Celeste.Mod;
using Celeste.Mod.Entities;
using Microsoft.Xna.Framework;
using Monocle;
using MonoMod.Cil;

namespace CJITCodeCanary;

// Ordinary Everest code mod: no launcher reference, native calls or game patch.
public sealed class CanaryModule : EverestModule
{
    public static CanaryModule Instance;
    public static int HookJumps, ILJumps, EntitiesCreated, RenderFrames, LoadedJumps, WrittenJumps;
    public static string ContextName;
    public override Type SaveDataType => typeof(CanarySaveData);
    public CanarySaveData Data => (CanarySaveData)_SaveData;

    public override void Load()
    {
        Instance = this;
        ContextName = AssemblyLoadContext.GetLoadContext(GetType().Assembly)?.Name;
        On.Celeste.Player.Jump += Jump;
        IL.Celeste.Player.Jump += PatchJump;
        Console.WriteLine("CJIT_MOD loaded; context=" + ContextName);
    }

    private static void Jump(On.Celeste.Player.orig_Jump orig, Player player, bool particles, bool playSfx)
    {
        orig(player, particles, playSfx);
        HookJumps++;
        if (Instance._SaveData is CanarySaveData data) data.Jumps++;
        Console.WriteLine("CJIT_MOD Hook jump=" + HookJumps + "; IL=" + ILJumps);
    }

    private static void PatchJump(ILContext context)
    {
        new ILCursor(context).EmitDelegate<Action>(() => ILJumps++);
    }

    public override void DeserializeSaveData(int index, byte[] data)
    {
        base.DeserializeSaveData(index, data);
        LoadedJumps = Data.Jumps;
        Console.WriteLine("CJIT_MOD save loaded; jumps=" + LoadedJumps + "; bytes=" + (data?.Length ?? 0));
    }

    public override void WriteSaveData(int index, byte[] data)
    {
        base.WriteSaveData(index, data);
        WrittenJumps = Data.Jumps;
        Console.WriteLine("CJIT_MOD save written; jumps=" + WrittenJumps + "; bytes=" + (data?.Length ?? 0));
    }

    public override void Unload()
    {
        On.Celeste.Player.Jump -= Jump;
        IL.Celeste.Player.Jump -= PatchJump;
        Console.WriteLine("CJIT_MOD hooks removed");
        Instance = null;
    }
}

public sealed class CanarySaveData : EverestModuleSaveData
{
    public int Jumps { get; set; }
}

[CustomEntity("CJITCanary/status")]
public sealed class StatusSign : Entity
{
    public StatusSign(EntityData data, Vector2 offset) : base(data.Position + offset)
    {
        Depth = -1000000;
        CanaryModule.EntitiesCreated++;
        Console.WriteLine("CJIT_MOD custom entity created");
    }

    public override void Render()
    {
        base.Render();
        if (!(Scene is Level level)) return;
        Vector2 at = level.Camera.Position + new Vector2(12, 12);
        Draw.Rect(at.X - 4, at.Y - 4, 220, 39, Color.Black * 0.8f);
        ActiveFont.DrawOutline("CODE MOD ACTIVE", at, Vector2.Zero, Vector2.One * 0.23f, Color.LimeGreen, 1, Color.Black);
        string text = "Hook " + CanaryModule.HookJumps + " / IL " + CanaryModule.ILJumps + " / saved " + CanaryModule.LoadedJumps;
        ActiveFont.DrawOutline(text, at + new Vector2(0, 19), Vector2.Zero, Vector2.One * 0.18f, Color.White, 1, Color.Black);
        CanaryModule.RenderFrames++;
    }
}

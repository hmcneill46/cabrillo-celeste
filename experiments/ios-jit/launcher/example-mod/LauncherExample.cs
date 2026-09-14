using Celeste.Mod;
namespace CelesteJITLauncherExample;
// A normal independent Everest DLL: no references to the iOS host or its probes.
public sealed class LauncherExample : EverestModule
{
    public override void Load() => Logger.Log("CJITLauncherExample", "Enabled through the native mod library (1.0.0).");
    public override void Unload() { }
}

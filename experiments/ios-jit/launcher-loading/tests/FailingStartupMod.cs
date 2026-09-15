// Deliberate external integration failure; never included in a device package.
using System;
using Celeste.Mod;
public sealed class FailingStartupMod : EverestModule {
    public override void Load() { throw new InvalidOperationException("CABRILLO_EXPECTED_STARTUP_MOD_FAILURE"); }
    public override void Unload() { }
}

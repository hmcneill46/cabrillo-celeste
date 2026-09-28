// Host-only, loaded into the actual pinned Everest game. Never shipped in the IPA.
using System;
using System.IO;
using System.Linq;
using Celeste;
using Monocle;
using CelesteJIT.Game;
public static class SaveTransferIntegrationTests {
    private static bool complete;
    public static void Run() {
        if (complete || CelesteJIT.Game.Platform.RunThreadActiveCount != 0 || !(Engine.Scene is Level || Engine.Scene is Overworld world && world.Current is OuiTitleScreen)) return;
        complete = true;
        var original = UserIO.Load<SaveData>("0");
        var imported = UserIO.Load<SaveData>("2");
        if (original == null || imported == null || imported.FileSlot != 2 || original.FileSlot != 0 ||
            original.Name != imported.Name || original.Time != imported.Time || original.TotalDeaths != imported.TotalDeaths)
            throw new Exception("Transferred desktop save did not deserialize with matching progress and new slot index.");
        var saves = Path.Combine(Environment.GetEnvironmentVariable("CJIT_GAME_SAVE_ROOT"), "Saves");
        int count = 0;
        foreach (var source in Directory.GetFiles(saves, "0-mod*.celeste")) {
            var target = Path.Combine(saves, "2" + Path.GetFileName(source).Substring(1));
            if (!File.Exists(target) || !File.ReadAllBytes(source).SequenceEqual(File.ReadAllBytes(target)))
                throw new Exception("Transferred mod sidecar differs: " + Path.GetFileName(source));
            count++;
        }
        Console.WriteLine("PASS_DESKTOP_SAVE_TRANSFER_REAL_EVEREST source=0 destination=2 mod_files=" + count);
    }
}

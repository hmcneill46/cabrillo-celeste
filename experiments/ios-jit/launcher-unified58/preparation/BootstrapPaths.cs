using System;
using System.IO;
using System.Linq;

namespace Cabrillo.Preparation;

// Everest normally keeps its rules beside Celeste.dll. The owned game is now
// in Documents; the public rules remain in the read-only application bundle.
public static class BootstrapPaths
{
    public static string BundledDirectory(string ignoredGamePath) => AppContext.BaseDirectory;
    public static string[] GameFiles(string gameDirectory) => Directory.GetFiles(gameDirectory)
        .Append(Path.Combine(AppContext.BaseDirectory, "Celeste.Mod.mm.dll")).Distinct(StringComparer.Ordinal).ToArray();
}

using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;

namespace Cabrillo.Preparation;

internal static class GameCodePipeline
{
    [MethodImpl(MethodImplOptions.NoInlining)]
    internal static void Prepare(string original, string output, string bundled, Action<string> stage)
    {
        string priorDeps = Environment.GetEnvironmentVariable("MONOMOD_DEPDIRS");
        string priorMissing = Environment.GetEnvironmentVariable("MONOMOD_DEPENDENCY_MISSING_THROW");
        try
        {
            Environment.SetEnvironmentVariable("MONOMOD_DEPDIRS", string.Join(Path.PathSeparator, new[] {output, bundled, original}));
            Environment.SetEnvironmentVariable("MONOMOD_DEPENDENCY_MISSING_THROW", "0");
            string game = Path.Combine(output, "Celeste.dll"), hooks = Path.Combine(output, "MMHOOK_Celeste.dll");
            stage("Preparing your game code · this is saved for future launches");
            NETCoreifier.Coreifier.ConvertToNetCore(Path.Combine(original, "Celeste.exe"), game);
            NETCoreifier.Coreifier.ConvertToNetCore(Path.Combine(original, "Celeste.Content.dll"), Path.Combine(output, "Celeste.Content.dll"));
            stage("Applying Everest to your game code");
            Tool("MonoMod.Patcher", game, Path.Combine(bundled, "Celeste.Mod.mm.dll"), game + ".patched");
            File.Move(game + ".patched", game, true);
            stage("Preparing mod hooks");
            Tool("MonoMod.RuntimeDetour.HookGen", "--private", game, hooks);
            Tool("MonoMod.Patcher", hooks, Path.Combine(bundled, "Celeste.Mod.mm.dll"), hooks + ".patched");
            File.Move(hooks + ".patched", hooks, true);
            stage("Applying the Apple platform adaptations");
            PlatformPatch.Apply(game, game + ".platform", Path.Combine(output, "platform.json"));
            File.Move(game + ".platform", game, true);
            stage("Applying the tested physics corrections");
            RepairPlayerPrecision.Apply(new[] {game, game + ".repaired", Path.Combine(output, "precision.json")});
            File.Move(game + ".repaired", game, true);
            stage("Verifying the prepared game");
            if (AppDomain.CurrentDomain.GetAssemblies().Any(a => a.GetName().Name == "Celeste"))
                throw new InvalidOperationException("The game was loaded before preparation completed. Relaunch before playing.");
            Directory.CreateDirectory(Path.Combine(output, "orig"));
            File.Copy(Path.Combine(original, "Celeste.exe"), Path.Combine(output, "orig/Celeste.exe"));
        }
        finally
        {
            Environment.SetEnvironmentVariable("MONOMOD_DEPDIRS", priorDeps);
            Environment.SetEnvironmentVariable("MONOMOD_DEPENDENCY_MISSING_THROW", priorMissing);
        }
    }
    private static void Tool(string name, params string[] arguments)
    {
        var main = Assembly.Load(name).EntryPoint ?? throw new MissingMethodException(name, "Main");
        try
        {
            object result = main.Invoke(null, new object[] {arguments});
            if (result is int code && code != 0) throw new InvalidOperationException(name + " could not prepare this game (" + code + ").");
        }
        catch (TargetInvocationException error) { throw error.InnerException ?? error; }
    }
}

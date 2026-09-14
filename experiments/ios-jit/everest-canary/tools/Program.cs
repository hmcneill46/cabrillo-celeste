using System.Reflection;
using System.Text.Json;
using Mono.Cecil;

internal static class Program
{
    private static int Main(string[] args)
    {
        if (args.Length == 0) throw new ArgumentException("Expected coreify, patch, hookgen or inspect.");
        switch (args[0])
        {
            case "coreify":
                NETCoreifier.Coreifier.ConvertToNetCore(args[1], args[2]);
                return 0;
            case "patch":
                return Run("MonoMod.Patcher", args[1..]);
            case "hookgen":
                return Run("MonoMod.RuntimeDetour.HookGen", args[1..]);
            case "platform":
                PlatformPatch.Apply(args[1], args[2], args[3]);
                return 0;
            case "fna-compat":
                FnaCompatibility.Apply(args[1], args[2], args[3]);
                return 0;
            case "check-fna":
                return FnaCompatibility.Check(args[1], args[2..]);
            case "inspect":
                using (var module = ModuleDefinition.ReadModule(args[1]))
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        identity = module.Assembly.Name.FullName,
                        references = module.AssemblyReferences.Select(x => x.FullName),
                        types = module.GetTypes().Select(t => new
                        {
                            name = t.FullName,
                            methods = t.Methods.Select(m => m.FullName),
                            fields = t.Fields.Select(f => f.FullName)
                        })
                    }));
                }
                return 0;
            default:
                throw new ArgumentException("Unknown operation: " + args[0]);
        }
    }

    private static int Run(string assemblyName, string[] args)
    {
        var main = Assembly.Load(assemblyName).EntryPoint ?? throw new MissingMethodException(assemblyName, "Main");
        try { return main.Invoke(null, new object[] { args }) as int? ?? 0; }
        catch (TargetInvocationException ex) { throw ex.InnerException ?? ex; }
    }
}

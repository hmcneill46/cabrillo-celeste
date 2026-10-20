using System.Collections;
using System.IO;
using System.Reflection;
using System.Runtime.Loader;
using Celeste.Mod;
using Mono.Cecil;
using MonoMod.RuntimeDetour;

namespace CelesteJIT.Game;

internal static class MonoTypeDiscovery
{
    private static Hook hook;
    private static readonly FieldInfo modulesField = typeof(EverestModuleAssemblyContext)
        .GetField("_AssemblyModules", BindingFlags.NonPublic | BindingFlags.Instance)
        ?? throw new MissingFieldException("EverestModuleAssemblyContext._AssemblyModules");
    private delegate Type[] Original(Assembly assembly);
    private delegate Type[] Detour(Original original, Assembly assembly);

    internal static void Install()
    {
        hook = new Hook(typeof(Celeste.Mod.Extensions).GetMethod("GetTypesSafe"), (Detour)Discover);
        Entry.Mark("mono_type_discovery_installed", "Retain loadable types when Mono GetTypes throws an individual loader exception.");
    }

    private static bool IsLoaderException(Exception error) =>
        error is TypeLoadException || error is FileNotFoundException || error is FileLoadException;

    private static Type[] Discover(Original original, Assembly assembly)
    {
        try
        {
            Type[] types = original(assembly);
            if (AssemblyLoadContext.GetLoadContext(assembly) is not EverestModuleAssemblyContext) return types;
            return types.Where(IsLoadable).ToArray();
        }
        catch (Exception ex) when (IsLoaderException(ex) && AssemblyLoadContext.GetLoadContext(assembly) is EverestModuleAssemblyContext)
        {
            var context = (EverestModuleAssemblyContext)AssemblyLoadContext.GetLoadContext(assembly);
            // Read only the exact relinked metadata already retained by this
            // context. No new assembly/file is loaded, substituted or disposed.
            var modules = (IDictionary)modulesField.GetValue(context);
            var module = modules[assembly.GetName().Name] as ModuleDefinition;
            if (module == null || module.Assembly.Name.FullName != assembly.FullName) throw;
            var result = new List<Type>();
            var skipped = new List<string>();
            foreach (var definition in module.GetTypes())
            {
                if (definition.Name == "<Module>") continue;
                string name = definition.FullName.Replace('/', '+');
                try
                {
                    Type type = assembly.GetType(name, throwOnError: false);
                    if (type != null && IsLoadable(type)) result.Add(type);
                    else skipped.Add(name);
                }
                catch (Exception error) when (IsLoaderException(error)) { skipped.Add(name); }
            }
            Entry.Mark("mono_type_discovery_recovered", "module=" + context.Name + "; retained=" + result.Count +
                "; skipped=" + skipped.Count + "; types=" + string.Join(",", skipped));
            return result.ToArray();
        }
    }

    private static bool IsLoadable(Type type)
    {
        try
        {
            // Mono can return a cached RuntimeType whose missing parent has
            // already marked its class failed. Namespace can crash on that
            // partial class; CanCastTo checks the failure and throws first.
            _ = typeof(object).IsAssignableFrom(type);
            return Celeste.Mod.Extensions.IsSafe(type);
        }
        catch (Exception error) when (IsLoaderException(error)) { return false; }
    }

    internal static void Dispose() { hook?.Dispose(); hook = null; }
}

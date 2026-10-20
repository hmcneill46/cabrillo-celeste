using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Mono.Cecil;
using Mono.Cecil.Cil;

// Build-time metadata reader. This never loads or executes the game or adapter.
internal static class Everest6642Audit
{
    const string Version = "1.6642.0";
    const string Commit = "5abd7876821223c20711c1844a5187321d6e904c";
    const string VersionString = Version + "-cjit-5abd787";
    static readonly List<string> Checks = new();
    static void Check(bool value, string label)
    {
        if (!value) throw new InvalidDataException(label);
        Checks.Add(label);
    }
    static string Hash(byte[] bytes) => Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
    static bool Digest(string value) => value != null && value.Length == 64 && value.All(c => c is >= '0' and <= '9' or >= 'a' and <= 'f');
    static TypeDefinition Type(AssemblyDefinition assembly, string name) =>
        assembly.MainModule.GetType(name) ?? throw new InvalidDataException("Missing compiled type: " + name);
    static FieldDefinition Field(TypeDefinition type, string name) =>
        type.Fields.SingleOrDefault(f => f.Name == name) ?? throw new InvalidDataException("Missing compiled field: " + name);
    static string Constant(TypeDefinition type, string name)
    {
        var field = Field(type, name);
        Check(field.HasConstant && field.Constant is string, "Compiled identity constant: " + name);
        return (string)field.Constant;
    }
    static Instruction VersionInstruction(AssemblyDefinition assembly)
    {
        var type = Type(assembly, "Celeste.Mod.Everest");
        var field = Field(type, "VersionString");
        var initializer = type.Methods.Single(m => m.IsConstructor && m.IsStatic);
        var write = initializer.Body.Instructions.Single(i => i.OpCode == OpCodes.Stsfld &&
            i.Operand is FieldReference f && f.FullName == field.FullName);
        var value = write.Previous;
        while (value != null && value.OpCode == OpCodes.Nop) value = value.Previous;
        Check(value != null && value.OpCode == OpCodes.Ldstr, "Everest VersionString has an explicit compiled initializer");
        return value;
    }
    static IEnumerable<string> AttributeStrings(CustomAttributeArgument argument)
    {
        if (argument.Value is string text) yield return text;
        if (argument.Value is CustomAttributeArgument[] nested)
            foreach (var item in nested) foreach (string value in AttributeStrings(item)) yield return value;
    }
    static Dictionary<string, string> Pins(JsonElement inputs) => inputs.EnumerateObject().ToDictionary(
        p => p.Name, p => p.Value.GetProperty("bytes").GetInt64().ToString(CultureInfo.InvariantCulture) + "\0" +
            p.Value.GetProperty("sha256").GetString(), StringComparer.Ordinal);
    static DefaultAssemblyResolver Resolver(string directory)
    {
        var resolver = new DefaultAssemblyResolver();
        resolver.AddSearchDirectory(directory);
        resolver.AddSearchDirectory(AppContext.BaseDirectory);
        return resolver;
    }
    static AssemblyDefinition Open(string path, IAssemblyResolver resolver) =>
        AssemblyDefinition.ReadAssembly(path, new ReaderParameters {AssemblyResolver=resolver});

    static int Main(string[] args)
    {
        try
        {
            if (args.Length == 3 && args[0] == "rewrite-version-control")
            {
                using var controlResolver = Resolver(Path.GetDirectoryName(Path.GetFullPath(args[1])));
                using var control = Open(args[1], controlResolver);
                Check((string)VersionInstruction(control).Operand == VersionString, "Version-control source is the actual stable6642 payload");
                // A whole-module rewrite would need the deliberately unbundled
                // Celeste reference for unrelated enum defaults. Change only the
                // one same-length user-string value, then read it back with Cecil.
                byte[] bytes = File.ReadAllBytes(args[1]);
                byte[] expected = Encoding.Unicode.GetBytes(VersionString);
                byte[] wrong = Encoding.Unicode.GetBytes("1.6580.0-cjit-082e21b");
                Check(expected.Length == wrong.Length, "Version-control replacement preserves metadata offsets");
                var locations = new List<int>();
                for (int index = 0; index <= bytes.Length - expected.Length; index++)
                    if (bytes.AsSpan(index, expected.Length).SequenceEqual(expected)) locations.Add(index);
                Check(locations.Count == 1, "Version-control user string is unique");
                wrong.CopyTo(bytes, locations[0]);
                File.WriteAllBytes(args[2], bytes);
                using var reread = Open(args[2], controlResolver);
                Check((string)VersionInstruction(reread).Operand == "1.6580.0-cjit-082e21b", "Cecil reads the intentionally wrong compiled version");
                Console.WriteLine("CREATED_INVALID_VERSION_CONTROL");
                return 0;
            }
            if (args.Length != 5) throw new ArgumentException("Expected managed directory, recipe, runtime identity, original identity and report paths.");
            string managed = Path.GetFullPath(args[0]);
            using var resolver = Resolver(managed);
            using var runtimeDocument = JsonDocument.Parse(File.ReadAllBytes(args[2]));
            var runtime = runtimeDocument.RootElement;
            string runtimeHash = Hash(File.ReadAllBytes(args[2]));
            var builtins = runtime.GetProperty("builtins");
            Check(runtime.GetProperty("schema").GetInt32() == 1 && runtime.GetProperty("compatibilityPolicy").GetInt32() == 1,
                "Runtime policy remains schema1/policy1");
            Check(runtime.GetProperty("everestSourceCommit").GetString() == Commit &&
                builtins.GetProperty("Everest").GetString() == Version && builtins.GetProperty("EverestCore").GetString() == Version,
                "Runtime manifest selects stable6642 source");
            using var patch = Open(Path.Combine(managed, "Celeste.Mod.mm.dll"), resolver);
            Check((string)VersionInstruction(patch).Operand == VersionString, "Everest VersionString matches stable6642");
            using var adapter = Open(Path.Combine(managed, "CelesteJITEverest.dll"), resolver);
            var identity = Type(adapter, "CelesteJIT.Game.RuntimeIdentity");
            Check(Constant(identity, "ManifestSHA256") == runtimeHash && Constant(identity, "EverestSourceCommit") == Commit &&
                Constant(identity, "EverestVersionString") == VersionString, "Adapter identity matches the native runtime manifest");
            var modules = identity.Methods.Single(m => m.Name == "ExpectedModules");
            var actualStrings = modules.Body.Instructions.Where(i => i.OpCode == OpCodes.Ldstr).Select(i => (string)i.Operand).ToArray();
            var expectedStrings = builtins.EnumerateObject().Where(p => p.Name != "EverestCore").OrderBy(p => p.Name, StringComparer.Ordinal)
                .SelectMany(p => new[] {p.Name, p.Value.GetString()}).ToArray();
            Check(actualStrings.SequenceEqual(expectedStrings), "Compiled adapter numeric module versions match native planning");

            var teleport = Type(patch, "Celeste.Mod.Entities.TeleportTrigger");
            Check(teleport.CustomAttributes.Any(a => a.AttributeType.Name == "CustomEntityAttribute" &&
                a.ConstructorArguments.SelectMany(AttributeStrings).Contains("everest/teleportTrigger")), "TeleportTrigger entity registration is compiled");
            Check(teleport.Methods.Any(m => m.Name == "OnEnter" && m.Parameters.Count == 1 && m.Parameters[0].ParameterType.FullName == "Celeste.Player"),
                "TeleportTrigger player entry method is compiled");
            var settings = Type(patch, "Celeste.Mod.Core.CoreModuleSettings");
            var search = settings.Properties.SingleOrDefault(p => p.Name == "MenuSearch");
            Check(search != null && search.PropertyType.FullName == "Celeste.Mod.ButtonBinding" && search.GetMethod != null && search.SetMethod != null,
                "MenuSearch binding property is compiled");
            var binding = search.CustomAttributes.Single(a => a.AttributeType.Name == "DefaultButtonBindingAttribute");
            Check(binding.ConstructorArguments.Count == 2 && Convert.ToInt32(binding.ConstructorArguments[0].Value, CultureInfo.InvariantCulture) == 0 &&
                Convert.ToInt32(binding.ConstructorArguments[1].Value, CultureInfo.InvariantCulture) == 82, "MenuSearch default binding is keyboard R");
            var helpers = Type(patch, "Celeste.Mod.Helpers.ModUpdaterHelper");
            var mirrors = helpers.Methods.Where(m => m.Name == "GetAllMirrorUrls").ToArray();
            Check(mirrors.Length == 1 && mirrors[0].IsPublic && mirrors[0].IsStatic && mirrors[0].Parameters.Count == 1 &&
                mirrors[0].Parameters[0].ParameterType.FullName == "Celeste.Mod.Helpers.ModUpdateInfo" &&
                mirrors[0].ReturnType.FullName == "System.Collections.Generic.IEnumerable`1<System.String>", "Mirror helper uses the stable6642 ModUpdateInfo signature");
            Check(Type(patch, "Celeste.Mod.Helpers.ModUpdateInfo").Properties.Any(p => p.Name == "MirrorName"), "MirrorName metadata is compiled");

            var forbidden = new HashSet<string>(new[] {"Celeste", "Celeste.Content", "MMHOOK_Celeste"}, StringComparer.OrdinalIgnoreCase);
            var assemblies = Directory.GetFileSystemEntries(managed).OrderBy(p => p, StringComparer.Ordinal).ToArray();
            Check(assemblies.All(p => File.Exists(p) && Path.GetExtension(p).Equals(".dll", StringComparison.OrdinalIgnoreCase)),
                "Managed payload contains only flat DLL files, without game executables or nested content");
            foreach (string path in assemblies)
            {
                Check(!forbidden.Contains(Path.GetFileNameWithoutExtension(path)), "No bundled game filename: " + Path.GetFileName(path));
                using var assembly = Open(path, resolver);
                Check(!forbidden.Contains(assembly.Name.Name), "No disguised bundled game assembly: " + assembly.Name.Name);
            }
            using var recipeDocument = JsonDocument.Parse(File.ReadAllBytes(args[1]));
            using var originalDocument = JsonDocument.Parse(File.ReadAllBytes(args[3]));
            var recipe = recipeDocument.RootElement; var original = originalDocument.RootElement;
            Check(recipe.GetProperty("schema").GetInt32() == 1, "Preparation recipe schema remains1");
            var inputs = Pins(recipe.GetProperty("inputs")); var expectedInputs = Pins(original.GetProperty("inputs"));
            Check(inputs.Count == 3 && inputs.Count == expectedInputs.Count && inputs.All(p => expectedInputs.TryGetValue(p.Key, out string value) && value == p.Value),
                "Original Celeste input pins are unchanged");
            string canonical = string.Concat(inputs.OrderBy(p => p.Key, StringComparer.Ordinal).Select(p => p.Key + "\0" + p.Value + "\n"));
            string sourceId = Hash(Encoding.UTF8.GetBytes(canonical));
            Check(recipe.GetProperty("source_id").GetString() == sourceId && original.GetProperty("source_id").GetString() == sourceId,
                "Original source identity is unchanged and canonical");
            var expectedTools = new HashSet<string>(new[] {"Cabrillo.Bootstrap.dll", "Celeste.Mod.mm.dll", "NETCoreifier.dll", "FNA.dll"}, StringComparer.Ordinal);
            expectedTools.UnionWith(assemblies.Select(Path.GetFileName).Where(n => n.StartsWith("Mono", StringComparison.Ordinal)));
            var tools = recipe.GetProperty("tools").EnumerateObject().ToDictionary(p => p.Name, p => p.Value.GetString(), StringComparer.Ordinal);
            Check(expectedTools.SetEquals(tools.Keys), "Preparation recipe covers patch/FNA/bootstrap/Mono tools exactly");
            foreach (var tool in tools)
                Check(Digest(tool.Value) && Hash(File.ReadAllBytes(Path.Combine(managed, tool.Key))) == tool.Value, "Recipe hash matches: " + tool.Key);
            var report = new {status="PASS_EVEREST6642_COMPILED_MANAGED_AUDIT", version=Version, source_commit=Commit,
                version_string=VersionString, runtime_manifest_sha256=runtimeHash, original_source_id=sourceId,
                recipe_sha256=Hash(File.ReadAllBytes(args[1])), recipe_tools=tools, managed_assemblies=assemblies.Length,
                checks=Checks, game_or_adapter_executed=false, native_runtime_executed=false, physical_device_tested=false};
            File.WriteAllText(args[4], JsonSerializer.Serialize(report, new JsonSerializerOptions {WriteIndented=true}) + "\n");
            Console.WriteLine("PASS_EVEREST6642_COMPILED_MANAGED_AUDIT checks=" + Checks.Count);
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine("FAIL_EVEREST6642_MANAGED_AUDIT: " + error.Message);
            Console.Error.WriteLine(error.StackTrace);
            return 2;
        }
    }
}

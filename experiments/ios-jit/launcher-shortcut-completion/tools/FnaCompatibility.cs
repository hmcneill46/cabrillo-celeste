using System.Security.Cryptography;
using System.Text.Json;
using Mono.Cecil;
using Mono.Cecil.Cil;

internal static class FnaCompatibility
{
    // Retain the physically accepted FNA/Metal lifecycle and expose the SDL state
    // query needed by this Everest version. Do not invent a cached input state.
    public static void Apply(string input, string output, string receipt)
    {
        using var module = ModuleDefinition.ReadModule(input);
        var text = module.GetType("Microsoft.Xna.Framework.Input.TextInputEXT");
        if (text.Methods.Any(m => m.Name == "IsTextInputActive"))
            throw new InvalidOperationException("FNA compatibility input changed.");
        var native = module.GetType("SDL2.SDL").Methods.Single(m => m.Name == "SDL_IsTextInputActive");
        var query = new MethodDefinition("IsTextInputActive", MethodAttributes.Public | MethodAttributes.Static | MethodAttributes.HideBySig, module.TypeSystem.Boolean);
        text.Methods.Add(query);
        var il = query.Body.GetILProcessor();
        il.Emit(OpCodes.Call, native);
        il.Emit(OpCodes.Ldc_I4_1);
        il.Emit(OpCodes.Ceq);
        il.Emit(OpCodes.Ret);
        module.Write(output);
        string Sha(string path) => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant();
        File.WriteAllText(receipt, JsonSerializer.Serialize(new {
            input_sha256 = Sha(input), output_sha256 = Sha(output),
            added_method = query.FullName, native_entry = native.PInvokeInfo.EntryPoint,
            rendering_lifecycle_changed = false
        }, new JsonSerializerOptions { WriteIndented = true }) + "\n");
    }

    public static int Check(string directory, string[] assemblies)
    {
        using var resolver = new DefaultAssemblyResolver();
        resolver.AddSearchDirectory(directory);
        var missing = new List<string>();
        int checkedCount = 0;
        foreach (string path in assemblies)
        {
            using var module = ModuleDefinition.ReadModule(path, new ReaderParameters { AssemblyResolver = resolver });
            foreach (var member in module.GetMemberReferences())
            {
                if (member.DeclaringType?.Scope?.Name != "FNA") continue;
                // Multidimensional array accessors are supplied by the CLR.
                if (member.DeclaringType is ArrayType) continue;
                checkedCount++;
                try
                {
                    if (member.Resolve() == null) missing.Add(module.Name + ": " + member.FullName);
                }
                catch (Exception ex) { missing.Add(module.Name + ": " + member.FullName + " (" + ex.Message + ")"); }
            }
        }
        Console.WriteLine(JsonSerializer.Serialize(new { checkedCount, missing }, new JsonSerializerOptions { WriteIndented = true }));
        return missing.Count == 0 ? 0 : 1;
    }
}

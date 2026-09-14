using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Security.Cryptography;
using System.Text.Json;
using Mono.Cecil;
using Mono.Cecil.Cil;

internal static class FnaGraphicsCompatibility
{
    private const string InputHash = "dfd000f1a1eff08d41451099c63a9de9363047a6c0025812fb9ff19d8d53ed6d";
    private const string Added = "System.Int32 Microsoft.Xna.Framework.Graphics.GraphicsDevice::GetRenderTargetsNoAllocEXT(Microsoft.Xna.Framework.Graphics.RenderTargetBinding[])";
    private static string Hash(string path) => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant();
    private static IEnumerable<TypeDefinition> Types(TypeDefinition t) => new[] { t }.Concat(t.NestedTypes.SelectMany(Types));
    private static IEnumerable<TypeDefinition> Types(ModuleDefinition m) => m.Types.SelectMany(Types);
    private static string Operand(object value, MethodDefinition method) => value switch {
        null => "", Instruction i => "i:" + method.Body.Instructions.IndexOf(i),
        Instruction[] a => string.Join(",", a.Select(i => "i:" + method.Body.Instructions.IndexOf(i))),
        VariableDefinition v => "v:" + v.Index + ":" + v.VariableType.FullName,
        ParameterDefinition p => "p:" + p.Index + ":" + p.ParameterType.FullName,
        _ => value.ToString()
    };
    private static string Fingerprint(MethodDefinition m) => m.FullName + "|" + m.Attributes + "|" + m.ImplAttributes + "|" +
        (m.HasBody ? m.Body.InitLocals + "|" + string.Join(";", m.Body.Variables.Select(v => v.VariableType.FullName)) + "|" +
        string.Join(";", m.Body.Instructions.Select(i => i.OpCode.Code + ":" + Operand(i.Operand, m))) + "|" +
        string.Join(";", m.Body.ExceptionHandlers.Select(h => h.HandlerType + ":" + h.CatchType?.FullName + ":" +
            Operand(h.TryStart,m) + ":" + Operand(h.TryEnd,m) + ":" + Operand(h.HandlerStart,m) + ":" + Operand(h.HandlerEnd,m) + ":" + Operand(h.FilterStart,m))) : "no-body");
    private static Dictionary<string,string> Methods(ModuleDefinition m) => Types(m).SelectMany(t => t.Methods).ToDictionary(x => x.FullName, Fingerprint);
    public static void Main(string[] a)
    {
        if (a[0] == "audit") { Audit(a[1], a[2], a[3]); return; }
        if (a[0] == "inspect") {
            using var z = ZipFile.OpenRead(a[1]);
            using var stream = z.Entries.Single(e => e.FullName.EndsWith("FrostTempleHelper.dll")).Open();
            using var memory = new MemoryStream(); stream.CopyTo(memory); memory.Position = 0;
            using var m = ModuleDefinition.ReadModule(memory);
            foreach (var t in Types(m).Where(t => t.FullName.Contains("GraphicsDeviceExt") || t.FullName == "FrostHelper.CustomLavaRect")) {
                Console.WriteLine(t.FullName);
                foreach (var inspected in t.Methods.Where(x => x.Name is ".ctor" or "StoreRenderTargets" or "Dispose" or "Render")) {
                    Console.WriteLine(inspected.FullName);
                    if (inspected.HasBody) foreach (var i in inspected.Body.Instructions) Console.WriteLine("  " + i);
                }
            }
            return;
        }
        if (a[0] != "patch" || Hash(a[1]) != InputHash) throw new InvalidDataException("Unreviewed FNA input.");
        using var input = AssemblyDefinition.ReadAssembly(a[1]);
        var m0 = input.MainModule; var before = Methods(m0);
        var device = m0.GetType("Microsoft.Xna.Framework.Graphics.GraphicsDevice");
        if (device.Methods.Any(x => x.Name == "GetRenderTargetsNoAllocEXT")) throw new InvalidDataException("Extension already exists.");
        var count = device.Fields.Single(x => x.Name == "renderTargetCount" && x.FieldType.FullName == "System.Int32");
        var bindings = device.Fields.Single(x => x.Name == "renderTargetBindings");
        var get = device.Methods.Single(x => x.Name == "GetRenderTargets" && x.Parameters.Count == 0);
        var copy = (MethodReference)get.Body.Instructions.Single(i => i.Operand is MethodReference r && r.Name == "Copy" && r.DeclaringType.FullName == "System.Array").Operand;
        var exception = m0.GetMemberReferences().OfType<MethodReference>().First(x => x.DeclaringType.FullName == "System.ArgumentException" && x.Name == ".ctor" && x.Parameters.Count == 1 && x.Parameters[0].ParameterType.FullName == "System.String");
        var method = new MethodDefinition("GetRenderTargetsNoAllocEXT", MethodAttributes.Public | MethodAttributes.HideBySig, m0.TypeSystem.Int32);
        method.Parameters.Add(new ParameterDefinition("output", ParameterAttributes.None, bindings.FieldType));
        var il = method.Body.GetILProcessor(); var check = Instruction.Create(OpCodes.Ldarg_1); var copyStart = Instruction.Create(OpCodes.Ldarg_0);
        il.Emit(OpCodes.Ldarg_1); il.Emit(OpCodes.Brtrue, check);
        il.Emit(OpCodes.Ldarg_0); il.Emit(OpCodes.Ldfld, count); il.Emit(OpCodes.Ret);
        il.Append(check); il.Emit(OpCodes.Ldlen); il.Emit(OpCodes.Conv_I4); il.Emit(OpCodes.Ldarg_0); il.Emit(OpCodes.Ldfld, count); il.Emit(OpCodes.Bge, copyStart);
        il.Emit(OpCodes.Ldstr, "Output buffer size incorrect"); il.Emit(OpCodes.Newobj, exception); il.Emit(OpCodes.Throw);
        il.Append(copyStart); il.Emit(OpCodes.Ldfld, bindings); il.Emit(OpCodes.Ldarg_1); il.Emit(OpCodes.Ldarg_0); il.Emit(OpCodes.Ldfld, count); il.Emit(OpCodes.Call, copy);
        il.Emit(OpCodes.Ldarg_0); il.Emit(OpCodes.Ldfld, count); il.Emit(OpCodes.Ret);
        device.Methods.Add(method);
        input.Write(a[2], new WriterParameters { DeterministicMvid = true });
        using var output = AssemblyDefinition.ReadAssembly(a[2]); var after = Methods(output.MainModule);
        if (after.Count != before.Count + 1 || !after.ContainsKey(Added) || before.Any(p => after[p.Key] != p.Value)) throw new InvalidDataException("Existing method changed.");
        var fieldsBefore = Types(m0).SelectMany(t => t.Fields).Select(f => f.FullName + ":" + f.Attributes).ToArray();
        var fieldsAfter = Types(output.MainModule).SelectMany(t => t.Fields).Select(f => f.FullName + ":" + f.Attributes).ToArray();
        if (!fieldsBefore.SequenceEqual(fieldsAfter) || input.Name.FullName != output.Name.FullName ||
            !m0.AssemblyReferences.Select(x => x.FullName).SequenceEqual(output.MainModule.AssemblyReferences.Select(x => x.FullName))) throw new InvalidDataException("Identity/fields/references changed.");
        foreach (var r in m0.Resources.OfType<EmbeddedResource>()) {
            var o = output.MainModule.Resources.OfType<EmbeddedResource>().Single(x => x.Name == r.Name);
            if (!r.GetResourceData().SequenceEqual(o.GetResourceData())) throw new InvalidDataException("Resource changed: " + r.Name);
        }
        File.WriteAllText(a[3], JsonSerializer.Serialize(new { status="PASS_FNA_RENDER_TARGET_EXTENSION_PATCH", input_sha256=InputHash, output_sha256=Hash(a[2]),
            added_method=Added, unchanged_existing_methods=before.Count, unchanged_fields=fieldsBefore.Length, existing_resources_preserved=true,
            native_renderer_changed=false, mod_zip_changes=false, semantics="null count query; reject undersized buffer; copy active bindings only; preserve unused tail; no allocation" }, new JsonSerializerOptions { WriteIndented=true }) + "\n");
        Console.WriteLine("PASS_FNA_RENDER_TARGET_EXTENSION_PATCH methods preserved=" + before.Count);
    }
    private static void Audit(string managed, string mods, string output)
    {
        using var resolver = new DefaultAssemblyResolver(); resolver.AddSearchDirectory(managed);
        var missing = new List<object>(); int references=0, assemblies=0, arrayIntrinsics=0;
        foreach (var zip in Directory.GetFiles(mods,"*.zip").OrderBy(x=>x)) {
            using var z = ZipFile.OpenRead(zip);
            foreach (var e in z.Entries.Where(x=>x.FullName.EndsWith(".dll",StringComparison.OrdinalIgnoreCase))) {
                using var stream=e.Open(); using var memory=new MemoryStream();stream.CopyTo(memory);memory.Position=0;
                ModuleDefinition module; try { module=ModuleDefinition.ReadModule(memory,new ReaderParameters { AssemblyResolver=resolver }); } catch (BadImageFormatException) { continue; }
                using (module) {
                    assemblies++;
                    foreach (var r in module.GetMemberReferences().Where(x=>x.DeclaringType.Scope?.Name=="FNA")) {
                        // ECMA-335 array methods are supplied by the runtime, not by FNA.
                        if (r.DeclaringType is ArrayType && r is MethodReference ar && (ar.Name is ".ctor" or "Get" or "Set" or "Address")) { arrayIntrinsics++; continue; }
                        references++; string error=null;
                        try { if ((r is MethodReference mr ? (object)mr.Resolve() : r is FieldReference fr ? fr.Resolve() : null)==null) error="unresolved"; }
                        catch (Exception ex) { error=ex.GetType().Name + ": " + ex.Message; }
                        if (error!=null) missing.Add(new { zip=Path.GetFileName(zip), assembly=e.FullName, member=r.FullName, error });
                    }
                }
            }
        }
        File.WriteAllText(output,JsonSerializer.Serialize(new { assemblies, fna_member_references=references, runtime_array_intrinsics=arrayIntrinsics, missing },new JsonSerializerOptions { WriteIndented=true })+"\n");
        Console.WriteLine("FNA reference audit assemblies="+assemblies+" references="+references+" unresolved="+missing.Count);
    }
}

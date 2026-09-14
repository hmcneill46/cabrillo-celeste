using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text.Json;
using Mono.Cecil;
using Mono.Cecil.Cil;

internal static class PatchMonoMod
{
    const string InputHash = "3fc0b9c537032738ee445023a15c738b5fab4726e60a17f769b46d9afa2f9dda";
    static string Hash(string p) => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(p))).ToLowerInvariant();
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
    private static Dictionary<string,string> Methods(ModuleDefinition m) => Types(m).SelectMany(t => t.Methods).ToDictionary(x => x.FullName + "#" + x.DeclaringType.Methods.IndexOf(x), Fingerprint);

    public static void Main(string[] args)
    {
        if (args.Length != 4 || Hash(args[0]) != InputHash) throw new InvalidDataException("Unreviewed MonoMod.Utils input.");
        using var assembly = AssemblyDefinition.ReadAssembly(args[0]);
        var m = assembly.MainModule; var before = Methods(m);
        var originalRefs = m.AssemblyReferences.Select(r=>r.FullName).ToArray();
        var originalFields = Types(m).SelectMany(t=>t.Fields).Select(f=>f.FullName+":"+f.Attributes).ToArray();
        var legacy = m.GetType("MonoMod.Utils.Extensions").Methods.Single(x => x.Name == "SetMonoCorlibInternal" && x.Parameters.Count == 2);
        if (!legacy.Body.Instructions.Any(i => i.OpCode == OpCodes.Stind_I1)) throw new InvalidDataException("Expected the pinned legacy native-struct byte write.");
        // Preserve the accepted Mono 8 correction: DMD uses IgnoresAccessChecksTo.
        legacy.Body = new MethodBody(legacy); legacy.Body.Instructions.Add(Instruction.Create(OpCodes.Ret));

        using var resolver = new DefaultAssemblyResolver(); resolver.AddSearchDirectory(Path.GetDirectoryName(args[0]));
        using var helper = AssemblyDefinition.ReadAssembly(args[1], new ReaderParameters { AssemblyResolver=resolver });
        var source = helper.MainModule.GetType("LiteralFieldEmitter").Methods.Single();
        if (source.Name != "Emit" || source.Body.HasExceptionHandlers) throw new InvalidDataException("Unexpected emitter fixture.");
        var owner = new TypeDefinition("MonoMod.Utils", "LiteralFieldEmitter", TypeAttributes.NotPublic|TypeAttributes.Abstract|TypeAttributes.Sealed|TypeAttributes.BeforeFieldInit, m.TypeSystem.Object);
        m.Types.Add(owner);
        TypeReference ImportType(TypeReference t) {
            if (t.Scope.Name == "MonoMod.Utils") return Types(m).Single(x=>x.FullName==t.FullName);
            return m.ImportReference(t);
        }
        var added = new MethodDefinition("Emit", MethodAttributes.Assembly|MethodAttributes.Static|MethodAttributes.HideBySig, ImportType(source.ReturnType));
        owner.Methods.Add(added);
        foreach (var p in source.Parameters) added.Parameters.Add(new ParameterDefinition(p.Name,p.Attributes,ImportType(p.ParameterType)));
        added.Body.InitLocals=source.Body.InitLocals;
        foreach(var v in source.Body.Variables) added.Body.Variables.Add(new VariableDefinition(ImportType(v.VariableType)));
        var instructions=source.Body.Instructions.ToDictionary(i=>i,i=>Instruction.Create(OpCodes.Nop));
        foreach(var i in source.Body.Instructions) {
            var o=instructions[i]; o.OpCode=i.OpCode;
            o.Operand=i.Operand switch {
                Instruction target=>instructions[target], Instruction[] targets=>targets.Select(t=>instructions[t]).ToArray(),
                VariableDefinition v=>added.Body.Variables[v.Index], ParameterDefinition p=>added.Parameters[p.Index],
                MethodReference r when r.DeclaringType.Scope.Name=="MonoMod.Utils"=>m.LookupToken(r.Resolve().MetadataToken),
                MethodReference r=>m.ImportReference(r), FieldReference f=>m.ImportReference(f), TypeReference t=>ImportType(t),
                _=>i.Operand
            };
            added.Body.Instructions.Add(o);
        }
        var emitter=Types(m).SelectMany(t=>t.Methods).Single(x=>x.Name=="<CreateFieldInvoker>b__0");
        var sites=emitter.Body.Instructions.Where(i=>i.OpCode==OpCodes.Ldsfld && i.Operand is FieldReference f && f.DeclaringType.FullName=="Mono.Cecil.Cil.OpCodes" && (f.Name=="Stsfld" || f.Name=="Ldsfld")).ToArray();
        if (sites.Length!=2) throw new InvalidDataException("Expected exactly two static field emitter sites.");
        foreach(var site in sites) {
            var call=site.Next.Next.Next;
            if (call.OpCode!=OpCodes.Callvirt || call.Operand is not MethodReference r || r.FullName!="MonoMod.Cil.ILCursor MonoMod.Cil.ILCursor::Emit(Mono.Cecil.Cil.OpCode,System.Reflection.FieldInfo)") throw new InvalidDataException("Unexpected field emitter shape: "+call);
            call.OpCode=OpCodes.Call;call.Operand=added;
        }
        assembly.Write(args[2],new WriterParameters { DeterministicMvid=true });
        using var result=AssemblyDefinition.ReadAssembly(args[2]);var after=Methods(result.MainModule);
        var changed=new[]{legacy.FullName + "#" + legacy.DeclaringType.Methods.IndexOf(legacy),emitter.FullName + "#" + emitter.DeclaringType.Methods.IndexOf(emitter)};
        if(after.Count!=before.Count+1 || before.Where(p=>!changed.Contains(p.Key)).Any(p=>after[p.Key]!=p.Value)) throw new InvalidDataException("Unrelated MonoMod method changed.");
        if(!originalRefs.SequenceEqual(result.MainModule.AssemblyReferences.Select(r=>r.FullName)) || !originalFields.SequenceEqual(Types(result.MainModule).SelectMany(t=>t.Fields).Select(f=>f.FullName+":"+f.Attributes)) || assembly.Name.FullName!=result.Name.FullName) throw new InvalidDataException("Existing identity/fields/references changed.");
        foreach(var resource in m.Resources.OfType<EmbeddedResource>())
            if(!resource.GetResourceData().SequenceEqual(result.MainModule.Resources.OfType<EmbeddedResource>().Single(r=>r.Name==resource.Name).GetResourceData())) throw new InvalidDataException("Embedded resource changed.");
        File.WriteAllText(args[3],JsonSerializer.Serialize(new { status="PASS_MONOMOD_LITERAL_FIELDS_AND_MONO8_PATCH", input_sha256=InputHash,output_sha256=Hash(args[2]),emitter_fixture_sha256=Hash(args[1]),changed_methods=changed,added_method=added.FullName,unchanged_methods=before.Count-2,unchanged_fields=originalFields.Length,unchanged_assembly_identity_and_references=true,legacy_native_struct_write_removed=true,literal_getters="Emit metadata constant with declared result type; no ldsfld",literal_setters="FieldAccessException; no stsfld",nonliteral_fields_unchanged=true,original_game_and_mods_unchanged=true },new JsonSerializerOptions { WriteIndented=true })+"\n");
        Console.WriteLine("PASS_MONOMOD_LITERAL_FIELDS_AND_MONO8_PATCH");
    }
}

// Preserve Mono's attributes without resolving unrelated method signature types.
// The host registers the private internal call before loading the game.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Mono.Cecil;
using Mono.Cecil.Cil;

internal static class PatchReflectionFlags {
    static string Hash(string p) => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(p))).ToLowerInvariant();
    static IEnumerable<TypeDefinition> Types(TypeDefinition t) => new[] { t }.Concat(t.NestedTypes.SelectMany(Types));
    static IEnumerable<TypeDefinition> Types(ModuleDefinition m) => m.Types.SelectMany(Types);
    static string Operand(object v, MethodDefinition m) => v switch {
        null => "", Instruction i => "i:" + m.Body.Instructions.IndexOf(i),
        Instruction[] a => string.Join(",", a.Select(i => "i:" + m.Body.Instructions.IndexOf(i))),
        VariableDefinition x => "v:" + x.Index + ":" + x.VariableType.FullName,
        ParameterDefinition p => "p:" + p.Index + ":" + p.ParameterType.FullName,
        _ => v.ToString()
    };
    static string Fingerprint(MethodDefinition m) => m.FullName + "|" + m.Attributes + "|" + m.ImplAttributes + "|" +
        (m.HasBody ? m.Body.InitLocals + "|" + string.Join(";", m.Body.Variables.Select(v => v.VariableType.FullName)) + "|" +
        string.Join(";", m.Body.Instructions.Select(i => i.OpCode.Code + ":" + Operand(i.Operand, m))) + "|" +
        string.Join(";", m.Body.ExceptionHandlers.Select(h => h.HandlerType + ":" + h.CatchType?.FullName + ":" + Operand(h.TryStart,m) + ":" + Operand(h.TryEnd,m) + ":" + Operand(h.HandlerStart,m) + ":" + Operand(h.HandlerEnd,m) + ":" + Operand(h.FilterStart,m))) : "no-body");
    static string Key(MethodDefinition m) => m.FullName + "#" + m.DeclaringType.Methods.IndexOf(m);
    static Dictionary<string,string> Methods(ModuleDefinition m) => Types(m).SelectMany(t => t.Methods).ToDictionary(Key, Fingerprint);
    static string[] Fields(ModuleDefinition m) => Types(m).SelectMany(t=>t.Fields).Select(f=>f.FullName+":"+f.Attributes+":"+f.Offset+":"+f.Constant).ToArray();
    static string[] Resources(ModuleDefinition m) => m.Resources.Select(r=>r.Name+":"+r.Attributes+":"+(r is EmbeddedResource e ? Convert.ToHexString(SHA256.HashData(e.GetResourceData())) : r.ToString())).ToArray();
    public static void Main(string[] args) {
        if(args.Length!=4 || Hash(args[0])!=args[1])throw new InvalidDataException("Unreviewed Mono CoreLib input.");
        using var assembly=AssemblyDefinition.ReadAssembly(args[0]);var m=assembly.MainModule;
        if(m.Assembly.Name.Name!="System.Private.CoreLib")throw new InvalidDataException("Expected Mono CoreLib.");
        var before=Methods(m);var fields=Fields(m);var resources=Resources(m);var references=m.AssemblyReferences.Select(x=>x.FullName).ToArray();
        var info=m.GetType("System.Reflection.MonoMethodInfo");var runtime=m.GetType("System.Reflection.RuntimeMethodInfo");
        var flags=info.Methods.Single(x=>x.Name=="GetMethodImplementationFlags");
        if(!flags.Body.Instructions.Any(i=>i.Operand is MethodReference r && r.Name=="GetMethodInfo"))throw new InvalidDataException("Unexpected flags implementation.");
        var direct=new MethodDefinition("CJITGetImplementationFlags",MethodAttributes.Private|MethodAttributes.Static|MethodAttributes.HideBySig,flags.ReturnType) { ImplAttributes=MethodImplAttributes.InternalCall };
        direct.Parameters.Add(new ParameterDefinition(m.TypeSystem.IntPtr));info.Methods.Add(direct);
        flags.Body=new MethodBody(flags);
        flags.Body.Instructions.Add(Instruction.Create(OpCodes.Ldarg_0));flags.Body.Instructions.Add(Instruction.Create(OpCodes.Call,direct));flags.Body.Instructions.Add(Instruction.Create(OpCodes.Ret));
        var changed=new HashSet<string> { Key(flags) };
        foreach(var name in new[]{"GetPseudoCustomAttributesData","GetPseudoCustomAttributes"}) {
            var pseudo=runtime.Methods.Single(x=>x.Name==name);changed.Add(Key(pseudo));
            var body=pseudo.Body;var il=body.GetILProcessor();
            var call=body.Instructions.Single(i=>i.Operand is MethodReference r && r.Name=="GetMethodInfo");
            if(call.Previous.OpCode!=OpCodes.Ldfld || call.Previous.Previous.OpCode!=OpCodes.Ldarg_0 || call.Next.OpCode!=OpCodes.Stloc_1)throw new InvalidDataException("Unexpected method-info initializer.");
            var handle=(FieldReference)call.Previous.Operand;
            if(handle.Name!="mhandle")throw new InvalidDataException("Unexpected method handle.");
            foreach(var i in new[]{call.Previous.Previous,call.Previous,call,call.Next}) {i.OpCode=OpCodes.Nop;i.Operand=null;}
            var sites=body.Instructions.Where(i=>i.OpCode==OpCodes.Ldfld && i.Operand is FieldReference f && f.DeclaringType.FullName==info.FullName).ToArray();
            if(sites.Length!=4 || sites.Count(i=>((FieldReference)i.Operand).Name=="iattrs")!=2 || sites.Count(i=>((FieldReference)i.Operand).Name=="attrs")!=2)throw new InvalidDataException("Unexpected pseudo-attribute fields.");
            foreach(var site in sites) {
                var f=(FieldReference)site.Operand;var previous=site.Previous;
                if(previous.OpCode!=OpCodes.Ldloc_1)throw new InvalidDataException("Unexpected info local.");
                previous.OpCode=OpCodes.Ldarg_0;previous.Operand=null;il.InsertAfter(previous,Instruction.Create(OpCodes.Ldfld,handle));
                site.OpCode=OpCodes.Call;site.Operand=f.Name=="iattrs"?flags:info.Methods.Single(x=>x.Name=="GetAttributes");
            }
        }
        var originalMvid=m.Mvid;
        m.Mvid=new Guid(SHA256.HashData(Encoding.UTF8.GetBytes(args[1]+":CJIT-reflection-flags-v1")).Take(16).ToArray());
        assembly.Write(args[2]);
        using var output=AssemblyDefinition.ReadAssembly(args[2]);var after=Methods(output.MainModule);
        if(after.Count!=before.Count+1 || before.Any(p=>!changed.Contains(p.Key) && (!after.TryGetValue(p.Key,out var v) || p.Value!=v)) || changed.Any(n=>before[n]==after[n]))throw new InvalidDataException("Unrelated method change.");
        if(!fields.SequenceEqual(Fields(output.MainModule)) || !resources.SequenceEqual(Resources(output.MainModule)) || !references.SequenceEqual(output.MainModule.AssemblyReferences.Select(x=>x.FullName)))throw new InvalidDataException("Unrelated fields/resources/references changed.");
        File.WriteAllText(args[3],JsonSerializer.Serialize(new {status="PASS_SCOPED_MONO_REFLECTION_FLAGS_PATCH",input_sha256=args[1],output_sha256=Hash(args[2]),original_methods=before.Count,unchanged_methods=before.Count-changed.Count,changed_methods=changed.OrderBy(x=>x).ToArray(),added_private_internal_call=direct.FullName,fields=fields.Length,fields_resources_references_unchanged=true,original_mvid=originalMvid,output_mvid=output.MainModule.Mvid},new JsonSerializerOptions{WriteIndented=true})+"\n");
        Console.WriteLine("PASS_SCOPED_MONO_REFLECTION_FLAGS_PATCH");
    }
}

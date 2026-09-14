using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text.Json;
using Mono.Cecil;
using Mono.Cecil.Cil;
internal static class PatchFnaBackbuffer
{
    const string InputHash = "e89f3b998229e04a6e596e548498e57214d23d97f753b633ea0d59c0bdfab79b";
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

    public static void Main(string[] a)
    {
        if (a.Length!=4 || Hash(a[0])!=InputHash) throw new InvalidDataException("Unreviewed FNA backbuffer input");
        using var input=AssemblyDefinition.ReadAssembly(a[0]); var m=input.MainModule; var before=Methods(m);
        var fields=Types(m).SelectMany(t=>t.Fields).Select(f=>f.FullName+":"+f.Attributes).ToArray();
        var references=m.AssemblyReferences.Select(r=>r.FullName).ToArray();
        using var helper=AssemblyDefinition.ReadAssembly(a[1]);
        var source=helper.MainModule.GetType("BackbufferReadGuard");
        var native=m.GetType("Microsoft.Xna.Framework.Graphics.FNA3D") ?? m.GetType("FNA3D");
        if(native==null)native=Types(m).Single(t=>t.Name=="FNA3D");
        var texture=m.GetType("Microsoft.Xna.Framework.Graphics.Texture");
        var device=m.GetType("Microsoft.Xna.Framework.Graphics.GraphicsDevice");
        var owner=new TypeDefinition("Microsoft.Xna.Framework.Graphics","CJITBackbufferRead",TypeAttributes.NotPublic|TypeAttributes.Abstract|TypeAttributes.Sealed|TypeAttributes.BeforeFieldInit,m.TypeSystem.Object);m.Types.Add(owner);
        var map=new Dictionary<string,MethodReference> {
            ["GetSize"]=native.Methods.Single(t=>t.Name=="FNA3D_GetBackbufferSize"),
            ["GetFormat"]=native.Methods.Single(t=>t.Name=="FNA3D_GetBackbufferSurfaceFormat"),
            ["NativeRead"]=native.Methods.Single(t=>t.Name=="FNA3D_ReadBackbuffer"),
            ["FormatSize"]=texture.Methods.Single(t=>t.Name=="GetFormatSize")
        };
        foreach(var name in new[]{"CheckDeviceAndData","Read"}) {
            var src=source.Methods.Single(x=>x.Name==name);
            var dst=new MethodDefinition(name,MethodAttributes.Assembly|MethodAttributes.Static|MethodAttributes.HideBySig,m.ImportReference(src.ReturnType));owner.Methods.Add(dst);map[name]=dst;
            foreach(var p in src.Parameters)dst.Parameters.Add(new ParameterDefinition(p.Name,p.Attributes,m.ImportReference(p.ParameterType)));
            dst.Body.InitLocals=src.Body.InitLocals;
            foreach(var v in src.Body.Variables)dst.Body.Variables.Add(new VariableDefinition(m.ImportReference(v.VariableType)));
            var ins=src.Body.Instructions.ToDictionary(i=>i,i=>Instruction.Create(OpCodes.Nop));
            foreach(var i in src.Body.Instructions) {
                var o=ins[i];o.OpCode=i.OpCode;o.Operand=i.Operand switch {
                    Instruction target=>ins[target],Instruction[] targets=>targets.Select(t=>ins[t]).ToArray(),
                    VariableDefinition v=>dst.Body.Variables[v.Index],ParameterDefinition p=>dst.Parameters[p.Index],
                    MethodReference r when r.DeclaringType.FullName==source.FullName=>map[r.Name],
                    MethodReference r=>m.ImportReference(r),FieldReference f=>m.ImportReference(f),TypeReference t=>m.ImportReference(t),_=>i.Operand
                };dst.Body.Instructions.Add(o);
            }
            foreach(var h in src.Body.ExceptionHandlers)dst.Body.ExceptionHandlers.Add(new ExceptionHandler(h.HandlerType) {
                TryStart=ins[h.TryStart],TryEnd=h.TryEnd==null?null:ins[h.TryEnd],HandlerStart=ins[h.HandlerStart],HandlerEnd=h.HandlerEnd==null?null:ins[h.HandlerEnd],CatchType=h.CatchType==null?null:m.ImportReference(h.CatchType)
            });
        }
        var main=device.Methods.Single(t=>t.Name=="GetBackBufferData"&&t.Parameters.Count==4);
        var one=device.Methods.Single(t=>t.Name=="GetBackBufferData"&&t.Parameters.Count==1);
        var getDisposed=device.Methods.Single(t=>t.Name=="get_IsDisposed");
        foreach(var method in new[]{main,one}) {
            var first=method.Body.Instructions[0];var il=method.Body.GetILProcessor();
            foreach(var i in new[]{Instruction.Create(OpCodes.Ldarg_0),Instruction.Create(OpCodes.Call,getDisposed),Instruction.Create(method==one?OpCodes.Ldarg_1:OpCodes.Ldarg_2),Instruction.Create(OpCodes.Call,map["CheckDeviceAndData"])})il.InsertBefore(first,i);
        }
        if(main.Body.HasExceptionHandlers || main.Body.Variables.Take(4).Any(v=>v.VariableType.FullName!="System.Int32"))throw new InvalidDataException("Unexpected readback method shape");
        var start=main.Body.Instructions.Single(i=>i.OpCode==OpCodes.Ldtoken&&i.Operand is GenericParameter);
        var index=main.Body.Instructions.IndexOf(start);
        while(main.Body.Instructions.Count>index+1)main.Body.Instructions.RemoveAt(index+1);
        // Preserve branch targets at the old Marshal.SizeOf boundary.
        start.OpCode=OpCodes.Ldarg_0;start.Operand=null;var code=main.Body.GetILProcessor();
        code.Emit(OpCodes.Ldfld,device.Fields.Single(f=>f.Name=="GLDevice"));code.Emit(OpCodes.Ldarg_2);
        for(int i=0;i<4;i++)code.Emit(OpCodes.Ldloc,main.Body.Variables[i]);
        code.Emit(OpCodes.Sizeof,main.GenericParameters[0]);
        var contains=m.ImportReference(((GenericInstanceMethod)source.Methods.Single(x=>x.Name=="Contains").Body.Instructions.Single(i=>i.Operand is MethodReference).Operand).ElementMethod);
        var generic=new GenericInstanceMethod(contains);generic.GenericArguments.Add(main.GenericParameters[0]);
        code.Emit(OpCodes.Call,generic);code.Emit(OpCodes.Ldarg_3);code.Emit(OpCodes.Ldarg,main.Parameters[3]);code.Emit(OpCodes.Call,map["Read"]);code.Emit(OpCodes.Ret);
        input.Write(a[2],new WriterParameters { DeterministicMvid=true });
        using var output=AssemblyDefinition.ReadAssembly(a[2]);var after=Methods(output.MainModule);
        var changed=new[]{main.FullName+"#"+main.DeclaringType.Methods.IndexOf(main),one.FullName+"#"+one.DeclaringType.Methods.IndexOf(one)};
        if(after.Count!=before.Count+2 || before.Where(x=>!changed.Contains(x.Key)).Any(x=>after[x.Key]!=x.Value))throw new InvalidDataException("Unrelated FNA method changed");
        if(!references.SequenceEqual(output.MainModule.AssemblyReferences.Select(r=>r.FullName)) || !fields.SequenceEqual(Types(output.MainModule).SelectMany(t=>t.Fields).Select(f=>f.FullName+":"+f.Attributes)) || input.Name.FullName!=output.Name.FullName)throw new InvalidDataException("FNA shape/references/identity changed");
        foreach(var r in m.Resources.OfType<EmbeddedResource>())if(!r.GetResourceData().SequenceEqual(output.MainModule.Resources.OfType<EmbeddedResource>().Single(x=>x.Name==r.Name).GetResourceData()))throw new InvalidDataException("Resource changed");
        File.WriteAllText(a[3],JsonSerializer.Serialize(new {status="PASS_FNA_BACKBUFFER_ARGUMENT_AND_PIN_LIFETIME_PATCH",input_sha256=InputHash,output_sha256=Hash(a[2]),helper_sha256=Hash(a[1]),changed_methods=changed,added_methods=2,unchanged_existing_methods=before.Count-2,unchanged_fields=fields.Length,identity_references_resources_preserved=true,semantics="validate actual element stride, reference-free elements, array segment and rectangle; exact native byte count; finally releases pin"},new JsonSerializerOptions {WriteIndented=true})+"\n");
        Console.WriteLine("PASS_FNA_BACKBUFFER_ARGUMENT_AND_PIN_LIFETIME_PATCH");
    }
}

using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text.Json;
using Mono.Cecil;
using Mono.Cecil.Cil;

static class PatchCecilOwnedGame
{
    static int Main(string[] args)
    {
        using var module=ModuleDefinition.ReadModule(args[0]);
        var type=module.GetType("Mono.Cecil.BaseAssemblyResolver");
        var method=type.Methods.Single(m=>m.Name=="Resolve" && m.Parameters.Count==2);
        var search=type.Methods.Single(m=>m.Name=="SearchDirectory");
        var throws=method.Body.Instructions.Where(i=>i.OpCode==OpCodes.Newobj && i.Operand is MethodReference r && r.DeclaringType.FullName=="Mono.Cecil.AssemblyResolutionException").ToArray();
        if(throws.Length!=1 || throws[0].Previous.OpCode!=OpCodes.Ldarg_1 || throws[0].Next.OpCode!=OpCodes.Throw)
            throw new InvalidDataException("Unexpected Cecil resolver failure branch");
        var original=throws[0].Previous;
        var directory=new VariableDefinition(module.TypeSystem.String);method.Body.Variables.Add(directory);method.Body.InitLocals=true;
        var ret=Instruction.Create(OpCodes.Ret);
        var il=method.Body.GetILProcessor();
        var added=new[]{
            Instruction.Create(OpCodes.Ldstr,"CJIT_PREPARED_GAME_DIRECTORY"),
            Instruction.Create(OpCodes.Call,module.ImportReference(typeof(Environment).GetMethod("GetEnvironmentVariable",new[]{typeof(string)}))),
            Instruction.Create(OpCodes.Stloc,directory),Instruction.Create(OpCodes.Ldloc,directory),
            Instruction.Create(OpCodes.Call,module.ImportReference(typeof(string).GetMethod("IsNullOrEmpty",new[]{typeof(string)}))),
            Instruction.Create(OpCodes.Brtrue,original),Instruction.Create(OpCodes.Ldarg_0),Instruction.Create(OpCodes.Ldarg_1),
            Instruction.Create(OpCodes.Ldc_I4_1),Instruction.Create(OpCodes.Newarr,module.TypeSystem.String),Instruction.Create(OpCodes.Dup),
            Instruction.Create(OpCodes.Ldc_I4_0),Instruction.Create(OpCodes.Ldloc,directory),Instruction.Create(OpCodes.Stelem_Ref),
            Instruction.Create(OpCodes.Ldarg_2),Instruction.Create(OpCodes.Callvirt,search),Instruction.Create(OpCodes.Dup),
            Instruction.Create(OpCodes.Brtrue,ret),Instruction.Create(OpCodes.Pop)};
        // Existing failure branches must enter the new fallback; branches inside the
        // fallback itself still go to the original exception when nothing resolves.
        foreach(var i in method.Body.Instructions)
            if(ReferenceEquals(i.Operand,original)) i.Operand=added[0];
        foreach(var i in added)il.InsertBefore(original,i);il.Append(ret);
        module.Write(args[1]);
        File.WriteAllText(args[2],JsonSerializer.Serialize(new{status="PASS_CECIL_OWNED_GAME_FALLBACK",changed_method=method.FullName,
            input_sha256=Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(args[0]))).ToLowerInvariant(),
            output_sha256=Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(args[1]))).ToLowerInvariant(),
            fallback_only=true,environment="CJIT_PREPARED_GAME_DIRECTORY"},new JsonSerializerOptions{WriteIndented=true}));
        return 0;
    }
}

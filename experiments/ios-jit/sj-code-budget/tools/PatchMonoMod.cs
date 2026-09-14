using System;
using System.IO;
using System.Linq;
using Mono.Cecil;
using Mono.Cecil.Cil;

internal static class PatchMonoMod
{
    public static void Main(string[] args)
    {
        using var assembly = AssemblyDefinition.ReadAssembly(args[0]);
        if (args.Length == 1)
        {
            foreach (var attr in assembly.CustomAttributes)
                Console.WriteLine(attr.AttributeType.FullName + ": " + string.Join(",", attr.ConstructorArguments.Select(a => a.Value)));
            return;
        }
        var method = assembly.MainModule.GetType("MonoMod.Utils.Extensions").Methods.Single(m =>
            m.Name == "SetMonoCorlibInternal" && m.Parameters.Count == 2);
        if (!method.Body.Instructions.Any(i => i.OpCode == OpCodes.Stind_I1))
            throw new InvalidDataException("Expected the pinned legacy native-struct byte write.");
        // Mono 8 removed corlib_internal and implements IgnoresAccessChecksTo.
        // The old guessed byte offset writes into an unrelated native field.
        // DMD already emits the supported attribute before loading its assembly.
        method.Body = new MethodBody(method);
        method.Body.Instructions.Add(Instruction.Create(OpCodes.Ret));
        assembly.Write(args[1]);
        Console.WriteLine("PASS_MONO8_NO_LEGACY_CORLIB_STRUCT_WRITE");
    }
}

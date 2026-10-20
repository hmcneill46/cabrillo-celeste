using System;
using System.IO;
using System.Linq;
using Mono.Cecil;
using Mono.Cecil.Cil;
using MonoMod;

// Build-only metadata from Everest's public stripped reference and its MIT
// patch assembly. No original Celeste implementation is needed or reconstructed.
internal sealed class ReferenceModder : MonoModder
{
    public override void ParseRules(ModuleDefinition module) { }
}

internal static class BuildReference
{
    public static void Main(string[] args)
    {
        string stripped = args[0], patch = args[1], output = args[2];
        NETCoreifier.Coreifier.ConvertToNetCore(stripped, output + ".core");
        using var modder = new ReferenceModder { InputPath=output + ".core", OutputPath=output,
            MissingDependencyThrow=false, PublicEverything=false };
        modder.Read(); modder.ReadMod(patch); modder.MapDependencies(); modder.AutoPatch();
        foreach (var type in modder.Module.GetTypes())
        foreach (var method in type.Methods.Where(m => m.HasBody))
        {
            method.Body = new MethodBody(method);
            method.Body.Instructions.Add(Instruction.Create(OpCodes.Ldnull));
            method.Body.Instructions.Add(Instruction.Create(OpCodes.Throw));
        }
        modder.Module.Resources.Clear();
        modder.Write(); File.Delete(output + ".core");
        Console.WriteLine("PASS_PUBLIC_METADATA_REFERENCE_ONLY");
    }
}

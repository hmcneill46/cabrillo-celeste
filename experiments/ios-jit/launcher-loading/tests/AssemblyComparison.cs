using System;
using System.IO;
using System.Linq;
using Mono.Cecil;
using Mono.Cecil.Cil;
using System.Security.Cryptography;
using System.Text.Json;

internal static class AssemblyComparison
{
    public static void Main(string[] args) => Write(args[0], args[1]);
    static string Operand(object? value, MethodDefinition method) => value switch {
        null => "", Instruction i => "i:" + method.Body.Instructions.IndexOf(i),
        Instruction[] a => string.Join(",", a.Select(i => "i:" + method.Body.Instructions.IndexOf(i))),
        VariableDefinition v => "v:" + v.Index + ":" + v.VariableType.FullName,
        ParameterDefinition p => "p:" + p.Index + ":" + p.ParameterType.FullName,
        _ => value.ToString() ?? ""
    };
    static string Method(MethodDefinition m) => m.FullName + "|" + m.Attributes + "|" + m.ImplAttributes + "|" +
        (m.HasBody ? m.Body.InitLocals + "|" + string.Join(";", m.Body.Variables.Select(v => v.VariableType.FullName)) + "|" +
        string.Join(";", m.Body.Instructions.Select(i => i.OpCode.Code + ":" + Operand(i.Operand, m))) + "|" +
        string.Join(";", m.Body.ExceptionHandlers.Select(h => h.HandlerType + ":" + h.CatchType?.FullName + ":" +
            Operand(h.TryStart,m) + ":" + Operand(h.TryEnd,m) + ":" + Operand(h.HandlerStart,m) + ":" + Operand(h.HandlerEnd,m) + ":" + Operand(h.FilterStart,m))) : "no-body");
    public static void Write(string path, string output)
    {
        using var m = ModuleDefinition.ReadModule(path);
        File.WriteAllText(output, JsonSerializer.Serialize(new {
            identity=m.Assembly.Name.FullName,
            references=m.AssemblyReferences.Select(x=>x.FullName),
            types=m.GetTypes().ToDictionary(t=>t.FullName,t=>t.Attributes+"|"+t.BaseType?.FullName),
            methods=m.GetTypes().SelectMany(t=>t.Methods).GroupBy(x=>x.FullName+"|generic_arity="+x.GenericParameters.Count).ToDictionary(g=>g.Key,g=>g.Select(Method).OrderBy(x=>x).ToArray()),
            fields=m.GetTypes().SelectMany(t=>t.Fields).ToDictionary(f=>f.FullName,f=>f.Attributes+"|"+f.Constant),
            resources=m.Resources.OfType<EmbeddedResource>().ToDictionary(x=>x.Name,x=>Convert.ToHexString(SHA256.HashData(x.GetResourceData())))
        }, new JsonSerializerOptions { WriteIndented=true })+"\n");
    }
}

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.Loader;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Mono.Cecil;
using Mono.Cecil.Cil;

// Reads the shipped patch DLL only as Cecil metadata. After a strict IL audit it
// clones just the pure System.Version comparison into a new, isolated assembly.
// The original Everest/game/adapter assembly and its static initializer never run.
internal static class RuntimeVersionAudit
{
    static readonly HashSet<Code> Allowed = new() {
        Code.Nop, Code.Ldarg, Code.Ldarg_S, Code.Ldarg_0, Code.Ldarg_1,
        Code.Ldloc, Code.Ldloc_S, Code.Ldloc_0, Code.Ldloc_1, Code.Ldloc_2, Code.Ldloc_3,
        Code.Stloc, Code.Stloc_S, Code.Stloc_0, Code.Stloc_1, Code.Stloc_2, Code.Stloc_3,
        Code.Ldc_I4, Code.Ldc_I4_S, Code.Ldc_I4_M1, Code.Ldc_I4_0, Code.Ldc_I4_1,
        Code.Ldc_I4_2, Code.Ldc_I4_3, Code.Ldc_I4_4, Code.Ldc_I4_5, Code.Ldc_I4_6, Code.Ldc_I4_7, Code.Ldc_I4_8,
        Code.Call, Code.Callvirt, Code.Br, Code.Br_S, Code.Brfalse, Code.Brfalse_S, Code.Brtrue, Code.Brtrue_S,
        Code.Beq, Code.Beq_S, Code.Bne_Un, Code.Bne_Un_S, Code.Bge, Code.Bge_S, Code.Bgt, Code.Bgt_S,
        Code.Ble, Code.Ble_S, Code.Blt, Code.Blt_S, Code.Ceq, Code.Cgt, Code.Cgt_Un, Code.Clt, Code.Clt_Un,
        Code.And, Code.Or, Code.Xor, Code.Ret
    };
    static readonly HashSet<string> Getters = new() { "get_Major", "get_Minor", "get_Build", "get_Revision" };
    static readonly List<string> Checks = new();
    static void Check(bool value, string message) {
        if (!value) throw new InvalidDataException(message);
        Checks.Add(message);
    }
    static string Hash(byte[] bytes) => Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
    static Version NumericVersion(string text) => new Version(text.Split('-')[0]);

    static byte[] Isolate(MethodDefinition source, out string bodyHash, out string[] getters)
    {
        Check(source.IsStatic && source.HasBody && !source.IsPInvokeImpl && source.Parameters.Count == 2 &&
              source.ReturnType.FullName == "System.Boolean" && source.Parameters.All(p => p.ParameterType.FullName == "System.Version"),
              "Actual shipped method has the pure two-Version boolean signature");
        Check(source.Body.ExceptionHandlers.Count == 0, "Comparison method has no exception handlers");
        Check(source.Body.Variables.All(v => v.VariableType.FullName is "System.Int32" or "System.Boolean"),
              "Comparison locals contain only integers or booleans");
        var calls = new HashSet<string>();
        foreach (var instruction in source.Body.Instructions) {
            Check(Allowed.Contains(instruction.OpCode.Code), "Audited comparison opcode: " + instruction.OpCode.Code);
            if (instruction.Operand is MethodReference call) {
                Check(instruction.OpCode.Code is Code.Call or Code.Callvirt && call.DeclaringType.FullName == "System.Version" &&
                      Getters.Contains(call.Name) && call.HasThis && call.Parameters.Count == 0 && call.ReturnType.FullName == "System.Int32",
                      "Only System.Version numeric getter calls are allowed");
                Check(call.DeclaringType.Scope is AssemblyNameReference scope && scope.Version == new Version(8, 0, 0, 0) &&
                      (scope.Name is "System.Runtime" or "System.Private.CoreLib"),
                      "System.Version getters resolve to the pinned NET8 core framework");
                calls.Add(call.Name);
            } else {
                Check(instruction.Operand == null || instruction.Operand is Instruction or ParameterDefinition or VariableDefinition or int or sbyte,
                      "Comparison operand contains no fields, types, strings or engine references");
            }
        }
        Check(calls.SetEquals(Getters), "All four System.Version component getters are present");
        getters = calls.OrderBy(x => x, StringComparer.Ordinal).ToArray();
        string canonical = string.Join("\n", source.Body.Instructions.Select(i => i.Offset + ":" + i.OpCode.Code + ":" + i.Operand));
        bodyHash = Hash(Encoding.UTF8.GetBytes(canonical));

        using var isolated = AssemblyDefinition.CreateAssembly(new AssemblyNameDefinition("RuntimeDependencyVersionIsolated", new Version(1, 0, 0, 0)), "RuntimeDependencyVersionIsolated", ModuleKind.Dll);
        var module = isolated.MainModule;
        var type = new TypeDefinition("RuntimeDependencyVersionIsolated", "Comparison",
            Mono.Cecil.TypeAttributes.Public | Mono.Cecil.TypeAttributes.Abstract | Mono.Cecil.TypeAttributes.Sealed,
            module.ImportReference(typeof(object)));
        module.Types.Add(type);
        var boolean = module.ImportReference(typeof(bool));
        var integer = module.ImportReference(typeof(int));
        var target = new MethodDefinition("Satisfies", Mono.Cecil.MethodAttributes.Public | Mono.Cecil.MethodAttributes.Static, boolean);
        type.Methods.Add(target);
        foreach (var parameter in source.Parameters)
            target.Parameters.Add(new ParameterDefinition(parameter.Name, Mono.Cecil.ParameterAttributes.None, module.ImportReference(typeof(Version))));
        target.Body.InitLocals = source.Body.InitLocals;
        target.Body.MaxStackSize = source.Body.MaxStackSize;
        foreach (var variable in source.Body.Variables)
            target.Body.Variables.Add(new VariableDefinition(variable.VariableType.FullName == "System.Boolean" ? boolean : integer));
        var instructions = source.Body.Instructions.ToDictionary(i => i, _ => Instruction.Create(OpCodes.Nop));
        foreach (var item in source.Body.Instructions) {
            var copy = instructions[item];
            copy.OpCode = item.OpCode;
            copy.Operand = item.Operand switch {
                null => null,
                Instruction branch => instructions[branch],
                ParameterDefinition parameter => target.Parameters[parameter.Index],
                VariableDefinition variable => target.Body.Variables[variable.Index],
                MethodReference call => module.ImportReference(typeof(Version).GetProperty(call.Name.Substring(4)).GetMethod),
                int number => number,
                sbyte number => number,
                _ => throw new InvalidDataException("Unexpected unreviewed comparison operand")
            };
            target.Body.Instructions.Add(copy);
        }
        Check(type.Methods.Count == 1 && type.Fields.Count == 0 && !type.Methods.Any(m => m.IsConstructor),
              "Isolated comparison type has no static initializer, fields or extra method");
        Check(module.AssemblyReferences.All(a => a.Name == typeof(Version).Assembly.GetName().Name),
              "Isolated assembly references only the host core library");
        using var output = new MemoryStream();
        isolated.Write(output);
        return output.ToArray();
    }

    static void RejectedOperand(MethodDefinition source, Instruction invalid, string expected, string label)
    {
        source.Body.Instructions.Insert(0, invalid);
        bool rejected = false;
        try { _ = Isolate(source, out _, out _); }
        catch (InvalidDataException error) when (error.Message == expected) { rejected = true; }
        finally { source.Body.Instructions.Remove(invalid); }
        Check(rejected, label);
    }

    static int Main(string[] args)
    {
        try {
            if (args.Length != 3) throw new ArgumentException("Expected public patch DLL, actual native-fixture results and report paths");
            byte[] original = File.ReadAllBytes(args[0]), nativeBytes = File.ReadAllBytes(args[1]);
            using var document = JsonDocument.Parse(nativeBytes);
            var native = document.RootElement;
            Check(native.GetProperty("status").GetString() == "PASS_DEPENDENCY56_RUNTIME", "Actual production Swift runtime fixture passed");
            Check(native.GetProperty("runtimeBuiltins").GetProperty("Everest").GetString() == "1.6642.0" &&
                  native.GetProperty("runtimeBuiltins").GetProperty("EverestCore").GetString() == "1.6642.0",
                  "Native dependency fixture uses the shipped6642 builtin identities");
            using var patch = AssemblyDefinition.ReadAssembly(new MemoryStream(original));
            var everestType = patch.MainModule.GetType("Celeste.Mod.Everest") ?? throw new InvalidDataException("Missing Everest metadata");
            var versionField = everestType.Fields.Single(f => f.Name == "VersionString");
            var initializer = everestType.Methods.Single(m => m.IsConstructor && m.IsStatic);
            var write = initializer.Body.Instructions.Single(i => i.OpCode == OpCodes.Stsfld && i.Operand is FieldReference f && f.FullName == versionField.FullName);
            var value = write.Previous;
            while (value != null && value.OpCode == OpCodes.Nop) value = value.Previous;
            Check(value?.OpCode == OpCodes.Ldstr && value.Operand as string == "1.6642.0-cjit-5abd787",
                  "Actual shipped patch metadata has the exact6642 VersionString");
            var loader = patch.MainModule.GetType("Celeste.Mod.Everest/Loader") ?? throw new InvalidDataException("Missing actual Everest.Loader metadata");
            var method = loader.Methods.Single(m => m.Name == "VersionSatisfiesDependency");
            RejectedOperand(method, Instruction.Create(OpCodes.Ldsfld, versionField), "Audited comparison opcode: Ldsfld",
                            "Guard control rejects an original Everest field access before isolation or execution");
            var foreign = patch.MainModule.ImportReference(typeof(Environment).GetProperty(nameof(Environment.TickCount)).GetMethod);
            RejectedOperand(method, Instruction.Create(OpCodes.Call, foreign), "Only System.Version numeric getter calls are allowed",
                            "Guard control rejects a non-Version framework call before isolation or execution");
            byte[] isolated = Isolate(method, out string methodHash, out string[] getters);
            var comparisons = new List<object>();
            var context = new AssemblyLoadContext("AuditedVersionComparisonOnly", isCollectible: true);
            try {
                using var stream = new MemoryStream(isolated);
                var assembly = context.LoadFromStream(stream);
                var comparison = assembly.GetType("RuntimeDependencyVersionIsolated.Comparison", throwOnError: true).GetMethod("Satisfies", BindingFlags.Public | BindingFlags.Static);
                var satisfies = comparison.CreateDelegate<Func<Version, Version, bool>>();
                foreach (var row in native.GetProperty("versionRuleCases").EnumerateArray()) {
                    string installed = row.GetProperty("installed").GetString(), required = row.GetProperty("required").GetString();
                    bool swift = row.GetProperty("actual").GetBoolean();
                    bool everest = satisfies(NumericVersion(required), NumericVersion(installed));
                    Check(swift == everest, "Actual compiled Everest and native Swift agree: installed=" + installed + "; required=" + required);
                    comparisons.Add(new {installed, required, native=swift, everest});
                }
            } finally { context.Unload(); }
            Check(comparisons.Count >= 14, "Version parity covers the full native numeric/suffix/0.0/absent-component matrix");
            Check(File.ReadAllBytes(args[0]).SequenceEqual(original) && File.ReadAllBytes(args[1]).SequenceEqual(nativeBytes),
                  "Original public payload and native results remain unchanged");
            var report = new {status="PASS_DEPENDENCY56_ACTUAL_COMPILED_VERSION_PARITY", patch_sha256=Hash(original), native_results_sha256=Hash(nativeBytes),
                actual_method=method.FullName, actual_method_il_sha256=methodHash, isolated_assembly_sha256=Hash(isolated), version_getters=getters,
                comparisons, checks=Checks, isolated_comparison_body_executed=true, original_everest_assembly_loaded=false,
                original_static_initializer_executed=false, game_or_adapter_executed=false, physical_device_tested=false};
            File.WriteAllText(args[2], JsonSerializer.Serialize(report, new JsonSerializerOptions {WriteIndented=true}) + "\n");
            Console.WriteLine(report.status + " comparisons=" + comparisons.Count);
            return 0;
        } catch (Exception error) {
            Console.Error.WriteLine("FAIL_DEPENDENCY56_VERSION_PARITY: " + error);
            return 2;
        }
    }
}

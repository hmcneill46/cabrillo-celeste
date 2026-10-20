// Read only metadata from a freshly compiled public adapter; never load it.
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Mono.Cecil;
using Mono.Cecil.Cil;

public static class ControllerLifecycleMetadata
{
    public static void Main(string[] args) {
        using var module = ModuleDefinition.ReadModule(args[0]);
        var entry = module.GetType("CelesteJIT.Game.Entry") ?? throw new InvalidOperationException("Missing game entry");
        var checks = new List<string>();
        foreach (var pair in new[] { ("Suspend", "Reset", "CelesteJIT.Game.TouchPort"), ("Resume", "SuspendAudio", "CelesteJIT.Game.Platform") }) {
            var method = entry.Methods.Single(m => m.Name == pair.Item1);
            var calls = method.Body.Instructions.Where(i => i.OpCode.Code is Code.Call or Code.Callvirt).ToArray();
            var targets = calls.Where(i => i.Operand is MethodReference c && c.DeclaringType.FullName == "CelesteJIT.Game.ControllerIntegration" && c.Name == pair.Item1).ToArray();
            if (targets.Length != 1) throw new InvalidOperationException("Missing or repeated controller lifecycle call: " + pair.Item1);
            var target = targets[0];
            var other = calls.Single(i => i.Operand is MethodReference c && c.DeclaringType.FullName == pair.Item3 && c.Name == pair.Item2);
            bool correct = pair.Item1 == "Suspend" ? target.Offset < other.Offset : target.Offset > other.Offset;
            if (!correct) throw new InvalidOperationException("Wrong controller lifecycle call order: " + pair.Item1);
            checks.Add("actual Entry." + pair.Item1 + " calls ControllerIntegration." + pair.Item1 + " once in the required order");
            if (pair.Item1 == "Resume") {
                var clock = calls.Single(i => i.Operand is MethodReference c && c.Name == "ResetElapsedTime");
                var active = method.Body.Instructions.Single(i => i.OpCode.Code == Code.Stsfld && i.Operand is FieldReference f && f.Name == "state");
                if (target.Offset <= clock.Offset || target.Offset >= active.Offset) throw new InvalidOperationException("Resume signal must follow clock reset and precede active state");
                checks.Add("actual Entry.Resume signals controller after clock reset and before active game state");
            }
        }
        var controller = module.GetType("CelesteJIT.Game.ControllerIntegration") ?? throw new InvalidOperationException("Missing controller integration");
        foreach (var name in new[] { "Suspend", "Resume" }) {
            var method = controller.Methods.Single(m => m.Name == name && m.IsPublic && m.IsStatic);
            if (method.Parameters.Count != 0 || method.ReturnType.FullName != "System.Void") throw new InvalidOperationException("Wrong controller lifecycle API");
            checks.Add("actual controller exposes parameterless static " + name);
        }
        File.WriteAllText(args[1], JsonSerializer.Serialize(new { status = "PASS_CONTROLLER59_ACTUAL_ADAPTER_WIRING", checks, assembly_loaded_or_executed = false }, new JsonSerializerOptions { WriteIndented = true }) + "\n");
        Console.WriteLine("PASS_CONTROLLER59_ACTUAL_ADAPTER_WIRING checks=" + checks.Count);
    }
}

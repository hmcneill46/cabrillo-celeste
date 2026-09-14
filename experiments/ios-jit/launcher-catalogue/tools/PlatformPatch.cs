using System.Text.Json;
using Mono.Cecil;
using Mono.Cecil.Cil;
using Mono.Cecil.Rocks;

internal static class PlatformPatch
{
    internal static void Apply(string input, string output, string receiptPath)
    {
        using var module = ModuleDefinition.ReadModule(input);
        var edits = new List<string>();
        var adapter = new AssemblyNameReference("CelesteJITEverest", new Version(1, 0, 0, 0));
        module.AssemblyReferences.Add(adapter);
        var platform = new TypeReference("CelesteJIT.Game", "Platform", module, adapter);

        MethodReference Bridge(string name, TypeReference result, params TypeReference[] args)
        {
            var method = new MethodReference(name, result, platform) { HasThis = false };
            foreach (var arg in args) method.Parameters.Add(new ParameterDefinition(arg));
            return method;
        }

        MethodDefinition Method(string type, string name) => module.GetType(type).Methods.Single(m => m.Name == name);

        void Replace(string type, string name, MethodReference target)
        {
            var method = Method(type, name);
            if (method.Parameters.Count != 0) throw new InvalidOperationException(method.FullName);
            method.Body = new MethodBody(method);
            method.Body.Instructions.Add(Instruction.Create(OpCodes.Call, target));
            method.Body.Instructions.Add(Instruction.Create(OpCodes.Ret));
            edits.Add("replace " + method.FullName + " -> " + target.FullName);
        }

        Replace("Monocle.Engine", "get_ContentDirectory", Bridge("GetContentRoot", module.TypeSystem.String));
        Replace("Celeste.Mod.Everest", "get_PathEverest", Bridge("GetModRoot", module.TypeSystem.String));
        Replace("Monocle.ErrorLog", "GetLogPath", Bridge("GetErrorLogPath", module.TypeSystem.String));
        Replace("Monocle.ErrorLog", "Open", Bridge("ReportErrorLog", module.TypeSystem.Void));
        Replace("Celeste.Settings", "ApplyScreen", Bridge("ApplyScreen", module.TypeSystem.Void));
        var contentInit = module.GetTypes().Single(t => t.FullName == "Celeste.Mod.Everest/Content").Methods.Single(m => m.Name == "Initialize");
        contentInit.Body.GetILProcessor().InsertBefore(contentInit.Body.Instructions[0],
            Instruction.Create(OpCodes.Call, Bridge("PrepareContent", module.TypeSystem.Void)));
        edits.Add("set original ContentManager root before Everest wraps it");

        var internalModule = module.ModuleReferences.FirstOrDefault(m => m.Name == "__Internal");
        if (internalModule == null) { internalModule = new ModuleReference("__Internal"); module.ModuleReferences.Add(internalModule); }
        int fmodImports = 0;
        foreach (var type in module.GetTypes())
        foreach (var method in type.Methods)
        {
            if (method.PInvokeInfo is { } pinvoke && pinvoke.Module.Name is "fmod" or "fmodstudio" or "fmod64" or "fmodstudio64")
            {
                pinvoke.Module = internalModule;
                fmodImports++;
            }
        }
        if (fmodImports < 480) throw new InvalidOperationException("Unexpected original FMOD import surface: " + fmodImports);
        edits.Add("static FMOD imports: " + fmodImports);

        // The linked iOS 1.10.09 SDK does not export this later optional query.
        var cpu = Method("FMOD.DSP", "FMOD_DSP_GetCPUUsage");
        int unsupported = Convert.ToInt32(module.GetType("FMOD.RESULT").Fields.Single(f => f.Name == "ERR_UNSUPPORTED").Constant);
        cpu.PInvokeInfo = null;
        // Cecil's PInvokeInfo setter sets PInvokeImpl even when assigned null.
        // Clear the flag afterwards, or reflection sees an absent ImplMap row.
        cpu.IsPInvokeImpl = false;
        cpu.IsIL = true;
        cpu.IsManaged = true;
        cpu.Body = new MethodBody(cpu);
        foreach (var param in cpu.Parameters.Where(p => p.ParameterType is ByReferenceType))
        {
            cpu.Body.Instructions.Add(Instruction.Create(OpCodes.Ldarg, param));
            cpu.Body.Instructions.Add(Instruction.Create(OpCodes.Ldc_I4_0));
            cpu.Body.Instructions.Add(Instruction.Create(OpCodes.Stind_I4));
        }
        cpu.Body.Instructions.Add(Instruction.Create(OpCodes.Ldc_I4, unsupported));
        cpu.Body.Instructions.Add(Instruction.Create(OpCodes.Ret));
        edits.Add("unsupported optional FMOD_DSP_GetCPUUsage returns " + unsupported);

        int latencyCalls = 0, priorityCalls = 0;
        foreach (var type in module.GetTypes())
        foreach (var method in type.Methods.Where(m => m.HasBody))
        {
            var il = method.Body.GetILProcessor();
            foreach (var instruction in method.Body.Instructions.ToArray())
            {
                if (instruction.OpCode != OpCodes.Call && instruction.OpCode != OpCodes.Callvirt) continue;
                if (instruction.Operand is not MethodReference call) continue;
                if (call.DeclaringType.FullName == "System.Runtime.GCSettings" && call.Name == "set_LatencyMode")
                {
                    instruction.OpCode = OpCodes.Pop;
                    instruction.Operand = null;
                    latencyCalls++;
                    edits.Add("Mono default GC latency: " + method.FullName);
                }
                if (call.DeclaringType.FullName == "System.Threading.Thread" && call.Name == "set_Priority")
                {
                    instruction.OpCode = OpCodes.Pop;
                    instruction.Operand = null;
                    il.InsertAfter(instruction, Instruction.Create(OpCodes.Pop));
                    priorityCalls++;
                    edits.Add("platform default worker priority: " + method.FullName);
                }
            }
        }
        if (latencyCalls != 1) throw new InvalidOperationException("Unexpected latency sites: " + latencyCalls);

        // Everest's precision patch widens the acceleration multiplier but
        // leaves DeltaTime single-width on the IL stack. Mono 8 does not widen
        // mixed floating operands like CoreCLR does. Make both widths explicit,
        // retain the double calculation, then pass the required float argument.
        int precisionSites = 0;
        foreach (var type in module.GetTypes().Where(t => t.FullName.StartsWith("Celeste.Player", StringComparison.Ordinal)))
        foreach (var method in type.Methods.Where(m => m.HasBody && m.Body.Instructions.Any(i => i.OpCode == OpCodes.Conv_R8)))
        {
            var body = method.Body;
            body.SimplifyMacros();
            var il = body.GetILProcessor();
            foreach (var call in body.Instructions.ToArray())
            {
                if (call.Operand is not MethodReference target || target.DeclaringType.FullName != "Monocle.Calc" || target.Name != "Approach") continue;
                var multiply = call.Previous;
                if (multiply?.OpCode != OpCodes.Mul || multiply.Previous?.Operand is not MethodReference delta || delta.DeclaringType.FullName != "Monocle.Engine" || delta.Name != "get_DeltaTime") continue;
                il.InsertBefore(multiply, Instruction.Create(OpCodes.Conv_R8));
                il.InsertBefore(call, Instruction.Create(OpCodes.Conv_R4));
                precisionSites++;
                edits.Add("explicit double multiplication and float argument: " + method.FullName);
            }
            body.OptimizeMacros();
        }
        if (precisionSites == 0) throw new InvalidOperationException("Everest movement precision sites disappeared.");

        void WrapWorker(string type, string name)
        {
            var method = Method(type, name);
            var body = method.Body;
            body.SimplifyMacros();
            var il = body.GetILProcessor();
            var pool = new VariableDefinition(module.TypeSystem.IntPtr);
            body.Variables.Add(pool);
            body.InitLocals = true;
            var tryStart = body.Instructions[0];
            var end = Instruction.Create(OpCodes.Ret);
            var finallyStart = Instruction.Create(OpCodes.Ldloc, pool);
            foreach (var instruction in body.Instructions)
                if (instruction.OpCode == OpCodes.Ret) { instruction.OpCode = OpCodes.Leave; instruction.Operand = end; }
            foreach (var handler in body.ExceptionHandlers)
            {
                handler.TryEnd ??= finallyStart;
                handler.HandlerEnd ??= finallyStart;
            }
            il.InsertBefore(tryStart, Instruction.Create(OpCodes.Call, Bridge("WorkerStart", module.TypeSystem.IntPtr)));
            il.InsertBefore(tryStart, Instruction.Create(OpCodes.Stloc, pool));
            il.Append(finallyStart);
            il.Append(Instruction.Create(OpCodes.Call, Bridge("WorkerEnd", module.TypeSystem.Void, module.TypeSystem.IntPtr)));
            il.Append(Instruction.Create(OpCodes.Endfinally));
            il.Append(end);
            body.ExceptionHandlers.Add(new ExceptionHandler(ExceptionHandlerType.Finally)
            {
                TryStart = tryStart, TryEnd = finallyStart, HandlerStart = finallyStart, HandlerEnd = end
            });
            body.OptimizeMacros();
            edits.Add("worker autorelease pool/finally: " + method.FullName);
        }

        WrapWorker("Celeste.RunThread", "RunThreadWithLogging");
        WrapWorker("Celeste.Mod.Helpers.WorkerThreadTaskScheduler", "WorkerThreadFunc");

        module.Write(output);
        using (var written = ModuleDefinition.ReadModule(output))
        {
            var cpuWritten = written.GetType("FMOD.DSP").Methods.Single(m => m.Name == "FMOD_DSP_GetCPUUsage");
            if (cpuWritten.IsPInvokeImpl || !cpuWritten.HasBody)
                throw new InvalidOperationException("Optional CPU query retained invalid native metadata.");
            foreach (var method in written.GetTypes().SelectMany(t => t.Methods).Where(m => m.IsPInvokeImpl))
                if (method.PInvokeInfo == null || string.IsNullOrEmpty(method.PInvokeInfo.Module.Name) || string.IsNullOrEmpty(method.PInvokeInfo.EntryPoint))
                    throw new InvalidOperationException("Malformed native metadata: " + method.FullName);
        }
        File.WriteAllText(receiptPath, JsonSerializer.Serialize(new
        {
            status = "PASS_RECORDED_IOS_IL_ADAPTATION",
            adapter = adapter.FullName, fmodImports, latencyCalls, priorityCalls, precisionSites, edits,
            hostTested = false, deviceTested = false
        }, new JsonSerializerOptions { WriteIndented = true }) + "\n");
    }
}

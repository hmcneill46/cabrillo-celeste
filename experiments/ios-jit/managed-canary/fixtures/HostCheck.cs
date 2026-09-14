using System;
using System.Reflection;
using System.Reflection.Emit;
using CelesteJIT.Canary;
class HostCheck
{
    static void CheckSwitchIL()
    {
        byte[] il = typeof(Entry).GetMethod("SwitchCase", BindingFlags.Static | BindingFlags.NonPublic)!.GetMethodBody()!.GetILAsByteArray()!;
        for (int i = 0; i < il.Length;)
        {
            short value = il[i++] == 0xfe ? (short)(0xfe00 | il[i++]) : (short)il[i - 1];
            OpCode opcode = default;
            foreach (FieldInfo field in typeof(OpCodes).GetFields(BindingFlags.Public | BindingFlags.Static))
                if (field.GetValue(null) is OpCode candidate && candidate.Value == value) { opcode = candidate; break; }
            if (opcode == OpCodes.Switch) { Console.WriteLine("PASS: fixture SwitchCase contains an actual IL switch instruction."); return; }
            i += opcode.OperandType switch {
                OperandType.InlineNone => 0,
                OperandType.ShortInlineBrTarget or OperandType.ShortInlineI or OperandType.ShortInlineVar => 1,
                OperandType.InlineVar => 2,
                OperandType.InlineI8 or OperandType.InlineR => 8,
                OperandType.InlineSwitch => 4 + 4 * BitConverter.ToInt32(il, i),
                _ => 4
            };
        }
        throw new Exception("SwitchCase did not contain IL switch; the device regression would be ineffective.");
    }
    static void Main()
    {
        CheckSwitchIL();
        Environment.SetEnvironmentVariable("CELESTE_JIT_CANARY_NATIVE_CHECK", "build-5-native-imports");
        AppContext.SetSwitch("System.Diagnostics.Tracing.EventSource.IsSupported", false);
        int count = 0;
        foreach (int x in new[] { -100, 0, 1, 100, 999 })
        {
            if (Entry.NativeImports(x) != x + 5 || Entry.SwitchTable(x) != x + 761 || Entry.DynamicSwitch(x) != x + 168 ||
                Entry.Arithmetic(x) != unchecked((x * 31) ^ 0x13579bdf) ||
                Entry.Dynamic(x) != x * 3 + 37 || Entry.GenericAbi(x) != x * 14 + 13 ||
                Entry.ExceptionsAndGC(x) != x + 19 || Entry.ThreadAndCallback(x) != x + 24)
                throw new Exception("Canary logic failed for " + x);
            count += 8;
        }
        Console.WriteLine("PASS: " + count + " fixture logic checks on host CoreCLR. This is not iOS Mono JIT acceptance.");
    }
}

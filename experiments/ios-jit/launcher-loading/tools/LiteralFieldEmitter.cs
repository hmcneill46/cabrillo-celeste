using System;
using System.Reflection;
using Mono.Cecil.Cil;
using MonoMod.Cil;

// Compiled separately, then merged into the pinned MonoMod.Utils assembly.
// Existing validation, result boxes, caches and nonliteral fields are retained.
internal static class LiteralFieldEmitter
{
    public static ILCursor Emit(ILCursor il, OpCode opcode, FieldInfo field)
    {
        if (!field.IsLiteral) return il.Emit(opcode, field);
        if (opcode == OpCodes.Stsfld)
        {
            // The ordinary setter has already loaded the result address and value.
            // Constants have no storage; reject writes without emitting stsfld.
            il.Emit(OpCodes.Pop);
            il.Emit(OpCodes.Pop);
            il.Emit(OpCodes.Ldstr, "Cannot set literal field " + field.DeclaringType.FullName + "." + field.Name);
            il.Emit(OpCodes.Newobj, typeof(FieldAccessException).GetConstructor(new[] { typeof(string) }));
            return il.Emit(OpCodes.Throw);
        }
        if (opcode != OpCodes.Ldsfld) throw new NotSupportedException("Unexpected literal-field opcode.");
        // ECMA-335 literal constants use their metadata value, including the
        // underlying primitive for enums. The original result store supplies
        // the declared type. Null reference constants emit ldnull.
        object value = field.GetRawConstantValue();
        if (value == null) return il.Emit(OpCodes.Ldnull);
        if (value is string text) return il.Emit(OpCodes.Ldstr, text);
        if (value is bool boolean) return il.Emit(OpCodes.Ldc_I4, boolean ? 1 : 0);
        if (value is char character) return il.Emit(OpCodes.Ldc_I4, (int)character);
        if (value is sbyte i8) return il.Emit(OpCodes.Ldc_I4, (int)i8);
        if (value is byte u8) return il.Emit(OpCodes.Ldc_I4, (int)u8);
        if (value is short i16) return il.Emit(OpCodes.Ldc_I4, (int)i16);
        if (value is ushort u16) return il.Emit(OpCodes.Ldc_I4, (int)u16);
        if (value is int i32) return il.Emit(OpCodes.Ldc_I4, i32);
        if (value is uint u32) return il.Emit(OpCodes.Ldc_I4, unchecked((int)u32));
        if (value is long i64) return il.Emit(OpCodes.Ldc_I8, i64);
        if (value is ulong u64) return il.Emit(OpCodes.Ldc_I8, unchecked((long)u64));
        if (value is float f32) return il.Emit(OpCodes.Ldc_R4, f32);
        if (value is double f64) return il.Emit(OpCodes.Ldc_R8, f64);
        throw new NotSupportedException("Unsupported literal metadata type: " + value.GetType().FullName);
    }
}

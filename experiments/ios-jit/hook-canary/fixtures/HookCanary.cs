using System;
using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Threading;
using MonoMod.Cil;
using MonoMod.Core.Platforms;
using MonoMod.Core.Platforms.Systems;
using MonoMod.RuntimeDetour;
using CilOpCodes = Mono.Cecil.Cil.OpCodes;

namespace CelesteJIT.Hooks;

public static class Entry
{
    [DllImport("CJHookNative")] private static extern void CJHookMark([MarshalAs(UnmanagedType.LPUTF8Str)] string stage, int state, int actual, int expected);
    [DllImport("CJHookNative")] private static extern int CJHookMethodLayout(IntPtr method);
    private delegate int OrigInt(int value);
    private delegate int IntHook(OrigInt orig, int value);
    private delegate int OrigInstance(Box self, int value);
    private delegate int InstanceHook(OrigInstance orig, Box self, int value);
    private delegate Big OrigBig(Box self, int value);
    private delegate Big BigHook(OrigBig orig, Box self, int value);
    private delegate Pair OrigPair(Pair value, double add);
    private delegate Pair PairHook(OrigPair orig, Pair value, double add);
    private delegate int OrigGeneric(int value, int add);
    private delegate int GenericHook(OrigGeneric orig, int value, int add);
    private static Hook? keptHook;
    private static ILHook? keptIL;
    private static int phase;
    private static int checks;

    public struct Big { public long A, B, C, D; }
    public struct Pair { public double X, Y; }
    public sealed class Box
    {
        public readonly int Bias;
        public Box(int bias) => Bias = bias;
        [MethodImpl(MethodImplOptions.NoInlining)] public int Add(int value) => Bias + value;
        [MethodImpl(MethodImplOptions.NoInlining)] public Big Value(int value) => new Big { A = Bias, B = value, C = Bias + value, D = value * 2 };
    }
    public static class Generic<T> where T : struct
    {
        [MethodImpl(MethodImplOptions.NoInlining)] public static int Value(T value, int add) => value.GetHashCode() + add * 2;
    }
    [MethodImpl(MethodImplOptions.NoInlining)] private static int Target(int value) => value * 3 + 7;
    [MethodImpl(MethodImplOptions.NoInlining)] private static int CallTarget(int value) => Target(value);
    [MethodImpl(MethodImplOptions.NoInlining)] private static int ILTarget(int value) => value + 5;
    [MethodImpl(MethodImplOptions.NoInlining)] private static int Persistent(int value) => value * 5 + 1;
    [MethodImpl(MethodImplOptions.NoInlining)] private static int PersistentIL(int value) => value + 8;
    [MethodImpl(MethodImplOptions.NoInlining)] private static int ExceptionTarget(int value) => value < 0 ? throw new InvalidOperationException("hook-exception-sentinel") : value + 1;
    [MethodImpl(MethodImplOptions.NoInlining)] private static Pair PairTarget(Pair value, double add) => new Pair { X = value.X + add, Y = value.Y + add * 2 };
    private static MethodInfo Method(string name) => typeof(Entry).GetMethod(name, BindingFlags.Static | BindingFlags.NonPublic)!;
    private static void Start(string stage) => CJHookMark(stage, 0, 0, 0);
    private static void Check(string name, int actual, int expected)
    {
        bool passed = actual == expected;
        CJHookMark(name, passed ? 1 : -1, actual, expected);
        if (!passed) throw new InvalidOperationException($"{name}: got {actual}, expected {expected}");
        checks++;
    }
    private static void ReplaceConstant(ILContext context, int oldValue, int newValue)
    {
        var cursor = new ILCursor(context);
        if (!cursor.TryGotoNext(i => i.MatchLdcI4(oldValue))) throw new InvalidOperationException("Expected IL constant was absent");
        cursor.Remove(); cursor.Emit(CilOpCodes.Ldc_I4, newValue);
    }
    private static void DynamicHandle(int value, bool resumed)
    {
        Start(resumed ? "dynamic_handle_after_resume" : "dynamic_handle");
        var method = new DynamicMethod(resumed ? "CJIT_HookResume_Dynamic" : "CJIT_Hook_Dynamic", typeof(int), new[] { typeof(int) }, typeof(Entry).Module, true);
        var il = method.GetILGenerator();
        il.Emit(OpCodes.Ldarg_0); il.Emit(OpCodes.Ldc_I4, resumed ? 73 : 37); il.Emit(OpCodes.Add); il.Emit(OpCodes.Ret);
        using var pin = PlatformTriple.Current.PinMethodIfNeeded(method);
        PlatformTriple.Current.Compile(method);
        var run = (Func<int, int>)method.CreateDelegate(typeof(Func<int, int>));
        Check(resumed ? "dynamic_handle_after_resume" : "dynamic_handle", run(value), value + (resumed ? 73 : 37));
        GC.KeepAlive(method);
    }

    public static int HookSetup(int x)
    {
        if (phase != 0) throw new InvalidOperationException("Hook canary may only initialize once");
        phase = 1;
        Start("platform_install");
        AppleJitSystem.Install();
        Check("mono_method_layout", CJHookMethodLayout(PlatformTriple.Current.Runtime.GetMethodHandle(Method(nameof(Target))).Value), 1);
        Check("platform_install", PlatformTriple.Current.System is AppleJitSystem ? 1 : 0, 1);
        DynamicHandle(x, false);

        Start("hook_original_and_removal");
        Check("original_baseline", CallTarget(x), x * 3 + 7);
        using (var hook = new Hook(Method(nameof(Target)), (IntHook)((orig, value) => orig(value + 2) + 11)))
        {
            Check("hook_is_applied", hook.IsApplied ? 1 : 0, 1);
            Check("hook_original_arguments", CallTarget(x), x * 3 + 24);
            hook.Undo(); Check("hook_undo", CallTarget(x), x * 3 + 7);
            hook.Apply(); Check("hook_reapply", CallTarget(x), x * 3 + 24);
        }
        Check("hook_dispose_restores_original", CallTarget(x), x * 3 + 7);

        Start("hook_ordering");
        using (var second = new Hook(Method(nameof(Target)), (IntHook)((orig, value) => orig(value) * 2), new DetourConfig("canary.second")))
        using (var first = new Hook(Method(nameof(Target)), (IntHook)((orig, value) => orig(value) + 10), new DetourConfig("canary.first", before: new[] { "canary.second" })))
        {
            Check("before_order_overrides_creation_order", CallTarget(x), (x * 3 + 7) * 2 + 10);
            first.Undo(); Check("remove_first_in_chain", CallTarget(x), (x * 3 + 7) * 2);
            first.Apply(); Check("reinsert_first_in_chain", CallTarget(x), (x * 3 + 7) * 2 + 10);
            second.Undo(); Check("remove_second_in_chain", CallTarget(x), x * 3 + 17);
        }
        Check("chain_disposal_restores_original", CallTarget(x), x * 3 + 7);

        Start("ilhook_and_combined_hook");
        Check("il_baseline", ILTarget(x), x + 5);
        using (var ilHook = new ILHook(Method(nameof(ILTarget)), il => ReplaceConstant(il, 5, 17)))
        {
            Check("ilhook_constant_changed", ILTarget(x), x + 17);
            using var hook = new Hook(Method(nameof(ILTarget)), (IntHook)((orig, value) => orig(value) * 3));
            Check("hook_calls_modified_il", ILTarget(x), (x + 17) * 3);
            ilHook.Undo(); Check("ilhook_removal_with_hook_active", ILTarget(x), (x + 5) * 3);
        }
        Check("combined_disposal_restores_original", ILTarget(x), x + 5);

        Start("instance_and_struct_abi");
        var box = new Box(9);
        using (var hook = new Hook(typeof(Box).GetMethod(nameof(Box.Add))!, (InstanceHook)((orig, self, value) => orig(self, value + 1) + self.Bias)))
            Check("instance_this_and_original", box.Add(x), x + 19);
        Check("instance_restored", box.Add(x), x + 9);
        using (var hook = new Hook(typeof(Box).GetMethod(nameof(Box.Value))!, (BigHook)((orig, self, value) => { var result = orig(self, value); result.C += 13; return result; })))
        {
            Big value = box.Value(x);
            Check("large_struct_return", checked((int)(value.A + value.B + value.C + value.D)), x * 4 + 31);
        }
        using (var hook = new Hook(Method(nameof(PairTarget)), (PairHook)((orig, value, add) => orig(value, add + 2))))
        {
            Pair pair = PairTarget(new Pair { X = x, Y = x + 1 }, 3);
            Check("floating_struct_argument_and_return", checked((int)(pair.X + pair.Y)), x * 2 + 16);
        }

        Start("upstream_generic_hook_restriction");
        // The pinned public Hook API rejects generic source methods/types, even
        // closed ones. Verify that boundary without changing MonoMod's policy.
        bool rejected = false;
        try
        {
            using var hook = new Hook(typeof(Generic<int>).GetMethod(nameof(Generic<int>.Value))!, (GenericHook)((orig, value, add) => orig(value, add) + 7));
        }
        catch (ArgumentException error) when (error.Message == "Source method is generic, generic hooks are not supported") { rejected = true; }
        Check("generic_hook_rejected_as_documented", rejected ? 1 : 0, 1);
        Check("closed_int_generic_execution", Generic<int>.Value(x, x), x * 3);
        Check("closed_long_generic_execution", Generic<long>.Value(x, x), x * 3);

        Start("exception_and_gc_through_hook");
        using (var hook = new Hook(Method(nameof(ExceptionTarget)), (IntHook)((orig, value) =>
        {
            try { return orig(value); }
            catch (InvalidOperationException error) when (error.Message == "hook-exception-sentinel") { return 61; }
        })))
        {
            GC.Collect(); GC.WaitForPendingFinalizers(); GC.Collect();
            Check("exception_original_call", ExceptionTarget(-x), 61);
            Check("hook_survives_gc", ExceptionTarget(x), x + 1);
        }

        Start("worker_thread_calls");
        using (var hook = new Hook(Method(nameof(Target)), (IntHook)((orig, value) => orig(value) + 17)))
        {
            int passed = 0; Exception? failure = null;
            var thread = new Thread(() => { try { for (int i = 0; i < 64; i++) if (CallTarget(x + i) == (x + i) * 3 + 24) passed++; } catch (Exception error) { failure = error; } });
            thread.Start(); thread.Join();
            if (failure != null) throw new InvalidOperationException("Hook worker failed", failure);
            Check("worker_thread_64_calls", passed, 64);
        }
        Check("worker_hook_restored", CallTarget(x), x * 3 + 7);

        Start("keep_hooks_for_background");
        keptHook = new Hook(Method(nameof(Persistent)), (IntHook)((orig, value) => orig(value) + 29));
        keptIL = new ILHook(Method(nameof(PersistentIL)), il => ReplaceConstant(il, 8, 18));
        Check("persistent_hook_before_background", Persistent(x), x * 5 + 30);
        Check("persistent_ilhook_before_background", PersistentIL(x), x + 18);
        CJHookMark("initial_hook_phase_complete", 1, checks, checks);
        phase = 2;
        return x + 101;
    }

    public static int HookResume(int x)
    {
        if (phase != 2 || keptHook == null || keptIL == null) throw new InvalidOperationException("Run the initial hook phase once first");
        phase = 3;
        Start("hooks_after_background");
        Check("persistent_hook_after_background", Persistent(x), x * 5 + 30);
        Check("persistent_ilhook_after_background", PersistentIL(x), x + 18);
        GC.Collect(); GC.WaitForPendingFinalizers();
        Check("persistent_hook_after_resume_gc", Persistent(x + 1), (x + 1) * 5 + 30);
        keptHook.Dispose(); keptHook = null;
        keptIL.Dispose(); keptIL = null;
        Check("persistent_hook_removed_after_resume", Persistent(x), x * 5 + 1);
        Check("persistent_ilhook_removed_after_resume", PersistentIL(x), x + 8);
        DynamicHandle(x, true);
        Start("fresh_hooks_after_resume");
        using (var hook = new Hook(Method(nameof(Persistent)), (IntHook)((orig, value) => orig(value) + 41)))
            Check("new_hook_after_resume", Persistent(x), x * 5 + 42);
        using (var ilHook = new ILHook(Method(nameof(PersistentIL)), il => ReplaceConstant(il, 8, 28)))
            Check("new_ilhook_after_resume", PersistentIL(x), x + 28);
        Check("final_hook_original_restored", Persistent(x), x * 5 + 1);
        Check("final_il_original_restored", PersistentIL(x), x + 8);
        CJHookMark("resume_hook_phase_complete", 1, checks, checks);
        phase = 4;
        return x + 202;
    }
}

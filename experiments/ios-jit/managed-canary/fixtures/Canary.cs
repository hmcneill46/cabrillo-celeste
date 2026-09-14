using System;
using System.Reflection.Emit;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Threading;

namespace CelesteJIT.Canary;

public static class Entry
{
    [MethodImpl(MethodImplOptions.NoInlining)]
    public static int NativeImports(int x)
    {
        if (Environment.GetEnvironmentVariable("CELESTE_JIT_CANARY_NATIVE_CHECK") != "build-5-native-imports")
            throw new Exception("Native environment import did not return the host value");
        if (!AppContext.TryGetSwitch("System.Diagnostics.Tracing.EventSource.IsSupported", out bool tracing) || tracing)
            throw new Exception("EventSource configuration does not match the disabled backend");
        return x + 5;
    }

    [MethodImpl(MethodImplOptions.NoInlining)]
    public static int Arithmetic(int x) => unchecked((x * 31) ^ 0x13579bdf);

    [MethodImpl(MethodImplOptions.NoInlining)]
    private static int SwitchCase(int x)
    {
        switch (x) {
            case 0: return 41; case 1: return -7; case 2: return 93; case 3: return 12;
            case 4: return 105; case 5: return 27; case 6: return -99; case 7: return 6;
            default: return 17;
        }
    }
    [MethodImpl(MethodImplOptions.NoInlining)]
    public static int SwitchTable(int x)
    {
        for (int i = -1; i <= 8; i++) x += (i + 2) * SwitchCase(i);
        return x;
    }

    [MethodImpl(MethodImplOptions.NoInlining)]
    public static int Dynamic(int x)
    {
        var method = new DynamicMethod("CJIT_Dynamic_" + x, typeof(int), new[] { typeof(int) });
        var il = method.GetILGenerator();
        il.Emit(OpCodes.Ldarg_0);
        il.Emit(OpCodes.Ldc_I4_3);
        il.Emit(OpCodes.Mul);
        il.Emit(OpCodes.Ldc_I4, 37);
        il.Emit(OpCodes.Add);
        il.Emit(OpCodes.Ret);
        return ((Func<int, int>)method.CreateDelegate(typeof(Func<int, int>)))(x);
    }

    [MethodImpl(MethodImplOptions.NoInlining)]
    public static int DynamicSwitch(int x)
    {
        var method = new DynamicMethod("CJIT_DynamicSwitch_" + x, typeof(int), new[] { typeof(int) });
        var il = method.GetILGenerator();
        int[] values = { 101, 17, -22, 31, 44, 13, -2, 8 };
        Label[] labels = new Label[values.Length];
        for (int i = 0; i < labels.Length; i++) labels[i] = il.DefineLabel();
        il.Emit(OpCodes.Ldarg_0); il.Emit(OpCodes.Switch, labels);
        il.Emit(OpCodes.Ldc_I4, -11); il.Emit(OpCodes.Ret);
        for (int i = 0; i < labels.Length; i++) {
            il.MarkLabel(labels[i]); il.Emit(OpCodes.Ldc_I4, values[i]); il.Emit(OpCodes.Ret);
        }
        var run = (Func<int, int>)method.CreateDelegate(typeof(Func<int, int>));
        for (int i = -1; i <= 8; i++) x += run(i);
        return x;
    }

    public struct Mixed { public int A; public long B; public double C; }
    public struct Pair { public double A, B; }
    [MethodImpl(MethodImplOptions.NoInlining)]
    private static T Identity<T>(T value) => value;
    [MethodImpl(MethodImplOptions.NoInlining)]
    private static Mixed MixedReturn(int x) => Identity(new Mixed { A = x, B = x + 7L, C = 1.5 });
    [MethodImpl(MethodImplOptions.NoInlining)]
    private static Pair PairReturn(int x) => Identity(new Pair { A = x + 0.5, B = x * 2.0 + 0.25 });
    [MethodImpl(MethodImplOptions.NoInlining)]
    public static int GenericAbi(int x)
    {
        Mixed a = MixedReturn(x);
        Pair b = PairReturn(x);
        return a.A + (int)a.B + (int)(a.C * 2) + (int)((b.A + b.B) * 4);
    }

    [MethodImpl(MethodImplOptions.NoInlining)]
    public static int ExceptionsAndGC(int x)
    {
        var roots = new string[64];
        for (int i = 0; i < roots.Length; i++) roots[i] = "canary-" + i;
        GC.Collect();
        GC.WaitForPendingFinalizers();
        GC.Collect();
        for (int i = 0; i < roots.Length; i++)
            if (roots[i] != "canary-" + i) throw new Exception("GC root contents changed");
        int cleanup = 0;
        try { ThrowForCanary(); }
        catch (InvalidOperationException e) when (e.Message == "CJIT expected exception") { cleanup = 12; }
        finally { cleanup += 7; }
        return x + cleanup;
    }
    [MethodImpl(MethodImplOptions.NoInlining)]
    private static void ThrowForCanary() => throw new InvalidOperationException("CJIT expected exception");

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    private delegate int Callback(int value);
    [DllImport("CJCanaryNative", EntryPoint = "CJCanaryInvokeCallback", CallingConvention = CallingConvention.Cdecl)]
    private static extern int NativeRoundTrip(Callback callback, int value);
    [MethodImpl(MethodImplOptions.NoInlining)]
    private static int ReverseCallback(int x) => x + 11;
    [MethodImpl(MethodImplOptions.NoInlining)]
    public static int ThreadAndCallback(int x)
    {
        int caller = Environment.CurrentManagedThreadId, worker = caller, result = 0;
        Exception? failure = null;
        var thread = new Thread(() => {
            try { worker = Environment.CurrentManagedThreadId; result = NativeRoundTrip(ReverseCallback, x); }
            catch (Exception e) { failure = e; }
        });
        thread.IsBackground = true;
        thread.Start();
        if (!thread.Join(10000)) throw new TimeoutException("Canary worker did not finish in 10 seconds");
        if (failure != null) throw new Exception("Canary worker failed", failure);
        if (worker == caller) throw new Exception("Worker did not use a separate thread");
        return result;
    }
}

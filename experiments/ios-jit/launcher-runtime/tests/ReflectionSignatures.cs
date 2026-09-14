using System;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
public sealed class MarkerAttribute : Attribute { }
public static class ReflectionSignatures {
    [Marker] public static MissingSignature.Type Plain() => throw new NotSupportedException();
    [Marker, PreserveSig] public static MissingSignature.Type Preserved() => throw new NotSupportedException();
    [Marker, MethodImpl(MethodImplOptions.NoInlining | MethodImplOptions.NoOptimization)]
    public static MissingSignature.Type NoInline() => throw new NotSupportedException();
    [Marker] public static void Parameter(MissingSignature.Type value) => throw new NotSupportedException();
    [Marker] public static MissingSignature.Type Generic<T>() => throw new NotSupportedException();
    [DllImport("not-a-real-library", EntryPoint="unused", CharSet=CharSet.Unicode, SetLastError=true, CallingConvention=CallingConvention.Cdecl, PreserveSig=false)]
    public static extern MissingSignature.Type NativeNoPreserve();
    [DllImport("not-a-real-library", EntryPoint="unused", CharSet=CharSet.Unicode, SetLastError=true, CallingConvention=CallingConvention.Cdecl)]
    public static extern MissingSignature.Type NativePreserve();
}

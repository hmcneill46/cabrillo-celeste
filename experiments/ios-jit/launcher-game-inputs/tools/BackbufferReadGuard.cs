using System;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

// Merged into FNA at build time. The four stub calls are bound to its existing
// native/format methods. This assembly and the stubs are never distributed.
internal static class BackbufferReadGuard
{
    internal static void CheckDeviceAndData(bool disposed, Array data)
    {
        if (disposed) throw new ObjectDisposedException("GraphicsDevice");
        if (data == null) throw new ArgumentNullException(nameof(data));
    }
    internal static void Read(IntPtr device, Array data, int x, int y, int w, int h,
        int elementSize, bool references, int startIndex, int elementCount)
    {
        if (references) throw new ArgumentException("Pixel elements cannot contain managed references.", nameof(data));
        if (startIndex < 0 || startIndex > data.Length) throw new ArgumentOutOfRangeException(nameof(startIndex));
        if (elementCount < 0 || elementCount > data.Length - startIndex) throw new ArgumentOutOfRangeException(nameof(elementCount));
        GetSize(device, out int width, out int height);
        if (x < 0 || y < 0 || w <= 0 || h <= 0 || x > width || y > height || w > width - x || h > height - y)
            throw new ArgumentException("The read rectangle must be inside the backbuffer.", "rect");
        int pixelSize = FormatSize(GetFormat(device));
        if (elementSize <= 0 || pixelSize % elementSize != 0)
            throw new ArgumentException("The element size does not match the backbuffer format.", nameof(data));
        long required = (long)w * h * pixelSize;
        long available = (long)elementCount * elementSize;
        long offset = (long)startIndex * elementSize;
        if (available < required || required > int.MaxValue || offset > int.MaxValue)
            throw new ArgumentException("The selected array segment cannot hold the requested pixels.", nameof(elementCount));
        GCHandle handle = GCHandle.Alloc(data, GCHandleType.Pinned);
        try { NativeRead(device, x, y, w, h, IntPtr.Add(handle.AddrOfPinnedObject(), (int)offset), (int)required); }
        finally { handle.Free(); }
    }
    internal static bool Contains<T>() => RuntimeHelpers.IsReferenceOrContainsReferences<T>();
    private static void GetSize(IntPtr device, out int w, out int h) => throw new NotSupportedException("Build-time stub");
    private static int GetFormat(IntPtr device) => throw new NotSupportedException("Build-time stub");
    private static int FormatSize(int format) => throw new NotSupportedException("Build-time stub");
    private static void NativeRead(IntPtr device, int x, int y, int w, int h, IntPtr data, int size) => throw new NotSupportedException("Build-time stub");
}

using MonoMod.Core.Platforms;
using MonoMod.Core.Platforms.Systems;
using MonoMod.Utils;
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.InteropServices;

namespace MonoMod.Core.Platforms.Systems
{
    // Explicit embedding backend: the host owns prepared code memory and all
    // writes go through its validated aliases. No MAP_JIT or dylib extraction.
    public sealed class AppleJitSystem : ISystem
    {
        private const string Library = "CJHookNative";
        [DllImport(Library)] private static extern int CJHookEnvironment();
        [DllImport(Library)] private static extern int CJHookPatch(IntPtr target, IntPtr data, int size, IntPtr backup, int backupSize);
        [DllImport(Library)] private static extern nint CJHookReadable(IntPtr start, nint guess);
        [DllImport(Library)] private static extern IntPtr CJHookAllocate(int size, int alignment, int executable, IntPtr low, IntPtr high);
        [DllImport(Library)] private static extern int CJHookRelease(IntPtr address);
        [DllImport(Library)] private static extern int CJHookImageCount();
        [DllImport(Library)] private static extern IntPtr CJHookImageName(int index);

        private readonly bool hostTest;
        public OSKind Target => hostTest ? OSKind.OSX : OSKind.IOS;
        public SystemFeature Features => SystemFeature.RXPages;
        public Abi? DefaultAbi { get; }
        public IMemoryAllocator MemoryAllocator { get; }
        public INativeExceptionHelper? NativeExceptionHelper => null;

        public AppleJitSystem()
        {
            int environment = CJHookEnvironment();
            hostTest = environment == 2;
            if (environment != 1 && !hostTest)
                throw new PlatformNotSupportedException("The prepared Apple JIT bridge is unavailable");
            if (PlatformDetection.Runtime != RuntimeKind.Mono)
                throw new PlatformNotSupportedException("This backend requires the pinned Mono runtime");
            if (hostTest)
            {
                if (PlatformDetection.Architecture != ArchitectureKind.x86_64 || PlatformDetection.OS != OSKind.OSX)
                    throw new PlatformNotSupportedException("Host regression requires macOS x64");
                DefaultAbi = new Abi(new[] { SpecialArgumentKind.ReturnBuffer, SpecialArgumentKind.ThisPointer, SpecialArgumentKind.UserArguments }, SystemVABI.ClassifyAMD64, true);
            }
            else
            {
                if (PlatformDetection.Architecture != ArchitectureKind.Arm64 || PlatformDetection.OS != OSKind.IOS)
                    throw new PlatformNotSupportedException("Device bridge requires iOS ARM64");
                DefaultAbi = new Abi(new[] { SpecialArgumentKind.ThisPointer, SpecialArgumentKind.UserArguments }, SystemVABI.ClassifyARM64, false);
            }
            MemoryAllocator = new PreparedAllocator();
        }

        public static void Install()
        {
            var system = new AppleJitSystem();
            var architecture = PlatformTriple.CreateCurrentArchitecture(system);
            var runtime = PlatformTriple.CreateCurrentRuntime(system, architecture);
            PlatformTriple.SetPlatformTriple(new PlatformTriple(architecture, system, runtime));
        }

        public IEnumerable<string?> EnumerateLoadedModuleFiles()
        {
            int count = CJHookImageCount();
            for (int i = 0; i < count; i++) yield return Marshal.PtrToStringUTF8(CJHookImageName(i));
        }

        public nint GetSizeOfReadableMemory(IntPtr start, nint guess) => CJHookReadable(start, guess);
        public IntPtr GetNativeJitHookConfig(int runtimeMajMin) => IntPtr.Zero;

        public unsafe void PatchData(PatchTargetKind targetKind, IntPtr patchTarget, ReadOnlySpan<byte> data, Span<byte> backup)
        {
            if (data.IsEmpty) return;
            if (!backup.IsEmpty && backup.Length < data.Length) throw new ArgumentException("Backup is shorter than the patch", nameof(backup));
            fixed (byte* source = data)
            fixed (byte* old = backup)
            {
                if (CJHookPatch(patchTarget, (IntPtr)source, data.Length, (IntPtr)old, backup.Length) != 1)
                    throw new InvalidOperationException("Host rejected hook write: inspect hook_patch_rejected diagnostics");
            }
        }

        private sealed class PreparedAllocator : IMemoryAllocator
        {
            public int MaxSize => 65536;
            public bool TryAllocate(AllocationRequest request, [MaybeNullWhen(false)] out IAllocatedMemory allocated)
                => Allocate(request, IntPtr.Zero, IntPtr.Zero, out allocated);
            public bool TryAllocateInRange(PositionedAllocationRequest request, [MaybeNullWhen(false)] out IAllocatedMemory allocated)
                => Allocate(request.Base, request.LowBound, request.HighBound, out allocated);
            private bool Allocate(AllocationRequest request, IntPtr low, IntPtr high, [MaybeNullWhen(false)] out IAllocatedMemory allocated)
            {
                allocated = null;
                if (request.Size <= 0 || request.Size > MaxSize || request.Alignment <= 0 || (request.Alignment & (request.Alignment - 1)) != 0)
                    return false;
                var pointer = CJHookAllocate(request.Size, request.Alignment, request.Executable ? 1 : 0, low, high);
                if (pointer == IntPtr.Zero) return false;
                allocated = new PreparedMemory(pointer, request.Size, request.Executable);
                return true;
            }
        }

        private sealed class PreparedMemory : IAllocatedMemory
        {
            public IntPtr BaseAddress { get; private set; }
            public int Size { get; }
            public bool IsExecutable { get; }
            public unsafe Span<byte> Memory => BaseAddress != IntPtr.Zero ? new Span<byte>((void*)BaseAddress, Size) : throw new ObjectDisposedException(nameof(PreparedMemory));
            public PreparedMemory(IntPtr pointer, int size, bool executable) { BaseAddress = pointer; Size = size; IsExecutable = executable; }
            public void Dispose()
            {
                if (BaseAddress != IntPtr.Zero)
                {
                    if (CJHookRelease(BaseAddress) != 1) throw new InvalidOperationException("Unknown native hook allocation");
                    BaseAddress = IntPtr.Zero;
                }
                GC.SuppressFinalize(this);
            }
            ~PreparedMemory() { if (BaseAddress != IntPtr.Zero) _ = CJHookRelease(BaseAddress); }
        }
    }
}

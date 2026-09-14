using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace CelesteJIT.Content;

// No game or Apple bindings: exercised both in isolation and by embedded Mono.
public sealed class ContentStore
{
    public sealed record Item(string Path, long Bytes, string Sha256);
    public sealed record Result(string ContentRoot, bool Reused, long VerifiedBytes, string ArchivePrefix);
    private readonly string root, identity;
    private readonly Item[] items;
    private readonly Action<string,long,long,int> progress;
    private readonly Func<bool> cancelled;
    private readonly Func<long> availableSpace;
    public long TotalBytes { get; }
    private readonly byte[] buffer = new byte[128 * 1024];
    private const long MaxArchiveBytes = 2L * 1024 * 1024 * 1024;

    public ContentStore(string manifestFile, string trustedIdentity, string libraryRoot,
        Action<string,long,long,int> report, Func<bool> isCancelled, Func<long> freeSpace)
    {
        progress = report; cancelled = isCancelled; availableSpace = freeSpace;
        using var manifest = JsonDocument.Parse(File.ReadAllBytes(manifestFile));
        if (manifest.RootElement.GetProperty("schema").GetInt32() != 1) throw new InvalidDataException("Unknown content manifest.");
        identity = manifest.RootElement.GetProperty("aggregate_sha256").GetString();
        if (identity != trustedIdentity || identity.Length != 64 || identity.Any(c => !Uri.IsHexDigit(c))) throw new InvalidDataException("Content identity differs from this app.");
        items = manifest.RootElement.GetProperty("files").EnumerateArray().Select(x => new Item(
            x.GetProperty("path").GetString(), x.GetProperty("bytes").GetInt64(), x.GetProperty("sha256").GetString())).OrderBy(x => x.Path, StringComparer.Ordinal).ToArray();
        if (items.Length == 0 || items.Length > 10000) throw new InvalidDataException("Unexpected content file count.");
        var paths = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var canonical = new StringBuilder();
        foreach (var item in items)
        {
            if (!SafeName(item.Path, false) || !paths.Add(item.Path) || item.Bytes < 0 || item.Bytes > MaxArchiveBytes || item.Sha256.Length != 64 || item.Sha256.Any(c => !Uri.IsHexDigit(c)))
                throw new InvalidDataException("Invalid trusted content record.");
            TotalBytes = checked(TotalBytes + item.Bytes);
            canonical.Append(item.Path).Append('\0').Append(item.Bytes.ToString(CultureInfo.InvariantCulture)).Append('\0').Append(item.Sha256).Append('\n');
        }
        if (TotalBytes > 4L * 1024 * 1024 * 1024 || Hash(Encoding.UTF8.GetBytes(canonical.ToString())) != identity)
            throw new InvalidDataException("Content manifest checksum mismatch.");
        libraryRoot = Path.GetFullPath(libraryRoot);
        if (Directory.Exists(libraryRoot)) RegularDirectory(libraryRoot);
        root = Path.Combine(libraryRoot, identity);
        Directory.CreateDirectory(root); RegularDirectory(root);
    }

    public static string Hash(byte[] data) => Convert.ToHexString(SHA256.HashData(data)).ToLowerInvariant();
    private static bool SafeName(string name, bool directory)
    {
        if (string.IsNullOrEmpty(name) || name.StartsWith('/') || name.Contains('\\') || name.Contains(':') || name.Contains('\0')) return false;
        string value = directory ? name.TrimEnd('/') : name;
        return value.Length > 0 && value.Split('/').All(p => p.Length > 0 && p != "." && p != "..");
    }
    private void Cancel() { if (cancelled()) throw new OperationCanceledException("Content import cancelled."); }
    private static void RegularDirectory(string path)
    {
        var a = File.GetAttributes(path);
        if ((a & FileAttributes.ReparsePoint) != 0 || (a & FileAttributes.Directory) == 0) throw new InvalidDataException("Content directory is a link or not a directory.");
    }
    private static void CheckFileParents(string content, string relative)
    {
        RegularDirectory(content);
        string parent = content;
        foreach (string segment in relative.Split('/').SkipLast(1)) { parent = Path.Combine(parent, segment); RegularDirectory(parent); }
        if ((File.GetAttributes(Path.Combine(content, relative)) & (FileAttributes.ReparsePoint | FileAttributes.Directory)) != 0)
            throw new InvalidDataException("Content file is a link or directory.");
    }
    private long VerifyStream(Stream input, Stream output, Item item, string phase, ref long total, int completed)
    {
        using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        long length = 0;
        while (length < item.Bytes)
        {
            Cancel();
            int read = input.Read(buffer, 0, (int)Math.Min(buffer.Length, item.Bytes - length));
            if (read == 0) throw new InvalidDataException("Content file is truncated: " + item.Path);
            hash.AppendData(buffer, 0, read); output?.Write(buffer, 0, read);
            length += read; total += read; progress(phase, total, TotalBytes, completed);
        }
        if (input.ReadByte() != -1 || Convert.ToHexString(hash.GetHashAndReset()).ToLowerInvariant() != item.Sha256)
            throw new InvalidDataException("Content checksum differs: " + item.Path);
        return length;
    }
    private Result TryCache()
    {
        string pointer = Path.Combine(root, "active.json");
        if (!File.Exists(pointer)) return null;
        try
        {
            if ((File.GetAttributes(pointer) & FileAttributes.ReparsePoint) != 0) throw new InvalidDataException("Content pointer is a link.");
            using var document = JsonDocument.Parse(File.ReadAllBytes(pointer));
            string generation = document.RootElement.GetProperty("generation").GetString();
            if (!Guid.TryParseExact(generation, "N", out _) || document.RootElement.GetProperty("identity").GetString() != identity)
                throw new InvalidDataException("Invalid content pointer.");
            string generationRoot = Path.Combine(root, generation); RegularDirectory(generationRoot);
            string content = Path.Combine(generationRoot, "Content"); long bytes = 0; int count = 0;
            foreach (var item in items)
            {
                Cancel(); CheckFileParents(content, item.Path);
                using var file = File.OpenRead(Path.Combine(content, item.Path));
                if (file.Length != item.Bytes) throw new InvalidDataException("Installed content length differs.");
                VerifyStream(file, null, item, "Verifying saved game files", ref bytes, count++);
            }
            progress("Saved game files verified", bytes, TotalBytes, count);
            return new Result(content, true, bytes, null);
        }
        catch (Exception e) when (e is IOException || e is InvalidDataException || e is UnauthorizedAccessException || e is JsonException || e is KeyNotFoundException || e is InvalidOperationException)
        {
            progress("Saved files need a new import", 0, TotalBytes, 0);
            return null;
        }
    }
    // Bound central-directory allocation before ZipArchive materializes entries.
    private static void CheckEnvelope(FileStream file)
    {
        if (file.Length < 22 || file.Length > MaxArchiveBytes) throw new InvalidDataException("Select an original game ZIP no larger than 2 GiB.");
        byte[] tail = new byte[(int)Math.Min(65557, file.Length)]; file.Position = file.Length - tail.Length; file.ReadExactly(tail);
        for (int offset = tail.Length - 22; offset >= 0; offset--)
        {
            if (BitConverter.ToUInt32(tail, offset) != 0x06054b50 || offset + 22 + BitConverter.ToUInt16(tail, offset + 20) != tail.Length) continue;
            int count = BitConverter.ToUInt16(tail, offset + 10);
            long centralBytes = BitConverter.ToUInt32(tail, offset + 12), centralStart = BitConverter.ToUInt32(tail, offset + 16);
            if (BitConverter.ToUInt16(tail, offset + 4) != 0 || BitConverter.ToUInt16(tail, offset + 6) != 0 || count != BitConverter.ToUInt16(tail, offset + 8) || count == 0 || count > 20000 || centralBytes > 16 * 1024 * 1024 || centralStart + centralBytes != file.Length - tail.Length + offset)
                throw new InvalidDataException("Unsupported split, ZIP64 or oversized archive directory.");
            file.Position = 0; return;
        }
        throw new InvalidDataException("No supported ZIP directory was found.");
    }
    private Dictionary<string,ZipArchiveEntry> Entries(ZipArchive archive, out string prefix)
    {
        string anchor = "Content/" + items[0].Path;
        var candidates = archive.Entries.Where(e => e.FullName == items[0].Path || e.FullName == anchor || e.FullName.EndsWith("/" + anchor, StringComparison.Ordinal))
            .Select(e => e.FullName[..^items[0].Path.Length]).Distinct(StringComparer.Ordinal).ToArray();
        if (candidates.Length != 1) throw new InvalidDataException("Select an archive with one complete matching Celeste Content folder.");
        prefix = candidates[0];
        if (prefix.Length > 0 && !SafeName(prefix, true)) throw new InvalidDataException("Invalid archive content path.");
        var expected = items.ToDictionary(x => x.Path, StringComparer.Ordinal);
        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var found = new Dictionary<string,ZipArchiveEntry>(StringComparer.Ordinal);
        foreach (var entry in archive.Entries)
        {
            if (!entry.FullName.StartsWith(prefix, StringComparison.Ordinal)) continue;
            string name = entry.FullName[prefix.Length..]; if (name.Length == 0) continue;
            bool directory = name.EndsWith('/'); int kind = (entry.ExternalAttributes >> 16) & 0xf000;
            if (!SafeName(name, directory) || !seen.Add(name.TrimEnd('/')) || kind == 0xa000)
                throw new InvalidDataException("Unsafe or duplicate content path.");
            if (directory) { if (kind != 0 && kind != 0x4000) throw new InvalidDataException("Invalid content directory type."); continue; }
            if ((kind != 0 && kind != 0x8000) || !expected.TryGetValue(name, out var item) || entry.Length != item.Bytes)
                throw new InvalidDataException("Archive content does not match this tested game version: " + name);
            found.Add(name, entry);
        }
        if (found.Count != items.Length) throw new InvalidDataException("The archive is missing required game files.");
        return found;
    }
    private static void AtomicJson(string path, object value)
    {
        string temporary = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try
        {
            using (var file = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            { byte[] bytes = JsonSerializer.SerializeToUtf8Bytes(value); file.Write(bytes); file.Flush(true); }
            File.Move(temporary, path, true);
        }
        finally { if (File.Exists(temporary)) File.Delete(temporary); }
    }
    private void RecoverInterrupted()
    {
        foreach (string path in Directory.EnumerateDirectories(root, ".incoming-*"))
        {
            Cancel();
            if (!Guid.TryParseExact(Path.GetFileName(path)[10..], "N", out _) ||
                (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0) continue;
            string marker = Path.Combine(path, "import-owner.txt");
            if (!File.Exists(marker) || (File.GetAttributes(marker) & FileAttributes.ReparsePoint) != 0 ||
                new FileInfo(marker).Length != 64 || File.ReadAllText(marker) != identity) continue;
            // This is an uncommitted generation created by this importer. The
            // active generation and user-selected source are outside this path.
            Directory.Delete(path, true);
            progress("Recovered interrupted import", 0, TotalBytes, 0);
        }
    }
    public Result Prepare(string archivePath)
    {
        Cancel(); RecoverInterrupted(); var cached = TryCache();
        if (string.IsNullOrEmpty(archivePath) || !File.Exists(archivePath))
            return cached ?? throw new InvalidDataException("Import your Celeste game files first.");
        using var input = new FileStream(archivePath, FileMode.Open, FileAccess.Read, FileShare.Read);
        CheckEnvelope(input); using var archive = new ZipArchive(input, ZipArchiveMode.Read, true);
        var entries = Entries(archive, out string prefix);
        string generation = Guid.NewGuid().ToString("N"), work = null;
        if (cached == null && availableSpace() < TotalBytes + 64L * 1024 * 1024) throw new IOException("Not enough free space to import game files.");
        try
        {
            if (cached == null)
            {
                work = Path.Combine(root, ".incoming-" + generation); Directory.CreateDirectory(work);
                File.WriteAllText(Path.Combine(work, "import-owner.txt"), identity);
                Directory.CreateDirectory(Path.Combine(work, "Content"));
            }
            long bytes = 0; int count = 0;
            foreach (var item in items)
            {
                Cancel(); using var source = entries[item.Path].Open();
                string target = work == null ? null : Path.Combine(work, "Content", item.Path);
                if (target != null) Directory.CreateDirectory(Path.GetDirectoryName(target));
                using var output = target == null ? null : new FileStream(target, FileMode.CreateNew, FileAccess.Write, FileShare.None);
                VerifyStream(source, output, item, work == null ? "Checking selected archive" : "Importing game files", ref bytes, count++);
            }
            Cancel();
            if (cached != null) { progress("Game files ready", bytes, TotalBytes, count); return cached with { ArchivePrefix = prefix }; }
            AtomicJson(Path.Combine(work, "receipt.json"), new { schema = 1, identity, files = items.Length, bytes, archive_prefix = prefix, verified_utc = DateTime.UtcNow });
            string installed = Path.Combine(root, generation);
            Directory.Move(work, installed); work = null;
            // Commit only after every file has passed its trusted SHA-256.
            AtomicJson(Path.Combine(root, "active.json"), new { schema = 1, identity, generation });
            progress("Game files ready", bytes, TotalBytes, count);
            return new Result(Path.Combine(installed, "Content"), false, bytes, prefix);
        }
        finally { if (work != null && Directory.Exists(work)) Directory.Delete(work, true); }
    }
}

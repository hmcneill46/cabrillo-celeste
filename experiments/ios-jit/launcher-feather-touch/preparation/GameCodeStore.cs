using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using CelesteJIT.Content;

namespace Cabrillo.Preparation;

// Persistent inputs come exclusively from the owner's selected original ZIP.
// Published generations are immutable; the final pointer is the only commit.
public sealed class GameCodeStore
{
    public sealed record FilePin(long bytes, string sha256);
    public sealed record SourcePin(string source_id, string kind, Dictionary<string, FilePin> inputs);
    public sealed record Recipe(int schema, string legacy_source_id, SourcePin[] sources, Dictionary<string, string> tools);
    public sealed record Result(string Directory, bool Reused, string Recipe, string Source);
    private static readonly string[] InputNames = { "Celeste.exe", "Celeste.Content.dll", "FNA.dll", "Steamworks.NET.dll" };
    private static readonly string[] OutputNames = { "Celeste.dll", "Celeste.Content.dll", "MMHOOK_Celeste.dll", "orig/Celeste.exe" };
    private readonly string root, bundled, recipeId;
    private string original;
    private SourcePin source;
    private readonly Recipe recipe;
    private readonly Action<string> progress;
    private readonly Func<bool> cancelled;
    private readonly Func<long> availableSpace;

    public GameCodeStore(string root, string bundled, string recipePath, Action<string> progress,
        Func<bool> cancelled, Func<long> availableSpace)
    {
        this.root = Path.GetFullPath(root); this.bundled = Path.GetFullPath(bundled);
        this.progress = progress; this.cancelled = cancelled; this.availableSpace = availableSpace;
        byte[] bytes = ReadRegular(recipePath, 128 * 1024);
        recipeId = Hash(bytes);
        recipe = JsonSerializer.Deserialize<Recipe>(bytes) ?? throw new InvalidDataException("Missing game preparation recipe.");
        if (recipe.schema != 2 || recipe.sources == null || recipe.sources.Length is < 1 or > 16 ||
            recipe.tools == null || recipe.tools.Count < 5 ||
            recipe.sources.Any(s => s == null) ||
            recipe.sources.Select(s => s.source_id).Distinct(StringComparer.Ordinal).Count() != recipe.sources.Length)
            throw new InvalidDataException("Unsupported game preparation recipe.");
        foreach (var candidate in recipe.sources)
        {
            string[] expected = candidate.kind switch {
                "standard" => new[] { "Celeste.exe", "Celeste.Content.dll", "FNA.dll" },
                "empty-content" => new[] { "Celeste.exe", "FNA.dll" },
                "steam" => InputNames,
                _ => throw new InvalidDataException("Unknown game input adaptation.")
            };
            if (candidate.inputs == null || !candidate.inputs.Keys.OrderBy(x => x, StringComparer.Ordinal)
                .SequenceEqual(expected.OrderBy(x => x, StringComparer.Ordinal)))
                throw new InvalidDataException("Unsupported original game input set.");
            var canonical = new StringBuilder();
            foreach (var pair in candidate.inputs.OrderBy(x => x.Key, StringComparer.Ordinal))
            {
                var pin = pair.Value;
                if (pin == null || pin.bytes <= 0 || pin.bytes > 32 * 1024 * 1024 || !Digest(pin.sha256))
                    throw new InvalidDataException("Invalid original game identity.");
                canonical.Append(pair.Key).Append('\0').Append(pin.bytes.ToString(System.Globalization.CultureInfo.InvariantCulture))
                    .Append('\0').Append(pin.sha256).Append('\n');
            }
            if (Hash(Encoding.UTF8.GetBytes(canonical.ToString())) != candidate.source_id)
                throw new InvalidDataException("Original game identity checksum differs.");
        }
        if (!recipe.sources.Any(s => s.source_id == recipe.legacy_source_id && s.kind == "standard"))
            throw new InvalidDataException("Missing previous-version game identity.");
        foreach (var pair in recipe.tools)
        {
            if (!SimpleName(pair.Key) || !pair.Key.EndsWith(".dll", StringComparison.Ordinal) || !Digest(pair.Value))
                throw new InvalidDataException("Invalid preparation tool identity.");
            if (Hash(ReadRegular(Path.Combine(this.bundled, pair.Key), 64 * 1024 * 1024)) != pair.Value)
                throw new InvalidDataException("A game preparation component differs: " + pair.Key);
        }
        EnsureDirectory(this.root);
        EnsureDirectory(Path.Combine(this.root, "original"));

    }

    private static bool SimpleName(string name) => !string.IsNullOrEmpty(name) &&
        name != "." && name != ".." && !name.Any(c => c is '/' or '\\' or ':' or '\0');
    private static bool Digest(string text) => text?.Length == 64 && text.All(c => c is >= '0' and <= '9' or >= 'a' and <= 'f');
    public static string Hash(byte[] bytes) => Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
    private void Cancel() { if (cancelled()) throw new OperationCanceledException("Game preparation cancelled."); }
    private void Stage(string text) { Cancel(); progress(text); }
    private static void Regular(string path, bool directory)
    {
        var flags = File.GetAttributes(path);
        if ((flags & FileAttributes.ReparsePoint) != 0 || ((flags & FileAttributes.Directory) != 0) != directory)
            throw new InvalidDataException("Game preparation storage contains a link or unexpected file type.");
    }
    private static void EnsureDirectory(string path)
    {
        if (File.Exists(path) || Directory.Exists(path)) Regular(path, true);
        else Directory.CreateDirectory(path);
        Regular(path, true);
    }
    private static byte[] ReadRegular(string path, long maximum)
    {
        Regular(path, false);
        using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read);
        if (stream.Length > maximum) throw new InvalidDataException("Unexpected game preparation file size.");
        byte[] bytes = new byte[checked((int)stream.Length)]; stream.ReadExactly(bytes);
        if (stream.ReadByte() != -1) throw new IOException("A game preparation file changed during verification.");
        return bytes;
    }
    private static void WriteNew(string path, byte[] bytes)
    {
        using var stream = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None);
        stream.Write(bytes); stream.Flush(true);
    }
    private static void AtomicJson(string path, object value)
    {
        if (File.Exists(path)) Regular(path, false);
        string temporary = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
        WriteNew(temporary, JsonSerializer.SerializeToUtf8Bytes(value));
        File.Move(temporary, path, true);
    }
    private bool VerifyOriginal()
    {
        if (!Directory.Exists(original)) return false;
        Regular(original, true);
        using var marker = JsonDocument.Parse(ReadRegular(Path.Combine(original, "source.json"), 4096));
        if (marker.RootElement.GetProperty("source_id").GetString() != source.source_id)
            throw new InvalidDataException("Original game receipt differs.");
        foreach (var pair in source.inputs)
        {
            Cancel(); byte[] bytes = ReadRegular(Path.Combine(original, pair.Key), pair.Value.bytes);
            if (bytes.LongLength != pair.Value.bytes || Hash(bytes) != pair.Value.sha256)
                throw new InvalidDataException("Saved original game code differs. Import the original game ZIP again.");
        }
        return true;
    }
    private Dictionary<string, byte[]> SelectArchive(string archive, string contentPrefix)
    {
        // ContentStore discovers the root independently of the ZIP name/store/platform.
        if (!File.Exists(archive) || contentPrefix == null || !contentPrefix.EndsWith("Content/", StringComparison.Ordinal))
            throw new InvalidDataException("Import a complete original Celeste FNA 1.4.0.0 ZIP. See the game files guide.");
        string prefix = contentPrefix[..^"Content/".Length];
        if (prefix.StartsWith('/') || prefix.Contains('\\') || prefix.Split('/').Any(x => x is "." or ".."))
            throw new InvalidDataException("Invalid original game archive prefix.");
        using var file = new FileStream(archive, FileMode.Open, FileAccess.Read, FileShare.Read);
        ContentStore.CheckEnvelope(file);
        using var zip = new ZipArchive(file, ZipArchiveMode.Read, false);
        var bytes = new Dictionary<string, byte[]>();
        var pins = new Dictionary<string, FilePin>();
        foreach (string name in InputNames)
        {
            Cancel();
            var matches = zip.Entries.Where(e => e.FullName.Equals(prefix + name, StringComparison.OrdinalIgnoreCase)).ToArray();
            if (matches.Length == 0) continue;
            if (matches.Length != 1 || matches[0].FullName != prefix + name || matches[0].Length is <= 0 or > 32 * 1024 * 1024 ||
                ((matches[0].ExternalAttributes >> 16) & 0xf000) is not (0 or 0x8000))
                throw new InvalidDataException("The game ZIP contains a duplicate, invalid or incorrectly cased " + name + ".");
            using var input = matches[0].Open(); byte[] data = new byte[checked((int)matches[0].Length)]; input.ReadExactly(data);
            if (input.ReadByte() != -1) throw new InvalidDataException("The game ZIP changed during verification.");
            bytes.Add(name, data); pins.Add(name, new FilePin(data.LongLength, Hash(data)));
        }
        source = recipe.sources.SingleOrDefault(s => s.inputs.Count == pins.Count &&
            s.inputs.All(p => pins.TryGetValue(p.Key, out var actual) && actual == p.Value));
        if (source == null)
            throw new InvalidDataException("Unsupported or modified game files. Use an original Celeste FNA 1.4.0.0 ZIP from itch.io, Steam or Epic; see the game files guide.");
        return bytes;
    }
    private void SelectSaved()
    {
        string id = recipe.legacy_source_id;
        string pointer = Path.Combine(root, "selected-source.json");
        if (File.Exists(pointer))
        {
            using var record = JsonDocument.Parse(ReadRegular(pointer, 4096));
            if (record.RootElement.GetProperty("schema").GetInt32() != 1)
                throw new InvalidDataException("Saved game selection is invalid. Import the original ZIP again.");
            id = record.RootElement.GetProperty("source").GetString();
        }
        source = recipe.sources.SingleOrDefault(s => s.source_id == id) ??
            throw new InvalidDataException("This saved game edition needs a new original ZIP import.");
    }
    private void CommitSelection()
    {
        Cancel();
        AtomicJson(Path.Combine(root, "selected-source.json"), new { schema = 1, source = source.source_id });
    }
    private void ImportOriginal(Dictionary<string, byte[]> bytes)
    {
        if (bytes == null)
            throw new InvalidDataException("Import the original Celeste FNA ZIP once to prepare its game code.");
        // Only this complete, exact recognized set is copied; no ZIP assembly is executed.
        string incoming = Path.Combine(root, "original", ".incoming-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(incoming);
        foreach (var pair in bytes) WriteNew(Path.Combine(incoming, pair.Key), pair.Value);
        AtomicJson(Path.Combine(incoming, "source.json"), new { schema = 1, source_id = source.source_id });
        Cancel();
        // Retain damaged/unknown contents for inspection instead of recursively deleting them.
        if (Directory.Exists(original))
        {
            Regular(original, true);
            Directory.Move(original, original + ".retained-" + Guid.NewGuid().ToString("N"));
        }
        Directory.Move(incoming, original);
        if (!VerifyOriginal()) throw new InvalidDataException("Original game code was not committed.");
    }
    private Result TryPrepared(string generations)
    {
        string active = Path.Combine(generations, "active.json");
        if (!File.Exists(active)) return null;
        using var pointer = JsonDocument.Parse(ReadRegular(active, 4096));
        string id = pointer.RootElement.GetProperty("generation").GetString();
        if (!Guid.TryParseExact(id, "N", out _) || pointer.RootElement.GetProperty("recipe").GetString() != recipeId)
            throw new InvalidDataException("Invalid prepared game pointer.");
        string folder = Path.Combine(generations, id); Regular(folder, true);
        using var receipt = JsonDocument.Parse(ReadRegular(Path.Combine(folder, "receipt.json"), 16384));
        var record = receipt.RootElement;
        if (record.GetProperty("schema").GetInt32() != 1 || record.GetProperty("recipe").GetString() != recipeId ||
            record.GetProperty("source").GetString() != source.source_id)
            throw new InvalidDataException("Prepared game recipe changed.");
        var files = record.GetProperty("files");
        if (files.EnumerateObject().Count() != OutputNames.Length) throw new InvalidDataException("Incomplete prepared game receipt.");
        Regular(Path.Combine(folder, "orig"), true);
        foreach (string name in OutputNames)
        {
            Cancel(); var pin = files.GetProperty(name); long size = pin.GetProperty("bytes").GetInt64();
            if (size <= 0 || size > 64 * 1024 * 1024) throw new InvalidDataException("Unexpected prepared game size.");
            byte[] bytes = ReadRegular(Path.Combine(folder, name), size);
            if (bytes.LongLength != size || Hash(bytes) != pin.GetProperty("sha256").GetString())
                throw new InvalidDataException("Saved prepared game code differs; it will be prepared again.");
        }
        return new Result(folder, true, recipeId, source.source_id);
    }
    private void CleanInterrupted(string generations)
    {
        // Remove only recognized, unpublished scratch files owned by this recipe.
        // Unknown files, links and published generations are always retained.
        var allowed = new System.Collections.Generic.HashSet<string>(OutputNames.Concat(new[] {
            "preparation-owner.json", "receipt.json", "platform.json", "precision.json", "input-adaptation.json", "Celeste.dll.input",
            "Celeste.dll.patched", "Celeste.dll.platform", "Celeste.dll.repaired", "MMHOOK_Celeste.dll.patched"
        }), StringComparer.Ordinal);
        foreach (string folder in Directory.GetDirectories(generations, ".incoming-*"))
        {
            Cancel();
            if (!Guid.TryParseExact(Path.GetFileName(folder)[10..], "N", out _)) continue;
            try
            {
                Regular(folder, true);
                using var marker = JsonDocument.Parse(ReadRegular(Path.Combine(folder, "preparation-owner.json"), 4096));
                if (marker.RootElement.GetProperty("schema").GetInt32() != 1 ||
                    marker.RootElement.GetProperty("recipe").GetString() != recipeId ||
                    marker.RootElement.GetProperty("source").GetString() != source.source_id) continue;
                var files = new System.Collections.Generic.List<string>(); bool known = true;
                foreach (string entry in Directory.GetFileSystemEntries(folder))
                {
                    string name = Path.GetFileName(entry);
                    if (name == "orig")
                    {
                        Regular(entry, true);
                        foreach (string child in Directory.GetFileSystemEntries(entry))
                        {
                            Regular(child, false);
                            if (Path.GetFileName(child) != "Celeste.exe") { known = false; break; }
                            files.Add(child);
                        }
                    }
                    else
                    {
                        Regular(entry, false);
                        if (!allowed.Contains(name)) { known = false; break; }
                        files.Add(entry);
                    }
                }
                if (!known) continue;
                foreach (string file in files) File.Delete(file);
                string orig = Path.Combine(folder, "orig");
                if (Directory.Exists(orig)) Directory.Delete(orig);
                Directory.Delete(folder);
            }
            catch (Exception e) when (Recoverable(e)) { /* Keep unrecognized or inaccessible data. */ }
        }
    }
    public Result Prepare(string archive, string contentPrefix)
    {
        Stage("Checking your original game code");
        Dictionary<string, byte[]> imported = null;
        if (!string.IsNullOrEmpty(archive)) imported = SelectArchive(archive, contentPrefix);
        else SelectSaved();
        original = Path.Combine(root, "original", source.source_id);
        bool haveOriginal = false;
        try { haveOriginal = VerifyOriginal(); }
        catch (Exception e) when (Recoverable(e)) { progress("Saved game code needs a new import"); }
        if (!haveOriginal) ImportOriginal(imported);
        string recipes = Path.Combine(root, recipeId); EnsureDirectory(recipes);
        string generations = Path.Combine(recipes, source.source_id); EnsureDirectory(generations);
        CleanInterrupted(generations);
        Stage("Checking the prepared game cache");
        Result cached = null;
        try { cached = TryPrepared(generations); }
        catch (Exception e) when (Recoverable(e)) { progress("Rebuilding the prepared game cache"); }
        if (cached != null) { CommitSelection(); return cached; }
        if (availableSpace() < 256L * 1024 * 1024) throw new IOException("Free at least 256 MB to prepare the game code.");
        string id = Guid.NewGuid().ToString("N"), incoming = Path.Combine(generations, ".incoming-" + id);
        Directory.CreateDirectory(incoming);
        AtomicJson(Path.Combine(incoming, "preparation-owner.json"), new { schema = 1, recipe = recipeId, source = source.source_id });
        // This can take time on older devices. It runs off the UI/game thread and
        // reports actual stages. Failed/cancelled generations never replace active.json.
        GameCodePipeline.Prepare(original, incoming, bundled, source.kind, Stage);
        Cancel();
        var hashes = new Dictionary<string, FilePin>();
        foreach (string name in OutputNames)
        {
            byte[] bytes = ReadRegular(Path.Combine(incoming, name), 64 * 1024 * 1024);
            hashes.Add(name, new FilePin(bytes.LongLength, Hash(bytes)));
        }
        AtomicJson(Path.Combine(incoming, "receipt.json"), new { schema = 1, recipe = recipeId, source = source.source_id, files = hashes });
        Cancel();
        string committed = Path.Combine(generations, id); Directory.Move(incoming, committed);
        AtomicJson(Path.Combine(generations, "active.json"), new { schema = 1, recipe = recipeId, generation = id });
        CommitSelection();
        return new Result(committed, false, recipeId, source.source_id);
    }
    public static bool Recoverable(Exception error) => error is IOException or UnauthorizedAccessException or
        InvalidDataException or JsonException or KeyNotFoundException or InvalidOperationException or FormatException;
}

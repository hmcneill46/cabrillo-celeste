using System;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using System.Security.Cryptography;
using Mono.Cecil;

static class AuditPayload
{
    static object Inspect(Stream stream, string filename)
    {
        using var module = ModuleDefinition.ReadModule(stream);
        string name = module.Assembly.Name.Name;
        if (name is "Celeste" or "Celeste.Content" or "MMHOOK_Celeste")
            throw new InvalidDataException("Game assembly in app payload: " + filename);
        if (Path.GetFileNameWithoutExtension(filename) != name)
            throw new InvalidDataException("Disguised assembly identity: " + filename + " is " + name);
        return new { identity=module.Assembly.Name.FullName,
            references=module.AssemblyReferences.Select(a=>a.Name).ToArray(),
            resources=module.Resources.OfType<EmbeddedResource>().ToDictionary(r=>r.Name,r=>Convert.ToHexString(SHA256.HashData(r.GetResourceData())).ToLowerInvariant()) };
    }
    static int Main(string[] args)
    {
        string bundle=args[0]; var assemblies=new Dictionary<string,object>();
        foreach (string path in Directory.GetFiles(Path.Combine(bundle,"Managed"),"*",SearchOption.AllDirectories))
        {
            if (Path.GetExtension(path)!=".dll" || Path.GetDirectoryName(path)!=Path.Combine(bundle,"Managed"))
                throw new InvalidDataException("Unexpected managed payload file: " + path);
            using var file=File.OpenRead(path); assemblies.Add(Path.GetFileName(path),Inspect(file,Path.GetFileName(path)));
        }
        using var zip=ZipFile.OpenRead(Path.Combine(bundle,"CJITCodeCanary-v1.0.0.zip"));
        if (!zip.Entries.Select(e=>e.FullName).OrderBy(x=>x).SequenceEqual(new[]{"CJITCodeCanary.dll","everest.yaml"}))
            throw new InvalidDataException("Unexpected internal mod payload.");
        using var memory=new MemoryStream(); using(var input=zip.GetEntry("CJITCodeCanary.dll").Open()) input.CopyTo(memory);
        memory.Position=0; assemblies.Add("CJITCodeCanary.dll",Inspect(memory,"CJITCodeCanary.dll"));
        File.WriteAllText(args[1],JsonSerializer.Serialize(new { status="PASS_NO_BUNDLED_GAME_ASSEMBLIES",assemblies },new JsonSerializerOptions{WriteIndented=true}));
        return 0;
    }
}

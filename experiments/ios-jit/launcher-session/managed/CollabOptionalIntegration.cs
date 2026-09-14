using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using Celeste.Mod;
using Mono.Cecil;
using Mono.Cecil.Cil;
using MonoMod.RuntimeDetour;
namespace CelesteJIT.Game;

// Roslyn put one optional CelesteNet delegate in the same cache type as normal
// lobby delegates. Mono resolves all field types when touching any cache field.
// Move that single compiler cache into the existing optional integration type.
// Original guards, delegate creation, event add/remove and gameplay IL remain.
public static class CollabOptionalIntegration
{
    private const string ZipHash="4bcea8a9011edb8b7d27b433c47f1f4a871b8f7a4dd7f2bffac67bb99c7f6ad5";
    private const string Policy="collab-optional-cache-v1";
    private static Hook hook;
    private delegate Assembly Original(EverestModuleAssemblyContext context,string path);
    private delegate Assembly Detour(Original original,EverestModuleAssemblyContext context,string path);
    private static string Hash(byte[] data)=>Convert.ToHexString(SHA256.HashData(data)).ToLowerInvariant();
    internal static void Install()
    {
        if(OperatingSystem.IsMacOS() && Environment.GetEnvironmentVariable("CJIT_TEST_ORIGINAL_COLLAB")=="1")return;
        hook=new Hook(typeof(EverestModuleAssemblyContext).GetMethod("LoadRelinkedAssembly",BindingFlags.NonPublic|BindingFlags.Instance),(Detour)Load);
        Entry.Mark("mono_collab_compatibility_installed",Policy);
    }
    private static Assembly Load(Original original,EverestModuleAssemblyContext context,string path)
    {
        if(context.ModuleMeta.Name!="CollabUtils2")return original(context,path);
        if(context.ModuleMeta.Version!=new Version(1,13,4) || string.IsNullOrEmpty(context.ModuleMeta.PathArchive) || Hash(File.ReadAllBytes(context.ModuleMeta.PathArchive))!=ZipHash)
            throw new InvalidOperationException("Collab compatibility requires the exact original 1.13.4 ZIP.");
        byte[] input=File.ReadAllBytes(path);
        using var module=ModuleDefinition.ReadModule(new MemoryStream(input));
        if(module.Assembly.Name.Name!="CollabUtils2")return original(context,path);
        int references=Rewrite(module);
        using var output=new MemoryStream();module.Write(output);byte[] bytes=output.ToArray();string hash=Hash(bytes);
        string directory=Path.Combine(Entry.SaveRoot,"Cache","CJITCompat",Policy,Hash(input));Directory.CreateDirectory(directory);
        string destination=Path.Combine(directory,"CollabUtils2.dll");bool reused=File.Exists(destination) && Hash(File.ReadAllBytes(destination))==hash;
        if(!reused){string temporary=destination+"."+Guid.NewGuid().ToString("N")+".tmp";try{File.WriteAllBytes(temporary,bytes);File.Move(temporary,destination,true);}finally{if(File.Exists(temporary))File.Delete(temporary);}}
        Entry.Mark("mono_collab_optional_relinked","policy="+Policy+"; movedFields=1; references="+references+"; reused="+reused+"; inputSHA256="+Hash(input)+"; outputSHA256="+hash);
        return original(context,destination);
    }
    public static int Rewrite(ModuleDefinition module)
    {
        if(module.Assembly.Name.Name!="CollabUtils2")throw new InvalidOperationException("Wrong assembly for Collab compatibility.");
        var owner=module.GetType("Celeste.Mod.CollabUtils2.LobbyHelper")??throw new MissingMemberException("LobbyHelper");
        var cache=owner.NestedTypes.Single(t=>t.Name=="<>O");var optional=owner.NestedTypes.Single(t=>t.Name=="CelesteNet");
        var field=cache.Fields.Single(f=>f.Name=="<23>__adjustCollabIcon");
        if(!field.IsStatic || cache.Methods.Count!=0 || !field.FieldType.FullName.Contains("CelesteNetPlayerListComponent/BlobPlayer") || !field.FieldType.FullName.Contains("DataPlayerState") || optional.Fields.Count!=0)
            throw new InvalidOperationException("Unexpected Collab optional cache shape.");
        string identity=field.FullName;
        var references=module.GetTypes().SelectMany(t=>t.Methods).Where(m=>m.HasBody).SelectMany(m=>m.Body.Instructions).Where(i=>i.Operand is FieldReference f && f.FullName==identity).ToArray();
        if(references.Length!=4 || references.Count(i=>i.OpCode==OpCodes.Ldsfld)!=2 || references.Count(i=>i.OpCode==OpCodes.Stsfld)!=2)
            throw new InvalidOperationException("Unexpected Collab optional cache references.");
        cache.Fields.Remove(field);optional.Fields.Add(field);
        foreach(var instruction in references)instruction.Operand=field;
        return references.Length;
    }
    internal static void Dispose(){hook?.Dispose();hook=null;}
}

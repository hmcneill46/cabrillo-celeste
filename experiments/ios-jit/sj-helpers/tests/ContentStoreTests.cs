using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text;
using System.Text.Json;
using CelesteJIT.Content;

static class Tests
{
    static int checks;
    static void Check(bool good,string name) { if(!good)throw new Exception(name);checks++;Console.WriteLine("PASS "+name); }
    static void Reject(Action action,string name) { try {action();}catch(Exception e)when(e is InvalidDataException || e is IOException || e is OperationCanceledException){Check(true,name);return;}throw new Exception("Expected rejection: "+name); }
    static void Zip(string path, Dictionary<string,byte[]> files, Action<ZipArchive> extra=null) {
        using var z=ZipFile.Open(path,ZipArchiveMode.Create);
        foreach(var pair in files){var e=z.CreateEntry("Payload/Test.app/Content/"+pair.Key);using var stream=e.Open();stream.Write(pair.Value);}
        extra?.Invoke(z);
    }
    public static void Main(string[] args) {
        string root=Path.GetFullPath(args[0]);Directory.CreateDirectory(root);
        var files=new Dictionary<string,byte[]> {{"Dialog/test.txt",Encoding.UTF8.GetBytes("owned fixture")},{"Graphics/test.bin",Enumerable.Range(0,512*1024).Select(i=>(byte)(i*71)).ToArray()}};
        var entries=files.OrderBy(p=>p.Key,StringComparer.Ordinal).Select(p=>new {path=p.Key,bytes=(long)p.Value.Length,sha256=ContentStore.Hash(p.Value)}).ToArray();
        string identity=ContentStore.Hash(Encoding.UTF8.GetBytes(string.Concat(entries.Select(x=>x.path+"\0"+x.bytes+"\0"+x.sha256+"\n"))));
        string manifest=Path.Combine(root,"manifest.json");File.WriteAllText(manifest,JsonSerializer.Serialize(new {schema=1,aggregate_sha256=identity,files=entries}));
        bool cancelled=false;string cancelPhase=null;
        ContentStore Store(string name="library",long free=long.MaxValue) => new ContentStore(manifest,identity,Path.Combine(root,name),
            (phase,done,total,count)=>{if(phase==cancelPhase && done>100000)cancelled=true;},()=>cancelled,()=>free);
        string good=Path.Combine(root,"good.ipa");Zip(good,files);
        var result=Store().Prepare(good);Check(!result.Reused && result.VerifiedBytes==files.Values.Sum(v=>(long)v.Length),"verified full archive import");
        Check(files.All(p=>File.ReadAllBytes(Path.Combine(result.ContentRoot,p.Key)).SequenceEqual(p.Value)),"extracted bytes match");
        string active=Path.Combine(root,"library",identity,"active.json");byte[] pointer=File.ReadAllBytes(active);
        result=Store().Prepare(null);Check(result.Reused,"fresh importer reuses hash-verified cache");
        string interrupted=Path.Combine(root,"library",identity,".incoming-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(interrupted);
        File.WriteAllText(Path.Combine(interrupted,"import-owner.txt"),identity);
        Directory.CreateSymbolicLink(Path.Combine(interrupted,"outside"),Path.GetDirectoryName(manifest));
        Check(Store().Prepare(null).Reused && !Directory.Exists(interrupted) && File.Exists(manifest),"interrupted staging recovered without following links or losing active data");
        string unowned=Path.Combine(root,"library",identity,".incoming-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(unowned);
        Check(Store().Prepare(null).Reused && Directory.Exists(unowned),"unmarked directories preserved");
        Reject(()=>Store("space",0).Prepare(good),"insufficient space before extraction");
        foreach(string kind in new[]{"hash","missing","extra","traversal","absolute","duplicate","case","symlink"}) {
            string path=Path.Combine(root,kind+".zip");var altered=files.ToDictionary(p=>p.Key,p=>p.Value);
            if(kind=="hash")altered["Graphics/test.bin"]=new byte[512*1024];
            if(kind=="missing")altered.Remove("Graphics/test.bin");
            Zip(path,altered,z=>{
                string name=kind switch {"extra"=>"extra.bin","traversal"=>"../escape.txt","absolute"=>"/escape.txt","duplicate"=>"Dialog/test.txt","case"=>"dialog/test.txt","symlink"=>"link",_=>null};
                if(name!=null){var e=z.CreateEntry("Payload/Test.app/Content/"+name);if(kind=="symlink")e.ExternalAttributes=unchecked((int)0xa1ff0000);using var s=e.Open();s.Write(new byte[]{1});}
            });
            Reject(()=>Store().Prepare(path),kind+" input rejected");
            Check(File.ReadAllBytes(active).SequenceEqual(pointer),kind+" preserves active pointer");
            Check(Store().Prepare(null).Reused,kind+" preserves working cache");
        }
        cancelPhase="Importing game files";cancelled=false;
        Reject(()=>Store("cancel-cold").Prepare(good),"cancel new import");
        Check(!Directory.EnumerateDirectories(Path.Combine(root,"cancel-cold",identity),".incoming-*").Any(),"cancel removes only new staging");
        cancelPhase="Checking selected archive";cancelled=false;
        Reject(()=>Store().Prepare(good),"cancel replacement validation");cancelPhase=null;cancelled=false;
        Check(File.ReadAllBytes(active).SequenceEqual(pointer) && Store().Prepare(null).Reused,"cancel keeps previous game files");
        string target=Path.Combine(result.ContentRoot,"Dialog/test.txt");File.WriteAllText(target,"corrupted");
        Reject(()=>Store().Prepare(null),"corrupt persistent cache cannot launch");
        var repaired=Store().Prepare(good);Check(!repaired.Reused && File.ReadAllBytes(Path.Combine(repaired.ContentRoot,"Dialog/test.txt")).SequenceEqual(files["Dialog/test.txt"]),"verified reimport repairs corrupt cache");
        string link=Path.Combine(repaired.ContentRoot,"Dialog/test.txt");File.Delete(link);File.CreateSymbolicLink(link,manifest);
        Reject(()=>Store().Prepare(null),"cache symlinks rejected");
        string huge=Path.Combine(root,"huge.zip");File.Copy(good,huge);byte[] raw=File.ReadAllBytes(huge);raw[^12]=0xff;raw[^11]=0xff;File.WriteAllBytes(huge,raw);
        Reject(()=>Store("envelope").Prepare(huge),"oversized central entry count rejected before loading entries");
        Check(!File.Exists(Path.Combine(root,"escape.txt")),"no archive traversal writes");
        Console.WriteLine("PASS_CONTENT_STORE_TESTS "+checks);
    }
}

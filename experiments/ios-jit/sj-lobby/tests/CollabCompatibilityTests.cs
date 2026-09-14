using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Mono.Cecil;
using Mono.Cecil.Cil;
using CelesteJIT.Game;
namespace CelesteJIT.Canary;
public static class Entry {
    static int checks;
    static void Check(bool pass,string name){if(!pass)throw new Exception(name);checks++;Console.WriteLine("PASS_COLLAB "+name);}
    static string Body(MethodDefinition m)=>!m.HasBody?"none":string.Join("\n",m.Body.Instructions.Select(i=>i.OpCode+":"+(i.Operand?.ToString()??"")))+"|EH="+m.Body.ExceptionHandlers.Count;
    static void Rejected(Action<ModuleDefinition> tamper,byte[] bytes){using var m=ModuleDefinition.ReadModule(new MemoryStream(bytes));tamper(m);bool threw=false;try{CollabOptionalIntegration.Rewrite(m);}catch{threw=true;}Check(threw,"unsupported shape rejected");}
    public static int Arithmetic(int unused){
        byte[] bytes=File.ReadAllBytes(Environment.GetEnvironmentVariable("CJIT_COLLAB_TEST_INPUT"));
        using var m=ModuleDefinition.ReadModule(new MemoryStream(bytes));
        var types=m.GetTypes().Select(t=>t.FullName).ToArray();var fields=m.GetTypes().SelectMany(t=>t.Fields).ToArray();
        var bodies=m.GetTypes().SelectMany(t=>t.Methods).ToDictionary(x=>x.FullName,Body);
        string old="Celeste.Mod.CollabUtils2.LobbyHelper/<>O::<23>__adjustCollabIcon",moved="Celeste.Mod.CollabUtils2.LobbyHelper/CelesteNet::<23>__adjustCollabIcon";
        Check(CollabOptionalIntegration.Rewrite(m)==4,"four field references redirected");
        Check(types.SequenceEqual(m.GetTypes().Select(t=>t.FullName)),"type identities preserved");
        Check(fields.Length==m.GetTypes().Sum(t=>t.Fields.Count),"field count preserved");
        int changed=0;
        foreach(var method in m.GetTypes().SelectMany(t=>t.Methods)){string after=Body(method),before=bodies[method.FullName];if(after!=before)changed++;Check(after==before.Replace(old,moved),"method preserved "+method.FullName);}
        Check(changed==2,"only optional event add/remove method operands changed");
        Check(m.GetType("Celeste.Mod.CollabUtils2.LobbyHelper").NestedTypes.Single(t=>t.Name=="<>O").Fields.All(f=>!f.FieldType.FullName.Contains("CelesteNet")),"normal cache no longer depends on CelesteNet");
        var relocated=m.GetType("Celeste.Mod.CollabUtils2.LobbyHelper").NestedTypes.Single(t=>t.Name=="CelesteNet").Fields.Single();
        Check(relocated.IsPublic && relocated.IsStatic && relocated.Name=="<23>__adjustCollabIcon" && relocated.FieldType.FullName.Contains("DataPlayerState"),"optional delegate type and storage flags preserved");
        bool duplicate=false;try{CollabOptionalIntegration.Rewrite(m);}catch{duplicate=true;}Check(duplicate,"duplicate application rejected");
        Rejected(x=>x.Assembly.Name.Name="WrongModule",bytes);
        Rejected(x=>x.GetType("Celeste.Mod.CollabUtils2.LobbyHelper").NestedTypes.Single(t=>t.Name=="<>O").Fields.Single(f=>f.Name=="<23>__adjustCollabIcon").Name="changed",bytes);
        Rejected(x=>x.GetType("Celeste.Mod.CollabUtils2.LobbyHelper").NestedTypes.Single(t=>t.Name=="CelesteNet").Fields.Add(new FieldDefinition("unexpected",FieldAttributes.Public,x.TypeSystem.Int32)),bytes);
        using var output=new MemoryStream();m.Write(output);using var roundtrip=ModuleDefinition.ReadModule(new MemoryStream(output.ToArray()));Check(roundtrip.GetTypes().Count()==types.Length,"rewritten assembly serializes and parses");
        Console.WriteLine("PASS_COLLAB_COMPATIBILITY checks="+checks+" methods="+bodies.Count);return 15;
    }
}

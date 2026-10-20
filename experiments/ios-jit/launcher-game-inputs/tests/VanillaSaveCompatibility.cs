// Uses the owner's original vanilla assembly under desktop Mono. No game code is
// copied into this test. The output is a normal standalone Celeste save file.
using System;
using System.IO;
using System.Reflection;
using System.Xml.Serialization;
class VanillaSaveCompatibility {
    static void Main(string[] args) {
        var folder=args[0];
        AppDomain.CurrentDomain.AssemblyResolve+=(sender,eventArgs)=> {
            var path=Path.Combine(folder,new AssemblyName(eventArgs.Name).Name+".dll");
            return File.Exists(path)?Assembly.LoadFrom(path):null;
        };
        var assembly=Assembly.LoadFrom(Path.Combine(folder,"Celeste.exe"));
        var type=assembly.GetType("Celeste.SaveData",true);var serializer=new XmlSerializer(type);
        object save;using(var input=File.OpenRead(args[1]))save=serializer.Deserialize(input);
        var time=type.GetField("Time");var deaths=type.GetField("TotalDeaths");
        time.SetValue(save,(long)time.GetValue(save)+600000000L);
        deaths.SetValue(save,(int)deaths.GetValue(save)+1);
        using(var output=File.Create(args[2]))serializer.Serialize(output,save);
        using(var input=File.OpenRead(args[2])) {
            var loaded=serializer.Deserialize(input);
            foreach(var field in new[]{"Name","Time","TotalDeaths","Version"})
                if(!Equals(type.GetField(field).GetValue(save),type.GetField(field).GetValue(loaded)))throw new Exception("Vanilla save roundtrip mismatch: "+field);
        }
        Console.WriteLine("PASS_ORIGINAL_VANILLA_SAVE_READ_UPDATE_WRITE version="+type.GetField("Version").GetValue(save));
    }
}

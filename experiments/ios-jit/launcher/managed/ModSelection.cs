using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using Celeste.Mod;
namespace CelesteJIT.Game;
internal static class ModSelection
{
    internal static void Verify()
    {
        string path=Path.Combine(Entry.SaveRoot,"launcher-run.json");
        var manifest=JObject.Parse(File.ReadAllText(path));
        if ((int)manifest["schema"]!=1) throw new InvalidOperationException("Unsupported launcher selection.");
        var expected=new Dictionary<string,Version>(StringComparer.Ordinal){{"Everest",new Version(1,6458,0)},{"Celeste",new Version(1,4,0,0)}};
        foreach(var row in (JArray)manifest["modules"])
            expected.Add((string)row["name"],new Version(((string)row["version"]).Split('-')[0]));
        // Multiple EverestModule implementations may share one metadata record
        // (e.g. original JackalHelper); all must have the selected version.
        foreach(var pair in expected)
        {
            var matches=Everest.Modules.Where(m=>m.Metadata.Name==pair.Key).ToArray();
            if(matches.Length==0 || matches.Any(m=>m.Metadata.Version!=pair.Value))
                throw new InvalidOperationException("Enabled module did not load at its selected version: "+pair.Key+" "+pair.Value);
            Entry.Mark("everest_selection_module_verified",pair.Key+" "+pair.Value+"; instances="+matches.Length);
        }
        foreach(var module in Everest.Modules)
            if(!expected.ContainsKey(module.Metadata.Name))throw new InvalidOperationException("Unexpected enabled module: "+module.Metadata.Name);
        Entry.Mark("everest_selection_pass","All "+expected.Count+" selected/built-in metadata identities match actual Everest registration; no disabled extras.");
    }
}

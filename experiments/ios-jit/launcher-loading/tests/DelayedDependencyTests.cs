// Compare the production cooperative pass with the pinned upstream algorithm.
// The runner supplies the unchanged upstream method as a private test reference.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using Celeste.Mod;
namespace Celeste.Mod {
    public sealed class EverestModuleMetadata {
        public string Name;public Version Version=new(1,0,0);
        public List<EverestModuleMetadata> Dependencies=new(),OptionalDependencies=new();
    }
    public sealed class TestModule { public EverestModuleMetadata Metadata; }
    public static class Logger { public static void Info(string category,string message){} public static void Warn(string category,string message){} }
    public static class EverestSplashHandler { public static void IncreaseLoadedModCount(string name){} }
    public static class CabrilloLoading {
        public static int Skipped,Stages;
        public static void Skip(){Skipped++;}
        public static void Stage(string phase,string detail){
            if(Monitor.IsEntered(Everest.Loader.Delayed) || Everest.Loader.DelayedLock!=1)throw new Exception("yield retained a Monitor or lost the reentrancy guard");
            Stages++;
        }
    }
    public static partial class Everest {
        public static readonly List<TestModule> Modules=new();
        public static readonly List<string> Calls=new();
        public static class Loader {
            public static readonly List<Tuple<EverestModuleMetadata,Action>> Delayed=new();
            public static int DelayedLock;
            public static bool DependencyLoaded(EverestModuleMetadata dep)=>Modules.Any(m=>m.Metadata.Name==dep.Name && m.Metadata.Version>=dep.Version);
            public static bool DependenciesLoaded(EverestModuleMetadata meta)=>meta.Dependencies.All(DependencyLoaded) && meta.OptionalDependencies.All(d=>DependencyLoaded(d) || !Modules.Any(m=>m.Metadata.Name==d.Name));
            public static bool LoadMod(EverestModuleMetadata meta){Calls.Add("load:"+meta.Name);Modules.Add(new TestModule{Metadata=meta});CheckDependenciesOfDelayedMods();return true;}
        }
    }
}
public static class DelayedDependencyTests {
    static EverestModuleMetadata Mod(string name,string dependencies="",string optional="") => new(){Name=name,
        Dependencies=dependencies.Split(',',StringSplitOptions.RemoveEmptyEntries).Select(n=>new EverestModuleMetadata{Name=n}).ToList(),
        OptionalDependencies=optional.Split(',',StringSplitOptions.RemoveEmptyEntries).Select(n=>new EverestModuleMetadata{Name=n}).ToList()};
    static string Run(int test,bool cooperative) {
        Everest.Modules.Clear();Everest.Calls.Clear();Everest.Loader.Delayed.Clear();Everest.Loader.DelayedLock=0;CabrilloLoading.Stages=0;
        var cases=new[]{new[]{Mod("A","B"),Mod("B","C"),Mod("C")},new[]{Mod("A",optional:"B"),Mod("B")},
            new[]{Mod("A",optional:"B"),Mod("B",optional:"A")},new[]{Mod("A",optional:"B"),Mod("B","C"),Mod("C","B")},
            new[]{Mod("A","Missing"),Mod("B")},new[]{Mod("Already"),Mod("Other")},new[]{Mod("Throw"),Mod("Later")},new[]{Mod("A","Old")}};
        if(test==5)Everest.Modules.Add(new TestModule{Metadata=Mod("Already")});
        if(test==7)Everest.Modules.Add(new TestModule{Metadata=new EverestModuleMetadata{Name="Old",Version=new Version(0,9,0)}});
        foreach(var meta in cases[test])Everest.Loader.Delayed.Add(Tuple.Create(meta,(Action)(()=>{Everest.Calls.Add("content:"+meta.Name);if(meta.Name=="Throw")throw new ApplicationException("expected");})));
        string failure="";int yields=0;
        try {
            if(cooperative){using var steps=Everest.CJITCheckDependenciesOfDelayedMods().GetEnumerator();while(steps.MoveNext()){
                if(Monitor.IsEntered(Everest.Loader.Delayed))throw new Exception("Monitor escaped a callback");
                int calls=Everest.Calls.Count;
                Everest.CheckDependenciesOfDelayedMods(); // nested callback must remain suppressed.
                if(Everest.Calls.Count!=calls)throw new Exception("recursive drain escaped guard");
                if(++yields>20)throw new Exception("unbounded cycle");
            }}else Everest.CheckDependenciesOfDelayedMods();
        }catch(ApplicationException e){failure=e.Message;}
        if(Everest.Loader.DelayedLock!=0)throw new Exception("guard leaked after completion/failure");
        if(cooperative && yields!=CabrilloLoading.Stages)throw new Exception("stage/yield mismatch");
        return string.Join(",",Everest.Calls)+"|pending:"+string.Join(",",Everest.Loader.Delayed.Select(d=>d.Item1.Name))+"|error:"+failure;
    }
    public static void Main(){
        for(int i=0;i<8;i++){
            string original=Run(i,false),cooperative=Run(i,true);
            if(original!=cooperative)throw new Exception("Changed dependency semantics in case "+i+": "+original+" != "+cooperative);
            Console.WriteLine("PASS_DELAYED_ORDER case="+i+" "+cooperative);
        }
        Console.WriteLine("PASS_DELAYED_DEPENDENCY_ORDER_AND_LOCKS");
    }
}

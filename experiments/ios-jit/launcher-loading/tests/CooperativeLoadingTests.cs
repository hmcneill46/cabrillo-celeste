using System;
using System.Collections.Generic;
using System.Threading;
using Celeste.Mod;

namespace Celeste.Mod {
    public sealed class EverestModuleMetadata { public string Name; public Version Version; }
    public static class Everest { public static class Loader { public static readonly List<object> Delayed = new(); } }
    public static class Logger { public static int Errors; public static void LogDetailed(Exception e) { Errors++; } }
}
public static class CooperativeLoadingTests {
    static int work, reports;
    static void Check(bool pass, string name) { if (!pass) throw new Exception(name); Console.WriteLine("PASS " + name); }
    static IEnumerable<int> Steps() { work++; yield return 0; work++; yield return 0; work++; }
    static IEnumerable<int> Broken() { work++; yield return 0; throw new ApplicationException("original failure"); }
    static Exception OnWorker(Action action) { Exception failure=null;var thread=new Thread(()=>{try{action();}catch(Exception e){failure=e;}});thread.Start();thread.Join();return failure; }
    public static void Main() {
        CabrilloLoading.Enable((phase,detail,done,total)=>reports++);
        CabrilloLoading.Defer(Steps());Check(work==0,"deferral performs no boot work");
        Check(CabrilloLoading.ContinueBoot() && work==1,"first continuation performs one step");
        Check(OnWorker(()=>CabrilloLoading.ContinueBoot()) is InvalidOperationException && work==1,"continuations reject a different owning thread");
        Check(CabrilloLoading.ContinueBoot() && work==2,"second continuation performs one step");
        Check(!CabrilloLoading.ContinueBoot() && work==3,"completion is reported after final work");
        CabrilloLoading.Discover(2);CabrilloLoading.Archive("Multi.zip");
        var one=new EverestModuleMetadata{Name="ExactModuleOne",Version=new Version(1,0)};
        var two=new EverestModuleMetadata{Name="ExactModuleTwo",Version=new Version(2,0)};
        CabrilloLoading.ModuleBeginning(one);CabrilloLoading.ModuleFinished(one,true);
        Check(OnWorker(()=>{CabrilloLoading.ModuleBeginning(two);CabrilloLoading.ModuleFinished(two,false);})==null,"module observers preserve the mod's own thread choices");
        CabrilloLoading.Skip();CabrilloLoading.ArchiveCompleted("Multi.zip");Everest.Loader.Delayed.Add(new object());
        Check(CabrilloLoading.ArchivesProcessed==1 && CabrilloLoading.ArchivesTotal==2 && CabrilloLoading.ModuleAttempts==2 && CabrilloLoading.ModulesLoaded==1 && CabrilloLoading.LoadFailures==1 && CabrilloLoading.Skipped==1 && CabrilloLoading.Delayed==1,"multiple modules and failed loads stay separate from archive counts");
        CabrilloLoading.Defer(Broken());Check(CabrilloLoading.ContinueBoot(),"failing boot yields before its failing operation");
        try { CabrilloLoading.ContinueBoot();throw new Exception("failure swallowed"); } catch(ApplicationException e) {Check(e.Message=="original failure" && Logger.Errors==1,"original boot exception is reported and preserved");}
        CabrilloLoading.FinishPresentation();int before=reports;
        Check(OnWorker(()=>{CabrilloLoading.Stage("mods","late");CabrilloLoading.Archive("late.zip");CabrilloLoading.ModuleBeginning(one);CabrilloLoading.ModuleFinished(one,true);})==null && reports==before && CabrilloLoading.ModuleAttempts==2,"late observations cannot reopen the loading screen or impose thread affinity");
        try{CabrilloLoading.Enable(null);throw new Exception("second owner accepted");}catch(InvalidOperationException){Check(true,"a second startup owner is rejected");}
        Console.WriteLine("PASS_COOPERATIVE_LOADING_CONTRACT");
    }
}

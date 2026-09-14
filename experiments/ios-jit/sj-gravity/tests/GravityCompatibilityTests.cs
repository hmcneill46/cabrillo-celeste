using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Mono.Cecil;
using Mono.Cecil.Cil;
using CelesteJIT.Game;
namespace CelesteJIT.Canary;
public static class Entry
{
    private static int checks;
    private static void Check(bool condition, string name)
    { if (!condition) throw new Exception(name); checks++; Console.WriteLine("GRAVITY_COMPAT " + name); }
    private static void Reject(Action operation, string name)
    { try { operation(); } catch (InvalidOperationException) { Check(true, name); return; } throw new Exception("Did not reject: " + name); }
    private static string Body(MethodDefinition m) => m.HasBody ? string.Join("\n", m.Body.Instructions.Select(i => i.OpCode + " " + i.Operand)) : "none";
    private static Dictionary<string,string> Bodies(ModuleDefinition m) => m.GetTypes().SelectMany(t => t.Methods.Select((x,i) => new { Key=t.FullName+"#"+i+":"+x.FullName, Value=Body(x) })).ToDictionary(x=>x.Key,x=>x.Value);
    private static string Shape(ModuleDefinition m) => string.Join("\n", m.GetTypes().Select(t => t.FullName + ":" + t.Attributes + ":" + t.BaseType + ":" + string.Join(",",t.Fields.Select(f => f.FullName + ":" + f.Attributes))));
    public static int Arithmetic(int unused)
    { try { return Run(); } catch(Exception error) { Console.WriteLine(error.ToString()); throw; } }
    private static int Run()
    {
        int calls=0;
        Check(!GravityOptionalIntegration.InvokeIfPresent(false, () => {calls++;throw new Exception("Unavailable optional type resolved");}), "absent_does_not_resolve_or_invoke");
        Check(calls==0,"absent_zero_calls");
        Check(GravityOptionalIntegration.InvokeIfPresent(true, () => calls++),"present_invokes");
        Check(calls==1,"present_exactly_once");
        var marker=new InvalidOperationException("present integration failure");
        try {GravityOptionalIntegration.InvokeIfPresent(true,()=>throw marker);throw new Exception("swallowed");}
        catch(InvalidOperationException error) {Check(ReferenceEquals(marker,error),"present_errors_propagate");}
        Check(!GravityOptionalIntegration.InvokeIfPresent(false,null),"absent_never_touches_operation");
        string path=Environment.GetEnvironmentVariable("CJIT_GRAVITY_TEST_INPUT");
        using var original=ModuleDefinition.ReadModule(path);
        var before=Bodies(original);string shape=Shape(original);
        Check(GravityOptionalIntegration.Rewrite(original)==2,"two_original_sites_rewritten");
        using var bytes=new MemoryStream();original.Write(bytes);bytes.Position=0;
        using var patched=ModuleDefinition.ReadModule(bytes);
        var after=Bodies(patched);var changed=before.Keys.Where(k=>before[k]!=after[k]).ToArray();
        Check(changed.Length==2 && changed.All(k=>k.Contains("GravityHelperModule::Load()") || k.Contains("GravityHelperModule::Unload()")),"only_load_and_unload_bodies_changed");
        Check(Shape(patched)==shape,"all_types_bases_and_fields_retained");
        Check(patched.GetType("Celeste.Mod.GravityHelper.ThirdParty.CelesteNet.CelesteNetModSupport")!=null,"optional_implementation_retained");
        var owner=patched.GetType("Celeste.Mod.GravityHelper.GravityHelperModule");
        foreach(var name in new[]{"Load","Unload"}) {
            var body=owner.Methods.Single(m=>m.Name==name && m.Parameters.Count==0).Body;
            Check(!body.Instructions.Any(i=>i.OpCode==OpCodes.Ldtoken && i.Operand.ToString().Contains("CelesteNetModSupport")),name+"_has_no_eager_optional_token");
            Check(body.Instructions.Count(i=>i.Operand is MethodReference r && r.DeclaringType.FullName==typeof(GravityOptionalIntegration).FullName && r.Name==name+"Optional")==1,name+"_uses_one_deferred_operation");
        }
        Reject(()=>GravityOptionalIntegration.Rewrite(patched),"double_patch_rejected");
        using var wrong=ModuleDefinition.ReadModule(path);wrong.Assembly.Name.Name="UnrelatedMod";
        Reject(()=>GravityOptionalIntegration.Rewrite(wrong),"unrelated_assembly_rejected");
        using var tampered=ModuleDefinition.ReadModule(path);
        var load=tampered.GetType("Celeste.Mod.GravityHelper.GravityHelperModule").Methods.Single(m=>m.Name=="Load" && m.Parameters.Count==0);
        var token=load.Body.Instructions.Single(i=>i.OpCode==OpCodes.Ldtoken && i.Operand.ToString().Contains("CelesteNetModSupport"));
        token.Next.Next.OpCode=OpCodes.Ldc_I4_2;
        Reject(()=>GravityOptionalIntegration.Rewrite(tampered),"changed_hook_level_rejected");
        Console.WriteLine("PASS_GRAVITY_COMPATIBILITY_CONTROLS checks="+checks+" methods="+before.Count);
        return 15;
    }
}

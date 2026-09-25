// Narrow repair of an over-broad, historical Mono precision adaptation.
// No original game implementation is reproduced here. Inputs are owner-provided.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Mono.Cecil;
using Mono.Cecil.Cil;
using Mono.Cecil.Rocks;

internal static class RepairPlayerPrecision {
    static readonly Dictionary<string,int> Targets = new() {
        ["System.Void Celeste.PlayerHair::AfterUpdate()"] = 1,
        ["System.Void Celeste.PlayerSeeker::Update()"] = 6,
        ["System.Boolean Celeste.Player/<BirdDashTutorialCoroutine>d__561::MoveNext()"] = 3
    };
    static string Hash(string text) => Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(text))).ToLowerInvariant();
    static Dictionary<string,string> Bodies(string path) {
        using var m = ModuleDefinition.ReadModule(path);
        return m.GetTypes().SelectMany(t=>t.Methods).Where(f=>f.HasBody).ToDictionary(f=>f.FullName+(f.HasGenericParameters ? "`"+f.GenericParameters.Count : ""), f=>{
            f.Body.SimplifyMacros(); var il=f.Body.Instructions;
            string Operand(object o) => o switch {
                Instruction target => "@"+il.IndexOf(target),
                Instruction[] targets => string.Join(",",targets.Select(t=>"@"+il.IndexOf(t))),
                VariableDefinition v => "local:"+v.Index+":"+v.VariableType.FullName,
                ParameterDefinition p => "arg:"+p.Index+":"+p.ParameterType.FullName,
                null => "", _ => Convert.ToString(o,System.Globalization.CultureInfo.InvariantCulture)
            };
            return Hash(string.Join("\n",il.Select(i=>i.OpCode+" "+Operand(i.Operand)))+"\n"+
                string.Join(";",f.Body.Variables.Select(v=>v.VariableType.FullName))+"\n"+
                string.Join(";",f.Body.ExceptionHandlers.Select(h=>h.HandlerType+":"+il.IndexOf(h.TryStart)+":"+il.IndexOf(h.TryEnd)+":"+il.IndexOf(h.HandlerStart)+":"+il.IndexOf(h.HandlerEnd)+":"+h.CatchType)));
        });
    }
    // Infer only a straight-line stack expression; control-flow joins/dup and
    // unsupported instructions return unknown, never a guessed numeric width.
    static (int width, Instruction before) Expr(Instruction i, MethodDefinition m, int depth=0) {
        if(i==null || depth>80)return(0,null);
        int width=0, pop=0;
        switch(i.OpCode.Code) {
            case Code.Ldc_R4: return(32,i.Previous);
            case Code.Ldc_R8: return(64,i.Previous);
            case Code.Conv_R4: width=32;pop=1;break;
            case Code.Conv_R8: width=64;pop=1;break;
            case Code.Ldloc: width=Width(((VariableDefinition)i.Operand).VariableType);break;
            case Code.Ldarg: width=Width(((ParameterDefinition)i.Operand).ParameterType);break;
            case Code.Ldfld: width=Width(((FieldReference)i.Operand).FieldType);pop=1;break;
            case Code.Ldsfld: width=Width(((FieldReference)i.Operand).FieldType);break;
            case Code.Call: case Code.Callvirt:
                var c=(MethodReference)i.Operand;
                if(c.ReturnType.MetadataType==MetadataType.Void)return(0,null);
                width=Width(c.ReturnType);pop=c.Parameters.Count+(c.HasThis?1:0);break;
            case Code.Add: case Code.Sub: case Code.Mul: case Code.Div: case Code.Rem:
                var r=Expr(i.Previous,m,depth+1);var l=Expr(r.before,m,depth+1);
                return(l.width==r.width?l.width:0,l.before);
            case Code.Neg: return Expr(i.Previous,m,depth+1);
            case Code.Ldloca: case Code.Ldarga: case Code.Ldc_I4: case Code.Ldc_I8: case Code.Ldnull: case Code.Ldstr: break;
            case Code.Newobj: pop=((MethodReference)i.Operand).Parameters.Count;break;
            default:return(0,null);
        }
        var previous=i.Previous;
        for(int n=0;n<pop;n++){var value=Expr(previous,m,depth+1);previous=value.before;if(previous==null && n<pop-1)return(0,null);}
        return(width,previous);
    }
    static int Width(TypeReference t) => t.MetadataType==MetadataType.Single?32:t.MetadataType==MetadataType.Double?64:0;
    static List<string> Mixed(string path) {
        using var m=ModuleDefinition.ReadModule(path);var found=new List<string>();
        foreach(var f in m.GetTypes().SelectMany(t=>t.Methods).Where(f=>f.HasBody)) {
            f.Body.SimplifyMacros();
            foreach(var i in f.Body.Instructions.Where(i=>new[]{Code.Add,Code.Sub,Code.Mul,Code.Div,Code.Rem}.Contains(i.OpCode.Code))) {
                var r=Expr(i.Previous,f);var l=Expr(r.before,f);
                if(l.width!=0 && r.width!=0 && l.width!=r.width)found.Add(f.FullName+" @"+i.Offset+" "+l.width+"/"+r.width);
            }
        }
        return found;
    }
    static List<string> FloatSinks(string path) {
        using var m=ModuleDefinition.ReadModule(path);var found=new List<string>();
        foreach(var f in m.GetTypes().SelectMany(t=>t.Methods).Where(f=>f.HasBody)) {
            f.Body.SimplifyMacros();
            foreach(var i in f.Body.Instructions) {
                if(i.Operand is MethodReference call && (i.OpCode==OpCodes.Call || i.OpCode==OpCodes.Callvirt)) {
                    var previous=i.Previous;
                    for(int n=call.Parameters.Count-1;n>=0 && previous!=null;n--) {
                        var expr=Expr(previous,f);
                        if(Width(call.Parameters[n].ParameterType)==32 && expr.width==64)found.Add(f.FullName+" -> "+call.FullName+" arg"+n);
                        previous=expr.before;
                    }
                } else if(i.OpCode==OpCodes.Stfld && i.Operand is FieldReference field && Width(field.FieldType)==32 && Expr(i.Previous,f).width==64)found.Add(f.FullName+" -> "+field.FullName);
            }
        }
        return found;
    }
    static void Main(string[] args) {
        var before=Bodies(args[0]);var mixedBefore=Mixed(args[0]);var sinksBefore=FloatSinks(args[0]);
        using(var m=ModuleDefinition.ReadModule(args[0])) {
            var counts=new Dictionary<string,int>();int preserved=0;
            foreach(var f in m.GetTypes().SelectMany(t=>t.Methods).Where(f=>f.HasBody)) {
                var hits=f.Body.Instructions.Where(i=> i.OpCode==OpCodes.Call && i.Operand is MethodReference mr && mr.DeclaringType.FullName=="Monocle.Calc" && mr.Name=="Approach" &&
                    i.Previous?.OpCode==OpCodes.Conv_R4 && i.Previous.Previous?.OpCode==OpCodes.Mul && i.Previous.Previous.Previous?.OpCode==OpCodes.Conv_R8 &&
                    i.Previous.Previous.Previous.Previous?.Operand is MethodReference dt && dt.DeclaringType.FullName=="Monocle.Engine" && dt.Name=="get_DeltaTime").ToArray();
                if(hits.Length==0)continue;
                if(!Targets.ContainsKey(f.FullName)) { preserved+=hits.Length; continue; }
                counts[f.FullName]=hits.Length;
                foreach(var call in hits) {
                    var narrow=call.Previous;var widen=narrow.Previous.Previous;var value=widen.Previous.Previous;
                    bool single=value.OpCode==OpCodes.Ldc_R4 || value.Operand is VariableDefinition local && local.VariableType.MetadataType==MetadataType.Single;
                    if(!single)throw new Exception("Expected an original float multiplier in "+f.FullName);
                    if(f.Body.Instructions.Any(i=>i.Operand==narrow || i.Operand==widen || i.Operand is Instruction[] branches && branches.Any(b=>b==narrow || b==widen)))throw new Exception("Conversion is a branch target");
                    f.Body.Instructions.Remove(narrow);f.Body.Instructions.Remove(widen);
                }
            }
            if(counts.Count!=Targets.Count || Targets.Any(p=>!counts.TryGetValue(p.Key,out int n)||n!=p.Value) || preserved!=10)throw new Exception("Unexpected historical precision sites");
            // Everest widens LavaRect calculations, but leaves one constant
            // single-width and feeds widened arguments to two float setters.
            // Keep its double calculations and make these boundaries explicit.
            var lava=m.GetType("Celeste.LavaRect").Methods.Single(f=>f.Name=="Resize");
            int sinks=0,constants=0;
            foreach(var i in lava.Body.Instructions.ToArray()) {
                if(i.Operand is MethodReference setter && new[]{"set_Width","set_Height"}.Contains(setter.Name) && setter.Parameters.Single().ParameterType.MetadataType==MetadataType.Single) {
                    if(i.Previous.OpCode!=OpCodes.Conv_R8)throw new Exception("Unexpected lava float setter");
                    lava.Body.Instructions.Remove(i.Previous);sinks++;
                }
                if(i.OpCode==OpCodes.Ldc_R4 && (float)i.Operand==0.25f && i.Next.OpCode==OpCodes.Mul) {
                    lava.Body.GetILProcessor().InsertAfter(i,Instruction.Create(OpCodes.Conv_R8));constants++;
                }
            }
            if(sinks!=2 || constants!=1)throw new Exception("Unexpected lava precision sites");
            m.Mvid=Guid.NewGuid();m.Write(args[1]);
        }
        Targets["System.Void Celeste.LavaRect::Resize(System.Single,System.Single,System.Int32)"]=3;
        var after=Bodies(args[1]);var changed=before.Keys.Where(k=>before[k]!=after[k]).OrderBy(k=>k).ToArray();
        if(before.Count!=after.Count || !changed.SequenceEqual(Targets.Keys.OrderBy(k=>k)))throw new Exception("Unrelated managed method changed");
        var mixedAfter=Mixed(args[1]);var sinksAfter=FloatSinks(args[1]);
        if(mixedBefore.Count-mixedAfter.Count!=11 || mixedAfter.Count!=0 || sinksBefore.Count-sinksAfter.Count!=2 || sinksAfter.Count!=0)throw new Exception("Unexpected mixed-width arithmetic change");
        File.WriteAllText(args[2],JsonSerializer.Serialize(new {status="PASS_SCOPED_PLAYER_PRECISION_REPAIR",changed_methods=Targets,unchanged_method_bodies=before.Count-changed.Length,
            preserved_double_precision_sites=10,mixed_before=mixedBefore,mixed_after=mixedAfter,float_sinks_before=sinksBefore,float_sinks_after=sinksAfter,new_mvid=ModuleDefinition.ReadModule(args[1]).Mvid,
            before_methods=Targets.Keys.ToDictionary(k=>k,k=>before[k]),after_methods=Targets.Keys.ToDictionary(k=>k,k=>after[k])},new JsonSerializerOptions{WriteIndented=true}));
    }
}

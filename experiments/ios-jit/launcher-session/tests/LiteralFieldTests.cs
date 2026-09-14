using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Celeste;
using MonoMod.Utils;

public static class LiteralFieldTests
{
    enum Kind : ulong { Large=0xfedcba9876543210UL }
    class Fields {
        public const string Text="literal value", Empty="", NullText=null;
        public const object NullObject=null;
        public const bool Bool=true;
        public const char Char='\uffff';
        public const sbyte I8=sbyte.MinValue;
        public const byte U8=byte.MaxValue;
        public const short I16=short.MinValue;
        public const ushort U16=ushort.MaxValue;
        public const int I32=int.MinValue;
        public const uint U32=uint.MaxValue;
        public const long I64=long.MinValue;
        public const ulong U64=ulong.MaxValue;
        public const float F32=-1.25f;
        public const double F64=double.NegativeInfinity;
        public const Kind Enum=Kind.Large;
        public const decimal Decimal=12.345m; // C# emits a static readonly field.
        public int Instance=7;
        public static string Mutable="before";
        public readonly int Readonly=19;
        public int Add(int x)=>Instance+x;
    }
    struct Value { public int Number; }
    static int checks;
    static void Check(bool ok,string name) {
        if(!ok)throw new InvalidOperationException("Literal field regression: "+name);
        checks++;Console.WriteLine("LITERAL_FIELD_PASS "+name);
    }
    static void Reject(Action action,string name) {
        bool rejected=false;try{action();}catch(FieldAccessException){rejected=true;}
        Check(rejected,name);
    }
    static void Literal(FieldInfo f) {
        object expected=f.GetValue(null);var fast=f.GetFastInvoker();var structure=FastReflectionHelper.GetFastStructInvoker(f);
        string label=f.DeclaringType.Name+"."+f.Name;
        Check(f.IsLiteral && f.IsStatic,label+"_metadata");
        Check(Equals(fast(null),expected) && Equals(fast(new object(),(object[])null),expected),label+"_fast_get");
        object box=f.FieldType.IsValueType?Activator.CreateInstance(f.FieldType):new WeakBox();
        structure(null,box);
        Check(Equals(f.FieldType.IsValueType?box:((WeakBox)box).Value,expected),label+"_struct_get");
        Reject(()=>fast(null,new object[]{expected}),label+"_fast_set_rejected");
        Reject(()=>structure(null,box,new object[]{expected}),label+"_struct_set_rejected");
        Check(Equals(fast(null),expected) && Equals(f.GetValue(null),expected),label+"_unchanged_after_set");
    }
    public static int Run(int mode) {
        var root=typeof(Decal).GetField("Root",BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Static);
        Check(root!=null && root.IsLiteral && root.IsStatic && root.FieldType==typeof(string),"actual_Decal_Root_literal_metadata");
        Console.WriteLine("ACTUAL_DECAL_ROOT "+root.GetRawConstantValue());
        if(mode==0) {
            try {root.GetFastInvoker()(null);throw new Exception("Original failure did not reproduce.");}
            catch(MissingFieldException e) {
                Check(e.Message.Contains("literal field") && e.Message.Contains("Celeste.Decal.Root"),"original_exact_missing_field");
                Console.WriteLine("PASS_ORIGINAL_MONOMOD_LITERAL_FAILURE "+e.Message);return 1;
            }
        }
        Literal(root);
        foreach(var f in typeof(Fields).GetFields(BindingFlags.Public|BindingFlags.Static).Where(f=>f.IsLiteral))Literal(f);
        var target=new Fields();var data=new DynamicData(target);
        foreach(var f in typeof(Fields).GetFields(BindingFlags.Public|BindingFlags.Static).Where(f=>f.IsLiteral))
            Check(Equals(data.Get(f.Name),f.GetValue(null)),"dynamic_get_"+f.Name);
        var enumerated=data.ToDictionary(kv=>kv.Key,kv=>kv.Value);
        Check(enumerated.Count>=21 && (string)enumerated["Text"]==Fields.Text && (Kind)enumerated["Enum"]==Kind.Large,"dynamic_enumeration_all_types");
        Reject(()=>data.Set("Text","changed"),"dynamic_literal_set_rejected");
        var instance=typeof(Fields).GetField("Instance").GetFastInvoker();Check((int)instance(target)==7,"instance_get");
        Check((int)instance(target,42)==42 && target.Instance==42,"instance_set");
        var stat=typeof(Fields).GetField("Mutable").GetFastInvoker();Check((string)stat(null)=="before","static_get");
        Check((string)stat(null,"after")=="after" && Fields.Mutable=="after","static_set");
        Check((int)typeof(Fields).GetField("Readonly").GetFastInvoker()(target)==19,"readonly_get");
        Check((decimal)typeof(Fields).GetField("Decimal").GetFastInvoker()(null)==Fields.Decimal,"decimal_nonliteral_get");
        Check((int)typeof(Fields).GetMethod("Add").GetFastInvoker()(target,5)==47,"method_invoker_unchanged");
        object boxed=new Value {Number=8};var structField=typeof(Value).GetField("Number").GetFastInvoker();
        Check((int)structField(boxed)==8 && (int)structField(boxed,9)==9 && ((Value)boxed).Number==9,"boxed_instance_struct_get_set");
        var fastRoot=root.GetFastInvoker();bool repeated=true;for(int i=0;i<1000;i++)repeated &= Equals(fastRoot(null),root.GetRawConstantValue());Check(repeated,"thousand_actual_root_reads");
        Console.WriteLine("PASS_MONOMOD_LITERAL_FIELDS checks="+checks);return 1;
    }
}

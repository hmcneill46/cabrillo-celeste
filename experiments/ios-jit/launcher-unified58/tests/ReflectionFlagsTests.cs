using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;
public static class ReflectionFlagsTests {
    private static bool done;
    private static int checks;
    private static void Check(bool value,string detail) {
        if(!value)throw new InvalidOperationException("Reflection flags: "+detail);
        checks++;Console.WriteLine("REFLECTION_FLAGS_PASS "+detail);
    }
    public static void Run() {
        if(done)return;done=true;
        var path=Environment.GetEnvironmentVariable("CJIT_REFLECTION_SIGNATURES") ?? throw new InvalidOperationException("Missing reflection fixture path");
        Check(!File.Exists(Path.Combine(Path.GetDirectoryName(path)!,"MissingSignature.dll")),"missing integration assembly is absent");
        var type=Assembly.LoadFrom(path).GetType("ReflectionSignatures",true)!;
        var methods=type.GetMethods(BindingFlags.Public|BindingFlags.Static|BindingFlags.DeclaredOnly);
        Check(methods.Length==7,"seven independent signature controls");
        foreach(var method in methods) {
            bool native=method.Name.StartsWith("Native"),preserve=method.Name=="Preserved" || method.Name=="NativePreserve";
            int expectedFlags=(preserve?128:0)|(method.Name=="NoInline"?72:0);
            Check((int)method.GetMethodImplementationFlags()==expectedFlags,method.Name+" implementation flags");
            var expected=native?(preserve?new[]{"DllImportAttribute","PreserveSigAttribute"}:new[]{"DllImportAttribute"}):(preserve?new[]{"MarkerAttribute","PreserveSigAttribute"}:new[]{"MarkerAttribute"});
            var data=method.GetCustomAttributesData();
            Check(data.Select(a=>a.AttributeType.Name).OrderBy(x=>x).SequenceEqual(expected.OrderBy(x=>x)),method.Name+" attribute metadata without resolving signature");
            Check(method.GetCustomAttributes(false).Select(a=>a.GetType().Name).OrderBy(x=>x).SequenceEqual(expected.OrderBy(x=>x)),method.Name+" instantiated attributes without resolving signature");
            if(native) {
                var attr=(DllImportAttribute)method.GetCustomAttributes(typeof(DllImportAttribute),false).Single();
                Check(attr.EntryPoint=="unused" && attr.CharSet==CharSet.Unicode && attr.SetLastError && attr.CallingConvention==CallingConvention.Cdecl && attr.PreserveSig==preserve,method.Name+" complete DllImport fields");
                var pseudo=data.Single(a=>a.AttributeType.Name=="DllImportAttribute");
                Check((bool)pseudo.NamedArguments.Single(a=>a.MemberName=="PreserveSig").TypedValue.Value! == preserve,method.Name+" DllImport metadata PreserveSig");
            }
        }
        Check(!AppDomain.CurrentDomain.GetAssemblies().Any(a=>a.GetName().Name=="MissingSignature"),"attributes did not load or fabricate missing dependency");
        var plain=methods.Single(m=>m.Name=="Plain");bool failed=false;
        try{_ = plain.ReturnType;}catch(FileNotFoundException){failed=true;}catch(TypeLoadException){failed=true;}
        Check(failed,"explicit return type still reports missing dependency");
        Check(plain.GetCustomAttributesData().Count==1,"attribute metadata still works after signature failure");
        Console.WriteLine("PASS_MONO_REFLECTION_FLAGS_CONTRACT checks="+checks);
    }
}

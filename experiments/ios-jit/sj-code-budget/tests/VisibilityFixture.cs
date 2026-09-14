using System;
using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.CompilerServices;

namespace System.Runtime.CompilerServices {
    [AttributeUsage(AttributeTargets.Assembly, AllowMultiple=true)]
    public sealed class IgnoresAccessChecksToAttribute : Attribute {
        public IgnoresAccessChecksToAttribute(string assemblyName) { AssemblyName=assemblyName; }
        public string AssemblyName { get; }
    }
}
public class VisibilityTarget {
#pragma warning disable CS0414
    private int Private=11;
    internal int Internal=13;
    protected int Protected=17;
    protected internal int FamilyOrAssembly=19;
    private protected int FamilyAndAssembly=23;
    protected class Nested { public static int Value=29; }
#pragma warning restore CS0414
}
namespace CelesteJIT.Canary {
public static class Entry {
    public static int Arithmetic(int challenge) {
        int checks=0;
        foreach(string grant in new[]{"none","wrong","VisibilityFixture"}) {
            var asm=AssemblyBuilder.DefineDynamicAssembly(new AssemblyName("VisibilityAccess_"+grant),AssemblyBuilderAccess.Run);
            if(grant!="none") asm.SetCustomAttribute(new CustomAttributeBuilder(typeof(IgnoresAccessChecksToAttribute).GetConstructor(new[]{typeof(string)}),new object[]{grant}));
            var module=asm.DefineDynamicModule("Main");
            foreach(string fieldName in new[]{"Private","Internal","Protected","FamilyOrAssembly","FamilyAndAssembly"}) {
                var type=module.DefineType("Probe_"+fieldName,TypeAttributes.Public);
                var method=type.DefineMethod("Read",MethodAttributes.Public|MethodAttributes.Static,typeof(int),new[]{typeof(VisibilityTarget)});
                var il=method.GetILGenerator();
                il.Emit(OpCodes.Ldarg_0);
                il.Emit(OpCodes.Ldfld,typeof(VisibilityTarget).GetField(fieldName,BindingFlags.NonPublic|BindingFlags.Instance));
                il.Emit(OpCodes.Ret);
                var reader=type.CreateType().GetMethod("Read");
                bool succeeded=false;
                try { int value=(int)reader.Invoke(null,new object[]{new VisibilityTarget()}); if(value<11)throw new Exception("Bad field value");succeeded=true; }
                catch(TargetInvocationException ex) when(ex.InnerException is MemberAccessException || ex.InnerException is TypeLoadException) { }
                bool expected=grant=="VisibilityFixture" && (challenge==1 || fieldName=="Private" || fieldName=="Internal" || fieldName=="FamilyOrAssembly");
                Console.WriteLine("VISIBILITY grant="+grant+" member="+fieldName+" expected="+expected+" actual="+succeeded);
                if(succeeded!=expected)throw new Exception("Visibility mismatch: grant="+grant+" member="+fieldName+" expected="+expected+" actual="+succeeded);
                checks++;
            }
        }
        Console.WriteLine("PASS_VISIBILITY_15_CASES runtime="+(challenge==1?"patched":"original control"));
        return checks;
    }
}
}

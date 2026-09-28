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
    public int Public=29;
#pragma warning restore CS0414
    private int PrivateMethod() => 11;
    internal int InternalMethod() => 13;
    protected int ProtectedMethod() => 17;
    protected internal int FamilyOrAssemblyMethod() => 19;
    private protected int FamilyAndAssemblyMethod() => 23;
    public int PublicMethod() => 29;
}

namespace CelesteJIT.Canary {
public static class Entry {
    public static int Arithmetic(int corrected) {
        int checks=0;
        string[] names={"Private","Internal","Protected","FamilyOrAssembly","FamilyAndAssembly","Public"};
        int[] values={11,13,17,19,23,29};
        foreach(string grant in new[]{"none","wrong","VisibilityFixture"}) {
            var asm=AssemblyBuilder.DefineDynamicAssembly(new AssemblyName("VisibilityAccess_"+grant),AssemblyBuilderAccess.Run);
            if(grant!="none") asm.SetCustomAttribute(new CustomAttributeBuilder(typeof(IgnoresAccessChecksToAttribute).GetConstructor(new[]{typeof(string)}),new object[]{grant}));
            var module=asm.DefineDynamicModule("Main");
            foreach(bool isMethod in new[]{false,true}) for(int i=0;i<names.Length;i++) {
                string member=names[i];
                var type=module.DefineType("Probe_"+member+isMethod,TypeAttributes.Public);
                var method=type.DefineMethod("Read",MethodAttributes.Public|MethodAttributes.Static,typeof(int),new[]{typeof(VisibilityTarget)});
                var il=method.GetILGenerator(); il.Emit(OpCodes.Ldarg_0);
                const BindingFlags flags=BindingFlags.NonPublic|BindingFlags.Public|BindingFlags.Instance;
                if(isMethod) il.Emit(OpCodes.Call,typeof(VisibilityTarget).GetMethod(member+"Method",flags));
                else il.Emit(OpCodes.Ldfld,typeof(VisibilityTarget).GetField(member,flags));
                il.Emit(OpCodes.Ret);
                var reader=type.CreateType().GetMethod("Read"); bool succeeded=false;
                try {
                    int value=(int)reader.Invoke(null,new object[]{new VisibilityTarget()});
                    if(value!=values[i]) throw new Exception("Incorrect member value");
                    succeeded=true;
                } catch(TargetInvocationException ex) when(ex.InnerException is MemberAccessException || ex.InnerException is TypeLoadException) { }
                bool expected=member=="Public" || (grant=="VisibilityFixture" && (corrected==1 || member=="Private" || member=="Internal" || member=="FamilyOrAssembly"));
                Console.WriteLine("VISIBILITY grant="+grant+" member="+member+" method="+isMethod+" expected="+expected+" actual="+succeeded);
                if(succeeded!=expected) throw new Exception("Unexpected access result");
                checks++;
            }
        }
        Console.WriteLine("PASS_VISIBILITY_36_CASES runtime="+(corrected==1?"restored":"build35 control"));
        return checks;
    }
}
}

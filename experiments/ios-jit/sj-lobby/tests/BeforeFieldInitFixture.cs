using System;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Threading;
namespace CelesteJIT.Canary;
public static class Entry {
    public static bool Ready;
    public static int Initializations, ExplicitCalls, Failures, ParallelCalls;
    static void Check(bool value,string name){if(!value)throw new Exception(name);Console.WriteLine("PASS_BFI "+name);}
    public static int Initialize(){if(!Ready)throw new InvalidOperationException("Source game particles are not initialized yet.");Initializations++;return 42;}
    public static int Arithmetic(int mode){
        if(mode==0){bool caught=false;try{Lazy.NoField();}catch(TypeInitializationException){caught=true;}Check(caught,"original eager initialization reproduced");return 15;}
        Check((typeof(Lazy).Attributes&TypeAttributes.BeforeFieldInit)!=0,"fixture carries beforefieldinit");
        Check(Lazy.NoField()==7 && Initializations==0,"static hook registration does not initialize particles");
        Check(Lazy.Read(false)==-1 && Initializations==0,"unexecuted field branch stays lazy");
        Ready=true;Check(Lazy.Read(true)==42 && Initializations==1,"first own static field read initializes exactly once");
        Check(Lazy.Read(true)==42 && Lazy.NoField()==7 && Initializations==1,"compiled-method lookup retains initialized value");
        Check(Generic<string>.NoField()==9 && Generic<object>.NoField()==9 && Initializations==1,"generic methods defer each closed class");
        Check(Generic<string>.Read()==42 && Generic<object>.Read()==42 && Initializations==3,"generic static fields initialize per closed class");
        Check(new Instance().Read()==42 && Initializations==4,"instance method static field access initializes");
        Check((int)typeof(Reflect).GetField("Value").GetValue(null)==42 && Initializations==5,"reflection field access initializes");
        RuntimeHelpers.RunClassConstructor(typeof(Forced).TypeHandle);Check(Forced.Read()==42 && Initializations==6,"explicit RunClassConstructor honored");
        Check(Explicit.NoField()==3 && ExplicitCalls==1,"explicit static constructors retain eager semantics");
        int errors=0;for(int i=0;i<2;i++){try{Bad.Read();}catch(TypeInitializationException){errors++;}}Check(errors==2 && Failures==1,"initializer exception cached");
        Thread[] threads=new Thread[8];int[] values=new int[8];for(int i=0;i<8;i++){int index=i;threads[i]=new Thread(()=>values[index]=Parallel.Read());threads[i].Start();}foreach(var t in threads)t.Join();Check(Array.TrueForAll(values,v=>v==81) && ParallelCalls==1,"concurrent first field reads initialize once");
        Console.WriteLine("PASS_BFI_13_CASES");return 15;
    }
}
public class Lazy {public static readonly int Value=Entry.Initialize();[MethodImpl(MethodImplOptions.NoInlining)]public static int NoField()=>7;[MethodImpl(MethodImplOptions.NoInlining)]public static int Read(bool access)=>access?Value:-1;}
public class Generic<T> {public static readonly int Value=Entry.Initialize();[MethodImpl(MethodImplOptions.NoInlining)]public static int NoField()=>9;[MethodImpl(MethodImplOptions.NoInlining)]public static int Read()=>Value;}
public class Instance {public static readonly int Value=Entry.Initialize();[MethodImpl(MethodImplOptions.NoInlining)]public int Read()=>Value;}
public class Reflect {public static readonly int Value=Entry.Initialize();}
public class Forced {public static readonly int Value=Entry.Initialize();public static int Read()=>Value;}
public class Explicit {static Explicit(){Entry.ExplicitCalls++;}[MethodImpl(MethodImplOptions.NoInlining)]public static int NoField()=>3;}
public class Bad {public static readonly int Value=Fail();static int Fail(){Entry.Failures++;throw new InvalidOperationException("expected");}[MethodImpl(MethodImplOptions.NoInlining)]public static int Read()=>Value;}
public class Parallel {public static readonly int Value=Initialize();static int Initialize(){Interlocked.Increment(ref Entry.ParallelCalls);Thread.Sleep(20);return 81;}[MethodImpl(MethodImplOptions.NoInlining)]public static int Read()=>Value;}

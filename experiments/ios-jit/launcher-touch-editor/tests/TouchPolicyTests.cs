using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using CelesteIOSFoundation;
using CelesteJIT.Game;

public static class TouchPolicyTests
{
    static int checks;
    static void Check(bool v,string name){if(!v)throw new Exception("Touch policy: "+name);checks++;Console.WriteLine("TOUCH_CHECK "+name);}
    static TouchPoint Add(TouchPoint a,TouchPoint b)=>new(a.X+b.X,a.Y+b.Y);
    static TouchConfiguration Default()=>TouchConfiguration.Default(960,540,default,false);
    static TouchPoint Center(TouchControl c)=>new((c.X+c.Width/2)*960,(c.Y+c.Height/2)*540);
    static ConfiguredTouchState State(TouchConfiguration c)=>new(c,new(0,0,960,540));
    static TouchControl Item(TouchConfiguration c,string kind)=>c.Controls.First(x=>x.Kind==kind);
    public static void Main(string[] args){Run();if(args.Length>0)Geometry(args[0]);Console.WriteLine("PASS_TOUCH_POLICY checks="+checks);}
    public static void Run()
    {
        var c=Default();Check(c.Validate()=="","factory validates");
        Check(TouchConfiguration.Decode(JsonSerializer.Serialize(c,TouchConfiguration.JSON)).Controls.Length==8,"layout JSON round trip");
        foreach(var bad in new[]{"{}","null","[]","{\"schema\":99}",new string('x',32769)}) {
            bool rejected=false;try{TouchConfiguration.Decode(bad);}catch(Exception){rejected=true;}Check(rejected,"invalid layout rejected");
        }
        var s=State(c);var j=Center(Item(c,"jump"));var d=Center(Item(c,"dash"));var g=Center(Item(c,"grab"));
        s.BeginFrame();s.Apply(1,TouchPhase.Pressed,j);Check(s.Jump && s.JumpPressed,"jump contact down");
        s.BeginFrame();s.Apply(1,TouchPhase.Moved,new(900,10));Check(s.Jump && !s.JumpPressed,"button holds outside its bounds");
        s.Apply(1,TouchPhase.Moved,d);Check(s.Dash && !s.Jump,"slide jump to dash");
        s.Apply(1,TouchPhase.Released,d);Check(!s.Dash && !s.Jump,"slide release clears both");
        c.Sliding=false;s=State(c);s.Apply(1,TouchPhase.Pressed,j);s.Apply(1,TouchPhase.Moved,d);Check(s.Jump && !s.Dash,"slide disabled");
        s.Reset();s.Apply(1,TouchPhase.Pressed,new(480,260));s.Apply(1,TouchPhase.Moved,j);Check(!s.Jump,"outside finger never acquires button");
        s.Reset();s.Apply(1,TouchPhase.Pressed,j);s.Apply(2,TouchPhase.Pressed,j);s.Apply(1,TouchPhase.Released,j);Check(s.Jump,"two owners preserve held action");
        s.ReleaseMissingOwners(ReadOnlySpan<int>.Empty);Check(!s.Jump,"missing contacts clear all holds");
        s.Apply(1,TouchPhase.Pressed,j);s.Apply(1,TouchPhase.Pressed,d);Check(!s.Jump && s.Dash,"reused ID replaces its prior ownership");
        s.Reset();s.Apply(1,TouchPhase.Pressed,g);Check(s.Grab,"toggle latches");s.Apply(2,TouchPhase.Pressed,g);Check(s.Grab,"duplicate grab down does not toggle twice");
        s.Apply(1,TouchPhase.Released,g);s.Apply(2,TouchPhase.Released,g);Check(s.Grab,"toggle survives release");s.Apply(3,TouchPhase.Pressed,g);Check(!s.Grab,"fresh logical grab edge toggles off");
        foreach(var mode in new[]{"hold","invert"}) {
            c.Grab=mode;s=State(c);Check(s.Grab==(mode=="invert"),mode+" idle");s.Apply(1,TouchPhase.Pressed,g);Check(s.Grab==(mode=="hold"),mode+" down");s.ReleaseMissingOwners([]);Check(s.Grab==(mode=="invert"),mode+" missing release");
        }
        c=Default();s=State(c);var m=Center(Item(c,"movement"));s.Apply(1,TouchPhase.Pressed,m);Check(s.MoveX==0 && s.MoveY==0,"movement dead zone");
        s.Apply(1,TouchPhase.Moved,Add(m,new TouchPoint(60,-60)));Check(s.MoveX==1 && s.MoveY==-1,"diagonal movement");
        s.Apply(2,TouchPhase.Pressed,Add(m,new TouchPoint(-60,0)));Check(s.MoveX==1,"second movement finger cannot steal");s.Apply(1,TouchPhase.Released,m);Check(s.MoveX==0,"release movement owner");s.Apply(2,TouchPhase.Moved,m);Check(s.MoveX==0,"held second finger cannot acquire later");
        c.Movement="floating";s=State(c);s.Apply(1,TouchPhase.Pressed,new(200,300));Check(s.MoveX==0 && s.MovementCenter==new TouchPoint(200,300),"floating center follows acquisition");s.Apply(1,TouchPhase.Moved,new(170,300));Check(s.MoveX==-1,"floating movement offset");
        foreach(int orientation in new[]{0,1,2,3})foreach(bool swap in new[]{false,true}) {
            c=Default();Item(c,"jump").Enabled=Item(c,"dash").Enabled=false;
            var split=new TouchControl{Id="split",Kind="split",Shape="rectangle",X=.55,Y=.25,Width=.4,Height=.65,Split=orientation,Swap=swap};c.Controls=c.Controls.Append(split).ToArray();s=State(c);
            var p=orientation switch {0=>new TouchPoint(840,220),1=>new TouchPoint(560,180),2=>new TouchPoint(570,300),_=>new TouchPoint(710,180)};
            s.Apply(1,TouchPhase.Pressed,p);Check(s.Jump==!swap && s.Dash==swap,"split first half "+orientation+" swap="+swap);
            var mid=Center(split);s.Apply(1,TouchPhase.Moved,mid);Check(s.Jump==!swap,"split boundary hysteresis "+orientation+" swap="+swap);
        }
        c=Default();var rect=Item(c,"jump");rect.Shape="rectangle";s=State(c);var corner=new TouchPoint(rect.X*960+1,rect.Y*540+1);s.Apply(1,TouchPhase.Pressed,corner);Check(s.Jump,"rectangle uses its corners");rect.Shape="circle";s=State(c);s.Apply(1,TouchPhase.Pressed,corner);Check(!s.Jump,"circle rejects bounding corners");
        foreach(string kind in new[]{"crouchDash","quickRestart","pause","journal"}) {
            c=Default();c.Controls=c.Controls.Append(new TouchControl{Id="extra",Kind=kind,Shape="rectangle",X=.42,Y=.38,Width=.10,Height=.13}).ToArray();s=State(c);s.Apply(1,TouchPhase.Pressed,new(440,230));
            Check(kind switch {"crouchDash"=>s.CrouchDashPressed,"quickRestart"=>s.QuickRestartPressed,"pause"=>s.PausePressed,_=>s.JournalPressed},"extra "+kind+" edge");
            s.Reset();Check(!s.CrouchDash && !s.QuickRestart && !s.Pause && !s.Journal,"extra reset "+kind);
        }
        foreach(var direction in new[]{new TouchPoint(30,0),new(30,30),new(0,30),new(-30,30),new(-30,0),new(-30,-30),new(0,-30),new(30,-30)}) {
            c=Default();c.Swipe=true;s=State(c);var start=new TouchPoint(740,320);
            s.BeginFrame();s.Apply(1,TouchPhase.Pressed,start);Check(s.Jump && !s.Dash,"gesture touch holds jump");s.Apply(2,TouchPhase.Pressed,Add(m,new TouchPoint(-50,0)));
            s.Apply(1,TouchPhase.Moved,Add(start,direction));Check(s.DashPressed && s.MoveX==-1 && s.HasDashAim,"swipe aim independent of movement");
            double len=direction.Length;Check(Math.Abs(s.DashAim.X-direction.X/len)<.001 && Math.Abs(s.DashAim.Y-direction.Y/len)<.001,"eight-way swipe direction");
            s.BeginFrame();s.Apply(1,TouchPhase.Moved,Add(Add(start,direction),direction));Check(!s.Dash && s.Jump && s.HasDashAim,"dash is a single pulse; hold keeps jump");
            s.Apply(1,TouchPhase.Released,start);Check(!s.Jump && s.HasDashAim,"lift releases jump but preserves buffered dash aim");
            for(int i=0;i<30;i++)s.BeginFrame();Check(!s.HasDashAim,"dash aim expires");
        }
        c=Default();c.Swipe=true;s=State(c);s.Apply(1,TouchPhase.Pressed,new(740,320));s.Apply(1,TouchPhase.Moved,new(763,320));Check(!s.Dash,"swipe threshold rejects small motion");
        s.CancelGestures();s.Apply(1,TouchPhase.Moved,new(800,320));Check(!s.Dash && !s.Jump,"cancel requires fresh contact");
        s.Reset();s.Apply(1,TouchPhase.Pressed,new(740,320),false);s.Apply(1,TouchPhase.Moved,new(780,320),false);Check(s.Jump && !s.Dash,"menus can confirm without a gameplay swipe");
        s.Reset();s.MenuMode=true;s.Apply(1,TouchPhase.Pressed,new(740,320));Check(!s.Jump && !s.Dash,"menu waits for tap release");
        s.Apply(1,TouchPhase.Released,new(740,320));Check(s.JumpPressed,"menu tap release confirms");
        s.Reset();s.Apply(1,TouchPhase.Pressed,new(740,320));s.Apply(1,TouchPhase.Moved,new(780,320));Check(!s.Jump && s.Dash && !s.HasDashAim,"menu swipe cancels without confirming");
        s.Apply(1,TouchPhase.Released,new(780,320));Check(!s.Jump,"menu swipe release does not confirm");
        s.Reset();s.MenuMode=false;s.Apply(1,TouchPhase.Pressed,new(740,320));s.Apply(1,TouchPhase.Moved,new(780,320));
        for(int i=0;i<15;i++)s.BeginFrame(1.0/120);Check(s.HasDashAim,"slow-motion input retains aim through scaled buffer");
        s.Reset();Check(!s.Jump && !s.Dash && !s.HasDashAim && s.MoveX==0,"lifecycle reset clears transient controls");
    }
    static void Geometry(string path) {
        using var fixture=JsonDocument.Parse(File.ReadAllText(path));
        foreach(var row in fixture.RootElement.EnumerateArray()) {
            double w=row.GetProperty("width").GetDouble(),h=row.GetProperty("height").GetDouble();var safe=row.GetProperty("safe").EnumerateArray().Select(v=>v.GetDouble()).ToArray();
            var config=TouchConfiguration.Decode(row.GetProperty("profile").GetRawText());var expected=TouchConfiguration.Default(w,h,new(safe[0],safe[1],safe[2],safe[3]),row.GetProperty("pad").GetBoolean());
            for(int i=0;i<config.Controls.Length;i++) {
                var a=config.Controls[i];var b=expected.Controls[i];Check(Math.Abs(a.X-b.X)+Math.Abs(a.Y-b.Y)+Math.Abs(a.Width-b.Width)+Math.Abs(a.Height-b.Height)<1e-10,"Swift / managed default geometry "+a.Kind);
            }
            var canvas=new TouchRect(0,0,w,h);
            foreach(var point in row.GetProperty("splitSamples").EnumerateArray()) {
                var c=JsonSerializer.Deserialize<TouchControl>(point.GetProperty("control").GetRawText(),TouchConfiguration.JSON);
                var pos=new TouchPoint(point.GetProperty("x").GetDouble(),point.GetProperty("y").GetDouble());
                Check(c.Contains(pos,canvas)==point.GetProperty("hit").GetBoolean(),"Swift / managed hit geometry");
                Check(c.Action(pos,canvas)==point.GetProperty("action").GetString(),"Swift / managed split assignment");
            }
        }
    }
}

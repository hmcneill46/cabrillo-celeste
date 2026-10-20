// Cabrillo's portable touch schema. Morro's MIT input policies informed the
// ownership, split hysteresis and source-specific grab behavior; see NOTICE.
using System.Text.Json;
using System.Text.Json.Serialization;
using CelesteIOSFoundation;

namespace CelesteJIT.Game;

public sealed class TouchControl
{
    public string Id { get; set; } = "";
    public string Kind { get; set; } = "jump";
    public string Shape { get; set; } = "circle";
    public double X { get; set; }
    public double Y { get; set; }
    public double Width { get; set; }
    public double Height { get; set; }
    public int Opacity { get; set; } = 100;
    public bool Enabled { get; set; } = true;
    public int Split { get; set; }
    public bool Swap { get; set; }
    public TouchRect Rect(TouchRect canvas) => new(canvas.X+X*canvas.Width,canvas.Y+Y*canvas.Height,Width*canvas.Width,Height*canvas.Height);
    public bool Contains(TouchPoint point, TouchRect canvas) {
        var r=Rect(canvas);
        if(Shape=="rectangle")return r.Contains(point);
        var d=point-new TouchPoint(r.X+r.Width/2,r.Y+r.Height/2);
        double radius=Math.Min(r.Width,r.Height)/2;
        return d.X*d.X+d.Y*d.Y<=radius*radius;
    }
    public string Action(TouchPoint point,TouchRect canvas,string previous="") {
        if(Kind!="split")return Kind;
        var r=Rect(canvas);double x=point.X-r.X,y=point.Y-r.Y;
        // Signed distance in points, including the diagonal's true normal.
        double side=Split switch {0=>(y*r.Width-x*r.Height)/Math.Sqrt(r.Width*r.Width+r.Height*r.Height),
            1=>(y*r.Width+x*r.Height-r.Width*r.Height)/Math.Sqrt(r.Width*r.Width+r.Height*r.Height),
            2=>x-r.Width/2,_=>y-r.Height/2};
        if(Math.Abs(side)<4 && (previous=="jump" || previous=="dash"))return previous;
        return ((side<=0)^Swap)?"jump":"dash";
    }
}

public sealed class TouchConfiguration
{
    public int Schema { get; set; } = 1;
    public string Movement { get; set; } = "fixed";
    public string Grab { get; set; } = "toggle";
    public string ControllerGrab { get; set; } = "game";
    public string KeyboardGrab { get; set; } = "game";
    public string Visibility { get; set; } = "automatic";
    public bool Sliding { get; set; } = true;
    public bool Haptics { get; set; } = true;
    public bool DirectionalHaptics { get; set; }
    public int Opacity { get; set; } = 100;
    public bool Swipe { get; set; }
    public double SwipeDistance { get; set; } = 24;
    public TouchControl[] Controls { get; set; } = [];
    public static readonly JsonSerializerOptions JSON = new() { PropertyNamingPolicy=JsonNamingPolicy.CamelCase,
        UnmappedMemberHandling=JsonUnmappedMemberHandling.Disallow, MaxDepth=8 };
    public static readonly string[] Kinds=["movement","floating","jump","dash","split","grab","pause","journal","crouchDash","quickRestart","gesture"];
    public bool Active(TouchControl c) => c.Enabled && (c.Kind!="floating" || Movement=="floating") &&
        (c.Kind!="gesture" || Swipe) && (!Swipe || c.Kind is not ("jump" or "dash" or "split"));
    public static TouchRect Canvas(double width,double height,SafeAreaMetrics safe) =>
        new(0,0,width,height);
    public static TouchConfiguration Default(double width,double height,SafeAreaMetrics safe,bool pad) {
        var old=TouchControlLayout.Create(width,height,safe,pad,1);var canvas=Canvas(width,height,safe);
        TouchControl C(string kind,TouchRect r,string shape="rectangle") => new() {Id=kind,Kind=kind,Shape=shape,
            X=(r.X-canvas.X)/canvas.Width,Y=(r.Y-canvas.Y)/canvas.Height,Width=r.Width/canvas.Width,Height=r.Height/canvas.Height};
        TouchControl Circle(string kind,TouchCircle c) => C(kind,new(c.Center.X-c.HitRadius,c.Center.Y-c.HitRadius,c.HitRadius*2,c.HitRadius*2),"circle");
        return new() { Controls=[Circle("movement",old.Movement),C("floating",old.MovementAcquisition),Circle("jump",old.Jump),Circle("dash",old.Dash),
            Circle("grab",old.Grab),C("pause",old.Pause),C("journal",old.Journal),
            new() {Id="gesture",Kind="gesture",Shape="rectangle",X=.53,Y=.30,Width=.46,Height=.69,Opacity=20}] };
    }
    public string Validate() {
        if(Schema!=1 || Movement is not ("fixed" or "floating") || Grab is not ("hold" or "invert" or "toggle") ||
            ControllerGrab is not ("game" or "hold" or "invert" or "toggle") || KeyboardGrab is not ("game" or "hold" or "invert" or "toggle") ||
            Visibility is not ("automatic" or "always" or "off") || Opacity<0 || Opacity>100 ||
            !double.IsFinite(SwipeDistance) || SwipeDistance<12 || SwipeDistance>80 || Controls==null || Controls.Length<3 || Controls.Length>24)
            return "This layout contains unsupported settings.";
        var ids=new HashSet<string>();
        foreach(var c in Controls) {
            if(c==null || string.IsNullOrEmpty(c.Id) || c.Id.Length>64 || !ids.Add(c.Id) || !Kinds.Contains(c.Kind) ||
                c.Shape is not ("circle" or "rectangle") || c.Split<0 || c.Split>3 || c.Opacity<0 || c.Opacity>100 ||
                !double.IsFinite(c.X+c.Y+c.Width+c.Height) || c.X<0 || c.Y<0 || c.Width<.015 || c.Height<.015 ||
                c.X+c.Width>1.00001 || c.Y+c.Height>1.00001)
                return "A control lies outside the screen or has invalid dimensions.";
        }
        foreach(string unique in new[]{"movement","floating","gesture"})
            if(Controls.Count(c=>c.Kind==unique)!=1)return "Keep one movement control, floating region and gesture region.";
        if(!Controls.Any(c=>c.Kind=="movement" && c.Enabled) || !Controls.Any(c=>c.Kind=="pause" && c.Enabled && c.Opacity>=20))
            return "Keep movement and a visible Pause button available.";
        if(Swipe && !Controls.Any(c=>c.Kind=="gesture" && c.Enabled))return "Enable the gesture region for tap and swipe.";
        if(Movement=="floating" && !Controls.Any(c=>c.Kind=="floating" && c.Enabled))return "Enable the floating movement region.";
        if(!Swipe && (!Controls.Any(c=>c.Enabled && c.Kind is "jump" or "split") || !Controls.Any(c=>c.Enabled && c.Kind is "dash" or "split")))
            return "Keep both Jump and Dash available.";
        return "";
    }
    public static TouchConfiguration Decode(string json) {
        if(string.IsNullOrEmpty(json) || json.Length>32768)throw new FormatException("Invalid touch layout size.");
        var value=JsonSerializer.Deserialize<TouchConfiguration>(json,JSON) ?? throw new FormatException("Empty touch layout.");
        var error=value.Validate();if(error!="")throw new FormatException(error);return value;
    }
}

// Fixed storage and stable finger ownership: no per-frame allocations. A finger
// that starts outside a control cannot acquire it later. Duplicates are ORed.
public sealed class ConfiguredTouchState
{
    public const int MaximumTouches=8;
    private struct Finger {public bool Active,Swiped;public int Id;public string Action;public TouchControl Control;public TouchPoint Start;}
    private readonly Finger[] owners=new Finger[MaximumTouches];
    private readonly bool[] held=new bool[9],previous=new bool[9];
    public TouchConfiguration Config { get; }
    public TouchRect Canvas { get; }
    public TouchDirection Direction {get;private set;}
    private TouchDirection previousDirection;
    private bool grabToggle,grabEdge;
    private double aimRemaining;
    private bool dashPulse,menuJumpPulse;
    public bool MenuMode {get;set;}
    public TouchPoint DashAim {get;private set;}
    public bool HasDashAim=>aimRemaining>0 && !MenuMode;
    public TouchPoint MovementCenter {get;private set;}
    public double MovementRadius {get;}
    public int MoveX=>TouchDirectionPolicy.Axis(Direction).X;
    public int MoveY=>TouchDirectionPolicy.Axis(Direction).Y;
    public bool Jump=>held[0]; public bool Dash=>held[1];public bool GrabRaw=>held[2];
    public bool Grab=>Config.Grab=="invert"?!GrabRaw:Config.Grab=="toggle"?grabToggle:GrabRaw;
    public bool Pause=>held[3];public bool Journal=>held[4];public bool CrouchDash=>held[5];public bool QuickRestart=>held[6];
    public bool JumpPressed=>Pressed(0);public bool DashPressed=>Pressed(1);public bool PausePressed=>Pressed(3);public bool JournalPressed=>Pressed(4);
    public bool CrouchDashPressed=>Pressed(5);public bool QuickRestartPressed=>Pressed(6);public bool GrabPressed=>grabEdge;
    public bool JumpReleased=>Released(0);public bool DashReleased=>Released(1);public bool PauseReleased=>Released(3);public bool JournalReleased=>Released(4);
    public bool CrouchDashReleased=>Released(5);public bool QuickRestartReleased=>Released(6);
    public bool LeftPressed=>MoveX<0 && TouchDirectionPolicy.Axis(previousDirection).X>=0;
    public bool RightPressed=>MoveX>0 && TouchDirectionPolicy.Axis(previousDirection).X<=0;
    public bool UpPressed=>MoveY<0 && TouchDirectionPolicy.Axis(previousDirection).Y>=0;
    public bool DownPressed=>MoveY>0 && TouchDirectionPolicy.Axis(previousDirection).Y<=0;
    public bool LeftReleased=>MoveX>=0 && TouchDirectionPolicy.Axis(previousDirection).X<0;
    public bool RightReleased=>MoveX<=0 && TouchDirectionPolicy.Axis(previousDirection).X>0;
    public bool UpReleased=>MoveY>=0 && TouchDirectionPolicy.Axis(previousDirection).Y<0;
    public bool DownReleased=>MoveY<=0 && TouchDirectionPolicy.Axis(previousDirection).Y>0;
    bool Pressed(int n)=>held[n]&&!previous[n];bool Released(int n)=>!held[n]&&previous[n];
    static int Index(string action)=>action switch {"jump"=>0,"dash"=>1,"grab"=>2,"pause"=>3,"journal"=>4,"crouchDash"=>5,"quickRestart"=>6,_=>-1};
    public ConfiguredTouchState(TouchConfiguration config,TouchRect canvas) {
        Config=config;Canvas=canvas;var r=config.Controls.First(c=>c.Kind=="movement").Rect(canvas);
        MovementCenter=new(r.X+r.Width/2,r.Y+r.Height/2);MovementRadius=Math.Min(r.Width,r.Height)/2*72/94;Reset();
    }
    public void BeginFrame(double delta=1.0/60) {
        Array.Copy(held,previous,held.Length);previousDirection=Direction;grabEdge=false;
        aimRemaining=Math.Max(0,aimRemaining-Math.Clamp(delta,0,1));dashPulse=menuJumpPulse=false;Recompute();
    }
    public TouchControl Hit(TouchPoint p,bool actionsOnly=false) {
        // Small explicit buttons always win over broad acquisition regions.
        foreach(var c in Config.Controls)if(Config.Active(c) && c.Kind is not ("movement" or "floating" or "gesture") && c.Contains(p,Canvas))return c;
        if(actionsOnly)return null;
        var movement=Config.Controls.First(c=>c.Kind==(Config.Movement=="fixed"?"movement":"floating"));
        if(movement.Contains(p,Canvas))return movement;
        if(Config.Swipe) {var c=Config.Controls.First(c=>c.Kind=="gesture");if(c.Enabled && c.Contains(p,Canvas))return c;}
        return null;
    }
    public bool IsAction(TouchPoint p)=>Hit(p,true)!=null;
    public TouchHapticAction Apply(int id,TouchPhase phase,TouchPoint p,bool gestureAllowed=true) {
        int slot=-1;for(int i=0;i<owners.Length;i++)if(owners[i].Active && owners[i].Id==id){slot=i;break;}
        bool wasGrab=GrabRaw,wasJump=Jump,wasDash=Dash;
        if(phase==TouchPhase.Pressed) {
            if(slot>=0)Release(slot);
            slot=Array.FindIndex(owners,f=>!f.Active);if(slot<0)return TouchHapticAction.None;
            var c=Hit(p);string action=c?.Action(p,Canvas)??"";
            if(action is "movement" or "floating") {
                if(owners.Any(f=>f.Active && f.Action=="movement"))action="";
                else {action="movement";if(Config.Movement=="floating")MovementCenter=p;UpdateDirection(p);}
            }
            if(action=="gesture" && (owners.Any(f=>f.Active && f.Action=="gesture")))action="";
            owners[slot]=new(){Id=id,Active=true,Action=action,Control=c,Start=p};
        } else if(slot>=0) {
            if(phase==TouchPhase.Released) {
                if(MenuMode && owners[slot].Action=="gesture" && !owners[slot].Swiped)menuJumpPulse=true;
                Release(slot);
            }
            else {
                var owner=owners[slot];
                if(owner.Action=="movement")UpdateDirection(p);
                else if(owner.Action=="gesture" && gestureAllowed && !owner.Swiped) {
                    var delta=p-owner.Start;double length=Math.Sqrt(delta.X*delta.X+delta.Y*delta.Y);
                    if(length>=Config.SwipeDistance) {
                        // Eight repeatable Celeste directions. One dash per contact.
                        var d=TouchDirectionPolicy.Classify(delta,1,0,0,TouchDirection.Neutral);
                        var axes=TouchDirectionPolicy.Axis(d);double norm=Math.Sqrt(axes.X*axes.X+axes.Y*axes.Y);
                        if(norm>0) {DashAim=new(axes.X/norm,axes.Y/norm);aimRemaining=.2;dashPulse=true;owner.Swiped=true;}
                    }
                } else if(Config.Sliding && owner.Action is "jump" or "dash") {
                    var c=Hit(p,true);if(c?.Kind is "jump" or "dash" or "split")owner.Action=c.Action(p,Canvas,owner.Action);
                }
                owners[slot]=owner;
            }
        }
        Recompute();
        if(!wasGrab && GrabRaw) {grabEdge=true;grabToggle=!grabToggle;}
        if(!Config.Haptics)return TouchHapticAction.None;
        return !wasJump && Jump?TouchHapticAction.Jump:!wasDash && Dash?TouchHapticAction.Dash:
            grabEdge && Config.Grab=="toggle"?TouchHapticAction.GrabToggle:TouchHapticAction.None;
    }
    void UpdateDirection(TouchPoint p)=>Direction=TouchDirectionPolicy.Classify(p-MovementCenter,MovementRadius,.18,8,Direction);
    void Release(int slot) {if(owners[slot].Action=="movement")Direction=TouchDirection.Neutral;owners[slot]=default;Recompute();}
    void Recompute() {
        Array.Clear(held);
        foreach(var f in owners)if(f.Active) {
            int n=Index(f.Action);if(n>=0)held[n]=true;
            if(f.Action=="gesture" && !MenuMode)held[0]=true;
        }
        // Pulse exactly one input update, retain its independent aim for Celeste's
        // ordinary button buffer + startup freeze; scaled time also supports slow motion.
        held[0]|=menuJumpPulse;held[1]|=dashPulse;
    }
    public void ReleaseMissingOwners(ReadOnlySpan<int> ids) {
        for(int i=0;i<owners.Length;i++)if(owners[i].Active && !ids.Contains(owners[i].Id))Release(i);
    }
    public void CancelGestures() {
        for(int i=0;i<owners.Length;i++)if(owners[i].Active && owners[i].Action=="gesture")owners[i].Action="";
        aimRemaining=0;dashPulse=menuJumpPulse=false;Recompute();
    }
    public void Reset() {
        Array.Clear(owners);Array.Clear(held);Array.Clear(previous);grabToggle=grabEdge=false;aimRemaining=0;dashPulse=menuJumpPulse=false;DashAim=default;
        Direction=previousDirection=TouchDirection.Neutral;var r=Config.Controls.First(c=>c.Kind=="movement").Rect(Canvas);MovementCenter=new(r.X+r.Width/2,r.Y+r.Height/2);
    }
}

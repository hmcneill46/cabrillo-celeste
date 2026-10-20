using System;
using CelesteJIT.Game;
using CelesteIOSFoundation;

public static class FeatherTouchTests
{
    public static int Checks;
    static void Check(bool pass, string text) { if (!pass) throw new Exception(text); Checks++; }
    public static void Run()
    {
        var s = new FeatherTouchState(); var player = new object();
        var far = new TouchPoint(80, 20); var origin = new TouchPoint(0, 0);
        Check(!s.Apply(1, TouchPhase.Pressed, far, true), "disabled/not in flight does not capture");
        s.BeginFrame(player);
        Check(!s.Apply(1, TouchPhase.Moved, far, true), "pre-existing joystick press cannot become a target");
        Check(!s.Apply(2, TouchPhase.Pressed, far, false), "action touch is not captured");
        Check(!s.Apply(2, TouchPhase.Moved, far, true), "action finger cannot slide into steering");
        Check(s.Apply(3, TouchPhase.Pressed, far, true) && s.ShouldSteer(origin), "fresh flight press steers");
        s.Apply(4, TouchPhase.Pressed, new(0, 100), true);
        Check(s.Target == far, "second finger cannot change target");
        s.Apply(3, TouchPhase.Moved, new(16, 0), true);
        Check(!s.ShouldSteer(origin), "near finger coasts");
        s.Apply(3, TouchPhase.Moved, new(20, 0), true);
        Check(!s.ShouldSteer(origin), "coast has jitter hysteresis");
        s.Apply(3, TouchPhase.Moved, new(23, 0), true);
        Check(s.ShouldSteer(origin), "farther finger resumes steering");
        s.Apply(3, TouchPhase.Moved, new(20, 0), true);
        Check(s.ShouldSteer(origin), "steering has jitter hysteresis");
        Check(s.Apply(3, TouchPhase.Released, far, true) && !s.HasTarget && !s.ShouldSteer(origin), "release is neutral immediately");
        s.Apply(4, TouchPhase.Moved, far, true);
        Check(!s.HasTarget, "release does not promote the other held finger");
        s.Apply(5, TouchPhase.Pressed, far, true);
        s.ReleaseMissing(new int[]{4});
        Check(!s.HasTarget, "missing/cancelled touch is neutral");
        s.Apply(6, TouchPhase.Pressed, far, true); s.BeginFrame(null);
        Check(!s.Active && !s.HasTarget && s.Apply(6, TouchPhase.Moved, far, false), "pause/flight exit quarantines finger");
        s.BeginFrame(player); s.Apply(6, TouchPhase.Moved, far, true);
        Check(!s.HasTarget, "resume requires a fresh touch");
        s.Apply(7, TouchPhase.Pressed, far, true); s.BeginFrame(new object());
        Check(!s.HasTarget, "replacement player cannot inherit steering");
        s.Apply(7, TouchPhase.Pressed, far, true);
        Check(s.HasTarget && s.ShouldSteer(origin), "fresh press can reuse a cancelled finger ID");
        s.Reset(); s.BeginFrame(player);
        Check(!s.Apply(7, TouchPhase.Moved, far, true), "layout/lifecycle reset rejects held movement");
        s.Apply(7, TouchPhase.Pressed, new(double.NaN, 0), true);
        Check(!s.ShouldSteer(origin), "non-finite position cannot steer");
        foreach (var geometry in new[]{(960.0,540.0,false),(852.0,393.0,false),(1024.0,768.0,true)}) {
            var l=TouchControlLayout.Create(geometry.Item1,geometry.Item2,new(0,0,0,0),geometry.Item3,1);
            foreach (var point in new[]{l.Jump.Center,l.Dash.Center,l.Grab.Center,new TouchPoint(l.Pause.X+5,l.Pause.Y+5),new TouchPoint(l.Journal.X+5,l.Journal.Y+5)})
                Check(FeatherTouchState.IsAction(l,point), "action hit areas stay reserved");
            Check(!FeatherTouchState.IsAction(l,l.Movement.Center), "hidden joystick area is usable during flight");
        }
        Console.WriteLine("PASS_FEATHER_GESTURE_CONTROLS checks="+Checks);
    }
}

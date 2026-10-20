// Calls the actual game hair solver on a real player, then restores its state.
// This probe is host-only and is never included in the phone payload.
using System;
using System.Linq;
using Celeste;
using Monocle;
using Microsoft.Xna.Framework;
public static class HairMotionTests {
    static bool complete;
    public static void Tick() {
        if(complete || !(Engine.Scene is Level level) || CelesteJIT.Game.Platform.RunThreadActiveCount!=0 || Engine.DeltaTime<=0)return;
        var player=level.Tracker.GetEntity<Player>();if(player==null || player.Hair.Nodes.Count<2)return;
        complete=true;
        bool fixedBuild=Environment.GetEnvironmentVariable("CJIT_EXPECT_HAIR_FIXED")=="1";
        Calc.PushRandom(1337);
        try {
            var lava=new LavaRect(256,128,4);
            var flags=System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic;
            int bubbles=((Array)typeof(LavaRect).GetField("bubbles",flags).GetValue(lava)).Length;
            int surface=((Array)typeof(LavaRect).GetField("surfaceBubbles",flags).GetValue(lava)).Length;
            Console.WriteLine("LAVA_RESIZE_PROBE width="+lava.Width+" height="+lava.Height+" bubbles="+bubbles+" surface="+surface);
            if(fixedBuild && (lava.Width!=256 || lava.Height!=128 || bubbles!=163 || surface!=40))throw new Exception("Lava resize precision regression");
        } finally { Calc.PopRandom(); }
        var hair=player.Hair;var saved=hair.Nodes.ToArray();var facing=hair.Facing;var motion=hair.SimulateMotion;
        var step=hair.StepPerSegment;var inFacing=hair.StepInFacingPerSegment;var approach=hair.StepApproach;var sine=hair.StepYSinePerSegment;
        try {
            hair.Facing=Facings.Right;hair.SimulateMotion=true;hair.StepPerSegment=Vector2.Zero;hair.StepInFacingPerSegment=2;hair.StepApproach=120;hair.StepYSinePerSegment=0;
            hair.AfterUpdate();var root=hair.Nodes[0];
            for(int n=1;n<hair.Nodes.Count;n++)hair.Nodes[n]=root;
            hair.AfterUpdate();var moved=(hair.Nodes[1]-hair.Nodes[0]).Length();
            bool expectedFixed=Environment.GetEnvironmentVariable("CJIT_EXPECT_HAIR_FIXED")=="1";
            Console.WriteLine("HAIR_SOLVER_PROBE fixed_expected="+expectedFixed+" delta="+Engine.DeltaTime+" first_segment_travel="+moved);
            if(expectedFixed ? !(moved>0.1f && moved<=3.001f) : moved!=0)
                throw new Exception("Hair solver differential did not match the expected baseline/fix.");
            Console.WriteLine(expectedFixed?"PASS_REAL_GAME_HAIR_MOTION_RESTORED":"PASS_REPRODUCED_REAL_GAME_HAIR_MOTION_BUG");
        } finally {
            hair.Facing=facing;hair.SimulateMotion=motion;hair.StepPerSegment=step;hair.StepInFacingPerSegment=inFacing;hair.StepApproach=approach;hair.StepYSinePerSegment=sine;
            hair.Nodes.Clear();hair.Nodes.AddRange(saved);
        }
    }
}

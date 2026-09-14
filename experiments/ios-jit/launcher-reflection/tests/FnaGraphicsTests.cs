using System;
using System.Linq;
using System.Reflection;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Celeste;
using Monocle;
using MonoMod.RuntimeDetour;

// Loaded only by the desktop regression harness. Never placed in an IPA.
public static class FnaGraphicsTests
{
    private static bool done, paintIntroCompleted;
    private static int checks;
    private delegate int Original(GraphicsDevice device, RenderTargetBinding[] output);
    private delegate int Detour(Original orig, GraphicsDevice device, RenderTargetBinding[] output);
    private static void Check(bool value,string name) {
        if(!value)throw new InvalidOperationException("FNA graphics regression: "+name);
        checks++;Console.WriteLine("FNA_CONTRACT_PASS "+name);
    }
    public static void Run(GraphicsDevice device)
    {
        if(Engine.Scene is not Level level)return;
        if(done) {
            if(!paintIntroCompleted && level.Session.Area.GetSID()=="StrawberryJam2021/1-Beginner/mosscairn" && level.Session.GetFlag("introWatched") && level.Tracker.GetEntity<Player>()?.StateMachine.State==0) {
                paintIntroCompleted=true;Check(true,"original_paint_intro_completed_and_player_control_restored");
                Console.WriteLine("PASS_REAL_PAINT_LUA_INTRO_COMPLETED");
            }
            return;
        }
        if(level.Session.Area.GetSID()=="StrawberryJam2021/1-Beginner/mosscairn") {
            Check(level.Session.Level=="intro","original_paint_intro_loaded");
            Check(level.Entities.Any(e=>e.GetType().FullName=="Celeste.Mod.EeveeHelper.Entities.Containers.FlagGateContainer"),"original_eevee_flag_gate_awake_completed");
            // The native callback releases its display drawable at frame end.
            // Read the retained gameplay texture rather than that ended drawable.
            var target=GameplayBuffers.Gameplay.Target;
            var pixels=new Color[target.Width*target.Height];
            target.GetData(pixels);
            Check(pixels.Select(c=>c.PackedValue).Distinct().Take(17).Count()>16,"paint_frame_nonempty_gpu_readback");
            done=true;Console.WriteLine("PASS_REAL_PAINT_INTRO_AND_GPU_READBACK checks="+checks);return;
        }
        if(!level.Session.Area.GetSID().Contains("0-Lobbies/1-Beginner"))return;
        var frost=AppDomain.CurrentDomain.GetAssemblies().Single(a=>a.GetType("FrostHelper.CustomLavaRect")!=null);
        var lavaType=frost.GetType("FrostHelper.CustomLavaRect");
        Component lava=level.Entities.SelectMany(e=>e.Components).FirstOrDefault(c=>lavaType.IsInstanceOfType(c));
        Check(lava!=null,"original_lobby_contains_frost_lava");
        var original=device.GetRenderTargets();
        var targets=Enumerable.Range(0,4).Select(i=>new RenderTarget2D(device,8,8,false,SurfaceFormat.Color,DepthFormat.None,0,RenderTargetUsage.PreserveContents)).ToArray();
        try {
            for(int count=0;count<=4;count++) {
                var selected=targets.Take(count).Select(t=>new RenderTargetBinding(t)).ToArray();device.SetRenderTargets(selected);
                Check(device.GetRenderTargetsNoAllocEXT(null)==count,"null_query_"+count);
                var exact=new RenderTargetBinding[count];Check(device.GetRenderTargetsNoAllocEXT(exact)==count && exact.Select(x=>x.RenderTarget).SequenceEqual(selected.Select(x=>x.RenderTarget)),"exact_buffer_"+count);
                var large=Enumerable.Repeat(new RenderTargetBinding(targets[3]),6).ToArray();
                Check(device.GetRenderTargetsNoAllocEXT(large)==count && large.Take(count).Select(x=>x.RenderTarget).SequenceEqual(selected.Select(x=>x.RenderTarget)) && large.Skip(count).All(x=>x.RenderTarget==targets[3]),"oversized_tail_unchanged_"+count);
                if(count>0) {
                    bool rejected=false;try{device.GetRenderTargetsNoAllocEXT(new RenderTargetBinding[count-1]);}catch(ArgumentException){rejected=true;}
                    Check(rejected,"undersized_rejected_"+count);
                }
                Check(device.GetRenderTargets().Select(x=>x.RenderTarget).SequenceEqual(selected.Select(x=>x.RenderTarget)),"query_preserves_binding_"+count);
            }
            device.SetRenderTarget(targets[0]);var buffer=new RenderTargetBinding[4];
            for(int i=0;i<1000;i++)device.GetRenderTargetsNoAllocEXT(buffer);
            long before=GC.GetAllocatedBytesForCurrentThread();for(int i=0;i<10000;i++)device.GetRenderTargetsNoAllocEXT(buffer);
            Check(GC.GetAllocatedBytesForCurrentThread()==before,"ten_thousand_queries_allocate_zero_bytes");
            var store=frost.GetType("FrostHelper.Helpers.GraphicsDeviceExt").GetMethod("StoreRenderTargets",BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Static);
            foreach(int count in new[]{0,1,4}) {
                var selected=targets.Take(count).Select(t=>new RenderTargetBinding(t)).ToArray();device.SetRenderTargets(selected);
                object holder=store.Invoke(null,new object[]{device});device.SetRenderTarget(targets[3]);
                holder.GetType().GetMethod("Dispose").Invoke(holder,null);
                Check(device.GetRenderTargets().Select(x=>x.RenderTarget).SequenceEqual(selected.Select(x=>x.RenderTarget)),"original_frost_store_restore_"+count);
            }
            device.SetRenderTarget(targets[0]);device.Clear(new Color(23,91,177,255));device.SetRenderTarget(null);
            var pixels=new Color[64];targets[0].GetData(pixels);Check(pixels.All(x=>x==new Color(23,91,177,255)),"gpu_readback_after_target_round_trips");
            using var render=new RenderTarget2D(device,320,180,false,SurfaceFormat.Color,DepthFormat.None);
            device.SetRenderTarget(render);device.Clear(Color.Transparent);
            Vector2 position=lava.Entity.Position;int queries=0;
            using(var hook=new Hook(typeof(GraphicsDevice).GetMethod("GetRenderTargetsNoAllocEXT"),(Detour)((orig,gd,output)=>{queries++;return orig(gd,output);}))) {
                try {
                    var offset=(Vector2)lavaType.GetField("Position").GetValue(lava);
                    lava.Entity.Position=level.Camera.Position+new Vector2(40,40)-offset;
                    GameplayRenderer.Begin();lava.Render();GameplayRenderer.End();
                    Check(queries>=2,"original_custom_lava_render_reaches_target_store");
                    Check(device.GetRenderTargets().Single().RenderTarget==render,"lava_restores_gameplay_render_target");
                } finally {lava.Entity.Position=position;}
            }
            device.SetRenderTarget(null);
            var lavaPixels=new Color[320*180];render.GetData(lavaPixels);
            Check(lavaPixels.Any(x=>x.A!=0),"original_lava_produces_nonempty_gpu_pixels");
            done=true;Console.WriteLine("PASS_REAL_FROST_LAVA_AND_FNA_CONTRACT checks="+checks+" queryCalls="+queries);
        } finally {device.SetRenderTargets(original);foreach(var t in targets)t.Dispose();}
    }
}

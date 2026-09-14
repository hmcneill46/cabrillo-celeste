using System;
using System.Linq;
using System.Runtime.InteropServices;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
namespace CelesteJIT.Game;
public static class Entry
{
    private static Microsoft.Xna.Framework.Game game;private static GraphicsDeviceManager manager;private static int frame,checks;
    public static void Mark(string name,string message) {Console.WriteLine(name+" "+message);if(name=="graphics_check_fail")throw new Exception(message);}
    private static void Check(bool yes,string name) {if(!yes)throw new Exception("BACKBUFFER_FAIL "+name);checks++;Console.WriteLine("BACKBUFFER_PASS "+name);}
    private static void Reject<T>(Action action,string name) where T:Exception {
        try {action();}catch(T){Check(true,name);return;}throw new Exception("Expected "+typeof(T).Name+": "+name);
    }
    public static int Start(int unused) {
        game=new Microsoft.Xna.Framework.Game();manager=new GraphicsDeviceManager(game){PreferredBackBufferWidth=63,PreferredBackBufferHeight=47,SynchronizeWithVerticalRetrace=false};
        game.CJITBeginExternalLoop();return 1;
    }
    private static void Guards(GraphicsDevice d) {
        var a=Enumerable.Repeat(new Color(1,2,3,4),100).ToArray();var r=new Rectangle(0,0,2,2);
        Reject<ArgumentNullException>(()=>d.GetBackBufferData<Color>(null),"null_simple");
        Reject<ArgumentNullException>(()=>d.GetBackBufferData<Color>(r,null,0,1),"null_rectangle");
        Reject<ArgumentOutOfRangeException>(()=>d.GetBackBufferData(r,a,-1,4),"negative_start");
        Reject<ArgumentOutOfRangeException>(()=>d.GetBackBufferData(r,a,101,0),"past_end_start");
        Reject<ArgumentOutOfRangeException>(()=>d.GetBackBufferData(r,a,0,-1),"negative_count");
        Reject<ArgumentOutOfRangeException>(()=>d.GetBackBufferData(r,a,98,4),"offset_exceeds_capacity");
        Reject<ArgumentOutOfRangeException>(()=>d.GetBackBufferData(r,a,int.MaxValue,int.MaxValue),"overflow_arguments");
        Reject<ArgumentException>(()=>d.GetBackBufferData(r,a,0,3),"short_explicit_count");
        Reject<ArgumentException>(()=>d.GetBackBufferData(new Color[2]),"short_whole_buffer");
        foreach(var bad in new[]{new Rectangle(-1,0,1,1),new Rectangle(0,-1,1,1),new Rectangle(0,0,0,1),new Rectangle(0,0,1,-1),new Rectangle(int.MaxValue,0,2,1),new Rectangle(1,1,int.MaxValue,2),new Rectangle(d.PresentationParameters.BackBufferWidth,0,1,1)})
            Reject<ArgumentException>(()=>d.GetBackBufferData(bad,a,0,100),"invalid_rectangle_"+bad);
        Reject<ArgumentException>(()=>d.GetBackBufferData(r,new Vector3[4],0,4),"invalid_element_stride");
        Reject<ArgumentException>(()=>d.GetBackBufferData(r,new ReferencePixel[4],0,4),"reference_fields_rejected");
        Check(a.All(c=>c==new Color(1,2,3,4)),"rejections_preserve_destination");
        var oversized=Enumerable.Repeat((byte)0xBC,32).ToArray();d.GetBackBufferData(new Rectangle(0,0,1,1),oversized,3,24);
        Check(oversized.Take(3).Concat(oversized.Skip(7)).All(v=>v==0xBC),"oversized_segment_tail_untouched");
    }
    private struct ReferencePixel {public string Text;}
    private static Color savedColor;
    public static int Frame(int unused) {
        var d=game.GraphicsDevice;
        if(frame<6) {
            if(frame%2==0) {
                var pp=d.PresentationParameters.Clone();pp.BackBufferWidth=63+frame*9;pp.BackBufferHeight=47+frame*7;pp.BackBufferFormat=SurfaceFormat.Color;pp.MultiSampleCount=frame==0?0:frame==2?2:4;pp.RenderTargetUsage=RenderTargetUsage.PreserveContents;d.Reset(pp);
                Console.WriteLine("BACKBUFFER_CONFIG width="+pp.BackBufferWidth+" height="+pp.BackBufferHeight+" msaa="+d.PresentationParameters.MultiSampleCount);
                if(Environment.GetEnvironmentVariable("CJIT_ORIGINAL_BACKBUFFER")=="1") {d.Clear(Color.Red);Console.WriteLine("ABOUT_TO_READ_ORIGINAL_BACKBUFFER");d.GetBackBufferData(new Color[pp.BackBufferWidth*pp.BackBufferHeight]);throw new Exception("Original unexpectedly returned");}
                BackbufferChecks.Pattern(d);Guards(d);
                savedColor=new Color(19+frame,51,123,255);d.Clear(savedColor);d.Present();
                var pixels=new Color[9];d.GetBackBufferData(new Rectangle(2,3,3,3),pixels,0,9);Check(pixels.All(x=>x==savedColor),"after_present_"+frame);
            } else {
                var pixels=new Color[9];d.GetBackBufferData(new Rectangle(2,3,3,3),pixels,0,9);Check(pixels.All(x=>x==savedColor),"across_callback_pool_"+frame);
            }
        } else if(frame<15) {
            SurfaceFormat[] formats={SurfaceFormat.ColorBgraEXT,SurfaceFormat.Single,SurfaceFormat.Vector2,SurfaceFormat.Vector4,SurfaceFormat.HalfSingle,SurfaceFormat.HalfVector2,SurfaceFormat.HalfVector4,SurfaceFormat.HdrBlendable,SurfaceFormat.Rgba1010102};
            var format=formats[frame-6];var pp=d.PresentationParameters.Clone();pp.BackBufferWidth=37;pp.BackBufferHeight=23;pp.BackBufferFormat=format;pp.MultiSampleCount=0;d.Reset(pp);
            var clear=new Vector4(0.25f,0.5f,0.75f,1f);d.Clear(ClearOptions.Target,clear,1,0);
            int stride=format==SurfaceFormat.ColorBgraEXT||format==SurfaceFormat.Single||format==SurfaceFormat.HalfVector2||format==SurfaceFormat.Rgba1010102?4:format==SurfaceFormat.HalfSingle?2:format==SurfaceFormat.Vector4?16:8;
            var bytes=Enumerable.Repeat((byte)0xA5,6*stride+5).ToArray();d.GetBackBufferData(new Rectangle(3,4,3,2),bytes,2,6*stride);
            Check(bytes.Take(2).Concat(bytes.Skip(2+6*stride)).All(b=>b==0xA5),"format_guards_"+format);
            byte[] expected;
            if(format==SurfaceFormat.ColorBgraEXT)expected=new byte[]{191,128,64,255};
            else if(format==SurfaceFormat.Rgba1010102)expected=BitConverter.GetBytes((256u | (512u<<10) | (767u<<20) | (3u<<30)));
            else {
                bool half=format==SurfaceFormat.HalfSingle||format==SurfaceFormat.HalfVector2||format==SurfaceFormat.HalfVector4||format==SurfaceFormat.HdrBlendable;
                expected=new[]{.25f,.5f,.75f,1f}.Take(stride/(half?2:4)).SelectMany(v=>half?BitConverter.GetBytes(BitConverter.HalfToUInt16Bits((Half)v)):BitConverter.GetBytes(v)).ToArray();
            }
            Check(Enumerable.Range(0,6).All(i=>bytes.Skip(2+i*stride).Take(stride).SequenceEqual(expected)),"format_pixels_"+format);
        }
        game.CJITFinishGraphicsCallback();frame++;return frame>=15?2:1;
    }
    public static int Suspend(int unused) {game.CJITFinishGraphicsCallback();return 1;}
    public static int Resume(int unused) {return 1;}
    public static int Stop(int unused) {game.CJITEndExternalLoop();game.CJITFinishGraphicsCallback();var d=game.GraphicsDevice;game.Dispose();Reject<ObjectDisposedException>(()=>d.GetBackBufferData(new Color[1]),"disposed_simple");Reject<ObjectDisposedException>(()=>d.GetBackBufferData(new Rectangle(0,0,1,1),new Color[1],0,1),"disposed_rectangle");Console.WriteLine("PASS_ACTUAL_MONO_METAL_BACKBUFFER checks="+checks);return 1;}
}

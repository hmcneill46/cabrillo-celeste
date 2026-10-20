using System;
using System.Linq;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
namespace CelesteJIT.Game;

// Bounded canary for this renderer increment. Runs once during content load,
// then takes a small real-frame sample after presentation and after resume.
internal static class BackbufferChecks
{
    private static readonly Color[] Palette = {new Color(23,91,177,255),new Color(201,67,11,255),new Color(37,193,71,255),new Color(153,41,217,255)};
    private static void Check(bool ok,string name) {
        Entry.Mark(ok?"graphics_check_pass":"graphics_check_fail","backbuffer_"+name);
        if(!ok)throw new InvalidOperationException("Backbuffer check failed: "+name);
    }
    private static Color At(int x,int y,int w,int h)=>Palette[(x>=w/2?1:0)+(y>=h/2?2:0)];
    public static void Pattern(GraphicsDevice d)
    {
        int w=d.PresentationParameters.BackBufferWidth,h=d.PresentationParameters.BackBufferHeight;
        if(w<16||h<16||d.PresentationParameters.BackBufferFormat!=SurfaceFormat.Color)throw new InvalidOperationException("Pattern requires Color backbuffer at least 16x16");
        var oldTargets=d.GetRenderTargets();var oldViewport=d.Viewport;var oldScissor=d.ScissorRectangle;
        var blend=d.BlendState;var depth=d.DepthStencilState;var raster=d.RasterizerState;var sampler=d.SamplerStates[0];var oldTexture=d.Textures[0];
        try {
            d.SetRenderTarget(null);d.Viewport=new Viewport(0,0,w,h);
            d.Clear(Palette[0]);var probe=new Color[4];d.GetBackBufferData(new Rectangle(3,5,2,2),probe,0,4);
            Check(probe.All(c=>c==Palette[0]),"deferred_clear_visible");
            using var white=new Texture2D(d,1,1);white.SetData(new[]{Color.White});using var batch=new SpriteBatch(d);
            batch.Begin(SpriteSortMode.Deferred,BlendState.Opaque,SamplerState.PointClamp,DepthStencilState.None,RasterizerState.CullNone);
            for(int y=0;y<2;y++)for(int x=0;x<2;x++) {
                int xx=x==0?0:w/2,yy=y==0?0:h/2;
                batch.Draw(white,new Rectangle(xx,yy,x==0?w/2:w-w/2,y==0?h/2:h-h/2),Palette[x+2*y]);
            }
            batch.End();
            var all=new Color[w*h];d.GetBackBufferData(all);
            Check(all.Where((c,i)=>c!=At(i%w,i/w,w,h)).Take(1).Count()==0,"full_rgba_orientation_and_rows");
            var rect=new Rectangle(w/2-3,h/2-2,7,5);var sentinel=new Color(9,8,7,6);
            var segment=Enumerable.Repeat(sentinel,42).ToArray();d.GetBackBufferData(rect,segment,3,35);
            Check(segment.Take(3).Concat(segment.Skip(38)).All(c=>c==sentinel)&&Enumerable.Range(0,35).All(i=>segment[i+3]==At(rect.X+i%7,rect.Y+i/7,w,h)),"rectangle_offset_and_guards");
            var bytes=Enumerable.Repeat((byte)0xAB,149).ToArray();d.GetBackBufferData(rect,bytes,5,140);
            Check(bytes.Take(5).Concat(bytes.Skip(145)).All(c=>c==0xAB)&&Enumerable.Range(0,35).All(i=> {
                Color c=At(rect.X+i%7,rect.Y+i/7,w,h);int k=5+4*i;return bytes[k]==c.R&&bytes[k+1]==c.G&&bytes[k+2]==c.B&&bytes[k+3]==c.A;
            }),"byte_stride_rgba_and_guards");
            // Continue drawing after the readback ended/resolved a render pass.
            batch.Begin(SpriteSortMode.Deferred,BlendState.Opaque,SamplerState.PointClamp,DepthStencilState.None,RasterizerState.CullNone);
            batch.Draw(white,new Rectangle(0,0,2,2),Color.White);batch.End();d.GetBackBufferData(all,0,all.Length);
            Check(all.Where((c,i)=>c!=((i%w<2&&i/w<2)?Color.White:At(i%w,i/w,w,h))).Take(1).Count()==0,"continued_draw_preserves_other_pixels");
            using var target=new RenderTarget2D(d,8,8,false,SurfaceFormat.Color,DepthFormat.None,0,RenderTargetUsage.PreserveContents);
            d.SetRenderTarget(target);d.Clear(Color.Orange);
            d.GetBackBufferData(new Rectangle(4,4,1,1),probe,0,1);
            Check(probe[0]==At(4,4,w,h)&&d.GetRenderTargets().Single().RenderTarget==target,"reads_backbuffer_while_other_target_bound");
            var targetPixels=new Color[64];target.GetData(targetPixels);
            Check(targetPixels.All(c=>c==Color.Orange),"pending_offscreen_clear_survives_read");
            d.SetRenderTarget(null);
            Entry.Mark("game_backbuffer_pattern_pass","width="+w+"; height="+h+"; format=Color; msaa="+d.PresentationParameters.MultiSampleCount+"; checks=7");
        } finally {
            d.SetRenderTargets(oldTargets);d.Viewport=oldViewport;d.ScissorRectangle=oldScissor;
            d.BlendState=blend;d.DepthStencilState=depth;d.RasterizerState=raster;d.SamplerStates[0]=sampler;d.Textures[0]=oldTexture;
        }
    }
    public static void Frame(GraphicsDevice d,string phase)
    {
        int w=d.PresentationParameters.BackBufferWidth,h=d.PresentationParameters.BackBufferHeight;
        var rect=new Rectangle(w/2-16,h/2-9,32,18);var pixels=new Color[rect.Width*rect.Height];
        d.GetBackBufferData(rect,pixels,0,pixels.Length);
        uint hash=2166136261;foreach(var pixel in pixels)hash=unchecked((hash^pixel.PackedValue)*16777619);
        Entry.Mark("game_backbuffer_frame_pass","phase="+phase+"; width="+w+"; height="+h+"; sample=32x18; fnv="+hash.ToString("x8"));
    }
}

// External host observation only; never compiled into the phone adapter.
using System;
using System.IO;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Monocle;
public static class SessionIntegrationTests {
    private static int frames;
    public static void Run(GraphicsDevice device) {
        frames++;
        if(frames!=1 && frames!=15 && frames!=60 && frames!=120 && frames!=240 && frames!=600)return;
        int w=device.PresentationParameters.BackBufferWidth,h=device.PresentationParameters.BackBufferHeight;
        var pixels=new Color[w*h];device.GetBackBufferData(pixels);
        int visible=0;foreach(var p in pixels)if(p.R!=0 || p.G!=0 || p.B!=0)visible++;
        string path=Path.Combine(Environment.GetEnvironmentVariable("CJIT_FRAME_CAPTURE"),"frame-"+frames.ToString("D4")+".png");
        using var texture=new Texture2D(device,w,h);texture.SetData(pixels);
        using var stream=File.Create(path);texture.SaveAsPng(stream,w,h);
        Console.WriteLine("FIRST_FRAME_SAMPLE frame="+frames+"; scene="+Engine.Scene?.GetType().FullName+"; nonblack_pixels="+visible+"; pixels="+pixels.Length);
    }
}

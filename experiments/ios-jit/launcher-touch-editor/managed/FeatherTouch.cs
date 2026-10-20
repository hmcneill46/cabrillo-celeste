using System.Reflection;
using Celeste;
using CelesteIOSFoundation;
using Microsoft.Xna.Framework;
using Monocle;

namespace CelesteJIT.Game;

public static class FeatherTouch
{
    public static readonly bool Enabled = Environment.GetEnvironmentVariable("CJIT_FEATHER_TOUCH") == "1";
    internal static readonly FeatherTouchState Gesture = new();
    // Set only the feather virtual input after MInput has finished polling.
    // This deliberately writes zero too, instead of leaving a previous node's
    // joystick direction in place. Aim, movement and hardware polling stay intact.
    private static readonly Action<VirtualJoystick, Vector2> setValue =
        (Action<VirtualJoystick, Vector2>)typeof(VirtualJoystick).GetProperty(nameof(VirtualJoystick.Value))
            .GetSetMethod(true).CreateDelegate(typeof(Action<VirtualJoystick, Vector2>));

    internal static Player PlayerInFlight()
    {
        if (!Enabled || !TouchPort.Visible || MInput.Disabled || Engine.Scene is not Level level ||
            level.Paused || level.Frozen || level.Transitioning) return null;
        var player = level.Tracker.GetEntity<Player>();
        return player != null && !player.Dead && player.StateMachine.State == Player.StStarFly ? player : null;
    }

    // Use the same forward transform in both directions. Motion Smoothing adjusts
    // CameraToScreen for drawing, while ScreenToCamera can remain unsmoothed; mixing World's two conversion helpers would offset the target.
    // A 64-pixel basis avoids cancellation on maps with large world coordinates.
    public static Vector2 PointToWorld(Level level, TouchPoint point, double width, double height)
    {
        var device = Engine.Instance.GraphicsDevice;
        var viewport = Engine.Viewport;
        var pixel = new Vector2((float)(point.X * device.PresentationParameters.BackBufferWidth / width) - viewport.X,
                                (float)(point.Y * device.PresentationParameters.BackBufferHeight / height) - viewport.Y);
        var screen = Vector2.Transform(pixel, Matrix.Invert(Engine.ScreenMatrix));
        var origin = level.WorldToScreen(Vector2.Zero);
        var x = level.WorldToScreen(new Vector2(64,0)) - origin;
        var y = level.WorldToScreen(new Vector2(0,64)) - origin;
        double determinant = (double)x.X*y.Y - (double)x.Y*y.X;
        if (!double.IsFinite(determinant) || Math.Abs(determinant)<0.000001)
            return new Vector2(float.NaN,float.NaN); // Invalid projection -> neutral.
        var delta = screen - origin;
        return new Vector2((float)(64*((double)delta.X*y.Y - (double)delta.Y*y.X)/determinant),
                           (float)(64*((double)x.X*delta.Y - (double)x.Y*delta.X)/determinant));
    }

    public static TouchPoint WorldToPoint(Level level, Vector2 world, double width, double height)
    {
        var device = Engine.Instance.GraphicsDevice;
        var pixel = Vector2.Transform(level.WorldToScreen(world), Engine.ScreenMatrix);
        return new((pixel.X + Engine.Viewport.X) * width / device.PresentationParameters.BackBufferWidth,
                   (pixel.Y + Engine.Viewport.Y) * height / device.PresentationParameters.BackBufferHeight);
    }

    public static bool InGameArea(TouchPoint point, double width, double height)
    {
        var p = Engine.Instance.GraphicsDevice.PresentationParameters;
        var view = Engine.Viewport;
        return new TouchRect(view.X * width / p.BackBufferWidth, view.Y * height / p.BackBufferHeight,
            view.Width * width / p.BackBufferWidth, view.Height * height / p.BackBufferHeight).Contains(point);
    }

    internal static void AfterInputUpdate(double width, double height)
    {
        var player = PlayerInFlight();
        Gesture.BeginFrame(player);
        if (player == null || Input.Feather == null) return;
        var level = (Level)player.Scene;
        var direction = Vector2.Zero;
        if (Gesture.ShouldSteer(WorldToPoint(level, player.Center, width, height))) {
            var delta = PointToWorld(level, Gesture.Target, width, height) - player.Center;
            float length = delta.Length();
            if (float.IsFinite(length) && length > 0.001f) direction = delta / length;
        }
        setValue(Input.Feather, direction);
    }
}

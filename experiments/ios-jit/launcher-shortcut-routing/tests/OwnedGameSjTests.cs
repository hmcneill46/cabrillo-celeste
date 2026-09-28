using System;
using Celeste;
using Monocle;
using Microsoft.Xna.Framework.Graphics;
public static class SessionIntegrationTests
{
    private static string room;
    public static void Run(GraphicsDevice device)
    {
        if (Engine.Scene is not Level level || level.Tracker.GetEntity<Player>() is not Player player) return;
        if (!float.IsFinite(player.X) || !float.IsFinite(player.Y)) throw new Exception("Non-finite player position");
        string current=level.Session.Area.GetSID()+"/"+level.Session.Level;
        if (current==room) return;
        room=current;
        Console.WriteLine("PASS_OWNED_SJ_ROOM "+room);
    }
}

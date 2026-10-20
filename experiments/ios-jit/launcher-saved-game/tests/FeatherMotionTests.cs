// Host-only combined input and original Motion Smoothing observation.
using Microsoft.Xna.Framework.Graphics;
public static class SessionIntegrationTests {
    public static void Run(GraphicsDevice device) {
        MotionSmoothingTests.Run(device);
        FeatherIntegrationTests.Run(device);
    }
}

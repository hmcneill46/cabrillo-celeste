// Private host fixture; never packaged.
using Microsoft.Xna.Framework.Graphics;
public static class SessionIntegrationTests {
    public static void Run(GraphicsDevice device) {
        MotionSmoothingTests.Run(device);
        FeatherIntegrationTests.Run(device);
        TouchInputIntegrationTests.Run();
        InputPreferencesIntegrationTests.Run();
    }
}

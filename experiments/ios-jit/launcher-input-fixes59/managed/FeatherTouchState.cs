using CelesteIOSFoundation;

namespace CelesteJIT.Game;

// Gesture ownership is independent of rendering and game timing. Only a fresh
// press in flight can acquire steering. An action-button finger never becomes
// a target, and a second finger never takes over when the first is released.
public sealed class FeatherTouchState
{
    private readonly int?[] captured = new int?[TouchInteractionState.MaximumTouches];
    private int? owner;
    private object context;
    private bool coasting = true;
    public bool Active => context != null;
    public bool HasTarget => owner.HasValue;
    public TouchPoint Target { get; private set; }
    public const double CoastRadius = 16;
    public const double SteerRadius = 22;

    public void BeginFrame(object flight)
    {
        if (!ReferenceEquals(context, flight)) {
            // Keep captured fingers quarantined until release across pause,
            // death or flight exit; they must not turn into movement/buttons.
            owner = null;
            coasting = true;
        }
        context = flight;
    }

    public bool Apply(int id, TouchPhase phase, TouchPoint point, bool eligible)
    {
        int slot = Array.IndexOf(captured, (int?)id);
        if (slot >= 0 && phase == TouchPhase.Pressed) {
            // SDL may reuse a cancelled finger ID without an intervening up.
            captured[slot] = null;
            if (owner == id) { owner = null; coasting = true; }
            slot = -1;
        }
        if (phase == TouchPhase.Released) {
            if (slot < 0) return false;
            captured[slot] = null;
            if (owner == id) { owner = null; coasting = true; }
            return true;
        }
        if (slot < 0 && phase == TouchPhase.Pressed && Active && eligible) {
            slot = Array.IndexOf(captured, null);
            if (slot < 0) return true; // Overflow must not become a game action.
            captured[slot] = id;
            if (!owner.HasValue) { owner = id; coasting = true; }
        }
        if (slot < 0) return false;
        if (owner == id) Target = point;
        return true;
    }

    public void ReleaseMissing(ReadOnlySpan<int> active)
    {
        for (int i = 0; i < captured.Length; i++) {
            if (captured[i] is not int id || active.Contains(id)) continue;
            captured[i] = null;
            if (owner == id) { owner = null; coasting = true; }
        }
    }

    public bool ShouldSteer(TouchPoint player)
    {
        if (!Active || !HasTarget) return false;
        double distance = (Target - player).Length;
        if (!double.IsFinite(distance)) return false;
        coasting = distance <= (coasting ? SteerRadius : CoastRadius);
        return !coasting;
    }

    public void Reset()
    {
        Array.Clear(captured); owner = null; context = null; coasting = true;
    }

    public static bool IsAction(TouchControlLayout layout, TouchPoint point) =>
        layout.Jump.Contains(point) || layout.Dash.Contains(point) || layout.Grab.Contains(point) ||
        layout.Pause.Contains(point) || layout.Journal.Contains(point);
}

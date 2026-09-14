"""Carry the existing Stage 24D2 logical-input extension into the private JIT game."""
def apply(work,replace):
    # Same extension points and semantics as scripts/celeste-ios-stage24d2.py.
    p=work/'Monocle/VirtualButton.cs'
    replace(p,'using Microsoft.Xna.Framework.Input;','using System;\nusing Microsoft.Xna.Framework.Input;')
    replace(p,'public class VirtualButton : VirtualInput\n{\n\tpublic Binding Binding;', 'public class VirtualButton : VirtualInput\n{\n\tpublic Func<bool> AdditionalCheck, AdditionalPressed, AdditionalReleased;\n\tpublic Binding Binding;')
    for method in ['Check','Pressed','Released']:
        replace(p,'return Binding.'+method+'(GamepadIndex, Threshold);','return Binding.'+method+'(GamepadIndex, Threshold) || (Additional'+method+'?.Invoke() ?? false);')
    replace(p,'if (Binding.Pressed(GamepadIndex, Threshold))','if (Binding.Pressed(GamepadIndex, Threshold) || (AdditionalPressed?.Invoke() ?? false))')
    replace(p,'else if (Binding.Check(GamepadIndex, Threshold))','else if (Binding.Check(GamepadIndex, Threshold) || (AdditionalCheck?.Invoke() ?? false))')
    p=work/'Monocle/VirtualIntegerAxis.cs'
    replace(p,'namespace Monocle;','using System;\nnamespace Monocle;')
    replace(p,'public class VirtualIntegerAxis : VirtualInput\n{','public class VirtualIntegerAxis : VirtualInput\n{\n\tpublic Func<int> AdditionalValue;')
    replace(p,'\t\tif (Inverted)\n\t\t{','\t\tint extra = AdditionalValue?.Invoke() ?? 0;\n\t\tif (extra != 0) Value = Math.Sign(extra);\n\t\tif (Inverted)\n\t\t{')
    p=work/'Monocle/VirtualJoystick.cs'
    replace(p,'using Microsoft.Xna.Framework;','using System;\nusing Microsoft.Xna.Framework;')
    replace(p,'public class VirtualJoystick : VirtualInput\n{','public class VirtualJoystick : VirtualInput\n{\n\tpublic Func<Vector2> AdditionalValue;')
    replace(p,'\t\tValue = new Vector2(InvertedX ?', '\t\tVector2 extra = AdditionalValue?.Invoke() ?? Vector2.Zero;\n\t\tif (extra != Vector2.Zero) value = extra;\n\t\tValue = new Vector2(InvertedX ?')
    p=work/'Celeste/Input.cs'
    replace(p,'public static bool GrabCheck => Settings.Instance.GrabMode switch', 'public static bool GrabCheck => CelesteIOSFoundation.TouchGrabPolicy.Resolve(CelesteJIT.Game.TouchPort.Grab, CelesteJIT.Game.TouchPort.Visible, CelesteJIT.Game.TouchPort.ControllerConnected, ControllerGrabCheck);\n\tprivate static bool ControllerGrabCheck => Settings.Instance.GrabMode switch')
    replace(p,'MenuCancel = new VirtualButton(Settings.Instance.Cancel, Gamepad, 0f, 0.2f);','MenuCancel = new VirtualButton(Settings.Instance.Cancel, Gamepad, 0f, 0.2f);\n\t\tCelesteJIT.Game.TouchPort.Bind();')
    replace(work/'Monocle/Engine.cs','\t\tFrameCounter++;\n\t\tMInput.Update();','\t\tFrameCounter++;\n\t\tCelesteJIT.Game.TouchPort.Update();\n\t\tMInput.Update();')

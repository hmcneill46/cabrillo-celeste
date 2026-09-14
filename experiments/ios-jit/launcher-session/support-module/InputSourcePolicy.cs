namespace CelesteIOS;
// Activity wins, with deterministic touch priority for simultaneous events.
// An idle connected pad must not immediately take prompts back from touch.
public sealed class InputSourcePolicy
{
    public InputSource Current {get;private set;}=InputSource.Touch;
    public bool Observe(bool touchActivity,bool keyActivity,bool padActivity,bool padConnected)
    {
        var previous=Current;
        if(Current==InputSource.Controller && !padConnected)Current=InputSource.Touch;
        if(keyActivity)Current=InputSource.Keyboard;
        if(padActivity && padConnected)Current=InputSource.Controller;
        if(touchActivity)Current=InputSource.Touch;
        return Current!=previous;
    }
}

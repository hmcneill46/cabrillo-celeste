-- Runs inside the original LuaCutscenes helper and Everest LuaCoroutine.
local probe = require("#CJITGravityProbe.HelperProbeModule")

function onBegin()
    wait(0.2)
    disableMovement()
    assert(probe.LuaCheckpoint("begin", player.X, player.Y) == 42)
    walk(24)
    wait(0.25)
    enableMovement()
    probe.LuaCheckpoint("waiting", player.X, player.Y)
    setFlag("cjit_sj_lua_waiting", true)
    while probe.ResumeSignals == 0 do
        wait(0.1)
    end
    wait(0.3)
    probe.LuaCheckpoint("resumed", player.X, player.Y)
    setFlag("cjit_sj_lua_completed", true)
end

function onEnd(room, wasSkipped)
    enableMovement()
    probe.LuaCheckpoint(wasSkipped and "skipped" or "end", player.X, player.Y)
end

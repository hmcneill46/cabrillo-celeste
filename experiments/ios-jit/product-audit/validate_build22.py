"""Validate the preserved phone export without conflating its four sessions.

Read-only against phone evidence and delivered build22. Writes a derived receipt
beside the private export. Run from any directory with Python 3.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / ".build/ios-jit/device-evidence/2026-09-12/build-22-results"
RAW = OUT / "CelesteJIT-6b626dd9-ba01-4afc-a019-f3c5b65e663a.diagnostics.json"
raw = RAW.read_bytes()
digest = hashlib.sha256(raw).hexdigest()
assert digest == "05b9b03285f37cba12c94ee787f04be3de9c88168b2cf375103a10bfe69d79ae"
data = json.loads(raw)
receipt = json.loads((ROOT / "artifacts/ios-jit/launcher-reflection-20260912-22/build-receipt.json").read_text())
assert data["schema"] == 2 and data["storage_error"] is None
assert data["device"]["hardware"] == "iPhone16,2" and data["device"]["os_version"] == "26.5"
assert all(receipt[k] == v for k, v in data["build"].items())

# The current process only exported logs; the played session is in history.
assert len(data["current_events"]) == 7
assert not any(e["event"] == "game_start_returned" for e in data["current_events"])
played = [s for s in data["previous_sessions"] if any(
    e["event"] == "native_launch" and e["fields"]["build"]["build_id"] == receipt["build_id"]
    for e in s["events"])]
assert len(played) == 1
session = played[0]
assert not session["bounded_excerpt"] and session["invalid_or_partial_lines"] == 0
events = session["events"]

def rows(name):
    return [e for e in events if e["event"] == name]

def one(name):
    found = rows(name)
    assert len(found) == 1, (name, len(found))
    return found[0]

launch = one("native_launch")
assert all(receipt[k] == v for k, v in launch["fields"]["build"].items())
counts = rows("diagnostic_counters")[-1]["fields"]
c = counts["counts"]
assert c["check_pass"] == 26 and c["graphics_check_pass"] == 13
for name in ["check_fail", "graphics_check_fail", "mono_jit_failed", "managed_exception",
             "managed_exception_detail", "graphics_frame_failed", "graphics_bridge_incomplete"]:
    assert c.get(name, 0) == 0 and not rows(name), name
assert counts["allocation_overflow"] == 0
selection = one("launcher_run_prepared")["fields"]["selection"]
assert selection["canRun"] and not selection["issues"]
assert selection["enabledCount"] == selection["installedCount"] == 56
assert len(selection["modules"]) == 56
assert "All 58 selected/built-in metadata identities match" in one("everest_selection_pass")["fields"]["message"]
assert one("launcher_landscape_ready")["fields"]["regression_mode"] is False
assert not rows("everest_test_map_requested") and not rows("sj_bing_button")
rooms = [e["fields"]["message"] for e in rows("game_room")]
paint_sequence = ["area=44; room=" + r for r in ["intro", "a-00", "a-01", "a-02"]]
assert all(r in rooms for r in paint_sequence)
assert [rooms.index(r) for r in paint_sequence] == sorted(rooms.index(r) for r in paint_sequence)
assert one("everest_mod_save_pass")["fields"]["message"] == "prior=102; written=320; readback=320; bytes=11"
assert "SaveData slot=1; bytes=162410; deaths=37" in [e["fields"]["message"] for e in rows("game_save_pass")]
assert all(e["fields"]["passed"] for e in rows("graphics_native_resumed"))
assert len(rows("graphics_native_resumed")) == 3
assert max(e["fields"]["background_seconds"] for e in rows("graphics_native_resumed")) > 27
assert all(e["fields"]["reason"] == "finish_button" and not e["fields"]["failure"] for e in rows("graphics_stop_start"))
assert one("graphics_finish_button")["fields"]["frame_callbacks"] == 82199

# Absence of final completion is material, even though gameplay/save checks pass.
assert not rows("game_checks_pass") and not rows("graphics_bridge_pass")
assert not rows("graphics_main_thread_detached") and not rows("graphics_result_presented")
samples = rows("graphics_sample")
last_runtime = samples[-1]["fields"]["runtime"]
assert last_runtime["code_reserved_bytes"] == 235503616
assert last_runtime["code_budget_bytes"] == 536870912
for name in ["jit_failed", "jit_unowned", "managed_errors", "patch_rejections"]:
    assert all(s["fields"]["runtime"][name] == 0 for s in samples)

result = {
    "schema": 1,
    "status": "PASS_BUILD22_RECORDED_GAMEPLAY_AND_SAVE_READBACK_SHUTDOWN_UNVERIFIED",
    "build_id": receipt["build_id"],
    "raw_path": str(RAW.relative_to(ROOT)), "raw_bytes": len(raw), "raw_sha256": digest,
    "export_session": data["session"], "played_session": launch["session"],
    "played_pid": launch["fields"]["process"]["pid"],
    "exact_build_identity_matches": True, "ipa_sha256": receipt["ipa_sha256"],
    "device": data["device"],
    "owner_report": "All passed; owner later could not remember whether SESSION SAVED appeared before closing.",
    "old_build21_sessions_in_same_export": len(data["previous_sessions"]) - 1,
    "native_checks": 26, "graphics_checks": 13,
    "normal_play": True, "regression_shortcuts_used": False,
    "enabled_zip_count": 56, "verified_metadata_identities": 58,
    "room_transitions": rooms,
    "paint_identity_scope": "Area44 intro/a-00/a-01/a-02 is consistent with the prescribed Paint retest and pinned map set. Phone room events record numeric area, not SID; future logs should include SID.",
    "seconds_from_game_start_to_finish": round(one("graphics_finish_button")["time_unix"] - one("game_start_returned")["time_unix"], 3),
    "frame_callbacks": 82199, "background_resume_count": 3,
    "longest_recorded_background_seconds": max(e["fields"]["background_seconds"] for e in rows("graphics_native_resumed")),
    "jump_count": 218, "mod_save_prior": 102, "mod_save_written_and_readback": 320,
    "save_slot": 1, "save_bytes": 162410, "save_deaths": 37,
    "last_sample_runtime_before_teardown": last_runtime,
    "peak_sampled_physical_footprint_bytes": max(s["fields"]["native"]["physical_footprint_bytes"] for s in samples),
    "last_counter_total_events": counts["total"],
    "last_counter_jit_done": c["mono_jit_done"],
    "tracked_jit_or_managed_failures": 0,
    "last_journal_seconds_after_finish": round(events[-1]["time_unix"] - one("graphics_finish_button")["time_unix"], 3),
    "clean_shutdown_confirmed": False, "shutdown_crash_proven": False,
    "fresh_process_post_test_save_reload_confirmed": False,
    "limits": ["New export process did not run the game.",
               "Save readback is in the played process; exact checkpoint reload is not established.",
               "Final 27.55-second resume has no subsequent recorded jump; earlier resumes do.",
               "No game_checks_pass, native detach or graphics_bridge_pass before journal ends during teardown.",
               "All-mod compatibility and indefinite memory/code headroom are not established."]
}
(OUT / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: result[k] for k in ["status", "seconds_from_game_start_to_finish", "peak_sampled_physical_footprint_bytes", "last_journal_seconds_after_finish"]}, indent=2))

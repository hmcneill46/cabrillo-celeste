#!/usr/bin/env python3
"""Use a booted simulator to check startup/export/recovery, never native JIT."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import shutil

root = Path(__file__).resolve().parents[4]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--device", required=True, help="UDID of an already booted simulator")
parser.add_argument("--build-id", default="everest-canary-20260911-13-simulator")
args = parser.parse_args()
env = dict(os.environ, DEVELOPER_DIR="/Applications/Xcode-26.6.app/Contents/Developer")
app = root / "artifacts/ios-jit" / args.build_id / "CelesteJITEverest.app"
out = root / ".build/ios-jit/everest-canary" / args.build_id / "smoke"
out.mkdir(parents=True, exist_ok=True)
bundle = "io.github.hmcneill46.celeste.everest.jit.everest"

def sim(*words, check=True):
    return subprocess.run(["xcrun", "simctl", *words], env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)

def launch_and_export():
    old = set(directory.glob("*.diagnostics.json"))
    sim("launch", args.device, bundle, "--probe-ui-test-export", "--probe-ui-test-path-alias", "--canary-ui-test-import", "--canary-ui-test-log-burst", "--hook-ui-test-protocol")
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        new = set(directory.glob("*.diagnostics.json")) - old
        if new:
            data = json.loads(next(iter(new)).read_text())
            assert data["device"]["simulator"] == 1
            assert data["build"]["build_id"] == args.build_id
            names = [event["event"] for event in data["current_events"]]
            assert "native_launch" in names and "diagnostics_export" in names
            assert any(e["event"] == "host_ui_path_alias_check" and e["fields"]["enabled"] for e in data["current_events"])
            assert not any("g0_memory_pass" == name or "jit_request_created" == name for name in names)
            assert [e['fields']['index'] for e in data['current_events'] if e['event'] in ('host_ui_burst', 'host_ui_burst_complete')] == list(range(800))
            assert any(e['event'] == 'host_ui_log_burst_check' and e['fields']['rendered_through_burst'] for e in data['current_events'])
            return data
        time.sleep(0.1)
    raise RuntimeError("Simulator did not create a diagnostic export within 30 seconds")

sim("terminate", args.device, bundle, check=False)
sim("install", args.device, str(app))
container = Path(sim("get_app_container", args.device, bundle, "data").stdout.strip())
directory = container / "Documents/Diagnostics"
directory.mkdir(parents=True, exist_ok=True)
for source in (root / ".build/ios-jit/everest-mods").glob("*.zip"):
    shutil.copy2(source,container / "Documents" / source.name)
first = launch_and_export()
request_events = [e for e in first["current_events"] if e["event"] == "host_ui_protocol_request"]
assert len(request_events) == 1
request_sample = request_events[0]["fields"]
assert request_sample["simulator"] and request_sample["debugger_commands_sent"] == 0
assert request_sample["request"]["length"] == 33554432
assert request_sample["compiled_protocol"]["bytes_per_arena"] == first["build"]["bytes_per_arena"]
(out / "native-generated-request.json").write_text(json.dumps(request_sample, indent=2) + "\n")
assert any(e["event"] == "mod_zip_imported" for e in first["current_events"])
assert any(e["event"] == "host_ui_import_check" and e["fields"]["managed_run_disabled_without_jit"] for e in first["current_events"])
assert "CJIT native console recovery sentinel" in first["native_console_tail"]
sim("terminate", args.device, bundle)
second = launch_and_export()
assert first["session"] != second["session"]
assert any("CJIT native console recovery sentinel" in s["native_console_tail"] for s in second["previous_sessions"])
previous = second["previous_sessions"]
assert any(any(event.get("session") == first["session"] for event in session["events"]) for session in previous)
assert not any(any(event.get("session") == second["session"] for event in session["events"]) for session in previous)
(out / "simulator-export.json").write_text(json.dumps(second, indent=2) + "\n")
# Let the simulator's launch animation finish before capturing its real UI.
time.sleep(1)
sim("io", args.device, "screenshot", str(out / "ui.png"))
receipt = {"status": "PASS_SIMULATOR_IMPORT_STARTUP_EXPORT_AND_CONSOLE_RECOVERY", "mod_zip_import_handler": "PASS", "run_disabled_without_jit": True, "native_console_recovered": True, "build_id": args.build_id,
           "background_event_burst_persisted_and_rendered": 800,
           "os": second["device"]["os_version"], "architecture": second["device"]["hardware"],
           "previous_session_recovered": True, "current_session_not_duplicated": True, "export_schema": second["schema"],
           "device_jit_execution": "NOT TESTED", "share_sheet_interaction": "NOT AUTOMATED",
           "notes": "Host terminated only the simulator probe between launches. Generated-code paths are disabled."}
(out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))

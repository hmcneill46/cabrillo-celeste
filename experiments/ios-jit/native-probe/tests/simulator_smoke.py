#!/usr/bin/env python3
"""Use a booted simulator to check startup/export/recovery, never native JIT."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

root = Path(__file__).resolve().parents[4]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--device", required=True, help="UDID of an already booted simulator")
parser.add_argument("--build-id", default="native-probe-20260911-03-simulator")
args = parser.parse_args()
env = dict(os.environ, DEVELOPER_DIR="/Applications/Xcode-26.6.app/Contents/Developer")
app = root / "artifacts/ios-jit" / args.build_id / "CelesteJITProbe.app"
out = root / ".build/ios-jit/native-probe" / args.build_id / "smoke"
out.mkdir(parents=True, exist_ok=True)
bundle = "io.github.hmcneill46.celeste.everest.jit.probe"

def sim(*words, check=True):
    return subprocess.run(["xcrun", "simctl", *words], env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)

def launch_and_export():
    old = set(directory.glob("*.diagnostics.json"))
    sim("launch", args.device, bundle, "--probe-ui-test-export", "--probe-ui-test-path-alias")
    deadline = time.monotonic() + 15
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
            return data
        time.sleep(0.1)
    raise RuntimeError("Simulator did not create a diagnostic export within 15 seconds")

sim("terminate", args.device, bundle, check=False)
sim("install", args.device, str(app))
container = Path(sim("get_app_container", args.device, bundle, "data").stdout.strip())
directory = container / "Documents/Diagnostics"
first = launch_and_export()
sim("terminate", args.device, bundle)
second = launch_and_export()
assert first["session"] != second["session"]
previous = second["previous_sessions"]
assert any(any(event.get("session") == first["session"] for event in session["events"]) for session in previous)
assert not any(any(event.get("session") == second["session"] for event in session["events"]) for session in previous)
(out / "simulator-export.json").write_text(json.dumps(second, indent=2) + "\n")
# Let the simulator's launch animation finish before capturing its real UI.
time.sleep(1)
sim("io", args.device, "screenshot", str(out / "ui.png"))
receipt = {"status": "PASS_SIMULATOR_STARTUP_EXPORT_PREVIOUS_SESSION_RECOVERY", "build_id": args.build_id,
           "os": second["device"]["os_version"], "architecture": second["device"]["hardware"],
           "previous_session_recovered": True, "current_session_not_duplicated": True, "export_schema": second["schema"],
           "device_jit_execution": "NOT TESTED", "share_sheet_interaction": "NOT AUTOMATED",
           "notes": "Host terminated only the simulator probe between launches. Generated-code paths are disabled."}
(out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))

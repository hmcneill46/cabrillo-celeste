#!/usr/bin/env python3
"""Summarize a probe export without treating simulator/mock data as JIT proof."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("diagnostics", type=Path)
args = parser.parse_args()
data = json.loads(args.diagnostics.read_text())
if data.get("kind") != "celeste-jit-native-probe-diagnostics" or data.get("schema") != 1:
    parser.error("Not a supported probe diagnostic export")

def summarize(events):
    startup = next((e.get("fields", {}) for e in events if e.get("event") == "native_launch"), {})
    device = startup.get("device", {})
    checks = [e for e in events if e.get("event") in ("check_pass", "check_fail")]
    passes = [e for e in events if e.get("event") == "g0_memory_pass"]
    failures = [e for e in events if e.get("event") in ("check_fail", "g0_memory_fail", "script_reported_failure", "trace_status_unavailable")]
    final = events[-1] if events else {}
    return {
        "session": next((e.get("session") for e in events if e.get("session")), None),
        "build_id": startup.get("build", {}).get("build_id"),
        "hardware": device.get("hardware"), "os_version": device.get("os_version"),
        "environment": "simulator" if device.get("simulator") else "physical_claim_in_export" if device else "unknown",
        "native_pass_runs_reported": len(passes),
        "physical_native_pass_reported": bool(passes) and device.get("simulator") in (False, 0) and bool(device.get("hardware")),
        "checks_passed": sum(e.get("event") == "check_pass" for e in checks),
        "failures": [{"event": e["event"], "fields": e.get("fields", {})} for e in failures],
        "last_event": final.get("event"),
        "last_execution_stage": next((e["event"] for e in reversed(events) if e.get("event", "").startswith("about_to_")), None),
        "scope": "Reported native-memory results only. No managed JIT/hook/game proof. An interrupted log does not confirm a crash.",
    }

result = {"current": summarize(data.get("current_events", [])),
          "previous": [summarize(s.get("events", [])) for s in data.get("previous_sessions", [])],
          "reported_versions": {k: v for k, v in data.items() if k.startswith("reported_")}}
print(json.dumps(result, indent=2))

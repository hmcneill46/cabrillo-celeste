"""Read-only contract experiment over captured public Olympus/GameBanana data.

Uses the audit's isolated Python environment (PyYAML 6.0.3). Does not download
or install mods, change the phone, or act as the production dependency solver.
"""
import hashlib
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / ".build/ios-jit/launcher-product-audit-20260912"
REF = OUT / "references"
read = lambda name: json.loads((REF / name).read_text())

# Bind every response to its recorded fetched bytes before interpreting it.
fetches = []
for name in ["source-fetches.json", "service-fetches.json", "current-backend-fetches.json", "category-detail-fetches.json"]:
    fetches.extend(read(name))
for entry in fetches:
    if "error" in entry:
        continue
    data = (REF / entry["file"]).read_bytes()
    assert len(data) == entry["bytes"]
    assert hashlib.sha256(data).hexdigest() == entry["sha256"]

updates = yaml.safe_load((REF / "current-updates.yaml").read_text())
graph = yaml.safe_load((REF / "current-graph.yaml").read_text())
assert len(updates) == len(graph) == 6166
assert updates["memorialHelper"]["Version"] == "1.0.4"
assert updates["memorialHelper"]["Size"] == 13965
assert {"Name": "memorialHelper", "Version": "1.0.0"} in graph["SpringCollab2020"]["Dependencies"]
assert read("olympus-memorial-search.json") == []
assert read("olympus-memorial-spaced-search.json")[0]["PageURL"] == "https://gamebanana.com/tools/6850"
assert read("olympus-spring-search.json")[0]["PageURL"] == "https://gamebanana.com/mods/150813"
for name, key in [("olympus-new.json", "CreatedDate"), ("olympus-popular.json", "Downloads")]:
    rows = read(name)
    assert len(rows) == 20
    assert [m[key] for m in rows] == sorted((m[key] for m in rows), reverse=True)
    for m in rows:
        assert all(k in m for k in ["PageURL", "Name", "Author", "Description", "Likes", "Views", "Downloads", "Text", "Category", "Files"])
for name, category in [("olympus-maps.json", "GameBanana_Mod_6800"), ("olympus-helpers.json", "GameBanana_Mod_5081")]:
    assert len(read(name)) == 20
    assert all(m["CategoryId"] == category for m in read(name))
categories = yaml.safe_load((REF / "olympus-categories.json").read_text())
assert all(m.get("itemtype") == "Obsolete" for m in categories[1:])
assert "Studio" not in read("olympus-new.json")[0]
for name in ["gamebanana-sj-profile.json", "gamebanana-spring-profile.json", "gamebanana-memorial-profile.json"]:
    m = read(name)
    assert m["_aGame"]["_idRow"] == 6460
    assert "_aContributingStudios" in m
    assert all(k in m for k in ["_aFiles", "_aSubmitter", "_aPreviewMedia", "_nLikeCount", "_nViewCount", "_nDownloadCount"])

# Illustrative plan: add the currently indexed Spring release to the validated
# enabled build22 set. Keep compatible installed versions. This cannot infer
# metadata for a different ZIP the owner may already have imported elsewhere.
phone = json.loads(next((ROOT / ".build/ios-jit/device-evidence/2026-09-12/build-22-results").glob("*.diagnostics.json")).read_text())
played = phone["previous_sessions"][0]["events"]
selection = next(e for e in played if e["event"] == "launcher_run_prepared")["fields"]["selection"]
installed = {m["name"]: m["version"] for m in selection["modules"]}
installed.update({"Everest": "1.6458.0", "EverestCore": "1.6458.0", "Celeste": "1.4.0.0"})

def version(value):
    parts = [int(p) for p in str(value).split("-", 1)[0].split(".")]
    assert 2 <= len(parts) <= 4
    return tuple(parts + [-1] * (4 - len(parts)))

def satisfies(actual, required):
    a, b = version(actual), version(required)
    return a[:2] == (0, 0) or a[0] == b[0] and a[1:] >= b[1:]

pending = [("SpringCollab2020", updates["SpringCollab2020"]["Version"])]
additions, provided = {}, dict(installed)
while pending:
    name, required = pending.pop()
    if name in provided and satisfies(provided[name], required):
        continue
    assert name not in additions, ("Conflicting requirements", name, required)
    candidate = updates[name]
    assert satisfies(candidate["Version"], required), (name, required)
    assert candidate["URL"] == graph[name]["URL"]
    assert len(candidate["xxHash"]) == 1  # This example only; ambiguity needs UI.
    additions[name] = candidate
    provided[name] = candidate["Version"]
    pending.extend((d["Name"], d["Version"]) for d in graph[name]["Dependencies"])
assert set(additions) == {"SpringCollab2020", "SpringCollab2020Audio", "ClutterHelper"}
total_bytes = sum(m["Size"] for m in additions.values())
assert total_bytes == 569790262

result = {
    "schema": 1, "status": "PASS_CAPTURED_PUBLIC_SERVICE_CONTRACTS_AND_SPRING_PLAN_EXAMPLE",
    "audit_date": "2026-09-12", "production_solver_implemented": False,
    "mods_downloaded_or_installed": False,
    "updates_count": len(updates), "graph_count": len(graph),
    "versions": {"Olympus": "568cc5fc846836d480e41f928a3db7c06e87798d",
                 "SearchService": "c9a933911eceac9022930bcdcdc7cf53552c62df",
                 "CurrentUpdaterBackend": "904284430da1e72218696cac6e4d0aebea663d1a"},
    "validated_services": ["latest", "downloads", "name search", "Maps filter", "Helpers filter", "categories", "subcategories response", "GameBanana profile details", "GameBanana featured response", "update database", "dependency graph"],
    "memorial_helper": {"id": "memorialHelper", "available_version": "1.0.4", "required_by_spring": "1.0.0", "bytes": 13965, "page": "https://gamebanana.com/tools/6850", "already_enabled_in_phone_export": True},
    "important_contracts": ["Internal YAML identity is different from a search title.",
                            "Current Olympus response GameBananaType is Obsolete; use provided PageURL and opaque IDs.",
                            "Upstream integrity hash is xxHash64 seed zero, not a signature.",
                            "A current dependency graph cannot describe every historical installed release.",
                            "Multi-file pages include optional files; do not install every attachment.",
                            "Studio field exists in direct profiles but was empty in all three samples; nonempty studio rendering remains untested."],
    "categories": [m["formatted"] for m in categories],
    "illustrative_spring_plan": {"basis": "Latest indexed Spring 1.7.10 added to build22's enabled 56-ZIP set; not a plan for an unobserved older owner ZIP.",
                                "additions": additions, "download_bytes": total_bytes,
                                "existing_compatible_helpers_left_unchanged": True,
                                "optional_dependencies_not_auto_installed": True,
                                "ios_execution_compatibility_proven": False},
    "fetches": fetches
}
(OUT / "service-validation.json").write_text(json.dumps(result, indent=2) + "\n")
print(result["status"])
print("Illustrative additions:", ", ".join(additions), "; bytes:", total_bytes)

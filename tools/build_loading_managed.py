#!/usr/bin/env python3
"""Rebuild the loading adapter and patched Everest in new Cabrillo-only stages."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments/ios-jit/launcher-loading"
INPUT = ROOT / ".private/loading-inputs"
BASE = ROOT / ".private/resources/build28"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", default=".build/loading-managed30")
    args = parser.parse_args()
    work = ROOT / args.work
    if work.resolve() != work.absolute() or ROOT / ".build" not in work.parents or work.exists():
        raise ValueError("Choose a new, unaliased work directory under .build")
    lock = read(SOURCE / "ManagedDependencies.json")
    if sha(INPUT / "manifest.json") != lock["manifest_sha256"]:
        raise ValueError("Managed input manifest differs")
    manifest = read(INPUT / "manifest.json")
    for name, row in manifest["files"].items():
        if sha(ROOT / name) != row["sha256"]:
            raise ValueError("Changed private managed input: " + name)
    capsule = read(ROOT / ".private/migration/inputs.json")
    for name, row in capsule.items():
        if name.startswith(".private/resources/build28/") and sha(ROOT / name) != row["sha256"]:
            raise ValueError("Changed accepted resource: " + name)
    work.mkdir(parents=True)
    repo = work / "source/Everest"
    shutil.copytree(INPUT / "source/Everest", repo)
    shutil.copytree(INPUT / "nuget", work / "nuget")
    (work / "NuGet.Config").write_text('<configuration><packageSources><clear /></packageSources></configuration>\n')
    spec = importlib.util.spec_from_file_location("loading_patch", SOURCE / "patch_loading.py")
    patch = importlib.util.module_from_spec(spec); spec.loader.exec_module(patch)
    changes = patch.apply(repo)
    (work / "source-patch.json").write_text(json.dumps(changes, indent=2) + "\n")
    sources = sorted((SOURCE / "managed").glob("*.cs")) + [ROOT / "modern-ios/CelesteIOSFoundation" / n for n in ["PlatformPolicies.cs", "TouchControlsPolicy.cs"]]
    source_paths = [*sources, *sorted((SOURCE / "tools").glob("*")), *sorted((SOURCE / "upstream").glob("*")), SOURCE / "patch_loading.py", SOURCE / "ManagedDependencies.json", Path(__file__)]
    source_hashes = {str(p.relative_to(ROOT)): sha(p) for p in source_paths if p.is_file()}
    commands = []
    env = dict(os.environ, DOTNET_CLI_HOME=str(work / "cli-home"),
        NUGET_PACKAGES=str(work / "nuget"), NUGET_HTTP_CACHE_PATH=str(work / "http-cache"),
        DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_MULTILEVEL_LOOKUP="0", DOTNET_SKIP_FIRST_TIME_EXPERIENCE="1",
        DOTNET_CLI_WORKLOAD_UPDATE_NOTIFY_DISABLE="true", DOTNET_GENERATE_ASPNET_CERTIFICATE="false",
        DEVELOPER_DIR="/Applications/Xcode-26.6.app/Contents/Developer")

    def run(command, label, sdk="sdk8", cwd=work):
        command = list(map(str, command)); commands.append(command)
        with (work / (label + ".log")).open("w") as log:
            result = subprocess.run(command, cwd=cwd, env=dict(env, DOTNET_ROOT=str(INPUT / sdk)), stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError(label + " failed; see " + str(work / (label + ".log")))
        print(label, "PASS", flush=True)

    sdk8, sdk9 = INPUT / "sdk8", INPUT / "sdk9"
    run([sdk9 / "dotnet", "build", "Celeste.Mod.mm/Celeste.Mod.mm.csproj", "-c", "Release",
        "-p:CJAppleJitCanary=true", "-p:DoNotAddSuffix=true", "-p:CecilVersion=0.11.6",
        "-p:RestoreLockedMode=false", "-p:NuGetAudit=false", "-p:BuildInParallel=false",
        "-p:CopyLocalLockFileAssemblies=true", "-p:ShouldIncludeNativeLua=false", "--nologo"], "everest", sdk="sdk9", cwd=repo)
    deps = repo / "Celeste.Mod.mm/bin/Release/net8.0"
    tools = work / "tools"
    shutil.copytree(SOURCE / "tools", tools)
    (tools / "global.json").write_text('{"sdk":{"version":"8.0.422","rollForward":"disable"}}\n')
    run([sdk8 / "dotnet", "build", tools / "EverestPrepare.csproj", "-c", "Release", "--artifacts-path", work / "tool-artifacts",
        "-p:EverestLibraries=" + str(deps), "-p:NuGetAudit=false", "--nologo"], "prepare-tool", cwd=tools)
    tool = work / "tool-artifacts/bin/EverestPrepare/release/EverestPrepare.dll"
    prepared = work / "prepared"; prepared.mkdir()
    for path in deps.glob("*.dll"):
        shutil.copy2(path, prepared / path.name)
    shutil.copy2(INPUT / "source/Everest/lib-ext/lib64-osx/Steamworks.NET.dll", prepared / "Steamworks.NET.dll")
    env.update(MONOMOD_DEPDIRS=os.pathsep.join(map(str, [prepared, deps, INPUT / "orig"])), MONOMOD_DEPENDENCY_MISSING_THROW="0")
    runner = [sdk8 / "dotnet", tool]
    run([*runner, "coreify", INPUT / "orig/Celeste.exe", prepared / "Celeste.dll"], "coreify-celeste")
    run([*runner, "coreify", INPUT / "orig/Celeste.Content.dll", prepared / "Celeste.Content.dll"], "coreify-content")
    shutil.copy2(INPUT / "fna-before-everest.dll", prepared / "FNA.dll")
    for name in ["FNA", "Celeste"]:
        patched = prepared / (name + ".patched.dll")
        run([*runner, "patch", prepared / (name + ".dll"), prepared / "Celeste.Mod.mm.dll", patched], "patch-" + name)
        patched.replace(prepared / (name + ".dll"))
    run([*runner, "hookgen", "--private", prepared / "Celeste.dll", prepared / "MMHOOK_Celeste.dll"], "hookgen")
    run([*runner, "patch", prepared / "MMHOOK_Celeste.dll", prepared / "Celeste.Mod.mm.dll", prepared / "MMHOOK_Celeste.patched.dll"], "relink-hooks")
    (prepared / "MMHOOK_Celeste.patched.dll").replace(prepared / "MMHOOK_Celeste.dll")
    for label, fna in [("before", INPUT / "accepted-prepared/FNA.dll"), ("after", prepared / "FNA.dll")]:
        run([*runner, "audit", fna, work / ("fna-" + label + ".json")], "audit-fna-" + label)
    if read(work / "fna-before.json") != read(work / "fna-after.json"):
        raise ValueError("Everest changes unexpectedly affect FNA; inspect semantic audits")
    if sha(prepared / "Celeste.Content.dll") != sha(BASE / "Managed/Celeste.Content.dll"):
        raise ValueError("Game content assembly unexpectedly changed")
    resources = work / "resources"
    shutil.copytree(BASE, resources)
    managed = resources / "Managed"
    for name in ["Celeste.Mod.mm.dll", "MMHOOK_Celeste.dll"]:
        shutil.copy2(prepared / name, managed / name)
    run([*runner, "platform", prepared / "Celeste.dll", managed / "Celeste.dll", work / "platform-patch.json"], "platform")
    run([*runner, "check-fna", managed, managed / "Celeste.dll", managed / "MMHOOK_Celeste.dll"], "check-fna")
    refs = sorted((sdk8 / "packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0").glob("*.dll"))
    names = ["Celeste.dll", "FNA.dll", "MMHOOK_Celeste.dll", "MonoMod.Core.dll", "MonoMod.RuntimeDetour.dll", "MonoMod.Utils.dll", "Mono.Cecil.dll", "NLua.dll", "KeraLua.dll", "Newtonsoft.Json.dll", "CelesteIOS.dll"]
    args = ["-nologo", "-nostdlib+", "-unsafe+", "-nullable:annotations", "-optimize+", "-deterministic+", "-target:library", '-out:"' + str(managed / "CelesteJITEverest.dll") + '"']
    args += ['-r:"' + str(p) + '"' for p in refs + [managed / name for name in names]]
    args += ['"' + str(p) + '"' for p in sources]
    args += ['-resource:"' + str(p) + '",Celeste.IOSTouchControls.' + p.name for p in sorted((INPUT / "touch-assets").glob("*.a8"))]
    rsp = work / "adapter.rsp"; rsp.write_text("\n".join(args) + "\n")
    run([sdk8 / "dotnet", "exec", sdk8 / "sdk/8.0.422/Roslyn/bincore/csc.dll", "@" + str(rsp)], "adapter")
    replacements = {"Managed/CelesteJITEverest.dll", "Managed/Celeste.Mod.mm.dll", "Managed/Celeste.dll", "Managed/MMHOOK_Celeste.dll"}
    for path in BASE.rglob("*"):
        if path.is_file() and str(path.relative_to(BASE)) not in replacements:
            if sha(path) != sha(resources / path.relative_to(BASE)):
                raise ValueError("Unrelated accepted resource changed: " + str(path))
    for name, digest in source_hashes.items():
        if sha(ROOT / name) != digest:
            raise ValueError("Source changed during build: " + name)
    receipt = dict(schema=1, status="PASS_LOADING_MANAGED_BUILD", created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        input_manifest_sha256=sha(INPUT / "manifest.json"), public_source_sha256=source_hashes, upstream_edits=changes,
        upstream_commit=manifest["pins"][""], replaced_resources=sorted(replacements),
        resources={str(p.relative_to(resources)): sha(p) for p in sorted(resources.rglob("*")) if p.is_file()},
        resource_root=str(resources.relative_to(ROOT)), commands=commands, fna_semantics_unchanged=True,
        original_content_assembly_unchanged=True, unchanged_native_runtime=True, host_tested=False, device_tested=False)
    (work / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(receipt["status"], flush=True)


if __name__ == "__main__":
    main()

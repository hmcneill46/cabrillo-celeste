#!/usr/bin/env python3
"""Narrow, recorded adaptations for the embedded Everest lifecycle."""
import hashlib
import json
import subprocess
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[2]
REPO = ROOT / '.build/ios-jit/launcher-runtime-everest-source/Everest'


def main():
    identity = json.loads((SOURCE / 'RuntimeIdentity.json').read_text())
    version_string = identity['builtins']['Everest'] + '-cjit-' + identity['everestSourceCommit'][:7]
    edits = {}
    receipt = REPO.parent / 'embedded-source-patch.json'
    previous = json.loads(receipt.read_text())['files'] if receipt.exists() else {}

    def change(name, pairs):
        original = subprocess.check_output(['git', '-C', str(REPO), 'show', 'HEAD:' + name])
        text = original.decode('utf-8-sig')
        for before, after in pairs:
            assert text.count(before) == 1, (name, before, text.count(before))
            text = text.replace(before, after)
        data = text.encode()
        target = REPO / name
        old_hash = hashlib.sha256(target.read_bytes()).hexdigest()
        assert target.read_bytes() in (original, data) or old_hash == previous.get(name, {}).get('patched_sha256'), ('Unrecognized source edit', name)
        target.write_bytes(data)
        edits[name] = dict(original_sha256=hashlib.sha256(original).hexdigest(), patched_sha256=hashlib.sha256(data).hexdigest())

    change('Celeste.Mod.mm/Mod/Everest/Everest.cs', [
        ('public readonly static string VersionString = "0.0.0-dev";', 'public readonly static string VersionString = ' + json.dumps(version_string) + ';'),
        ('Updater._VersionListRequestTask = Updater.RequestAll();', 'if (Environment.GetEnvironmentVariable("CJIT_EMBEDDED") != "1")\n                Updater._VersionListRequestTask = Updater.RequestAll();'),
        ('ModUpdaterHelper.RunAsyncCheckForModUpdates(excludeBlacklist: true);', 'if (Environment.GetEnvironmentVariable("CJIT_EMBEDDED") != "1")\n                ModUpdaterHelper.RunAsyncCheckForModUpdates(excludeBlacklist: true);'),
        ('DiscordSDK.LoadRichPresenceIcons();', 'if (Environment.GetEnvironmentVariable("CJIT_EMBEDDED") != "1")\n                DiscordSDK.LoadRichPresenceIcons();'),
    ])
    change('Celeste.Mod.mm/Mod/Everest/Everest.DiscordSDK.cs', [
        ('public static DiscordSDK CreateInstance() {', 'public static DiscordSDK CreateInstance() {\n                if (Environment.GetEnvironmentVariable("CJIT_EMBEDDED") == "1") return null;'),
    ])
    change('Celeste.Mod.mm/Mod/Everest/Everest.Loader.cs', [
        ('                try {\n                    Watcher = new FileSystemWatcher {',
         '                if (Environment.GetEnvironmentVariable("CJIT_EMBEDDED") == "1") {\n                    AutoLoadNewMods = false;\n                    return;\n                }\n\n                try {\n                    Watcher = new FileSystemWatcher {'),
    ])
    change('NETCoreifier/Coreifier.cs', [
        ('Assembly.GetEntryAssembly().GetCustomAttribute<DebuggableAttribute>()', '(Assembly.GetEntryAssembly() ?? Assembly.GetExecutingAssembly()).GetCustomAttribute<DebuggableAttribute>()'),
    ])
    # The native launcher retains its process after game disposal. The upstream
    # inverted condition would leave the helper's idle thread waiting forever.
    change('Celeste.Mod.mm/Mod/Helpers/WorkerThreadTaskScheduler.cs', [
        ('if (!isDisposed)\n                return;', 'if (isDisposed)\n                return;'),
    ])
    (REPO.parent / 'embedded-source-patch.json').write_text(json.dumps(dict(schema=1, files=edits), indent=2) + '\n')
    print('EMBEDDED_EVEREST_SOURCE_PATCH_READY', len(edits), flush=True)


if __name__ == '__main__':
    main()

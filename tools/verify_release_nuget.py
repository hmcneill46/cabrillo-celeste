"""Verify exact NuGet inputs for the selected macOS build host."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST_X64 = 'microsoft.netcore.app.host.osx-x64/8.0.16/microsoft.netcore.app.host.osx-x64.8.0.16.nupkg'
HOST_ARM64 = HOST_X64.replace('osx-x64', 'osx-arm64')


def expected_packages(arch):
    base = json.loads((ROOT / 'release/owned-game-nuget.json').read_text())['packages']
    hosts = json.loads((ROOT / 'release/nuget-hosts.json').read_text())
    if (hosts.get('schema') != 1 or hosts.get('base_lock') != 'release/owned-game-nuget.json'
            or hosts.get('base_arch') != 'x64' or set(hosts.get('replacements', {})) != {'arm64'}
            or set(hosts['replacements']['arm64']) != {HOST_ARM64} or HOST_X64 not in base):
        raise ValueError('Unexpected NuGet host lock structure')
    if arch == 'arm64':
        del base[HOST_X64]
        base.update(hosts['replacements']['arm64'])
    elif arch != 'x64':
        raise ValueError('Unsupported NuGet build host architecture: ' + str(arch))
    return base


def verify_packages(actual, arch):
    expected = expected_packages(arch)
    if actual != expected:
        missing = sorted(expected.keys() - actual.keys())
        extra = sorted(actual.keys() - expected.keys())
        changed = sorted(k for k in expected.keys() & actual.keys() if expected[k] != actual[k])
        raise ValueError('NuGet lock mismatch for ' + arch + ': ' + json.dumps(
            dict(missing=missing, extra=extra, changed=changed), sort_keys=True))
    return dict(status='PASS_EXACT_NUGET_INPUTS', host_arch=arch, package_count=len(expected))

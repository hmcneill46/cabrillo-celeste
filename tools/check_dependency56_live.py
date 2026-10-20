#!/usr/bin/env python3
"""Run build56's production mod resolver/installer against the live public index.

Downloads public Strawberry Jam mod ZIPs (about1.2GiB) into a fresh ignored host
profile. It never takes a game ZIP, SDK, private capsule or device argument and
never executes mod DLLs. The warm control uses the captured live index and
rejects transport calls after seeding only the production-verified ZIP cache.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / 'experiments/ios-jit/launcher-dependency-downloads'
XCODE = 'Xcode 26.6\nBuild version 17F113'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed_cache(source, destination):
    """Copy only public verified ZIP/cache records; production revalidates them."""
    if source.resolve() != source or ROOT / '.build' not in source.parents or not source.is_dir():
        raise ValueError('Seed only an unaliased public integration result directory under .build')
    profile = source / 'Profile'
    cache = profile / 'LauncherDownloads'
    target = destination / 'Profile/LauncherDownloads'
    target.mkdir(parents=True)
    rows = []
    for metadata in sorted(cache.glob('*.json')):
        if metadata.is_symlink() or metadata.resolve() != metadata:
            raise ValueError('Seed metadata must be a regular unaliased file')
        row = json.loads(metadata.read_text())
        key = metadata.stem
        filename = row['archive']['filename']
        if (not re.fullmatch('[0-9a-f]{64}', key) or filename != Path(filename).name
                or not filename.endswith('.zip') or '\\' in filename or ':' in filename):
            raise ValueError('Unsafe public seed-cache record')
        archive = cache / (key + '.zip')
        if not archive.exists():
            archive = profile / 'Mods' / filename
        if not archive.is_file() or archive.is_symlink() or archive.resolve() != archive:
            raise ValueError('Missing or aliased public seed archive')
        shutil.copyfile(archive, target / (key + '.zip'))
        shutil.copyfile(metadata, target / metadata.name)
        rows.append(dict(key=key, recorded_sha256=row['identity']['sha256'], bytes=archive.stat().st_size,
                         source_path=str(archive.relative_to(ROOT)), record_sha256=sha(metadata)))
    if not rows:
        raise ValueError('The public seed cache contains no production-verified records')
    return dict(source_results=str(source.relative_to(ROOT)), archive_count=len(rows), records=rows,
                seed_copies_trusted_without_production_reverification=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, help='Fresh directory under .build')
    parser.add_argument('--developer-dir', default=os.environ.get('DEVELOPER_DIR', '/Applications/Xcode.app/Contents/Developer'))
    parser.add_argument('--operation-timeout', type=int, default=3600)
    parser.add_argument('--seed-cache', type=Path, help='Previous ignored public live-integration result directory')
    args = parser.parse_args()
    work = (ROOT / args.work).absolute()
    if work.resolve() != work or ROOT / '.build' not in work.parents or work.exists():
        raise ValueError('Choose a fresh unaliased directory under .build')
    if not 60 <= args.operation_timeout <= 7200:
        raise ValueError('Operation timeout must be between60 and7200 seconds')
    sys.path.insert(0, str(ROOT / 'tools'))
    import compile_release56 as build
    lock = json.loads((build.IDENTITY / 'Dependencies.json').read_text())
    build.validate_overlay(lock)
    build.validate_download_metadata()
    identity = json.loads((build.IDENTITY / 'BuildIdentity.json').read_text())
    if identity['version'] != '0.25.1' or identity['build_number'] != '56':
        raise ValueError('Expected build56/0.25.1 production source selection')
    selected = build.selected_swift_sources()
    required = {OVERLAY / 'native/DependencyPlan.swift', OVERLAY / 'native/DependencyInstaller.swift',
                build.EVEREST_OVERLAY / 'native/RuntimeIdentity.swift'}
    if not required.issubset(selected):
        raise ValueError('The live fixture must compile actual production56 source overrides')
    production = [path for path in selected if path.name not in {'PlatformViews.swift', 'ShortcutViews.swift'}]
    fixture = OVERLAY / 'tests/LiveDependencyInstall.swift'
    vendor = sorted((ROOT / 'vendor/ZIPFoundation/Sources/ZIPFoundation').glob('*.swift'))
    yaml = ROOT / 'vendor/Yams/Sources/CYaml'
    c_sources = sorted((yaml / 'src').glob('*.c'))
    inputs = set(production + vendor + c_sources + [fixture, Path(__file__), ROOT / 'tools/compile_release56.py',
                 build.IDENTITY / 'Dependencies.json', build.IDENTITY / 'BuildIdentity.json',
                 OVERLAY / 'CompatibilityDownloads.json', build.SOURCE / 'RuntimeCompatibleReleases.json',
                 build.EVEREST_OVERLAY / 'RuntimeIdentity.json'])
    inputs.update(path for path in (yaml / 'include').rglob('*') if path.is_file())
    inputs.add(yaml / 'src/yaml_private.h')
    source_hashes = {str(path.relative_to(ROOT)): sha(path) for path in sorted(inputs)}
    env = dict(os.environ, DEVELOPER_DIR=args.developer_dir, CLANG_MODULE_CACHE_PATH=str(work / 'module-cache'),
               SWIFT_MODULECACHE_PATH=str(work / 'module-cache'))
    if subprocess.check_output(['xcodebuild', '-version'], env=env, text=True).strip() != XCODE:
        raise ValueError('Expected Xcode26.6/17F113')
    work.mkdir(parents=True)
    (work / 'source-initial.json').write_text(json.dumps(source_hashes, indent=2) + '\n')
    native = work / 'native'
    native.mkdir()
    commands = []

    def run(command, label):
        command = list(map(str, command))
        commands.append(command)
        with (work / (label + '.log')).open('w') as log:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            print((work / (label + '.log')).read_text(errors='replace')[-12000:], flush=True)
            raise RuntimeError(label + ' failed')
        print('PASS ' + label, flush=True)

    run(['xcrun', 'swiftc', '-swift-version', '5', '-O', '-module-name', 'ZIPFoundation',
         '-emit-library', '-static', '-emit-module', '-emit-module-path', native / 'ZIPFoundation.swiftmodule',
         '-o', native / 'libZIPFoundation.a', *vendor], 'compile-zip')
    for path in c_sources:
        run(['xcrun', 'clang', '-DYAML_DECLARE_STATIC', '-O2', '-I' + str(yaml / 'include'), '-c', path,
             '-o', native / (path.stem + '.o')], 'compile-yaml-' + path.stem)
    run(['xcrun', 'libtool', '-static', '-o', native / 'libCYaml.a',
         *[native / (path.stem + '.o') for path in c_sources]], 'archive-yaml')
    run(['xcrun', 'swiftc', '-swift-version', '5', '-O', '-g', '-I', native, '-I', yaml / 'include',
         *production, fixture, native / 'libZIPFoundation.a', native / 'libCYaml.a', '-o', work / 'live-tests'], 'compile-live-fixture')
    policy = '(version 1)\n(allow default)\n'
    for path in [ROOT / '.private', ROOT.parent / 'celeste-ios',
                 ROOT.parent / 'Celeste-Everest-JIT-Apple-Platforms', ROOT.parent / 'Celeste Required Files']:
        policy += '(deny file-read* file-write* (subpath ' + json.dumps(str(path)) + '))\n'
    sandbox = work / 'live-tests.sb'
    sandbox.write_text(policy)
    seeded = seed_cache((ROOT / args.seed_cache).absolute(), work / 'results') if args.seed_cache else None
    if seeded:
        (work / 'seed-cache.json').write_text(json.dumps(seeded, indent=2) + '\n')
    # This one stage intentionally permits production HTTPS to public mod services.
    command = ['sandbox-exec', '-f', str(sandbox), str(work / 'live-tests'), str(work / 'results'),
               str(OVERLAY), str(build.SOURCE / 'RuntimeCompatibleReleases.json'), str(args.operation_timeout)]
    commands.append(command)
    with (work / 'live-tests.log').open('w') as log:
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            log.write(line)
            log.flush()
            print(line.rstrip(), flush=True)
        code = process.wait()
    if code:
        raise RuntimeError('Live integration failed; retained public results/logs are in ' + str(work))
    relocation_command = [*command, '--relocation-only']
    relocation_command[4] = str(work / 'relocation')
    commands.append(relocation_command)
    with (work / 'relocation.log').open('w') as log:
        process = subprocess.Popen(relocation_command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            log.write(line)
            log.flush()
            print(line.rstrip(), flush=True)
        code = process.wait()
    if code:
        raise RuntimeError('Real stale Femto relocation failed; inspect retained scoped relocation logs')
    result_file = work / 'results/result.json'
    result = json.loads(result_file.read_text())
    relocation_file = work / 'relocation/relocation-result.json'
    relocation = json.loads(relocation_file.read_text())
    if relocation['status'] != 'PASS_REAL_BUILD56_STALE_FEMTO_RELOCATION':
        raise ValueError('Real stale Femto URL did not recover through production discovery')
    if result['status'] != 'PASS_LIVE_BUILD56_STRAWBERRY_JAM_DEPENDENCY_INSTALL':
        raise ValueError('Missing complete live dependency installation result')
    if source_hashes != {str(path.relative_to(ROOT)): sha(path) for path in sorted(inputs)}:
        raise RuntimeError('Production/fixture source changed during the live integration')
    build.validate_overlay(lock)
    receipt = dict(status=result['status'], version=identity['version'], build_number=identity['build_number'],
                   source_sha256=source_hashes, commands=commands, xcode=XCODE,
                   compiled_production_swift_sources=len(production), compiled_test_sources=1,
                   result_sha256=sha(result_file), index=result['index'], checks=len(result['checks']),
                   initial_download_count=result['initialDownloadCount'], archive_count=result['actualInstalledArchiveCount'],
                   downloaded_bytes=result['totalDownloadedBytes'], accepted_host_reviews=result['acceptedHostReviews'],
                   verified_archive_records_sha256=sha(work / 'results/downloaded-archives.json'),
                   production_foundation_transport_executed=True, live_provider_overrides=False,
                   seeded_public_cache=seeded is not None,
                   seeded_public_cache_archives=seeded['archive_count'] if seeded else 0,
                   fresh_network_archive_verifications=result['freshNetworkArchiveVerifications'],
                   real_stale_femto_relocation_status=relocation['status'],
                   real_stale_femto_relocation_result_sha256=sha(relocation_file),
                   warm_cache_download_attempts=result['cacheReuseDownloadAttempts'],
                   game_or_mod_dll_executed=False, ios_jit_executed=False, physical_device_tested=False,
                   private_or_legacy_inputs=False,
                   scope='macOS production56 resolver/installer real HTTPS/index/graph/mod ZIP integrity and metadata, explicit host reviews, filesystem commit, and verified cache reuse; no game, Mono, JIT or device acceptance')
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(receipt['status'], 'archives=' + str(receipt['archive_count']), 'checks=' + str(receipt['checks']), flush=True)


if __name__ == '__main__':
    main()

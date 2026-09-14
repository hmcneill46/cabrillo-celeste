#!/usr/bin/env python3
import hashlib, json, os, subprocess, sys
from pathlib import Path
S = Path(__file__).resolve().parents[1]; R = S.parents[2]; B = R / '.build/ios-jit'
O = B / 'launcher-runtime-spring-install'; O.mkdir(parents=True, exist_ok=True)
N = B / 'launcher-runtime-native/host'; D = B / 'launcher-runtime-native-dependencies'
env = dict(os.environ, DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
sources = sorted((S / 'native').glob('*.swift')) + [S / 'tests/FreshResolutionTests.swift']
cmd = ['xcrun', 'swiftc', '-swift-version', '5', '-O', '-g', '-I', str(N), '-I', str(D / 'Yams/Sources/CYaml/include'), *map(str, sources), str(N / 'libZIPFoundation.a'), str(N / 'libCYaml.a'), '-o', str(O / 'tests')]
p = subprocess.run(cmd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
(O / 'compile.log').write_text(p.stdout)
if p.returncode: print(p.stdout[-8000:]); sys.exit(p.returncode)
with (O / 'run.log').open('w') as log:
 p = subprocess.run([str(O / 'tests'), str(O), str(B / 'launcher-runtime-service'), str(S), *sys.argv[1:]], env=env, stdout=log, stderr=subprocess.STDOUT, timeout=1800)
if p.returncode: print((O / 'run.log').read_text()[-8000:]); sys.exit(p.returncode)
result = O / ('result.json' if '--install' in sys.argv else 'plan-result.json')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
receipt = dict(status=json.loads(result.read_text())['status'], source_sha256={str(p.relative_to(R)): sha(p) for p in sources + [Path(__file__), S / 'CompatibilityDownloads.json', S / 'RuntimeCompatibleReleases.json']}, result_sha256=sha(result), command=cmd, physical_execution=False)
(O / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(receipt['status'])

#!/usr/bin/env python3
"""Capture public sources for the reported fresh-install case; retain original bytes."""
import datetime, hashlib, json, urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import xxhash, yaml

S = Path(__file__).resolve().parents[1]
R = S.parents[2]
O = R / '.build/ios-jit/launcher-catalogue-service'
O.mkdir(parents=True, exist_ok=True)

def fetch(name, url, limit, sha256=None, xhash=None):
    target = O / name
    if target.exists():
        data = target.read_bytes()
        if sha256 is not None and hashlib.sha256(data).hexdigest() == sha256:
            return dict(file=name, bytes=len(data), sha256=sha256, url=url, reused_verified=True)
    request = urllib.request.Request(url, headers={'User-Agent': 'CelesteIOS-development/0.13.1'})
    temp = target.with_suffix(target.suffix + '.part')
    try:
        with urllib.request.urlopen(request, timeout=60) as response, temp.open('wb') as stream:
            assert response.url.startswith('https://')
            total = 0
            while chunk := response.read(1048576):
                total += len(chunk)
                assert total <= limit, name
                stream.write(chunk)
            resolved = response.url
        data = temp.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if sha256 is not None: assert actual == sha256, name
        if xhash is not None: assert len(data) == limit and xxhash.xxh64(data).hexdigest() == xhash, name
        temp.replace(target)
        result = dict(file=name, bytes=len(data), sha256=actual, url=url, resolved_url=resolved,
                      fetched_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        print(name, len(data), actual, flush=True)
        return result
    finally:
        temp.unlink(missing_ok=True)

if __name__ == '__main__':
    urls = [('updater-pointer.txt', 'https://everestapi.github.io/modupdater.txt'),
            ('graph-pointer.txt', 'https://everestapi.github.io/modgraph.txt')]
    receipts = [fetch(n, u, 4096) for n, u in urls]
    for pointer, filename in [('updater-pointer.txt', 'live-updates.yaml'), ('graph-pointer.txt', 'live-graph.yaml')]:
        url = (O / pointer).read_text().strip()
        assert url.startswith('https://') and '\n' not in url
        receipts.append(fetch(filename, url, 33554432))
    updates = yaml.load((O / 'live-updates.yaml').read_text(), Loader=yaml.BaseLoader)
    inputs = [(m['modules'][0]['name'] + '-earlier.zip', m['url'], m['bytes'], m['pinnedSHA256'], m['hashes'][0])
              for m in json.loads((S / 'RuntimeCompatibleReleases.json').read_text())]
    spring = updates['SpringCollab2020']
    inputs.append(('SpringCollab2020.zip', spring['URL'], int(spring['Size']), None, spring['xxHash'][0]))
    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts += list(pool.map(lambda args: fetch(*args), inputs))
    (O / 'resolution-fetches.json').write_text(json.dumps(receipts, indent=2) + '\n')

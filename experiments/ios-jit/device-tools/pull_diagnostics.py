#!/usr/bin/env python3
"""Read one canary session and its console from LiveContainer over USB.

Requires pymobiledevice3 11.12.4 in the isolated device-transfer environment.
No export action, debugger attach, phone writes, or recursive app-data copy.
"""

import argparse
import asyncio
import datetime
import hashlib
import json
import re
import uuid
from importlib.metadata import version
from pathlib import Path

from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.house_arrest import HouseArrestService


async def stable_read(afc, remote, maximum):
    before = await afc.stat(remote)
    if before['st_ifmt'] != 'S_IFREG' or before['st_size'] > maximum:
        raise RuntimeError('Expected a regular log within the configured size limit')
    data = await afc.get_file_contents(remote)
    after = await afc.stat(remote)
    repeated = await afc.get_file_contents(remote)
    if data != repeated or before['st_size'] != after['st_size'] or len(data) != after['st_size']:
        raise RuntimeError('The log changed during collection; retry when the canary is idle')
    return data


def parse_events(raw):
    # A crash can interrupt the final JSONL write. Preserve its bytes in the
    # snapshot, but do not present that incomplete record as a parsed event.
    complete, separator, partial = raw.rpartition(b'\n')
    if not separator:
        raise RuntimeError('No complete persisted event is available')
    return [json.loads(line) for line in complete.splitlines() if line], len(partial)


async def collect(args):
    if args.output.exists():
        raise RuntimeError('Use a new output directory to preserve earlier snapshots')
    if version('pymobiledevice3') != '11.12.4':
        raise RuntimeError('This collector was verified with pymobiledevice3 11.12.4')
    inventory = json.loads(args.device_inventory.read_text())
    devices = [r for r in inventory if r.get('ProductType') == args.product_type and r.get('ConnectionType') == 'USB']
    if len(devices) != 1:
        raise RuntimeError('The private device inventory must identify exactly one target USB phone')
    guest = str(uuid.UUID(args.guest_data_id)).upper()
    remote = '/Documents/Data/Application/' + guest + '/Documents/Diagnostics'
    async with await create_using_usbmux(
        serial=devices[0]['UniqueDeviceID'], connection_type='USB', pair_timeout=3,
        pairing_records_cache_folder=args.pairing_cache,
    ) as lockdown:
        if await lockdown.get_value(key='ProductType') != args.product_type:
            raise RuntimeError('Connected phone does not match the requested model')
        async with await HouseArrestService.create(lockdown, args.host_bundle_id, documents_only=True) as afc:
            if args.session:
                session = str(uuid.UUID(args.session))
            else:
                candidates = []
                for name in await afc.listdir(remote):
                    match = re.fullmatch(r'session-([0-9a-f-]{36})\.jsonl', name)
                    if match:
                        session = str(uuid.UUID(match[1]))
                        stat = await afc.stat(remote + '/' + name)
                        if stat['st_ifmt'] == 'S_IFREG':
                            candidates.append((stat['st_mtime'], session))
                if not candidates:
                    raise RuntimeError('No saved canary sessions in the supplied guest data folder')
                session = max(candidates)[1]
            session_file = 'session-' + session + '.jsonl'
            raw = await stable_read(afc, remote + '/' + session_file, args.max_file_bytes)
            events, partial_bytes = parse_events(raw)
            launch = events[0]
            if launch.get('event') != 'native_launch' or any(e.get('session') != session for e in events):
                raise RuntimeError('The saved log is not a single expected canary session')
            device = launch['fields']['device']
            if device['guest_bundle_id'] != args.guest_bundle_id or device['hardware'] != args.product_type or device['simulator']:
                raise RuntimeError('Log identity differs from the requested physical canary')
            console_file = 'console-' + session + '.txt'
            console = await stable_read(afc, remote + '/' + console_file, args.max_file_bytes)
    # Write only to the new local evidence directory after identity checks pass.
    args.output.mkdir(parents=True)
    rows = []
    for name, data in [(session_file, raw), (console_file, console)]:
        (args.output/name).write_bytes(data)
        rows.append({'file': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'two_reads_identical': True})
    receipt = {
        'status': 'PASS_DIRECT_USB_RAW_LOG_COLLECTION',
        'collected_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'tool_version': version('pymobiledevice3'), 'connection': 'USB',
        'device': device, 'build_id': launch['fields']['build']['build_id'],
        'host_bundle_id': args.host_bundle_id, 'guest_data_id': guest,
        'remote_directory': remote, 'session': session, 'files': rows,
        'complete_events': len(events), 'trailing_partial_event_bytes': partial_bytes,
        'phone_files_modified': False, 'debugger_attached': False,
        'export_action_triggered': False,
        'scope': 'One persisted session and its full native console; no exported bundle or preferences required',
    }
    (args.output/'collection-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps({'status': receipt['status'], 'build_id': receipt['build_id'], 'complete_events': len(events), 'trailing_partial_event_bytes': partial_bytes, 'local_output': str(args.output.resolve())}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device-inventory', type=Path, required=True, help='Private usbmux JSON inventory containing the target UDID')
    parser.add_argument('--pairing-cache', type=Path, required=True, help='Existing private pairing cache; never commit it')
    parser.add_argument('--host-bundle-id', required=True, help='Installed LiveContainer 1 host bundle identifier')
    parser.add_argument('--guest-data-id', required=True, help='Verified canary data-container UUID under LiveContainer/Data/Application')
    parser.add_argument('--guest-bundle-id', default='io.github.hmcneill46.celeste.everest.jit.canary')
    parser.add_argument('--product-type', default='iPhone16,2')
    parser.add_argument('--session', help='Specific launch UUID; omitted selects the most recently modified session log')
    parser.add_argument('--output', type=Path, required=True, help='New local private evidence directory')
    parser.add_argument('--max-file-bytes', type=int, default=20_000_000)
    args = parser.parse_args()
    if args.max_file_bytes <= 0:
        parser.error('--max-file-bytes must be positive')
    asyncio.run(asyncio.wait_for(collect(args), 45))


if __name__ == '__main__':
    main()

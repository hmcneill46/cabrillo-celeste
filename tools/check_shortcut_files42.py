#!/usr/bin/env python3
"""Check revision42 branches and execute isolated comparisons in Apple's engine.

The Apple host fixture substitutes plain text input for each dictionary-output
reference; it retains the generated comparison parameters and coercion. Only If
and Comment actions are allowed. This is not a full iOS shortcut execution test.
"""
import argparse
import copy
import hashlib
import json
import os
import plistlib
import subprocess
from pathlib import Path

import build_shortcut_files42 as generator
import check_shortcut_launch as branches

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'experiments/ios-jit/shortcut-files42/AppleConditionChecks.m'


def apple_cases():
    cases = []
    for host in ('livecontainer', ''):
        for i, row in enumerate(generator.generate(host)['WFWorkflowActions']):
            p = row['WFWorkflowActionParameters']
            if row['WFWorkflowActionIdentifier'] != 'is.workflow.actions.conditional' or 'WFConditionalActionString' not in p:
                continue
            target = p['WFConditionalActionString']
            assert p['WFInput']['Variable']['Value']['Aggrandizements'] == [
                dict(Type='WFCoercionVariableAggrandizement', CoercionItemClass='WFStringContentItem')]
            for variant, supplied, expected in [('match', target, 'MATCH'), ('other', 'not-'+target, 'OTHER'), ('original', target, None)]:
                condition = copy.deepcopy(row)
                value = condition['WFWorkflowActionParameters']['WFInput']['Variable']['Value']
                value.pop('OutputUUID');value.pop('OutputName');value['Type'] = 'ExtensionInput'
                if variant == 'original':value.pop('Aggrandizements')
                group = p['GroupingIdentifier']
                def action(name, **params):
                    return dict(WFWorkflowActionIdentifier='is.workflow.actions.'+name, WFWorkflowActionParameters=params)
                actions = [condition, action('comment', WFCommentActionText='MATCH'),
                    action('conditional', GroupingIdentifier=group, WFControlFlowMode=1),
                    action('comment', WFCommentActionText='OTHER'),
                    action('conditional', GroupingIdentifier=group, WFControlFlowMode=2)]
                cases.append(dict(name=f'{host or "standalone"}-{i}-{variant}', actions=actions,
                    input=supplied, comments=[expected] if expected else [], truth=variant=='match', expectMissingParameter=variant=='original'))
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    args = parser.parse_args();work = args.work.absolute();work.mkdir(parents=True, exist_ok=False)
    # Reuse the retained branch interpreter without editing its frozen file.
    branches.generate = generator.generate
    interpreted = branches.shortcut_checks()
    cases = apple_cases();(work/'cases.plist').write_bytes(plistlib.dumps(cases))
    env = dict(os.environ, DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
    subprocess.run(['xcrun','clang','-fobjc-arc','-Wall','-Wextra','-Werror','-Wno-deprecated-declarations',
        '-framework','Foundation',str(SOURCE),'-o',str(work/'apple-checks')], env=env, check=True)
    result = subprocess.run([str(work/'apple-checks'),str(work/'cases.plist')], capture_output=True, text=True)
    (work/'apple-results.json').write_text(result.stdout);(work/'apple-stderr.txt').write_text(result.stderr)
    result.check_returncode();apple = json.loads(result.stdout)
    assert apple['status'] == 'PASS_APPLE_CONDITIONS' and apple['checks'] == 36
    files = [Path(__file__),ROOT/'tools/build_shortcut_files42.py',SOURCE,ROOT/'tools/check_shortcut_launch.py']
    receipt = dict(status='PASS_SHORTCUT42_HOST_CONTROLS',apple_condition_checks=36,
        expected_original_failures=sum(c['expectMissingParameter'] for c in cases),
        generated_branches=len(interpreted),physical_device_tested=False,
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__ == '__main__':main()

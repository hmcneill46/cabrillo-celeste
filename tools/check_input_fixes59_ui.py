#!/usr/bin/env python3
"""Exercise the production SwiftUI touch editor in isolated simulator containers."""
import argparse,hashlib,json,os,plistlib,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'experiments/ios-jit/launcher-input-fixes59'
BASELINE=ROOT/'experiments/ios-jit/launcher-unified58'
def expected_ui_cases(suite, *, baseline=False, edge_only=False, normal_only=False):
    if suite not in ('touch', 'unified') or sum((baseline, edge_only, normal_only)) > 1:
        raise ValueError('Invalid UI suite selection')
    if suite == 'unified':
        if baseline or edge_only or normal_only:
            raise ValueError('Touch-only selection used for unified suite')
        return {
            'testTouchSettingsAndIntegratedJITCoexist': 'PASS_UNIFIED_TOUCH_SAVE_FEATHER_AND_INTEGRATED_PAIRING_ACTION',
            'testIntegratedBusyLocksEditorAndExternalProviderKeepsIt': 'PASS_UNIFIED_JIT_BUSY_LOCK_AND_EXTERNAL_FULL_DISPLAY_EDITOR',
            'testLayoutCopyPickerCancellationKeepsDraft': 'PASS_UNIFIED_LAYOUT_COPY_PICKER_CANCEL_RETAINS_DRAFT',
        }
    if baseline:
        return {'testBuild58SmallEdgeResizeNegativeControl': 'PASS_BUILD58_REAL_EDGE_RESIZE_NEGATIVE_CONTROL'}
    edge = {'testSmallEdgeResizeKeepsLayoutSaveable': 'PASS_BUILD59_REAL_EDGE_RESIZE_SAVE_UNDO'}
    if edge_only:
        return edge
    cases = {
        'testNativeEditor': 'PASS_TOUCH_EDITOR_DRAFT_UNDO_DUPLICATE_PRESET_SAVE_CANCEL_PERSISTENCE_LOCK',
        'testLiveInputPreferences': 'PASS_LIVE_INPUT_PREFERENCES_SAVE_CANCEL_PERSISTENCE',
        'testLandscapeDragAndPauseEditor': 'PASS_TOUCH_EDITOR_LANDSCAPE_DRAG_NATIVE_PRESENTATION',
    }
    if not normal_only:
        cases.update(edge)
    return cases


def validate_ui_results(summary, tests, log, expected_cases):
    """Require real XCTest cases, exact counts and independent log assertions.

    Inputs are the JSON from xcresulttool get test-results summary/tests and
    the original xcodebuild stdout. The caller must separately bind these
    files, the source snapshot and this checker to its receipt.
    """
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    require(isinstance(expected_cases, dict) and bool(expected_cases), 'No expected UI cases')
    require(all(isinstance(k, str) and re.fullmatch(r'test\w+', k) and isinstance(v, str) and v
                for k, v in expected_cases.items()), 'Malformed expected UI cases')
    require(isinstance(summary, dict) and isinstance(tests, dict) and isinstance(log, str), 'Malformed UI evidence')
    expected_count = len(expected_cases)
    require(summary.get('result') == 'Passed', 'xcresult summary did not pass')
    for key, expected in (('totalTestCount', expected_count), ('passedTests', expected_count),
                          ('failedTests', 0), ('skippedTests', 0), ('expectedFailures', 0)):
        require(type(summary.get(key)) is int and summary[key] == expected, 'Unexpected xcresult ' + key)
    require(summary.get('testFailures') == [], 'xcresult contains failures or lacks failure list')
    configurations = summary.get('devicesAndConfigurations')
    require(isinstance(configurations, list) and len(configurations) == 1, 'Expected one simulator result')
    require(isinstance(configurations[0], dict), 'Malformed simulator result')
    for key, expected in (('passedTests', expected_count), ('failedTests', 0), ('skippedTests', 0), ('expectedFailures', 0)):
        require(type(configurations[0].get(key)) is int and configurations[0][key] == expected,
                'Unexpected simulator ' + key)

    cases = []
    def visit(nodes):
        require(isinstance(nodes, list), 'Malformed xcresult test nodes')
        for node in nodes:
            require(isinstance(node, dict), 'Malformed xcresult test node')
            if node.get('nodeType') == 'Test Case':
                require('children' not in node or node['children'] == [], 'Unexpected nested test case')
                cases.append(node)
            elif 'children' in node:
                visit(node['children'])
    visit(tests.get('testNodes'))
    require(len(cases) == expected_count, 'Unexpected actual UI case count')
    observed = []
    for case in cases:
        name = case.get('name')
        require(isinstance(name, str) and name.endswith('()'), 'Malformed actual UI case name')
        method = name[:-2]
        require(method in expected_cases, 'Unexpected actual UI method')
        require(case.get('nodeIdentifier') == 'ProfileUITests/' + name, 'Unexpected actual UI case identity')
        require(case.get('result') == 'Passed', 'Actual UI case did not pass')
        observed.append(method)
    require(len(set(observed)) == expected_count and set(observed) == set(expected_cases), 'Duplicate or missing UI method')

    passed = re.findall(r"^Test Case '-\[ProfileUITests\.ProfileUITests (test\w+)\]' passed \([0-9.]+ seconds\)\.$", log, re.MULTILINE)
    require(len(passed) == expected_count and len(set(passed)) == expected_count and set(passed) == set(expected_cases),
            'xcodebuild passed method set differs')
    counts = re.findall(r'Executed (\d+) tests?, with (\d+) failures? \((\d+) unexpected\)', log)
    require(bool(counts) and all(tuple(map(int, count)) == (expected_count, 0, 0) for count in counts),
            'xcodebuild count missing or inconsistent')
    require('** TEST SUCCEEDED **' in log and not any(marker in log for marker in
            ('** TEST FAILED **', '** TEST INTERRUPTED **', '** BUILD INTERRUPTED **')),
            'Missing successful xcodebuild conclusion')
    for marker in expected_cases.values():
        require(marker in log, 'Missing actual UI assertion marker: ' + marker)
    return {'status': 'PASS_STRICT_UI_RESULTS', 'test_count': expected_count,
            'methods': sorted(observed), 'markers': sorted(expected_cases.values()),
            'summary_and_case_tree_verified': True, 'log_methods_counts_markers_verified': True}


def validate_runtime_receipt_status(metadata, partial):
    if not isinstance(metadata,dict):raise ValueError('Malformed runtime receipt')
    if partial:
        if metadata.get('status')!='PARTIAL_PHONE4_PASS_PAD_INTERRUPTED_NO_AGGREGATE_PASS':
            raise ValueError('Expected the known explicitly partial runtime receipt')
        return False
    if metadata.get('status') not in ('PASS_BUILD59_TOUCH_EDITOR_UI','PASS_BUILD58_EXPECTED_INVALID_RESIZE_UI_CONTROL'):
        raise ValueError('Runtime receipt did not complete successfully')
    return True


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_saved_work(args, expected):
    """Validate saved result bundles without compiling, booting or rerunning UI."""
    work=(ROOT/args.verify_work).absolute()
    if work.resolve()!=work or ROOT/'.build' not in work.parents or not work.is_dir():
        raise ValueError('Saved UI work must be an existing ignored build directory')
    metadata_path=work/'receipt.json'
    partial=False
    if not metadata_path.exists():
        metadata_path=work/'partial-receipt.json';partial=True
    metadata=json.loads(metadata_path.read_text())
    runtime_guard_completed=validate_runtime_receipt_status(metadata,partial)
    recorded=metadata.get('source_sha256',metadata.get('fixture_sha256',{}))
    runner_hash=recorded.get('tools/check_input_fixes59_ui.py')
    snapshots=[Path(__file__).resolve()]+[(ROOT/path).absolute() for path in args.orchestrator_snapshot or []]
    if any(path.resolve()!=path for path in snapshots):raise ValueError('Use unaliased orchestrator snapshots')
    matching=[path for path in snapshots if path.is_file() and file_sha(path)==runner_hash]
    if not matching:raise ValueError('Supply the exact archived runtime orchestrator with --orchestrator-snapshot')
    test_inputs=[path for path in recorded if path.endswith('/tests/TouchEditorUITests.swift') or path.endswith('/tests/UnifiedLauncherUITests.swift')]
    if len(test_inputs)!=1:raise ValueError('Runtime receipt must bind one selected UI test source')
    test_input=test_inputs[0];test_name=Path(test_input).name
    originals=[ROOT/test_input,matching[0].parent/test_name]
    originals=[path for path in originals if path.is_file() and file_sha(path)==recorded[test_input]]
    if not originals:raise ValueError('Keep the exact archived UI test source beside the runtime orchestrator snapshot')
    fixture=originals[0].read_text()
    right=metadata.get('orientation_rewrite_in_ignored_fixture_only',False)
    if right:fixture=fixture.replace('.landscapeLeft','.landscapeRight')
    reconstructed=hashlib.sha256(fixture.encode()).hexdigest()
    recorded_compiled=metadata.get('compiled_ui_fixture_sha256')
    # Earlier direct-source runs bound the UI source in their completed input
    # guard before a separate compiled-fixture hash field was introduced.
    compiled_basis='explicit_compiled_fixture_hash' if recorded_compiled else 'captured_direct_source_hash' if not partial and not right else 'specific_partial_source_snapshot_only'
    required_compiled=recorded_compiled or (recorded[test_input] if not partial and not right else None)
    if not partial and required_compiled!=reconstructed:raise ValueError('Recorded compiled UI fixture differs from its captured source')
    if right and (not (work/test_name).is_file() or file_sha(work/test_name)!=reconstructed):
        raise ValueError('Saved generated orientation fixture differs from its captured source')
    reconstruction=dict(original_test_source=test_input,original_source_sha256=recorded[test_input],
        exact_source_snapshot=str(originals[0].relative_to(ROOT)),orientation_rewrite=right,
        expected_compiled_sha256=reconstructed,recorded_compiled_sha256=recorded_compiled,compiled_hash_binding_basis=compiled_basis,
        recorded_end_hash_matches_reconstruction=(recorded_compiled==reconstructed) if recorded_compiled else None,
        runtime_compiled_fixture_before_after_guard_completed=metadata.get('compiled_ui_fixture_hash_guard') is True)
    bundles={int(path.name[3:-9]):path for path in work.glob('UI-*.xcresult') if re.fullmatch(r'UI-\d+\.xcresult',path.name)}
    indices=sorted(bundles) if args.result_index is None else args.result_index
    if not indices or len(indices)!=len(set(indices)) or any(index not in bundles for index in indices):
        raise ValueError('Choose existing, unique UI result indices')
    output=(ROOT/args.validation_output).absolute() if args.validation_output else work/'strict-validation'
    if output.resolve()!=output or ROOT/'.build' not in output.parents or output.exists():
        raise ValueError('Use a new ignored validation output directory')
    output.mkdir(parents=True)
    env=dict(os.environ,DEVELOPER_DIR=os.environ.get('DEVELOPER_DIR','/Applications/Xcode.app/Contents/Developer'))
    commands=[];results=[]
    for index in indices:
        extracted={}
        for kind in ('summary','tests'):
            command=['xcrun','xcresulttool','get','test-results',kind,'--path',str(bundles[index]),'--compact']
            commands.append(command)
            result=subprocess.run(command,cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
            (output/f'UI-{index}-{kind}.stderr').write_text(result.stderr)
            if result.returncode:raise RuntimeError('xcresult extraction failed: '+result.stderr[-2000:])
            target=output/f'UI-{index}-{kind}.json';target.write_text(result.stdout)
            extracted[kind]=json.loads(result.stdout)
        log=work/f'uitests-{index}.log'
        checked=validate_ui_results(extracted['summary'],extracted['tests'],log.read_text(),expected)
        tree=hashlib.sha256()
        for item in sorted(path for path in bundles[index].rglob('*') if path.is_file()):
            tree.update(str(item.relative_to(bundles[index])).encode()+b'\0'+file_sha(item).encode()+b'\n')
        checked.update(index=index,result_bundle=str(bundles[index].relative_to(ROOT)),result_bundle_tree_sha256=tree.hexdigest(),log_sha256=file_sha(log),
            summary_sha256=file_sha(output/f'UI-{index}-summary.json'),tests_sha256=file_sha(output/f'UI-{index}-tests.json'))
        results.append(checked)
    omitted=sorted(set(bundles)-set(indices))
    receipt=dict(status='PASS_SELECTED_UI_RESULTS_ONLY' if partial or omitted else 'PASS_STRICT_UI_WORK_RESULTS',
        work=str(work.relative_to(ROOT)),requested_indices=indices,omitted_indices=omitted,partial_runtime_work=partial,
        runtime_receipt_sha256=file_sha(metadata_path),runtime_receipt_status=metadata.get('status'),
        runtime_post_run_all_input_guard_completed=runtime_guard_completed,compiled_fixture_reconstruction=reconstruction,
        runtime_orchestrator_snapshot=str(matching[0].relative_to(ROOT)),runtime_orchestrator_sha256=runner_hash,
        validation_orchestrator_sha256=file_sha(Path(__file__)),runtime_source_hashes=recorded,
        source_scope='Specific source snapshots only; interrupted runtime did not finish its all-input post-run guard.' if partial else 'Original completed runtime receipt and its source guard; this is stricter retrospective result validation.',
        mode=dict(suite=args.suite,baseline=args.baseline,edge_only=args.edge_only,normal_only=args.normal_only),
        test_count=sum(result['test_count'] for result in results),results=results,commands=commands,
        no_runtime_reexecution=True,phone_game_or_jit_tested=False)
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(receipt['status'],receipt['test_count'])


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--work');p.add_argument('--verify-work');p.add_argument('--validation-output')
    p.add_argument('--result-index',type=int,action='append');p.add_argument('--orchestrator-snapshot',action='append')
    p.add_argument('--device',action='append');p.add_argument('--fresh-simulators',action='store_true')
    p.add_argument('--baseline',action='store_true');p.add_argument('--edge-only',action='store_true');p.add_argument('--normal-only',action='store_true')
    p.add_argument('--landscape-right',action='store_true');p.add_argument('--fresh-kind',choices=['both','phone','pad'],default='both')
    p.add_argument('--suite',choices=['touch','unified'],default='touch');a=p.parse_args()
    expected_cases=expected_ui_cases(a.suite,baseline=a.baseline,edge_only=a.edge_only,normal_only=a.normal_only)
    assert bool(a.work) != bool(a.verify_work)
    if a.verify_work:
        verify_saved_work(a,expected_cases);return
    assert bool(a.device) != a.fresh_simulators
    assert not a.result_index and not a.orchestrator_snapshot and not a.validation_output
    work=ROOT/a.work
    assert work.resolve()==work.absolute() and ROOT/'.build' in work.parents and not work.exists()
    work.mkdir(parents=True);native=work/'native';native.mkdir()
    env=dict(os.environ,DEVELOPER_DIR=os.environ.get('DEVELOPER_DIR','/Applications/Xcode.app/Contents/Developer'),CLANG_MODULE_CACHE_PATH=str(work/'module-cache'))
    commands=[]
    def run(command,label,timeout=700):
        command=list(map(str,command));commands.append(command)
        with (work/(label+'.log')).open('w') as log:r=subprocess.run(command,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
        output=(work/(label+'.log')).read_text()
        if r.returncode:raise RuntimeError(label+' failed: '+output[-3000:])
        return output.strip()
    sdk=run(['xcrun','--sdk','iphonesimulator','--show-sdk-path'],'sdk');target='x86_64-apple-ios26.0-simulator'
    preview='UnifiedLauncherPreview.swift' if a.suite=='unified' else 'TouchEditorPreview.swift'
    test='UnifiedLauncherUITests.swift' if a.suite=='unified' else 'TouchEditorUITests.swift'
    sources=sorted((SOURCE/'native').glob('*.swift'))+[SOURCE/'tests'/preview]
    if a.baseline:sources=[BASELINE/'native/TouchEditor.swift' if f==SOURCE/'native/TouchEditor.swift' else f for f in sources]
    vendor=sorted((ROOT/'vendor/ZIPFoundation/Sources/ZIPFoundation').glob('*.swift'));yaml=ROOT/'vendor/Yams/Sources/CYaml';c=sorted((yaml/'src').glob('*.c'))
    inputs=sources+vendor+c+[SOURCE/'tests'/test,SOURCE/'tests/ProfileUITests.pbxproj.template',SOURCE/'tests/ProfileUITests.xcscheme',Path(__file__)]
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();hashes={str(f.relative_to(ROOT)):sha(f) for f in inputs}
    flags=['-swift-version','5','-g','-target',target,'-sdk',sdk]
    run(['xcrun','swiftc',*flags,'-module-name','ZIPFoundation','-emit-library','-static','-emit-module','-emit-module-path',native/'ZIPFoundation.swiftmodule','-o',native/'libZIPFoundation.a',*vendor],'zip')
    for f in c:run(['xcrun','clang','-target',target,'-isysroot',sdk,'-DYAML_DECLARE_STATIC','-I'+str(yaml/'include'),'-c',f,'-o',native/(f.stem+'.o')],f.stem)
    run(['xcrun','libtool','-static','-o',native/'libCYaml.a',*[native/(f.stem+'.o') for f in c]],'yaml')
    app=work/'ProfilePreview.app';app.mkdir();bundle='io.github.hmcneill46.cabrillo.unified58.preview' if a.suite=='unified' else 'io.github.hmcneill46.cabrillo.touch.preview'
    settings=dict(CFBundleIdentifier=bundle,CFBundleName='ProfilePreview',CFBundleExecutable='ProfilePreview',CFBundlePackageType='APPL',CFBundleVersion='1',CFBundleShortVersionString='1.0',MinimumOSVersion='26.0',UIDeviceFamily=[1,2],LSRequiresIPhoneOS=True,UILaunchScreen={},UIApplicationSceneManifest={'UIApplicationSupportsMultipleScenes':False},UISupportedInterfaceOrientations=['UIInterfaceOrientationPortrait','UIInterfaceOrientationLandscapeLeft','UIInterfaceOrientationLandscapeRight'])
    (app/'Info.plist').write_bytes(plistlib.dumps(settings))
    run(['xcrun','swiftc',*flags,'-whole-module-optimization','-parse-as-library','-I',native,'-I',yaml/'include',*sources,native/'libZIPFoundation.a',native/'libCYaml.a','-lz','-o',app/'ProfilePreview'],'preview')
    run(['codesign','--force','--sign','-',app],'sign')
    project=work/'Profile.xcodeproj';project.mkdir();schemes=project/'xcshareddata/xcschemes';schemes.mkdir(parents=True)
    compiled_test=SOURCE/'tests'/test
    if a.landscape_right:
        fixture=compiled_test.read_text();assert '.landscapeLeft' in fixture
        compiled_test=work/test;compiled_test.write_text(fixture.replace('.landscapeLeft','.landscapeRight'))
    compiled_test_hash_before=sha(compiled_test)
    (project/'project.pbxproj').write_text((SOURCE/'tests/ProfileUITests.pbxproj.template').read_text().replace('SOURCE_PATH',str(compiled_test)))
    (schemes/'ProfileUITests.xcscheme').write_text((SOURCE/'tests/ProfileUITests.xcscheme').read_text())
    devices=json.loads(run(['xcrun','simctl','list','devices','available','--json'],'devices'))
    created=[]
    if a.fresh_simulators:
        runtimes=json.loads(run(['xcrun','simctl','list','runtimes','--json'],'runtimes'))
        runtime=[r['identifier'] for r in runtimes['runtimes'] if r.get('isAvailable') and r.get('platform')=='iOS'][-1]
        for role,kind in [('phone','com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro'),('pad','com.apple.CoreSimulator.SimDeviceType.iPad-Pro-11-inch-M5-12GB')]:
            if a.fresh_kind not in ('both',role):continue
            created.append(run(['xcrun','simctl','create','Cabrillo59-'+work.name+'-'+role,kind,runtime],'create-'+role))
        a.device=created
        devices=json.loads(run(['xcrun','simctl','list','devices','available','--json'],'created-devices'))
    results=[]
    try:
        for index,udid in enumerate(a.device):
            selected=[d for group in devices['devices'].values() for d in group if d['udid']==udid];assert len(selected)==1
            booted=selected[0]['state']=='Booted'
            try:
                if not booted:run(['xcrun','simctl','boot',udid],f'boot-{index}')
                run(['xcrun','simctl','bootstatus',udid,'-b'],f'bootstatus-{index}')
                run(['xcrun','simctl','install',udid,app],f'install-{index}')
                if a.baseline:selection=['-only-testing:ProfileUITests/ProfileUITests/testBuild58SmallEdgeResizeNegativeControl']
                elif a.edge_only:selection=['-only-testing:ProfileUITests/ProfileUITests/testSmallEdgeResizeKeepsLayoutSaveable']
                else:
                    selection=['-skip-testing:ProfileUITests/ProfileUITests/testBuild58SmallEdgeResizeNegativeControl']
                    if a.normal_only:selection.append('-skip-testing:ProfileUITests/ProfileUITests/testSmallEdgeResizeKeepsLayoutSaveable')
                run(['xcodebuild','-project',project,'-scheme','ProfileUITests','-destination',f'platform=iOS Simulator,id={udid}','-derivedDataPath',work/'Derived','-resultBundlePath',work/f'UI-{index}.xcresult','-parallel-testing-enabled','NO',*selection,'test'],f'uitests-{index}')
                run(['xcrun','xcresulttool','export','attachments','--path',work/f'UI-{index}.xcresult','--output-path',work/f'attachments-{index}'],f'attachments-{index}')
                summary=json.loads(run(['xcrun','xcresulttool','get','test-results','summary','--path',work/f'UI-{index}.xcresult','--compact'],f'ui-summary-{index}'))
                tests=json.loads(run(['xcrun','xcresulttool','get','test-results','tests','--path',work/f'UI-{index}.xcresult','--compact'],f'ui-tests-{index}'))
                validation=validate_ui_results(summary,tests,(work/f'uitests-{index}.log').read_text(),expected_cases)
                results.append(dict(device=selected[0],status='EXPECTED_BUILD58_INVALID_RESIZE_REPRODUCED' if a.baseline else 'PASS_BUILD59_TOUCH_EDITOR_UI',log_sha256=sha(work/f'uitests-{index}.log'),strict_validation=validation))
            finally:
                if not booted:run(['xcrun','simctl','shutdown',udid],f'shutdown-{index}')
    finally:
        for index,udid in enumerate(created):run(['xcrun','simctl','delete',udid],f'delete-{index}')
    assert hashes=={str(f.relative_to(ROOT)):sha(f) for f in inputs},'Sources changed during check'
    assert sha(compiled_test)==compiled_test_hash_before,'Compiled UI fixture changed during check'
    receipt=dict(status='PASS_BUILD58_EXPECTED_INVALID_RESIZE_UI_CONTROL' if a.baseline else 'PASS_BUILD59_TOUCH_EDITOR_UI',suite=a.suite,baseline58=a.baseline,edge_only=a.edge_only,normal_only=a.normal_only,device_orientation='landscapeRight' if a.landscape_right else 'landscapeLeft',compiled_ui_fixture_sha256=compiled_test_hash_before,compiled_ui_fixture_hash_guard=True,expected_ui_methods=sorted(expected_cases),orientation_rewrite_in_ignored_fixture_only=a.landscape_right,created_simulators_deleted=created,devices=results,source_sha256=hashes,commands=commands,fixture_not_in_device_binary=True,phone_game_or_jit_tested=False)
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'])
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Adversarial controls for the real xcresult + log UI result validator.

Run directly after the helper is inlined into tools/check_input_fixes59_ui.py.
During development, --validator accepts the ignored prototype's path.
"""
import argparse
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[4]
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--validator', type=Path, default=ROOT / 'tools/check_input_fixes59_ui.py')
args, remaining = parser.parse_known_args()
spec = importlib.util.spec_from_file_location('ui_results_validator', args.validator)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def evidence(expected):
    count = len(expected)
    summary = dict(result='Passed', totalTestCount=count, passedTests=count,
                   failedTests=0, skippedTests=0, expectedFailures=0, testFailures=[],
                   devicesAndConfigurations=[dict(passedTests=count, failedTests=0,
                                                   skippedTests=0, expectedFailures=0)])
    cases = [dict(nodeType='Test Case', name=method + '()',
                  nodeIdentifier='ProfileUITests/' + method + '()', result='Passed') for method in expected]
    tests = dict(testNodes=[dict(nodeType='Test Plan', children=[dict(nodeType='Test Suite', children=cases)])])
    log = '\n'.join("Test Case '-[ProfileUITests.ProfileUITests %s]' passed (1.001 seconds)." % method
                    for method in expected)
    log += '\n' + '\n'.join(expected.values())
    log += '\n Executed %s tests, with 0 failures (0 unexpected) in 1.0 seconds\n** TEST SUCCEEDED **\n' % count
    return summary, tests, log


class UIResultsValidatorTests(unittest.TestCase):
    def setUp(self):
        self.expected = validator.expected_ui_cases('touch', normal_only=True)
        self.summary, self.tests, self.log = evidence(self.expected)

    def validate(self, summary=None, tests=None, log=None, expected=None):
        return validator.validate_ui_results(self.summary if summary is None else summary,
                                             self.tests if tests is None else tests,
                                             self.log if log is None else log,
                                             self.expected if expected is None else expected)

    def assertRejected(self, **kwargs):
        with self.assertRaises(ValueError):
            self.validate(**kwargs)

    def cases(self):
        return self.tests['testNodes'][0]['children'][0]['children']

    def test_all_five_modes_have_exact_expected_nonzero_counts(self):
        for suite, options, count in [('touch', {}, 4), ('touch', {'normal_only': True}, 3),
                                       ('touch', {'edge_only': True}, 1), ('touch', {'baseline': True}, 1),
                                       ('unified', {}, 3)]:
            with self.subTest(suite=suite, options=options):
                expected = validator.expected_ui_cases(suite, **options)
                summary, tests, log = evidence(expected)
                self.assertEqual(validator.validate_ui_results(summary, tests, log, expected)['test_count'], count)

    def test_invalid_suite_and_mutually_exclusive_modes(self):
        for suite, options in [('missing', {}), ('unified', {'edge_only': True}),
                               ('touch', {'baseline': True, 'normal_only': True})]:
            with self.subTest(suite=suite, options=options), self.assertRaises(ValueError):
                validator.expected_ui_cases(suite, **options)

    def test_zero_tests_cannot_pass(self):
        self.summary.update(totalTestCount=0, passedTests=0)
        self.tests['testNodes'] = []
        self.assertRejected(log='Executed 0 tests, with 0 failures (0 unexpected)\n** TEST SUCCEEDED **')

    def test_marker_only_cannot_pass(self):
        self.assertRejected(log='\n'.join(self.expected.values()) + '\n** TEST SUCCEEDED **')

    def test_good_logs_cannot_replace_missing_tree(self):
        self.assertRejected(tests={'testNodes': []})

    def test_good_tree_cannot_replace_missing_summary_counts(self):
        for key in ['totalTestCount', 'passedTests', 'failedTests', 'skippedTests', 'expectedFailures']:
            changed = copy.deepcopy(self.summary); changed.pop(key)
            with self.subTest(key=key): self.assertRejected(summary=changed)

    def test_wrong_summary_counts_and_types_fail(self):
        for key, value in [('totalTestCount', 4), ('passedTests', 2), ('failedTests', 1),
                            ('skippedTests', 1), ('expectedFailures', 1), ('failedTests', False),
                            ('totalTestCount', '3'), ('passedTests', 3.0)]:
            changed = copy.deepcopy(self.summary); changed[key] = value
            with self.subTest(key=key, value=value): self.assertRejected(summary=changed)

    def test_failure_summary_or_failure_array_fails(self):
        for change in [dict(result='Failed'), dict(testFailures=[{'failureText': 'broken'}]), dict(testFailures=None)]:
            with self.subTest(change=change): self.assertRejected(summary=dict(self.summary, **change))

    def test_missing_or_extra_device_result_fails(self):
        for configurations in [None, [], [False], [self.summary['devicesAndConfigurations'][0]] * 2]:
            with self.subTest(configurations=configurations):
                self.assertRejected(summary=dict(self.summary, devicesAndConfigurations=configurations))

    def test_device_counts_must_match(self):
        for key, value in [('passedTests', 2), ('failedTests', 1), ('skippedTests', 1), ('expectedFailures', 1)]:
            changed = copy.deepcopy(self.summary); changed['devicesAndConfigurations'][0][key] = value
            with self.subTest(key=key): self.assertRejected(summary=changed)

    def test_missing_actual_case_fails(self):
        self.cases().pop(); self.assertRejected()

    def test_unexpected_extra_case_fails(self):
        self.cases().append(dict(self.cases()[0])); self.assertRejected()

    def test_duplicate_case_cannot_replace_expected_case(self):
        self.cases()[1] = dict(self.cases()[0]); self.assertRejected()

    def test_unexpected_case_identity_fails(self):
        for field, value in [('name', 'testOther()'), ('nodeIdentifier', 'OtherTests/testNativeEditor()'),
                              ('result', 'Skipped'), ('result', 'Failed'), ('name', 'testNativeEditor')]:
            changed = copy.deepcopy(self.tests)
            changed['testNodes'][0]['children'][0]['children'][0][field] = value
            with self.subTest(field=field, value=value): self.assertRejected(tests=changed)

    def test_nested_case_or_malformed_nodes_fail(self):
        changed = copy.deepcopy(self.tests)
        changed['testNodes'][0]['children'][0]['children'][0]['children'] = [dict(self.cases()[1])]
        self.assertRejected(tests=changed)
        for tests in [{'testNodes': None}, {'testNodes': [False]}, {'testNodes': [{'children': 'bad'}]}]:
            with self.subTest(tests=tests): self.assertRejected(tests=tests)

    def test_missing_or_wrong_passed_log_method_fails(self):
        first = next(iter(self.expected))
        self.assertRejected(log=self.log.replace(first + "]' passed", "testOther]' passed"))
        self.assertRejected(log='\n'.join(line for line in self.log.splitlines() if not line.startswith('Test Case')))

    def test_duplicate_passed_log_line_fails(self):
        self.assertRejected(log=self.log + self.log.splitlines()[0] + '\n')

    def test_log_wrong_counts_zero_failures_and_missing_counts(self):
        for replacement in ['', 'Executed 0 tests, with 0 failures (0 unexpected)',
                             'Executed 3 tests, with 1 failure (0 unexpected)',
                             'Executed 3 tests, with 0 failures (1 unexpected)']:
            with self.subTest(replacement=replacement):
                self.assertRejected(log=self.log.replace('Executed 3 tests, with 0 failures (0 unexpected)', replacement))

    def test_inconsistent_log_summaries_fail(self):
        self.assertRejected(log=self.log + '\nExecuted 0 tests, with 0 failures (0 unexpected)\n')

    def test_each_assertion_marker_required(self):
        for marker in self.expected.values():
            with self.subTest(marker=marker): self.assertRejected(log=self.log.replace(marker, ''))

    def test_successful_build_without_successful_test_conclusion_fails(self):
        self.assertRejected(log=self.log.replace('** TEST SUCCEEDED **', '** BUILD SUCCEEDED **'))
        self.assertRejected(log=self.log + '\n** TEST FAILED **\n')

    def test_interrupted_test_or_build_cannot_be_hidden_by_pass_text(self):
        for marker in ['** TEST INTERRUPTED **', '** BUILD INTERRUPTED **']:
            with self.subTest(marker=marker): self.assertRejected(log=self.log + '\n' + marker + '\n')

    def test_empty_or_malformed_expectations_fail(self):
        for expected in [{}, [], {'testNativeEditor': ''}, {'notATest': 'MARKER'}]:
            with self.subTest(expected=expected): self.assertRejected(expected=expected)

    def test_only_known_completed_runtime_statuses_claim_source_guard(self):
        for status in ['PASS_BUILD59_TOUCH_EDITOR_UI', 'PASS_BUILD58_EXPECTED_INVALID_RESIZE_UI_CONTROL']:
            with self.subTest(status=status):
                self.assertIs(validator.validate_runtime_receipt_status({'status': status}, False), True)

    def test_known_partial_runtime_never_claims_completed_source_guard(self):
        self.assertIs(validator.validate_runtime_receipt_status(
            {'status': 'PARTIAL_PHONE4_PASS_PAD_INTERRUPTED_NO_AGGREGATE_PASS'}, True), False)

    def test_bad_or_mismatched_runtime_statuses_fail(self):
        full = 'PASS_BUILD59_TOUCH_EDITOR_UI'
        partial = 'PARTIAL_PHONE4_PASS_PAD_INTERRUPTED_NO_AGGREGATE_PASS'
        for status, is_partial in [(None, False), (False, False), ([], False), ('PASS', False),
                                   ('FAIL', False), ('INTERRUPTED', False), (partial, False),
                                   (full, True), ('PASS_BUILD58_EXPECTED_INVALID_RESIZE_UI_CONTROL', True),
                                   (None, True), ('PARTIAL', True)]:
            with self.subTest(status=status, partial=is_partial), self.assertRaises(ValueError):
                validator.validate_runtime_receipt_status({'status': status}, is_partial)

    def test_nonmapping_runtime_metadata_fails(self):
        for metadata in [None, [], 'PASS_BUILD59_TOUCH_EDITOR_UI', False]:
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                validator.validate_runtime_receipt_status(metadata, False)


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], *remaining])

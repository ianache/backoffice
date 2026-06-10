"""
Unit tests for backoffice_sdk.evaluator — Python port of the canonical
backend OPERATORS / _evaluate_rule / evaluate_flag (Plan 01) and the
sdk-js evaluateFlag bootstrap-cache semantics (Plan 06).

Fixture (rule, user) pairs for the 7 operators mirror
backend/tests/test_feature_flags_eval.py::TestEvaluateRule exactly,
for cross-implementation parity (4-way consistency: backend, sdk-js,
sdk-python, frontend RuleSimulator).
"""
from backoffice_sdk.evaluator import evaluate_rule, evaluate_flag, OPERATORS


# ---------------------------------------------------------------------------
# OPERATORS table shape
# ---------------------------------------------------------------------------

class TestOperatorsTable:
    def test_seven_operators_present(self):
        assert set(OPERATORS.keys()) == {
            'equals', 'in', 'notIn', 'contains', 'regex', 'greaterThan', 'lessThan',
        }


# ---------------------------------------------------------------------------
# evaluate_rule — ported fixtures from backend/tests/test_feature_flags_eval.py
# ---------------------------------------------------------------------------

class TestEvaluateRule:

    def test_equals_true(self):
        rule = {'attribute': 'country', 'operator': 'equals', 'value': 'PE'}
        assert evaluate_rule(rule, {'country': 'PE'}) is True

    def test_equals_false(self):
        rule = {'attribute': 'country', 'operator': 'equals', 'value': 'PE'}
        assert evaluate_rule(rule, {'country': 'US'}) is False

    def test_in_true(self):
        rule = {'attribute': 'country', 'operator': 'in', 'value': ['PE', 'AR']}
        assert evaluate_rule(rule, {'country': 'PE'}) is True

    def test_in_false(self):
        rule = {'attribute': 'country', 'operator': 'in', 'value': ['PE', 'AR']}
        assert evaluate_rule(rule, {'country': 'US'}) is False

    def test_not_in_true(self):
        rule = {'attribute': 'country', 'operator': 'notIn', 'value': ['US']}
        assert evaluate_rule(rule, {'country': 'PE'}) is True

    def test_not_in_false(self):
        rule = {'attribute': 'country', 'operator': 'notIn', 'value': ['US']}
        assert evaluate_rule(rule, {'country': 'US'}) is False

    def test_contains_true(self):
        rule = {'attribute': 'email', 'operator': 'contains', 'value': '@acme'}
        assert evaluate_rule(rule, {'email': 'john@acme.com'}) is True

    def test_contains_false(self):
        rule = {'attribute': 'email', 'operator': 'contains', 'value': '@acme'}
        assert evaluate_rule(rule, {'email': 'john@other.com'}) is False

    def test_regex_true(self):
        rule = {'attribute': 'email', 'operator': 'regex', 'value': '^admin'}
        assert evaluate_rule(rule, {'email': 'admin@co.com'}) is True

    def test_regex_false(self):
        rule = {'attribute': 'email', 'operator': 'regex', 'value': '^admin'}
        assert evaluate_rule(rule, {'email': 'user@co.com'}) is False

    def test_unknown_operator_returns_false_no_exception(self):
        rule = {'attribute': 'country', 'operator': 'unknown_op', 'value': 'PE'}
        assert evaluate_rule(rule, {'country': 'PE'}) is False

    def test_missing_attribute_returns_false_no_key_error(self):
        rule = {'attribute': 'missing_attr', 'operator': 'equals', 'value': 'X'}
        assert evaluate_rule(rule, {}) is False

    def test_missing_attribute_with_in_operator(self):
        rule = {'attribute': 'plan', 'operator': 'in', 'value': ['free', 'basic']}
        assert evaluate_rule(rule, {}) is False

    def test_greater_than_true(self):
        rule = {'attribute': 'ltv', 'operator': 'greaterThan', 'value': 500}
        assert evaluate_rule(rule, {'ltv': 600}) is True

    def test_greater_than_false(self):
        rule = {'attribute': 'ltv', 'operator': 'greaterThan', 'value': 500}
        assert evaluate_rule(rule, {'ltv': 400}) is False

    def test_greater_than_numeric_strings(self):
        """Numeric strings are coerced via float() before comparison."""
        rule = {'attribute': 'ltv', 'operator': 'greaterThan', 'value': '500'}
        assert evaluate_rule(rule, {'ltv': '600'}) is True

    def test_greater_than_non_numeric_returns_false(self):
        """Non-numeric actual value fails closed via float() ValueError caught."""
        rule = {'attribute': 'plan', 'operator': 'greaterThan', 'value': 500}
        assert evaluate_rule(rule, {'plan': 'enterprise'}) is False

    def test_less_than_true(self):
        rule = {'attribute': 'ltv', 'operator': 'lessThan', 'value': 500}
        assert evaluate_rule(rule, {'ltv': 100}) is True

    def test_less_than_false(self):
        rule = {'attribute': 'ltv', 'operator': 'lessThan', 'value': 500}
        assert evaluate_rule(rule, {'ltv': 600}) is False

    def test_less_than_missing_attribute(self):
        rule = {'attribute': 'ltv', 'operator': 'lessThan', 'value': 500}
        assert evaluate_rule(rule, {}) is False

    def test_all_seven_operators_have_true_case(self):
        true_cases = {
            'equals': ({'attribute': 'country', 'operator': 'equals', 'value': 'PE'}, {'country': 'PE'}),
            'in': ({'attribute': 'country', 'operator': 'in', 'value': ['PE', 'AR']}, {'country': 'PE'}),
            'notIn': ({'attribute': 'country', 'operator': 'notIn', 'value': ['US']}, {'country': 'PE'}),
            'contains': ({'attribute': 'email', 'operator': 'contains', 'value': '@acme'}, {'email': 'john@acme.com'}),
            'regex': ({'attribute': 'email', 'operator': 'regex', 'value': '^admin'}, {'email': 'admin@co.com'}),
            'greaterThan': ({'attribute': 'ltv', 'operator': 'greaterThan', 'value': 500}, {'ltv': 600}),
            'lessThan': ({'attribute': 'ltv', 'operator': 'lessThan', 'value': 500}, {'ltv': 100}),
        }
        for op, (rule, user) in true_cases.items():
            assert evaluate_rule(rule, user) is True, f"operator {op} should return True"


# ---------------------------------------------------------------------------
# evaluate_flag — bootstrap-cache entry semantics (Plan 06 / sdk-js parity)
# ---------------------------------------------------------------------------

class TestEvaluateFlag:

    def test_disabled_flag_returns_false(self):
        entry = {
            'enabled': False,
            'rules': [{'attribute': 'country', 'operator': 'equals', 'value': 'PE', 'result': True}],
            'segments': [],
            'default_val': True,
            'scope': 'global',
        }
        assert evaluate_flag(entry, {'country': 'PE'}) is False

    def test_matching_rule_returns_rule_result(self):
        entry = {
            'enabled': True,
            'rules': [{'attribute': 'country', 'operator': 'equals', 'value': 'PE', 'result': True}],
            'segments': [],
            'default_val': False,
            'scope': 'global',
        }
        assert evaluate_flag(entry, {'country': 'PE'}) is True

    def test_no_matching_rule_returns_default_val(self):
        entry = {
            'enabled': True,
            'rules': [{'attribute': 'country', 'operator': 'equals', 'value': 'PE', 'result': True}],
            'segments': [],
            'default_val': False,
            'scope': 'global',
        }
        assert evaluate_flag(entry, {'country': 'US'}) is False

    def test_rule_based_segment_any_match_returns_true(self):
        entry = {
            'enabled': True,
            'rules': [],
            'segments': [
                {
                    'id': 1,
                    'type': 'rule_based',
                    'conditions': [{'attribute': 'ltv', 'operator': 'greaterThan', 'value': 500}],
                    'members': [],
                },
            ],
            'default_val': False,
            'scope': 'global',
        }
        assert evaluate_flag(entry, {'ltv': 600}) is True

    def test_rule_based_segment_no_match_returns_default_val(self):
        entry = {
            'enabled': True,
            'rules': [],
            'segments': [
                {
                    'id': 1,
                    'type': 'rule_based',
                    'conditions': [{'attribute': 'ltv', 'operator': 'greaterThan', 'value': 500}],
                    'members': [],
                },
            ],
            'default_val': False,
            'scope': 'global',
        }
        assert evaluate_flag(entry, {'ltv': 100}) is False

    def test_manual_segment_member_by_id_returns_true(self):
        entry = {
            'enabled': True,
            'rules': [],
            'segments': [
                {'id': 2, 'type': 'manual', 'conditions': [], 'members': ['uuid-1', 'uuid-2']},
            ],
            'default_val': False,
            'scope': 'global',
        }
        assert evaluate_flag(entry, {'id': 'uuid-1'}) is True

    def test_manual_segment_member_by_sub_returns_true(self):
        entry = {
            'enabled': True,
            'rules': [],
            'segments': [
                {'id': 2, 'type': 'manual', 'conditions': [], 'members': ['uuid-1', 'uuid-2']},
            ],
            'default_val': False,
            'scope': 'global',
        }
        assert evaluate_flag(entry, {'sub': 'uuid-2'}) is True

    def test_manual_segment_member_by_user_id_returns_true(self):
        entry = {
            'enabled': True,
            'rules': [],
            'segments': [
                {'id': 2, 'type': 'manual', 'conditions': [], 'members': ['uuid-1', 'uuid-2']},
            ],
            'default_val': False,
            'scope': 'global',
        }
        assert evaluate_flag(entry, {'user_id': 'uuid-2'}) is True

    def test_manual_segment_non_member_returns_default_val(self):
        entry = {
            'enabled': True,
            'rules': [],
            'segments': [
                {'id': 2, 'type': 'manual', 'conditions': [], 'members': ['uuid-1', 'uuid-2']},
            ],
            'default_val': False,
            'scope': 'global',
        }
        assert evaluate_flag(entry, {'id': 'uuid-999'}) is False

    def test_no_rule_no_segment_match_returns_default_val_true(self):
        entry = {
            'enabled': True,
            'rules': [],
            'segments': [],
            'default_val': True,
            'scope': 'global',
        }
        assert evaluate_flag(entry, {}) is True

    def test_inline_rule_match_takes_priority_over_segment(self):
        entry = {
            'enabled': True,
            'rules': [{'attribute': 'country', 'operator': 'equals', 'value': 'PE', 'result': True}],
            'segments': [
                {'id': 2, 'type': 'manual', 'conditions': [], 'members': ['uuid-1']},
            ],
            'default_val': False,
            'scope': 'global',
        }
        # Rule matches with result=True even though user is also in segment
        assert evaluate_flag(entry, {'id': 'uuid-1', 'country': 'PE'}) is True

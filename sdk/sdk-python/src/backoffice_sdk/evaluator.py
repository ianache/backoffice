"""
Local (DB-free) flag evaluation engine for backoffice_sdk.

Mirrors the canonical backend OPERATORS table and _evaluate_rule()/evaluate_flag()
logic in backend/app/domains/feature_flags/service.py (Plan 01), and the
sdk-js evaluator.ts evaluateFlag() bootstrap-cache semantics (Plan 06),
including manual segment members[] resolution.
"""
import re

OPERATORS = {
    'equals':      lambda actual, expected: actual == expected,
    'in':          lambda actual, expected: actual in expected,
    'notIn':       lambda actual, expected: actual not in expected,
    'contains':    lambda actual, expected: expected in str(actual),
    'regex':       lambda actual, expected: bool(re.match(expected, str(actual))),
    'greaterThan': lambda actual, expected: float(actual) > float(expected),
    'lessThan':    lambda actual, expected: float(actual) < float(expected),
    'anyOf':       lambda actual, expected: (
        bool(set(actual) & set(expected)) if isinstance(actual, (list, tuple, set))
        else actual in expected
    ),
}


def evaluate_rule(rule: dict, user: dict) -> bool:
    """Evaluate a single rule against user attributes.

    Returns False on unknown operator, missing attribute, or any exception.
    Mirrors backend/app/domains/feature_flags/service.py::_evaluate_rule exactly.
    """
    attr = rule.get('attribute', '')
    op = rule.get('operator', 'equals')
    val = rule.get('value')
    actual = user.get(attr)
    if actual is None:
        return False
    fn = OPERATORS.get(op)
    if fn is None:
        return False
    try:
        return bool(fn(actual, val))
    except Exception:
        return False


def evaluate_flag(entry: dict, user: dict) -> bool:
    """Evaluate a single flag entry from the bootstrap cache.

    entry: {enabled, rules, segments, default_val, scope}
    segments: [{id, type, conditions, members}]

    DB-free: manual segment membership resolved via inlined `members` list (Plan 06).
    Mirrors sdk-js evaluator.ts::evaluateFlag any-match semantics.

    Company-scope target guard (TGT-03): when entry['scope'] == 'company' and
    entry.get('company_id') is not None, the entry only applies if
    user.get('company_id') == entry['company_id'] — otherwise returns False
    (fail-closed). Legacy entries without a 'company_id' key (or with it set
    to None) skip this check entirely. Tenant/product targeting is enforced
    upstream by bootstrap filtering (by SDK client identity), not here.

    Rule combination mode (AND-01): `entry.get('rule_combination_mode') or
    'first_match'`.
    - 'and' with non-empty rules: True only if EVERY rule matches (per-rule
      `result` is ignored); any failure returns False immediately without
      consulting segments or default_val.
    - 'and' with empty rules: falls through to the legacy segment/default_val
      path unchanged (vacuous AND).
    - 'first_match' (or missing/empty): first matching rule wins, as before.
    """
    if not entry.get('enabled'):
        return False

    if entry.get('scope') == 'company' and entry.get('company_id') is not None:
        if user.get('company_id') != entry.get('company_id'):
            return False

    mode = entry.get('rule_combination_mode') or 'first_match'
    rules = entry.get('rules', [])
    if mode == 'and' and rules:
        # AND mode: True only if ALL rules match; per-rule `result` is ignored (AND-01).
        return all(evaluate_rule(rule, user) for rule in rules)

    for rule in rules:
        if evaluate_rule(rule, user):
            return bool(rule.get('result', entry.get('default_val', False)))

    user_id = user.get('id') or user.get('sub') or user.get('user_id')
    for seg in entry.get('segments', []):
        seg_type = seg.get('type', 'manual')
        if seg_type == 'rule_based':
            if any(evaluate_rule(c, user) for c in seg.get('conditions', [])):
                return True
        elif seg_type == 'manual':
            if user_id and str(user_id) in seg.get('members', []):
                return True

    return bool(entry.get('default_val', False))

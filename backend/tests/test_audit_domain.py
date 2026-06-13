from app.domains.audit.schemas import (
    AuditLogCreate,
    AuditLogResponse,
    AuditLogListResponse,
)
from app.domains.audit.service import compute_diff
from app.domains.audit.router import router, _audit_tenant_filter


def test_compute_diff_added_removed_modified():
    before = {"a": 1, "b": 2}
    after = {"b": 3, "c": 4}
    result = compute_diff(before, after)
    assert result == {
        "added": {"c": 4},
        "removed": {"a": 1},
        "modified": {"b": {"before": 2, "after": 3}},
    }


def test_compute_diff_none_before_defaults_to_empty():
    result = compute_diff(None, {"a": 1})
    assert result == {"added": {"a": 1}, "removed": {}, "modified": {}}


def test_compute_diff_identical_payloads_no_diff():
    result = compute_diff({"a": 1}, {"a": 1})
    assert result == {"added": {}, "removed": {}, "modified": {}}


def test_audit_log_create_accepts_dict_payloads():
    payload = AuditLogCreate(
        user_id="u1",
        action_type="CREATE_FLAG",
        target_type="flag",
        target_id="f1",
        payload_before={"a": 1},
        payload_after={"a": 2},
    )
    assert payload.payload_before == {"a": 1}
    assert payload.payload_after == {"a": 2}


def test_audit_log_list_response_constructs_with_empty_items():
    response = AuditLogListResponse(items=[], total=0, page=1, limit=25)
    assert response.items == []
    assert response.total == 0
    assert response.page == 1
    assert response.limit == 25


def test_audit_log_response_round_trip_excludes_payloads():
    assert "payload_before" not in AuditLogResponse.model_fields
    assert "payload_after" not in AuditLogResponse.model_fields


def test_audit_tenant_filter_platform_admin_sees_all():
    assert _audit_tenant_filter(["PlatformAdmin"], "t1") is None


def test_audit_tenant_filter_tenant_admin_scoped():
    assert _audit_tenant_filter(["TenantAdmin"], "t1") == "t1"


def test_audit_router_has_only_get_routes():
    assert len(router.routes) > 0
    for r in router.routes:
        assert r.methods == {'GET'}


def test_action_type_constants_cover_flags_and_segments():
    from app.domains.audit.schemas import ActionType
    for name in ["CREATE_FLAG", "UPDATE_FLAG", "DELETE_FLAG", "ENABLE_FLAG", "DISABLE_FLAG",
                  "CREATE_SEGMENT", "UPDATE_SEGMENT", "DELETE_SEGMENT"]:
        assert hasattr(ActionType, name)


def test_audit_request_meta_returns_none_for_none_request():
    from app.domains.feature_flags.router import _audit_request_meta
    assert _audit_request_meta(None) == (None, None)

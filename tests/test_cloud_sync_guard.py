from services.cloud_sync_guard import (
    payload_has_meaningful_data,
    payload_snapshot,
    should_keep_local_data_before_auto_import,
)


def test_payload_has_meaningful_data_false_for_empty_payload():
    assert payload_has_meaningful_data({}) is False
    assert payload_has_meaningful_data({"transactions": {}, "documents": [], "recurring": {"items": []}}) is False


def test_payload_has_meaningful_data_true_for_finance_keys():
    assert payload_has_meaningful_data({"transactions": {"2026-04": [{"amount": 10}]}}) is True
    assert payload_has_meaningful_data({"documents": [{"name": "proof.pdf"}]}) is True
    assert payload_has_meaningful_data({"recurring": {"items": [{"name": "Rent"}]}}) is True


def test_should_keep_local_data_before_auto_import_when_remote_differs():
    local_payload = {"transactions": {"2026-04": [{"amount": 10, "note": "local"}]}}
    remote_payload = {"transactions": {"2026-04": [{"amount": 10, "note": "cloud"}]}}

    assert should_keep_local_data_before_auto_import(local_payload, remote_payload) is True


def test_should_not_keep_local_data_when_remote_matches():
    payload = {"transactions": {"2026-04": [{"amount": 10, "note": "same"}]}}

    assert should_keep_local_data_before_auto_import(payload, payload) is False


def test_should_not_keep_local_data_when_local_is_empty():
    local_payload = {"transactions": {}, "documents": []}
    remote_payload = {"transactions": {"2026-04": [{"amount": 20}]}}

    assert should_keep_local_data_before_auto_import(local_payload, remote_payload) is False


def test_payload_snapshot_is_stable_for_equal_payloads():
    payload_a = {"transactions": {"2026-04": [{"amount": 1, "note": "x"}]}, "documents": []}
    payload_b = {"documents": [], "transactions": {"2026-04": [{"note": "x", "amount": 1}]}}

    assert payload_snapshot(payload_a) == payload_snapshot(payload_b)

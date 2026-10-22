import pytest
from fastapi import HTTPException
from mock_backend import MOCK_ORDERS, get_order, root


def test_example_orders_cover_three_support_scenarios():
    assert set(root()["available_example_orders"]) == set(MOCK_ORDERS)
    missing = get_order("kv-10482")
    damaged = get_order("KV-20991")
    partner = get_order("KV-77830")
    assert "ontbrekend" in missing["issue_type"]
    assert "beschadigd" in damaged["issue_type"]
    assert partner["partner_order"] is True


def test_unknown_order_returns_404_without_customer_data():
    with pytest.raises(HTTPException) as failure:
        get_order("KV-99999")
    assert failure.value.status_code == 404
    assert "niet gevonden" in failure.value.detail

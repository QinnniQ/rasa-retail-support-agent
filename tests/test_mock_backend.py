from fastapi.testclient import TestClient

from mock_backend import app


client = TestClient(app)


def test_example_orders_cover_three_support_scenarios():
    root = client.get("/")
    assert root.status_code == 200
    assert set(root.json()["available_example_orders"]) == {"KV-10482", "KV-20991", "KV-77830"}

    missing = client.get("/orders/kv-10482")
    damaged = client.get("/orders/KV-20991")
    partner = client.get("/orders/KV-77830")
    assert "ontbrekend" in missing.json()["issue_type"]
    assert "beschadigd" in damaged.json()["issue_type"]
    assert partner.json()["partner_order"] is True


def test_unknown_order_returns_404_without_customer_data():
    response = client.get("/orders/KV-99999")
    assert response.status_code == 404
    assert "niet gevonden" in response.json()["detail"]

import asyncio
import pytest
import httpx
import mock_backend
from support.policy import advice, classify, extract_order_id
from support.models import Order
from support.store import Store


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(mock_backend, "STORE", Store(str(tmp_path / "support.db")))
    monkeypatch.setattr(mock_backend, "MODE", "demo")
    monkeypatch.setenv("SUPPORT_OPS_TOKEN", "test-secret")
    class Client:
        def request(self, method, path, **kwargs):
            async def perform():
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=mock_backend.app), base_url="http://testserver") as client:
                    return await client.request(method, path, **kwargs)
            return asyncio.run(perform())

        def get(self, path, **kwargs):
            return self.request("GET", path, **kwargs)

        def post(self, path, **kwargs):
            return self.request("POST", path, **kwargs)

        def patch(self, path, **kwargs):
            return self.request("PATCH", path, **kwargs)

    return Client()


def ask(client, sender, text, category=None):
    return client.post("/api/chat", json={"session_id": sender, "message": text, "category": category})


def test_order_contract_and_validation(client):
    assert client.get("/orders/KV-10482").json()["items"][1]["quantity_delivered"] == 0
    assert client.get("/orders/KV-99999").status_code == 404
    assert client.get("/orders/bad").status_code == 422
    assert extract_order_id("mijn order is kv-10482") == "KV-10482"


def test_multiturn_missing_item_creates_persisted_case(client):
    sender = "session_alpha"
    first = ask(client, sender, "Er ontbreekt een artikel", "missing").json()
    assert "ordernummer" in first["messages"][0]
    second = ask(client, sender, "KV-10482").json()
    assert second["order"]["order_id"] == "KV-10482"
    assert second["case_id"] is not None
    assert second["trace"][-1]["step"] == "handoff"
    again = ask(client, sender, "KV-10482").json()
    assert again["case_id"] == second["case_id"]
    cases = client.get("/api/cases", headers={"X-Support-Token": "test-secret"}).json()
    assert len(cases) == 1
    assert cases[0]["reason"] == "Ontbrekend artikel vereist orderonderzoek"


def test_sessions_are_isolated(client):
    ask(client, "session_alpha", "Beschadigd artikel", "damaged")
    result = ask(client, "session_beta0", "KV-50036").json()
    assert result["case_id"] is None
    assert result["order"]["order_id"] == "KV-50036"


def test_policy_distinguishes_partner_refund_and_return():
    partner = Order.model_validate(mock_backend.MOCK_ORDERS["KV-77830"])
    assert advice(partner, "return")[1] is True
    refund = Order.model_validate(mock_backend.MOCK_ORDERS["KV-50036"])
    assert "afgerond" in advice(refund, "refund")[0]
    exception = Order.model_validate(mock_backend.MOCK_ORDERS["KV-60047"])
    assert advice(exception, "return")[1] is True
    assert classify("Mijn product is kapot aangekomen") == "damaged"


def test_case_auth_lifecycle_and_validation(client):
    created = ask(client, "session_gamma", "Mijn product is beschadigd KV-20991", "damaged").json()
    assert client.get("/api/cases").status_code == 401
    headers = {"X-Support-Token": "test-secret"}
    case_id = created["case_id"]
    updated = client.patch(f"/api/cases/{case_id}", headers=headers, json={"status": "investigating", "assignee": "Demo medewerker"})
    assert updated.status_code == 200
    assert updated.json()["assignee"] == "Demo medewerker"
    assert len(client.get("/api/cases?status=investigating", headers=headers).json()) == 1
    assert client.patch("/api/cases/999", headers=headers, json={"status": "resolved"}).status_code == 404
    assert client.patch(f"/api/cases/{case_id}", headers=headers, json={"status": "unknown"}).status_code == 422


def test_rasa_outage_is_honest(client, monkeypatch):
    monkeypatch.setattr(mock_backend, "MODE", "rasa")
    monkeypatch.setattr(mock_backend, "RASA_URL", "http://127.0.0.1:1")
    response = ask(client, "session_delta", "Hoi")
    assert response.status_code == 503
    assert "Rasa" in response.json()["detail"]


def test_rasa_mode_uses_only_action_supplied_order_card(client, monkeypatch):
    monkeypatch.setattr(mock_backend, "MODE", "rasa")
    async def without_action(sender, message):
        return [{"text": "Ik heb je ordernummer ontvangen."}]
    monkeypatch.setattr(mock_backend, "send_to_rasa", without_action)
    plain = ask(client, "session_rasa0", "KV-10482").json()
    assert plain["order"] is None
    assert plain["mode"] == "rasa"
    async def with_action(sender, message):
        return [{"text": "Voorbeeldorder opgehaald.", "custom": {"order": mock_backend.MOCK_ORDERS["KV-10482"], "case_id": 7}}]
    monkeypatch.setattr(mock_backend, "send_to_rasa", with_action)
    rich = ask(client, "session_rasa0", "KV-10482").json()
    assert rich["order"]["order_id"] == "KV-10482"
    assert rich["case_id"] == 7


def test_bad_payload(client):
    assert ask(client, "bad", "Hi").status_code == 422
    assert ask(client, "session_alpha", "").status_code == 422

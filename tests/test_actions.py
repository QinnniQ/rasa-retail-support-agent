from pathlib import Path

import pytest
import requests

from actions import actions
from mock_backend import MOCK_ORDERS


class Dispatcher:
    def __init__(self):
        self.messages = []

    def utter_message(self, **kwargs):
        self.messages.append(kwargs["text"])


class Tracker:
    def __init__(self, slot=None, text=""):
        self.slot = slot
        self.latest_message = {"text": text}

    def get_slot(self, name):
        assert name == "order_id"
        return self.slot


def run_action(slot=None, text=""):
    dispatcher = Dispatcher()
    events = actions.ActionCheckOrderContext().run(dispatcher, Tracker(slot, text), {})
    assert events == []
    return dispatcher.messages[0]


def test_order_id_extraction_and_invalid_slot(monkeypatch):
    assert actions.extract_order_id("Mijn order is kv-10482.") == "KV-10482"
    assert actions.extract_order_id("geen nummer") is None

    def forbidden_get(*args, **kwargs):
        raise AssertionError("Invalid order ID must not reach backend")

    monkeypatch.setattr(actions.requests, "get", forbidden_get)
    assert "ordernummer" in run_action(slot="../../admin").lower()


@pytest.mark.parametrize(
    ("order_id", "expected"),
    [("KV-10482", "ontbrekend"), ("KV-20991", "beschadigd"), ("KV-77830", "partnerartikel")],
)
def test_action_uses_backend_data_for_customer_advice(monkeypatch, order_id, expected):
    calls = []

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return MOCK_ORDERS[order_id]

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return Response()

    monkeypatch.setattr(actions.requests, "get", fake_get)
    message = run_action(slot=order_id.lower())
    assert calls == [(f"http://localhost:8001/orders/{order_id}", 5)]
    assert expected in message.lower()
    assert "Advies:" in message
    assert "Artikeloverzicht:" in message


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (requests.exceptions.ConnectionError, "niet bereiken"),
        (requests.exceptions.Timeout, "te langzaam"),
        (requests.exceptions.RequestException, "ging iets mis"),
    ],
)
def test_action_explains_backend_failures(monkeypatch, error, expected):
    def fail(*args, **kwargs):
        raise error("sample")

    monkeypatch.setattr(actions.requests, "get", fail)
    assert expected in run_action(slot="KV-10482")


@pytest.mark.parametrize(("status_code", "expected"), [(404, "niet vinden"), (503, "gaf een fout")])
def test_action_distinguishes_missing_order_from_backend_failure(monkeypatch, status_code, expected):
    def fail(*args, **kwargs):
        response = requests.Response()
        response.status_code = status_code
        raise requests.exceptions.HTTPError("sample", response=response)

    monkeypatch.setattr(actions.requests, "get", fail)
    assert expected in run_action(slot="KV-10482")


def test_action_handles_invalid_backend_json(monkeypatch):
    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            raise ValueError("invalid JSON")

    monkeypatch.setattr(actions.requests, "get", lambda *args, **kwargs: Response())
    assert "ongeldige gegevens" in run_action(slot="KV-10482")


def test_helper_fallbacks_and_rest_channel_file():
    assert actions.format_bool_or_text(None) == "onbekend"
    assert actions.format_bool_or_text(False) == "nee"
    assert actions.summarize_items({}) == "Geen artikelinformatie beschikbaar."
    assert "medewerkerhulp" in actions.build_customer_facing_advice({"handoff_reason": "controle"})
    assert Path("credentials.yml").read_text(encoding="utf-8").strip() == "rest:"

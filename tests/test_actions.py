"""Exercise action logic without requiring a licensed Rasa runtime in CI."""
import importlib.util
import sys
import types
from pathlib import Path

import pytest
import requests
import mock_backend


@pytest.fixture
def actions_module(monkeypatch):
    sdk = types.ModuleType("rasa_sdk")
    sdk.Action = type("Action", (), {})
    sdk.Tracker = type("Tracker", (), {})
    executor = types.ModuleType("rasa_sdk.executor")
    executor.CollectingDispatcher = type("CollectingDispatcher", (), {})
    monkeypatch.setitem(sys.modules, "rasa_sdk", sdk)
    monkeypatch.setitem(sys.modules, "rasa_sdk.executor", executor)
    spec = importlib.util.spec_from_file_location("test_rasa_actions", Path("actions/actions.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Tracker:
    sender_id = "test_sender"
    latest_message = {"text": "KV-10482"}

    def get_slot(self, name):
        return "KV-10482" if name == "order_id" else None


class Dispatcher:
    def __init__(self):
        self.messages = []

    def utter_message(self, text, **kwargs):
        self.messages.append(text)


class Response:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status_code = status

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError()


def test_missing_action_fetches_order_and_creates_case(actions_module, monkeypatch):
    monkeypatch.setattr(actions_module, "OPS_TOKEN", "test-token")
    monkeypatch.setattr(actions_module.requests, "get", lambda *args, **kwargs: Response(mock_backend.MOCK_ORDERS["KV-10482"]))
    calls = []
    def post(*args, **kwargs):
        calls.append(kwargs["json"])
        return Response({"id": 42})
    monkeypatch.setattr(actions_module.requests, "post", post)
    dispatcher = Dispatcher()
    assert actions_module.ActionCheckMissingItem().run(dispatcher, Tracker(), {}) == []
    assert "Demonstratiecase #42" in dispatcher.messages[0]
    assert calls[0]["issue"] == "missing"
    assert calls[0]["order_id"] == "KV-10482"


@pytest.mark.parametrize("failure,expected", [
    (requests.exceptions.Timeout(), "te langzaam"),
    (Response({"order_id": "wrong", "items": []}), "niet betrouwbaar"),
    (Response({}, 404), "niet gevonden"),
])
def test_action_failure_paths(actions_module, monkeypatch, failure, expected):
    def get(*args, **kwargs):
        if isinstance(failure, Exception):
            raise failure
        return failure
    monkeypatch.setattr(actions_module.requests, "get", get)
    dispatcher = Dispatcher()
    actions_module.ActionCheckOrderContext().run(dispatcher, Tracker(), {})
    assert expected in dispatcher.messages[0]


def test_case_failure_is_not_reported_as_success(actions_module, monkeypatch):
    monkeypatch.setattr(actions_module, "OPS_TOKEN", "")
    dispatcher = Dispatcher()
    actions_module.ActionCreateSupportCase().run(dispatcher, Tracker(), {})
    assert "geen demonstratiecase" in dispatcher.messages[0]

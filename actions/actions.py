"""Rasa SDK actions for the optional, licensed conversation path."""
import os
import re
from typing import Any, Dict, List, Text

import requests
from pydantic import ValidationError
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from support.models import Order
from support.policy import advice

RETAIL_API_URL = os.getenv("RETAIL_API_URL", "http://localhost:8001").rstrip("/")
OPS_TOKEN = os.getenv("SUPPORT_OPS_TOKEN", "")
ORDER_PATTERN = re.compile(r"\bKV-\d{5}\b", re.IGNORECASE)


def _order_id(tracker: Tracker) -> str | None:
    candidate = str(tracker.get_slot("order_id") or tracker.latest_message.get("text", ""))
    match = ORDER_PATTERN.search(candidate)
    return match.group().upper() if match else None


def _create_case(tracker: Tracker, issue: str, reason: str, order_id: str | None, summary: str) -> int | None:
    if not OPS_TOKEN:
        return None
    try:
        response = requests.post(
            f"{RETAIL_API_URL}/internal/cases",
            json={"session_id": tracker.sender_id, "issue": issue, "reason": reason, "order_id": order_id, "summary": summary[:1000]},
            headers={"X-Support-Token": OPS_TOKEN}, timeout=5,
        )
        response.raise_for_status()
        return int(response.json()["id"])
    except (requests.exceptions.RequestException, ValueError, KeyError, TypeError):
        return None


def _run_order(issue: str, dispatcher: CollectingDispatcher, tracker: Tracker) -> List[Dict[Text, Any]]:
    order_id = _order_id(tracker)
    if not order_id:
        dispatcher.utter_message(text="Ik heb een voorbeeldordernummer nodig, zoals KV-10482.")
        return []
    try:
        response = requests.get(f"{RETAIL_API_URL}/orders/{order_id}", timeout=5)
        if response.status_code == 404:
            dispatcher.utter_message(text=f"Voorbeeldorder {order_id} is niet gevonden. Controleer het nummer.")
            return []
        response.raise_for_status()
        order = Order.model_validate(response.json())
        if order.order_id != order_id:
            raise ValueError("Order ID mismatch")
    except requests.exceptions.Timeout:
        dispatcher.utter_message(text="Het voorbeeldordersysteem reageert te langzaam. Probeer het opnieuw.")
        return []
    except (requests.exceptions.RequestException, ValidationError, ValueError, TypeError):
        dispatcher.utter_message(text="Ik kan de voorbeeldorder nu niet betrouwbaar lezen. Probeer later opnieuw of vraag om hulp.")
        return []

    message, handoff, reason = advice(order, issue)  # same policy function as public demo
    items = "; ".join(f"{item.name} ({item.quantity_delivered}/{item.quantity_ordered} geleverd)" for item in order.items)
    response_text = f"Voorbeeldorder {order_id}: {order.status}. Bezorging: {order.delivery_status}. Artikelen: {items}. {message}"
    case_id = None
    if handoff:
        case_id = _create_case(tracker, issue, reason, order_id, f"Rasa-gesprek over {order_id}: {message}")
        response_text += f" Demonstratiecase #{case_id} is opgeslagen." if case_id else " Ik kon geen demonstratiecase opslaan; neem zelf contact op als je hulp nodig hebt."
    dispatcher.utter_message(text=response_text, json_message={"order": order.model_dump(), "case_id": case_id})
    return []


class ActionCheckOrderContext(Action):
    def name(self) -> Text:
        return "action_check_order_context"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return _run_order("order", dispatcher, tracker)


class ActionCheckMissingItem(Action):
    def name(self) -> Text:
        return "action_check_missing_item"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return _run_order("missing", dispatcher, tracker)


class ActionCheckDamagedProduct(Action):
    def name(self) -> Text:
        return "action_check_damaged_product"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return _run_order("damaged", dispatcher, tracker)


class ActionCheckReturn(Action):
    def name(self) -> Text:
        return "action_check_return"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return _run_order("return", dispatcher, tracker)


class ActionCheckRefund(Action):
    def name(self) -> Text:
        return "action_check_refund"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return _run_order("refund", dispatcher, tracker)


class ActionCheckPartner(Action):
    def name(self) -> Text:
        return "action_check_partner"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return _run_order("partner", dispatcher, tracker)


class ActionCreateSupportCase(Action):
    def name(self) -> Text:
        return "action_create_support_case"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        case_id = _create_case(tracker, "human", "Klant vraagt om menselijke beoordeling", _order_id(tracker), f"Rasa-gesprek: {tracker.latest_message.get('text', '')[:300]}")
        if case_id:
            dispatcher.utter_message(text=f"Demonstratiecase #{case_id} is opgeslagen. Dit is geen overdracht naar de echte Kruidvat klantenservice.", json_message={"case_id": case_id})
        else:
            dispatcher.utter_message(text="Ik kan nu geen demonstratiecase opslaan. Probeer later opnieuw.")
        return []

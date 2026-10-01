import re
from typing import Any, Dict, List, Optional, Text

import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

MOCK_BACKEND_URL = "http://localhost:8001"


def extract_order_id(text: str) -> Optional[str]:
    match = re.search(r"\bKV-\d{5}\b", text.upper())
    if match:
        return match.group(0)
    return None


def format_bool_or_text(value: Any) -> str:
    if value is True:
        return "ja"
    if value is False:
        return "nee"
    if value is None:
        return "onbekend"
    return str(value)


def summarize_items(order: Dict[str, Any]) -> str:
    items = order.get("items", [])
    if not items:
        return "Geen artikelinformatie beschikbaar."

    item_lines = []
    for item in items:
        name = item.get("name", "Onbekend artikel")
        ordered = item.get("quantity_ordered", "?")
        delivered = item.get("quantity_delivered", "?")
        condition = item.get("condition", "onbekend")
        item_lines.append(
            f"- {name}: besteld {ordered}, geleverd {delivered}, status: {condition}"
        )

    return "\n".join(item_lines)


def build_customer_facing_advice(order: Dict[str, Any]) -> str:
    issue_type = (order.get("issue_type") or "").lower()
    missing_item_status = order.get("missing_item_status")
    damaged_item_case = order.get("damaged_item_case")
    partner_order = order.get("partner_order")
    handoff_reason = order.get("handoff_reason")
    recommended_next_step = order.get("recommended_next_step", "")

    if "ontbrekend" in issue_type or missing_item_status:
        return (
            "Ik zie dat deze bestelling een ontbrekend-artikel situatie lijkt te hebben. "
            "Bewaar de verpakking en pakbon nog even. Omdat dit gecontroleerd moet worden "
            "tegen de order- en verzendgegevens, is medewerkerhulp de juiste volgende stap."
        )

    if "beschadigd" in issue_type or damaged_item_case:
        return (
            "Ik zie dat dit om een beschadigd artikel lijkt te gaan. Bewaar het artikel en de verpakking, "
            "en maak indien mogelijk duidelijke foto’s van de schade. Een medewerker kan dit daarna beoordelen "
            "voor een passende oplossing, zoals vervanging of terugbetaling."
        )

    if partner_order is True:
        return (
            "Ik zie dat dit een partnerartikel lijkt te zijn. Bij partnerartikelen kunnen retour- of "
            "beoordelingsstappen anders verlopen dan bij gewone Kruidvat-artikelen. Een medewerker kan je "
            "met deze partnercontext gerichter verder helpen."
        )

    if handoff_reason:
        return (
            f"Deze situatie vraagt waarschijnlijk om medewerkerhulp: {handoff_reason} "
            "Ik kan de belangrijkste context alvast verzamelen zodat de overdracht duidelijker is."
        )

    return recommended_next_step or (
        "Ik heb de ordercontext gevonden. Voor een order-specifieke beoordeling kan een medewerker verder meekijken."
    )


class ActionCheckOrderContext(Action):
    def name(self) -> Text:
        return "action_check_order_context"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        latest_text = tracker.latest_message.get("text") or ""
        slot_order_id = str(tracker.get_slot("order_id") or "").strip().upper()
        order_id = slot_order_id if re.fullmatch(r"KV-\d{5}", slot_order_id) else extract_order_id(latest_text)

        if not order_id:
            dispatcher.utter_message(
                text=(
                    "Ik kan de bestelling controleren als je een ordernummer geeft, "
                    "bijvoorbeeld KV-10482, KV-20991 of KV-77830."
                )
            )
            return []

        try:
            response = requests.get(f"{MOCK_BACKEND_URL}/orders/{order_id}", timeout=5)
            response.raise_for_status()
            order = response.json()

        except requests.exceptions.ConnectionError:
            dispatcher.utter_message(
                text=(
                    "Ik kan het ordersysteem op dit moment niet bereiken. "
                    "Probeer het later opnieuw of neem contact op met een medewerker."
                )
            )
            return []

        except requests.exceptions.HTTPError as exc:
            if getattr(getattr(exc, "response", None), "status_code", None) == 404:
                message = (
                    f"Ik kon order {order_id} niet vinden. Controleer het ordernummer "
                    "of neem contact op met een medewerker."
                )
            else:
                message = "Het ordersysteem gaf een fout. Probeer het later opnieuw of neem contact op met een medewerker."
            dispatcher.utter_message(text=message)
            return []

        except requests.exceptions.Timeout:
            dispatcher.utter_message(
                text="Het ordersysteem reageert op dit moment te langzaam. Probeer het zo opnieuw."
            )
            return []

        except requests.exceptions.RequestException:
            dispatcher.utter_message(
                text=(
                    "Er ging iets mis bij het ophalen van de orderinformatie. "
                    "Probeer het later opnieuw of neem contact op met een medewerker."
                )
            )
            return []

        except ValueError:
            dispatcher.utter_message(
                text="Het ordersysteem gaf ongeldige gegevens terug. Neem contact op met een medewerker."
            )
            return []

        items_summary = summarize_items(order)
        advice = build_customer_facing_advice(order)

        partner_text = "ja" if order.get("partner_order") is True else "nee"
        missing_text = order.get("missing_item_status") or "geen ontbrekend artikel bekend"
        damaged_text = order.get("damaged_item_case") or "geen schadecase bekend"

        dispatcher.utter_message(
            text=(
                f"Ik heb order {order_id} gecontroleerd.\n\n"
                f"Status: {order.get('status', 'onbekend')}.\n"
                f"Bezorgstatus: {order.get('delivery_status', 'onbekend')}.\n"
                f"Bezorgdatum: {order.get('delivery_date', 'onbekend')}.\n"
                f"Type issue: {order.get('issue_type', 'onbekend')}.\n"
                f"Partnerorder: {partner_text}.\n"
                f"Retour mogelijk: {format_bool_or_text(order.get('return_eligible'))}.\n"
                f"Terugbetaling: {order.get('refund_status', 'onbekend')}.\n"
                f"Ontbrekend artikel: {missing_text}.\n"
                f"Beschadigd artikel: {damaged_text}.\n\n"
                f"Artikeloverzicht:\n{items_summary}\n\n"
                f"Advies: {advice}"
            )
        )

        return []

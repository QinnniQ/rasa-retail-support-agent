import os
import sqlite3
from pathlib import Path

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from support.models import CaseCreate, CaseUpdate, ChatRequest, ChatResponse, Order, TraceStep, Issue
from pydantic import BaseModel
from support.policy import advice, classify, extract_order_id
from support.store import Store

app = FastAPI(
    title="Kruidvat Support Backend",
    description="Example backend API for the Kruidvat Rasa support-agent prototype.",
    version="0.1.0",
)

STORE = Store(os.getenv("SUPPORT_DB_PATH", str(Path("data") / "support.db")))
MODE = os.getenv("SUPPORT_MODE", "demo").lower()
if MODE not in {"demo", "rasa"}:
    raise RuntimeError("SUPPORT_MODE must be demo or rasa")
RASA_URL = os.getenv("RASA_URL", "http://localhost:5005").rstrip("/")

MOCK_ORDERS = {
    "KV-10482": {
        "order_id": "KV-10482",
        "customer_name": "Voorbeeld klant",
        "status": "gedeeltelijk geleverd",
        "delivery_status": "bezorgd volgens vervoerder",
        "delivery_date": "2026-06-08",
        "issue_type": "ontbrekend artikel",
        "missing_item_status": "artikel ontbreekt in geleverd pakket",
        "damaged_item_case": None,
        "partner_order": False,
        "return_eligible": True,
        "refund_status": "nog niet gestart",
        "kruidvat_club_context": "Klant is ingelogd met Kruidvat Club-account.",
        "items": [
            {
                "name": "Kruidvat Vitamine D tabletten",
                "quantity_ordered": 1,
                "quantity_delivered": 1,
                "condition": "geleverd",
            },
            {
                "name": "Kruidvat dagcrème sensitive",
                "quantity_ordered": 1,
                "quantity_delivered": 0,
                "condition": "ontbreekt",
            },
        ],
        "recommended_next_step": (
            "Leg uit dat één artikel lijkt te ontbreken. Adviseer de klant om de verpakking "
            "en pakbon te bewaren. Zet de case door naar een medewerker voor controle en mogelijke nalevering of terugbetaling."
        ),
        "handoff_reason": (
            "Ontbrekend artikel vereist ordercontrole en mogelijk magazijn-/verzendonderzoek."
        ),
    },
    "KV-20991": {
        "order_id": "KV-20991",
        "customer_name": "Voorbeeld klant",
        "status": "bezorgd",
        "delivery_status": "bezorgd",
        "delivery_date": "2026-06-09",
        "issue_type": "beschadigd artikel",
        "missing_item_status": None,
        "damaged_item_case": "artikel beschadigd aangekomen",
        "partner_order": False,
        "return_eligible": True,
        "refund_status": "nog niet gestart",
        "kruidvat_club_context": "Geen bijzonderheden bekend.",
        "items": [
            {
                "name": "Kruidvat shampoo voordeelverpakking",
                "quantity_ordered": 1,
                "quantity_delivered": 1,
                "condition": "beschadigd aangekomen",
            }
        ],
        "recommended_next_step": (
            "Vraag de klant om foto’s van het beschadigde artikel en de verpakking te bewaren. "
            "Zet de case door naar een medewerker voor beoordeling van vervanging of terugbetaling."
        ),
        "handoff_reason": (
            "Beschadigd artikel vraagt om beoordeling en eventueel bewijs zoals foto’s."
        ),
    },
    "KV-77830": {
        "order_id": "KV-77830",
        "customer_name": "Voorbeeld klant",
        "status": "bezorgd",
        "delivery_status": "bezorgd",
        "delivery_date": "2026-06-05",
        "issue_type": "partner retourvraag",
        "missing_item_status": None,
        "damaged_item_case": None,
        "partner_order": True,
        "partner_name": "Externe verkooppartner",
        "return_eligible": "afhankelijk van partnervoorwaarden",
        "refund_status": "niet gestart",
        "kruidvat_club_context": "Order zichtbaar in account, maar retour loopt via partnerproces.",
        "items": [
            {
                "name": "Elektrische tandenborstel partnerartikel",
                "quantity_ordered": 1,
                "quantity_delivered": 1,
                "condition": "geleverd",
            }
        ],
        "recommended_next_step": (
            "Leg uit dat dit een partnerartikel is. Retour of beoordeling loopt waarschijnlijk via "
            "de partnerprocedure. Zet de klant door naar een medewerker met ordernummer en partnercontext."
        ),
        "handoff_reason": (
            "Partnerorder vereist specifieke retourinstructies en mogelijk communicatie met externe verkoper."
        ),
    },
}

MOCK_ORDERS.update({
    "KV-30014": {"order_id": "KV-30014", "status": "vertraagd", "delivery_status": "onderweg", "delivery_date": None, "partner_order": False, "return_eligible": None, "refund_status": "niet gestart", "items": [{"name": "Handcrème", "quantity_ordered": 1, "quantity_delivered": 0, "condition": "onderweg"}]},
    "KV-40025": {"order_id": "KV-40025", "status": "deellevering", "delivery_status": "tweede pakket onderweg", "delivery_date": None, "partner_order": False, "return_eligible": True, "refund_status": "niet gestart", "items": [{"name": "Shampoo", "quantity_ordered": 2, "quantity_delivered": 1, "condition": "gesplitste levering"}]},
    "KV-50036": {"order_id": "KV-50036", "status": "geretourneerd", "delivery_status": "afgerond", "delivery_date": "2026-06-02", "partner_order": False, "return_eligible": True, "refund_status": "afgerond in simulatie", "items": [{"name": "Make-uptas", "quantity_ordered": 1, "quantity_delivered": 1, "condition": "geretourneerd"}]},
    "KV-60047": {"order_id": "KV-60047", "status": "bezorgd", "delivery_status": "bezorgd", "delivery_date": "2026-06-11", "partner_order": False, "return_eligible": False, "refund_status": "niet gestart", "items": [{"name": "Verzegeld verzorgingsproduct", "quantity_ordered": 1, "quantity_delivered": 1, "condition": "verzegeling geopend"}]},
    "KV-70058": {"order_id": "KV-70058", "status": "retour in verwerking", "delivery_status": "retour ontvangen", "delivery_date": "2026-06-07", "partner_order": False, "return_eligible": True, "refund_status": "in behandeling; geen datum bevestigd", "items": [{"name": "Badhanddoek", "quantity_ordered": 1, "quantity_delivered": 1, "condition": "retour ontvangen"}]},
})


def require_ops(x_support_token: str | None = Header(default=None)):
    token = os.getenv("SUPPORT_OPS_TOKEN")
    if not token:
        raise HTTPException(503, "Operations access is not configured")
    if x_support_token != token:
        raise HTTPException(401, "Operations token required")


class EvaluationRequest(BaseModel):
    order_id: str
    issue: Issue


@app.post("/internal/evaluate", dependencies=[Depends(require_ops)])
def evaluate(request: EvaluationRequest):
    order = MOCK_ORDERS.get(request.order_id.upper())
    if not order:
        raise HTTPException(404, "Order not found")
    message, handoff, reason = advice(Order.model_validate(order), request.issue)
    return {"message": message, "handoff": handoff, "reason": reason}


@app.post("/internal/cases", dependencies=[Depends(require_ops)])
def create_internal_case(case: CaseCreate):
    return STORE.create_case(case)


@app.get("/health")
def health():
    return {"status": "ok", "mode": MODE, "retail_api": "ok", "rasa": "not_checked"}


@app.get("/api/status")
async def status():
    rasa_status = "not_configured" if MODE != "rasa" else "unavailable"
    if MODE == "rasa":
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                result = await client.get(f"{RASA_URL}/status")
                rasa_status = "ok" if result.is_success else "unavailable"
        except httpx.HTTPError:
            pass
    try:
        with STORE.connection() as db:
            db.execute("SELECT 1 FROM cases LIMIT 1").fetchone()
        case_store = "ok"
    except sqlite3.Error:
        case_store = "unavailable"
    return {"mode": MODE, "retail_api": "ok", "rasa": rasa_status, "case_store": case_store}


@app.get("/api/examples")
def examples():
    return [{"order_id": key, "status": value["status"], "issue_type": value.get("issue_type") or "voorbeeldscenario"} for key, value in MOCK_ORDERS.items()]


async def send_to_rasa(session_id: str, message: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=10) as client:
        result = await client.post(f"{RASA_URL}/webhooks/rest/webhook", json={"sender": session_id, "message": message})
        result.raise_for_status()
        payload = result.json()
    if not isinstance(payload, list):
        raise ValueError("Invalid Rasa response")
    return payload


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session = STORE.session(request.session_id)
    issue = request.category or classify(request.message) or session["issue"]
    order_id = extract_order_id(request.message) or session["order_id"]
    trace = [TraceStep(step="message", detail="Bericht ontvangen en gevalideerd")]
    if MODE == "rasa":
        try:
            payload = await send_to_rasa(request.session_id, request.message)
            messages = [part["text"] for part in payload if isinstance(part, dict) and isinstance(part.get("text"), str)]
            if not messages:
                messages = ["De Rasa-server gaf geen tekst terug. Probeer je vraag anders te formuleren."]
            trace.append(TraceStep(step="rasa", detail="Antwoord ontvangen via REST-kanaal; interne Rasa-acties niet zichtbaar in deze trace"))
        except (httpx.HTTPError, ValueError, TypeError):
            raise HTTPException(503, "Rasa is momenteel niet bereikbaar. Probeer het later opnieuw.")
        custom = next((part.get("custom") for part in payload if isinstance(part, dict) and isinstance(part.get("custom"), dict) and ("order" in part["custom"] or "case_id" in part["custom"])), {})
        try:
            order = Order.model_validate(custom["order"]) if custom.get("order") else None
        except (ValueError, TypeError):
            order = None
        case_id = custom.get("case_id") if isinstance(custom.get("case_id"), int) else None
        session.update(issue=issue, order_id=order_id)
        STORE.save_session(session, request.message, " ".join(messages))
        return ChatResponse(messages=messages, mode="rasa", order=order, case_id=case_id, trace=trace)

    trace.append(TraceStep(step="routing", detail=f"Deterministische demo-classificatie: {issue or 'onbekend'}"))
    if not issue and not order_id:
        answer = "Ik kan helpen met bestellingen, ontbrekende of beschadigde artikelen, retouren en terugbetalingen. Kies een onderwerp of geef een voorbeeldordernummer."
        replies = ["Bestelling volgen", "Artikel ontbreekt", "Retourneren"]
    elif not order_id and issue != "human":
        answer = "Wat is je voorbeeldordernummer? Gebruik bijvoorbeeld KV-10482, KV-20991 of KV-77830."
        replies = ["KV-10482", "KV-20991", "KV-77830"]
        trace.append(TraceStep(step="slot", detail="Wacht op voorbeeldordernummer"))
    elif order_id and order_id not in MOCK_ORDERS:
        answer = f"Ik kan {order_id} niet vinden in de fictieve voorbeeldorders. Controleer het nummer of probeer KV-10482."
        replies = ["KV-10482", "Contact met medewerker"]
        order_id = None
        trace.append(TraceStep(step="lookup", detail="Order niet gevonden"))
    else:
        replies = ["Contact met medewerker", "Andere vraag"]
        order = Order.model_validate(MOCK_ORDERS[order_id]) if order_id else None
        trace.append(TraceStep(step="lookup", detail=f"Fictieve order {order_id} opgehaald" if order else "Geen order gekoppeld"))
        answer, handoff, reason = advice(order, issue or "order") if order else ("Ik kan een demonstratiecase voor een medewerker aanmaken. Beschrijf zo nodig je probleem en geef een voorbeeldordernummer.", True, "Klant vraagt om ondersteuning")
        if order:
            trace.append(TraceStep(step="policy", detail=f"Demo-regel voor {issue or 'order'} geëvalueerd; handoff={handoff}"))
        case_id = None
        if handoff:
            existing = [case for case in STORE.cases() if case["session_id"] == request.session_id and case["status"] != "resolved" and case["issue"] == (issue or "human") and case["order_id"] == order_id]
            case = existing[0] if existing else STORE.create_case(CaseCreate(session_id=request.session_id, issue=issue or "human", reason=reason, order_id=order_id, summary=f"Klantvraag: {request.message[:300]}. Advies: {answer[:500]}"))
            case_id = case["id"]
            answer += f" Demonstratiecase #{case_id} is aangemaakt voor opvolging."
            trace.append(TraceStep(step="handoff", detail=f"Case #{case_id} opgeslagen"))
        session.update(issue=issue, order_id=order_id)
        STORE.save_session(session, request.message, answer)
        return ChatResponse(messages=[answer], mode="demo", order=order, case_id=case_id, quick_replies=replies, trace=trace)
    session.update(issue=issue, order_id=order_id)
    STORE.save_session(session, request.message, answer)
    return ChatResponse(messages=[answer], mode="demo", quick_replies=replies, trace=trace)


@app.get("/api/cases", dependencies=[Depends(require_ops)])
def list_cases(status: str | None = None):
    if status and status not in {"open", "investigating", "resolved"}:
        raise HTTPException(422, "Invalid case status")
    return STORE.cases(status)


@app.patch("/api/cases/{case_id}", dependencies=[Depends(require_ops)])
def update_case(case_id: int, update: CaseUpdate):
    case = STORE.update_case(case_id, update)
    if not case:
        raise HTTPException(404, "Case not found")
    return case


@app.get("/")
def root():
    return {
        "message": "Kruidvat support backend is running",
        "available_example_orders": list(MOCK_ORDERS.keys()),
    }


@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    order_id = order_id.upper()

    if not extract_order_id(order_id) or len(order_id) != 8:
        raise HTTPException(status_code=422, detail="Invalid order ID")

    if order_id not in MOCK_ORDERS:
        raise HTTPException(status_code=404, detail=f"Order {order_id} niet gevonden.")

    return MOCK_ORDERS[order_id]

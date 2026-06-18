from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="Kruidvat Support Backend",
    description="Example backend API for the Kruidvat Rasa support-agent prototype.",
    version="0.1.0",
)

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


@app.get("/")
def root():
    return {
        "message": "Kruidvat support backend is running",
        "available_example_orders": list(MOCK_ORDERS.keys()),
    }


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    order_id = order_id.upper()

    if order_id not in MOCK_ORDERS:
        raise HTTPException(status_code=404, detail=f"Order {order_id} niet gevonden.")

    return MOCK_ORDERS[order_id]
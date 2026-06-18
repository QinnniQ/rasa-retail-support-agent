# Retail Support AgentOps — Rasa Customer-Service Automation

A Rasa-based customer-service automation prototype for Dutch retail webshop support.

This project demonstrates how a retail chatbot can move beyond static FAQ responses toward structured, order-aware, and inspectable support automation. The prototype focuses on high-volume customer-service scenarios such as missing items, damaged products, returns, delivery issues, partner orders, refund status, and smarter handoff to human support.

> This is an independent portfolio project inspired by common Dutch retail webshop support flows. It is not an official Kruidvat, HEMA, or AS Watson product.

---

## Why this project matters

Many retail chatbots can answer general customer-service questions, but more complex webshop cases often require order-specific context.

This prototype explores the next layer of support automation:

* collecting the right information from the customer,
* retrieving structured order context from a backend service,
* identifying whether the issue involves a missing item, damaged product, partner order, refund, or delivery problem,
* providing clearer customer guidance,
* and preparing a more useful handoff when a human medewerker is needed.

The goal is not to replace human support. The goal is to reduce avoidable support load and make escalations more informed.

---

## Core use case

A customer reports a missing item:

```text
Er ontbreekt een artikel in mijn bestelling. Wat nu?
```

The assistant gives initial guidance and then supports an order-aware lookup:

```text
Ik wil mijn bestelling controleren
Mijn ordernummer is KV-10482
```

The system retrieves example order data from a FastAPI backend and returns context such as:

* order status,
* delivery status,
* missing item details,
* refund status,
* item overview,
* partner-order flag,
* recommended next step,
* and handoff reason.

---

## Key features

* **Rasa conversational agent** with structured Dutch support flows
* **Flow-based order lookup** using slot collection for `order_id`
* **Custom Rasa actions** for backend API calls
* **FastAPI mock backend** simulating order context
* **Streamlit demo UI** for a customer-facing retail support experience
* **Rasa Inspector compatibility** for traceable agent behavior
* **Dutch retail CX scenarios** including missing items, damaged products, returns, delivery issues, partner-order nuance, and human handoff

---

## Architecture

```text
Customer
   ↓
Streamlit Chat UI
   ↓
Rasa REST Channel
   ↓
Rasa Flow / NLU / Rules
   ↓
Custom Action: action_check_order_context
   ↓
FastAPI Mock Backend
   ↓
Order-aware response
```

---

## Tech stack

* Python
* Rasa Pro
* Rasa SDK
* FastAPI
* Streamlit
* Requests
* Uvicorn
* YAML-based Rasa domain, rules, stories, NLU, and flows

---

## Example demo orders

The mock backend includes three example orders:

| Order ID   | Scenario      | Purpose                                                 |
| ---------- | ------------- | ------------------------------------------------------- |
| `KV-10482` | Missing item  | Demonstrates incomplete delivery and handoff reasoning  |
| `KV-20991` | Damaged item  | Demonstrates damage guidance and review escalation      |
| `KV-77830` | Partner order | Demonstrates partner-order nuance and return complexity |

---

## Demo flow

Recommended primary demo:

```text
Er ontbreekt een artikel in mijn bestelling. Wat nu?
```

```text
Ik wil mijn bestelling controleren
```

```text
Mijn ordernummer is KV-10482
```

Optional damaged-item demo:

```text
Mijn artikel is beschadigd aangekomen. Wat moet ik doen?
```

```text
Ik wil mijn bestelling controleren
```

```text
Mijn ordernummer is KV-20991
```

Optional partner-order demo:

```text
Hoe retourneer ik een partnerartikel?
```

```text
Ik wil mijn bestelling controleren
```

```text
Mijn ordernummer is KV-77830
```

---

## Project structure

```text
rasa-retail-support-agent/
│
├── app.py                  # Streamlit customer-facing demo UI
├── mock_backend.py          # FastAPI mock order backend
├── config.yml               # Rasa pipeline and policies
├── domain.yml               # Intents, slots, responses, actions
├── endpoints.yml            # Rasa action server endpoint
├── credentials.yml          # Rasa channel configuration
│
├── actions/
│   └── actions.py           # Custom Rasa backend lookup action
│
├── data/
│   ├── nlu.yml              # Dutch NLU examples and order regex
│   ├── rules.yml            # Rule-based support responses
│   ├── stories.yml          # Example conversation paths
│   └── flows.yml            # Order context lookup flow
│
├── screenshots/             # Optional: demo and Inspector screenshots
│   
│   
│
└── README.md
```

---

## Running locally

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install rasa-pro rasa-sdk fastapi uvicorn requests streamlit
```

> Depending on your Rasa license/setup, you may need to install the appropriate Rasa package available to you.

### 3. Train the Rasa assistant

```powershell
rasa train
```

### 4. Start the mock backend

```powershell
python -m uvicorn mock_backend:app --reload --port 8001
```

### 5. Start the Rasa action server

Open a second terminal:

```powershell
.\.venv\Scripts\Activate.ps1
rasa run actions
```

### 6. Start the Rasa server

Open a third terminal:

```powershell
.\.venv\Scripts\Activate.ps1
rasa run --enable-api --cors "*" --port 5005
```

### 7. Start the Streamlit UI

Open a fourth terminal:

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

---

## Rasa Inspector

To inspect the assistant behavior under the hood:

```powershell
rasa inspect --nextgen
```

The Inspector view can show:

* active flow,
* slot collection,
* order ID handling,
* custom action execution,
* and flow completion.

This is useful for demonstrating that the assistant is not a black-box chatbot, but a structured and traceable support workflow.

---

## Portfolio value

This project demonstrates practical skills in:

* conversational AI design,
* Rasa flow development,
* custom action engineering,
* backend API integration,
* customer-service automation,
* Streamlit interface design,
* support workflow modeling,
* and business-facing AI prototyping.

---

## Disclaimer

This project uses simulated order data and mock backend services. It does not connect to real customer accounts, retailer systems, or private order data.

Brand references are used only to demonstrate realistic retail support scenarios in an independent portfolio prototype.

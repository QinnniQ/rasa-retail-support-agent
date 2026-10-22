# Five-minute live demo (public mode)

Prerequisite: run the API and frontend as in the README. Set `SUPPORT_OPS_TOKEN` and keep it available locally. The outputs below were checked against the implemented 22 October 2026 demo.

| Time | Action | What to say and expect |
| --- | --- | --- |
| 0:00–0:40 | Open the homepage. | “This is an independent Kruidvat-inspired demonstration with fictional data. The problem is moving beyond FAQs to order-aware support.” |
| 0:40–1:35 | Select **Ontbrekend artikel**. | The assistant asks for a sample order number. Enter `KV-10482`. The order card shows two articles, one delivered `0/1`, and a case number. |
| 1:35–2:15 | Open `/orders/KV-10482` on the local API or its `/docs` page. | Show that the order card came from typed backend data. The policy detects the quantity mismatch and requests human investigation. |
| 2:15–3:00 | Open **Support Operations**, enter the local token, select the new case. | The case has an order ID, summary, reason, and `open` status. Change to `investigating` and refresh to show persistence. This is a simulated assignment space. |
| 3:00–3:50 | Open **Architectuur**. | Show actual service status and explain `demo` versus licensed `rasa` mode. The trace is labeled simulated. In Rasa mode the gateway only sees the REST response. |
| 3:50–4:35 | Mention `python -m pytest -q`, `python -m evaluation.run`, and `npm run build`. | Fourteen Python tests, fourteen authored journeys, and four browser tests passed locally. These do not show broad language accuracy or customer impact. |
| 4:35–5:00 | Close. | “For a real pilot, I would validate retailer APIs and policy, add identity and privacy controls, then measure task completion and handoff quality with agents.” |

Fallback if a service is down: show `support/policy.py`, `support/store.py`, and `evaluation/cases.json`. Do not pretend a failed live call succeeded.

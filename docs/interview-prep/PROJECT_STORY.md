# Project story

These scripts separate the 2026 collaboration/prototype context from later independent portfolio engineering. Confirm personal contribution details before using them as first-person claims.

## 30 seconds

“This is an independent retail support demo built from an earlier Rasa prototype. A customer can describe a missing or damaged item, provide a fictional order number, get structured guidance, and have the issue recorded as a case for human review. I later rebuilt the interface in React and added a public mode so interviewers can try it without a Rasa Pro license. It shows how I connect a customer-service problem to practical software boundaries.”

## Two minutes

“Retail support is more than answering FAQs. To answer an order question well, an assistant needs an identifier, a reliable order source, explicit business rules, and a route to a person when the data is uncertain. The original 2026 collaboration explored this with Rasa flows, a Python custom action, a mock order API, and Streamlit. My later independent portfolio work added a React experience, persistent sessions and cases, a deterministic public demo adapter, tests, and an engineering explorer.

In demo mode, the frontend calls FastAPI. FastAPI tracks the issue and example order ID, reads fictional order data, evaluates a small policy function, and returns a typed order card plus guidance. Missing and damaged items create a SQLite case. In a licensed setup, the same frontend can send messages through a Rasa REST adapter. I keep those modes clearly labeled because a public demo is not proof that Rasa is running. The business potential is more consistent self-service and a better handoff, but I have not measured a production outcome.”

## Five minutes

Start with `KV-10482`. Explain why a generic FAQ cannot tell whether an item was delivered. Show a missing-item conversation: the assistant asks for an order number, retrieves two item records, sees one quantity mismatch, and creates a case. Open Support Operations and show its reason, order link, status, and assignment. Point to `support/policy.py` for the rule, `support/store.py` for SQLite persistence, and `actions/actions.py` for the retained Rasa action path.

Describe the main tradeoff: the public mode is immediately reproducible and deterministic, but it handles limited phrasing. The genuine mode requires a licensed Rasa Pro runtime and further version-specific validation. Explain why business decisions are explicit Python rules rather than improvised text. Mention the observed frontend effect bug and local asyncio sandbox issue in `FAILURE_STORIES.md`. Close with the next engineering step: identity, retailer API access, approved policy sources, privacy controls, and a measured pilot with human reviewers. Do not claim this has served real Kruidvat customers.

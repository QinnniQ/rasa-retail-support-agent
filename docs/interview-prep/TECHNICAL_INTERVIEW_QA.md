# Technical interview questions

The answers distinguish this application's actual behavior from general AI/ML concepts. Practice them aloud and adapt wording to your own contribution.

1. **What problem does this solve?** A retail question often needs order facts, not an FAQ paragraph. The demo collects context, checks a fictional order, applies a rule, and records cases for human review.
2. **Is this an official Kruidvat service?** No. It is an independent portfolio simulation using only invented data.
3. **What is Rasa's role?** In licensed mode Rasa manages dialogue, slot collection, and custom-action calls. Public mode uses a separate deterministic adapter.
4. **Is a trained model running in public mode?** No. `support/policy.py` uses explicit Dutch phrase matching and business rules.
5. **How does intent recognition work here?** Demo mode checks ordered keyword groups. The retained Rasa configuration uses a keyword classifier and NLU command adapter, but training was not verified in this environment.
6. **What is NLU?** It maps user language to structured meaning such as an intent and entities. It does not itself decide return eligibility.
7. **What is dialogue management?** It decides which question or action follows from conversation state. Rasa flows and the demo session state each do this in different modes.
8. **What is business logic?** Explicit rules over order fields, such as whether a missing item is actually in a second parcel.
9. **What is a slot?** A stored conversation value. `order_id` is the key slot in the Rasa flow; the local demo keeps it in SQLite, and the public Pages demo keeps it in D1 session state.
10. **Why ask for an order ID?** It links a vague customer claim to a structured example record. Validation prevents arbitrary strings from becoming order lookups.
11. **How is the ID validated?** The example format is `KV-` plus five digits. Unknown valid IDs return a not-found message; malformed paths return HTTP 422.
12. **What is a custom action?** Python code called by Rasa to perform work outside dialogue prediction. Here it fetches an order or creates a demo case.
13. **Why separate the action server?** It isolates I/O and dependencies from conversation management and gives network failures an explicit boundary.
14. **What is a REST API?** An HTTP interface with resources and JSON. The browser posts chat requests and the action server fetches order data.
15. **What happens to one browser request?** React posts a typed message and session ID. In public mode, a Pages Function validates it, reads demo state from D1, applies deterministic policy, and returns text plus optional order and case. In local mode, FastAPI handles the request.
16. **Why FastAPI?** It makes request validation and response contracts concise and generates OpenAPI documentation. Its speed is not the reason to choose it here.
17. **What does Pydantic add?** It rejects malformed input and ensures the backend response matches the expected order and chat shapes.
18. **Why SQLite and D1?** SQLite persists the local demo without extra infrastructure. Cloudflare D1 persists the public demo within the Free plan. A real pilot would need a reviewed data model, identity, retention, and database operations.
19. **How are sessions isolated?** Each browser tab has a random session ID. The local SQLite and public D1 stores key state by that ID; public case reads and updates are restricted to the same ID. This is a demo boundary, not user authentication.
20. **What is a human handoff here?** A structured case stored in the demo database. It is not a live CRM transfer or message to a real employee.
21. **When is a handoff required?** Current demo rules use it for damage, confirmed missing items, partner exceptions, and uncertain returns.
22. **How are refund promises prevented?** The response reports the stored simulated status and explicitly says no payment or date is being promised.
23. **How does the app handle an outage?** The Rasa gateway returns HTTP 503; the UI shows a failure message. The action also has timeouts and connection-error responses.
24. **Why use timeouts?** A backend call should fail predictably instead of hanging a support conversation indefinitely.
25. **Why no retry loop?** Repeating case creation could duplicate side effects. The small demo favors one bounded request and a clear failure.
26. **What is supervised learning?** Learning from labeled examples. The public router does not train such a model; Rasa's NLU may use labeled intents when a licensed model is trained.
27. **What is unsupervised learning?** Finding structure in unlabeled data, such as clustering. It is not used in this repository.
28. **Why split training, validation, and test data?** Training fits parameters, validation guides choices, and a held-out test estimates generalization. This demo has no trained public model and too few samples for a meaningful split.
29. **What is overfitting?** A model performs well on seen phrases but poorly on new ones. The authored evaluation here cannot establish generalization.
30. **What is underfitting?** A model or rule set is too simple for the problem, such as keyword routing missing natural customer paraphrases.
31. **What is data leakage?** Letting test information influence training or tuning. The current curated scenarios intentionally match implemented rules, so 14/14 should not be treated as unbiased accuracy.
32. **What are precision and recall?** Precision asks how many predicted cases were right; recall asks how many true cases were found. A held-out labeled set is needed to measure them here.
33. **What is F1?** The harmonic mean of precision and recall. It is useful when both false positives and missed cases matter, but no F1 is reported for this project.
34. **What is measured today?** The evaluation script checks expected final order, handoff, and one guidance phrase for 14 selected journeys and records local execution time.
35. **Unit vs integration vs end-to-end tests?** Policy tests isolate decisions; API and cloud adapter tests exercise routes with temporary databases; Chromium tests cover authored browser journeys. Live Pages chat and case updates were also checked manually.
36. **What is a Docker image?** A packaged filesystem and command. A container is a running instance of that image.
37. **What does Compose do?** It starts and networks the frontend and API, mounts a persistent volume, and optionally starts the SDK action server.
38. **What is CI/CD here?** GitHub Actions runs Python and frontend checks. Cloudflare Pages automatically builds and deploys the `main` branch. A successful deployment does not imply the independent GitHub Actions run has passed.
39. **How is access protected?** Local case operations use a configured header token. Public case operations are limited to the browser session ID and per-IP rate limits, over HTTPS. There is no real user identity or staff role; a production pilot would need those controls plus audit logs.
40. **How would you scale it?** Separate stateless API replicas from managed persistent storage, make case creation idempotent, keep Rasa/action endpoints private, and monitor latency and errors.
41. **What should be monitored in a pilot?** Service failures, request latency, task completion, unsupported claims, handoff quality, and customer feedback, with privacy-conscious event collection.
42. **Why human in the loop?** Missing items, damage, and exceptions require judgment or authority the assistant does not have. A good case reduces repeated information gathering.
43. **Why not generate every answer with an LLM?** It could make unsupported refund or return claims. Explicit policy controls are easier to inspect and test for this narrow demo.
44. **What is the biggest limitation?** Fictional records and a small hand-written router cannot represent real customer language, policy, identity, or operational impact.
45. **What would you do before a client pilot?** Validate the retailer's problem and policies, secure a consented data source, build authenticated integrations, test with agents, and measure outcomes against a baseline.

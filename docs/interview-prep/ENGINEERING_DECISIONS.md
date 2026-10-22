# Engineering decisions and tradeoffs

- **Keep Rasa central in licensed mode.** The original work is a Rasa conversation prototype. Flows, slots, and actions are valuable for controlled support journeys. A generic LLM would add cost and risk without solving order verification. The public adapter is explicitly a limited demonstration.
- **Separate conversation, action, and retail API.** Dialogue logic asks for missing context; actions access a backend; the backend owns order and case contracts. Each boundary can be replaced independently. The cost is configuration and network failure handling.
- **Use FastAPI and Pydantic.** Typed schemas give clear input errors and readable OpenAPI docs. A separate integration gateway would be justified at larger scale; one FastAPI service keeps this demo understandable.
- **Use deterministic policies.** Missing quantities, split deliveries, partner flags, and return exceptions should lead to explainable results. Customer-facing text may be improved later, but refund and return decisions must remain auditable.
- **Replace Streamlit as the primary UI with React.** The original UI worked as a prototype. React gives finer control over responsive customer and employee experiences and typed component contracts. The Streamlit source stays in history.
- **Use SQLite for demo persistence.** A file database makes real case updates possible without external spend. It is not the right shared database for horizontally scaled production.
- **Keep sample orders fictional.** The prototype can be rehearsed and tested without private customer data or retailer credentials. It cannot validate real operational outcomes.
- **Containerize only public components.** The API, frontend, and SDK action server have Dockerfiles. A proprietary Rasa Pro image is not distributed. Licensed operators provide their own runtime.
- **Escalate exceptions.** Damage, actual missing items, partner-specific questions, and return exceptions require assessment. The app records a simulated case but does not contact a real employee or issue compensation.
- **Production gap.** A pilot needs authenticated retailer APIs, verified policy and legal review, consent and retention rules, role-based case access, incident handling, monitoring, human evaluation, and a deployment architecture with TLS and managed persistence.

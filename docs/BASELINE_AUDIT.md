# Baseline audit (before October 2026 portfolio upgrade)

The two committed revisions contained a Streamlit interface (`app.py`, 794 lines), a Rasa Pro style NLU/flow configuration, one Rasa SDK action, and a FastAPI service with three in-memory example orders. The separation between conversation server, action server, and retail API was useful and is retained. The action already handled connection and timeout errors and the Streamlit reset created a new sender ID.

The repository did **not** contain the `tests/` directory or GitHub Actions workflow mentioned in the project brief. There was no persistent case operation, real handoff, order-ID validation, typed order contract, public mode without Rasa Pro, or Docker configuration. `requirements.txt` left most versions unconstrained. Both the UI and action had localhost URLs embedded in source. The response for an order was a long text dump, and the existing rules answered most issue intents with generic guidance before a separate order lookup. The `assistant_id` still said `hema` despite the Kruidvat copy. No verified Rasa Pro runtime or license is available in this checkout; compatibility and live training cannot be asserted.

This audit describes repository state, not a claim about the author's historical work or any real retailer deployment.

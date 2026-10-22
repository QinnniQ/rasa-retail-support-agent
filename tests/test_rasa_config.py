"""Static checks only; they do not replace training in licensed Rasa Pro."""
from pathlib import Path
import yaml


def read(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def test_flows_actions_and_rules_are_consistent():
    flows = read("data/flows.yml")["flows"]
    domain = read("domain.yml")
    rules = read("data/rules.yml")["rules"]
    actions = set(domain["actions"])
    triggers = set()
    for flow in flows.values():
        triggers.update(item["intent"] for item in flow["nlu_trigger"])
        assert any(step.get("collect") == "order_id" for step in flow["steps"])
        assert all(step["action"] in actions for step in flow["steps"] if "action" in step)
    rule_intents = {step["intent"] for rule in rules for step in rule["steps"] if "intent" in step}
    assert not (triggers & rule_intents)
    assert len(triggers) >= 7
    assert "action_create_support_case" in actions

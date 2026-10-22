"""Evaluate implemented public demo journeys, without claiming NLU model accuracy."""
import asyncio
import json
import tempfile
import time
from pathlib import Path

import httpx
import mock_backend
from support.store import Store


async def main():
    cases = json.loads(Path("evaluation/cases.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as directory:
        mock_backend.STORE = Store(str(Path(directory) / "evaluation.db"))
        mock_backend.MODE = "demo"
        results = []
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=mock_backend.app), base_url="http://test") as client:
            for index, case in enumerate(cases):
                start = time.perf_counter()
                response = None
                for turn in case["turns"]:
                    response = await client.post("/api/chat", json={"session_id": f"evaluation_{index:03d}", **turn})
                    response.raise_for_status()
                payload = response.json()
                actual_order = payload["order"]["order_id"] if payload["order"] else None
                correct = (actual_order == case["order"] and bool(payload["case_id"]) == case["handoff"]
                           and case["contains"].lower() in " ".join(payload["messages"]).lower())
                results.append({"name": case["name"], "correct": correct, "latency_ms": round((time.perf_counter() - start) * 1000, 1), "order": actual_order, "handoff": bool(payload["case_id"])})
    print(json.dumps({"passed": sum(row["correct"] for row in results), "total": len(results), "results": results}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

"""Evaluation harness for the Multi-Agent AI Travelling Agent.

Runs the deterministic checks from the evaluation dataset against the travel
planner (origin/destination/mode/meal/budget extraction) and the guardrails
(input blocking).

The harness NEVER fabricates numbers: it measures the extraction accuracy of
the planner deterministically, and (when --live is set) runs full workflows
against the real Google Maps / LLM APIs and reports actual latency/tokens/cost
from run metrics.

Usage:
    python evaluate.py                              # deterministic subset (no API keys)
    python evaluate.py --dataset app/data/eval_travel_dataset.json
    python evaluate.py --live                       # also run full workflows (needs keys)
"""

import argparse
import asyncio
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.agents.travel_planner_agent import (
    extract_origin_destination,
    extract_travel_modes,
    extract_meal_types,
    extract_time_budget,
)
from app.tools.guardrails import guardrails


def load_dataset(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_extraction(dataset: list) -> dict:
    """Score deterministic extraction against expectations for each case."""
    metrics = {
        "origin_correct": 0,
        "destination_correct": 0,
        "modes_correct": 0,
        "meals_correct": 0,
        "budget_correct": 0,
        "blocked_detected": 0,
        "total": len(dataset),
        "errors": [],
    }
    for case in dataset:
        intent = case["intent"]
        if case.get("expected_action") == "blocked":
            if not guardrails.validate_input(intent)["safe"]:
                metrics["blocked_detected"] += 1
                metrics["origin_correct"] += 1
            else:
                metrics["errors"].append(f"FAIL(block): {intent}")
            continue

        origin, destination = extract_origin_destination(intent)
        modes = extract_travel_modes(intent)
        meals = extract_meal_types(intent)
        budget = extract_time_budget(intent)

        for label, got, expected in [
            ("origin", origin, case.get("expected_origin")),
            ("destination", destination, case.get("expected_destination")),
        ]:
            if (got or "").lower() == (expected or "").lower():
                metrics[f"{label}_correct"] += 1
            else:
                metrics["errors"].append(
                    f"FAIL({label}): {intent!r} -> {got!r} (expected {expected!r})")

        exp_modes = sorted(case.get("expected_modes", []) or [])
        if sorted(modes) == exp_modes:
            metrics["modes_correct"] += 1
        else:
            metrics["errors"].append(
                f"FAIL(modes): {intent!r} -> {modes} (expected {exp_modes})")

        exp_meals = sorted(case.get("expected_meals", []) or [])
        if sorted(meals) == exp_meals:
            metrics["meals_correct"] += 1
        else:
            metrics["errors"].append(
                f"FAIL(meals): {intent!r} -> {meals} (expected {exp_meals})")

        exp_budget = case.get("expected_budget_minutes")
        if budget == exp_budget:
            metrics["budget_correct"] += 1
        elif exp_budget is not None:
            metrics["errors"].append(
                f"FAIL(budget): {intent!r} -> {budget} (expected {exp_budget})")

    n = metrics["total"]
    return {
        **metrics,
        "origin_accuracy": round(metrics["origin_correct"] / n, 4) if n else 0.0,
        "destination_accuracy": round(metrics["destination_correct"] / n, 4) if n else 0.0,
    }


async def evaluate_live(dataset: list, limit: int) -> dict:
    """Run full travel workflows against the real backend and collect metrics."""
    from app.graph.workflow import travel_workflow

    results = []
    for case in dataset[:limit]:
        intent = case["intent"]
        if not guardrails.validate_input(intent)["safe"]:
            results.append({"id": case["id"], "intent": intent,
                            "status": "blocked", "metrics": {}})
            continue
        r = await travel_workflow.run(
            intent,
            origin=case.get("origin"),
            destination=case.get("destination"),
            travel_modes=case.get("modes"),
            meal_types=case.get("meals"),
            time_budget_minutes=case.get("budget_minutes"),
            user_id="eval-runner",
        )
        results.append({
            "id": case["id"],
            "intent": intent,
            "status": r.get("terminal_status"),
            "step": r.get("current_step"),
            "metrics": r.get("metrics", {}) or {},
            "best_mode": (r.get("route_data") or {}).get("best_mode"),
        })

    completed = [r for r in results if r.get("status") == "complete"]
    latencies = [r["metrics"].get("total_latency_ms", 0) for r in completed]
    tokens = [r["metrics"].get("total_tokens", 0) for r in completed]
    costs = [r["metrics"].get("estimated_cost_usd", 0.0) for r in completed]
    return {
        "runs": results,
        "n_attempted": len(results),
        "n_completed": len(completed),
        "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else None,
        "p95_latency_ms": round(statistics.quantiles(latencies, n=20)[18], 2) if len(latencies) >= 20 else None,
        "avg_tokens": round(statistics.mean(tokens), 1) if tokens else None,
        "total_cost_usd": round(sum(costs), 6) if costs else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="app/data/eval_travel_dataset.json")
    parser.add_argument("--live", action="store_true", help="run full workflows (needs API keys)")
    parser.add_argument("--limit", type=int, default=5, help="max live workflows")
    args = parser.parse_args()

    dataset = load_dataset(args.dataset)

    print(f"[evaluate] dataset={args.dataset} cases={len(dataset)}")
    score = evaluate_extraction(dataset)
    print(f"[evaluate] origin_accuracy={score['origin_accuracy']} "
          f"destination_accuracy={score['destination_accuracy']} "
          f"modes_correct={score['modes_correct']} meals_correct={score['meals_correct']} "
          f"budget_correct={score['budget_correct']} blocked_detected={score['blocked_detected']}")
    for err in score["errors"][:20]:
        print(f"[evaluate]   {err}")

    if args.live:
        live = asyncio.run(evaluate_live(dataset, args.limit))
        print(f"[evaluate] live: completed={live['n_completed']}/{live['n_attempted']}")
        print(f"[evaluate] live: avg_latency_ms={live['avg_latency_ms']} "
              f"avg_tokens={live['avg_tokens']} total_cost_usd={live['total_cost_usd']}")
        for run in live["runs"]:
            print(f"[evaluate]   {run['id']}: {run['status']} ({run['step']})")

    blocked = sum(1 for c in dataset if c.get("expected_action") == "blocked")
    if score["origin_accuracy"] < 1.0 or score["blocked_detected"] < blocked:
        print("[evaluate] FAILED deterministic checks")
        sys.exit(1)
    print("[evaluate] PASS")


if __name__ == "__main__":
    main()
"""Evaluation harness for the Multi-Agent AI platform.

Runs the deterministic checks from the evaluation dataset against the planner
(classification), guardrails (input blocking) and the approval-gating contract.

The harness NEVER fabricates numbers: it measures the classification of the
planner, the guardrail decisions, and (when --live is set) runs full workflows
against the real API and reports actual latency/tokens/cost from run metrics.

Usage:
    python evaluate.py                      # deterministic subset (no API keys)
    python evaluate.py --dataset app/data/eval_dataset.json
    python evaluate.py --live               # also run full workflows (needs keys)
"""

import argparse
import asyncio
import json
import os
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.agents.planner_agent import classify_action, PlannerAgent
from app.tools.guardrails import guardrails


def load_dataset(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_classification(dataset: list, agent: PlannerAgent) -> dict:
    """Score intent -> action / technology / target extraction against expectations."""
    metrics = {
        "action_correct": 0,
        "technology_correct": 0,
        "targets_correct": 0,
        "total": len(dataset),
        "applicable_tech": 0,
        "applicable_targets": 0,
        "blocked_detected": 0,
        "errors": [],
    }
    for case in dataset:
        intent = case["intent"]
        expected = case.get("expected_action")
        if expected == "blocked":
            check = guardrails.validate_input(intent)
            if not check["safe"]:
                metrics["blocked_detected"] += 1
                metrics["action_correct"] += 1
            else:
                metrics["errors"].append(f"FAIL(block): {intent}")
            continue

        action = classify_action(intent)
        tech = agent._extract_technology(intent)
        targets = agent._extract_devices(intent)

        if action == expected:
            metrics["action_correct"] += 1
        else:
            metrics["errors"].append(
                f"FAIL(action): {intent!r} -> {action} (expected {expected})")

        exp_tech = case.get("expected_technology") or ""
        if exp_tech:
            metrics["applicable_tech"] += 1
            if (tech or "") == exp_tech:
                metrics["technology_correct"] += 1
            else:
                metrics["errors"].append(
                    f"FAIL(tech): {intent!r} -> {tech!r} (expected {exp_tech!r})")

        if case.get("expected_targets") is not None:
            metrics["applicable_targets"] += 1
            if sorted(set(targets)) == sorted(set(case["expected_targets"])):
                metrics["targets_correct"] += 1
            else:
                metrics["errors"].append(
                    f"FAIL(targets): {intent!r} -> {targets} "
                    f"(expected {case['expected_targets']})")

    n = metrics["total"]
    t = metrics["applicable_tech"]
    g = metrics["applicable_targets"]
    return {
        **metrics,
        "action_accuracy": round(metrics["action_correct"] / n, 4) if n else 0.0,
        "technology_accuracy": round(metrics["technology_correct"] / t, 4) if t else 0.0,
        "target_accuracy": round(metrics["targets_correct"] / g, 4) if g else 0.0,
    }


async def evaluate_live(dataset: list, limit: int) -> dict:
    """Run full workflows against the real backend and collect truthful metrics."""
    from app.graph.workflow import NetworkWorkflow
    from app.tools.evaluation import evaluation

    wf = NetworkWorkflow()
    results = []
    for case in dataset[:limit]:
        intent = case["intent"]
        check = guardrails.validate_input(intent)
        if not check["safe"]:
            results.append({"id": case["id"], "intent": intent,
                            "status": "blocked", "metrics": {}})
            continue
        r = await wf.run(intent, user_id="eval-runner")
        m = r.get("metrics", {}) or {}
        results.append({
            "id": case["id"],
            "intent": intent,
            "status": r.get("terminal_status"),
            "step": r.get("current_step"),
            "metrics": m,
            "requires_approval": r.get("requires_approval", False),
        })

    completed = [r for r in results if r.get("status") in ("complete", "awaiting_approval")]
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
    parser.add_argument("--dataset", default="app/data/eval_dataset.json")
    parser.add_argument("--live", action="store_true", help="run full workflows (needs API keys)")
    parser.add_argument("--limit", type=int, default=5, help="max live workflows")
    args = parser.parse_args()

    dataset = load_dataset(args.dataset)
    agent = PlannerAgent()

    print(f"[evaluate] dataset={args.dataset} cases={len(dataset)}")
    score = evaluate_classification(dataset, agent)
    print(f"[evaluate] action_accuracy={score['action_accuracy']} "
          f"technology_accuracy={score['technology_accuracy']} "
          f"target_accuracy={score['target_accuracy']} "
          f"blocked_detected={score['blocked_detected']}")
    for err in score["errors"][:20]:
        print(f"[evaluate]   {err}")

    if args.live:
        live = asyncio.run(evaluate_live(dataset, args.limit))
        print(f"[evaluate] live: completed={live['n_completed']}/{live['n_attempted']}")
        print(f"[evaluate] live: avg_latency_ms={live['avg_latency_ms']} "
              f"avg_tokens={live['avg_tokens']} total_cost_usd={live['total_cost_usd']}")
        for run in live["runs"]:
            print(f"[evaluate]   {run['id']}: {run['status']} ({run['step']})")

    # Exit nonzero if deterministic checks fail, so CI can gate on it.
    if score["action_accuracy"] < 1.0 or score["blocked_detected"] < sum(
            1 for c in dataset if c.get("expected_action") == "blocked"):
        print("[evaluate] FAILED deterministic checks")
        sys.exit(1)
    print("[evaluate] PASS")


if __name__ == "__main__":
    main()
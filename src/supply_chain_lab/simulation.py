"""Phase 4: decision-support simulation under limited review capacity.

Compares random vs business-rule vs model-based prioritization at daily review
capacities (20/50/100) under low/base/high hypothetical effectiveness.
Monte Carlo captures sampling uncertainty; all projections labeled hypothetical.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import EFFECTIVENESS_SCENARIOS, MONTE_CARLO_RUNS, RANDOM_SEED, REVIEW_CAPACITIES


def rank_top_k(scores: np.ndarray, k: int) -> np.ndarray:
    k = min(k, len(scores))
    return np.argsort(-scores, kind="stable")[:k]


def simulate_policy(
    y_true: np.ndarray,
    scores: np.ndarray,
    capacity: int,
    effectiveness: float,
    n_runs: int = MONTE_CARLO_RUNS,
    seed: int = RANDOM_SEED,
) -> dict:
    """Expected rescued lates among top-k reviewed orders.

    Each reviewed actually-late order is 'rescued' with probability
    `effectiveness` (Bernoulli, hypothetical intervention). Returns mean + CI.
    """
    rng = np.random.default_rng(seed)
    idx = rank_top_k(scores, capacity)
    flagged_late = y_true[idx]  # 0/1 vector of reviewed orders that were truly late
    draws = rng.binomial(1, effectiveness, size=(n_runs, len(idx)))
    rescued = (draws * flagged_late).sum(axis=1)
    return {
        "capacity": capacity,
        "effectiveness": effectiveness,
        "n_reviewed": len(idx),
        "n_flagged_truly_late": int(flagged_late.sum()),
        "precision_at_k": round(float(flagged_late.mean()) if len(idx) else 0.0, 4),
        "recall_at_k": round(float(flagged_late.sum() / y_true.sum()), 4) if y_true.sum() else 0.0,
        "expected_rescued_mean": round(float(rescued.mean()), 2),
        "expected_rescued_p5": round(float(np.percentile(rescued, 5)), 2),
        "expected_rescued_p95": round(float(np.percentile(rescued, 95)), 2),
    }


def compare_policies(
    test_frame: pd.DataFrame,
    model_scores: np.ndarray,
    rule_scores: np.ndarray,
    capacities: list[int] | None = None,
    scenarios: dict[str, float] | None = None,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Full policy × capacity × effectiveness comparison on the TEST set."""
    capacities = capacities or REVIEW_CAPACITIES
    scenarios = scenarios or EFFECTIVENESS_SCENARIOS
    y = test_frame["target_late"].to_numpy()
    rng = np.random.default_rng(seed)
    random_scores = rng.random(len(y))
    policies = {"random": random_scores, "business_rule": rule_scores, "model": model_scores}
    rows = []
    for pname, scores in policies.items():
        for cap in capacities:
            for sname, eff in scenarios.items():
                r = simulate_policy(y, np.asarray(scores), cap, eff, seed=seed)
                r.update({"policy": pname, "scenario": sname})
                rows.append(r)
    # No-intervention baseline rows.
    for cap in capacities:
        rows.append(
            {
                "policy": "no_intervention",
                "scenario": "base",
                "capacity": cap,
                "effectiveness": 0.0,
                "n_reviewed": 0,
                "n_flagged_truly_late": 0,
                "precision_at_k": 0.0,
                "recall_at_k": 0.0,
                "expected_rescued_mean": 0.0,
                "expected_rescued_p5": 0.0,
                "expected_rescued_p95": 0.0,
            }
        )
    df = pd.DataFrame(rows)
    return df.sort_values(["capacity", "scenario", "policy"]).reset_index(drop=True)


def hypothetical_costs(comparison: pd.DataFrame, cost_per_review: float = 2.0) -> pd.DataFrame:
    """Attach ILLUSTRATIVE review costs (not observed unit economics)."""
    df = comparison.copy()
    df["illustrative_reviews_cost"] = (df["n_reviewed"] * cost_per_review).round(2)
    df["illustrative_cost_note"] = (
        f"Illustrative only: {cost_per_review} USD per reviewed order (assumption, not observed)"
    )
    return df

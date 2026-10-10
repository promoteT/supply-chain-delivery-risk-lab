import numpy as np

from supply_chain_lab import simulation as S


def test_simulate_policy_reproducible():
    rng = np.random.default_rng(0)
    y = (rng.random(200) < 0.3).astype(int)
    scores = rng.random(200)
    a = S.simulate_policy(y, scores, 20, 0.25)
    b = S.simulate_policy(y, scores, 20, 0.25)
    assert a == b
    assert a["expected_rescued_p5"] <= a["expected_rescued_mean"] <= 100


def test_compare_policies_covers_all(tmp_path):
    import pandas as pd

    rng = np.random.default_rng(1)
    n = 150
    frame = pd.DataFrame({"target_late": (rng.random(n) < 0.3).astype(int)})
    comp = S.compare_policies(
        frame, rng.random(n), rng.random(n), capacities=[20], scenarios={"low": 0.1, "base": 0.25}
    )
    policies = set(comp["policy"])
    assert {"random", "business_rule", "model", "no_intervention"} <= policies
    assert (comp[comp["policy"] == "no_intervention"]["expected_rescued_mean"] == 0).all()


def test_hypothetical_costs_labeled():
    import pandas as pd

    df = pd.DataFrame({"n_reviewed": [20], "policy": ["model"]})
    out = S.hypothetical_costs(df, 2.0)
    assert out["illustrative_reviews_cost"].iloc[0] == 40.0
    assert "Illustrative" in out["illustrative_cost_note"].iloc[0]

import numpy as np

from supply_chain_lab import features as F
from supply_chain_lab import modelling as M


def _frame(tables):
    return F.build_model_frame(
        tables["orders"],
        tables["order_items"],
        tables["customers"],
        tables["sellers"],
        tables["products"],
    )


def test_chronological_split_ordered(tables):
    frame = _frame(tables)
    splits = M.chronological_split(frame)
    assert splits["train"][M.TIME_COL].max() <= splits["valid"][M.TIME_COL].min()
    assert splits["valid"][M.TIME_COL].max() <= splits["test"][M.TIME_COL].min()
    total = sum(len(v) for v in splits.values())
    assert total == len(frame)


def test_evaluate_model_held_out_test(tables):
    frame = _frame(tables)
    splits = M.chronological_split(frame)
    models = M.build_models()
    res = M.evaluate_model("logistic", models["logistic"], splits, capacities=(5, 10))
    assert 0.0 <= res["roc_auc"] <= 1.0
    assert res["n_test"] > 0
    assert len(res["capacity_metrics"]) == 2
    assert "calibration" in res


def test_recall_at_capacity_bounds(tables):
    frame = _frame(tables)
    y = frame["target_late"]
    scores = np.linspace(0, 1, len(y))
    m = M.recall_at_capacity(y, scores, 10)
    assert 0.0 <= m["recall_at_k"] <= 1.0
    assert 0.0 <= m["precision_at_k"] <= 1.0


def test_assert_no_leakage_rejects_full_frame(tables):
    import pandas as pd
    import pytest

    frame = _frame(tables).copy()
    frame["order_delivered_customer_date"] = pd.Timestamp("2017-01-01")
    with pytest.raises(ValueError):
        M.assert_no_leakage(frame)


def test_business_rule_uses_train_stats(tables):
    frame = _frame(tables)
    splits = M.chronological_split(frame)
    train_stats = M._fit_rule_params(splits["train"])
    s_train_fit = M.business_rule_scores(splits["test"], train_stats=train_stats)
    assert ((s_train_fit >= 0) & (s_train_fit <= 1)).all()
    # train-fitted params come from train, not test
    assert train_stats["median"] == splits["train"]["promised_days_at_approval"].median()


def test_evaluate_model_single_class_safe():
    import pandas as pd

    base = pd.Timestamp("2017-01-01")
    n = 30
    df = pd.DataFrame(
        {
            "order_id": [f"x{i}" for i in range(n)],
            "order_approved_at": [base + pd.Timedelta(days=i) for i in range(n)],
            "target_late": [0] * n,
            **{c: 0.0 for c in M.NUMERIC_FEATURES},
            **{c: "unknown" for c in M.CATEGORICAL_FEATURES},
        }
    )
    splits = M.chronological_split(df)
    models = M.build_models()
    res = M.evaluate_model("logistic", models["logistic"], splits, capacities=(5,))
    import math

    assert math.isnan(res["roc_auc"]) or 0.0 <= res["roc_auc"] <= 1.0

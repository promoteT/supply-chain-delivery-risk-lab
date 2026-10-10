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

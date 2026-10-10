"""Phase 3: early-warning risk model (prediction time = order approval).

Guards: chronological split on approval time; preprocessing fit on train only;
threshold chosen on validation, never test; leakage columns rejected.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import RANDOM_SEED, TRAIN_FRAC, VALID_FRAC
from .features import CATEGORICAL_FEATURES, LEAKAGE_COLUMNS, NUMERIC_FEATURES

logger = logging.getLogger(__name__)

FEATURE_COLS = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TIME_COL = "order_approved_at"


def assert_no_leakage(df: pd.DataFrame) -> None:
    leak = LEAKAGE_COLUMNS.intersection(set(df.columns)) - {"target_late"}
    present = [c for c in FEATURE_COLS if c in leak]
    if present:
        raise ValueError(f"Leakage features detected: {present}")
    for forbidden in (
        "order_delivered_customer_date",
        "order_delivered_carrier_date",
        "order_status",
    ):
        if forbidden in FEATURE_COLS:
            raise ValueError(f"Leakage feature configured: {forbidden}")


def chronological_split(
    df: pd.DataFrame, train_frac: float = TRAIN_FRAC, valid_frac: float = VALID_FRAC
) -> dict[str, pd.DataFrame]:
    """Sort by approval time; split 60/20/20. No shuffling across time."""
    d = df.sort_values(TIME_COL).reset_index(drop=True)
    n = len(d)
    i_train = int(n * train_frac)
    i_valid = i_train + int(n * valid_frac)
    return {
        "train": d.iloc[:i_train].reset_index(drop=True),
        "valid": d.iloc[i_train:i_valid].reset_index(drop=True),
        "test": d.iloc[i_valid:].reset_index(drop=True),
    }


def _preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        [
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )


def build_models() -> dict[str, Pipeline]:
    return {
        "logistic": Pipeline(
            [
                ("prep", _preprocessor()),
                ("clf", LogisticRegression(max_iter=2000, C=1.0, random_state=RANDOM_SEED)),
            ]
        ),
        "hgb": Pipeline(
            [
                ("prep", _preprocessor()),
                ("clf", HistGradientBoostingClassifier(random_state=RANDOM_SEED)),
            ]
        ),
    }


def majority_baseline_rate(y_train: pd.Series) -> float:
    return float(y_train.mean())


def business_rule_scores(df: pd.DataFrame) -> np.ndarray:
    """Simple rule: risk rises with short promised window + multi-seller + high freight share.

    Uses ONLY approval-time features. Returns scores in [0,1] (not calibrated).
    """
    promised = df["promised_days_at_approval"].fillna(df["promised_days_at_approval"].median())
    # shorter promised window -> historically riskier
    short = 1.0 - (promised - promised.min()) / (promised.max() - promised.min() + 1e-9)
    score = (
        0.5 * short.fillna(0.5)
        + 0.3 * df["is_multi_seller"].fillna(0)
        + 0.2 * df["freight_share"].fillna(0).clip(0, 1)
    )
    return score.to_numpy()


def _metrics_at_threshold(y: pd.Series, scores: np.ndarray, thr: float) -> dict:
    pred = (scores >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    return {
        "threshold": round(float(thr), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def recall_at_capacity(y: pd.Series, scores: np.ndarray, capacity: int) -> dict:
    """Top-k review capacity metric: if we can review `capacity` orders, what
    share of actual lates do we catch (recall@k) and with what precision?"""
    k = min(capacity, len(y))
    order = np.argsort(-scores, kind="stable")[:k]
    caught = int(np.asarray(y)[order].sum())
    total_late = int(np.asarray(y).sum())
    return {
        "capacity": int(capacity),
        "k": int(k),
        "caught": caught,
        "total_late": total_late,
        "recall_at_k": round(caught / total_late, 4) if total_late else 0.0,
        "precision_at_k": round(caught / k, 4) if k else 0.0,
    }


def evaluate_model(
    name: str,
    model: Pipeline,
    splits: dict[str, pd.DataFrame],
    capacities: tuple[int, ...] = (20, 50, 100),
) -> dict:
    """Fit on train; threshold via Youden's J on VALID; report on TEST (held out)."""
    X_train, y_train = splits["train"][FEATURE_COLS], splits["train"]["target_late"]
    X_valid, y_valid = splits["valid"][FEATURE_COLS], splits["valid"]["target_late"]
    X_test, y_test = splits["test"][FEATURE_COLS], splits["test"]["target_late"]
    model.fit(X_train, y_train)
    s_valid = model.predict_proba(X_valid)[:, 1]
    s_test = model.predict_proba(X_test)[:, 1]

    # Threshold selection on validation only (maximize Youden's J).
    thrs = np.linspace(0.05, 0.95, 37)
    best, best_j = 0.5, -1.0
    for t in thrs:
        m = _metrics_at_threshold(y_valid, s_valid, t)
        j = (m["recall"] + m["tn"] / (m["tn"] + m["fp"] + 1e-9)) - 1
        if j > best_j:
            best_j, best = j, t

    test_m = _metrics_at_threshold(y_test, s_test, best)
    result = {
        "model": name,
        "n_train": len(X_train),
        "n_valid": len(X_valid),
        "n_test": len(X_test),
        "base_rate_test": round(float(np.asarray(y_test).mean()), 4),
        "roc_auc": round(float(roc_auc_score(y_test, s_test)), 4),
        "pr_auc": round(float(average_precision_score(y_test, s_test)), 4),
        **test_m,
        "capacity_metrics": [recall_at_capacity(y_test, s_test, c) for c in capacities],
    }
    # Calibration deciles on test.
    cal = pd.DataFrame({"score": s_test, "y": np.asarray(y_test)})
    cal["decile"] = pd.qcut(cal["score"], 10, duplicates="drop")
    result["calibration"] = (
        cal.groupby("decile", observed=True)
        .agg(n=("y", "size"), mean_score=("score", "mean"), late_rate=("y", "mean"))
        .reset_index(drop=True)
        .round(4)
        .to_dict(orient="records")
    )
    return result


def evaluate_rule_and_baseline(splits: dict[str, pd.DataFrame]) -> list[dict]:
    y_test = splits["test"]["target_late"]
    base_rate = majority_baseline_rate(splits["train"]["target_late"])
    # Majority-class predictions (predict late iff base_rate > 0.5).
    maj_pred = np.ones(len(y_test)) if base_rate > 0.5 else np.zeros(len(y_test))
    tn, fp, fn, tp = confusion_matrix(y_test, maj_pred, labels=[0, 1]).ravel()
    out = [
        {
            "model": "majority_baseline",
            "train_base_rate": round(base_rate, 4),
            "precision": round(tp / (tp + fp), 4) if (tp + fp) else 0.0,
            "recall": round(tp / (tp + fn), 4) if (tp + fn) else 0.0,
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        }
    ]
    rule_scores = business_rule_scores(splits["test"])
    out.append(
        {
            "model": "business_rule",
            "roc_auc": round(float(roc_auc_score(y_test, rule_scores)), 4),
            "pr_auc": round(float(average_precision_score(y_test, rule_scores)), 4),
            "capacity_metrics": [recall_at_capacity(y_test, rule_scores, c) for c in (20, 50, 100)],
        }
    )
    return out


def precision_recall_points(y: pd.Series, scores: np.ndarray) -> pd.DataFrame:
    p, r, t = precision_recall_curve(y, scores)
    return pd.DataFrame({"precision": p, "recall": r, "threshold": list(t) + [float("nan")]})

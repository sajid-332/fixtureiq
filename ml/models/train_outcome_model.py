"""Stage 5: train and validate FixtureIQ's leakage-safe EPL outcome model.

Important development rule: the 2025/26 season is a locked final test set. This
script deliberately does not score, tune, or report performance on that season.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    log_loss,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT / "data/historical/processed/epl_stage5_features.csv"
MODEL_DIR = ROOT / "ml/models"

TRAIN_SEASONS = ["2021/22", "2022/23", "2023/24"]
VALIDATION_SEASON = "2024/25"
LOCKED_TEST_SEASON = "2025/26"
SELECTION_VALIDATION_SEASONS = ["2023/24", "2024/25"]
MODEL_VERSION = "0.5.0-stage5"

# Stage 4 contextual features remain available in the dataset but are excluded
# from the core probability model until validation demonstrates an improvement.
CORE_FEATURES = [
    "HomeLast5Points",
    "AwayLast5Points",
    "Last5HomePoints",
    "Last5AwayPoints",
    "LeaguePointsGap",
    "GamesPlayedGap",
    "HomePositionBefore",
    "AwayPositionBefore",
]

CANDIDATE_FEATURE_SETS: Dict[str, List[str]] = {
    "core_form_table": CORE_FEATURES,
    "core_plus_previous_season": CORE_FEATURES
    + [
        "HomePreviousSeasonPPG",
        "AwayPreviousSeasonPPG",
    ],
    "core_plus_cross_season": CORE_FEATURES
    + [
        "HomeCrossSeasonRecentPPG",
        "AwayCrossSeasonRecentPPG",
        "HomeCrossSeasonMatchesUsed",
        "AwayCrossSeasonMatchesUsed",
    ],
    "core_plus_all_historical": CORE_FEATURES
    + [
        "HomePreviousSeasonPPG",
        "AwayPreviousSeasonPPG",
        "HomeCrossSeasonRecentPPG",
        "AwayCrossSeasonRecentPPG",
        "HomeCrossSeasonMatchesUsed",
        "AwayCrossSeasonMatchesUsed",
    ],
}

EXCLUDED_CONTEXT_FEATURE_GROUPS = [
    "H2H",
    "momentum/upset",
    "league pressure",
    "bookmaker odds",
]


def load_dataset(path: Path = DATA_FILE) -> pd.DataFrame:
    """Load and chronologically sort the Stage 5 feature dataset."""
    if not path.exists():
        raise FileNotFoundError(
            f"Stage 5 feature dataset not found: {path}. "
            "Run `python ml/features/build_stage5_features.py` first."
        )

    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"], errors="raise")
    df = df.sort_values("Date").reset_index(drop=True)

    required = {
        "Date",
        "Season",
        "FTR",
        "HomeGamesPlayedBefore",
        "AwayGamesPlayedBefore",
    }
    required.update(
        feature
        for features in CANDIDATE_FEATURE_SETS.values()
        for feature in features
    )
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(
            "Stage 5 dataset is missing required columns: "
            + ", ".join(sorted(missing))
        )

    return df


def build_model() -> Pipeline:
    """Create the deterministic Stage 5 multinomial logistic pipeline."""
    return Pipeline(
        [
            (
                "imputer",
                SimpleImputer(strategy="median", add_indicator=True),
            ),
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(max_iter=3000, random_state=42),
            ),
        ]
    )


def multiclass_brier_score(
    y_true: Sequence[str],
    probabilities: np.ndarray,
    classes: Sequence[str],
) -> float:
    """Mean squared probability error across all outcome classes."""
    class_to_index = {label: index for index, label in enumerate(classes)}
    one_hot = np.zeros_like(probabilities, dtype=float)
    for row_index, label in enumerate(y_true):
        one_hot[row_index, class_to_index[label]] = 1.0
    return float(np.mean(np.sum((probabilities - one_hot) ** 2, axis=1)))


def evaluate_model(
    model: Pipeline,
    frame: pd.DataFrame,
    feature_columns: Sequence[str],
) -> Dict[str, object]:
    """Evaluate a fitted model on a development/validation frame."""
    x = frame[list(feature_columns)]
    y = frame["FTR"]

    predictions = model.predict(x)
    probabilities = model.predict_proba(x)
    classes = list(model.classes_)

    ordered_labels = ["H", "D", "A"]
    recalls = recall_score(
        y,
        predictions,
        labels=ordered_labels,
        average=None,
        zero_division=0,
    )
    matrix = confusion_matrix(y, predictions, labels=ordered_labels)

    return {
        "matches": int(len(frame)),
        "accuracy": float(accuracy_score(y, predictions)),
        "log_loss": float(log_loss(y, probabilities, labels=classes)),
        "macro_f1": float(
            f1_score(
                y,
                predictions,
                labels=ordered_labels,
                average="macro",
                zero_division=0,
            )
        ),
        "multiclass_brier": multiclass_brier_score(y, probabilities, classes),
        "recall": {
            "home": float(recalls[0]),
            "draw": float(recalls[1]),
            "away": float(recalls[2]),
        },
        "confusion_matrix_labels": ordered_labels,
        "confusion_matrix": matrix.astype(int).tolist(),
    }


def seasons_before(df: pd.DataFrame, validation_season: str) -> List[str]:
    """Return all available seasons chronologically before validation_season."""
    season_order = (
        df.groupby("Season")["Date"].min().sort_values().index.astype(str).tolist()
    )
    if validation_season not in season_order:
        raise ValueError(f"Unknown validation season: {validation_season}")
    return season_order[: season_order.index(validation_season)]


def compare_feature_sets(df: pd.DataFrame) -> pd.DataFrame:
    """Compare candidate feature sets across chronological development windows.

    We start with 2023/24 as a validation window so that previous-season PPG is
    actually observable in the training data. 2025/26 is never used here.
    """
    rows = []

    for candidate_name, features in CANDIDATE_FEATURE_SETS.items():
        for validation_season in SELECTION_VALIDATION_SEASONS:
            train_seasons = seasons_before(df, validation_season)

            if LOCKED_TEST_SEASON in train_seasons:
                raise AssertionError("Locked test season entered model selection")

            train = df[df["Season"].isin(train_seasons)].copy()
            validation = df[df["Season"] == validation_season].copy()

            model = build_model()
            model.fit(train[features], train["FTR"])
            metrics = evaluate_model(model, validation, features)

            rows.append(
                {
                    "candidate": candidate_name,
                    "validation_season": validation_season,
                    "train_seasons": ",".join(train_seasons),
                    "feature_count": len(features),
                    "accuracy": metrics["accuracy"],
                    "log_loss": metrics["log_loss"],
                    "macro_f1": metrics["macro_f1"],
                    "draw_recall": metrics["recall"]["draw"],
                }
            )

    return pd.DataFrame(rows)


def choose_feature_set(comparison: pd.DataFrame) -> str:
    """Choose the lowest mean chronological validation log loss."""
    summary = (
        comparison.groupby("candidate", as_index=False)
        .agg(
            mean_log_loss=("log_loss", "mean"),
            mean_accuracy=("accuracy", "mean"),
            mean_macro_f1=("macro_f1", "mean"),
        )
        .sort_values(["mean_log_loss", "candidate"])
        .reset_index(drop=True)
    )
    return str(summary.loc[0, "candidate"])


def probability_baseline_metrics(
    train: pd.DataFrame,
    validation: pd.DataFrame,
) -> Dict[str, float]:
    """Training-frequency probability baseline and always-home accuracy."""
    frequencies = train["FTR"].value_counts(normalize=True)
    class_order = ["A", "D", "H"]
    probabilities = np.tile(
        [float(frequencies[label]) for label in class_order],
        (len(validation), 1),
    )

    return {
        "always_home_accuracy": float((validation["FTR"] == "H").mean()),
        "training_frequency_log_loss": float(
            log_loss(validation["FTR"], probabilities, labels=class_order)
        ),
    }


def save_json(path: Path, payload: Dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    df = load_dataset()

    # Chronology guard. We inspect dates/counts only for the locked test season;
    # its labels are never used for fitting, selection, or evaluation here.
    train = df[df["Season"].isin(TRAIN_SEASONS)].copy()
    validation = df[df["Season"] == VALIDATION_SEASON].copy()
    locked_test_rows = df[df["Season"] == LOCKED_TEST_SEASON].copy()

    if train.empty or validation.empty or locked_test_rows.empty:
        raise ValueError("Expected train/validation/locked-test seasons are missing")

    if train["Date"].max() >= validation["Date"].min():
        raise AssertionError("Training period overlaps validation period")
    if validation["Date"].max() >= locked_test_rows["Date"].min():
        raise AssertionError("Validation period overlaps locked test period")

    print("=" * 72)
    print("FIXTUREIQ STAGE 5 - OUTCOME MODEL")
    print("=" * 72)
    print("Train seasons:", ", ".join(TRAIN_SEASONS))
    print("Validation season:", VALIDATION_SEASON)
    print("Locked final test season:", LOCKED_TEST_SEASON, "(NOT EVALUATED)")

    comparison = compare_feature_sets(df)
    selected_name = choose_feature_set(comparison)
    selected_features = CANDIDATE_FEATURE_SETS[selected_name]

    summary = (
        comparison.groupby("candidate", as_index=False)
        .agg(
            mean_log_loss=("log_loss", "mean"),
            mean_accuracy=("accuracy", "mean"),
            mean_macro_f1=("macro_f1", "mean"),
        )
        .sort_values("mean_log_loss")
    )

    print("\nChronological feature-set comparison:")
    print(
        comparison[
            [
                "candidate",
                "validation_season",
                "accuracy",
                "log_loss",
                "draw_recall",
            ]
        ].to_string(
            index=False,
            formatters={
                "accuracy": lambda x: f"{x:.4f}",
                "log_loss": lambda x: f"{x:.4f}",
                "draw_recall": lambda x: f"{x:.4f}",
            },
        )
    )

    print("\nMean development performance:")
    print(
        summary.to_string(
            index=False,
            formatters={
                "mean_log_loss": lambda x: f"{x:.4f}",
                "mean_accuracy": lambda x: f"{x:.4f}",
                "mean_macro_f1": lambda x: f"{x:.4f}",
            },
        )
    )
    print("\nSelected feature set:", selected_name)
    for feature in selected_features:
        print(" -", feature)

    model = build_model()
    model.fit(train[selected_features], train["FTR"])

    validation_metrics = evaluate_model(model, validation, selected_features)
    baseline_metrics = probability_baseline_metrics(train, validation)

    # Explicit early-season diagnostic: both clubs have fewer than five current
    # season matches before the fixture. This directly tests the August problem.
    early_validation = validation[
        (validation["HomeGamesPlayedBefore"] < 5)
        & (validation["AwayGamesPlayedBefore"] < 5)
    ].copy()
    early_metrics = evaluate_model(model, early_validation, selected_features)

    print("\n2024/25 validation metrics:")
    print(f" Accuracy: {validation_metrics['accuracy']:.4f}")
    print(f" Log loss: {validation_metrics['log_loss']:.4f}")
    print(f" Macro F1: {validation_metrics['macro_f1']:.4f}")
    print(f" Draw recall: {validation_metrics['recall']['draw']:.4f}")
    print(f" Multiclass Brier: {validation_metrics['multiclass_brier']:.4f}")
    print(" Confusion matrix [H, D, A]:")
    print(np.array(validation_metrics["confusion_matrix"]))

    print("\nEarly-season validation (<5 matches played by both teams):")
    print(" Matches:", early_metrics["matches"])
    print(f" Accuracy: {early_metrics['accuracy']:.4f}")
    print(f" Log loss: {early_metrics['log_loss']:.4f}")

    print("\nBaselines:")
    print(
        f" Always-home accuracy: {baseline_metrics['always_home_accuracy']:.4f}"
    )
    print(
        " Training-frequency log loss: "
        f"{baseline_metrics['training_frequency_log_loss']:.4f}"
    )

    # Save Stage 5 development artifacts. We intentionally do NOT refit using
    # 2024/25 yet, because 2025/26 remains locked until the broader pipeline is
    # finalized (including Stage 6 calibration/scoreline work).
    joblib.dump(model, MODEL_DIR / "outcome_model.joblib")
    (MODEL_DIR / "feature_columns.json").write_text(
        json.dumps(selected_features, indent=2), encoding="utf-8"
    )

    comparison_records = json.loads(comparison.to_json(orient="records"))
    summary_records = json.loads(summary.to_json(orient="records"))

    metrics_payload: Dict[str, object] = {
        "model_version": MODEL_VERSION,
        "selected_candidate": selected_name,
        "selection_windows": SELECTION_VALIDATION_SEASONS,
        "candidate_comparison": comparison_records,
        "candidate_summary": summary_records,
        "validation": {
            "season": VALIDATION_SEASON,
            **validation_metrics,
        },
        "early_season_validation": {
            "definition": "both teams have fewer than 5 current-season matches before kickoff",
            **early_metrics,
        },
        "baselines": baseline_metrics,
        "locked_test": {
            "season": LOCKED_TEST_SEASON,
            "status": "locked_not_evaluated",
            "metrics": None,
        },
    }
    save_json(MODEL_DIR / "metrics.json", metrics_payload)

    metadata_payload: Dict[str, object] = {
        "model_version": MODEL_VERSION,
        "model_status": "stage5_development",
        "model_type": "multinomial_logistic_regression_pipeline",
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": str(DATA_FILE.relative_to(ROOT)),
        "training_seasons": TRAIN_SEASONS,
        "training_date_start": train["Date"].min().date().isoformat(),
        "training_date_end": train["Date"].max().date().isoformat(),
        "validation_season": VALIDATION_SEASON,
        "locked_test_season": LOCKED_TEST_SEASON,
        "test_season_evaluated": False,
        "selected_feature_set": selected_name,
        "feature_columns": selected_features,
        "target": "FTR",
        "classes": list(model.classes_),
        "probability_calibrated": False,
        "calibration_status": "deferred_until_stage6/final_pipeline_validation",
        "excluded_from_core_model": EXCLUDED_CONTEXT_FEATURE_GROUPS,
        "bookmaker_odds_policy": "excluded_from_training; optional external benchmark only",
        "missing_value_policy": "training-median imputation with missingness indicators",
        "leakage_policy": "pre-match features only; target result enters rolling history after feature snapshot",
    }
    save_json(MODEL_DIR / "model_metadata.json", metadata_payload)

    print("\nSaved Stage 5 artifacts:")
    for filename in [
        "outcome_model.joblib",
        "feature_columns.json",
        "metrics.json",
        "model_metadata.json",
    ]:
        print(" -", MODEL_DIR / filename)

    print("\n2025/26 remains LOCKED. No test metric was calculated.")


if __name__ == "__main__":
    main()

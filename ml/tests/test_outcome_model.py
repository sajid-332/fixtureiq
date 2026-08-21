import json
from pathlib import Path

import numpy as np

from ml.models.train_outcome_model import (
    CANDIDATE_FEATURE_SETS,
    LOCKED_TEST_SEASON,
    TRAIN_SEASONS,
    VALIDATION_SEASON,
    build_model,
    choose_feature_set,
    compare_feature_sets,
    evaluate_model,
    load_dataset,
    main,
)


ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "ml/models"


def test_model_selection_never_uses_locked_test_season():
    df = load_dataset()
    comparison = compare_feature_sets(df)

    assert LOCKED_TEST_SEASON not in set(comparison["validation_season"])
    assert not comparison["train_seasons"].str.contains(LOCKED_TEST_SEASON).any()


def test_outcome_probabilities_sum_to_one():
    df = load_dataset()
    comparison = compare_feature_sets(df)
    selected = choose_feature_set(comparison)
    features = CANDIDATE_FEATURE_SETS[selected]

    train = df[df["Season"].isin(TRAIN_SEASONS)]
    validation = df[df["Season"] == VALIDATION_SEASON].head(25)

    model = build_model()
    model.fit(train[features], train["FTR"])
    probabilities = model.predict_proba(validation[features])

    np.testing.assert_allclose(probabilities.sum(axis=1), 1.0, atol=1e-10)


def test_validation_metrics_are_finite():
    df = load_dataset()
    comparison = compare_feature_sets(df)
    selected = choose_feature_set(comparison)
    features = CANDIDATE_FEATURE_SETS[selected]

    train = df[df["Season"].isin(TRAIN_SEASONS)]
    validation = df[df["Season"] == VALIDATION_SEASON]

    model = build_model()
    model.fit(train[features], train["FTR"])
    metrics = evaluate_model(model, validation, features)

    assert np.isfinite(metrics["log_loss"])
    assert 0 <= metrics["accuracy"] <= 1
    assert 0 <= metrics["multiclass_brier"] <= 2


def test_training_workflow_saves_artifacts_without_test_metrics():
    main()

    expected = [
        "outcome_model.joblib",
        "feature_columns.json",
        "metrics.json",
        "model_metadata.json",
    ]
    for filename in expected:
        assert (MODEL_DIR / filename).exists()

    metrics = json.loads((MODEL_DIR / "metrics.json").read_text(encoding="utf-8"))
    metadata = json.loads(
        (MODEL_DIR / "model_metadata.json").read_text(encoding="utf-8")
    )

    assert metrics["locked_test"]["season"] == LOCKED_TEST_SEASON
    assert metrics["locked_test"]["status"] == "locked_not_evaluated"
    assert metrics["locked_test"]["metrics"] is None
    assert metadata["test_season_evaluated"] is False

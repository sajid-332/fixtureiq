from pathlib import Path

import numpy as np
import pandas as pd

from ml.features.historical_strength import add_historical_strength_features


ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_FILE = ROOT / "data/historical/processed/epl_historical.csv"
STAGE4_FILE = ROOT / "data/historical/processed/epl_stage4_features.csv"


def load_inputs():
    historical = pd.read_csv(HISTORICAL_FILE)
    stage4 = pd.read_csv(STAGE4_FILE)
    historical["Date"] = pd.to_datetime(historical["Date"])
    stage4["Date"] = pd.to_datetime(stage4["Date"])
    return historical, stage4


def target_row(frame, date, home, away):
    rows = frame[
        (frame["Date"] == pd.Timestamp(date))
        & (frame["HomeTeam"] == home)
        & (frame["AwayTeam"] == away)
    ]
    assert len(rows) == 1
    return rows.iloc[0]


def test_target_result_cannot_change_its_historical_strength_features():
    historical, stage4 = load_inputs()
    original = add_historical_strength_features(stage4, historical)

    date = "2024-08-17"
    home = "Arsenal"
    away = "Wolverhampton Wanderers"

    mutated_historical = historical.copy()
    mask = (
        (mutated_historical["Date"] == pd.Timestamp(date))
        & (mutated_historical["HomeTeam"] == home)
        & (mutated_historical["AwayTeam"] == away)
    )
    assert mask.sum() == 1
    old_result = mutated_historical.loc[mask, "FTR"].iloc[0]
    mutated_historical.loc[mask, "FTR"] = "A" if old_result != "A" else "H"

    mutated = add_historical_strength_features(stage4, mutated_historical)

    columns = [
        "HomePreviousSeasonPPG",
        "AwayPreviousSeasonPPG",
        "HomePreviousSeasonDataAvailable",
        "AwayPreviousSeasonDataAvailable",
        "HomeCrossSeasonRecentPPG",
        "AwayCrossSeasonRecentPPG",
        "HomeCrossSeasonMatchesUsed",
        "AwayCrossSeasonMatchesUsed",
    ]

    original_values = target_row(original, date, home, away)[columns]
    mutated_values = target_row(mutated, date, home, away)[columns]
    pd.testing.assert_series_equal(
        original_values,
        mutated_values,
        check_names=False,
    )


def test_promoted_team_has_no_previous_season_epl_ppg():
    historical, stage4 = load_inputs()
    features = add_historical_strength_features(stage4, historical)

    row = target_row(
        features,
        "2024-08-17",
        "Ipswich Town",
        "Liverpool",
    )

    assert np.isnan(row["HomePreviousSeasonPPG"])
    assert row["HomePreviousSeasonDataAvailable"] == 0


def test_cross_season_form_does_not_bridge_a_relegation_gap():
    historical, stage4 = load_inputs()
    features = add_historical_strength_features(stage4, historical)

    # Leicester City appears in 2022/23, is absent in 2023/24, then returns in
    # 2024/25. Its old EPL form must not be carried across that missing season.
    row = target_row(
        features,
        "2024-08-19",
        "Leicester City",
        "Tottenham Hotspur",
    )

    assert row["HomeCrossSeasonMatchesUsed"] == 0
    assert np.isnan(row["HomeCrossSeasonRecentPPG"])


def test_incumbent_team_carries_immediate_previous_season_history():
    historical, stage4 = load_inputs()
    features = add_historical_strength_features(stage4, historical)

    row = target_row(
        features,
        "2024-08-17",
        "Arsenal",
        "Wolverhampton Wanderers",
    )

    assert row["HomePreviousSeasonDataAvailable"] == 1
    assert row["HomeCrossSeasonMatchesUsed"] == 5
    assert 0 <= row["HomePreviousSeasonPPG"] <= 3
    assert 0 <= row["HomeCrossSeasonRecentPPG"] <= 3


def test_historical_strength_provides_early_season_fallback():
    historical, stage4 = load_inputs()
    features = add_historical_strength_features(stage4, historical)

    row = target_row(
        features,
        "2024-08-17",
        "Arsenal",
        "Wolverhampton Wanderers",
    )

    # Stage 3 last-five resets at the season boundary, so it is missing here.
    assert np.isnan(row["HomeLast5Points"])
    # The new historical prior remains available before Matchweek 1.
    assert not np.isnan(row["HomePreviousSeasonPPG"])

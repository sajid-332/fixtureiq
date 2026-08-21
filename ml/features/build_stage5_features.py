"""Build the Stage 5 development dataset from the completed Stage 4 dataset."""

from pathlib import Path

import pandas as pd

try:
    from ml.features.historical_strength import (
        HISTORICAL_STRENGTH_COLUMNS,
        add_historical_strength_features,
    )
except ModuleNotFoundError:  # direct execution: python ml/features/...
    from historical_strength import (  # type: ignore
        HISTORICAL_STRENGTH_COLUMNS,
        add_historical_strength_features,
    )


ROOT = Path(__file__).resolve().parents[2]
STAGE4_FILE = ROOT / "data/historical/processed/epl_stage4_features.csv"
HISTORICAL_FILE = ROOT / "data/historical/processed/epl_historical.csv"
OUTPUT_FILE = ROOT / "data/historical/processed/epl_stage5_features.csv"


def main() -> None:
    stage4 = pd.read_csv(STAGE4_FILE)
    historical = pd.read_csv(HISTORICAL_FILE)

    stage4["Date"] = pd.to_datetime(stage4["Date"], errors="raise")
    historical["Date"] = pd.to_datetime(historical["Date"], errors="raise")

    stage5 = add_historical_strength_features(stage4, historical)

    if len(stage5) != len(stage4):
        raise AssertionError("Stage 5 feature build changed the number of matches")

    for column in [
        "HomePreviousSeasonDataAvailable",
        "AwayPreviousSeasonDataAvailable",
    ]:
        values = set(stage5[column].dropna().unique())
        if not values.issubset({0, 1}):
            raise AssertionError(f"{column} must contain only 0/1")

    for column in [
        "HomeCrossSeasonMatchesUsed",
        "AwayCrossSeasonMatchesUsed",
    ]:
        if not stage5[column].between(0, 5).all():
            raise AssertionError(f"{column} must be between 0 and 5")

    for column in [
        "HomeCrossSeasonRecentPPG",
        "AwayCrossSeasonRecentPPG",
        "HomePreviousSeasonPPG",
        "AwayPreviousSeasonPPG",
    ]:
        values = stage5[column].dropna()
        if not values.between(0, 3).all():
            raise AssertionError(f"{column} must be between 0 and 3")

    stage5 = stage5.sort_values("Date").reset_index(drop=True)
    stage5.to_csv(OUTPUT_FILE, index=False)

    print("Stage 5 feature dataset created successfully!")
    print("Matches:", len(stage5))
    print("Columns:", len(stage5.columns))
    print("Added historical-strength columns:")
    for column in HISTORICAL_STRENGTH_COLUMNS:
        print(" -", column)

    print("\nMissing historical-strength values by season:")
    summary_columns = [
        "HomePreviousSeasonPPG",
        "AwayPreviousSeasonPPG",
        "HomeCrossSeasonRecentPPG",
        "AwayCrossSeasonRecentPPG",
    ]
    print(
        stage5.groupby("Season")[summary_columns]
        .agg(lambda series: int(series.isna().sum()))
        .to_string()
    )
    print("\nSaved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()

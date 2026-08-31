"""
FixtureIQ Stage 7.3.3
Historical Dataset Quality Control.

Checks:
- Schema
- Fixture IDs
- Seasons
- Teams
- Dates
- Scores
- Match status
- Missing critical values
- Duplicate fixture IDs

The script reports problems and does not silently modify
the historical dataset.
"""

import json
import sys
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BASE_DIR),
)

from backend.providers.historical import (
    HISTORICAL_FILE,
    HISTORICAL_COLUMNS,
    load_historical_fixtures,
)


REPORT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "historical_quality_report.json"
)


CRITICAL_COLUMNS = [
    "fixture_id",
    "season",
    "date",
    "home_team_id",
    "home_team_name",
    "away_team_id",
    "away_team_name",
]


def main():

    print("=" * 50)
    print(
        "FixtureIQ Stage 7.3.3"
    )
    print(
        "Historical Dataset Quality Control"
    )
    print("=" * 50)

    if not HISTORICAL_FILE.exists():

        print(
            "\nHistorical dataset: FAIL"
        )

        print(
            f"Missing file: {HISTORICAL_FILE}"
        )

        sys.exit(1)

    dataframe = pd.read_csv(
        HISTORICAL_FILE
    )

    total = len(dataframe)

    print(
        f"\nDataset: {HISTORICAL_FILE}"
    )

    print(
        f"Total fixtures: {total}"
    )

    # ========================================================
    # Schema
    # ========================================================

    expected_columns = set(
        HISTORICAL_COLUMNS
    )

    actual_columns = set(
        dataframe.columns
    )

    missing_columns = sorted(
        expected_columns
        - actual_columns
    )

    schema_pass = (
        len(missing_columns) == 0
    )

    print(
        "\nSchema validation: "
        f"{'PASS' if schema_pass else 'FAIL'}"
    )

    if missing_columns:

        print(
            f"Missing columns: "
            f"{missing_columns}"
        )

    # ========================================================
    # Fixture IDs
    # ========================================================

    fixture_id_numeric = pd.to_numeric(
        dataframe["fixture_id"],
        errors="coerce",
    )

    missing_fixture_ids = int(
        fixture_id_numeric.isna().sum()
    )

    duplicate_fixture_ids = int(
        dataframe["fixture_id"]
        .duplicated()
        .sum()
    )

    fixture_id_pass = (
        missing_fixture_ids == 0
        and
        duplicate_fixture_ids == 0
    )

    print(
        "\nFixture ID validation: "
        f"{'PASS' if fixture_id_pass else 'FAIL'}"
    )

    print(
        f"Missing fixture IDs: "
        f"{missing_fixture_ids}"
    )

    print(
        f"Duplicate fixture IDs: "
        f"{duplicate_fixture_ids}"
    )

    # ========================================================
    # Season
    # ========================================================

    season_numeric = pd.to_numeric(
        dataframe["season"],
        errors="coerce",
    )

    missing_seasons = int(
        season_numeric.isna().sum()
    )

    invalid_seasons = int(
        (
            (season_numeric < 2000)
            |
            (season_numeric > 2100)
        )
        .fillna(False)
        .sum()
    )

    season_pass = (
        missing_seasons == 0
        and
        invalid_seasons == 0
    )

    print(
        "\nSeason validation: "
        f"{'PASS' if season_pass else 'FAIL'}"
    )

    print(
        f"Missing seasons: "
        f"{missing_seasons}"
    )

    print(
        f"Invalid seasons: "
        f"{invalid_seasons}"
    )

    # ========================================================
    # Teams
    # ========================================================

    home_missing = int(
        dataframe["home_team_name"]
        .isna()
        .sum()
    )

    away_missing = int(
        dataframe["away_team_name"]
        .isna()
        .sum()
    )

    same_team = int(
        (
            dataframe["home_team_id"]
            == dataframe["away_team_id"]
        )
        .fillna(False)
        .sum()
    )

    teams_pass = (
        home_missing == 0
        and
        away_missing == 0
        and
        same_team == 0
    )

    print(
        "\nTeam validation: "
        f"{'PASS' if teams_pass else 'FAIL'}"
    )

    print(
        f"Missing home teams: "
        f"{home_missing}"
    )

    print(
        f"Missing away teams: "
        f"{away_missing}"
    )

    print(
        f"Home = Away records: "
        f"{same_team}"
    )

    # ========================================================
    # Dates
    # ========================================================

    dates = pd.to_datetime(
        dataframe["date"],
        errors="coerce",
        utc=True,
    )

    invalid_dates = int(
        dates.isna().sum()
    )

    date_pass = (
        invalid_dates == 0
    )

    print(
        "\nDate validation: "
        f"{'PASS' if date_pass else 'FAIL'}"
    )

    print(
        f"Invalid dates: "
        f"{invalid_dates}"
    )

    # ========================================================
    # Scores
    # ========================================================

    home_goals = pd.to_numeric(
        dataframe["home_goals"],
        errors="coerce",
    )

    away_goals = pd.to_numeric(
        dataframe["away_goals"],
        errors="coerce",
    )

    negative_home_goals = int(
        (home_goals < 0)
        .fillna(False)
        .sum()
    )

    negative_away_goals = int(
        (away_goals < 0)
        .fillna(False)
        .sum()
    )

    score_pass = (
        negative_home_goals == 0
        and
        negative_away_goals == 0
    )

    print(
        "\nScore validation: "
        f"{'PASS' if score_pass else 'FAIL'}"
    )

    print(
        f"Negative home goals: "
        f"{negative_home_goals}"
    )

    print(
        f"Negative away goals: "
        f"{negative_away_goals}"
    )

    # ========================================================
    # Status
    # ========================================================

    status_missing = int(
        dataframe["status_short"]
        .isna()
        .sum()
    )

    status_pass = (
        status_missing == 0
    )

    print(
        "\nStatus validation: "
        f"{'PASS' if status_pass else 'FAIL'}"
    )

    print(
        f"Missing status: "
        f"{status_missing}"
    )

    # ========================================================
    # Critical missing values
    # ========================================================

    missing_critical = {}

    for column in CRITICAL_COLUMNS:

        missing_critical[column] = int(
            dataframe[column]
            .isna()
            .sum()
        )

    total_critical_missing = sum(
        missing_critical.values()
    )

    critical_pass = (
        total_critical_missing == 0
    )

    print(
        "\nCritical missing values: "
        f"{'PASS' if critical_pass else 'FAIL'}"
    )

    print(
        f"Total critical missing values: "
        f"{total_critical_missing}"
    )

    # ========================================================
    # Season summary
    # ========================================================

    season_summary = {}

    for season, group in dataframe.groupby(
        "season"
    ):

        season_summary[str(int(season))] = {
            "fixtures": int(len(group)),
            "unique_fixture_ids": int(
                group["fixture_id"].nunique()
            ),
        }

    # ========================================================
    # Overall quality
    # ========================================================

    checks = {
        "schema": schema_pass,
        "fixture_ids": fixture_id_pass,
        "seasons": season_pass,
        "teams": teams_pass,
        "dates": date_pass,
        "scores": score_pass,
        "status": status_pass,
        "critical_missing_values": critical_pass,
    }

    passed_checks = sum(
        bool(value)
        for value in checks.values()
    )

    quality_percentage = round(
        (
            passed_checks
            /
            len(checks)
        )
        * 100,
        2,
    )

    overall_pass = all(
        checks.values()
    )

    # A stricter valid-record calculation.

    valid_mask = (
        fixture_id_numeric.notna()
        &
        season_numeric.notna()
        &
        dates.notna()
        &
        dataframe["home_team_name"].notna()
        &
        dataframe["away_team_name"].notna()
        &
        home_goals.notna()
        &
        away_goals.notna()
    )

    valid_records = int(
        valid_mask.sum()
    )

    invalid_records = (
        total
        -
        valid_records
    )

    # ========================================================
    # Report
    # ========================================================

    report = {
        "stage": "7.3.3",
        "dataset": str(
            HISTORICAL_FILE
        ),
        "total_fixtures": total,
        "valid_fixtures": valid_records,
        "invalid_fixtures": invalid_records,
        "duplicate_fixture_ids": duplicate_fixture_ids,
        "missing_critical_values":
            total_critical_missing,
        "quality_percentage":
            quality_percentage,
        "checks": checks,
        "season_summary":
            season_summary,
        "details": {
            "missing_fixture_ids":
                missing_fixture_ids,
            "missing_seasons":
                missing_seasons,
            "invalid_seasons":
                invalid_seasons,
            "missing_home_teams":
                home_missing,
            "missing_away_teams":
                away_missing,
            "same_team_records":
                same_team,
            "invalid_dates":
                invalid_dates,
            "negative_home_goals":
                negative_home_goals,
            "negative_away_goals":
                negative_away_goals,
            "missing_status":
                status_missing,
            "missing_critical_fields":
                missing_critical,
        },
        "overall_pass":
            overall_pass,
    }

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with REPORT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # ========================================================
    # Final output
    # ========================================================

    print(
        "\n" + "=" * 50
    )

    print(
        "QUALITY SUMMARY"
    )

    print(
        "=" * 50
    )

    print(
        f"Total fixtures: "
        f"{total}"
    )

    print(
        f"Valid fixtures: "
        f"{valid_records}"
    )

    print(
        f"Invalid fixtures: "
        f"{invalid_records}"
    )

    print(
        f"Duplicate fixtures: "
        f"{duplicate_fixture_ids}"
    )

    print(
        f"Quality checks passed: "
        f"{passed_checks}/{len(checks)}"
    )

    print(
        f"Data quality: "
        f"{quality_percentage}%"
    )

    print(
        f"\nReport saved:"
    )

    print(
        REPORT_FILE
    )

    print(
        "\nSTAGE 7.3.3: "
        f"{'PASS' if overall_pass else 'FAIL'}"
    )

    if not overall_pass:

        sys.exit(1)


if __name__ == "__main__":
    main()
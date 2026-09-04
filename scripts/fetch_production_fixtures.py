"""
FixtureIQ Stage 7.8.2
Production Upcoming Fixture Fetcher.

Fetches ONLY the configured production EPL season.

Important:
- Never silently falls back to an old season.
- Never uses completed fixtures as upcoming fixtures.
- Never uses final-test artifacts.
- Removes stale upcoming_fixtures.csv if the provider
  cannot provide valid current production fixtures.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BASE_DIR),
)


from backend.config import (
    API_FOOTBALL_LEAGUE_ID,
    API_FOOTBALL_SEASON,
)

from backend.providers.api_football import (
    APIFootballProvider,
    APIFootballError,
)


OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "production"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "upcoming_fixtures.csv"
)

REPORT_FILE = (
    OUTPUT_DIR
    / "production_fixture_fetch_report.json"
)


# Fixtures that are genuinely candidates for future prediction.
UPCOMING_STATUSES = {
    "NS",     # Not Started
    "TBD",    # Time To Be Defined
    "PST",    # Postponed / rescheduled
}


def remove_stale_output() -> None:

    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()


def write_report(
    status: str,
    message: str,
    fixture_count: int = 0,
) -> None:

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    report = {
        "stage": "7.8.2",
        "component": "production_fixture_fetch",
        "status": status,
        "message": message,
        "league_id": API_FOOTBALL_LEAGUE_ID,
        "configured_season": API_FOOTBALL_SEASON,
        "fixture_count": fixture_count,
        "fallback_season_used": False,
        "completed_fixtures_used": False,
        "final_test_artifacts_used": False,
    }

    with REPORT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
        )


def plan_restricted(
    payload: dict,
) -> bool:

    errors = payload.get(
        "errors",
        {},
    )

    return (
        isinstance(errors, dict)
        and bool(errors.get("plan"))
    )


def normalize_upcoming(
    payload: dict,
) -> pd.DataFrame:

    response = payload.get(
        "response",
        [],
    )

    if not isinstance(response, list):
        raise RuntimeError(
            "API response field is not a list."
        )

    now = pd.Timestamp.now(
        tz="UTC"
    )

    rows = []

    for item in response:

        if not isinstance(item, dict):
            continue

        fixture = item.get(
            "fixture",
            {},
        )

        league = item.get(
            "league",
            {},
        )

        teams = item.get(
            "teams",
            {},
        )

        status = fixture.get(
            "status",
            {},
        )

        home = teams.get(
            "home",
            {},
        )

        away = teams.get(
            "away",
            {},
        )

        fixture_id = fixture.get(
            "id"
        )

        fixture_date = pd.to_datetime(
            fixture.get("date"),
            errors="coerce",
            utc=True,
        )

        status_short = status.get(
            "short"
        )

        home_team_id = home.get(
            "id"
        )

        away_team_id = away.get(
            "id"
        )

        home_team_name = home.get(
            "name"
        )

        away_team_name = away.get(
            "name"
        )

        if fixture_id is None:
            continue

        if pd.isna(fixture_date):
            continue

        # Do not include historical/completed fixtures.
        if fixture_date <= now:
            continue

        # Only genuine future statuses.
        if status_short not in UPCOMING_STATUSES:
            continue

        if (
            home_team_id is None
            or away_team_id is None
            or not home_team_name
            or not away_team_name
        ):
            continue

        rows.append(
            {
                "fixture_id":
                    int(fixture_id),

                "date":
                    fixture_date.isoformat(),

                "timestamp":
                    fixture.get("timestamp"),

                "timezone":
                    fixture.get("timezone", "UTC"),

                "status_short":
                    status_short,

                "status_long":
                    status.get("long"),

                "status_elapsed":
                    status.get("elapsed"),

                "league_id":
                    league.get("id"),

                "league_name":
                    league.get("name"),

                "country":
                    league.get("country"),

                "season":
                    league.get(
                        "season",
                        API_FOOTBALL_SEASON,
                    ),

                "round":
                    league.get("round"),

                "home_team_id":
                    int(home_team_id),

                "home_team_name":
                    str(home_team_name),

                "home_team_code":
                    home.get("code"),

                "away_team_id":
                    int(away_team_id),

                "away_team_name":
                    str(away_team_name),

                "away_team_code":
                    away.get("code"),
            }
        )

    dataframe = pd.DataFrame(
        rows
    )

    if dataframe.empty:
        return dataframe

    dataframe["date"] = pd.to_datetime(
        dataframe["date"],
        utc=True,
    )

    dataframe = (
        dataframe
        .sort_values(
            [
                "date",
                "fixture_id",
            ]
        )
        .drop_duplicates(
            subset=[
                "fixture_id",
            ],
            keep="first",
        )
        .reset_index(drop=True)
    )

    return dataframe


def main():

    print("=" * 55)
    print("FixtureIQ Stage 7.8.2")
    print("Production Upcoming Fixture Fetch")
    print("=" * 55)

    print(
        f"\nLeague ID: {API_FOOTBALL_LEAGUE_ID}"
    )

    print(
        f"Configured season: {API_FOOTBALL_SEASON}"
    )

    print(
        "Season fallback allowed: NO"
    )

    provider = APIFootballProvider()

    print(
        "\nRequesting configured production season..."
    )

    try:

        payload = provider.get_fixtures(
            API_FOOTBALL_LEAGUE_ID,
            API_FOOTBALL_SEASON,
        )

    except APIFootballError as exc:

        remove_stale_output()

        write_report(
            status="PROVIDER_ERROR",
            message=str(exc),
        )

        print(
            "\nPRODUCTION FIXTURE FETCH: FAIL"
        )

        print(
            f"Provider error: {exc}"
        )

        sys.exit(1)

    if not isinstance(
        payload,
        dict,
    ):

        remove_stale_output()

        write_report(
            status="INVALID_RESPONSE",
            message="Provider returned non-dictionary payload.",
        )

        raise RuntimeError(
            "Provider returned invalid payload."
        )

    if plan_restricted(
        payload
    ):

        remove_stale_output()

        errors = payload.get(
            "errors",
            {},
        )

        message = str(
            errors.get(
                "plan",
                "Production season unavailable on current plan.",
            )
        )

        write_report(
            status="PROVIDER_PLAN_BLOCKED",
            message=message,
        )

        print(
            "\nProvider plan limitation: DETECTED"
        )

        print(
            f"Message: {message}"
        )

        print(
            "\nNo fallback season was used."
        )

        print(
            "No stale production fixture file was retained."
        )

        print(
            "\nPRODUCTION FIXTURE FETCH: BLOCKED"
        )

        sys.exit(2)

    fixtures = normalize_upcoming(
        payload
    )

    print(
        f"\nValid upcoming fixtures: {len(fixtures)}"
    )

    if fixtures.empty:

        remove_stale_output()

        write_report(
            status="NO_UPCOMING_FIXTURES",
            message=(
                "No genuine future EPL fixtures were "
                "available for the configured season."
            ),
        )

        print(
            "\nNo valid upcoming fixtures found."
        )

        print(
            "PRODUCTION FIXTURE FETCH: NO DATA"
        )

        sys.exit(3)

    if not fixtures[
        "fixture_id"
    ].is_unique:

        raise RuntimeError(
            "Production fixture IDs are not unique."
        )

    dates = pd.to_datetime(
        fixtures["date"],
        utc=True,
    )

    if not dates.is_monotonic_increasing:

        raise RuntimeError(
            "Production fixtures are not chronological."
        )

    if not set(
        fixtures[
            "status_short"
        ].unique()
    ).issubset(
        UPCOMING_STATUSES
    ):

        raise RuntimeError(
            "Invalid production fixture status detected."
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    fixtures.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    write_report(
        status="PASS",
        message="Production upcoming fixtures fetched successfully.",
        fixture_count=len(fixtures),
    )

    print(
        "\nFixture validation: PASS"
    )

    print(
        "Completed fixtures included: NO"
    )

    print(
        "Fallback season used: NO"
    )

    print(
        "Final-test artifacts used: NO"
    )

    print(
        f"\nSaved:\n{OUTPUT_FILE}"
    )

    print(
        "\n" + "=" * 55
    )

    print(
        "PRODUCTION FIXTURE FETCH: PASS"
    )

    print("=" * 55)


if __name__ == "__main__":
    main()
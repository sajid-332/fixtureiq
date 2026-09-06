"""
FixtureIQ Stage 7.8.2
Production Upcoming Fixture Fetcher.

Production fixture source:
    football-data.org

IMPORTANT:
- Uses production_history.csv for FixtureIQ team identities.
- Uses only configured production season.
- Never falls back to an older season.
- Saves only genuine future EPL fixtures.
- Never accesses consumed final-test evaluation artifacts.
- Never retrains, tunes, or selects a model.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd


# ============================================================
# Project root
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

sys.path.insert(
    0,
    str(BASE_DIR),
)


# ============================================================
# FixtureIQ imports
# ============================================================

from backend.config import (
    API_FOOTBALL_SEASON,
)

from backend.providers.football_data import (
    FootballDataProvider,
    FootballDataError,
)


# ============================================================
# Paths
# ============================================================

HISTORY_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "production"
    / "production_history.csv"
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


# ============================================================
# Provider statuses
# ============================================================

FUTURE_STATUSES = {
    "SCHEDULED",
    "TIMED",
    "POSTPONED",
}


# ============================================================
# Team aliases
# ============================================================

PROVIDER_ALIASES = {

    "Manchester City FC":
        "Manchester City",

    "Manchester United FC":
        "Manchester United",

    "Liverpool FC":
        "Liverpool",

    "Arsenal FC":
        "Arsenal",

    "Chelsea FC":
        "Chelsea",

    "Tottenham Hotspur FC":
        "Tottenham",

    "Newcastle United FC":
        "Newcastle",

    "Aston Villa FC":
        "Aston Villa",

    "West Ham United FC":
        "West Ham",

    "Everton FC":
        "Everton",

    "Fulham FC":
        "Fulham",

    "Brentford FC":
        "Brentford",

    "Crystal Palace FC":
        "Crystal Palace",

    "Brighton & Hove Albion FC":
        "Brighton",

    "Wolverhampton Wanderers FC":
        "Wolves",

    "AFC Bournemouth":
        "Bournemouth",

    "Nottingham Forest FC":
        "Nottingham Forest",

    "Leicester City FC":
        "Leicester",

    "Southampton FC":
        "Southampton",

    "Ipswich Town FC":
        "Ipswich",

    "Burnley FC":
        "Burnley",

    "Leeds United FC":
        "Leeds",

    "Sunderland AFC":
        "Sunderland",

    "Sheffield United FC":
        "Sheffield Utd",

    "Luton Town FC":
        "Luton",

    "Coventry City FC":
        "Coventry City",

    "Hull City AFC":
        "Hull City",
}


# ============================================================
# Helpers
# ============================================================

def deterministic_negative_id(
    namespace: str,
    value: str,
) -> int:

    raw = (
        f"{namespace}:{value}"
        .encode("utf-8")
    )

    digest = hashlib.sha256(
        raw
    ).hexdigest()

    return -int(
        digest[:12],
        16,
    )


def canonical_provider_name(
    provider_name,
    short_name=None,
) -> str:

    provider_name = (
        str(provider_name).strip()
        if provider_name
        else ""
    )

    short_name = (
        str(short_name).strip()
        if short_name
        else ""
    )

    if provider_name in PROVIDER_ALIASES:

        return PROVIDER_ALIASES[
            provider_name
        ]

    if short_name in PROVIDER_ALIASES:

        return PROVIDER_ALIASES[
            short_name
        ]

    candidate = (
        short_name
        or
        provider_name
    )

    if not candidate:

        raise ValueError(
            "Provider team name is missing."
        )

    for suffix in [
        " Football Club",
        " FC",
        " AFC",
    ]:

        if candidate.endswith(
            suffix
        ):

            candidate = candidate[
                :-len(suffix)
            ].strip()

    return candidate


def normalize_status(
    provider_status: str,
) -> str:

    if provider_status in {
        "SCHEDULED",
        "TIMED",
    }:

        return "NS"

    if provider_status == "POSTPONED":

        return "PST"

    raise ValueError(
        "Unsupported future fixture status: "
        f"{provider_status}"
    )


def load_internal_team_mapping() -> dict:

    if not HISTORY_FILE.exists():

        raise FileNotFoundError(
            "Production history does not exist.\n"
            "Run first:\n"
            "python scripts\\build_production_history.py"
        )

    history = pd.read_csv(
        HISTORY_FILE
    )

    if history.empty:

        raise RuntimeError(
            "Production history is empty."
        )

    required = {
        "home_team_id",
        "home_team_name",
        "away_team_id",
        "away_team_name",
    }

    missing = (
        required
        -
        set(history.columns)
    )

    if missing:

        raise RuntimeError(
            "Production history missing team fields: "
            f"{sorted(missing)}"
        )

    mapping = {}

    for _, row in history.iterrows():

        home_name = str(
            row["home_team_name"]
        ).strip()

        away_name = str(
            row["away_team_name"]
        ).strip()

        home_id = int(
            row["home_team_id"]
        )

        away_id = int(
            row["away_team_id"]
        )

        if (
            home_name in mapping
            and mapping[home_name] != home_id
        ):

            raise RuntimeError(
                "Conflicting team ID detected for "
                f"{home_name}."
            )

        if (
            away_name in mapping
            and mapping[away_name] != away_id
        ):

            raise RuntimeError(
                "Conflicting team ID detected for "
                f"{away_name}."
            )

        mapping[
            home_name
        ] = home_id

        mapping[
            away_name
        ] = away_id

    return mapping


def remove_stale_output():

    if OUTPUT_FILE.exists():

        OUTPUT_FILE.unlink()


def write_report(
    *,
    status: str,
    message: str,
    received: int = 0,
    upcoming: int = 0,
    known_teams: int = 0,
    new_teams: dict | None = None,
):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    report = {

        "stage":
            "7.8.2",

        "component":
            "production_fixture_fetch",

        "provider":
            "football-data.org",

        "configured_season":
            int(
                API_FOOTBALL_SEASON
            ),

        "status":
            status,

        "message":
            message,

        "provider_matches_received":
            int(received),

        "upcoming_fixture_count":
            int(upcoming),

        "known_production_history_teams":
            int(known_teams),

        "new_team_ids":
            new_teams or {},

        "fallback_season_used":
            False,

        "completed_fixtures_used":
            False,

        "final_test_evaluation_artifacts_used":
            False,

        "model_retrained":
            False,

        "model_reselected":
            False,

        "hyperparameter_tuned":
            False,
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


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 60)

    print(
        "FixtureIQ Stage 7.8.2"
    )

    print(
        "Production Upcoming Fixture Fetch"
    )

    print("=" * 60)

    print(
        "\nProvider: football-data.org"
    )

    print(
        f"Configured season: "
        f"{API_FOOTBALL_SEASON}"
    )

    print(
        "Fallback season: DISABLED"
    )

    # ========================================================
    # 1. Production history mapping
    # ========================================================

    print(
        "\n1. PRODUCTION TEAM IDENTITY"
    )

    internal_team_ids = (
        load_internal_team_mapping()
    )

    print(
        f"Production-history teams: "
        f"{len(internal_team_ids)}"
    )

    # ========================================================
    # 2. Provider request
    # ========================================================

    print(
        "\n2. PROVIDER REQUEST"
    )

    try:

        provider = (
            FootballDataProvider()
        )

        payload = (
            provider
            .get_premier_league_matches(
                int(
                    API_FOOTBALL_SEASON
                )
            )
        )

    except FootballDataError as exc:

        remove_stale_output()

        write_report(
            status="PROVIDER_ERROR",
            message=str(exc),
        )

        print(
            "Provider request: FAIL"
        )

        print(
            f"Error: {exc}"
        )

        sys.exit(1)

    matches = payload.get(
        "matches",
        [],
    )

    if not isinstance(
        matches,
        list,
    ):

        raise RuntimeError(
            "Provider response contains "
            "invalid matches field."
        )

    print(
        "Provider request: PASS"
    )

    print(
        f"Provider matches received: "
        f"{len(matches)}"
    )

    # ========================================================
    # 3. Normalize future fixtures
    # ========================================================

    print(
        "\n3. UPCOMING FIXTURE NORMALIZATION"
    )

    now = pd.Timestamp.now(
        tz="UTC"
    )

    rows = []

    new_team_ids = {}

    resolved_known_teams = set()

    for match in matches:

        if not isinstance(
            match,
            dict,
        ):

            continue

        provider_status = str(
            match.get(
                "status",
                "",
            )
        ).upper()

        if provider_status not in FUTURE_STATUSES:

            continue

        kickoff = pd.to_datetime(
            match.get(
                "utcDate"
            ),
            errors="coerce",
            utc=True,
        )

        if pd.isna(
            kickoff
        ):

            continue

        if kickoff <= now:

            continue

        home = match.get(
            "homeTeam",
            {},
        )

        away = match.get(
            "awayTeam",
            {},
        )

        home_name = (
            canonical_provider_name(
                home.get(
                    "name"
                ),
                home.get(
                    "shortName"
                ),
            )
        )

        away_name = (
            canonical_provider_name(
                away.get(
                    "name"
                ),
                away.get(
                    "shortName"
                ),
            )
        )

        # ----------------------------------------------------
        # Resolve home team
        # ----------------------------------------------------

        if home_name in internal_team_ids:

            home_id = int(
                internal_team_ids[
                    home_name
                ]
            )

            resolved_known_teams.add(
                home_name
            )

        else:

            home_id = (
                deterministic_negative_id(
                    "fixtureiq-team",
                    home_name,
                )
            )

            new_team_ids[
                home_name
            ] = home_id

        # ----------------------------------------------------
        # Resolve away team
        # ----------------------------------------------------

        if away_name in internal_team_ids:

            away_id = int(
                internal_team_ids[
                    away_name
                ]
            )

            resolved_known_teams.add(
                away_name
            )

        else:

            away_id = (
                deterministic_negative_id(
                    "fixtureiq-team",
                    away_name,
                )
            )

            new_team_ids[
                away_name
            ] = away_id

        provider_fixture_id = (
            match.get(
                "id"
            )
        )

        if provider_fixture_id is None:

            continue

        fixture_id = (
            deterministic_negative_id(
                "football-data-fixture",
                str(
                    provider_fixture_id
                ),
            )
        )

        competition = match.get(
            "competition",
            {},
        )

        matchday = match.get(
            "matchday"
        )

        rows.append(
            {
                "fixture_id":
                    fixture_id,

                "provider_fixture_id":
                    int(
                        provider_fixture_id
                    ),

                "provider":
                    "football-data.org",

                "date":
                    kickoff.isoformat(),

                "timestamp":
                    int(
                        kickoff.timestamp()
                    ),

                "timezone":
                    "UTC",

                "status_short":
                    normalize_status(
                        provider_status
                    ),

                "status_long":
                    provider_status,

                "status_elapsed":
                    None,

                "league_id":
                    39,

                "league_name":
                    competition.get(
                        "name",
                        "Premier League",
                    ),

                "country":
                    "England",

                "season":
                    int(
                        API_FOOTBALL_SEASON
                    ),

                "round":
                    (
                        f"Regular Season - {matchday}"
                        if matchday is not None
                        else None
                    ),

                "home_team_id":
                    home_id,

                "home_team_name":
                    home_name,

                "home_team_code":
                    home.get(
                        "tla"
                    ),

                "provider_home_team_id":
                    home.get(
                        "id"
                    ),

                "away_team_id":
                    away_id,

                "away_team_name":
                    away_name,

                "away_team_code":
                    away.get(
                        "tla"
                    ),

                "provider_away_team_id":
                    away.get(
                        "id"
                    ),
            }
        )

    fixtures = pd.DataFrame(
        rows
    )

    if fixtures.empty:

        remove_stale_output()

        write_report(
            status="NO_UPCOMING_FIXTURES",
            message=(
                "Provider returned no genuine "
                "future Premier League fixtures."
            ),
            received=len(matches),
        )

        print(
            "Valid upcoming fixtures: 0"
        )

        print(
            "\nPRODUCTION FIXTURE FETCH: NO DATA"
        )

        sys.exit(2)

    fixtures["date"] = pd.to_datetime(
        fixtures["date"],
        errors="raise",
        utc=True,
    )

    fixtures = (
        fixtures
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

    # ========================================================
    # 4. Integrity checks
    # ========================================================

    print(
        "\n4. FIXTURE INTEGRITY"
    )

    if not fixtures[
        "fixture_id"
    ].is_unique:

        raise RuntimeError(
            "Internal fixture IDs are not unique."
        )

    if not fixtures[
        "provider_fixture_id"
    ].is_unique:

        raise RuntimeError(
            "Provider fixture IDs are not unique."
        )

    if (
        fixtures["date"]
        <= now
    ).any():

        raise RuntimeError(
            "Past fixture detected in "
            "upcoming snapshot."
        )

    valid_internal_statuses = {
        "NS",
        "PST",
    }

    statuses = set(
        fixtures[
            "status_short"
        ].unique()
    )

    if not statuses.issubset(
        valid_internal_statuses
    ):

        raise RuntimeError(
            "Invalid normalized fixture status."
        )

    if (
        fixtures[
            "home_team_id"
        ]
        ==
        fixtures[
            "away_team_id"
        ]
    ).any():

        raise RuntimeError(
            "Fixture contains identical "
            "home and away team IDs."
        )

    print(
        f"Valid upcoming fixtures: "
        f"{len(fixtures)}"
    )

    print(
        "Fixture IDs unique: PASS"
    )

    print(
        "Provider fixture IDs unique: PASS"
    )

    print(
        "Future fixtures only: PASS"
    )

    print(
        "Upcoming status validation: PASS"
    )

    # ========================================================
    # 5. Team identity report
    # ========================================================

    print(
        "\n5. TEAM IDENTITY"
    )

    print(
        f"Known production-history teams resolved: "
        f"{len(resolved_known_teams)}"
    )

    print(
        f"New zero-state teams: "
        f"{len(new_team_ids)}"
    )

    if new_team_ids:

        for (
            team_name,
            team_id,
        ) in sorted(
            new_team_ids.items()
        ):

            print(
                f"  {team_name}: "
                f"{team_id}"
            )

    # ========================================================
    # 6. Save
    # ========================================================

    print(
        "\n6. SAVE ARTIFACTS"
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
        message=(
            "Current Premier League upcoming "
            "fixtures fetched successfully."
        ),
        received=len(matches),
        upcoming=len(fixtures),
        known_teams=len(
            resolved_known_teams
        ),
        new_teams=new_team_ids,
    )

    print(
        f"Upcoming fixtures:\n"
        f"{OUTPUT_FILE}"
    )

    print(
        f"\nReport:\n"
        f"{REPORT_FILE}"
    )

    # ========================================================
    # 7. Protection
    # ========================================================

    print(
        "\n7. PROTECTION"
    )

    print(
        "Completed fixtures included: NO"
    )

    print(
        "Fallback season used: NO"
    )

    print(
        "Final-test evaluation artifacts used: NO"
    )

    print(
        "Model retrained: NO"
    )

    print(
        "Model re-selected: NO"
    )

    print(
        "Hyperparameter tuning: NO"
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "PRODUCTION FIXTURE FETCH: PASS"
    )

    print("=" * 60)


if __name__ == "__main__":

    main()
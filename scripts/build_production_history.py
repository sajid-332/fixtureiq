"""
FixtureIQ Stage 7.8.2
Production Historical Context Builder.

Purpose
-------
Build the read-only historical context used for LIVE inference.

Sources:
1. Historical EPL 2023/24 + 2024/25
2. Completed EPL 2025/26 raw Football-Data file
3. Completed EPL 2026/27 matches from football-data.org

IMPORTANT:
- historical_fixtures.csv is NEVER modified.
- final-test evaluation artifacts are NEVER read.
- the model is NEVER trained, tuned or selected here.
- only completed matches may enter production history.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

sys.path.insert(
    0,
    str(BASE_DIR),
)


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

BASE_HISTORY_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "historical_fixtures.csv"
)

RAW_2025_FILE = (
    BASE_DIR
    / "data"
    / "historical"
    / "raw"
    / "epl_2025_26.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "production"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "production_history.csv"
)

REPORT_FILE = (
    OUTPUT_DIR
    / "production_history_report.json"
)


# ============================================================
# Team aliases
# ============================================================

RAW_ALIASES = {

    "Man City":
        "Manchester City",

    "Man United":
        "Manchester United",

    "Nott'm Forest":
        "Nottingham Forest",
}


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


def canonical_raw_name(
    name,
) -> str:

    name = str(
        name
    ).strip()

    return RAW_ALIASES.get(
        name,
        name,
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
            "Team name is missing."
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


def load_base_history():

    if not BASE_HISTORY_FILE.exists():

        raise FileNotFoundError(
            f"Missing historical dataset: "
            f"{BASE_HISTORY_FILE}"
        )

    history = pd.read_csv(
        BASE_HISTORY_FILE
    )

    if len(history) != 760:

        raise RuntimeError(
            "Expected 760 protected historical "
            f"records, found {len(history)}."
        )

    history["date"] = pd.to_datetime(
        history["date"],
        errors="coerce",
        utc=True,
    )

    if history["date"].isna().any():

        raise RuntimeError(
            "Invalid date detected in base history."
        )

    return history


def build_team_mapping(
    history: pd.DataFrame,
) -> dict:

    mapping = {}

    for _, row in history.iterrows():

        home_name = str(
            row["home_team_name"]
        ).strip()

        away_name = str(
            row["away_team_name"]
        ).strip()

        mapping[
            home_name
        ] = int(
            row["home_team_id"]
        )

        mapping[
            away_name
        ] = int(
            row["away_team_id"]
        )

    return mapping


def resolve_team_id(
    team_name: str,
    team_mapping: dict,
) -> int:

    if team_name in team_mapping:

        return int(
            team_mapping[
                team_name
            ]
        )

    team_id = (
        deterministic_negative_id(
            "fixtureiq-team",
            team_name,
        )
    )

    team_mapping[
        team_name
    ] = team_id

    return team_id


# ============================================================
# 2025/26 source
# ============================================================

def normalize_2025_26(
    team_mapping: dict,
) -> pd.DataFrame:

    if not RAW_2025_FILE.exists():

        raise FileNotFoundError(
            f"Missing 2025/26 raw file: "
            f"{RAW_2025_FILE}"
        )

    raw = pd.read_csv(
        RAW_2025_FILE
    )

    print(
        f"2025/26 raw records: {len(raw)}"
    )

    if len(raw) != 380:

        raise RuntimeError(
            "Expected 380 2025/26 records, "
            f"found {len(raw)}."
        )

    required = {
        "Date",
        "HomeTeam",
        "AwayTeam",
        "FTHG",
        "FTAG",
    }

    missing = (
        required
        -
        set(raw.columns)
    )

    if missing:

        raise RuntimeError(
            "2025/26 source missing columns: "
            f"{sorted(missing)}"
        )

    # --------------------------------------------------------
    # Date + time
    # --------------------------------------------------------

    date_text = (
        raw["Date"]
        .astype(str)
        .str.strip()
    )

    if "Time" in raw.columns:

        time_text = (
            raw["Time"]
            .fillna("00:00")
            .astype(str)
            .str.strip()
        )

        datetime_text = (
            date_text
            +
            " "
            +
            time_text
        )

    else:

        datetime_text = (
            date_text
            +
            " 00:00"
        )

    dates = pd.to_datetime(
        datetime_text,
        errors="coerce",
        dayfirst=True,
        utc=True,
    )

    if dates.isna().any():

        bad_count = int(
            dates.isna().sum()
        )

        raise RuntimeError(
            "Invalid 2025/26 dates: "
            f"{bad_count}"
        )

    home_goals = pd.to_numeric(
        raw["FTHG"],
        errors="coerce",
    )

    away_goals = pd.to_numeric(
        raw["FTAG"],
        errors="coerce",
    )

    if (
        home_goals.isna().any()
        or
        away_goals.isna().any()
    ):

        raise RuntimeError(
            "2025/26 contains missing "
            "full-time scores."
        )

    rows = []

    for index, row in raw.iterrows():

        home_name = canonical_raw_name(
            row["HomeTeam"]
        )

        away_name = canonical_raw_name(
            row["AwayTeam"]
        )

        home_id = resolve_team_id(
            home_name,
            team_mapping,
        )

        away_id = resolve_team_id(
            away_name,
            team_mapping,
        )

        kickoff = dates.iloc[
            index
        ]

        fixture_key = (
            f"{kickoff.isoformat()}"
            f"|{home_name}"
            f"|{away_name}"
        )

        fixture_id = (
            deterministic_negative_id(
                "football-data-raw-2025",
                fixture_key,
            )
        )

        rows.append(
            {
                "fixture_id":
                    fixture_id,

                "season":
                    2025,

                "date":
                    kickoff,

                "timestamp":
                    int(
                        kickoff.timestamp()
                    ),

                "timezone":
                    "UTC",

                "status_short":
                    "FT",

                "status_long":
                    "Match Finished",

                "status_elapsed":
                    90,

                "league_id":
                    39,

                "league_name":
                    "Premier League",

                "country":
                    "England",

                "round":
                    "Regular Season",

                "home_team_id":
                    home_id,

                "home_team_name":
                    home_name,

                "home_team_code":
                    None,

                "away_team_id":
                    away_id,

                "away_team_name":
                    away_name,

                "away_team_code":
                    None,

                "home_goals":
                    int(
                        home_goals.iloc[
                            index
                        ]
                    ),

                "away_goals":
                    int(
                        away_goals.iloc[
                            index
                        ]
                    ),
            }
        )

    dataframe = pd.DataFrame(
        rows
    )

    if len(
        dataframe
    ) != 380:

        raise RuntimeError(
            "2025/26 normalization did not "
            "produce 380 matches."
        )

    if not dataframe[
        "fixture_id"
    ].is_unique:

        raise RuntimeError(
            "2025/26 fixture IDs are not unique."
        )

    return dataframe


# ============================================================
# Current 2026/27 completed matches
# ============================================================

def fetch_current_completed(
    team_mapping: dict,
) -> tuple[pd.DataFrame, int]:

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

        raise RuntimeError(
            "Unable to build production history: "
            f"{exc}"
        ) from exc

    matches = payload.get(
        "matches",
        [],
    )

    now = pd.Timestamp.now(
        tz="UTC"
    )

    rows = []

    for match in matches:

        if not isinstance(
            match,
            dict,
        ):

            continue

        status = str(
            match.get(
                "status",
                "",
            )
        ).upper()

        # Strict rule:
        # only fully completed matches enter state.
        if status != "FINISHED":

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

        if kickoff > now:

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

        home_id = resolve_team_id(
            home_name,
            team_mapping,
        )

        away_id = resolve_team_id(
            away_name,
            team_mapping,
        )

        score = match.get(
            "score",
            {},
        )

        full_time = score.get(
            "fullTime",
            {},
        )

        home_goals = full_time.get(
            "home"
        )

        away_goals = full_time.get(
            "away"
        )

        if (
            home_goals is None
            or
            away_goals is None
        ):

            raise RuntimeError(
                "FINISHED current-season fixture "
                "has no full-time score."
            )

        provider_fixture_id = (
            match.get(
                "id"
            )
        )

        if provider_fixture_id is None:

            raise RuntimeError(
                "Current completed fixture "
                "has no provider ID."
            )

        fixture_id = (
            deterministic_negative_id(
                "football-data-fixture",
                str(
                    provider_fixture_id
                ),
            )
        )

        rows.append(
            {
                "fixture_id":
                    fixture_id,

                "season":
                    int(
                        API_FOOTBALL_SEASON
                    ),

                "date":
                    kickoff,

                "timestamp":
                    int(
                        kickoff.timestamp()
                    ),

                "timezone":
                    "UTC",

                "status_short":
                    "FT",

                "status_long":
                    "Match Finished",

                "status_elapsed":
                    90,

                "league_id":
                    39,

                "league_name":
                    "Premier League",

                "country":
                    "England",

                "round":
                    (
                        f"Regular Season - "
                        f"{match.get('matchday')}"
                        if match.get(
                            "matchday"
                        ) is not None
                        else "Regular Season"
                    ),

                "home_team_id":
                    home_id,

                "home_team_name":
                    home_name,

                "home_team_code":
                    home.get(
                        "tla"
                    ),

                "away_team_id":
                    away_id,

                "away_team_name":
                    away_name,

                "away_team_code":
                    away.get(
                        "tla"
                    ),

                "home_goals":
                    int(
                        home_goals
                    ),

                "away_goals":
                    int(
                        away_goals
                    ),
            }
        )

    dataframe = pd.DataFrame(
        rows
    )

    if not dataframe.empty:

        if not dataframe[
            "fixture_id"
        ].is_unique:

            raise RuntimeError(
                "Current-season completed fixture "
                "IDs are not unique."
            )

        dataframe = (
            dataframe
            .sort_values(
                [
                    "date",
                    "fixture_id",
                ]
            )
            .reset_index(drop=True)
        )

    return (
        dataframe,
        len(matches),
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
        "Production Historical Context Builder"
    )

    print("=" * 60)

    # ========================================================
    # 1. Protected base history
    # ========================================================

    print(
        "\n1. PROTECTED BASE HISTORY"
    )

    base_history = (
        load_base_history()
    )

    print(
        f"Base historical records: "
        f"{len(base_history)}"
    )

    print(
        "Protected historical file modified: NO"
    )

    team_mapping = (
        build_team_mapping(
            base_history
        )
    )

    print(
        f"Initial team identities: "
        f"{len(team_mapping)}"
    )

    # ========================================================
    # 2. 2025/26 operational history
    # ========================================================

    print(
        "\n2. 2025/26 OPERATIONAL HISTORY"
    )

    season_2025 = (
        normalize_2025_26(
            team_mapping
        )
    )

    print(
        f"2025/26 completed records: "
        f"{len(season_2025)}"
    )

    print(
        "Final-test evaluation artifacts read: NO"
    )

    print(
        "Raw match results used as future "
        "operational history: YES"
    )

    # ========================================================
    # 3. Current completed matches
    # ========================================================

    print(
        "\n3. 2026/27 COMPLETED MATCHES"
    )

    (
        current_completed,
        provider_total,
    ) = fetch_current_completed(
        team_mapping
    )

    print(
        f"Provider season fixtures: "
        f"{provider_total}"
    )

    print(
        f"Completed current-season matches: "
        f"{len(current_completed)}"
    )

    print(
        "Scheduled matches added to history: NO"
    )

    # ========================================================
    # 4. Combine
    # ========================================================

    print(
        "\n4. PRODUCTION HISTORY"
    )

    frames = [
        base_history,
        season_2025,
    ]

    if not current_completed.empty:

        frames.append(
            current_completed
        )

    production_history = pd.concat(
        frames,
        ignore_index=True,
        sort=False,
    )

    production_history[
        "date"
    ] = pd.to_datetime(
        production_history[
            "date"
        ],
        errors="coerce",
        utc=True,
    )

    if production_history[
        "date"
    ].isna().any():

        raise RuntimeError(
            "Production history contains "
            "invalid dates."
        )

    production_history = (
        production_history
        .sort_values(
            [
                "date",
                "fixture_id",
            ]
        )
        .reset_index(drop=True)
    )

    if not production_history[
        "fixture_id"
    ].is_unique:

        duplicated = (
            production_history[
                production_history[
                    "fixture_id"
                ].duplicated(
                    keep=False
                )
            ][
                "fixture_id"
            ]
            .tolist()
        )

        raise RuntimeError(
            "Duplicate production fixture IDs: "
            f"{duplicated[:10]}"
        )

    if (
        production_history[
            "home_goals"
        ].isna().any()
        or
        production_history[
            "away_goals"
        ].isna().any()
    ):

        raise RuntimeError(
            "Production history contains "
            "missing match results."
        )

    expected_total = (
        len(base_history)
        +
        len(season_2025)
        +
        len(current_completed)
    )

    if len(
        production_history
    ) != expected_total:

        raise RuntimeError(
            "Production history record "
            "count mismatch."
        )

    print(
        f"Base history: "
        f"{len(base_history)}"
    )

    print(
        f"2025/26 history: "
        f"{len(season_2025)}"
    )

    print(
        f"2026/27 completed: "
        f"{len(current_completed)}"
    )

    print(
        f"Total production history: "
        f"{len(production_history)}"
    )

    print(
        "Fixture IDs unique: PASS"
    )

    print(
        "Chronological ordering: PASS"
    )

    print(
        "Completed results only: PASS"
    )

    # ========================================================
    # 5. Team-state coverage
    # ========================================================

    print(
        "\n5. TEAM STATE COVERAGE"
    )

    all_teams = set(
        production_history[
            "home_team_name"
        ].astype(str)
    ) | set(
        production_history[
            "away_team_name"
        ].astype(str)
    )

    print(
        f"Production-history teams: "
        f"{len(all_teams)}"
    )

    for team in [
        "Leeds",
        "Sunderland",
    ]:

        print(
            f"{team} historical state: "
            +
            (
                "PASS"
                if team in all_teams
                else "FAIL"
            )
        )

        if team not in all_teams:

            raise RuntimeError(
                f"{team} is missing from "
                "production history."
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

    production_history.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    report = {

        "stage":
            "7.8.2",

        "component":
            "production_historical_context",

        "status":
            "PASS",

        "base_historical_records":
            int(
                len(base_history)
            ),

        "season_2025_26_records":
            int(
                len(season_2025)
            ),

        "current_season_completed_records":
            int(
                len(current_completed)
            ),

        "total_production_history":
            int(
                len(production_history)
            ),

        "configured_current_season":
            int(
                API_FOOTBALL_SEASON
            ),

        "historical_fixtures_modified":
            False,

        "final_test_evaluation_artifacts_used":
            False,

        "model_retrained":
            False,

        "model_reselected":
            False,

        "hyperparameter_tuning":
            False,

        "completed_results_only":
            True,

        "chronological":
            True,

        "fixture_ids_unique":
            True,

        "production_history_file":
            str(
                OUTPUT_FILE
            ),
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

    print(
        f"Production history:\n"
        f"{OUTPUT_FILE}"
    )

    print(
        f"\nReport:\n"
        f"{REPORT_FILE}"
    )

    # ========================================================
    # Final
    # ========================================================

    print(
        "\n7. PROTECTION"
    )

    print(
        "historical_fixtures.csv modified: NO"
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
        "PRODUCTION HISTORICAL CONTEXT: PASS"
    )

    print("=" * 60)


if __name__ == "__main__":

    main()
"""
FixtureIQ Stage 8.3.3
Independent Canonical Current Team Form Verification.

Recomputes overall/home/away form directly from the verified
current-season completed-match source and compares it against
current_team_form.csv.

No provider fetch.
No model execution.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(
    BASE_DIR
) not in sys.path:

    sys.path.insert(
        0,
        str(
            BASE_DIR
        ),
    )


from backend.services.team_form_engine import (
    TeamFormEngine,
    sha256_file,
)


PRODUCTION_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "production"
)

CONTEXT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "context"
)


CONTRACT_FILE = (
    CONTEXT_DIR
    / "stage8_context_contract.json"
)

STANDINGS_FILE = (
    CONTEXT_DIR
    / "current_standings.csv"
)

STANDINGS_REPORT_FILE = (
    CONTEXT_DIR
    / "standings_report.json"
)

HISTORY_FILE = (
    PRODUCTION_DIR
    / "production_history.csv"
)

TEAM_FORM_FILE = (
    CONTEXT_DIR
    / "current_team_form.csv"
)

TEAM_FORM_REPORT_FILE = (
    CONTEXT_DIR
    / "team_form_report.json"
)


EXPECTED_FIELDS = [

    "team_id",
    "team_name",

    "form_matches_available",
    "recent_results",
    "recent_points",
    "recent_wins",
    "recent_draws",
    "recent_losses",
    "recent_goals_for",
    "recent_goals_against",
    "recent_goal_difference",

    "home_form_matches_available",
    "home_recent_results",
    "home_recent_points",
    "home_recent_wins",
    "home_recent_draws",
    "home_recent_losses",
    "home_recent_goals_for",
    "home_recent_goals_against",
    "home_recent_goal_difference",

    "away_form_matches_available",
    "away_recent_results",
    "away_recent_points",
    "away_recent_wins",
    "away_recent_draws",
    "away_recent_losses",
    "away_recent_goals_for",
    "away_recent_goals_against",
    "away_recent_goal_difference",
]


INTEGER_FIELDS = [

    field

    for field in EXPECTED_FIELDS

    if field not in {
        "team_id",
        "team_name",
        "recent_results",
        "home_recent_results",
        "away_recent_results",
    }
]


def load_json(
    path: Path,
) -> dict:

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(
            file
        )


def check(
    label: str,
    condition,
    failures: list[str],
) -> bool:

    passed = bool(
        condition
    )

    print(
        f"{label}: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    if not passed:

        failures.append(
            label
        )

    return passed


def registry_sha256(
    rows: list[dict],
) -> str:

    lines = sorted(
        (
            f"{row['team_id']}|"
            f"{row['team_name']}"
        )
        for row in rows
    )

    payload = (
        "\n".join(
            lines
        )
        + "\n"
    ).encode(
        "utf-8"
    )

    return hashlib.sha256(
        payload
    ).hexdigest()


def recompute_block(
    matches: list[dict],
    team_id: str,
    mode: str,
) -> dict:

    relevant = []

    for match in matches:

        is_home = (
            match[
                "home_team_id"
            ]
            == team_id
        )

        is_away = (
            match[
                "away_team_id"
            ]
            == team_id
        )

        if mode == "OVERALL":

            include = (
                is_home
                or
                is_away
            )

        elif mode == "HOME":

            include = is_home

        elif mode == "AWAY":

            include = is_away

        else:

            raise RuntimeError(
                f"Invalid mode: {mode}"
            )

        if include:

            relevant.append(
                match
            )

    selected = relevant[
        -5:
    ]

    results = []

    wins = 0
    draws = 0
    losses = 0

    goals_for = 0
    goals_against = 0

    for match in selected:

        if (
            match[
                "home_team_id"
            ]
            == team_id
        ):

            gf = match[
                "home_goals"
            ]

            ga = match[
                "away_goals"
            ]

        else:

            gf = match[
                "away_goals"
            ]

            ga = match[
                "home_goals"
            ]

        if gf > ga:

            result = "W"
            wins += 1

        elif gf == ga:

            result = "D"
            draws += 1

        else:

            result = "L"
            losses += 1

        results.append(
            result
        )

        goals_for += gf
        goals_against += ga

    return {

        "matches_available":
            len(
                selected
            ),

        "results":
            "".join(
                results
            ),

        "points":
            3 * wins + draws,

        "wins":
            wins,

        "draws":
            draws,

        "losses":
            losses,

        "goals_for":
            goals_for,

        "goals_against":
            goals_against,

        "goal_difference":
            goals_for - goals_against,
    }


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.3.3"
    )

    print(
        "Canonical Team Form Verification"
    )

    print("=" * 72)

    failures = []

    # ========================================================
    # 1. Required artifacts
    # ========================================================

    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    required = [

        CONTRACT_FILE,
        STANDINGS_FILE,
        STANDINGS_REPORT_FILE,
        HISTORY_FILE,
        TEAM_FORM_FILE,
        TEAM_FORM_REPORT_FILE,
    ]

    for path in required:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        sys.exit(1)

    contract = load_json(
        CONTRACT_FILE
    )

    standings_report = load_json(
        STANDINGS_REPORT_FILE
    )

    report = load_json(
        TEAM_FORM_REPORT_FILE
    )

    # ========================================================
    # 2. Foundation
    # ========================================================

    print(
        "\n2. STAGE FOUNDATION"
    )

    check(
        "Stage 8.1 COMPLETE",
        contract.get(
            "stage_8_1_complete"
        )
        is True,
        failures,
    )

    check(
        "Context contract LOCKED",
        contract.get(
            "contract_status"
        )
        == "LOCKED_CONTEXT_CONTRACT",
        failures,
    )

    check(
        "Stage 8.2 COMPLETE",
        standings_report.get(
            "stage_8_2_complete"
        )
        is True,
        failures,
    )

    sub_stages = report.get(
        "sub_stages",
        {}
    )

    check(
        "8.3.1 PASS",
        sub_stages.get(
            "8.3.1"
        )
        == "PASS",
        failures,
    )

    check(
        "8.3.2 PASS",
        sub_stages.get(
            "8.3.2"
        )
        == "PASS",
        failures,
    )

    check(
        "8.3.3 builder PASS",
        sub_stages.get(
            "8.3.3"
        )
        == "PASS",
        failures,
    )

    # ========================================================
    # 3. Read CSV
    # ========================================================

    print(
        "\n3. CANONICAL CSV"
    )

    with TEAM_FORM_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        fields = (
            reader.fieldnames
            or []
        )

        raw_rows = list(
            reader
        )

    check(
        "Schema exact",
        fields
        == EXPECTED_FIELDS,
        failures,
    )

    check(
        "Column count = 29",
        len(
            fields
        )
        == 29,
        failures,
    )

    check(
        "Row count = 20",
        len(
            raw_rows
        )
        == 20,
        failures,
    )

    rows = []

    try:

        for raw in raw_rows:

            row = dict(
                raw
            )

            for field in INTEGER_FIELDS:

                row[
                    field
                ] = int(
                    raw[
                        field
                    ]
                )

            rows.append(
                row
            )

        numeric_parse_ok = True

    except (
        KeyError,
        ValueError,
        TypeError,
    ):

        numeric_parse_ok = False

    check(
        "Numeric fields valid",
        numeric_parse_ok,
        failures,
    )

    if not numeric_parse_ok:

        sys.exit(1)

    # ========================================================
    # 4. Team identity
    # ========================================================

    print(
        "\n4. TEAM IDENTITY"
    )

    check(
        "20 unique IDs",
        len(
            {
                row[
                    "team_id"
                ]
                for row in rows
            }
        )
        == 20,
        failures,
    )

    check(
        "20 unique names",
        len(
            {
                row[
                    "team_name"
                ].casefold()
                for row in rows
            }
        )
        == 20,
        failures,
    )

    check(
        "Sorted team_name ASC",
        [
            row[
                "team_name"
            ].casefold()
            for row in rows
        ]
        ==
        sorted(
            [
                row[
                    "team_name"
                ].casefold()
                for row in rows
            ]
        ),
        failures,
    )

    # ========================================================
    # 5. Generic form invariants
    # ========================================================

    print(
        "\n5. FORM INVARIANTS"
    )

    prefixes = [

        (
            "",
            "form_matches_available",
            "recent_results",
            "recent_points",
            "recent_wins",
            "recent_draws",
            "recent_losses",
            "recent_goals_for",
            "recent_goals_against",
            "recent_goal_difference",
        ),

        (
            "home",
            "home_form_matches_available",
            "home_recent_results",
            "home_recent_points",
            "home_recent_wins",
            "home_recent_draws",
            "home_recent_losses",
            "home_recent_goals_for",
            "home_recent_goals_against",
            "home_recent_goal_difference",
        ),

        (
            "away",
            "away_form_matches_available",
            "away_recent_results",
            "away_recent_points",
            "away_recent_wins",
            "away_recent_draws",
            "away_recent_losses",
            "away_recent_goals_for",
            "away_recent_goals_against",
            "away_recent_goal_difference",
        ),
    ]

    for (
        label,
        matches_field,
        results_field,
        points_field,
        wins_field,
        draws_field,
        losses_field,
        gf_field,
        ga_field,
        gd_field,
    ) in prefixes:

        name = (
            label.upper()
            if label
            else "OVERALL"
        )

        check(
            f"{name} window <= 5",
            all(
                0
                <= row[
                    matches_field
                ]
                <= 5
                for row in rows
            ),
            failures,
        )

        check(
            f"{name} result symbols W/D/L",
            all(
                set(
                    row[
                        results_field
                    ]
                ).issubset(
                    {
                        "W",
                        "D",
                        "L",
                    }
                )
                for row in rows
            ),
            failures,
        )

        check(
            f"{name} result length valid",
            all(
                len(
                    row[
                        results_field
                    ]
                )
                ==
                row[
                    matches_field
                ]
                for row in rows
            ),
            failures,
        )

        check(
            f"{name} matches = W+D+L",
            all(
                row[
                    matches_field
                ]
                ==
                (
                    row[
                        wins_field
                    ]
                    +
                    row[
                        draws_field
                    ]
                    +
                    row[
                        losses_field
                    ]
                )
                for row in rows
            ),
            failures,
        )

        check(
            f"{name} points = 3W+D",
            all(
                row[
                    points_field
                ]
                ==
                (
                    3
                    *
                    row[
                        wins_field
                    ]
                    +
                    row[
                        draws_field
                    ]
                )
                for row in rows
            ),
            failures,
        )

        check(
            f"{name} GD = GF-GA",
            all(
                row[
                    gd_field
                ]
                ==
                (
                    row[
                        gf_field
                    ]
                    -
                    row[
                        ga_field
                    ]
                )
                for row in rows
            ),
            failures,
        )

    # ========================================================
    # 6. Independent history recomputation
    # ========================================================

    print(
        "\n6. INDEPENDENT HISTORY RECOMPUTATION"
    )

    engine = TeamFormEngine(
        season=2026,
        window=5,
    )

    gated = (
        engine.load_current_season_matches()
    )

    matches = gated[
        "matches"
    ]

    check(
        "All source matches season 2026",
        all(
            match[
                "season"
            ]
            == 2026
            for match in matches
        ),
        failures,
    )

    now_utc = datetime.now(
        timezone.utc
    )

    check(
        "No future matches used",
        all(
            match[
                "date_utc"
            ]
            <= now_utc
            for match in matches
        ),
        failures,
    )

    expected_by_id = {}

    for team in (
        engine.team_by_id.values()
    ):

        team_id = (
            team[
                "team_id"
            ]
        )

        overall = recompute_block(
            matches,
            team_id,
            "OVERALL",
        )

        home = recompute_block(
            matches,
            team_id,
            "HOME",
        )

        away = recompute_block(
            matches,
            team_id,
            "AWAY",
        )

        expected_by_id[
            team_id
        ] = {

            "team_id":
                team_id,

            "team_name":
                team[
                    "team_name"
                ],

            "form_matches_available":
                overall[
                    "matches_available"
                ],

            "recent_results":
                overall[
                    "results"
                ],

            "recent_points":
                overall[
                    "points"
                ],

            "recent_wins":
                overall[
                    "wins"
                ],

            "recent_draws":
                overall[
                    "draws"
                ],

            "recent_losses":
                overall[
                    "losses"
                ],

            "recent_goals_for":
                overall[
                    "goals_for"
                ],

            "recent_goals_against":
                overall[
                    "goals_against"
                ],

            "recent_goal_difference":
                overall[
                    "goal_difference"
                ],

            "home_form_matches_available":
                home[
                    "matches_available"
                ],

            "home_recent_results":
                home[
                    "results"
                ],

            "home_recent_points":
                home[
                    "points"
                ],

            "home_recent_wins":
                home[
                    "wins"
                ],

            "home_recent_draws":
                home[
                    "draws"
                ],

            "home_recent_losses":
                home[
                    "losses"
                ],

            "home_recent_goals_for":
                home[
                    "goals_for"
                ],

            "home_recent_goals_against":
                home[
                    "goals_against"
                ],

            "home_recent_goal_difference":
                home[
                    "goal_difference"
                ],

            "away_form_matches_available":
                away[
                    "matches_available"
                ],

            "away_recent_results":
                away[
                    "results"
                ],

            "away_recent_points":
                away[
                    "points"
                ],

            "away_recent_wins":
                away[
                    "wins"
                ],

            "away_recent_draws":
                away[
                    "draws"
                ],

            "away_recent_losses":
                away[
                    "losses"
                ],

            "away_recent_goals_for":
                away[
                    "goals_for"
                ],

            "away_recent_goals_against":
                away[
                    "goals_against"
                ],

            "away_recent_goal_difference":
                away[
                    "goal_difference"
                ],
        }

    recomputation_ok = True

    for row in rows:

        expected = (
            expected_by_id.get(
                row[
                    "team_id"
                ]
            )
        )

        if (
            expected is None
            or
            row != expected
        ):

            recomputation_ok = False
            break

    check(
        "CSV exactly matches recomputed form",
        recomputation_ok,
        failures,
    )

    check(
        "Previous-season padding = 0",
        report.get(
            "source_gate",
            {}
        ).get(
            "previous_season_padding"
        )
        == 0,
        failures,
    )

    # ========================================================
    # 7. Artifact / provenance
    # ========================================================

    print(
        "\n7. ARTIFACT & PROVENANCE"
    )

    artifact = report.get(
        "current_team_form",
        {}
    )

    check(
        "CSV SHA matches report",
        artifact.get(
            "sha256"
        )
        ==
        sha256_file(
            TEAM_FORM_FILE
        ),
        failures,
    )

    check(
        "Report row count = 20",
        artifact.get(
            "row_count"
        )
        == 20,
        failures,
    )

    check(
        "Report column count = 29",
        artifact.get(
            "column_count"
        )
        == 29,
        failures,
    )

    check(
        "Report columns exact",
        artifact.get(
            "columns"
        )
        == EXPECTED_FIELDS,
        failures,
    )

    check(
        "Namespace fixtureiq-team",
        artifact.get(
            "team_namespace"
        )
        == "fixtureiq-team",
        failures,
    )

    check(
        "History dependency hash valid",
        report.get(
            "dependency_identity",
            {}
        ).get(
            "production_history",
            {}
        ).get(
            "sha256"
        )
        ==
        sha256_file(
            HISTORY_FILE
        ),
        failures,
    )

    registry_dependency = (
        report.get(
            "dependency_identity",
            {}
        ).get(
            "current_epl_team_registry",
            {}
        )
    )

    check(
        "Team registry semantic hash valid",
        registry_dependency.get(
            "semantic_sha256"
        )
        ==
        registry_sha256(
            rows
        ),
        failures,
    )

    check(
        "History cutoff present",
        bool(
            report.get(
                "history_cutoff_utc"
            )
        ),
        failures,
    )

    # ========================================================
    # 8. Safety
    # ========================================================

    print(
        "\n8. SAFETY BOUNDARY"
    )

    safety = report.get(
        "safety",
        {}
    )

    check(
        "Context only",
        safety.get(
            "context_only"
        )
        is True,
        failures,
    )

    false_flags = [

        "stage7_artifacts_modified",
        "provider_fetch_performed",
        "future_matches_used",
        "previous_season_padding_used",
        "model_loaded",
        "model_executed",
        "model_modified",
        "production_predictions_modified",
        "feature_schema_modified",
        "form_used_as_model_features",
        "final_test_accessed",
    ]

    for flag in false_flags:

        check(
            f"{flag} = false",
            safety.get(
                flag
            )
            is False,
            failures,
        )

    # ========================================================
    # Final
    # ========================================================

    overall_pass = (
        len(
            failures
        )
        == 0
    )

    print(
        "\n" + "=" * 72
    )

    if overall_pass:

        print(
            "STAGE 8.3.1: PASS"
        )

        print(
            "STAGE 8.3.2: PASS"
        )

        print(
            "STAGE 8.3.3: PASS"
        )

        print(
            "HOME/AWAY TEAM FORM: VERIFIED"
        )

        print(
            "CANONICAL CURRENT TEAM FORM: VERIFIED"
        )

        print(
            "STAGE 8.3: IN PROGRESS"
        )

    else:

        print(
            "STAGE 8.3.3: FAIL"
        )

        print(
            "STAGE 8.3: INCOMPLETE"
        )

        print(
            "\nFailures:"
        )

        for failure in failures:

            print(
                f"  - {failure}"
            )

    print("=" * 72)

    sys.exit(
        0
        if overall_pass
        else 1
    )


if __name__ == "__main__":

    main()
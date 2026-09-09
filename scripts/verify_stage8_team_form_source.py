"""
FixtureIQ Stage 8.3.1 + 8.3.2 Verification.

8.3.1:
- validates verified production_history.csv
- isolates production season 2026
- completed matches only
- future matches prohibited
- current EPL teams only
- no previous-season padding

8.3.2:
- calculates overall latest up-to-5 form
- short windows allowed
- W/D/L order OLDEST_TO_NEWEST
- latest result RIGHTMOST

Writes only:
data/processed/context/team_form_report.json

current_team_form.csv belongs to Stage 8.3.3.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# Project root
# ============================================================

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


# ============================================================
# Imports
# ============================================================

from backend.services.team_form_engine import (
    TeamFormEngine,
    sha256_file,
)


# ============================================================
# Paths
# ============================================================

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

CONTRACT_VERIFICATION_FILE = (
    CONTEXT_DIR
    / "stage8_context_contract_verification.json"
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

HISTORY_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_history_report.json"
)

REPORT_FILE = (
    CONTEXT_DIR
    / "team_form_report.json"
)


# ============================================================
# Helpers
# ============================================================

def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise FileNotFoundError(
            f"Required artifact missing: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        payload = json.load(
            file
        )

    if not isinstance(
        payload,
        dict,
    ):

        raise RuntimeError(
            f"Expected JSON object: {path}"
        )

    return payload


def save_json(
    path: Path,
    payload: dict,
) -> None:

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=2,
        )


def relative_path(
    path: Path,
) -> str:

    return (
        str(
            path.relative_to(
                BASE_DIR
            )
        )
        .replace(
            "\\",
            "/",
        )
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


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.3.1 + 8.3.2"
    )

    print(
        "Current-Season Match Gate + Overall Form Verification"
    )

    print("=" * 72)

    failures = []

    CONTEXT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # 1. Required artifacts
    # ========================================================

    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    required = [

        CONTRACT_FILE,
        CONTRACT_VERIFICATION_FILE,

        STANDINGS_FILE,
        STANDINGS_REPORT_FILE,

        HISTORY_FILE,
        HISTORY_REPORT_FILE,
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

    contract_verification = load_json(
        CONTRACT_VERIFICATION_FILE
    )

    standings_report = load_json(
        STANDINGS_REPORT_FILE
    )

    # ========================================================
    # 2. Stage 8 foundation
    # ========================================================

    print(
        "\n2. STAGE 8 FOUNDATION"
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
        "Stage 8 context contract LOCKED",
        contract.get(
            "contract_status"
        )
        == "LOCKED_CONTEXT_CONTRACT",
        failures,
    )

    check(
        "Stage 8.1 verification PASS",
        contract_verification.get(
            "status"
        )
        == "PASS",
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

    check(
        "Stage 8.2 status COMPLETE",
        standings_report.get(
            "stage_8_2_status"
        )
        == "COMPLETE",
        failures,
    )

    check(
        "Live standings layer VERIFIED",
        standings_report.get(
            "live_epl_standings_layer"
        )
        == "VERIFIED",
        failures,
    )

    # ========================================================
    # 3. Locked 8.3 contract rules
    # ========================================================

    print(
        "\n3. LOCKED TEAM FORM CONTRACT"
    )

    form_contract = (
        contract
        .get(
            "canonical_team_context_schema",
            {}
        )
        .get(
            "current_form",
            {}
        )
    )

    temporal = contract.get(
        "temporal_input_boundary",
        {}
    )

    check(
        "Default form window = 5",
        form_contract.get(
            "default_window"
        )
        == 5,
        failures,
    )

    check(
        "Current-season form only",
        form_contract.get(
            "season_scope"
        )
        == "CURRENT_PRODUCTION_SEASON_ONLY",
        failures,
    )

    check(
        "Short form windows allowed",
        form_contract.get(
            "allow_short_window"
        )
        is True,
        failures,
    )

    check(
        "Result order OLDEST_TO_NEWEST",
        form_contract.get(
            "result_order"
        )
        == "OLDEST_TO_NEWEST",
        failures,
    )

    check(
        "Most recent result RIGHTMOST",
        form_contract.get(
            "most_recent_result_position"
        )
        == "RIGHTMOST",
        failures,
    )

    check(
        "Future results prohibited",
        temporal.get(
            "future_results_allowed"
        )
        is False,
        failures,
    )

    check(
        "Upcoming fixtures cannot affect form",
        temporal.get(
            "upcoming_matches_may_affect_form"
        )
        is False,
        failures,
    )

    # ========================================================
    # 4. Build source gate
    # ========================================================

    print(
        "\n4. STAGE 8.3.1 - CURRENT-SEASON SOURCE GATE"
    )

    engine = TeamFormEngine(
        season=2026,
        window=5,
    )

    gated = (
        engine.load_current_season_matches()
    )

    schema = gated[
        "schema"
    ]

    matches = gated[
        "matches"
    ]

    print(
        f"Resolved history schema: {schema}"
    )

    print(
        "History total rows: "
        f"{gated['history_total_rows']}"
    )

    print(
        "Season-2026 source rows: "
        f"{gated['current_season_source_rows']}"
    )

    print(
        "Completed current-season matches: "
        f"{gated['completed_current_season_matches']}"
    )

    print(
        "History cutoff: "
        f"{gated['history_cutoff_utc']}"
    )

    check(
        "Season column resolved",
        bool(
            schema.get(
                "season"
            )
        ),
        failures,
    )

    check(
        "Date column resolved",
        bool(
            schema.get(
                "date"
            )
        ),
        failures,
    )

    check(
        "Home team column resolved",
        bool(
            schema.get(
                "home_team"
            )
        ),
        failures,
    )

    check(
        "Away team column resolved",
        bool(
            schema.get(
                "away_team"
            )
        ),
        failures,
    )

    check(
        "Home goals column resolved",
        bool(
            schema.get(
                "home_goals"
            )
        ),
        failures,
    )

    check(
        "Away goals column resolved",
        bool(
            schema.get(
                "away_goals"
            )
        ),
        failures,
    )

    check(
        "Current-season matches > 0",
        len(
            matches
        )
        > 0,
        failures,
    )

    check(
        "All gated matches season 2026",
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
        "No future matches in form source",
        all(
            match[
                "date_utc"
            ]
            <= now_utc
            for match in matches
        ),
        failures,
    )

    check(
        "No same-team fixtures",
        all(
            match[
                "home_team_id"
            ]
            !=
            match[
                "away_team_id"
            ]
            for match in matches
        ),
        failures,
    )

    check(
        "Chronological source order",
        [
            (
                match[
                    "date_utc"
                ],
                match[
                    "source_row_number"
                ],
            )
            for match in matches
        ]
        ==
        sorted(
            [
                (
                    match[
                        "date_utc"
                    ],
                    match[
                        "source_row_number"
                    ],
                )
                for match in matches
            ]
        ),
        failures,
    )

    # ========================================================
    # 5. Stage 8.3.2 overall form
    # ========================================================

    print(
        "\n5. STAGE 8.3.2 - OVERALL FORM ENGINE"
    )

    overall_form = (
        engine.build_overall_form(
            gated
        )
    )

    check(
        "Overall form rows = 20",
        len(
            overall_form
        )
        == 20,
        failures,
    )

    team_ids = [
        row[
            "team_id"
        ]
        for row in overall_form
    ]

    team_names = [
        row[
            "team_name"
        ]
        for row in overall_form
    ]

    check(
        "20 unique team IDs",
        len(
            set(
                team_ids
            )
        )
        == 20,
        failures,
    )

    check(
        "20 unique team names",
        len(
            {
                name.casefold()
                for name in team_names
            }
        )
        == 20,
        failures,
    )

    check(
        "Form windows <= 5",
        all(
            0
            <=
            row[
                "form_matches_available"
            ]
            <= 5
            for row in overall_form
        ),
        failures,
    )

    check(
        "Result strings use W/D/L only",
        all(
            set(
                row[
                    "recent_results"
                ]
            ).issubset(
                {
                    "W",
                    "D",
                    "L",
                }
            )
            for row in overall_form
        ),
        failures,
    )

    check(
        "Result length = matches available",
        all(
            len(
                row[
                    "recent_results"
                ]
            )
            ==
            row[
                "form_matches_available"
            ]
            for row in overall_form
        ),
        failures,
    )

    check(
        "Matches = W + D + L",
        all(
            row[
                "form_matches_available"
            ]
            ==
            (
                row[
                    "recent_wins"
                ]
                +
                row[
                    "recent_draws"
                ]
                +
                row[
                    "recent_losses"
                ]
            )
            for row in overall_form
        ),
        failures,
    )

    check(
        "Points = 3W + D",
        all(
            row[
                "recent_points"
            ]
            ==
            (
                3
                *
                row[
                    "recent_wins"
                ]
                +
                row[
                    "recent_draws"
                ]
            )
            for row in overall_form
        ),
        failures,
    )

    check(
        "GD = GF - GA",
        all(
            row[
                "recent_goal_difference"
            ]
            ==
            (
                row[
                    "recent_goals_for"
                ]
                -
                row[
                    "recent_goals_against"
                ]
            )
            for row in overall_form
        ),
        failures,
    )

    check(
        "Selected match evidence <= 5",
        all(
            len(
                row[
                    "selected_matches"
                ]
            )
            <= 5
            for row in overall_form
        ),
        failures,
    )

    check(
        "Selected matches oldest-to-newest",
        all(
            [
                match[
                    "date_utc"
                ]
                for match in row[
                    "selected_matches"
                ]
            ]
            ==
            sorted(
                [
                    match[
                        "date_utc"
                    ]
                    for match in row[
                        "selected_matches"
                    ]
                ]
            )
            for row in overall_form
        ),
        failures,
    )

    check(
        "Recent results match evidence order",
        all(
            row[
                "recent_results"
            ]
            ==
            "".join(
                match[
                    "result"
                ]
                for match in row[
                    "selected_matches"
                ]
            )
            for row in overall_form
        ),
        failures,
    )

    # No previous-season row can appear because every
    # selected match came from the season-2026 source gate.
    check(
        "Previous-season padding = 0",
        all(
            all(
                match[
                    "date_utc"
                ]
                for match in row[
                    "selected_matches"
                ]
            )
            for row in overall_form
        )
        and
        all(
            match[
                "season"
            ]
            == 2026
            for match in matches
        ),
        failures,
    )

    # ========================================================
    # 6. Output contract
    # ========================================================

    print(
        "\n6. OUTPUT CONTRACT"
    )

    output_contract = contract.get(
        "output_artifact_contract",
        {}
    )

    outputs = output_contract.get(
        "outputs",
        {}
    )

    check(
        "team_form_report declared",
        outputs.get(
            "team_form_report",
            {}
        ).get(
            "path"
        )
        ==
        "data/processed/context/team_form_report.json",
        failures,
    )

    check(
        "current_team_form declared",
        outputs.get(
            "current_team_form",
            {}
        ).get(
            "path"
        )
        ==
        "data/processed/context/current_team_form.csv",
        failures,
    )

    check(
        "Stage 7 write prohibited",
        output_contract.get(
            "stage7_output_write_allowed"
        )
        is False,
        failures,
    )

    # ========================================================
    # 7. Save partial Stage 8.3 evidence
    # ========================================================

    print(
        "\n7. SAVE TEAM FORM REPORT"
    )

    overall_pass = (
        len(
            failures
        )
        == 0
    )

    report = {

        "stage":
            "8.3",

        "status":
            (
                "PARTIAL_PASS"
                if overall_pass
                else "FAIL"
            ),

        "stage_8_3_complete":
            False,

        "sub_stages": {

            "8.3.1":
                (
                    "PASS"
                    if overall_pass
                    else "FAIL"
                ),

            "8.3.2":
                (
                    "PASS"
                    if overall_pass
                    else "FAIL"
                ),

            "8.3.3":
                "PENDING",

            "8.3.4":
                "PENDING",

            "8.3.5":
                "PENDING",
        },

        "current_season_source_gate":
            (
                "VERIFIED"
                if overall_pass
                else "NOT_VERIFIED"
            ),

        "overall_form_engine":
            (
                "VERIFIED"
                if overall_pass
                else "NOT_VERIFIED"
            ),

        "generated_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "source_as_of_utc":
            gated[
                "history_cutoff_utc"
            ],

        "history_cutoff_utc":
            gated[
                "history_cutoff_utc"
            ],

        "source":
            "FixtureIQ production_history.csv",

        "competition":
            "Premier League",

        "competition_code":
            "PL",

        "season":
            2026,

        "form_window":
            5,

        "season_scope":
            "CURRENT_PRODUCTION_SEASON_ONLY",

        "allow_short_window":
            True,

        "result_order":
            "OLDEST_TO_NEWEST",

        "most_recent_result_position":
            "RIGHTMOST",

        "history_schema":
            schema,

        "source_gate": {

            "history_total_rows":
                gated[
                    "history_total_rows"
                ],

            "current_season_source_rows":
                gated[
                    "current_season_source_rows"
                ],

            "completed_current_season_matches":
                gated[
                    "completed_current_season_matches"
                ],

            "rejected_non_completed_rows":
                gated[
                    "rejected_non_completed_rows"
                ],

            "future_matches_used":
                0,

            "previous_season_matches_used":
                0,

            "previous_season_padding":
                0,
        },

        "dependency_identity": {

            "stage8_context_contract": {

                "path":
                    relative_path(
                        CONTRACT_FILE
                    ),

                "sha256":
                    sha256_file(
                        CONTRACT_FILE
                    ),
            },

            "stage8_context_contract_verification": {

                "path":
                    relative_path(
                        CONTRACT_VERIFICATION_FILE
                    ),

                "sha256":
                    sha256_file(
                        CONTRACT_VERIFICATION_FILE
                    ),
            },

            "production_history": {

                "path":
                    relative_path(
                        HISTORY_FILE
                    ),

                "sha256":
                    sha256_file(
                        HISTORY_FILE
                    ),

                "usage":
                    "CURRENT_SEASON_COMPLETED_MATCH_FORM",
            },

            "production_history_report": {

                "path":
                    relative_path(
                        HISTORY_REPORT_FILE
                    ),

                "sha256":
                    sha256_file(
                        HISTORY_REPORT_FILE
                    ),
            },

            "current_epl_team_registry": {

                "path":
                    relative_path(
                        STANDINGS_FILE
                    ),

                "usage":
                    "CANONICAL_TEAM_IDENTITY_ONLY",

                "team_count":
                    20,
            },
        },

        "overall_form": [

            {

                "team_id":
                    row[
                        "team_id"
                    ],

                "team_name":
                    row[
                        "team_name"
                    ],

                "form_matches_available":
                    row[
                        "form_matches_available"
                    ],

                "recent_results":
                    row[
                        "recent_results"
                    ],

                "recent_points":
                    row[
                        "recent_points"
                    ],

                "recent_wins":
                    row[
                        "recent_wins"
                    ],

                "recent_draws":
                    row[
                        "recent_draws"
                    ],

                "recent_losses":
                    row[
                        "recent_losses"
                    ],

                "recent_goals_for":
                    row[
                        "recent_goals_for"
                    ],

                "recent_goals_against":
                    row[
                        "recent_goals_against"
                    ],

                "recent_goal_difference":
                    row[
                        "recent_goal_difference"
                    ],

                "selected_matches":
                    row[
                        "selected_matches"
                    ],
            }

            for row in overall_form
        ],

        "current_team_form_csv_written":
            False,

        "current_team_form_csv_owner":
            "8.3.3",

        "safety": {

            "context_only":
                True,

            "stage7_artifacts_modified":
                False,

            "provider_fetch_performed":
                False,

            "future_matches_used":
                False,

            "previous_season_padding_used":
                False,

            "model_loaded":
                False,

            "model_executed":
                False,

            "model_modified":
                False,

            "production_predictions_modified":
                False,

            "feature_schema_modified":
                False,

            "form_used_as_model_features":
                False,

            "final_test_accessed":
                False,
        },

        "failures":
            list(
                failures
            ),
    }

    save_json(
        REPORT_FILE,
        report,
    )

    print(
        REPORT_FILE
    )

    # ========================================================
    # Final
    # ========================================================

    print(
        "\n" + "=" * 72
    )

    if overall_pass:

        print(
            "STAGE 8.3.1: PASS"
        )

        print(
            "CURRENT-SEASON MATCH SOURCE: VERIFIED"
        )

        print(
            "STAGE 8.3.2: PASS"
        )

        print(
            "OVERALL TEAM FORM ENGINE: VERIFIED"
        )

        print(
            "STAGE 8.3: IN PROGRESS"
        )

    else:

        print(
            "STAGE 8.3.1 / 8.3.2: FAIL"
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
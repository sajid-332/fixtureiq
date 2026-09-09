"""
FixtureIQ Stage 8.3.5
Final Current Team Form Layer Gate.

Independently verifies:

8.3.1 - current-season completed-match source gate
8.3.2 - overall last-up-to-5 form
8.3.3 - home/away form + canonical artifact
8.3.4 - team-form service + dependency freshness
8.3.5 - final Stage 8.3 integrity gate

On PASS:
- team_form_report.json -> PASS
- stage_8_3_complete = true
- stage_8_3_status = COMPLETE
- current_team_form_layer = VERIFIED

No provider fetch.
No model execution.
No Stage 7 write.
No final-test access.
"""

from __future__ import annotations

import csv
import hashlib
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
# FixtureIQ imports
# ============================================================

from backend.services.team_form_engine import (
    TeamFormEngine,
)

from backend.services.team_form_service import (
    TeamFormService,
)


# ============================================================
# Paths
# ============================================================

MODEL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
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

TEAM_FORM_FILE = (
    CONTEXT_DIR
    / "current_team_form.csv"
)

TEAM_FORM_REPORT_FILE = (
    CONTEXT_DIR
    / "team_form_report.json"
)

HISTORY_FILE = (
    PRODUCTION_DIR
    / "production_history.csv"
)

HISTORY_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_history_report.json"
)

STAGE7_8_FILE = (
    PRODUCTION_DIR
    / "stage7_8_final_verification.json"
)

STAGE7_9_FILE = (
    PRODUCTION_DIR
    / "stage7_9_final_verification.json"
)

SELECTED_MODEL_FILE = (
    MODEL_DIR
    / "selected"
    / "selected_model.joblib"
)


# ============================================================
# Locked canonical schema
# ============================================================

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


def sha256_file(
    path: Path,
) -> str:

    if not path.exists():

        raise FileNotFoundError(
            f"Required artifact missing: {path}"
        )

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as file:

        while True:

            chunk = file.read(
                1024 * 1024
            )

            if not chunk:

                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


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


def valid_aware_timestamp(
    value,
) -> bool:

    if not isinstance(
        value,
        str,
    ):

        return False

    text = value.strip()

    if not text:

        return False

    if text.endswith(
        "Z"
    ):

        text = (
            text[:-1]
            + "+00:00"
        )

    try:

        parsed = datetime.fromisoformat(
            text
        )

    except ValueError:

        return False

    return (
        parsed.tzinfo
        is not None
    )


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


def read_team_form_csv() -> tuple[
    list[str],
    list[dict],
]:

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

    rows = []

    for raw in raw_rows:

        row = dict(
            raw
        )

        row[
            "team_id"
        ] = str(
            raw.get(
                "team_id",
                ""
            )
        ).strip()

        row[
            "team_name"
        ] = str(
            raw.get(
                "team_name",
                ""
            )
        ).strip()

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

    return (
        fields,
        rows,
    )


def read_standings_registry() -> list[dict]:

    with STANDINGS_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        fields = set(
            reader.fieldnames
            or []
        )

        required = {
            "team_id",
            "team_name",
        }

        if not required.issubset(
            fields
        ):

            raise RuntimeError(
                "Standings identity schema invalid."
            )

        raw_rows = list(
            reader
        )

    registry = []

    for raw in raw_rows:

        registry.append(
            {
                "team_id":
                    str(
                        raw.get(
                            "team_id",
                            ""
                        )
                    ).strip(),

                "team_name":
                    str(
                        raw.get(
                            "team_name",
                            ""
                        )
                    ).strip(),
            }
        )

    return registry


# ============================================================
# Independent form recomputation
# ============================================================

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
                f"Invalid form mode: {mode}"
            )

        if include:

            relevant.append(
                match
            )

    # Source gate already gives chronological matches.
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

            results.append(
                "W"
            )

            wins += 1

        elif gf == ga:

            results.append(
                "D"
            )

            draws += 1

        else:

            results.append(
                "L"
            )

            losses += 1

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


def build_expected_rows(
    engine: TeamFormEngine,
    matches: list[dict],
) -> list[dict]:

    teams = sorted(
        engine.team_by_id.values(),
        key=lambda team:
            team[
                "team_name"
            ].casefold(),
    )

    expected_rows = []

    for team in teams:

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

        expected_rows.append(
            {

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
        )

    return expected_rows


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.3.5"
    )

    print(
        "Final Current Team Form Layer Gate"
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
        CONTRACT_VERIFICATION_FILE,

        STANDINGS_FILE,
        STANDINGS_REPORT_FILE,

        TEAM_FORM_FILE,
        TEAM_FORM_REPORT_FILE,

        HISTORY_FILE,
        HISTORY_REPORT_FILE,

        STAGE7_8_FILE,
        STAGE7_9_FILE,

        SELECTED_MODEL_FILE,
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

    report = load_json(
        TEAM_FORM_REPORT_FILE
    )

    stage7_8 = load_json(
        STAGE7_8_FILE
    )

    stage7_9 = load_json(
        STAGE7_9_FILE
    )

    # ========================================================
    # 2. Upstream foundation
    # ========================================================

    print(
        "\n2. UPSTREAM FOUNDATION"
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
        "Stage 8.1 status COMPLETE",
        contract.get(
            "stage_8_1_status"
        )
        == "COMPLETE",
        failures,
    )

    check(
        "Stage 8 contract LOCKED",
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

    check(
        "Stage 7.8 PASS",
        stage7_8.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 7.9 PASS",
        stage7_9.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 7.9 COMPLETE",
        stage7_9.get(
            "stage_7_9_complete"
        )
        is True,
        failures,
    )

    check(
        "Production serving stack VERIFIED",
        stage7_9.get(
            "production_serving_stack"
        )
        == "VERIFIED",
        failures,
    )

    # ========================================================
    # 3. Stage 8.3 prior evidence
    # ========================================================

    print(
        "\n3. STAGE 8.3 PRIOR EVIDENCE"
    )

    sub_stages = report.get(
        "sub_stages",
        {}
    )

    check(
        "Report stage = 8.3",
        report.get(
            "stage"
        )
        == "8.3",
        failures,
    )

    for stage in (
        "8.3.1",
        "8.3.2",
        "8.3.3",
        "8.3.4",
    ):

        check(
            f"{stage} PASS",
            sub_stages.get(
                stage
            )
            == "PASS",
            failures,
        )

    check(
        "8.3.5 state valid",
        sub_stages.get(
            "8.3.5"
        )
        in {
            "PENDING",
            "PASS",
        },
        failures,
    )

    check(
        "Current-season source gate VERIFIED",
        report.get(
            "current_season_source_gate"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Overall form engine VERIFIED",
        report.get(
            "overall_form_engine"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Venue form engine VERIFIED",
        report.get(
            "venue_form_engine"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Canonical team form VERIFIED",
        report.get(
            "canonical_team_form"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Team form service VERIFIED",
        report.get(
            "team_form_service"
        )
        == "VERIFIED",
        failures,
    )

    # ========================================================
    # 4. Locked form policy
    # ========================================================

    print(
        "\n4. LOCKED FORM POLICY"
    )

    check(
        "Season = 2026",
        report.get(
            "season"
        )
        == 2026,
        failures,
    )

    check(
        "Form window = 5",
        report.get(
            "form_window"
        )
        == 5,
        failures,
    )

    check(
        "Current season only",
        report.get(
            "season_scope"
        )
        == "CURRENT_PRODUCTION_SEASON_ONLY",
        failures,
    )

    check(
        "Short windows allowed",
        report.get(
            "allow_short_window"
        )
        is True,
        failures,
    )

    check(
        "Results OLDEST_TO_NEWEST",
        report.get(
            "result_order"
        )
        == "OLDEST_TO_NEWEST",
        failures,
    )

    check(
        "Most recent result RIGHTMOST",
        report.get(
            "most_recent_result_position"
        )
        == "RIGHTMOST",
        failures,
    )

    # ========================================================
    # 5. Canonical form artifact
    # ========================================================

    print(
        "\n5. CANONICAL TEAM FORM ARTIFACT"
    )

    try:

        fields, rows = (
            read_team_form_csv()
        )

        csv_read_ok = True

    except Exception as exc:

        print(
            "CSV read error:",
            exc,
        )

        fields = []
        rows = []
        csv_read_ok = False

    check(
        "Canonical CSV readable",
        csv_read_ok,
        failures,
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
            rows
        )
        == 20,
        failures,
    )

    if rows:

        check(
            "20 unique team IDs",
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
            "20 unique team names",
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
                row[
                    "team_name"
                ].casefold()
                for row in rows
            ),
            failures,
        )

    # ========================================================
    # 6. Form arithmetic invariants
    # ========================================================

    print(
        "\n6. FORM ARITHMETIC"
    )

    form_blocks = [

        (
            "OVERALL",
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
            "HOME",
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
            "AWAY",
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
    ) in form_blocks:

        check(
            f"{label} window <= 5",
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
            f"{label} W/D/L only",
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
            f"{label} result length valid",
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
            f"{label} matches = W+D+L",
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
            f"{label} points = 3W+D",
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
            f"{label} GD = GF-GA",
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
    # 7. Independently recompute from production history
    # ========================================================

    print(
        "\n7. INDEPENDENT HISTORY RECOMPUTATION"
    )

    try:

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

        engine_ok = True

    except Exception as exc:

        print(
            "Form-engine error:",
            exc,
        )

        engine_ok = False
        gated = {}
        matches = []

    check(
        "Current-season source gate readable",
        engine_ok,
        failures,
    )

    if engine_ok:

        check(
            "Completed current-season matches > 0",
            len(
                matches
            )
            > 0,
            failures,
        )

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

        expected_rows = (
            build_expected_rows(
                engine,
                matches,
            )
        )

        check(
            "Independent recomputation = 20 teams",
            len(
                expected_rows
            )
            == 20,
            failures,
        )

        check(
            "CSV exactly matches independent recomputation",
            rows
            == expected_rows,
            failures,
        )

        check(
            "History cutoff matches source gate",
            report.get(
                "history_cutoff_utc"
            )
            ==
            gated.get(
                "history_cutoff_utc"
            ),
            failures,
        )

        check(
            "Completed-match count matches report",
            report.get(
                "source_gate",
                {}
            ).get(
                "completed_current_season_matches"
            )
            ==
            gated.get(
                "completed_current_season_matches"
            ),
            failures,
        )

    # ========================================================
    # 8. No leakage / no previous-season padding
    # ========================================================

    print(
        "\n8. TEMPORAL SAFETY"
    )

    source_gate = report.get(
        "source_gate",
        {}
    )

    check(
        "Future matches used = 0",
        source_gate.get(
            "future_matches_used"
        )
        == 0,
        failures,
    )

    check(
        "Previous-season matches used = 0",
        source_gate.get(
            "previous_season_matches_used"
        )
        == 0,
        failures,
    )

    check(
        "Previous-season padding = 0",
        source_gate.get(
            "previous_season_padding"
        )
        == 0,
        failures,
    )

    # ========================================================
    # 9. Artifact identity + provenance
    # ========================================================

    print(
        "\n9. ARTIFACT & PROVENANCE"
    )

    artifact = report.get(
        "current_team_form",
        {}
    )

    actual_form_sha = (
        sha256_file(
            TEAM_FORM_FILE
        )
    )

    check(
        "CSV SHA matches report",
        artifact.get(
            "sha256"
        )
        == actual_form_sha,
        failures,
    )

    check(
        "Reported rows = 20",
        artifact.get(
            "row_count"
        )
        == 20,
        failures,
    )

    check(
        "Reported columns = 29",
        artifact.get(
            "column_count"
        )
        == 29,
        failures,
    )

    check(
        "Reported schema exact",
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
        "generated_at_utc valid",
        valid_aware_timestamp(
            report.get(
                "generated_at_utc"
            )
        ),
        failures,
    )

    check(
        "source_as_of_utc valid",
        valid_aware_timestamp(
            report.get(
                "source_as_of_utc"
            )
        ),
        failures,
    )

    check(
        "history_cutoff_utc valid",
        valid_aware_timestamp(
            report.get(
                "history_cutoff_utc"
            )
        ),
        failures,
    )

    check(
        "source_as_of = history cutoff",
        report.get(
            "source_as_of_utc"
        )
        ==
        report.get(
            "history_cutoff_utc"
        ),
        failures,
    )

    # ========================================================
    # 10. Output contract
    # ========================================================

    print(
        "\n10. OUTPUT CONTRACT"
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
        "current_team_form path locked",
        outputs.get(
            "current_team_form",
            {}
        ).get(
            "path"
        )
        ==
        relative_path(
            TEAM_FORM_FILE
        ),
        failures,
    )

    check(
        "team_form_report path locked",
        outputs.get(
            "team_form_report",
            {}
        ).get(
            "path"
        )
        ==
        relative_path(
            TEAM_FORM_REPORT_FILE
        ),
        failures,
    )

    check(
        "Stage 7 writes prohibited",
        output_contract.get(
            "stage7_output_write_allowed"
        )
        is False,
        failures,
    )

    # ========================================================
    # 11. Dependency identity
    # ========================================================

    print(
        "\n11. DEPENDENCY IDENTITY"
    )

    dependencies = report.get(
        "dependency_identity",
        {}
    )

    check(
        "Stage 8 contract dependency valid",
        dependencies.get(
            "stage8_context_contract",
            {}
        ).get(
            "sha256"
        )
        ==
        sha256_file(
            CONTRACT_FILE
        ),
        failures,
    )

    check(
        "Stage 8.1 verification dependency valid",
        dependencies.get(
            "stage8_context_contract_verification",
            {}
        ).get(
            "sha256"
        )
        ==
        sha256_file(
            CONTRACT_VERIFICATION_FILE
        ),
        failures,
    )

    check(
        "Production history dependency valid",
        dependencies.get(
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

    check(
        "Production-history usage correct",
        dependencies.get(
            "production_history",
            {}
        ).get(
            "usage"
        )
        ==
        "CURRENT_SEASON_COMPLETED_MATCH_FORM",
        failures,
    )

    check(
        "Production history report dependency valid",
        dependencies.get(
            "production_history_report",
            {}
        ).get(
            "sha256"
        )
        ==
        sha256_file(
            HISTORY_REPORT_FILE
        ),
        failures,
    )

    registry_dependency = dependencies.get(
        "current_epl_team_registry",
        {}
    )

    standings_registry = (
        read_standings_registry()
    )

    check(
        "Current team registry count = 20",
        len(
            standings_registry
        )
        == 20,
        failures,
    )

    check(
        "Team registry dependency usage correct",
        registry_dependency.get(
            "usage"
        )
        ==
        "CANONICAL_TEAM_IDENTITY_ONLY",
        failures,
    )

    check(
        "Semantic team registry matches standings",
        registry_dependency.get(
            "semantic_sha256"
        )
        ==
        registry_sha256(
            standings_registry
        ),
        failures,
    )

    check(
        "Semantic team registry matches form CSV",
        registry_dependency.get(
            "semantic_sha256"
        )
        ==
        registry_sha256(
            rows
        ),
        failures,
    )

    # ========================================================
    # 12. Real TeamFormService
    # ========================================================

    print(
        "\n12. REAL TEAM FORM SERVICE"
    )

    service = (
        TeamFormService()
    )

    service_status = (
        service.get_status()
    )

    if (
        service_status.get(
            "status"
        )
        != "READY"
    ):

        print(
            "Service reason:",
            service_status.get(
                "reason"
            ),
        )

    check(
        "Team form service READY",
        service_status.get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "Service stage = 8.3.4",
        service_status.get(
            "stage"
        )
        == "8.3.4",
        failures,
    )

    check(
        "Service team count = 20",
        service_status.get(
            "team_count"
        )
        == 20,
        failures,
    )

    check(
        "Service form window = 5",
        service_status.get(
            "form_window"
        )
        == 5,
        failures,
    )

    check(
        "Service freshness DEPENDENCY_BASED",
        service_status.get(
            "freshness_mode"
        )
        == "DEPENDENCY_BASED",
        failures,
    )

    check(
        "Service dependencies valid",
        service_status.get(
            "dependencies_valid"
        )
        is True,
        failures,
    )

    check(
        "Service team registry valid",
        service_status.get(
            "team_registry_valid"
        )
        is True,
        failures,
    )

    try:

        served_rows = (
            service.get_all_team_form()
        )

        service_read_ok = True

    except Exception:

        served_rows = []
        service_read_ok = False

    check(
        "Service read succeeds",
        service_read_ok,
        failures,
    )

    check(
        "Service returns canonical CSV",
        served_rows
        == rows,
        failures,
    )

    if rows:

        first_team = (
            rows[
                0
            ][
                "team_name"
            ]
        )

        exact_lookup = (
            service.get_team_form(
                first_team
            )
        )

        case_lookup = (
            service.get_team_form(
                first_team.upper()
            )
        )

        check(
            "Exact lookup works",
            (
                exact_lookup
                is not None
                and
                exact_lookup.get(
                    "team_name"
                )
                == first_team
            ),
            failures,
        )

        check(
            "Case-insensitive lookup works",
            (
                case_lookup
                is not None
                and
                case_lookup.get(
                    "team_name"
                )
                == first_team
            ),
            failures,
        )

    check(
        "Unknown team returns None",
        service.get_team_form(
            "Definitely Not An EPL Team"
        )
        is None,
        failures,
    )

    # ========================================================
    # 13. Freshness / fail-closed evidence
    # ========================================================

    print(
        "\n13. FRESHNESS & FAIL-CLOSED EVIDENCE"
    )

    freshness = report.get(
        "freshness",
        {}
    )

    service_freshness = report.get(
        "service_freshness",
        {}
    )

    check(
        "Freshness mode DEPENDENCY_BASED",
        freshness.get(
            "mode"
        )
        == "DEPENDENCY_BASED",
        failures,
    )

    check(
        "History change invalidates form",
        freshness.get(
            "production_history_change_invalidates_form"
        )
        is True,
        failures,
    )

    check(
        "History report change invalidates form",
        freshness.get(
            "production_history_report_change_invalidates_form"
        )
        is True,
        failures,
    )

    check(
        "Team registry change invalidates form",
        freshness.get(
            "current_team_registry_change_invalidates_form"
        )
        is True,
        failures,
    )

    check(
        "Standings numeric change does not invalidate form",
        freshness.get(
            "standings_numeric_change_invalidates_form"
        )
        is False,
        failures,
    )

    check(
        "Stale fallback prohibited",
        freshness.get(
            "stale_fallback_allowed"
        )
        is False,
        failures,
    )

    check(
        "Partial unverified output prohibited",
        freshness.get(
            "partial_unverified_output_allowed"
        )
        is False,
        failures,
    )

    check(
        "Freshness fails closed",
        freshness.get(
            "fail_closed"
        )
        is True,
        failures,
    )

    check(
        "Service freshness VERIFIED",
        service_freshness.get(
            "status"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Artifact hash validation verified",
        service_freshness.get(
            "artifact_hash_validation"
        )
        is True,
        failures,
    )

    check(
        "Production history hash validation verified",
        service_freshness.get(
            "production_history_hash_validation"
        )
        is True,
        failures,
    )

    check(
        "History-report hash validation verified",
        service_freshness.get(
            "production_history_report_hash_validation"
        )
        is True,
        failures,
    )

    check(
        "Semantic registry validation verified",
        service_freshness.get(
            "semantic_team_registry_validation"
        )
        is True,
        failures,
    )

    check(
        "Invalid provenance -> NOT_READY verified",
        service_freshness.get(
            "invalid_provenance_not_ready"
        )
        is True,
        failures,
    )

    check(
        "Missing artifact -> NOT_READY verified",
        service_freshness.get(
            "missing_artifact_not_ready"
        )
        is True,
        failures,
    )

    check(
        "Service fail-closed verified",
        service_freshness.get(
            "fail_closed"
        )
        is True,
        failures,
    )

    # ========================================================
    # 14. Locked model + context safety
    # ========================================================

    print(
        "\n14. MODEL & CONTEXT SAFETY"
    )

    check(
        "Stage 8 context-only",
        contract.get(
            "context_only"
        )
        is True,
        failures,
    )

    locked_model = contract.get(
        "locked_model",
        {}
    )

    actual_model_sha = (
        sha256_file(
            SELECTED_MODEL_FILE
        )
    )

    check(
        "Locked model = random_forest",
        locked_model.get(
            "model_id"
        )
        == "random_forest",
        failures,
    )

    check(
        "Locked feature count = 86",
        locked_model.get(
            "feature_count"
        )
        == 86,
        failures,
    )

    check(
        "Locked model SHA unchanged",
        locked_model.get(
            "sha256"
        )
        == actual_model_sha,
        failures,
    )

    model_protection = contract.get(
        "model_protection",
        {}
    )

    prohibited_flags = [

        "model_mutation_allowed",
        "retraining_allowed",
        "model_selection_allowed",
        "hyperparameter_tuning_allowed",
        "feature_schema_mutation_allowed",
        "prediction_mutation_allowed",
        "final_test_reuse_allowed",
        "standings_as_model_features_allowed",
        "form_as_model_features_allowed",
    ]

    for flag in prohibited_flags:

        check(
            f"{flag} = false",
            model_protection.get(
                flag
            )
            is False,
            failures,
        )

    safety = report.get(
        "safety",
        {}
    )

    check(
        "Team form context-only",
        safety.get(
            "context_only"
        )
        is True,
        failures,
    )

    safety_false_flags = [

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

    for flag in safety_false_flags:

        check(
            f"{flag} = false",
            safety.get(
                flag
            )
            is False,
            failures,
        )

    # ========================================================
    # 15. Final Stage 8.3 decision
    # ========================================================

    print(
        "\n15. STAGE 8.3.5 FINAL DECISION"
    )

    final_pass = (
        len(
            failures
        )
        == 0
    )

    if final_pass:

        verified_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        evidence_sha256 = {

            "stage8_context_contract":
                sha256_file(
                    CONTRACT_FILE
                ),

            "stage8_context_contract_verification":
                sha256_file(
                    CONTRACT_VERIFICATION_FILE
                ),

            "standings_report":
                sha256_file(
                    STANDINGS_REPORT_FILE
                ),

            "current_team_form":
                actual_form_sha,

            "production_history":
                sha256_file(
                    HISTORY_FILE
                ),

            "production_history_report":
                sha256_file(
                    HISTORY_REPORT_FILE
                ),

            "selected_model":
                actual_model_sha,

            "stage7_8_final_verification":
                sha256_file(
                    STAGE7_8_FILE
                ),

            "stage7_9_final_verification":
                sha256_file(
                    STAGE7_9_FILE
                ),
        }

        # ----------------------------------------------------
        # Promote declared team-form report
        # ----------------------------------------------------

        final_report = load_json(
            TEAM_FORM_REPORT_FILE
        )

        final_sub_stages = dict(
            final_report.get(
                "sub_stages",
                {}
            )
        )

        final_sub_stages[
            "8.3.1"
        ] = "PASS"

        final_sub_stages[
            "8.3.2"
        ] = "PASS"

        final_sub_stages[
            "8.3.3"
        ] = "PASS"

        final_sub_stages[
            "8.3.4"
        ] = "PASS"

        final_sub_stages[
            "8.3.5"
        ] = "PASS"

        final_report[
            "sub_stages"
        ] = final_sub_stages

        final_report[
            "status"
        ] = "PASS"

        final_report[
            "stage_8_3_complete"
        ] = True

        final_report[
            "stage_8_3_status"
        ] = "COMPLETE"

        final_report[
            "current_team_form_layer"
        ] = "VERIFIED"

        final_report[
            "stage_8_3_5_verified_at_utc"
        ] = verified_at

        final_report[
            "final_gate"
        ] = {

            "stage":
                "8.3.5",

            "status":
                "PASS",

            "verified_at_utc":
                verified_at,

            "canonical_team_count":
                20,

            "canonical_column_count":
                29,

            "current_season_source_verified":
                True,

            "overall_form_verified":
                True,

            "home_form_verified":
                True,

            "away_form_verified":
                True,

            "independent_history_recomputation_verified":
                True,

            "previous_season_padding":
                0,

            "future_matches_used":
                0,

            "team_form_service_ready":
                True,

            "dependency_freshness_verified":
                True,

            "fail_closed_verified":
                True,

            "locked_model_unchanged":
                True,

            "locked_model_feature_count":
                86,

            "stage7_write_protection":
                True,

            "form_context_only":
                True,
        }

        final_report[
            "evidence_sha256"
        ] = evidence_sha256

        save_json(
            TEAM_FORM_REPORT_FILE,
            final_report,
        )

        # ----------------------------------------------------
        # Verify persisted final state
        # ----------------------------------------------------

        persisted = load_json(
            TEAM_FORM_REPORT_FILE
        )

        check(
            "Final report status PASS persisted",
            persisted.get(
                "status"
            )
            == "PASS",
            failures,
        )

        check(
            "stage_8_3_complete persisted",
            persisted.get(
                "stage_8_3_complete"
            )
            is True,
            failures,
        )

        check(
            "Stage 8.3 COMPLETE persisted",
            persisted.get(
                "stage_8_3_status"
            )
            == "COMPLETE",
            failures,
        )

        check(
            "Current team form layer VERIFIED persisted",
            persisted.get(
                "current_team_form_layer"
            )
            == "VERIFIED",
            failures,
        )

        check(
            "8.3.5 PASS persisted",
            persisted.get(
                "sub_stages",
                {}
            ).get(
                "8.3.5"
            )
            == "PASS",
            failures,
        )

        # ----------------------------------------------------
        # Service must remain READY after final report update
        # ----------------------------------------------------

        final_service_status = (
            TeamFormService()
            .get_status()
        )

        if (
            final_service_status.get(
                "status"
            )
            != "READY"
        ):

            print(
                "Final service reason:",
                final_service_status.get(
                    "reason"
                ),
            )

        check(
            "Team form service remains READY",
            final_service_status.get(
                "status"
            )
            == "READY",
            failures,
        )

        final_pass = (
            len(
                failures
            )
            == 0
        )

    # ========================================================
    # Final output
    # ========================================================

    print(
        "\n" + "=" * 72
    )

    if final_pass:

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
            "STAGE 8.3.4: PASS"
        )

        print(
            "STAGE 8.3.5: PASS"
        )

        print()

        print(
            "STAGE 8.3: COMPLETE"
        )

        print(
            "CURRENT TEAM FORM LAYER: VERIFIED"
        )

    else:

        print(
            "STAGE 8.3.5: FAIL"
        )

        print(
            "STAGE 8.3: INCOMPLETE"
        )

        print(
            "CURRENT TEAM FORM LAYER: NOT VERIFIED"
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
        if final_pass
        else 1
    )


if __name__ == "__main__":

    main()
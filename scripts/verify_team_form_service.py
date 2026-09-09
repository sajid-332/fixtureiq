"""
FixtureIQ Stage 8.3.4
Team Form Service & Dependency-Freshness Verification.

Verifies:
- real service READY
- 20 canonical teams
- exact 29-field public schema
- exact/case-insensitive lookup
- defensive copies
- form artifact tamper -> NOT_READY
- production history change -> NOT_READY
- production history report change -> NOT_READY
- standings numeric-only change -> remains READY
- team identity change -> NOT_READY
- invalid provenance -> NOT_READY
- missing artifact -> NOT_READY
- read methods fail closed

No provider fetch.
No model load.
No model execution.
"""

from __future__ import annotations

import csv
import json
import shutil
import sys
import tempfile
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

from backend.services.team_form_service import (
    EXPECTED_FIELDS,
    TeamFormNotReadyError,
    TeamFormService,
)


# ============================================================
# Real artifact paths
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


# ============================================================
# Helpers
# ============================================================

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


def build_test_copy(
    root: Path,
    name: str,
) -> dict[str, Path]:

    sandbox = (
        root
        / name
    )

    sandbox.mkdir(
        parents=True,
        exist_ok=True,
    )

    paths = {

        "contract":
            sandbox
            / "stage8_context_contract.json",

        "contract_verification":
            sandbox
            / "stage8_context_contract_verification.json",

        "standings":
            sandbox
            / "current_standings.csv",

        "standings_report":
            sandbox
            / "standings_report.json",

        "team_form":
            sandbox
            / "current_team_form.csv",

        "team_form_report":
            sandbox
            / "team_form_report.json",

        "history":
            sandbox
            / "production_history.csv",

        "history_report":
            sandbox
            / "production_history_report.json",
    }

    shutil.copy2(
        CONTRACT_FILE,
        paths[
            "contract"
        ],
    )

    shutil.copy2(
        CONTRACT_VERIFICATION_FILE,
        paths[
            "contract_verification"
        ],
    )

    shutil.copy2(
        STANDINGS_FILE,
        paths[
            "standings"
        ],
    )

    shutil.copy2(
        STANDINGS_REPORT_FILE,
        paths[
            "standings_report"
        ],
    )

    shutil.copy2(
        TEAM_FORM_FILE,
        paths[
            "team_form"
        ],
    )

    shutil.copy2(
        TEAM_FORM_REPORT_FILE,
        paths[
            "team_form_report"
        ],
    )

    shutil.copy2(
        HISTORY_FILE,
        paths[
            "history"
        ],
    )

    shutil.copy2(
        HISTORY_REPORT_FILE,
        paths[
            "history_report"
        ],
    )

    return paths


def make_service(
    paths: dict[str, Path],
) -> TeamFormService:

    return TeamFormService(

        contract_file=
            paths[
                "contract"
            ],

        contract_verification_file=
            paths[
                "contract_verification"
            ],

        standings_file=
            paths[
                "standings"
            ],

        standings_report_file=
            paths[
                "standings_report"
            ],

        team_form_file=
            paths[
                "team_form"
            ],

        team_form_report_file=
            paths[
                "team_form_report"
            ],

        history_file=
            paths[
                "history"
            ],

        history_report_file=
            paths[
                "history_report"
            ],
    )


def alter_standings_numeric_value(
    path: Path,
) -> bool:

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        fieldnames = (
            reader.fieldnames
            or []
        )

        rows = list(
            reader
        )

    candidates = [

        "position",
        "played",
        "won",
        "drawn",
        "lost",
        "goals_for",
        "goals_against",
        "goal_difference",
        "points",
    ]

    target = next(
        (
            field
            for field in candidates
            if field in fieldnames
        ),
        None,
    )

    if (
        target is None
        or
        not rows
    ):

        return False

    current = str(
        rows[
            0
        ].get(
            target,
            "0"
        )
    ).strip()

    try:

        numeric = int(
            current
        )

    except ValueError:

        numeric = 0

    rows[
        0
    ][
        target
    ] = str(
        numeric + 100
    )

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            rows
        )

    return True


def alter_standings_team_identity(
    path: Path,
) -> None:

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        fieldnames = (
            reader.fieldnames
            or []
        )

        rows = list(
            reader
        )

    if not rows:

        raise RuntimeError(
            "Cannot alter empty standings file."
        )

    rows[
        0
    ][
        "team_name"
    ] = "FixtureIQ Broken Team"

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            rows
        )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.3.4"
    )

    print(
        "Team Form Service & Freshness Verification"
    )

    print("=" * 72)

    failures = []

    # ========================================================
    # 1. Required real artifacts
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
    ]

    for path in required:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        sys.exit(1)

    # ========================================================
    # 2. Real service
    # ========================================================

    print(
        "\n2. REAL TEAM FORM SERVICE"
    )

    service = (
        TeamFormService()
    )

    status = (
        service.get_status()
    )

    if (
        status.get(
            "status"
        )
        != "READY"
    ):

        print(
            "Service reason:",
            status.get(
                "reason"
            ),
        )

    check(
        "Service READY",
        status.get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "Stage = 8.3.4",
        status.get(
            "stage"
        )
        == "8.3.4",
        failures,
    )

    check(
        "Service = team_form",
        status.get(
            "service"
        )
        == "team_form",
        failures,
    )

    check(
        "Season = 2026",
        status.get(
            "season"
        )
        == 2026,
        failures,
    )

    check(
        "Form window = 5",
        status.get(
            "form_window"
        )
        == 5,
        failures,
    )

    check(
        "Team count = 20",
        status.get(
            "team_count"
        )
        == 20,
        failures,
    )

    check(
        "Freshness DEPENDENCY_BASED",
        status.get(
            "freshness_mode"
        )
        == "DEPENDENCY_BASED",
        failures,
    )

    check(
        "Dependencies valid",
        status.get(
            "dependencies_valid"
        )
        is True,
        failures,
    )

    check(
        "Team registry valid",
        status.get(
            "team_registry_valid"
        )
        is True,
        failures,
    )

    # ========================================================
    # 3. Public read behavior
    # ========================================================

    print(
        "\n3. PUBLIC READ BEHAVIOR"
    )

    rows = (
        service.get_all_team_form()
    )

    check(
        "get_all_team_form returns 20",
        len(
            rows
        )
        == 20,
        failures,
    )

    check(
        "Exact 29 public fields",
        all(
            list(
                row.keys()
            )
            == EXPECTED_FIELDS
            for row in rows
        ),
        failures,
    )

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
        "Exact team lookup",
        (
            exact_lookup is not None
            and
            exact_lookup.get(
                "team_name"
            )
            == first_team
        ),
        failures,
    )

    check(
        "Case-insensitive exact lookup",
        (
            case_lookup is not None
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

    # Defensive copy
    original_points = (
        rows[
            0
        ][
            "recent_points"
        ]
    )

    rows[
        0
    ][
        "recent_points"
    ] = 999999

    new_rows = (
        service.get_all_team_form()
    )

    check(
        "Returned data is mutation-isolated",
        new_rows[
            0
        ][
            "recent_points"
        ]
        == original_points,
        failures,
    )

    # ========================================================
    # 4. Freshness / failure simulations
    # ========================================================

    print(
        "\n4. DEPENDENCY & FAIL-CLOSED TESTS"
    )

    with tempfile.TemporaryDirectory() as temp_dir:

        root = Path(
            temp_dir
        )

        # ----------------------------------------------------
        # Baseline
        # ----------------------------------------------------

        baseline_paths = (
            build_test_copy(
                root,
                "baseline",
            )
        )

        baseline_service = (
            make_service(
                baseline_paths
            )
        )

        check(
            "Copied baseline READY",
            baseline_service
            .get_status()
            .get(
                "status"
            )
            == "READY",
            failures,
        )

        # ----------------------------------------------------
        # Form artifact tamper
        # ----------------------------------------------------

        form_tamper_paths = (
            build_test_copy(
                root,
                "form_tamper",
            )
        )

        with form_tamper_paths[
            "team_form"
        ].open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                "\n"
            )

        form_tamper_service = (
            make_service(
                form_tamper_paths
            )
        )

        check(
            "Team-form tamper -> NOT_READY",
            form_tamper_service
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Production history changed
        # ----------------------------------------------------

        history_paths = (
            build_test_copy(
                root,
                "history_change",
            )
        )

        with history_paths[
            "history"
        ].open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                " "
            )

        history_service = (
            make_service(
                history_paths
            )
        )

        check(
            "Production history change -> NOT_READY",
            history_service
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Production-history report changed
        # ----------------------------------------------------

        history_report_paths = (
            build_test_copy(
                root,
                "history_report_change",
            )
        )

        with history_report_paths[
            "history_report"
        ].open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                " "
            )

        history_report_service = (
            make_service(
                history_report_paths
            )
        )

        check(
            "History report change -> NOT_READY",
            history_report_service
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Standings numeric-only change
        #
        # Form depends only on canonical identities.
        # ----------------------------------------------------

        standings_numeric_paths = (
            build_test_copy(
                root,
                "standings_numeric_change",
            )
        )

        changed = (
            alter_standings_numeric_value(
                standings_numeric_paths[
                    "standings"
                ]
            )
        )

        check(
            "Standings numeric test available",
            changed,
            failures,
        )

        if changed:

            standings_numeric_service = (
                make_service(
                    standings_numeric_paths
                )
            )

            check(
                (
                    "Standings numeric-only change "
                    "keeps form READY"
                ),
                standings_numeric_service
                .get_status()
                .get(
                    "status"
                )
                == "READY",
                failures,
            )

        # ----------------------------------------------------
        # Team identity changed
        # ----------------------------------------------------

        registry_paths = (
            build_test_copy(
                root,
                "registry_change",
            )
        )

        alter_standings_team_identity(
            registry_paths[
                "standings"
            ]
        )

        registry_service = (
            make_service(
                registry_paths
            )
        )

        check(
            "Current team registry change -> NOT_READY",
            registry_service
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Invalid provenance
        # ----------------------------------------------------

        provenance_paths = (
            build_test_copy(
                root,
                "invalid_provenance",
            )
        )

        provenance_report = (
            load_json(
                provenance_paths[
                    "team_form_report"
                ]
            )
        )

        provenance_report[
            "history_cutoff_utc"
        ] = ""

        save_json(
            provenance_paths[
                "team_form_report"
            ],
            provenance_report,
        )

        provenance_service = (
            make_service(
                provenance_paths
            )
        )

        check(
            "Invalid provenance -> NOT_READY",
            provenance_service
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Missing form artifact
        # ----------------------------------------------------

        missing_paths = (
            build_test_copy(
                root,
                "missing_form",
            )
        )

        missing_paths[
            "team_form"
        ].unlink()

        missing_service = (
            make_service(
                missing_paths
            )
        )

        check(
            "Missing form artifact -> NOT_READY",
            missing_service
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        try:

            missing_service.get_all_team_form()

            failed_closed = False

        except TeamFormNotReadyError:

            failed_closed = True

        check(
            "Read service fails closed",
            failed_closed,
            failures,
        )

    # ========================================================
    # 5. Persist 8.3.4 evidence
    # ========================================================

    print(
        "\n5. SAVE STAGE 8.3.4 VERIFICATION"
    )

    overall_pass = (
        len(
            failures
        )
        == 0
    )

    if overall_pass:

        report = load_json(
            TEAM_FORM_REPORT_FILE
        )

        sub_stages = dict(
            report.get(
                "sub_stages",
                {}
            )
        )

        sub_stages[
            "8.3.4"
        ] = "PASS"

        report[
            "sub_stages"
        ] = sub_stages

        report[
            "status"
        ] = "PARTIAL_PASS"

        report[
            "stage_8_3_complete"
        ] = False

        report[
            "team_form_service"
        ] = "VERIFIED"

        report[
            "freshness"
        ] = {

            "mode":
                "DEPENDENCY_BASED",

            "production_history_change_invalidates_form":
                True,

            "production_history_report_change_invalidates_form":
                True,

            "current_team_registry_change_invalidates_form":
                True,

            "standings_numeric_change_invalidates_form":
                False,

            "stale_fallback_allowed":
                False,

            "partial_unverified_output_allowed":
                False,

            "fail_closed":
                True,
        }

        report[
            "service_freshness"
        ] = {

            "status":
                "VERIFIED",

            "mode":
                "DEPENDENCY_BASED",

            "artifact_hash_validation":
                True,

            "production_history_hash_validation":
                True,

            "production_history_report_hash_validation":
                True,

            "semantic_team_registry_validation":
                True,

            "standings_numeric_change_keeps_form_ready":
                True,

            "team_registry_change_not_ready":
                True,

            "invalid_provenance_not_ready":
                True,

            "missing_artifact_not_ready":
                True,

            "fail_closed":
                True,
        }

        report[
            "stage_8_3_4_verified_at_utc"
        ] = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        save_json(
            TEAM_FORM_REPORT_FILE,
            report,
        )

        # Real artifact must remain servable after report update.
        final_status = (
            TeamFormService()
            .get_status()
        )

        if (
            final_status.get(
                "status"
            )
            != "READY"
        ):

            print(
                "Post-update service reason:",
                final_status.get(
                    "reason"
                ),
            )

        check(
            "Service remains READY after report update",
            final_status.get(
                "status"
            )
            == "READY",
            failures,
        )

        overall_pass = (
            len(
                failures
            )
            == 0
        )

    print(
        TEAM_FORM_REPORT_FILE
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
            "STAGE 8.3.2: PASS"
        )

        print(
            "STAGE 8.3.3: PASS"
        )

        print(
            "STAGE 8.3.4: PASS"
        )

        print(
            "TEAM FORM SERVICE: READY"
        )

        print(
            "DEPENDENCY FRESHNESS: VERIFIED"
        )

        print(
            "STAGE 8.3: IN PROGRESS"
        )

    else:

        print(
            "STAGE 8.3.4: FAIL"
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
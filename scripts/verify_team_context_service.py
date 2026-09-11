"""
FixtureIQ Stage 8.4.4
Team Context Service & Dependency Freshness Verification.

Tests:
- real service READY
- canonical 20 x 38 public output
- exact / case-insensitive lookup
- defensive copies
- team_context tamper -> NOT_READY
- current standings change -> NOT_READY
- standings report change -> NOT_READY
- current team form change -> NOT_READY
- team form report change -> NOT_READY
- production history change -> NOT_READY transitively
- canonical fixture team registry change -> NOT_READY transitively
- invalid provenance -> NOT_READY
- missing context artifact -> NOT_READY
- reads fail closed

No provider fetch.
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

from backend.services.team_context_builder import (
    TEAM_CONTEXT_FIELDS,
)

from backend.services.team_context_service import (
    TeamContextNotReadyError,
    TeamContextService,
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

TEAM_FORM_FILE = (
    CONTEXT_DIR
    / "current_team_form.csv"
)

TEAM_FORM_REPORT_FILE = (
    CONTEXT_DIR
    / "team_form_report.json"
)

TEAM_CONTEXT_FILE = (
    CONTEXT_DIR
    / "team_context.csv"
)

TEAM_CONTEXT_REPORT_FILE = (
    CONTEXT_DIR
    / "team_context_report.json"
)

UPCOMING_FIXTURES_FILE = (
    PRODUCTION_DIR
    / "upcoming_fixtures.csv"
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

        "team_context":
            sandbox
            / "team_context.csv",

        "team_context_report":
            sandbox
            / "team_context_report.json",

        "fixtures":
            sandbox
            / "upcoming_fixtures.csv",

        "history":
            sandbox
            / "production_history.csv",

        "history_report":
            sandbox
            / "production_history_report.json",
    }

    copy_map = {

        CONTRACT_FILE:
            paths[
                "contract"
            ],

        CONTRACT_VERIFICATION_FILE:
            paths[
                "contract_verification"
            ],

        STANDINGS_FILE:
            paths[
                "standings"
            ],

        STANDINGS_REPORT_FILE:
            paths[
                "standings_report"
            ],

        TEAM_FORM_FILE:
            paths[
                "team_form"
            ],

        TEAM_FORM_REPORT_FILE:
            paths[
                "team_form_report"
            ],

        TEAM_CONTEXT_FILE:
            paths[
                "team_context"
            ],

        TEAM_CONTEXT_REPORT_FILE:
            paths[
                "team_context_report"
            ],

        UPCOMING_FIXTURES_FILE:
            paths[
                "fixtures"
            ],

        HISTORY_FILE:
            paths[
                "history"
            ],

        HISTORY_REPORT_FILE:
            paths[
                "history_report"
            ],
    }

    for source, destination in copy_map.items():

        shutil.copy2(
            source,
            destination,
        )

    return paths


def make_service(
    paths: dict[str, Path],
) -> TeamContextService:

    return TeamContextService(

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

        team_context_file=
            paths[
                "team_context"
            ],

        team_context_report_file=
            paths[
                "team_context_report"
            ],

        upcoming_fixtures_file=
            paths[
                "fixtures"
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


def alter_fixture_team_identity(
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
            "Cannot alter empty fixture artifact."
        )

    rows[
        0
    ][
        "home_team_name"
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
        "FixtureIQ Stage 8.4.4"
    )

    print(
        "Team Context Service & Freshness Verification"
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

        TEAM_CONTEXT_FILE,
        TEAM_CONTEXT_REPORT_FILE,

        UPCOMING_FIXTURES_FILE,

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
        "\n2. REAL TEAM CONTEXT SERVICE"
    )

    service = (
        TeamContextService()
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
        "Stage = 8.4.4",
        status.get(
            "stage"
        )
        == "8.4.4",
        failures,
    )

    check(
        "Service = team_context",
        status.get(
            "service"
        )
        == "team_context",
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
        "Team count = 20",
        status.get(
            "team_count"
        )
        == 20,
        failures,
    )

    check(
        "Column count = 38",
        status.get(
            "column_count"
        )
        == 38,
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
        "Upstream services READY",
        status.get(
            "upstream_services_ready"
        )
        is True,
        failures,
    )

    check(
        "Independent reconstruction valid",
        status.get(
            "independent_reconstruction_valid"
        )
        is True,
        failures,
    )

    # ========================================================
    # 3. Public behavior
    # ========================================================

    print(
        "\n3. PUBLIC READ BEHAVIOR"
    )

    rows = (
        service.get_all_team_context()
    )

    check(
        "get_all_team_context returns 20",
        len(
            rows
        )
        == 20,
        failures,
    )

    check(
        "Exact 38 public fields",
        all(
            list(
                row.keys()
            )
            == TEAM_CONTEXT_FIELDS
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
        service.get_team_context(
            first_team
        )
    )

    case_lookup = (
        service.get_team_context(
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
        service.get_team_context(
            "Definitely Not An EPL Team"
        )
        is None,
        failures,
    )

    original_points = (
        rows[
            0
        ][
            "points"
        ]
    )

    rows[
        0
    ][
        "points"
    ] = 999999

    fresh_rows = (
        service.get_all_team_context()
    )

    check(
        "Returned data mutation-isolated",
        fresh_rows[
            0
        ][
            "points"
        ]
        == original_points,
        failures,
    )

    # ========================================================
    # 4. Failure simulations
    # ========================================================

    print(
        "\n4. DEPENDENCY / FAIL-CLOSED TESTS"
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

        check(
            "Copied baseline READY",
            make_service(
                baseline_paths
            )
            .get_status()
            .get(
                "status"
            )
            == "READY",
            failures,
        )

        # ----------------------------------------------------
        # Context artifact tamper
        # ----------------------------------------------------

        context_paths = (
            build_test_copy(
                root,
                "context_tamper",
            )
        )

        with context_paths[
            "team_context"
        ].open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                "\n"
            )

        check(
            "Team-context tamper -> NOT_READY",
            make_service(
                context_paths
            )
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Current standings changed
        # ----------------------------------------------------

        standings_paths = (
            build_test_copy(
                root,
                "standings_change",
            )
        )

        with standings_paths[
            "standings"
        ].open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                "\n"
            )

        check(
            "Current standings change -> NOT_READY",
            make_service(
                standings_paths
            )
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Standings report changed
        # ----------------------------------------------------

        standings_report_paths = (
            build_test_copy(
                root,
                "standings_report_change",
            )
        )

        with standings_report_paths[
            "standings_report"
        ].open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                " "
            )

        check(
            "Standings report change -> NOT_READY",
            make_service(
                standings_report_paths
            )
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Current team form changed
        # ----------------------------------------------------

        form_paths = (
            build_test_copy(
                root,
                "form_change",
            )
        )

        with form_paths[
            "team_form"
        ].open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                "\n"
            )

        check(
            "Current team form change -> NOT_READY",
            make_service(
                form_paths
            )
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Team form report changed
        # ----------------------------------------------------

        form_report_paths = (
            build_test_copy(
                root,
                "form_report_change",
            )
        )

        with form_report_paths[
            "team_form_report"
        ].open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                " "
            )

        check(
            "Team form report change -> NOT_READY",
            make_service(
                form_report_paths
            )
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Production history changes.
        #
        # This is not a direct team-context hash dependency.
        # TeamFormService must detect it transitively.
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

        check(
            "Production history change -> NOT_READY transitively",
            make_service(
                history_paths
            )
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Canonical team registry changes in fixture source.
        #
        # StandingsService must detect this transitively.
        # ----------------------------------------------------

        registry_paths = (
            build_test_copy(
                root,
                "registry_change",
            )
        )

        alter_fixture_team_identity(
            registry_paths[
                "fixtures"
            ]
        )

        check(
            "Team registry change -> NOT_READY transitively",
            make_service(
                registry_paths
            )
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Invalid team-context provenance
        # ----------------------------------------------------

        provenance_paths = (
            build_test_copy(
                root,
                "invalid_provenance",
            )
        )

        provenance_report = load_json(
            provenance_paths[
                "team_context_report"
            ]
        )

        provenance_report[
            "source_as_of_utc"
        ] = ""

        save_json(
            provenance_paths[
                "team_context_report"
            ],
            provenance_report,
        )

        check(
            "Invalid provenance -> NOT_READY",
            make_service(
                provenance_paths
            )
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Missing context artifact
        # ----------------------------------------------------

        missing_paths = (
            build_test_copy(
                root,
                "missing_context",
            )
        )

        missing_paths[
            "team_context"
        ].unlink()

        missing_service = (
            make_service(
                missing_paths
            )
        )

        check(
            "Missing context artifact -> NOT_READY",
            missing_service
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        try:

            missing_service.get_all_team_context()

            read_failed_closed = False

        except TeamContextNotReadyError:

            read_failed_closed = True

        check(
            "Read service fails closed",
            read_failed_closed,
            failures,
        )

    # ========================================================
    # 5. Persist 8.4.4 evidence
    # ========================================================

    print(
        "\n5. SAVE STAGE 8.4.4 VERIFICATION"
    )

    overall_pass = (
        len(
            failures
        )
        == 0
    )

    if overall_pass:

        report = load_json(
            TEAM_CONTEXT_REPORT_FILE
        )

        sub_stages = dict(
            report.get(
                "sub_stages",
                {}
            )
        )

        sub_stages[
            "8.4.4"
        ] = "PASS"

        report[
            "sub_stages"
        ] = sub_stages

        report[
            "status"
        ] = "PARTIAL_PASS"

        report[
            "stage_8_4_complete"
        ] = False

        report[
            "team_context_service"
        ] = "VERIFIED"

        report[
            "service_freshness"
        ] = {

            "status":
                "VERIFIED",

            "mode":
                "DEPENDENCY_BASED",

            "team_context_hash_validation":
                True,

            "current_standings_hash_validation":
                True,

            "standings_report_hash_validation":
                True,

            "current_team_form_hash_validation":
                True,

            "team_form_report_hash_validation":
                True,

            "upstream_standings_service_validation":
                True,

            "upstream_team_form_service_validation":
                True,

            "production_history_transitive_invalidation":
                True,

            "team_registry_transitive_invalidation":
                True,

            "independent_reconstruction_validation":
                True,

            "invalid_provenance_not_ready":
                True,

            "missing_artifact_not_ready":
                True,

            "stale_fallback_allowed":
                False,

            "partial_unverified_output_allowed":
                False,

            "fail_closed":
                True,
        }

        report[
            "stage_8_4_4_verified_at_utc"
        ] = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        save_json(
            TEAM_CONTEXT_REPORT_FILE,
            report,
        )

        final_status = (
            TeamContextService()
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
        TEAM_CONTEXT_REPORT_FILE
    )

    # ========================================================
    # Final
    # ========================================================

    print(
        "\n" + "=" * 72
    )

    if overall_pass:

        print(
            "STAGE 8.4.1: PASS"
        )

        print(
            "STAGE 8.4.2: PASS"
        )

        print(
            "STAGE 8.4.3: PASS"
        )

        print(
            "STAGE 8.4.4: PASS"
        )

        print(
            "TEAM CONTEXT SERVICE: READY"
        )

        print(
            "DEPENDENCY FRESHNESS: VERIFIED"
        )

        print(
            "STAGE 8.4: IN PROGRESS"
        )

    else:

        print(
            "STAGE 8.4.4: FAIL"
        )

        print(
            "STAGE 8.4: INCOMPLETE"
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
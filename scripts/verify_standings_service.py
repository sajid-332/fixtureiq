"""
FixtureIQ Stage 8.2.4
Standings Service & Dependency-Freshness Verification.

Verifies:
- real standings service READY
- canonical read behavior
- case-insensitive exact team lookup
- unknown team behavior
- defensive copies
- artifact tamper rejection
- Stage 8 contract dependency rejection
- semantic team-registry freshness
- normal fixture-only refresh does NOT invalidate standings
- canonical team registry change DOES invalidate standings
- invalid provenance rejection
- missing artifact rejection
- fail-closed behavior

No provider fetch.
No model loading.
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

from backend.services.standings_service import (
    StandingsService,
    StandingsNotReadyError,
)


# ============================================================
# Real paths
# ============================================================

CONTEXT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "context"
)

PRODUCTION_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "production"
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

REPORT_FILE = (
    CONTEXT_DIR
    / "standings_report.json"
)

UPCOMING_FIXTURES_FILE = (
    PRODUCTION_DIR
    / "upcoming_fixtures.csv"
)


EXPECTED_FIELDS = [

    "team_id",
    "team_name",

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

        "verification":
            sandbox
            / "stage8_context_contract_verification.json",

        "standings":
            sandbox
            / "current_standings.csv",

        "report":
            sandbox
            / "standings_report.json",

        "fixtures":
            sandbox
            / "upcoming_fixtures.csv",
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
            "verification"
        ],
    )

    shutil.copy2(
        STANDINGS_FILE,
        paths[
            "standings"
        ],
    )

    shutil.copy2(
        REPORT_FILE,
        paths[
            "report"
        ],
    )

    shutil.copy2(
        UPCOMING_FIXTURES_FILE,
        paths[
            "fixtures"
        ],
    )

    return paths


def make_service(
    paths: dict[str, Path],
) -> StandingsService:

    return StandingsService(

        contract_file=
            paths[
                "contract"
            ],

        contract_verification_file=
            paths[
                "verification"
            ],

        standings_file=
            paths[
                "standings"
            ],

        report_file=
            paths[
                "report"
            ],

        upcoming_fixtures_file=
            paths[
                "fixtures"
            ],
    )


def alter_non_team_fixture_value(
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

    team_fields = {

        "home_team_id",
        "home_team_name",
        "away_team_id",
        "away_team_name",
    }

    candidates = [

        field

        for field in fieldnames

        if field not in team_fields
    ]

    if (
        not candidates
        or
        not rows
    ):

        return False

    field = candidates[
        0
    ]

    rows[
        0
    ][
        field
    ] = (
        str(
            rows[
                0
            ].get(
                field,
                ""
            )
        )
        + "_freshness_test"
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


def corrupt_team_registry(
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
            "Cannot corrupt empty fixtures artifact."
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
        "FixtureIQ Stage 8.2.4"
    )

    print(
        "Standings Service & Freshness Verification"
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
        REPORT_FILE,
        UPCOMING_FIXTURES_FILE,
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
    # 2. Real service readiness
    # ========================================================

    print(
        "\n2. REAL STANDINGS SERVICE"
    )

    service = (
        StandingsService()
    )

    status = (
        service.get_status()
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
        "Stage = 8.2.4",
        status.get(
            "stage"
        )
        == "8.2.4",
        failures,
    )

    check(
        "Service name standings",
        status.get(
            "service"
        )
        == "standings",
        failures,
    )

    check(
        "Provider football-data.org",
        status.get(
            "provider"
        )
        == "football-data.org",
        failures,
    )

    check(
        "Competition code PL",
        status.get(
            "competition_code"
        )
        == "PL",
        failures,
    )

    check(
        "Season 2026",
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

    standings = (
        service.get_standings()
    )

    check(
        "get_standings returns 20",
        len(
            standings
        )
        == 20,
        failures,
    )

    check(
        "Public fields exact",
        all(
            list(
                row.keys()
            )
            == EXPECTED_FIELDS
            for row in standings
        ),
        failures,
    )

    check(
        "Positions 1..20",
        [
            row[
                "position"
            ]
            for row in standings
        ]
        ==
        list(
            range(
                1,
                21,
            )
        ),
        failures,
    )

    first_team = (
        standings[
            0
        ][
            "team_name"
        ]
    )

    lookup = (
        service.get_team_standing(
            first_team
        )
    )

    check(
        "Exact team lookup",
        (
            lookup is not None
            and
            lookup.get(
                "team_name"
            )
            == first_team
        ),
        failures,
    )

    case_lookup = (
        service.get_team_standing(
            first_team.upper()
        )
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
        service.get_team_standing(
            "Definitely Not An EPL Team"
        )
        is None,
        failures,
    )

    # --------------------------------------------------------
    # Defensive-copy test
    # --------------------------------------------------------

    original_points = (
        standings[
            0
        ][
            "points"
        ]
    )

    standings[
        0
    ][
        "points"
    ] = 999999

    fresh_read = (
        service.get_standings()
    )

    check(
        "Returned data is mutation-isolated",
        fresh_read[
            0
        ][
            "points"
        ]
        == original_points,
        failures,
    )

    # ========================================================
    # 4. Runtime fail-closed scenarios
    # ========================================================

    print(
        "\n4. DEPENDENCY / TAMPER SAFETY"
    )

    with tempfile.TemporaryDirectory() as temp_dir:

        root = Path(
            temp_dir
        )

        # ----------------------------------------------------
        # Baseline copy
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
        # Standings tamper
        # ----------------------------------------------------

        tamper_paths = (
            build_test_copy(
                root,
                "standings_tamper",
            )
        )

        with tamper_paths[
            "standings"
        ].open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                "\n"
            )

        tamper_service = (
            make_service(
                tamper_paths
            )
        )

        check(
            "Standings tamper -> NOT_READY",
            tamper_service
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Contract hash changed
        # ----------------------------------------------------

        contract_paths = (
            build_test_copy(
                root,
                "contract_change",
            )
        )

        with contract_paths[
            "contract"
        ].open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                " "
            )

        contract_service = (
            make_service(
                contract_paths
            )
        )

        check(
            "Contract change -> NOT_READY",
            contract_service
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Fixture-only change should NOT invalidate standings
        # ----------------------------------------------------

        fixture_refresh_paths = (
            build_test_copy(
                root,
                "fixture_only_change",
            )
        )

        altered = (
            alter_non_team_fixture_value(
                fixture_refresh_paths[
                    "fixtures"
                ]
            )
        )

        check(
            "Non-team fixture field available",
            altered,
            failures,
        )

        if altered:

            fixture_refresh_service = (
                make_service(
                    fixture_refresh_paths
                )
            )

            check(
                (
                    "Fixture-only refresh keeps "
                    "standings READY"
                ),
                fixture_refresh_service
                .get_status()
                .get(
                    "status"
                )
                == "READY",
                failures,
            )

        # ----------------------------------------------------
        # Canonical team registry changed
        # ----------------------------------------------------

        registry_paths = (
            build_test_copy(
                root,
                "team_registry_change",
            )
        )

        corrupt_team_registry(
            registry_paths[
                "fixtures"
            ]
        )

        registry_service = (
            make_service(
                registry_paths
            )
        )

        check(
            "Team registry change -> NOT_READY",
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
                    "report"
                ]
            )
        )

        provenance_report[
            "generated_at_utc"
        ] = ""

        save_json(
            provenance_paths[
                "report"
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
        # Missing artifact
        # ----------------------------------------------------

        missing_paths = (
            build_test_copy(
                root,
                "missing_artifact",
            )
        )

        missing_paths[
            "standings"
        ].unlink()

        missing_service = (
            make_service(
                missing_paths
            )
        )

        check(
            "Missing standings -> NOT_READY",
            missing_service
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        try:

            missing_service.get_standings()

            read_failed_closed = False

        except StandingsNotReadyError:

            read_failed_closed = True

        check(
            "Read method fails closed",
            read_failed_closed,
            failures,
        )

    # ========================================================
    # 5. Update Stage 8.2 report
    # ========================================================

    print(
        "\n5. SAVE STAGE 8.2.4 VERIFICATION"
    )

    overall_pass = (
        len(
            failures
        )
        == 0
    )

    if overall_pass:

        report = load_json(
            REPORT_FILE
        )

        sub_stages = dict(
            report.get(
                "sub_stages",
                {}
            )
        )

        sub_stages[
            "8.2.4"
        ] = "PASS"

        report[
            "sub_stages"
        ] = sub_stages

        report[
            "status"
        ] = "PARTIAL_PASS"

        report[
            "stage_8_2_complete"
        ] = False

        report[
            "standings_service"
        ] = "VERIFIED"

        report[
            "service_freshness"
        ] = {

            "status":
                "VERIFIED",

            "mode":
                "DEPENDENCY_BASED",

            "fail_closed":
                True,

            "artifact_hash_validation":
                True,

            "contract_hash_validation":
                True,

            "semantic_team_registry_validation":
                True,

            "fixture_only_refresh_invalidates_standings":
                False,

            "team_registry_change_invalidates_standings":
                True,

            "invalid_provenance_not_ready":
                True,

            "missing_artifact_not_ready":
                True,
        }

        report[
            "stage_8_2_4_verified_at_utc"
        ] = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        save_json(
            REPORT_FILE,
            report,
        )

        # Verify the real service remains READY
        # after the report update.
        final_status = (
            StandingsService()
            .get_status()
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
            "STAGE 8.2.1: PASS"
        )

        print(
            "STAGE 8.2.2: PASS"
        )

        print(
            "STAGE 8.2.3: PASS"
        )

        print(
            "STAGE 8.2.4: PASS"
        )

        print(
            "STANDINGS SERVICE: READY"
        )

        print(
            "DEPENDENCY FRESHNESS: VERIFIED"
        )

        print(
            "STAGE 8.2: IN PROGRESS"
        )

    else:

        print(
            "STAGE 8.2.4: FAIL"
        )

        print(
            "STAGE 8.2: INCOMPLETE"
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
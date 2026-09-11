"""
FixtureIQ Stage 8.5.4
Fixture Context Service & Freshness Verification.

Proves:
- real service READY
- canonical public reads
- defensive copies
- direct dependency changes -> NOT_READY
- upstream TeamContextService staleness -> NOT_READY
- production-history change -> NOT_READY transitively
- kickoff boundary reached -> NOT_READY
- invalid provenance -> NOT_READY
- missing artifact -> NOT_READY
- reads fail closed

No provider fetch.
No model execution.
"""

from __future__ import annotations

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

if str(BASE_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(BASE_DIR),
    )


# ============================================================
# Imports
# ============================================================

from backend.services.fixture_context_service import (
    FixtureContextNotReadyError,
    FixtureContextService,
)

from backend.services.team_context_service import (
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

FIXTURE_FETCH_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_fixture_fetch_report.json"
)

ENRICHED_FIXTURES_FILE = (
    CONTEXT_DIR
    / "enriched_upcoming_fixtures.csv"
)

FIXTURE_CONTEXT_REPORT_FILE = (
    CONTEXT_DIR
    / "fixture_context_report.json"
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

        return json.load(file)


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


def parse_aware(
    value,
) -> datetime:

    text = str(value).strip()

    if text.endswith("Z"):

        text = (
            text[:-1]
            + "+00:00"
        )

    result = datetime.fromisoformat(
        text
    )

    if result.tzinfo is None:

        raise RuntimeError(
            "Timestamp is not timezone-aware."
        )

    return result.astimezone(
        timezone.utc
    )


def check(
    label: str,
    condition,
    failures: list[str],
) -> bool:

    passed = bool(condition)

    print(
        f"{label}: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    if not passed:

        failures.append(label)

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

        "upcoming":
            sandbox
            / "upcoming_fixtures.csv",

        "fixture_fetch_report":
            sandbox
            / "production_fixture_fetch_report.json",

        "enriched":
            sandbox
            / "enriched_upcoming_fixtures.csv",

        "fixture_context_report":
            sandbox
            / "fixture_context_report.json",

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
                "upcoming"
            ],

        FIXTURE_FETCH_REPORT_FILE:
            paths[
                "fixture_fetch_report"
            ],

        ENRICHED_FIXTURES_FILE:
            paths[
                "enriched"
            ],

        FIXTURE_CONTEXT_REPORT_FILE:
            paths[
                "fixture_context_report"
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


def make_team_context_service(
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
                "upcoming"
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


def make_fixture_service(
    paths: dict[str, Path],
    *,
    clock=None,
) -> FixtureContextService:

    upstream = (
        make_team_context_service(
            paths
        )
    )

    return FixtureContextService(

        contract_file=
            paths[
                "contract"
            ],

        contract_verification_file=
            paths[
                "contract_verification"
            ],

        upcoming_fixtures_file=
            paths[
                "upcoming"
            ],

        fixture_fetch_report_file=
            paths[
                "fixture_fetch_report"
            ],

        team_context_file=
            paths[
                "team_context"
            ],

        team_context_report_file=
            paths[
                "team_context_report"
            ],

        enriched_fixtures_file=
            paths[
                "enriched"
            ],

        fixture_context_report_file=
            paths[
                "fixture_context_report"
            ],

        team_context_service=
            upstream,

        clock=
            clock,
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.5.4"
    )

    print(
        "Fixture Context Service & Freshness Verification"
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
        FIXTURE_FETCH_REPORT_FILE,

        ENRICHED_FIXTURES_FILE,
        FIXTURE_CONTEXT_REPORT_FILE,

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
        "\n2. REAL FIXTURE CONTEXT SERVICE"
    )

    service = (
        FixtureContextService()
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
        "Stage = 8.5.4",
        status.get(
            "stage"
        )
        == "8.5.4",
        failures,
    )

    check(
        "Service = fixture_context",
        status.get(
            "service"
        )
        == "fixture_context",
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
        "Fixture count > 0",
        status.get(
            "fixture_count",
            0
        )
        > 0,
        failures,
    )

    check(
        "72 context columns",
        status.get(
            "context_column_count"
        )
        == 72,
        failures,
    )

    check(
        "Dependency validation",
        status.get(
            "dependency_validation"
        )
        is True,
        failures,
    )

    check(
        "Temporal boundary valid",
        status.get(
            "temporal_boundary_valid"
        )
        is True,
        failures,
    )

    check(
        "Upstream TeamContextService READY",
        status.get(
            "upstream_team_context_ready"
        )
        is True,
        failures,
    )

    check(
        "Independent validation active",
        status.get(
            "independent_validation"
        )
        is True,
        failures,
    )

    # ========================================================
    # 3. Public reads
    # ========================================================

    print(
        "\n3. PUBLIC READ BEHAVIOR"
    )

    rows = (
        service.get_all_fixture_context()
    )

    check(
        "All fixtures returned",
        len(rows)
        ==
        status.get(
            "fixture_count"
        ),
        failures,
    )

    first = rows[0]

    first_fixture_id = str(
        first[
            "fixture_id"
        ]
    )

    first_home_team = str(
        first[
            "home_team_name"
        ]
    )

    exact_lookup = (
        service.get_fixture_context(
            first_fixture_id
        )
    )

    check(
        "Fixture ID lookup works",
        (
            exact_lookup is not None
            and
            str(
                exact_lookup[
                    "fixture_id"
                ]
            )
            == first_fixture_id
        ),
        failures,
    )

    check(
        "Unknown fixture returns None",
        service.get_fixture_context(
            "fixtureiq-does-not-exist"
        )
        is None,
        failures,
    )

    team_fixtures = (
        service.get_team_fixtures(
            first_home_team
        )
    )

    check(
        "Team fixture lookup works",
        len(
            team_fixtures
        )
        > 0,
        failures,
    )

    team_fixtures_upper = (
        service.get_team_fixtures(
            first_home_team.upper()
        )
    )

    check(
        "Team lookup case-insensitive",
        team_fixtures_upper
        == team_fixtures,
        failures,
    )

    original_home_points = (
        rows[
            0
        ][
            "home_team_points"
        ]
    )

    rows[
        0
    ][
        "home_team_points"
    ] = 999999

    fresh_rows = (
        service.get_all_fixture_context()
    )

    check(
        "Returned data mutation-isolated",
        fresh_rows[
            0
        ][
            "home_team_points"
        ]
        == original_home_points,
        failures,
    )

    # ========================================================
    # 4. Fail-closed simulations
    # ========================================================

    print(
        "\n4. DEPENDENCY / TEMPORAL FAIL-CLOSED TESTS"
    )

    with tempfile.TemporaryDirectory() as temp_dir:

        root = Path(
            temp_dir
        )

        # ----------------------------------------------------
        # Baseline copied environment
        # ----------------------------------------------------

        baseline = build_test_copy(
            root,
            "baseline",
        )

        baseline_status = (
            make_fixture_service(
                baseline
            )
            .get_status()
        )

        if (
            baseline_status.get(
                "status"
            )
            != "READY"
        ):

            print(
                "Copied baseline reason:",
                baseline_status.get(
                    "reason"
                ),
            )

        check(
            "Copied baseline READY",
            baseline_status.get(
                "status"
            )
            == "READY",
            failures,
        )

        # ----------------------------------------------------
        # Enriched artifact changes
        # ----------------------------------------------------

        paths = build_test_copy(
            root,
            "enriched_change",
        )

        with paths[
            "enriched"
        ].open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write("\n")

        check(
            "Enriched fixture change -> NOT_READY",
            make_fixture_service(
                paths
            )
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Upcoming fixture source changes
        # ----------------------------------------------------

        paths = build_test_copy(
            root,
            "upcoming_change",
        )

        with paths[
            "upcoming"
        ].open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write("\n")

        check(
            "Upcoming fixture change -> NOT_READY",
            make_fixture_service(
                paths
            )
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Fixture source report changes
        # ----------------------------------------------------

        paths = build_test_copy(
            root,
            "fixture_report_change",
        )

        with paths[
            "fixture_fetch_report"
        ].open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(" ")

        check(
            "Fixture fetch report change -> NOT_READY",
            make_fixture_service(
                paths
            )
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Team context changes
        # ----------------------------------------------------

        paths = build_test_copy(
            root,
            "team_context_change",
        )

        with paths[
            "team_context"
        ].open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write("\n")

        check(
            "Team context change -> NOT_READY",
            make_fixture_service(
                paths
            )
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Team context report changes
        # ----------------------------------------------------

        paths = build_test_copy(
            root,
            "team_context_report_change",
        )

        with paths[
            "team_context_report"
        ].open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(" ")

        check(
            "Team context report change -> NOT_READY",
            make_fixture_service(
                paths
            )
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Contract changes
        # ----------------------------------------------------

        paths = build_test_copy(
            root,
            "contract_change",
        )

        with paths[
            "contract"
        ].open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(" ")

        check(
            "Stage 8 contract change -> NOT_READY",
            make_fixture_service(
                paths
            )
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Transitive production-history change
        #
        # Fixture context does not directly hash history.
        # TeamContextService must become NOT_READY and cause
        # FixtureContextService to fail closed.
        # ----------------------------------------------------

        paths = build_test_copy(
            root,
            "history_change",
        )

        with paths[
            "history"
        ].open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(" ")

        history_status = (
            make_fixture_service(
                paths
            )
            .get_status()
        )

        if (
            history_status.get(
                "status"
            )
            != "NOT_READY"
        ):

            print(
                "History transitive test status:",
                history_status,
            )

        check(
            "Production history change -> NOT_READY transitively",
            history_status.get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Kickoff temporal boundary
        # ----------------------------------------------------

        paths = build_test_copy(
            root,
            "kickoff_boundary",
        )

        kickoff_report = load_json(
            paths[
                "fixture_context_report"
            ]
        )

        earliest = parse_aware(
            kickoff_report[
                "earliest_fixture_kickoff_utc"
            ]
        )

        temporal_service = (
            make_fixture_service(

                paths,

                clock=lambda:
                    earliest,
            )
        )

        temporal_status = (
            temporal_service.get_status()
        )

        if (
            temporal_status.get(
                "status"
            )
            != "NOT_READY"
        ):

            print(
                "Temporal test status:",
                temporal_status,
            )

        check(
            "Fixture kickoff reached -> NOT_READY",
            temporal_status.get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Invalid fixture provenance
        # ----------------------------------------------------

        paths = build_test_copy(
            root,
            "invalid_provenance",
        )

        invalid_report = load_json(
            paths[
                "fixture_context_report"
            ]
        )

        invalid_report[
            "fixture_snapshot_as_of_utc"
        ] = ""

        save_json(
            paths[
                "fixture_context_report"
            ],
            invalid_report,
        )

        check(
            "Invalid provenance -> NOT_READY",
            make_fixture_service(
                paths
            )
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ----------------------------------------------------
        # Missing canonical artifact
        # ----------------------------------------------------

        paths = build_test_copy(
            root,
            "missing_enriched",
        )

        paths[
            "enriched"
        ].unlink()

        missing_service = (
            make_fixture_service(
                paths
            )
        )

        check(
            "Missing enriched artifact -> NOT_READY",
            missing_service
            .get_status()
            .get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        try:

            missing_service.get_all_fixture_context()

            read_failed_closed = False

        except FixtureContextNotReadyError:

            read_failed_closed = True

        check(
            "Read service fails closed",
            read_failed_closed,
            failures,
        )

    # ========================================================
    # 5. Persist 8.5.4 evidence
    # ========================================================

    print(
        "\n5. SAVE STAGE 8.5.4 EVIDENCE"
    )

    overall_pass = (
        len(failures)
        == 0
    )

    if overall_pass:

        report = load_json(
            FIXTURE_CONTEXT_REPORT_FILE
        )

        sub_stages = dict(
            report.get(
                "sub_stages",
                {}
            )
        )

        sub_stages[
            "8.5.4"
        ] = "PASS"

        report[
            "sub_stages"
        ] = sub_stages

        report[
            "status"
        ] = "PARTIAL_PASS"

        report[
            "stage_8_5_complete"
        ] = False

        report[
            "fixture_context_service"
        ] = "VERIFIED"

        report[
            "service_freshness"
        ] = {

            "status":
                "VERIFIED",

            "mode":
                "DEPENDENCY_BASED_PLUS_TEMPORAL_BOUNDARY",

            "enriched_fixture_validation":
                True,

            "upcoming_fixture_hash_validation":
                True,

            "fixture_fetch_report_hash_validation":
                True,

            "team_context_hash_validation":
                True,

            "team_context_report_hash_validation":
                True,

            "upstream_team_context_service_validation":
                True,

            "independent_validation_reuse":
                True,

            "production_history_transitive_invalidation":
                True,

            "fixture_kickoff_temporal_invalidation":
                True,

            "invalid_provenance_not_ready":
                True,

            "missing_artifact_not_ready":
                True,

            "defensive_copy_validation":
                True,

            "stale_fallback_allowed":
                False,

            "partial_unverified_output_allowed":
                False,

            "fail_closed":
                True,
        }

        report[
            "stage_8_5_4_verified_at_utc"
        ] = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        save_json(
            FIXTURE_CONTEXT_REPORT_FILE,
            report,
        )

        print(
            FIXTURE_CONTEXT_REPORT_FILE
        )

        # ----------------------------------------------------
        # Revalidate after report mutation
        # ----------------------------------------------------

        post_status = (
            FixtureContextService()
            .get_status()
        )

        if (
            post_status.get(
                "status"
            )
            != "READY"
        ):

            print(
                "Post-update service reason:",
                post_status.get(
                    "reason"
                ),
            )

        check(
            "Service remains READY after report update",
            post_status.get(
                "status"
            )
            == "READY",
            failures,
        )

        overall_pass = (
            len(failures)
            == 0
        )

    # ========================================================
    # Final
    # ========================================================

    print(
        "\n" + "=" * 72
    )

    if overall_pass:

        print(
            "STAGE 8.5.1: PASS"
        )

        print(
            "STAGE 8.5.2: PASS"
        )

        print(
            "STAGE 8.5.3: PASS"
        )

        print(
            "STAGE 8.5.4: PASS"
        )

        print(
            "FIXTURE CONTEXT SERVICE: READY"
        )

        print(
            "DEPENDENCY + TEMPORAL FRESHNESS: VERIFIED"
        )

        print(
            "STAGE 8.5: IN PROGRESS"
        )

    else:

        print(
            "STAGE 8.5.4: FAIL"
        )

        print(
            "STAGE 8.5: INCOMPLETE"
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
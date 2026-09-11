"""
FixtureIQ Stage 8.5.1 + 8.5.2 Build Verification.

Independently verifies:
- Stage 8.4 COMPLETE
- TeamContextService READY
- upcoming fixture source integrity
- every fixture remains future
- form cutoff predates every fixture
- team-context snapshot predates every fixture
- exact canonical home/away team identity matches
- source fixture fields are preserved
- 36 home + 36 away context fields appended
- row count preserved
- deterministic ordering
- exact independent reconstruction
- artifact/dependency hashes
- context-only safety boundary
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# Root
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

from backend.services.fixture_context_builder import (
    CONTEXT_FIELDS_APPENDED,
    HOME_CONTEXT_FIELDS,
    AWAY_CONTEXT_FIELDS,
    TEAM_CONTEXT_VALUE_FIELDS,
    build_enriched_fixture_context,
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

UPCOMING_FIXTURES_FILE = (
    PRODUCTION_DIR
    / "upcoming_fixtures.csv"
)

FIXTURE_FETCH_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_fixture_fetch_report.json"
)

TEAM_CONTEXT_FILE = (
    CONTEXT_DIR
    / "team_context.csv"
)

TEAM_CONTEXT_REPORT_FILE = (
    CONTEXT_DIR
    / "team_context_report.json"
)

ENRICHED_FIXTURES_FILE = (
    CONTEXT_DIR
    / "enriched_upcoming_fixtures.csv"
)

REPORT_FILE = (
    CONTEXT_DIR
    / "fixture_context_report.json"
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


def sha256_file(
    path: Path,
) -> str:

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


def parse_aware(
    value,
) -> datetime:

    text = str(
        value
    ).strip()

    if text.endswith(
        "Z"
    ):

        text = (
            text[:-1]
            + "+00:00"
        )

    parsed = datetime.fromisoformat(
        text
    )

    if parsed.tzinfo is None:

        raise ValueError(
            "Timestamp is not timezone-aware."
        )

    return parsed.astimezone(
        timezone.utc
    )


def read_enriched_csv(
    report: dict,
) -> tuple[
    list[str],
    list[dict],
]:

    artifact = report.get(
        "enriched_upcoming_fixtures",
        {}
    )

    expected_fields = artifact.get(
        "columns",
        [],
    )

    with ENRICHED_FIXTURES_FILE.open(
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

    if (
        fields
        != expected_fields
    ):

        raise RuntimeError(
            "Enriched fixture schema differs from report."
        )

    # Convert only appended numerical team-context fields.
    string_context_fields = {

        "recent_results",
        "home_recent_results",
        "away_recent_results",
    }

    rows = []

    for raw in raw_rows:

        row = dict(
            raw
        )

        for prefix in (
            "home_team_",
            "away_team_",
        ):

            for source_field in TEAM_CONTEXT_VALUE_FIELDS:

                output_field = (
                    prefix
                    +
                    source_field
                )

                if (
                    source_field
                    not in string_context_fields
                ):

                    row[
                        output_field
                    ] = int(
                        raw[
                            output_field
                        ]
                    )

        rows.append(
            row
        )

    return (
        fields,
        rows,
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.5.1 + 8.5.2"
    )

    print(
        "Fixture Context Build Verification"
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

        UPCOMING_FIXTURES_FILE,
        FIXTURE_FETCH_REPORT_FILE,

        TEAM_CONTEXT_FILE,
        TEAM_CONTEXT_REPORT_FILE,

        ENRICHED_FIXTURES_FILE,
        REPORT_FILE,
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

    team_context_report = load_json(
        TEAM_CONTEXT_REPORT_FILE
    )

    report = load_json(
        REPORT_FILE
    )

    # ========================================================
    # 2. Foundation
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
        "Stage 8.4 COMPLETE",
        team_context_report.get(
            "stage_8_4_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 8.4 status COMPLETE",
        team_context_report.get(
            "stage_8_4_status"
        )
        == "COMPLETE",
        failures,
    )

    check(
        "Unified Team Context VERIFIED",
        team_context_report.get(
            "unified_team_context_layer"
        )
        == "VERIFIED",
        failures,
    )

    # ========================================================
    # 3. Stage 8.5 report evidence
    # ========================================================

    print(
        "\n3. STAGE 8.5 EVIDENCE"
    )

    sub_stages = report.get(
        "sub_stages",
        {}
    )

    check(
        "Report stage = 8.5",
        report.get(
            "stage"
        )
        == "8.5",
        failures,
    )

    check(
        "8.5.1 PASS",
        sub_stages.get(
            "8.5.1"
        )
        == "PASS",
        failures,
    )

    check(
        "8.5.2 PASS",
        sub_stages.get(
            "8.5.2"
        )
        == "PASS",
        failures,
    )

    check(
        "Fixture source gate VERIFIED",
        report.get(
            "upcoming_fixture_source_gate"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Home/Away context join VERIFIED",
        report.get(
            "home_away_context_join"
        )
        == "VERIFIED",
        failures,
    )

    # ========================================================
    # 4. Real TeamContextService
    # ========================================================

    print(
        "\n4. REAL TEAM CONTEXT SERVICE"
    )

    service = (
        TeamContextService()
    )

    status = (
        service.get_status()
    )

    check(
        "TeamContextService READY",
        status.get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "Context team count = 20",
        status.get(
            "team_count"
        )
        == 20,
        failures,
    )

    # ========================================================
    # 5. Independently rebuild
    # ========================================================

    print(
        "\n5. INDEPENDENT FIXTURE RECONSTRUCTION"
    )

    now_utc = datetime.now(
        timezone.utc
    )

    try:

        expected = (
            build_enriched_fixture_context(

                upcoming_fixtures_file=
                    UPCOMING_FIXTURES_FILE,

                team_context_service=
                    service,

                form_history_cutoff_utc=
                    report[
                        "form_history_cutoff_utc"
                    ],

                context_generated_at_utc=
                    report[
                        "team_context_generated_at_utc"
                    ],

                now_utc=
                    now_utc,
            )
        )

        reconstruction_ok = True

    except Exception as exc:

        print(
            "Reconstruction error:",
            exc,
        )

        expected = {}
        reconstruction_ok = False

    check(
        "Independent reconstruction succeeds",
        reconstruction_ok,
        failures,
    )

    if reconstruction_ok:

        check(
            "All fixtures future",
            expected.get(
                "all_fixtures_future"
            )
            is True,
            failures,
        )

        check(
            "Form cutoff before all fixtures",
            expected.get(
                "form_cutoff_before_all_fixtures"
            )
            is True,
            failures,
        )

        check(
            "Context generated before all fixtures",
            expected.get(
                "context_generated_before_all_fixtures"
            )
            is True,
            failures,
        )

        check(
            "Home context matches",
            expected.get(
                "home_context_match"
            )
            is True,
            failures,
        )

        check(
            "Away context matches",
            expected.get(
                "away_context_match"
            )
            is True,
            failures,
        )

        check(
            "Shared context snapshot",
            expected.get(
                "shared_context_snapshot"
            )
            is True,
            failures,
        )

        check(
            "No future-fixture state propagation",
            expected.get(
                "future_fixture_state_propagation"
            )
            is False,
            failures,
        )

    # ========================================================
    # 6. Read persisted enriched artifact
    # ========================================================

    print(
        "\n6. CANONICAL ENRICHED FIXTURE ARTIFACT"
    )

    try:

        fields, rows = (
            read_enriched_csv(
                report
            )
        )

        read_ok = True

    except Exception as exc:

        print(
            "Enriched CSV error:",
            exc,
        )

        fields = []
        rows = []
        read_ok = False

    check(
        "Enriched CSV readable",
        read_ok,
        failures,
    )

    artifact = report.get(
        "enriched_upcoming_fixtures",
        {}
    )

    check(
        "Artifact schema exact",
        fields
        == artifact.get(
            "columns"
        ),
        failures,
    )

    check(
        "Artifact row count matches report",
        len(
            rows
        )
        == artifact.get(
            "row_count"
        ),
        failures,
    )

    check(
        "Artifact column count matches report",
        len(
            fields
        )
        == artifact.get(
            "column_count"
        ),
        failures,
    )

    check(
        "Artifact SHA matches report",
        sha256_file(
            ENRICHED_FIXTURES_FILE
        )
        ==
        artifact.get(
            "sha256"
        ),
        failures,
    )

    # ========================================================
    # 7. Exact reconstruction comparison
    # ========================================================

    print(
        "\n7. EXACT ENRICHMENT COMPARISON"
    )

    if (
        reconstruction_ok
        and
        read_ok
    ):

        check(
            "Source schema exactly preserved",
            fields[
                :
                expected[
                    "source_column_count"
                ]
            ]
            ==
            expected[
                "source_fields"
            ],
            failures,
        )

        check(
            "36 context fields per team",
            expected.get(
                "context_fields_per_team"
            )
            == 36,
            failures,
        )

        check(
            "36 home context fields",
            len(
                HOME_CONTEXT_FIELDS
            )
            == 36,
            failures,
        )

        check(
            "36 away context fields",
            len(
                AWAY_CONTEXT_FIELDS
            )
            == 36,
            failures,
        )

        check(
            "72 total appended context fields",
            len(
                CONTEXT_FIELDS_APPENDED
            )
            == 72,
            failures,
        )

        check(
            "Output row count preserves source",
            expected.get(
                "enriched_row_count"
            )
            ==
            expected.get(
                "source_row_count"
            ),
            failures,
        )

        check(
            "Persisted rows = independent reconstruction",
            rows
            ==
            expected[
                "enriched_rows"
            ],
            failures,
        )

    # ========================================================
    # 8. Join evidence
    # ========================================================

    print(
        "\n8. HOME/AWAY JOIN CONTRACT"
    )

    join = report.get(
        "context_join",
        {}
    )

    check(
        "Strict canonical identity join",
        join.get(
            "type"
        )
        == "STRICT_CANONICAL_IDENTITY_JOIN",
        failures,
    )

    check(
        "Team ID match required",
        join.get(
            "team_id_match_required"
        )
        is True,
        failures,
    )

    check(
        "Team name match required",
        join.get(
            "team_name_match_required"
        )
        is True,
        failures,
    )

    check(
        "Fuzzy matching prohibited",
        join.get(
            "fuzzy_matching_allowed"
        )
        is False,
        failures,
    )

    check(
        "Missing-context fallback prohibited",
        join.get(
            "missing_context_fallback_allowed"
        )
        is False,
        failures,
    )

    check(
        "72 context fields recorded",
        join.get(
            "total_context_fields_appended"
        )
        == 72,
        failures,
    )

    check(
        "Fixture row count preserved",
        join.get(
            "row_count_preserved"
        )
        is True,
        failures,
    )

    # ========================================================
    # 9. Temporal evidence
    # ========================================================

    print(
        "\n9. TEMPORAL SAFETY"
    )

    temporal = report.get(
        "temporal_gate",
        {}
    )

    check(
        "Report says all fixtures future",
        temporal.get(
            "all_fixtures_future"
        )
        is True,
        failures,
    )

    check(
        "Report form cutoff safe",
        temporal.get(
            "form_history_cutoff_before_all_fixtures"
        )
        is True,
        failures,
    )

    check(
        "Report context snapshot safe",
        temporal.get(
            "team_context_generated_before_all_fixtures"
        )
        is True,
        failures,
    )

    check(
        "Earliest kickoff remains future NOW",
        parse_aware(
            report[
                "earliest_fixture_kickoff_utc"
            ]
        )
        >
        now_utc,
        failures,
    )

    # ========================================================
    # 10. Dependency identity
    # ========================================================

    print(
        "\n10. DEPENDENCY IDENTITY"
    )

    dependencies = report.get(
        "dependency_identity",
        {}
    )

    dependency_checks = [

        (
            "Stage 8 contract hash valid",
            "stage8_context_contract",
            CONTRACT_FILE,
        ),

        (
            "Stage 8 verification hash valid",
            "stage8_context_contract_verification",
            CONTRACT_VERIFICATION_FILE,
        ),

        (
            "Upcoming fixture hash valid",
            "upcoming_fixtures",
            UPCOMING_FIXTURES_FILE,
        ),

        (
            "Fixture fetch report hash valid",
            "production_fixture_fetch_report",
            FIXTURE_FETCH_REPORT_FILE,
        ),

        (
            "Team context hash valid",
            "team_context",
            TEAM_CONTEXT_FILE,
        ),

        (
            "Team context report hash valid",
            "team_context_report",
            TEAM_CONTEXT_REPORT_FILE,
        ),
    ]

    for (
        label,
        dependency_name,
        path,
    ) in dependency_checks:

        check(
            label,
            dependencies.get(
                dependency_name,
                {}
            ).get(
                "sha256"
            )
            ==
            sha256_file(
                path
            ),
            failures,
        )

    # ========================================================
    # 11. Freshness / safety
    # ========================================================

    print(
        "\n11. FRESHNESS & SAFETY"
    )

    freshness = report.get(
        "freshness",
        {}
    )

    check(
        "Freshness mode includes temporal boundary",
        freshness.get(
            "mode"
        )
        ==
        "DEPENDENCY_BASED_PLUS_TEMPORAL_BOUNDARY",
        failures,
    )

    check(
        "Fixture change invalidates context",
        freshness.get(
            "upcoming_fixture_change_invalidates_context"
        )
        is True,
        failures,
    )

    check(
        "Team context change invalidates context",
        freshness.get(
            "team_context_change_invalidates_context"
        )
        is True,
        failures,
    )

    check(
        "Kickoff reached invalidates context",
        freshness.get(
            "fixture_kickoff_reached_invalidates_context"
        )
        is True,
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
        "Fail closed",
        freshness.get(
            "fail_closed"
        )
        is True,
        failures,
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
        "fixture_source_modified",
        "team_context_modified",
        "future_results_used",
        "future_fixture_state_propagation",
        "model_loaded",
        "model_executed",
        "model_modified",
        "production_predictions_modified",
        "feature_schema_modified",
        "fixture_context_used_as_model_features",
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
            "STAGE 8.5.1: PASS"
        )

        print(
            "UPCOMING FIXTURE SOURCE & TEMPORAL GATE: VERIFIED"
        )

        print(
            "STAGE 8.5.2: PASS"
        )

        print(
            "HOME/AWAY FIXTURE CONTEXT: VERIFIED"
        )

        print(
            "STAGE 8.5: IN PROGRESS"
        )

    else:

        print(
            "STAGE 8.5.1 / 8.5.2: FAIL"
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
"""
FixtureIQ Stage 8.5.5
Final Fixture Context Enrichment Layer Gate.

Verifies:
- Stage 8.1 contract remains locked
- Stage 8.4 Unified Team Context Layer remains COMPLETE
- Stage 8.5.1 through 8.5.4 are PASS
- canonical enriched fixture artifact is intact
- source fixture rows are preserved
- 36 home + 36 away context fields remain attached
- independent fixture validator passes
- FixtureContextService remains READY
- dependency freshness remains valid
- temporal freshness remains valid
- shared-snapshot / no-future-propagation policy remains valid
- locked Random Forest remains unchanged
- 86-feature ML boundary remains unchanged
- Stage 8 context remains context-only
- final-test state remains untouched

On PASS:
- 8.5.5 -> PASS
- Stage 8.5 -> COMPLETE
- Fixture Context Enrichment Layer -> VERIFIED

No provider fetch.
No model execution.
No prediction mutation.
No Stage 7 write.
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

if str(BASE_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(BASE_DIR),
    )


# ============================================================
# FixtureIQ imports
# ============================================================

from backend.services.fixture_context_service import (
    FixtureContextService,
)

from backend.services.fixture_context_validator import (
    APPENDED_CONTEXT_FIELDS,
    FixtureContextValidationError,
    FixtureContextValidator,
)

from backend.services.team_context_service import (
    TeamContextService,
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

FIXTURE_CONTEXT_REPORT_FILE = (
    CONTEXT_DIR
    / "fixture_context_report.json"
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

        payload = json.load(file)

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

            digest.update(chunk)

    return digest.hexdigest()


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


def parse_aware(
    value,
    field_name: str,
) -> datetime:

    if not isinstance(
        value,
        str,
    ):

        raise RuntimeError(
            f"{field_name} missing."
        )

    text = value.strip()

    if not text:

        raise RuntimeError(
            f"{field_name} blank."
        )

    if text.endswith("Z"):

        text = (
            text[:-1]
            + "+00:00"
        )

    try:

        parsed = datetime.fromisoformat(
            text
        )

    except ValueError as exc:

        raise RuntimeError(
            f"{field_name} invalid."
        ) from exc

    if parsed.tzinfo is None:

        raise RuntimeError(
            f"{field_name} must be timezone-aware."
        )

    return parsed.astimezone(
        timezone.utc
    )


def read_csv(
    path: Path,
) -> tuple[
    list[str],
    list[dict],
]:

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        fields = (
            reader.fieldnames
            or []
        )

        rows = list(reader)

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
        "FixtureIQ Stage 8.5.5"
    )

    print(
        "Final Fixture Context Enrichment Layer Gate"
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
        FIXTURE_CONTEXT_REPORT_FILE,

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

    team_context_report = load_json(
        TEAM_CONTEXT_REPORT_FILE
    )

    report = load_json(
        FIXTURE_CONTEXT_REPORT_FILE
    )

    stage7_8 = load_json(
        STAGE7_8_FILE
    )

    stage7_9 = load_json(
        STAGE7_9_FILE
    )

    # ========================================================
    # 2. Foundation
    # ========================================================

    print(
        "\n2. FOUNDATION"
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
        "Unified Team Context Layer VERIFIED",
        team_context_report.get(
            "unified_team_context_layer"
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

    # ========================================================
    # 3. Stage 8.5 prior substages
    # ========================================================

    print(
        "\n3. STAGE 8.5 PRIOR EVIDENCE"
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

    for stage in (
        "8.5.1",
        "8.5.2",
        "8.5.3",
        "8.5.4",
    ):

        check(
            f"{stage} PASS",
            sub_stages.get(stage)
            == "PASS",
            failures,
        )

    check(
        "8.5.5 state valid",
        sub_stages.get(
            "8.5.5"
        )
        in {
            "PENDING",
            "PASS",
        },
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

    check(
        "Independent fixture validation VERIFIED",
        report.get(
            "independent_fixture_context_validation"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Fixture context service VERIFIED",
        report.get(
            "fixture_context_service"
        )
        == "VERIFIED",
        failures,
    )

    # ========================================================
    # 4. Canonical fixture artifact
    # ========================================================

    print(
        "\n4. CANONICAL ENRICHED FIXTURE ARTIFACT"
    )

    try:

        (
            source_fields,
            source_rows,
        ) = read_csv(
            UPCOMING_FIXTURES_FILE
        )

        (
            enriched_fields,
            enriched_rows,
        ) = read_csv(
            ENRICHED_FIXTURES_FILE
        )

        csv_ok = True

    except Exception as exc:

        print(
            "CSV error:",
            exc,
        )

        source_fields = []
        source_rows = []

        enriched_fields = []
        enriched_rows = []

        csv_ok = False

    check(
        "Fixture CSV artifacts readable",
        csv_ok,
        failures,
    )

    artifact = report.get(
        "enriched_upcoming_fixtures",
        {}
    )

    check(
        "Source fixture count > 0",
        len(source_rows)
        > 0,
        failures,
    )

    check(
        "Source/output row count equal",
        len(source_rows)
        ==
        len(enriched_rows),
        failures,
    )

    check(
        "Reported fixture count exact",
        report.get(
            "fixture_count"
        )
        ==
        len(enriched_rows),
        failures,
    )

    check(
        "Artifact row count exact",
        artifact.get(
            "row_count"
        )
        ==
        len(enriched_rows),
        failures,
    )

    check(
        "Artifact columns exact",
        artifact.get(
            "columns"
        )
        ==
        enriched_fields,
        failures,
    )

    check(
        "Artifact column count exact",
        artifact.get(
            "column_count"
        )
        ==
        len(enriched_fields),
        failures,
    )

    check(
        "Source column count exact",
        artifact.get(
            "source_column_count"
        )
        ==
        len(source_fields),
        failures,
    )

    check(
        "72 context columns appended",
        artifact.get(
            "context_column_count"
        )
        == 72,
        failures,
    )

    check(
        "Canonical schema = source + 72 context fields",
        enriched_fields
        ==
        source_fields
        +
        APPENDED_CONTEXT_FIELDS,
        failures,
    )

    actual_enriched_sha = (
        sha256_file(
            ENRICHED_FIXTURES_FILE
        )
    )

    check(
        "Enriched artifact SHA exact",
        artifact.get(
            "sha256"
        )
        == actual_enriched_sha,
        failures,
    )

    check(
        "FixtureIQ team namespace",
        artifact.get(
            "team_namespace"
        )
        == "fixtureiq-team",
        failures,
    )

    # ========================================================
    # 5. TeamContextService
    # ========================================================

    print(
        "\n5. UPSTREAM TEAM CONTEXT SERVICE"
    )

    team_service = (
        TeamContextService()
    )

    team_status = (
        team_service.get_status()
    )

    if (
        team_status.get(
            "status"
        )
        != "READY"
    ):

        print(
            "Team context reason:",
            team_status.get(
                "reason"
            ),
        )

    check(
        "TeamContextService READY",
        team_status.get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "Canonical context team count = 20",
        team_status.get(
            "team_count"
        )
        == 20,
        failures,
    )

    # ========================================================
    # 6. Independent fixture validator
    # ========================================================

    print(
        "\n6. INDEPENDENT FIXTURE VALIDATOR"
    )

    try:

        validation = (
            FixtureContextValidator()
            .validate()
        )

        validator_ok = (
            validation.get(
                "status"
            )
            == "PASS"
        )

    except FixtureContextValidationError as exc:

        print(
            "Validator reason:",
            exc,
        )

        validation = {}
        validator_ok = False

    except Exception as exc:

        print(
            "Unexpected validator error:",
            exc,
        )

        validation = {}
        validator_ok = False

    check(
        "Independent validator PASS",
        validator_ok,
        failures,
    )

    if validator_ok:

        check(
            "Fixture IDs unique",
            validation.get(
                "fixture_ids_unique"
            )
            is True,
            failures,
        )

        check(
            "Source fields preserved",
            validation.get(
                "source_fields_preserved"
            )
            is True,
            failures,
        )

        check(
            "Strict home identity verified",
            validation.get(
                "strict_home_identity_verified"
            )
            is True,
            failures,
        )

        check(
            "Strict away identity verified",
            validation.get(
                "strict_away_identity_verified"
            )
            is True,
            failures,
        )

        check(
            "Home context preserved",
            validation.get(
                "home_context_preservation_verified"
            )
            is True,
            failures,
        )

        check(
            "Away context preserved",
            validation.get(
                "away_context_preservation_verified"
            )
            is True,
            failures,
        )

        check(
            "Exact reconstruction verified",
            validation.get(
                "exact_independent_reconstruction_verified"
            )
            is True,
            failures,
        )

        check(
            "All fixtures future",
            validation.get(
                "all_fixtures_future"
            )
            is True,
            failures,
        )

        check(
            "Form cutoff verified",
            validation.get(
                "form_cutoff_verified"
            )
            is True,
            failures,
        )

        check(
            "Temporal context boundary verified",
            validation.get(
                "team_context_temporal_boundary_verified"
            )
            is True,
            failures,
        )

        check(
            "Fixture provenance verified",
            validation.get(
                "fixture_snapshot_provenance_verified"
            )
            is True,
            failures,
        )

        check(
            "Shared snapshot verified",
            validation.get(
                "shared_context_snapshot_verified"
            )
            is True,
            failures,
        )

        check(
            "No future-fixture propagation",
            validation.get(
                "future_fixture_state_propagation"
            )
            is False,
            failures,
        )

        check(
            "Dependency identity verified",
            validation.get(
                "dependency_identity_verified"
            )
            is True,
            failures,
        )

        check(
            "Freshness contract verified",
            validation.get(
                "freshness_contract_verified"
            )
            is True,
            failures,
        )

        check(
            "Safety verified",
            validation.get(
                "safety_verified"
            )
            is True,
            failures,
        )

    # ========================================================
    # 7. FixtureContextService
    # ========================================================

    print(
        "\n7. FIXTURE CONTEXT SERVICE"
    )

    fixture_service = (
        FixtureContextService()
    )

    service_status = (
        fixture_service.get_status()
    )

    if (
        service_status.get(
            "status"
        )
        != "READY"
    ):

        print(
            "Fixture service reason:",
            service_status.get(
                "reason"
            ),
        )

    check(
        "FixtureContextService READY",
        service_status.get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "Service stage = 8.5.4",
        service_status.get(
            "stage"
        )
        == "8.5.4",
        failures,
    )

    check(
        "Service fixture count exact",
        service_status.get(
            "fixture_count"
        )
        ==
        len(enriched_rows),
        failures,
    )

    check(
        "Service 72 context columns",
        service_status.get(
            "context_column_count"
        )
        == 72,
        failures,
    )

    check(
        "Service dependency validation",
        service_status.get(
            "dependency_validation"
        )
        is True,
        failures,
    )

    check(
        "Service temporal boundary valid",
        service_status.get(
            "temporal_boundary_valid"
        )
        is True,
        failures,
    )

    check(
        "Service upstream context READY",
        service_status.get(
            "upstream_team_context_ready"
        )
        is True,
        failures,
    )

    check(
        "Service independent validation",
        service_status.get(
            "independent_validation"
        )
        is True,
        failures,
    )

    try:

        served_rows = (
            fixture_service
            .get_all_fixture_context()
        )

        service_read_ok = True

    except Exception as exc:

        print(
            "Service read error:",
            exc,
        )

        served_rows = []
        service_read_ok = False

    check(
        "Service read succeeds",
        service_read_ok,
        failures,
    )

    check(
        "Service returns every fixture",
        len(served_rows)
        ==
        len(enriched_rows),
        failures,
    )

    # ========================================================
    # 8. Join and snapshot contract
    # ========================================================

    print(
        "\n8. JOIN & SNAPSHOT CONTRACT"
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
        "36 home context fields",
        join.get(
            "home_context_fields_appended"
        )
        == 36,
        failures,
    )

    check(
        "36 away context fields",
        join.get(
            "away_context_fields_appended"
        )
        == 36,
        failures,
    )

    check(
        "72 total context fields",
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

    snapshot_policy = report.get(
        "snapshot_policy",
        {}
    )

    check(
        "Shared context snapshot",
        snapshot_policy.get(
            "shared_context_snapshot"
        )
        is True,
        failures,
    )

    check(
        "Future fixture propagation disabled",
        snapshot_policy.get(
            "future_fixture_state_propagation"
        )
        is False,
        failures,
    )

    check(
        "Future fixtures do not update each other",
        snapshot_policy.get(
            "future_fixtures_update_each_other"
        )
        is False,
        failures,
    )

    check(
        "Pre-kickoff context only",
        snapshot_policy.get(
            "pre_kickoff_context_only"
        )
        is True,
        failures,
    )

    # ========================================================
    # 9. Temporal boundary
    # ========================================================

    print(
        "\n9. TEMPORAL BOUNDARY"
    )

    now_utc = datetime.now(
        timezone.utc
    )

    earliest_kickoff = parse_aware(
        report.get(
            "earliest_fixture_kickoff_utc"
        ),
        "earliest_fixture_kickoff_utc",
    )

    latest_kickoff = parse_aware(
        report.get(
            "latest_fixture_kickoff_utc"
        ),
        "latest_fixture_kickoff_utc",
    )

    form_cutoff = parse_aware(
        report.get(
            "form_history_cutoff_utc"
        ),
        "form_history_cutoff_utc",
    )

    context_generated = parse_aware(
        report.get(
            "team_context_generated_at_utc"
        ),
        "team_context_generated_at_utc",
    )

    check(
        "Earliest fixture still future",
        earliest_kickoff
        > now_utc,
        failures,
    )

    check(
        "Latest kickoff after earliest",
        latest_kickoff
        >= earliest_kickoff,
        failures,
    )

    check(
        "Form cutoff before earliest fixture",
        form_cutoff
        <
        earliest_kickoff,
        failures,
    )

    check(
        "Team context generated before earliest fixture",
        context_generated
        <
        earliest_kickoff,
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
            "Stage 8 contract dependency valid",
            "stage8_context_contract",
            CONTRACT_FILE,
        ),

        (
            "Stage 8 verification dependency valid",
            "stage8_context_contract_verification",
            CONTRACT_VERIFICATION_FILE,
        ),

        (
            "Upcoming fixtures dependency valid",
            "upcoming_fixtures",
            UPCOMING_FIXTURES_FILE,
        ),

        (
            "Fixture fetch report dependency valid",
            "production_fixture_fetch_report",
            FIXTURE_FETCH_REPORT_FILE,
        ),

        (
            "Team context dependency valid",
            "team_context",
            TEAM_CONTEXT_FILE,
        ),

        (
            "Team context report dependency valid",
            "team_context_report",
            TEAM_CONTEXT_REPORT_FILE,
        ),
    ]

    for (
        label,
        name,
        path,
    ) in dependency_checks:

        check(
            label,
            dependencies.get(
                name,
                {}
            ).get(
                "sha256"
            )
            ==
            sha256_file(path),
            failures,
        )

    check(
        "Upcoming fixture usage correct",
        dependencies.get(
            "upcoming_fixtures",
            {}
        ).get(
            "usage"
        )
        == "UPCOMING_FIXTURE_SOURCE",
        failures,
    )

    check(
        "Fixture report usage correct",
        dependencies.get(
            "production_fixture_fetch_report",
            {}
        ).get(
            "usage"
        )
        == "FIXTURE_SOURCE_PROVENANCE",
        failures,
    )

    check(
        "Team context usage correct",
        dependencies.get(
            "team_context",
            {}
        ).get(
            "usage"
        )
        == "FULL_HOME_AWAY_CONTEXT",
        failures,
    )

    check(
        "Team context report usage correct",
        dependencies.get(
            "team_context_report",
            {}
        ).get(
            "usage"
        )
        == "VERIFIED_TEAM_CONTEXT_PROVENANCE",
        failures,
    )

    # ========================================================
    # 11. Freshness evidence
    # ========================================================

    print(
        "\n11. FRESHNESS & FAIL-CLOSED EVIDENCE"
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
        "Freshness mode correct",
        freshness.get(
            "mode"
        )
        ==
        "DEPENDENCY_BASED_PLUS_TEMPORAL_BOUNDARY",
        failures,
    )

    direct_freshness_flags = [

        "upcoming_fixture_change_invalidates_context",
        "fixture_fetch_report_change_invalidates_context",
        "team_context_change_invalidates_context",
        "team_context_report_change_invalidates_context",
        "fixture_kickoff_reached_invalidates_context",
        "fail_closed",
    ]

    for flag in direct_freshness_flags:

        check(
            f"{flag} = true",
            freshness.get(flag)
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
        "Partial unverified output prohibited",
        freshness.get(
            "partial_unverified_output_allowed"
        )
        is False,
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
        "Service freshness mode correct",
        service_freshness.get(
            "mode"
        )
        ==
        "DEPENDENCY_BASED_PLUS_TEMPORAL_BOUNDARY",
        failures,
    )

    service_true_flags = [

        "enriched_fixture_validation",
        "upcoming_fixture_hash_validation",
        "fixture_fetch_report_hash_validation",
        "team_context_hash_validation",
        "team_context_report_hash_validation",
        "upstream_team_context_service_validation",
        "independent_validation_reuse",
        "production_history_transitive_invalidation",
        "fixture_kickoff_temporal_invalidation",
        "invalid_provenance_not_ready",
        "missing_artifact_not_ready",
        "defensive_copy_validation",
        "fail_closed",
    ]

    for flag in service_true_flags:

        check(
            f"{flag} verified",
            service_freshness.get(flag)
            is True,
            failures,
        )

    check(
        "Service stale fallback prohibited",
        service_freshness.get(
            "stale_fallback_allowed"
        )
        is False,
        failures,
    )

    check(
        "Service partial output prohibited",
        service_freshness.get(
            "partial_unverified_output_allowed"
        )
        is False,
        failures,
    )

    # ========================================================
    # 12. Legacy fixture provenance
    # ========================================================

    print(
        "\n12. FIXTURE SNAPSHOT PROVENANCE"
    )

    provider_timestamp_available = (
        report.get(
            "fixture_provider_timestamp_available"
        )
    )

    provenance_mode = report.get(
        "fixture_snapshot_provenance_mode"
    )

    if (
        provider_timestamp_available
        is False
    ):

        check(
            "Legacy Stage 7 timestamp absence recorded",
            report.get(
                "legacy_fixture_report_timestamp_missing"
            )
            is True,
            failures,
        )

        check(
            "Stage 8 observation provenance used",
            provenance_mode
            ==
            "STAGE8_VERIFIED_ARTIFACT_OBSERVATION",
            failures,
        )

        check(
            "Provider timestamp not fabricated",
            report.get(
                "safety",
                {}
            ).get(
                "provider_timestamp_fabricated"
            )
            is False,
            failures,
        )

        check(
            "Filesystem mtime not used",
            report.get(
                "safety",
                {}
            ).get(
                "filesystem_mtime_used_as_provenance"
            )
            is False,
            failures,
        )

    else:

        check(
            "Provider provenance mode valid",
            provenance_mode
            ==
            "PROVIDER_REPORTED_TIMESTAMP",
            failures,
        )

    # ========================================================
    # 13. Locked ML boundary
    # ========================================================

    print(
        "\n13. LOCKED MODEL PROTECTION"
    )

    locked_model = contract.get(
        "locked_model",
        {}
    )

    actual_model_sha = sha256_file(
        SELECTED_MODEL_FILE
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

    model_false_flags = [

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

    for flag in model_false_flags:

        check(
            f"{flag} = false",
            model_protection.get(flag)
            is False,
            failures,
        )

    # ========================================================
    # 14. Safety boundary
    # ========================================================

    print(
        "\n14. CONTEXT SAFETY BOUNDARY"
    )

    check(
        "Stage 8 context-only",
        contract.get(
            "context_only"
        )
        is True,
        failures,
    )

    safety = report.get(
        "safety",
        {}
    )

    check(
        "Fixture context context-only",
        safety.get(
            "context_only"
        )
        is True,
        failures,
    )

    false_safety_flags = [

        "stage7_artifacts_modified",
        "legacy_stage7_report_modified",
        "provider_timestamp_fabricated",
        "filesystem_mtime_used_as_provenance",
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

    for flag in false_safety_flags:

        check(
            f"{flag} = false",
            safety.get(flag)
            is False,
            failures,
        )

    # ========================================================
    # 15. Final decision
    # ========================================================

    print(
        "\n15. STAGE 8.5.5 FINAL DECISION"
    )

    final_pass = (
        len(failures)
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

            "upcoming_fixtures":
                sha256_file(
                    UPCOMING_FIXTURES_FILE
                ),

            "production_fixture_fetch_report":
                sha256_file(
                    FIXTURE_FETCH_REPORT_FILE
                ),

            "team_context":
                sha256_file(
                    TEAM_CONTEXT_FILE
                ),

            "team_context_report":
                sha256_file(
                    TEAM_CONTEXT_REPORT_FILE
                ),

            "enriched_upcoming_fixtures":
                actual_enriched_sha,

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

        final_report = load_json(
            FIXTURE_CONTEXT_REPORT_FILE
        )

        final_sub_stages = dict(
            final_report.get(
                "sub_stages",
                {}
            )
        )

        final_sub_stages[
            "8.5.1"
        ] = "PASS"

        final_sub_stages[
            "8.5.2"
        ] = "PASS"

        final_sub_stages[
            "8.5.3"
        ] = "PASS"

        final_sub_stages[
            "8.5.4"
        ] = "PASS"

        final_sub_stages[
            "8.5.5"
        ] = "PASS"

        final_report[
            "sub_stages"
        ] = final_sub_stages

        final_report[
            "status"
        ] = "PASS"

        final_report[
            "stage_8_5_complete"
        ] = True

        final_report[
            "stage_8_5_status"
        ] = "COMPLETE"

        final_report[
            "fixture_context_enrichment_layer"
        ] = "VERIFIED"

        final_report[
            "stage_8_5_5_verified_at_utc"
        ] = verified_at

        final_report[
            "final_gate"
        ] = {

            "stage":
                "8.5.5",

            "status":
                "PASS",

            "verified_at_utc":
                verified_at,

            "fixture_count":
                len(
                    enriched_rows
                ),

            "context_team_count":
                20,

            "home_context_fields":
                36,

            "away_context_fields":
                36,

            "total_context_fields":
                72,

            "source_fixture_preservation_verified":
                True,

            "strict_home_identity_verified":
                True,

            "strict_away_identity_verified":
                True,

            "home_context_preservation_verified":
                True,

            "away_context_preservation_verified":
                True,

            "independent_reconstruction_verified":
                True,

            "shared_context_snapshot_verified":
                True,

            "future_fixture_state_propagation":
                False,

            "fixture_context_service_ready":
                True,

            "dependency_freshness_verified":
                True,

            "transitive_freshness_verified":
                True,

            "temporal_freshness_verified":
                True,

            "fail_closed_verified":
                True,

            "locked_model_unchanged":
                True,

            "locked_model_feature_count":
                86,

            "fixture_context_used_as_model_features":
                False,

            "stage7_write_protection":
                True,

            "context_only":
                True,

            "final_test_untouched":
                True,
        }

        final_report[
            "evidence_sha256"
        ] = evidence_sha256

        save_json(
            FIXTURE_CONTEXT_REPORT_FILE,
            final_report,
        )

        # ====================================================
        # Persisted final state
        # ====================================================

        persisted = load_json(
            FIXTURE_CONTEXT_REPORT_FILE
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
            "stage_8_5_complete persisted",
            persisted.get(
                "stage_8_5_complete"
            )
            is True,
            failures,
        )

        check(
            "Stage 8.5 COMPLETE persisted",
            persisted.get(
                "stage_8_5_status"
            )
            == "COMPLETE",
            failures,
        )

        check(
            "Fixture Context Enrichment Layer VERIFIED persisted",
            persisted.get(
                "fixture_context_enrichment_layer"
            )
            == "VERIFIED",
            failures,
        )

        check(
            "8.5.5 PASS persisted",
            persisted.get(
                "sub_stages",
                {}
            ).get(
                "8.5.5"
            )
            == "PASS",
            failures,
        )

        # ====================================================
        # Revalidate after promotion
        # ====================================================

        try:

            post_validation = (
                FixtureContextValidator()
                .validate()
            )

            post_validator_ok = (
                post_validation.get(
                    "status"
                )
                == "PASS"
            )

        except Exception as exc:

            print(
                "Post-promotion validator error:",
                exc,
            )

            post_validator_ok = False

        check(
            "Independent validator remains PASS",
            post_validator_ok,
            failures,
        )

        post_service_status = (
            FixtureContextService()
            .get_status()
        )

        if (
            post_service_status.get(
                "status"
            )
            != "READY"
        ):

            print(
                "Post-promotion service reason:",
                post_service_status.get(
                    "reason"
                ),
            )

        check(
            "FixtureContextService remains READY",
            post_service_status.get(
                "status"
            )
            == "READY",
            failures,
        )

        final_pass = (
            len(failures)
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
            "STAGE 8.5.5: PASS"
        )

        print()

        print(
            "STAGE 8.5: COMPLETE"
        )

        print(
            "FIXTURE CONTEXT ENRICHMENT LAYER: VERIFIED"
        )

    else:

        print(
            "STAGE 8.5.5: FAIL"
        )

        print(
            "STAGE 8.5: INCOMPLETE"
        )

        print(
            "FIXTURE CONTEXT ENRICHMENT LAYER: NOT VERIFIED"
        )

        if failures:

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
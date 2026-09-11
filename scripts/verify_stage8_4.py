"""
FixtureIQ Stage 8.4.5
Final Unified Team Context Layer Gate.

Verifies:
- Stage 8.1 contract remains locked
- Stage 8.2 standings layer COMPLETE
- Stage 8.3 team-form layer COMPLETE
- Stage 8.4.1 through 8.4.4 PASS
- canonical team_context.csv is exactly 20 x 38
- independent validator passes
- TeamContextService is READY
- service output exactly matches canonical artifact
- dependency freshness evidence is verified
- context remains context-only
- locked Random Forest remains unchanged
- 86-feature boundary remains unchanged
- predictions/model/final-test state untouched

On PASS:
- 8.4.5 -> PASS
- Stage 8.4 -> COMPLETE
- Unified Team Context Layer -> VERIFIED

No provider fetch.
No model execution.
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

from backend.services.team_context_builder import (
    TEAM_CONTEXT_FIELDS,
)

from backend.services.team_context_validator import (
    TeamContextValidationError,
    TeamContextValidator,
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
# Canonical CSV typing
# ============================================================

INTEGER_FIELDS = [

    field

    for field in TEAM_CONTEXT_FIELDS

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


def valid_timestamp(
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

    if text.endswith("Z"):

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

    return parsed.tzinfo is not None


def read_context_csv() -> tuple[
    list[str],
    list[dict],
]:

    with TEAM_CONTEXT_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        fields = (
            reader.fieldnames
            or []
        )

        raw_rows = list(reader)

    rows = []

    for raw in raw_rows:

        row = dict(raw)

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

            row[field] = int(
                raw[field]
            )

        rows.append(row)

    return fields, rows


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.4.5"
    )

    print(
        "Final Unified Team Context Layer Gate"
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

    form_report = load_json(
        TEAM_FORM_REPORT_FILE
    )

    report = load_json(
        TEAM_CONTEXT_REPORT_FILE
    )

    stage7_8 = load_json(
        STAGE7_8_FILE
    )

    stage7_9 = load_json(
        STAGE7_9_FILE
    )

    # ========================================================
    # 2. Upstream completion chain
    # ========================================================

    print(
        "\n2. UPSTREAM COMPLETION CHAIN"
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
        "Stage 8.3 COMPLETE",
        form_report.get(
            "stage_8_3_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 8.3 status COMPLETE",
        form_report.get(
            "stage_8_3_status"
        )
        == "COMPLETE",
        failures,
    )

    check(
        "Current team form layer VERIFIED",
        form_report.get(
            "current_team_form_layer"
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
    # 3. Stage 8.4 previous substages
    # ========================================================

    print(
        "\n3. STAGE 8.4 PRIOR EVIDENCE"
    )

    sub_stages = report.get(
        "sub_stages",
        {}
    )

    check(
        "Report stage = 8.4",
        report.get(
            "stage"
        )
        == "8.4",
        failures,
    )

    for stage in (
        "8.4.1",
        "8.4.2",
        "8.4.3",
        "8.4.4",
    ):

        check(
            f"{stage} PASS",
            sub_stages.get(stage)
            == "PASS",
            failures,
        )

    check(
        "8.4.5 state valid",
        sub_stages.get(
            "8.4.5"
        )
        in {
            "PENDING",
            "PASS",
        },
        failures,
    )

    check(
        "Upstream context readiness VERIFIED",
        report.get(
            "upstream_context_readiness"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Unified builder VERIFIED",
        report.get(
            "unified_team_context_builder"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Independent context validation VERIFIED",
        report.get(
            "independent_context_validation"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Team context service VERIFIED",
        report.get(
            "team_context_service"
        )
        == "VERIFIED",
        failures,
    )

    # ========================================================
    # 4. Canonical team-context artifact
    # ========================================================

    print(
        "\n4. CANONICAL TEAM CONTEXT"
    )

    try:

        fields, rows = (
            read_context_csv()
        )

        csv_ok = True

    except Exception as exc:

        print(
            "CSV error:",
            exc,
        )

        fields = []
        rows = []
        csv_ok = False

    check(
        "Canonical CSV readable",
        csv_ok,
        failures,
    )

    check(
        "Exact 38-column schema",
        fields
        == TEAM_CONTEXT_FIELDS,
        failures,
    )

    check(
        "Column count = 38",
        len(fields)
        == 38,
        failures,
    )

    check(
        "Row count = 20",
        len(rows)
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

        check(
            "Positions exactly 1..20",
            sorted(
                row[
                    "position"
                ]
                for row in rows
            )
            ==
            list(
                range(
                    1,
                    21,
                )
            ),
            failures,
        )

    artifact = report.get(
        "team_context",
        {}
    )

    actual_context_sha = (
        sha256_file(
            TEAM_CONTEXT_FILE
        )
    )

    check(
        "Context SHA matches report",
        artifact.get(
            "sha256"
        )
        == actual_context_sha,
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
        "Reported columns = 38",
        artifact.get(
            "column_count"
        )
        == 38,
        failures,
    )

    check(
        "Reported schema exact",
        artifact.get(
            "columns"
        )
        == TEAM_CONTEXT_FIELDS,
        failures,
    )

    check(
        "FixtureIQ namespace",
        artifact.get(
            "team_namespace"
        )
        == "fixtureiq-team",
        failures,
    )

    # ========================================================
    # 5. Independent validator
    # ========================================================

    print(
        "\n5. INDEPENDENT CONTEXT VALIDATOR"
    )

    try:

        validation = (
            TeamContextValidator()
            .validate()
        )

        validation_ok = (
            validation.get(
                "status"
            )
            == "PASS"
        )

    except TeamContextValidationError as exc:

        print(
            "Validation reason:",
            exc,
        )

        validation = {}
        validation_ok = False

    except Exception as exc:

        print(
            "Unexpected validator error:",
            exc,
        )

        validation = {}
        validation_ok = False

    check(
        "Independent validator PASS",
        validation_ok,
        failures,
    )

    if validation_ok:

        check(
            "Validator team count = 20",
            validation.get(
                "team_count"
            )
            == 20,
            failures,
        )

        check(
            "Validator column count = 38",
            validation.get(
                "column_count"
            )
            == 38,
            failures,
        )

        check(
            "Independent join verified",
            validation.get(
                "independent_join_verified"
            )
            is True,
            failures,
        )

        check(
            "Standings arithmetic verified",
            validation.get(
                "standings_arithmetic_verified"
            )
            is True,
            failures,
        )

        check(
            "Overall form verified",
            validation.get(
                "overall_form_verified"
            )
            is True,
            failures,
        )

        check(
            "Home form verified",
            validation.get(
                "home_form_verified"
            )
            is True,
            failures,
        )

        check(
            "Away form verified",
            validation.get(
                "away_form_verified"
            )
            is True,
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
            "Provenance verified",
            validation.get(
                "provenance_verified"
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
    # 6. Real TeamContextService
    # ========================================================

    print(
        "\n6. REAL TEAM CONTEXT SERVICE"
    )

    service = (
        TeamContextService()
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
        "TeamContextService READY",
        service_status.get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "Service stage = 8.4.4",
        service_status.get(
            "stage"
        )
        == "8.4.4",
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
        "Service column count = 38",
        service_status.get(
            "column_count"
        )
        == 38,
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
        "Upstream services READY",
        service_status.get(
            "upstream_services_ready"
        )
        is True,
        failures,
    )

    check(
        "Independent reconstruction valid",
        service_status.get(
            "independent_reconstruction_valid"
        )
        is True,
        failures,
    )

    try:

        served_rows = (
            service.get_all_team_context()
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
        "Service exactly matches canonical artifact",
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

        check(
            "Exact lookup works",
            (
                service.get_team_context(
                    first_team
                )
                is not None
            ),
            failures,
        )

        check(
            "Case-insensitive lookup works",
            (
                service.get_team_context(
                    first_team.upper()
                )
                is not None
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

    # ========================================================
    # 7. Join contract
    # ========================================================

    print(
        "\n7. ONE-TO-ONE JOIN CONTRACT"
    )

    join = report.get(
        "join",
        {}
    )

    check(
        "Join type ONE_TO_ONE",
        join.get(
            "type"
        )
        == "ONE_TO_ONE",
        failures,
    )

    check(
        "Join identity match",
        join.get(
            "identity_match"
        )
        is True,
        failures,
    )

    check(
        "Standings input rows = 20",
        join.get(
            "standings_rows"
        )
        == 20,
        failures,
    )

    check(
        "Form input rows = 20",
        join.get(
            "form_rows"
        )
        == 20,
        failures,
    )

    check(
        "Output rows = 20",
        join.get(
            "output_rows"
        )
        == 20,
        failures,
    )

    check(
        "No missing standings teams",
        join.get(
            "missing_standings_teams"
        )
        == 0,
        failures,
    )

    check(
        "No missing form teams",
        join.get(
            "missing_form_teams"
        )
        == 0,
        failures,
    )

    check(
        "No duplicate output teams",
        join.get(
            "duplicate_output_teams"
        )
        == 0,
        failures,
    )

    # ========================================================
    # 8. Dependency identity
    # ========================================================

    print(
        "\n8. DEPENDENCY IDENTITY"
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
            "Current standings dependency valid",
            "current_standings",
            STANDINGS_FILE,
        ),

        (
            "Standings report dependency valid",
            "standings_report",
            STANDINGS_REPORT_FILE,
        ),

        (
            "Current team form dependency valid",
            "current_team_form",
            TEAM_FORM_FILE,
        ),

        (
            "Team form report dependency valid",
            "team_form_report",
            TEAM_FORM_REPORT_FILE,
        ),
    ]

    for (
        label,
        dependency_name,
        dependency_path,
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
                dependency_path
            ),
            failures,
        )

    check(
        "Standings dependency usage correct",
        dependencies.get(
            "current_standings",
            {}
        ).get(
            "usage"
        )
        == "FULL_STANDINGS_CONTEXT",
        failures,
    )

    check(
        "Form dependency usage correct",
        dependencies.get(
            "current_team_form",
            {}
        ).get(
            "usage"
        )
        == "FULL_CURRENT_FORM_CONTEXT",
        failures,
    )

    # ========================================================
    # 9. Provenance
    # ========================================================

    print(
        "\n9. PROVENANCE"
    )

    provenance_fields = (

        "generated_at_utc",
        "source_as_of_utc",
        "standings_source_as_of_utc",
        "form_source_as_of_utc",
        "form_history_cutoff_utc",
    )

    for field in provenance_fields:

        check(
            f"{field} valid",
            valid_timestamp(
                report.get(field)
            ),
            failures,
        )

    check(
        "Competition code = PL",
        report.get(
            "competition_code"
        )
        == "PL",
        failures,
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
        "Team namespace = fixtureiq-team",
        report.get(
            "team_namespace"
        )
        == "fixtureiq-team",
        failures,
    )

    check(
        "Reported team count = 20",
        report.get(
            "team_count"
        )
        == 20,
        failures,
    )

    # ========================================================
    # 10. Freshness evidence
    # ========================================================

    print(
        "\n10. FRESHNESS & FAIL-CLOSED EVIDENCE"
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
        "Freshness DEPENDENCY_BASED",
        freshness.get(
            "mode"
        )
        == "DEPENDENCY_BASED",
        failures,
    )

    check(
        "Standings change invalidates context",
        freshness.get(
            "current_standings_change_invalidates_context"
        )
        is True,
        failures,
    )

    check(
        "Standings report change invalidates context",
        freshness.get(
            "standings_report_change_invalidates_context"
        )
        is True,
        failures,
    )

    check(
        "Form change invalidates context",
        freshness.get(
            "current_team_form_change_invalidates_context"
        )
        is True,
        failures,
    )

    check(
        "Form report change invalidates context",
        freshness.get(
            "team_form_report_change_invalidates_context"
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
        "Partial unverified output prohibited",
        freshness.get(
            "partial_unverified_output_allowed"
        )
        is False,
        failures,
    )

    check(
        "Freshness fail-closed",
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
        "Context hash validation verified",
        service_freshness.get(
            "team_context_hash_validation"
        )
        is True,
        failures,
    )

    check(
        "Standings hash validation verified",
        service_freshness.get(
            "current_standings_hash_validation"
        )
        is True,
        failures,
    )

    check(
        "Form hash validation verified",
        service_freshness.get(
            "current_team_form_hash_validation"
        )
        is True,
        failures,
    )

    check(
        "Production-history transitive invalidation verified",
        service_freshness.get(
            "production_history_transitive_invalidation"
        )
        is True,
        failures,
    )

    check(
        "Team-registry transitive invalidation verified",
        service_freshness.get(
            "team_registry_transitive_invalidation"
        )
        is True,
        failures,
    )

    check(
        "Independent reconstruction verified",
        service_freshness.get(
            "independent_reconstruction_validation"
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
    # 11. Locked model protection
    # ========================================================

    print(
        "\n11. LOCKED MODEL PROTECTION"
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

    protected_false_flags = [

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

    for flag in protected_false_flags:

        check(
            f"{flag} = false",
            model_protection.get(flag)
            is False,
            failures,
        )

    # ========================================================
    # 12. Context safety
    # ========================================================

    print(
        "\n12. CONTEXT SAFETY BOUNDARY"
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
        "Team context context-only",
        safety.get(
            "context_only"
        )
        is True,
        failures,
    )

    safety_false_flags = [

        "stage7_artifacts_modified",
        "provider_fetch_performed",
        "standings_rebuilt",
        "team_form_rebuilt",
        "model_loaded",
        "model_executed",
        "model_modified",
        "production_predictions_modified",
        "feature_schema_modified",
        "team_context_used_as_model_features",
        "final_test_accessed",
    ]

    for flag in safety_false_flags:

        check(
            f"{flag} = false",
            safety.get(flag)
            is False,
            failures,
        )

    # ========================================================
    # 13. Final decision
    # ========================================================

    print(
        "\n13. STAGE 8.4.5 FINAL DECISION"
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

            "current_standings":
                sha256_file(
                    STANDINGS_FILE
                ),

            "standings_report":
                sha256_file(
                    STANDINGS_REPORT_FILE
                ),

            "current_team_form":
                sha256_file(
                    TEAM_FORM_FILE
                ),

            "team_form_report":
                sha256_file(
                    TEAM_FORM_REPORT_FILE
                ),

            "team_context":
                actual_context_sha,

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
            TEAM_CONTEXT_REPORT_FILE
        )

        final_sub_stages = dict(
            final_report.get(
                "sub_stages",
                {}
            )
        )

        final_sub_stages[
            "8.4.1"
        ] = "PASS"

        final_sub_stages[
            "8.4.2"
        ] = "PASS"

        final_sub_stages[
            "8.4.3"
        ] = "PASS"

        final_sub_stages[
            "8.4.4"
        ] = "PASS"

        final_sub_stages[
            "8.4.5"
        ] = "PASS"

        final_report[
            "sub_stages"
        ] = final_sub_stages

        final_report[
            "status"
        ] = "PASS"

        final_report[
            "stage_8_4_complete"
        ] = True

        final_report[
            "stage_8_4_status"
        ] = "COMPLETE"

        final_report[
            "unified_team_context_layer"
        ] = "VERIFIED"

        final_report[
            "stage_8_4_5_verified_at_utc"
        ] = verified_at

        final_report[
            "final_gate"
        ] = {

            "stage":
                "8.4.5",

            "status":
                "PASS",

            "verified_at_utc":
                verified_at,

            "canonical_team_count":
                20,

            "canonical_column_count":
                38,

            "one_to_one_join_verified":
                True,

            "standings_preservation_verified":
                True,

            "overall_form_preservation_verified":
                True,

            "home_form_preservation_verified":
                True,

            "away_form_preservation_verified":
                True,

            "independent_context_validation_verified":
                True,

            "team_context_service_ready":
                True,

            "dependency_freshness_verified":
                True,

            "transitive_freshness_verified":
                True,

            "fail_closed_verified":
                True,

            "locked_model_unchanged":
                True,

            "locked_model_feature_count":
                86,

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
            TEAM_CONTEXT_REPORT_FILE,
            final_report,
        )

        # ====================================================
        # Persisted state
        # ====================================================

        persisted = load_json(
            TEAM_CONTEXT_REPORT_FILE
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
            "stage_8_4_complete persisted",
            persisted.get(
                "stage_8_4_complete"
            )
            is True,
            failures,
        )

        check(
            "Stage 8.4 COMPLETE persisted",
            persisted.get(
                "stage_8_4_status"
            )
            == "COMPLETE",
            failures,
        )

        check(
            "Unified team context layer VERIFIED persisted",
            persisted.get(
                "unified_team_context_layer"
            )
            == "VERIFIED",
            failures,
        )

        check(
            "8.4.5 PASS persisted",
            persisted.get(
                "sub_stages",
                {}
            ).get(
                "8.4.5"
            )
            == "PASS",
            failures,
        )

        # ====================================================
        # Revalidate after final report promotion
        # ====================================================

        try:

            post_validator = (
                TeamContextValidator()
                .validate()
            )

            post_validator_ok = (
                post_validator.get(
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
            TeamContextService()
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
            "TeamContextService remains READY",
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
            "STAGE 8.4.5: PASS"
        )

        print()

        print(
            "STAGE 8.4: COMPLETE"
        )

        print(
            "UNIFIED TEAM CONTEXT LAYER: VERIFIED"
        )

    else:

        print(
            "STAGE 8.4.5: FAIL"
        )

        print(
            "STAGE 8.4: INCOMPLETE"
        )

        print(
            "UNIFIED TEAM CONTEXT LAYER: NOT VERIFIED"
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
"""
FixtureIQ Stage 8.8
Final Stage 8 Verification Gate.

Sub-stages:
8.8.1 Stage 8 Foundation & Output Contract
8.8.2 Context Layer End-to-End Verification
8.8.3 REST API & Runtime Verification
8.8.4 Locked ML / Safety Boundary
8.8.5 Final Stage 8 Promotion

Creates:
data/processed/context/stage8_final_verification.json

This gate verifies the complete Stage 8 stack:

8.1 Context Contract
8.2 Live EPL Standings
8.3 Current Team Form
8.4 Unified Team Context
8.5 Fixture Context Enrichment
8.6 Context REST API
8.7 Freshness / Cache / Runtime Safety

Safety:
- no provider fetch
- no context rebuild
- no model loading
- no model execution
- no model mutation
- no prediction mutation
- no feature-schema mutation
- no final-test access
- no Stage 7 writes

The only artifact written is:
stage8_final_verification.json
"""

from __future__ import annotations

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

from backend.app import app

from backend.routes.context_api import (
    CONTEXT_API_STAGE,
    CONTEXT_API_VERSION,
    PUBLIC_ROUTES,
)

from backend.services.fixture_context_service import (
    FixtureContextService,
)

from backend.services.fixture_context_validator import (
    FixtureContextValidationError,
    FixtureContextValidator,
)

from backend.services.standings_service import (
    StandingsService,
)

from backend.services.team_context_service import (
    TeamContextService,
)

from backend.services.team_form_service import (
    TeamFormService,
)


# ============================================================
# Directories
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

MODEL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
)


# ============================================================
# Stage 7 artifacts
# ============================================================

STAGE7_8_FILE = (
    PRODUCTION_DIR
    / "stage7_8_final_verification.json"
)

STAGE7_9_FILE = (
    PRODUCTION_DIR
    / "stage7_9_final_verification.json"
)


# ============================================================
# Stage 8 artifacts
# ============================================================

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

ENRICHED_FIXTURES_FILE = (
    CONTEXT_DIR
    / "enriched_upcoming_fixtures.csv"
)

FIXTURE_CONTEXT_REPORT_FILE = (
    CONTEXT_DIR
    / "fixture_context_report.json"
)

CONTEXT_API_VERIFICATION_FILE = (
    CONTEXT_DIR
    / "context_api_verification.json"
)

CONTEXT_RUNTIME_VERIFICATION_FILE = (
    CONTEXT_DIR
    / "context_runtime_verification.json"
)

FINAL_OUTPUT_FILE = (
    CONTEXT_DIR
    / "stage8_final_verification.json"
)


# ============================================================
# Locked model
# ============================================================

SELECTED_MODEL_FILE = (
    MODEL_DIR
    / "selected"
    / "selected_model.joblib"
)

EXPECTED_FEATURE_COUNT = 86


# ============================================================
# Runtime code
# ============================================================

APP_CODE_FILE = (
    BASE_DIR
    / "backend"
    / "app.py"
)

CONTEXT_API_CODE_FILE = (
    BASE_DIR
    / "backend"
    / "routes"
    / "context_api.py"
)

STANDINGS_SERVICE_CODE_FILE = (
    BASE_DIR
    / "backend"
    / "services"
    / "standings_service.py"
)

TEAM_FORM_SERVICE_CODE_FILE = (
    BASE_DIR
    / "backend"
    / "services"
    / "team_form_service.py"
)

TEAM_CONTEXT_SERVICE_CODE_FILE = (
    BASE_DIR
    / "backend"
    / "services"
    / "team_context_service.py"
)

FIXTURE_CONTEXT_SERVICE_CODE_FILE = (
    BASE_DIR
    / "backend"
    / "services"
    / "fixture_context_service.py"
)

FIXTURE_CONTEXT_VALIDATOR_CODE_FILE = (
    BASE_DIR
    / "backend"
    / "services"
    / "fixture_context_validator.py"
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


def save_json_atomic(
    path: Path,
    payload: dict,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temporary.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=2,
        )

    temporary.replace(
        path
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


def has_no_store_headers(
    response,
) -> bool:

    cache_control = (
        response.headers
        .get(
            "Cache-Control",
            "",
        )
        .lower()
    )

    pragma = (
        response.headers
        .get(
            "Pragma",
            "",
        )
        .lower()
    )

    expires = (
        response.headers
        .get(
            "Expires",
            "",
        )
        .strip()
    )

    return (
        "no-store"
        in cache_control
        and
        "no-cache"
        in cache_control
        and
        "must-revalidate"
        in cache_control
        and
        "max-age=0"
        in cache_control
        and
        pragma
        == "no-cache"
        and
        expires
        == "0"
    )


def contains_private_key(
    value,
) -> bool:

    forbidden = {

        "sha256",
        "dependency_identity",
        "evidence_sha256",
        "runtime_code_identity",
        "failures",
        "reason",
        "model_sha256",
        "artifact_sha256",
    }

    if isinstance(
        value,
        dict,
    ):

        for key, child in value.items():

            if key in forbidden:

                return True

            if contains_private_key(
                child
            ):

                return True

    elif isinstance(
        value,
        list,
    ):

        for child in value:

            if contains_private_key(
                child
            ):

                return True

    return False


def dependency_hash_matches(
    container: dict,
    key: str,
    path: Path,
) -> bool:

    value = container.get(
        key,
        {}
    )

    if not isinstance(
        value,
        dict,
    ):

        return False

    return (
        value.get(
            "sha256"
        )
        ==
        sha256_file(
            path
        )
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.8"
    )

    print(
        "FINAL STAGE 8 VERIFICATION GATE"
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

        STAGE7_8_FILE,
        STAGE7_9_FILE,

        CONTRACT_FILE,
        CONTRACT_VERIFICATION_FILE,

        STANDINGS_FILE,
        STANDINGS_REPORT_FILE,

        TEAM_FORM_FILE,
        TEAM_FORM_REPORT_FILE,

        TEAM_CONTEXT_FILE,
        TEAM_CONTEXT_REPORT_FILE,

        ENRICHED_FIXTURES_FILE,
        FIXTURE_CONTEXT_REPORT_FILE,

        CONTEXT_API_VERIFICATION_FILE,
        CONTEXT_RUNTIME_VERIFICATION_FILE,

        SELECTED_MODEL_FILE,

        APP_CODE_FILE,
        CONTEXT_API_CODE_FILE,

        STANDINGS_SERVICE_CODE_FILE,
        TEAM_FORM_SERVICE_CODE_FILE,
        TEAM_CONTEXT_SERVICE_CODE_FILE,
        FIXTURE_CONTEXT_SERVICE_CODE_FILE,
        FIXTURE_CONTEXT_VALIDATOR_CODE_FILE,
    ]

    for path in required:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        print(
            "\nRequired artifacts are missing."
        )

        sys.exit(1)

    # ========================================================
    # Protected identities before final verification
    # ========================================================

    protected_before = {

        "stage7_8":
            sha256_file(
                STAGE7_8_FILE
            ),

        "stage7_9":
            sha256_file(
                STAGE7_9_FILE
            ),

        "selected_model":
            sha256_file(
                SELECTED_MODEL_FILE
            ),
    }

    # ========================================================
    # Load reports
    # ========================================================

    stage7_8 = load_json(
        STAGE7_8_FILE
    )

    stage7_9 = load_json(
        STAGE7_9_FILE
    )

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

    team_context_report = load_json(
        TEAM_CONTEXT_REPORT_FILE
    )

    fixture_context_report = load_json(
        FIXTURE_CONTEXT_REPORT_FILE
    )

    api_verification = load_json(
        CONTEXT_API_VERIFICATION_FILE
    )

    runtime_verification = load_json(
        CONTEXT_RUNTIME_VERIFICATION_FILE
    )

    # ========================================================
    # 2. Stage 8.8.1 - Foundation & output contract
    # ========================================================

    print(
        "\n2. STAGE 8.8.1 FOUNDATION & OUTPUT CONTRACT"
    )

    check(
        "Stage 7.8 verification PASS",
        stage7_8.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 7.9 verification PASS",
        stage7_9.get(
            "status"
        )
        == "PASS",
        failures,
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
        "Stage 8 context-only",
        contract.get(
            "context_only"
        )
        is True,
        failures,
    )

    check(
        "Stage 8.1 contract verification PASS",
        contract_verification.get(
            "status"
        )
        == "PASS",
        failures,
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
        "Stage 8 final output path locked",
        outputs.get(
            "stage8_final_verification",
            {}
        ).get(
            "path"
        )
        ==
        relative_path(
            FINAL_OUTPUT_FILE
        ),
        failures,
    )

    check(
        "Stage 7 output writes prohibited",
        output_contract.get(
            "stage7_output_write_allowed"
        )
        is False,
        failures,
    )

    # ========================================================
    # 3. Previous Stage 8 layer completion
    # ========================================================

    print(
        "\n3. STAGE 8 LAYER COMPLETION"
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
        "Live EPL Standings Layer VERIFIED",
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
        "Current Team Form Layer VERIFIED",
        form_report.get(
            "current_team_form_layer"
        )
        == "VERIFIED",
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
        "Stage 8.5 COMPLETE",
        fixture_context_report.get(
            "stage_8_5_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 8.5 status COMPLETE",
        fixture_context_report.get(
            "stage_8_5_status"
        )
        == "COMPLETE",
        failures,
    )

    check(
        "Fixture Context Enrichment Layer VERIFIED",
        fixture_context_report.get(
            "fixture_context_enrichment_layer"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Stage 8.6 COMPLETE",
        api_verification.get(
            "stage_8_6_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 8.6 status COMPLETE",
        api_verification.get(
            "stage_8_6_status"
        )
        == "COMPLETE",
        failures,
    )

    check(
        "Context REST API VERIFIED",
        api_verification.get(
            "context_rest_api"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Stage 8.7 COMPLETE",
        runtime_verification.get(
            "stage_8_7_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 8.7 status COMPLETE",
        runtime_verification.get(
            "stage_8_7_status"
        )
        == "COMPLETE",
        failures,
    )

    check(
        "Context Runtime Safety VERIFIED",
        runtime_verification.get(
            "context_runtime_safety"
        )
        == "VERIFIED",
        failures,
    )

    # ========================================================
    # 4. Sub-stage completion
    # ========================================================

    print(
        "\n4. SUB-STAGE COMPLETION"
    )

    expected_substages = {

        "8.2":
            (
                standings_report,
                [
                    "8.2.1",
                    "8.2.2",
                    "8.2.3",
                    "8.2.4",
                    "8.2.5",
                ],
            ),

        "8.3":
            (
                form_report,
                [
                    "8.3.1",
                    "8.3.2",
                    "8.3.3",
                    "8.3.4",
                    "8.3.5",
                ],
            ),

        "8.4":
            (
                team_context_report,
                [
                    "8.4.1",
                    "8.4.2",
                    "8.4.3",
                    "8.4.4",
                    "8.4.5",
                ],
            ),

        "8.5":
            (
                fixture_context_report,
                [
                    "8.5.1",
                    "8.5.2",
                    "8.5.3",
                    "8.5.4",
                    "8.5.5",
                ],
            ),

        "8.6":
            (
                api_verification,
                [
                    "8.6.1",
                    "8.6.2",
                    "8.6.3",
                    "8.6.4",
                    "8.6.5",
                ],
            ),

        "8.7":
            (
                runtime_verification,
                [
                    "8.7.1",
                    "8.7.2",
                    "8.7.3",
                    "8.7.4",
                    "8.7.5",
                ],
            ),
    }

    for stage_name, (
        report,
        substages,
    ) in expected_substages.items():

        report_substages = (
            report.get(
                "sub_stages",
                {}
            )
        )

        check(
            f"All {stage_name} substages PASS",
            all(
                report_substages.get(
                    substage
                )
                == "PASS"

                for substage in substages
            ),
            failures,
        )

    # ========================================================
    # 5. Stage 8.8.2 - Context service stack
    # ========================================================

    print(
        "\n5. STAGE 8.8.2 CONTEXT SERVICE STACK"
    )

    standings_service = (
        StandingsService()
    )

    form_service = (
        TeamFormService()
    )

    team_context_service = (
        TeamContextService()
    )

    fixture_context_service = (
        FixtureContextService()
    )

    service_objects = {

        "standings":
            standings_service,

        "team_form":
            form_service,

        "team_context":
            team_context_service,

        "fixture_context":
            fixture_context_service,
    }

    service_statuses = {}

    for name, service in service_objects.items():

        status = (
            service.get_status()
        )

        service_statuses[
            name
        ] = status

        if (
            status.get(
                "status"
            )
            != "READY"
        ):

            print(
                f"{name} reason:",
                status.get(
                    "reason"
                ),
            )

        check(
            f"{name} service READY",
            status.get(
                "status"
            )
            == "READY",
            failures,
        )

    # ========================================================
    # 6. Canonical context reads
    # ========================================================

    print(
        "\n6. CANONICAL CONTEXT READS"
    )

    try:

        standings_rows = (
            standings_service
            .get_standings()
        )

        standings_read_ok = True

    except Exception as exc:

        print(
            "Standings read error:",
            exc,
        )

        standings_rows = []
        standings_read_ok = False

    check(
        "Standings read succeeds",
        standings_read_ok,
        failures,
    )

    check(
        "Standings team count = 20",
        len(
            standings_rows
        )
        == 20,
        failures,
    )

    check(
        "Standings schema = 11 fields",
        (
            len(
                standings_rows
            )
            == 20
            and
            all(
                len(row)
                == 11

                for row in standings_rows
            )
        ),
        failures,
    )

    try:

        form_rows = (
            form_service
            .get_all_team_form()
        )

        form_read_ok = True

    except Exception as exc:

        print(
            "Form read error:",
            exc,
        )

        form_rows = []
        form_read_ok = False

    check(
        "Team form read succeeds",
        form_read_ok,
        failures,
    )

    check(
        "Team form count = 20",
        len(
            form_rows
        )
        == 20,
        failures,
    )

    check(
        "Team form schema = 29 fields",
        (
            len(
                form_rows
            )
            == 20
            and
            all(
                len(row)
                == 29

                for row in form_rows
            )
        ),
        failures,
    )

    try:

        team_context_rows = (
            team_context_service
            .get_all_team_context()
        )

        team_context_read_ok = True

    except Exception as exc:

        print(
            "Team context read error:",
            exc,
        )

        team_context_rows = []
        team_context_read_ok = False

    check(
        "Team context read succeeds",
        team_context_read_ok,
        failures,
    )

    check(
        "Team context count = 20",
        len(
            team_context_rows
        )
        == 20,
        failures,
    )

    check(
        "Team context schema = 38 fields",
        (
            len(
                team_context_rows
            )
            == 20
            and
            all(
                len(row)
                == 38

                for row in team_context_rows
            )
        ),
        failures,
    )

    try:

        fixture_rows = (
            fixture_context_service
            .get_all_fixture_context()
        )

        fixture_read_ok = True

    except Exception as exc:

        print(
            "Fixture context read error:",
            exc,
        )

        fixture_rows = []
        fixture_read_ok = False

    check(
        "Fixture context read succeeds",
        fixture_read_ok,
        failures,
    )

    check(
        "Upcoming fixture context non-empty",
        len(
            fixture_rows
        )
        > 0,
        failures,
    )

    check(
        "Fixture count matches Stage 8.5 report",
        len(
            fixture_rows
        )
        ==
        fixture_context_report.get(
            "fixture_count"
        ),
        failures,
    )

    fixture_status = service_statuses.get(
        "fixture_context",
        {}
    )

    check(
        "Fixture context appends 72 fields",
        fixture_status.get(
            "context_column_count"
        )
        == 72,
        failures,
    )

    # ========================================================
    # 7. Independent fixture reconstruction
    # ========================================================

    print(
        "\n7. INDEPENDENT FIXTURE VALIDATION"
    )

    try:

        fixture_validation = (
            FixtureContextValidator()
            .validate()
        )

        independent_fixture_ok = (
            fixture_validation.get(
                "status"
            )
            == "PASS"
        )

    except FixtureContextValidationError as exc:

        print(
            "Fixture validator reason:",
            exc,
        )

        fixture_validation = {}
        independent_fixture_ok = False

    except Exception as exc:

        print(
            "Unexpected fixture validator error:",
            exc,
        )

        fixture_validation = {}
        independent_fixture_ok = False

    check(
        "Independent fixture validator PASS",
        independent_fixture_ok,
        failures,
    )

    if independent_fixture_ok:

        validation_true_keys = [

            "fixture_ids_unique",
            "source_fields_preserved",
            "strict_home_identity_verified",
            "strict_away_identity_verified",
            "home_context_preservation_verified",
            "away_context_preservation_verified",
            "exact_independent_reconstruction_verified",
            "all_fixtures_future",
            "form_cutoff_verified",
            "team_context_temporal_boundary_verified",
            "fixture_snapshot_provenance_verified",
            "shared_context_snapshot_verified",
            "dependency_identity_verified",
            "freshness_contract_verified",
            "safety_verified",
        ]

        for key in validation_true_keys:

            check(
                f"{key} verified",
                fixture_validation.get(
                    key
                )
                is True,
                failures,
            )

        check(
            "Future fixture state propagation disabled",
            fixture_validation.get(
                "future_fixture_state_propagation"
            )
            is False,
            failures,
        )

    # ========================================================
    # 8. Verified dependency chain
    # ========================================================

    print(
        "\n8. VERIFIED DEPENDENCY CHAIN"
    )

    api_dependencies = (
        api_verification.get(
            "dependency_identity",
            {}
        )
    )

    check(
        "8.6 -> contract hash current",
        dependency_hash_matches(
            api_dependencies,
            "stage8_context_contract",
            CONTRACT_FILE,
        ),
        failures,
    )

    check(
        "8.6 -> contract verification hash current",
        dependency_hash_matches(
            api_dependencies,
            "stage8_context_contract_verification",
            CONTRACT_VERIFICATION_FILE,
        ),
        failures,
    )

    check(
        "8.6 -> standings report hash current",
        dependency_hash_matches(
            api_dependencies,
            "standings_report",
            STANDINGS_REPORT_FILE,
        ),
        failures,
    )

    check(
        "8.6 -> team form report hash current",
        dependency_hash_matches(
            api_dependencies,
            "team_form_report",
            TEAM_FORM_REPORT_FILE,
        ),
        failures,
    )

    check(
        "8.6 -> team context report hash current",
        dependency_hash_matches(
            api_dependencies,
            "team_context_report",
            TEAM_CONTEXT_REPORT_FILE,
        ),
        failures,
    )

    check(
        "8.6 -> fixture context report hash current",
        dependency_hash_matches(
            api_dependencies,
            "fixture_context_report",
            FIXTURE_CONTEXT_REPORT_FILE,
        ),
        failures,
    )

    runtime_dependencies = (
        runtime_verification.get(
            "dependency_identity",
            {}
        )
    )

    check(
        "8.7 -> contract hash current",
        dependency_hash_matches(
            runtime_dependencies,
            "stage8_context_contract",
            CONTRACT_FILE,
        ),
        failures,
    )

    check(
        "8.7 -> 8.6 verification hash current",
        dependency_hash_matches(
            runtime_dependencies,
            "context_api_verification",
            CONTEXT_API_VERIFICATION_FILE,
        ),
        failures,
    )

    check(
        "8.7 -> standings report hash current",
        dependency_hash_matches(
            runtime_dependencies,
            "standings_report",
            STANDINGS_REPORT_FILE,
        ),
        failures,
    )

    check(
        "8.7 -> team form report hash current",
        dependency_hash_matches(
            runtime_dependencies,
            "team_form_report",
            TEAM_FORM_REPORT_FILE,
        ),
        failures,
    )

    check(
        "8.7 -> team context report hash current",
        dependency_hash_matches(
            runtime_dependencies,
            "team_context_report",
            TEAM_CONTEXT_REPORT_FILE,
        ),
        failures,
    )

    check(
        "8.7 -> fixture context report hash current",
        dependency_hash_matches(
            runtime_dependencies,
            "fixture_context_report",
            FIXTURE_CONTEXT_REPORT_FILE,
        ),
        failures,
    )

    # ========================================================
    # 9. Stage 8.8.3 - REST API contract
    # ========================================================

    print(
        "\n9. STAGE 8.8.3 REST API CONTRACT"
    )

    registered_context_routes = {}

    for rule in app.url_map.iter_rules():

        rule_text = str(
            rule
        )

        if rule_text.startswith(
            "/api/v1/context"
        ):

            registered_context_routes[
                rule_text
            ] = sorted(
                method

                for method in rule.methods

                if method not in {
                    "HEAD",
                    "OPTIONS",
                }
            )

    expected_routes = {

        route:
            [
                "GET"
            ]

        for route in PUBLIC_ROUTES
    }

    check(
        "Context API version = v1",
        CONTEXT_API_VERSION
        == "v1",
        failures,
    )

    check(
        "Context API stage = 8.6",
        CONTEXT_API_STAGE
        == "8.6",
        failures,
    )

    check(
        "Exactly 10 context routes",
        len(
            registered_context_routes
        )
        == 10,
        failures,
    )

    check(
        "Context route contract exact",
        registered_context_routes
        ==
        expected_routes,
        failures,
    )

    # ========================================================
    # 10. Context API live baseline
    # ========================================================

    print(
        "\n10. CONTEXT API LIVE BASELINE"
    )

    client = app.test_client()

    baseline_paths = [

        "/api/v1/context/status",
        "/api/v1/context/standings",
        "/api/v1/context/form",
        "/api/v1/context/teams",
        "/api/v1/context/fixtures",
    ]

    for endpoint in baseline_paths:

        response = (
            client.get(
                endpoint
            )
        )

        check(
            f"GET {endpoint} -> 200",
            response.status_code
            == 200,
            failures,
        )

        check(
            f"{endpoint} no-store",
            has_no_store_headers(
                response
            ),
            failures,
        )

        payload = (
            response.get_json()
        )

        check(
            f"{endpoint} public-safe",
            not contains_private_key(
                payload
            ),
            failures,
        )

    status_response = (
        client.get(
            "/api/v1/context/status"
        )
    )

    status_payload = (
        status_response.get_json()
    )

    check(
        "Overall context API READY",
        status_payload.get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "Context API read-only",
        status_payload.get(
            "read_only"
        )
        is True,
        failures,
    )

    check(
        "All four context layers exposed",
        set(
            status_payload.get(
                "layers",
                {}
            ).keys()
        )
        ==
        {
            "standings",
            "team_form",
            "team_context",
            "fixture_context",
        },
        failures,
    )

    check(
        "Every exposed context layer READY",
        all(
            layer.get(
                "status"
            )
            == "READY"

            for layer in (
                status_payload.get(
                    "layers",
                    {}
                ).values()
            )
        ),
        failures,
    )

    # ========================================================
    # 11. Read-only HTTP boundary
    # ========================================================

    print(
        "\n11. READ-ONLY HTTP BOUNDARY"
    )

    # Flask-generated 405 responses occur before the blueprint
    # route handler executes. The important contract here is
    # that all Stage 8 context endpoints remain GET-only.
    #
    # Cache safety is independently verified for:
    # - normal READY responses
    # - custom context 404 responses
    # - stale context 503 responses in Stage 8.7

    for endpoint in baseline_paths:

        response = (
            client.post(
                endpoint,
                json={
                    "fixtureiq":
                        "stage8-final"
                },
            )
        )

        check(
            f"POST {endpoint} -> 405",
            response.status_code
            == 405,
            failures,
        )

    unknown_response = (
        client.get(
            (
                "/api/v1/context/fixtures/"
                "fixtureiq-does-not-exist"
            )
        )
    )

    check(
        "Unknown context resource -> 404",
        unknown_response.status_code
        == 404,
        failures,
    )

    check(
        "404 remains no-store",
        has_no_store_headers(
            unknown_response
        ),
        failures,
    )

    # ========================================================
    # 12. Stage 8.7 runtime evidence
    # ========================================================

    print(
        "\n12. STAGE 8.7 RUNTIME EVIDENCE"
    )

    runtime_contract = (
        runtime_verification.get(
            "runtime_contract",
            {}
        )
    )

    check(
        "Request-time validation required",
        runtime_contract.get(
            "service_validation_timing"
        )
        == "REQUEST_TIME",
        failures,
    )

    check(
        "Runtime stale context -> HTTP 503",
        runtime_contract.get(
            "stale_context_http_status"
        )
        == 503,
        failures,
    )

    check(
        "Dependency freshness required",
        runtime_contract.get(
            "dependency_freshness_required"
        )
        is True,
        failures,
    )

    check(
        "Transitive freshness required",
        runtime_contract.get(
            "transitive_dependency_freshness_required"
        )
        is True,
        failures,
    )

    check(
        "Temporal freshness required",
        runtime_contract.get(
            "temporal_freshness_required"
        )
        is True,
        failures,
    )

    check(
        "Runtime stale fallback prohibited",
        runtime_contract.get(
            "stale_fallback_allowed"
        )
        is False,
        failures,
    )

    check(
        "Runtime fail-closed",
        runtime_contract.get(
            "fail_closed"
        )
        is True,
        failures,
    )

    cache_evidence = (
        runtime_verification.get(
            "cache_and_request_isolation",
            {}
        )
    )

    check(
        "Cache / request isolation VERIFIED",
        cache_evidence.get(
            "status"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "HTTP cache storage prohibited",
        cache_evidence.get(
            "http_cache_storage_allowed"
        )
        is False,
        failures,
    )

    check(
        "Stale response reuse prohibited",
        cache_evidence.get(
            "stale_response_reuse_allowed"
        )
        is False,
        failures,
    )

    check(
        "Runtime state rechecked per request",
        cache_evidence.get(
            "runtime_state_rechecked_per_request"
        )
        is True,
        failures,
    )

    recovery_evidence = (
        runtime_verification.get(
            "runtime_recovery",
            {}
        )
    )

    check(
        "Runtime recovery VERIFIED",
        recovery_evidence.get(
            "status"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Runtime recovery initial HTTP 503",
        recovery_evidence.get(
            "initial_http_status"
        )
        == 503,
        failures,
    )

    check(
        "Runtime recovery restored HTTP 200",
        recovery_evidence.get(
            "restored_http_status"
        )
        == 200,
        failures,
    )

    check(
        "Runtime recovery requires no Flask restart",
        recovery_evidence.get(
            "flask_restart_required"
        )
        is False,
        failures,
    )

    runtime_final_gate = (
        runtime_verification.get(
            "final_gate",
            {}
        )
    )

    check(
        "Stage 8.7 final gate PASS",
        runtime_final_gate.get(
            "status"
        )
        == "PASS",
        failures,
    )

    # ========================================================
    # 13. Runtime code identity
    # ========================================================

    print(
        "\n13. RUNTIME CODE IDENTITY"
    )

    runtime_code_identity = (
        runtime_verification.get(
            "runtime_code_identity",
            {}
        )
    )

    code_identity_checks = [

        (
            "context_api",
            CONTEXT_API_CODE_FILE,
        ),

        (
            "flask_app",
            APP_CODE_FILE,
        ),

        (
            "fixture_context_service",
            FIXTURE_CONTEXT_SERVICE_CODE_FILE,
        ),

        (
            "team_context_service",
            TEAM_CONTEXT_SERVICE_CODE_FILE,
        ),
    ]

    for name, path in code_identity_checks:

        check(
            f"{name} runtime code unchanged since 8.7",
            runtime_code_identity.get(
                name,
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
    # 14. Existing production API preservation
    # ========================================================

    print(
        "\n14. STAGE 7 PRODUCTION API PRESERVATION"
    )

    health_response = (
        client.get(
            "/api/health"
        )
    )

    health_payload = (
        health_response.get_json()
    )

    check(
        "/api/health -> 200",
        health_response.status_code
        == 200,
        failures,
    )

    check(
        "Health project = FixtureIQ",
        health_payload.get(
            "project"
        )
        == "FixtureIQ",
        failures,
    )

    production_routes = {

        str(
            rule
        )

        for rule in app.url_map.iter_rules()

        if (
            str(
                rule
            ).startswith(
                "/api/v1/predictions"
            )
            or
            str(
                rule
            ).startswith(
                "/api/v1/production"
            )
        )
    }

    check(
        "Stage 7 production routes preserved",
        len(
            production_routes
        )
        >= 7,
        failures,
    )

    # ========================================================
    # 15. Stage 8.8.4 - Locked ML boundary
    # ========================================================

    print(
        "\n15. STAGE 8.8.4 LOCKED ML BOUNDARY"
    )

    locked_model = (
        contract.get(
            "locked_model",
            {}
        )
    )

    actual_model_sha = (
        sha256_file(
            SELECTED_MODEL_FILE
        )
    )

    contract_model_sha = (
        str(
            locked_model.get(
                "sha256",
                "",
            )
        )
        .strip()
        .lower()
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
        == EXPECTED_FEATURE_COUNT,
        failures,
    )

    check(
        "Locked model SHA is valid SHA256",
        (
            len(
                contract_model_sha
            )
            == 64
            and
            all(
                char
                in
                "0123456789abcdef"

                for char in contract_model_sha
            )
        ),
        failures,
    )

    check(
        "Contract model SHA matches selected model",
        contract_model_sha
        ==
        actual_model_sha.lower(),
        failures,
    )

    check(
        "Selected model identity locked by verified Stage 8 contract",
        (
            contract_verification.get(
                "status"
            )
            == "PASS"
            and
            contract.get(
                "contract_status"
            )
            == "LOCKED_CONTEXT_CONTRACT"
            and
            contract_model_sha
            ==
            actual_model_sha.lower()
        ),
        failures,
    )

    model_protection = (
        contract.get(
            "model_protection",
            {}
        )
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
            model_protection.get(
                flag
            )
            is False,
            failures,
        )

    # ========================================================
    # 16. Stage 8 safety boundaries
    # ========================================================

    print(
        "\n16. STAGE 8 SAFETY BOUNDARIES"
    )

    fixture_safety = (
        fixture_context_report.get(
            "safety",
            {}
        )
    )

    check(
        "Fixture context remains context-only",
        fixture_safety.get(
            "context_only"
        )
        is True,
        failures,
    )

    fixture_false_flags = [

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

    for flag in fixture_false_flags:

        check(
            f"Fixture safety {flag} = false",
            fixture_safety.get(
                flag
            )
            is False,
            failures,
        )

    api_safety = (
        api_verification.get(
            "safety",
            {}
        )
    )

    check(
        "Context API read-only",
        api_safety.get(
            "read_only"
        )
        is True,
        failures,
    )

    check(
        "Context API context-only",
        api_safety.get(
            "context_only"
        )
        is True,
        failures,
    )

    api_false_flags = [

        "provider_fetch_performed",
        "context_rebuilt",
        "model_loaded",
        "model_executed",
        "model_modified",
        "production_predictions_modified",
        "feature_schema_modified",
        "context_used_as_model_features",
        "stage7_artifacts_modified",
        "final_test_accessed",
        "private_dependency_hashes_exposed",
    ]

    for flag in api_false_flags:

        check(
            f"API safety {flag} = false",
            api_safety.get(
                flag
            )
            is False,
            failures,
        )

    runtime_safety = (
        runtime_verification.get(
            "safety",
            {}
        )
    )

    check(
        "Runtime remains read-only",
        runtime_safety.get(
            "read_only"
        )
        is True,
        failures,
    )

    check(
        "Runtime remains context-only",
        runtime_safety.get(
            "context_only"
        )
        is True,
        failures,
    )

    runtime_false_flags = [

        "provider_fetch_performed",
        "context_rebuilt",
        "stage7_artifacts_modified",
        "model_loaded",
        "model_executed",
        "model_modified",
        "production_predictions_modified",
        "feature_schema_modified",
        "context_used_as_model_features",
        "final_test_accessed",
        "stale_data_served",
        "http_cache_storage_allowed",
    ]

    for flag in runtime_false_flags:

        check(
            f"Runtime safety {flag} = false",
            runtime_safety.get(
                flag
            )
            is False,
            failures,
        )

    # ========================================================
    # 17. Protected artifact identity
    # ========================================================

    print(
        "\n17. PROTECTED ARTIFACT IDENTITY"
    )

    check(
        "Stage 7.8 artifact unchanged during final gate",
        sha256_file(
            STAGE7_8_FILE
        )
        ==
        protected_before[
            "stage7_8"
        ],
        failures,
    )

    check(
        "Stage 7.9 artifact unchanged during final gate",
        sha256_file(
            STAGE7_9_FILE
        )
        ==
        protected_before[
            "stage7_9"
        ],
        failures,
    )

    check(
        "Selected model unchanged during final gate",
        sha256_file(
            SELECTED_MODEL_FILE
        )
        ==
        protected_before[
            "selected_model"
        ],
        failures,
    )

    # ========================================================
    # 18. Stage 8.8.5 - Final decision
    # ========================================================

    print(
        "\n18. STAGE 8.8.5 FINAL DECISION"
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

        dependency_identity = {

            "stage7_8_final_verification": {

                "path":
                    relative_path(
                        STAGE7_8_FILE
                    ),

                "sha256":
                    sha256_file(
                        STAGE7_8_FILE
                    ),
            },

            "stage7_9_final_verification": {

                "path":
                    relative_path(
                        STAGE7_9_FILE
                    ),

                "sha256":
                    sha256_file(
                        STAGE7_9_FILE
                    ),
            },

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

            "standings_report": {

                "path":
                    relative_path(
                        STANDINGS_REPORT_FILE
                    ),

                "sha256":
                    sha256_file(
                        STANDINGS_REPORT_FILE
                    ),
            },

            "team_form_report": {

                "path":
                    relative_path(
                        TEAM_FORM_REPORT_FILE
                    ),

                "sha256":
                    sha256_file(
                        TEAM_FORM_REPORT_FILE
                    ),
            },

            "team_context_report": {

                "path":
                    relative_path(
                        TEAM_CONTEXT_REPORT_FILE
                    ),

                "sha256":
                    sha256_file(
                        TEAM_CONTEXT_REPORT_FILE
                    ),
            },

            "fixture_context_report": {

                "path":
                    relative_path(
                        FIXTURE_CONTEXT_REPORT_FILE
                    ),

                "sha256":
                    sha256_file(
                        FIXTURE_CONTEXT_REPORT_FILE
                    ),
            },

            "context_api_verification": {

                "path":
                    relative_path(
                        CONTEXT_API_VERIFICATION_FILE
                    ),

                "sha256":
                    sha256_file(
                        CONTEXT_API_VERIFICATION_FILE
                    ),
            },

            "context_runtime_verification": {

                "path":
                    relative_path(
                        CONTEXT_RUNTIME_VERIFICATION_FILE
                    ),

                "sha256":
                    sha256_file(
                        CONTEXT_RUNTIME_VERIFICATION_FILE
                    ),
            },

            "selected_model": {

                "path":
                    relative_path(
                        SELECTED_MODEL_FILE
                    ),

                "sha256":
                    actual_model_sha,
            },
        }

        code_identity = {

            "flask_app": {

                "path":
                    relative_path(
                        APP_CODE_FILE
                    ),

                "sha256":
                    sha256_file(
                        APP_CODE_FILE
                    ),
            },

            "context_api": {

                "path":
                    relative_path(
                        CONTEXT_API_CODE_FILE
                    ),

                "sha256":
                    sha256_file(
                        CONTEXT_API_CODE_FILE
                    ),
            },

            "standings_service": {

                "path":
                    relative_path(
                        STANDINGS_SERVICE_CODE_FILE
                    ),

                "sha256":
                    sha256_file(
                        STANDINGS_SERVICE_CODE_FILE
                    ),
            },

            "team_form_service": {

                "path":
                    relative_path(
                        TEAM_FORM_SERVICE_CODE_FILE
                    ),

                "sha256":
                    sha256_file(
                        TEAM_FORM_SERVICE_CODE_FILE
                    ),
            },

            "team_context_service": {

                "path":
                    relative_path(
                        TEAM_CONTEXT_SERVICE_CODE_FILE
                    ),

                "sha256":
                    sha256_file(
                        TEAM_CONTEXT_SERVICE_CODE_FILE
                    ),
            },

            "fixture_context_service": {

                "path":
                    relative_path(
                        FIXTURE_CONTEXT_SERVICE_CODE_FILE
                    ),

                "sha256":
                    sha256_file(
                        FIXTURE_CONTEXT_SERVICE_CODE_FILE
                    ),
            },

            "fixture_context_validator": {

                "path":
                    relative_path(
                        FIXTURE_CONTEXT_VALIDATOR_CODE_FILE
                    ),

                "sha256":
                    sha256_file(
                        FIXTURE_CONTEXT_VALIDATOR_CODE_FILE
                    ),
            },
        }

        final_report = {

            "stage":
                "8.8",

            "status":
                "PASS",

            "stage_8_complete":
                True,

            "stage_8_status":
                "COMPLETE",

            "stage8_context_layer":
                "VERIFIED",

            "verified_at_utc":
                verified_at,

            "sub_stages": {

                "8.8.1":
                    "PASS",

                "8.8.2":
                    "PASS",

                "8.8.3":
                    "PASS",

                "8.8.4":
                    "PASS",

                "8.8.5":
                    "PASS",
            },

            "stage_summary": {

                "8.1_context_contract":
                    "COMPLETE",

                "8.2_live_epl_standings":
                    "COMPLETE",

                "8.3_current_team_form":
                    "COMPLETE",

                "8.4_unified_team_context":
                    "COMPLETE",

                "8.5_fixture_context_enrichment":
                    "COMPLETE",

                "8.6_context_rest_api":
                    "COMPLETE",

                "8.7_context_runtime_safety":
                    "COMPLETE",

                "8.8_final_verification_gate":
                    "COMPLETE",
            },

            "context_stack": {

                "standings_service":
                    "READY",

                "team_form_service":
                    "READY",

                "team_context_service":
                    "READY",

                "fixture_context_service":
                    "READY",

                "context_api":
                    "READY",

                "team_count":
                    20,

                "fixture_count":
                    len(
                        fixture_rows
                    ),

                "standings_columns":
                    11,

                "team_form_columns":
                    29,

                "team_context_columns":
                    38,

                "fixture_context_columns_appended":
                    72,
            },

            "api": {

                "version":
                    CONTEXT_API_VERSION,

                "route_count":
                    10,

                "read_only":
                    True,

                "baseline_http_status":
                    200,

                "stale_http_status":
                    503,

                "unknown_resource_status":
                    404,

                "write_method_status":
                    405,

                "no_store":
                    True,

                "request_time_revalidation":
                    True,

                "runtime_recovery_without_restart":
                    True,
            },

            "locked_model": {

                "model_id":
                    "random_forest",

                "feature_count":
                    EXPECTED_FEATURE_COUNT,

                "sha256":
                    actual_model_sha,

                "contract_sha256":
                    contract_model_sha,

                "contract_identity_match":
                    True,

                "unchanged":
                    True,

                "used_by_stage8_context":
                    False,
            },

            "dependency_identity":
                dependency_identity,

            "code_identity":
                code_identity,

            "safety": {

                "context_only":
                    True,

                "read_only":
                    True,

                "fail_closed":
                    True,

                "provider_fetch_performed":
                    False,

                "context_rebuilt_by_final_gate":
                    False,

                "stage7_artifacts_modified":
                    False,

                "model_loaded":
                    False,

                "model_executed":
                    False,

                "model_modified":
                    False,

                "model_retrained":
                    False,

                "model_reselected":
                    False,

                "hyperparameter_tuned":
                    False,

                "production_predictions_modified":
                    False,

                "feature_schema_modified":
                    False,

                "context_used_as_model_features":
                    False,

                "standings_used_as_model_features":
                    False,

                "form_used_as_model_features":
                    False,

                "fixture_context_used_as_model_features":
                    False,

                "future_results_used":
                    False,

                "future_fixture_state_propagation":
                    False,

                "stale_data_served":
                    False,

                "http_cache_storage_allowed":
                    False,

                "final_test_accessed":
                    False,
            },

            "final_gate": {

                "status":
                    "PASS",

                "stage8_contract_locked":
                    True,

                "all_stage8_layers_complete":
                    True,

                "all_context_services_ready":
                    True,

                "independent_fixture_validation_pass":
                    True,

                "dependency_chain_verified":
                    True,

                "context_api_verified":
                    True,

                "runtime_safety_verified":
                    True,

                "no_stale_cache_verified":
                    True,

                "runtime_recovery_verified":
                    True,

                "locked_model_identity_verified":
                    True,

                "locked_model_unchanged":
                    True,

                "locked_feature_count":
                    EXPECTED_FEATURE_COUNT,

                "stage7_production_api_preserved":
                    True,

                "stage7_write_protection_verified":
                    True,

                "context_only_boundary_verified":
                    True,

                "final_test_untouched":
                    True,

                "fixtureiq_stage8_ready":
                    True,
            },

            "failures":
                [],
        }

        save_json_atomic(
            FINAL_OUTPUT_FILE,
            final_report,
        )

        print(
            FINAL_OUTPUT_FILE
        )

        # ====================================================
        # Persisted final artifact checks
        # ====================================================

        persisted = load_json(
            FINAL_OUTPUT_FILE
        )

        check(
            "Stage 8 final status PASS persisted",
            persisted.get(
                "status"
            )
            == "PASS",
            failures,
        )

        check(
            "stage_8_complete persisted",
            persisted.get(
                "stage_8_complete"
            )
            is True,
            failures,
        )

        check(
            "Stage 8 COMPLETE persisted",
            persisted.get(
                "stage_8_status"
            )
            == "COMPLETE",
            failures,
        )

        check(
            "Stage 8 Context Layer VERIFIED persisted",
            persisted.get(
                "stage8_context_layer"
            )
            == "VERIFIED",
            failures,
        )

        for substage in (
            "8.8.1",
            "8.8.2",
            "8.8.3",
            "8.8.4",
            "8.8.5",
        ):

            check(
                f"{substage} PASS persisted",
                persisted.get(
                    "sub_stages",
                    {}
                ).get(
                    substage
                )
                == "PASS",
                failures,
            )

        check(
            "Final gate PASS persisted",
            persisted.get(
                "final_gate",
                {}
            ).get(
                "status"
            )
            == "PASS",
            failures,
        )

        check(
            "FixtureIQ Stage 8 ready persisted",
            persisted.get(
                "final_gate",
                {}
            ).get(
                "fixtureiq_stage8_ready"
            )
            is True,
            failures,
        )

        # ====================================================
        # Post-write protection checks
        # ====================================================

        check(
            "Stage 7.8 remains unchanged after final write",
            sha256_file(
                STAGE7_8_FILE
            )
            ==
            protected_before[
                "stage7_8"
            ],
            failures,
        )

        check(
            "Stage 7.9 remains unchanged after final write",
            sha256_file(
                STAGE7_9_FILE
            )
            ==
            protected_before[
                "stage7_9"
            ],
            failures,
        )

        check(
            "Locked model remains unchanged after final write",
            sha256_file(
                SELECTED_MODEL_FILE
            )
            ==
            protected_before[
                "selected_model"
            ],
            failures,
        )

        # ====================================================
        # Final live smoke test
        # ====================================================

        final_http_response = (
            client.get(
                "/api/v1/context/status"
            )
        )

        check(
            "Context API remains HTTP 200 after Stage 8 promotion",
            final_http_response.status_code
            == 200,
            failures,
        )

        check(
            "Context API remains READY after Stage 8 promotion",
            final_http_response
            .get_json()
            .get(
                "status"
            )
            == "READY",
            failures,
        )

        check(
            "No-store remains active after Stage 8 promotion",
            has_no_store_headers(
                final_http_response
            ),
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
            "STAGE 8.8.1: PASS"
        )

        print(
            "STAGE 8.8.2: PASS"
        )

        print(
            "STAGE 8.8.3: PASS"
        )

        print(
            "STAGE 8.8.4: PASS"
        )

        print(
            "STAGE 8.8.5: PASS"
        )

        print()

        print(
            "STAGE 8.8: COMPLETE"
        )

        print(
            "STAGE 8: COMPLETE"
        )

        print(
            "FIXTUREIQ CONTEXT LAYER: VERIFIED"
        )

    else:

        print(
            "STAGE 8.8: FAIL"
        )

        print(
            "STAGE 8: INCOMPLETE"
        )

        print(
            "FIXTUREIQ CONTEXT LAYER: NOT VERIFIED"
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
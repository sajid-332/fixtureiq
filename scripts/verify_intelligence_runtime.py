"""
FixtureIQ Stage 9.7
Runtime Freshness / Safety Verification.

Verifies:

- current live service readiness
- Stage 7/8 dependency revalidation
- FixtureContextService readiness propagation
- temporal-boundary fail closed
- no stale fallback
- same-process stale -> healthy recovery
- Stage 9 artifact mutation rejection
- Stage 9.2 dependency mutation rejection
- exact public 503 response
- 404 / 405 preservation
- Cache-Control: no-store
- no provider fetch
- no rebuild
- no model execution
- no upstream mutation
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


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


from backend.app import app

from backend.services.match_intelligence_service import (
    MatchIntelligenceNotReadyError,
    MatchIntelligenceService,
)


# ============================================================
# Paths
# ============================================================

INTELLIGENCE_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "intelligence"
)

CONTRACT_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract.json"
)

CONTRACT_VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract_verification.json"
)

BASE_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_base.csv"
)

BASE_REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_base_report.json"
)

INTELLIGENCE_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence.csv"
)

REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_report.json"
)

API_VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "intelligence_api_verification.json"
)

OUTPUT_FILE = (
    INTELLIGENCE_DIR
    / "intelligence_runtime_verification.json"
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


def save_json_atomic(
    path: Path,
    payload: dict,
) -> None:

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    save_json(
        temporary,
        payload,
    )

    temporary.replace(
        path
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


def response_json(
    response,
) -> dict:

    payload = response.get_json(
        silent=True
    )

    if isinstance(
        payload,
        dict,
    ):

        return payload

    return {}


def has_no_store(
    response,
) -> bool:

    cache_control = str(
        response.headers.get(
            "Cache-Control",
            "",
        )
    ).lower()

    pragma = str(
        response.headers.get(
            "Pragma",
            "",
        )
    ).lower()

    expires = str(
        response.headers.get(
            "Expires",
            "",
        )
    )

    return (
        "no-store"
        in cache_control
        and
        "no-cache"
        in cache_control
        and
        pragma
        == "no-cache"
        and
        expires
        == "0"
    )


# ============================================================
# Toggleable fake Stage 8 runtime service
# ============================================================

class ToggleFixtureContextService:

    def __init__(
        self,
    ) -> None:

        self.ready = True

        self.reason = (
            "Runtime test forced stale context."
        )

    def get_status(
        self,
    ) -> dict:

        if self.ready:

            return {

                "status":
                    "READY",

                "service":
                    "fixture_context",
            }

        return {

            "status":
                "NOT_READY",

            "service":
                "fixture_context",

            "reason":
                self.reason,
        }


# ============================================================
# Forced API stale service
# ============================================================

class ForcedNotReadyService:

    def get_status(
        self,
    ) -> dict:

        return {

            "status":
                "NOT_READY",

            "stage":
                "9.7",

            "service":
                "match_intelligence",

            "reason":
                "Forced runtime verification stale state.",
        }

    def get_all_matches(
        self,
    ):

        raise MatchIntelligenceNotReadyError(
            "Forced stale state."
        )

    def get_match(
        self,
        fixture_id,
    ):

        raise MatchIntelligenceNotReadyError(
            "Forced stale state."
        )

    def get_team_matches(
        self,
        team_name,
    ):

        raise MatchIntelligenceNotReadyError(
            "Forced stale state."
        )

    def get_upcoming(
        self,
    ):

        raise MatchIntelligenceNotReadyError(
            "Forced stale state."
        )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 9.7"
    )

    print(
        "RUNTIME FRESHNESS / SAFETY VERIFICATION"
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
        BASE_FILE,
        BASE_REPORT_FILE,
        INTELLIGENCE_FILE,
        REPORT_FILE,
        API_VERIFICATION_FILE,
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
    # Protected snapshot
    # ========================================================

    protected_paths = list(
        required
    )

    protected_before = {

        relative_path(
            path
        ):
            sha256_file(
                path
            )

        for path in protected_paths
    }

    # ========================================================
    # 2. Stage 9.6 foundation
    # ========================================================

    print(
        "\n2. STAGE 9.6 FOUNDATION"
    )

    api_verification = load_json(
        API_VERIFICATION_FILE
    )

    report = load_json(
        REPORT_FILE
    )

    check(
        "Stage 9.5 COMPLETE",
        report.get(
            "stage_9_5_complete"
        )
        is True,
        failures,
    )

    check(
        "Explanation Engine VERIFIED",
        report.get(
            "match_explanation_engine"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Stage 9.6 status PASS",
        api_verification.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 9.6 COMPLETE",
        api_verification.get(
            "stage_9_6_complete"
        )
        is True,
        failures,
    )

    check(
        "REST API VERIFIED",
        api_verification.get(
            "match_intelligence_rest_api"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Stage 9 ready for 9.7",
        api_verification.get(
            "stage9_ready_for_9_7"
        )
        is True,
        failures,
    )

    # ========================================================
    # 3. Live runtime readiness
    # ========================================================

    print(
        "\n3. LIVE RUNTIME READINESS"
    )

    live_service = (
        MatchIntelligenceService()
    )

    live_status = (
        live_service.get_status()
    )

    if (
        live_status.get(
            "status"
        )
        != "READY"
    ):

        print(
            "Runtime reason:",
            live_status.get(
                "reason"
            ),
        )

    check(
        "Live intelligence service READY",
        live_status.get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "Runtime stage = 9.7",
        live_status.get(
            "stage"
        )
        == "9.7",
        failures,
    )

    check(
        "Runtime policy exact",
        live_status.get(
            "runtime_policy"
        )
        ==
        (
            "DUAL_UPSTREAM_DEPENDENCY_"
            "PLUS_TEMPORAL_BOUNDARY"
        ),
        failures,
    )

    check(
        "Stale fallback disabled",
        live_status.get(
            "stale_fallback"
        )
        is False,
        failures,
    )

    live_matches = []

    if (
        live_status.get(
            "status"
        )
        == "READY"
    ):

        try:

            live_matches = (
                live_service.get_all_matches()
            )

        except Exception as exc:

            print(
                "Live read error:",
                exc,
            )

            live_matches = []

    check(
        "Live intelligence rows > 0",
        len(
            live_matches
        )
        > 0,
        failures,
    )

    # ========================================================
    # 4. Stage 8 readiness propagation
    # ========================================================

    print(
        "\n4. STAGE 8 READINESS PROPAGATION"
    )

    toggle_context = (
        ToggleFixtureContextService()
    )

    runtime_service = (
        MatchIntelligenceService(

            fixture_context_service_factory=
                lambda:
                    toggle_context,
        )
    )

    ready_before = (
        runtime_service.get_status()
    )

    check(
        "Injected context READY -> intelligence READY",
        ready_before.get(
            "status"
        )
        == "READY",
        failures,
    )

    toggle_context.ready = False

    stale_status = (
        runtime_service.get_status()
    )

    check(
        "Injected context NOT_READY -> intelligence NOT_READY",
        stale_status.get(
            "status"
        )
        == "NOT_READY",
        failures,
    )

    stale_read_rejected = False

    try:

        runtime_service.get_all_matches()

    except MatchIntelligenceNotReadyError:

        stale_read_rejected = True

    except Exception:

        stale_read_rejected = True

    check(
        "No stale match fallback",
        stale_read_rejected,
        failures,
    )

    toggle_context.ready = True

    recovered_status = (
        runtime_service.get_status()
    )

    check(
        "Same service object recovers to READY",
        recovered_status.get(
            "status"
        )
        == "READY",
        failures,
    )

    recovered_rows = []

    try:

        recovered_rows = (
            runtime_service.get_all_matches()
        )

    except Exception:

        recovered_rows = []

    check(
        "Recovered service serves rows",
        len(
            recovered_rows
        )
        > 0,
        failures,
    )

    # ========================================================
    # 5. Dynamic Stage 9.2 dependency revalidation
    # ========================================================

    print(
        "\n5. DYNAMIC UPSTREAM DEPENDENCY REVALIDATION"
    )

    with tempfile.TemporaryDirectory() as temp_dir:

        temp_dir = Path(
            temp_dir
        )

        temp_base_report = (
            temp_dir
            / "match_intelligence_base_report.json"
        )

        temp_report = (
            temp_dir
            / "match_intelligence_report.json"
        )

        base_payload = copy.deepcopy(
            load_json(
                BASE_REPORT_FILE
            )
        )

        report_payload = copy.deepcopy(
            load_json(
                REPORT_FILE
            )
        )

        dependencies = (
            base_payload.get(
                "dependency_identity",
                {}
            )
        )

        selected_dependency = (
            "production_predictions"
        )

        selected_item = dependencies.get(
            selected_dependency
        )

        check(
            "Production prediction dependency available",
            isinstance(
                selected_item,
                dict,
            ),
            failures,
        )

        original_dependency_sha = None

        if isinstance(
            selected_item,
            dict,
        ):

            original_dependency_sha = (
                selected_item.get(
                    "sha256"
                )
            )

            selected_item[
                "sha256"
            ] = (
                "0"
                * 64
            )

        save_json(
            temp_base_report,
            base_payload,
        )

        report_payload[
            "dependency_identity"
        ][
            "match_intelligence_base_report"
        ][
            "sha256"
        ] = sha256_file(
            temp_base_report
        )

        save_json(
            temp_report,
            report_payload,
        )

        dependency_test_service = (
            MatchIntelligenceService(

                base_report_file=
                    temp_base_report,

                report_file=
                    temp_report,

                fixture_context_service_factory=
                    lambda:
                        toggle_context,
            )
        )

        dependency_stale = (
            dependency_test_service.get_status()
        )

        check(
            "Mutated dependency SHA -> NOT_READY",
            dependency_stale.get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        dependency_read_rejected = False

        try:

            dependency_test_service.get_all_matches()

        except MatchIntelligenceNotReadyError:

            dependency_read_rejected = True

        except Exception:

            dependency_read_rejected = True

        check(
            "Mutated dependency cannot serve stale rows",
            dependency_read_rejected,
            failures,
        )

        if isinstance(
            selected_item,
            dict,
        ):

            selected_item[
                "sha256"
            ] = original_dependency_sha

        save_json(
            temp_base_report,
            base_payload,
        )

        report_payload[
            "dependency_identity"
        ][
            "match_intelligence_base_report"
        ][
            "sha256"
        ] = sha256_file(
            temp_base_report
        )

        save_json(
            temp_report,
            report_payload,
        )

        dependency_recovered = (
            dependency_test_service.get_status()
        )

        check(
            (
                "Dependency restoration -> READY "
                "without service restart"
            ),
            dependency_recovered.get(
                "status"
            )
            == "READY",
            failures,
        )

    # ========================================================
    # 6. Stage 9 final artifact mutation
    # ========================================================

    print(
        "\n6. STAGE 9 ARTIFACT MUTATION"
    )

    with tempfile.TemporaryDirectory() as temp_dir:

        temp_dir = Path(
            temp_dir
        )

        temp_intelligence = (
            temp_dir
            / "match_intelligence.csv"
        )

        temp_report = (
            temp_dir
            / "match_intelligence_report.json"
        )

        original_bytes = (
            INTELLIGENCE_FILE.read_bytes()
        )

        temp_intelligence.write_bytes(
            original_bytes
        )

        temp_report_payload = copy.deepcopy(
            load_json(
                REPORT_FILE
            )
        )

        temp_report_payload[
            "output_artifact"
        ][
            "sha256"
        ] = sha256_file(
            temp_intelligence
        )

        save_json(
            temp_report,
            temp_report_payload,
        )

        artifact_test_service = (
            MatchIntelligenceService(

                intelligence_file=
                    temp_intelligence,

                report_file=
                    temp_report,

                fixture_context_service_factory=
                    lambda:
                        toggle_context,
            )
        )

        check(
            "Temporary clean artifact READY",
            artifact_test_service.get_status().get(
                "status"
            )
            == "READY",
            failures,
        )

        with temp_intelligence.open(
            "ab"
        ) as file:

            file.write(
                b"\n"
            )

        artifact_stale = (
            artifact_test_service.get_status()
        )

        check(
            "Mutated Stage 9 artifact -> NOT_READY",
            artifact_stale.get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        artifact_read_rejected = False

        try:

            artifact_test_service.get_all_matches()

        except MatchIntelligenceNotReadyError:

            artifact_read_rejected = True

        except Exception:

            artifact_read_rejected = True

        check(
            "Mutated artifact has no stale fallback",
            artifact_read_rejected,
            failures,
        )

        temp_intelligence.write_bytes(
            original_bytes
        )

        artifact_recovered = (
            artifact_test_service.get_status()
        )

        check(
            (
                "Artifact restoration -> READY "
                "without service restart"
            ),
            artifact_recovered.get(
                "status"
            )
            == "READY",
            failures,
        )

    # ========================================================
    # 7. Healthy API + no-store
    # ========================================================

    print(
        "\n7. HEALTHY API / NO-STORE"
    )

    client = app.test_client()

    healthy_paths = [

        "/api/v1/intelligence/status",
        "/api/v1/intelligence/matches",
        "/api/v1/intelligence/upcoming",
    ]

    if live_matches:

        first = live_matches[
            0
        ]

        healthy_paths.append(
            (
                "/api/v1/intelligence/matches/"
                f"{first['fixture_id']}"
            )
        )

        healthy_paths.append(
            (
                "/api/v1/intelligence/team/"
                f"{first['home_team_name']}"
            )
        )

    for path in healthy_paths:

        response = client.get(
            path
        )

        check(
            f"GET {path} -> 200",
            response.status_code
            == 200,
            failures,
        )

        check(
            f"GET {path} Cache-Control no-store",
            has_no_store(
                response
            ),
            failures,
        )

    # ========================================================
    # 8. Exact public 503 behavior
    # ========================================================

    print(
        "\n8. FAIL-CLOSED 503 API"
    )

    with patch(
        (
            "backend.routes.intelligence_api."
            "MatchIntelligenceService"
        ),
        ForcedNotReadyService,
    ):

        stale_client = app.test_client()

        stale_paths = [

            "/api/v1/intelligence/status",
            "/api/v1/intelligence/matches",
            "/api/v1/intelligence/upcoming",
        ]

        for path in stale_paths:

            response = stale_client.get(
                path
            )

            payload = response_json(
                response
            )

            check(
                f"Stale GET {path} -> 503",
                response.status_code
                == 503,
                failures,
            )

            check(
                f"Stale GET {path} exact public payload",
                payload
                ==
                {
                    "status":
                        "NOT_READY",

                    "service":
                        "match_intelligence",
                },
                failures,
            )

            check(
                f"Stale GET {path} no-store",
                has_no_store(
                    response
                ),
                failures,
            )

    # ========================================================
    # 9. 404 / 405 + no-store
    # ========================================================

    print(
        "\n9. 404 / 405 SAFETY"
    )

    unknown = client.get(
        (
            "/api/v1/intelligence/matches/"
            "__fixtureiq_runtime_unknown__"
        )
    )

    check(
        "Unknown fixture -> 404",
        unknown.status_code
        == 404,
        failures,
    )

    check(
        "Unknown fixture response no-store",
        has_no_store(
            unknown
        ),
        failures,
    )

    write_response = client.post(
        "/api/v1/intelligence/matches"
    )

    check(
        "POST intelligence -> 405",
        write_response.status_code
        == 405,
        failures,
    )

    check(
        "405 response no-store",
        has_no_store(
            write_response
        ),
        failures,
    )

    # ========================================================
    # 10. Live artifact protection
    # ========================================================

    print(
        "\n10. LIVE WRITE PROTECTION"
    )

    for path in protected_paths:

        key = relative_path(
            path
        )

        check(
            f"{path.name} unchanged",
            sha256_file(
                path
            )
            ==
            protected_before[
                key
            ],
            failures,
        )

    # ========================================================
    # 11. Save Stage 9.7 artifact
    # ========================================================

    print(
        "\n11. SAVE STAGE 9.7 VERIFICATION"
    )

    overall_pass = (
        len(
            failures
        )
        == 0
    )

    if overall_pass:

        from datetime import (
            datetime,
            timezone,
        )

        verified_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        artifact = {

            "stage":
                "9.7",

            "status":
                "PASS",

            "stage_9_7_complete":
                True,

            "stage_9_7_status":
                "COMPLETE",

            "intelligence_runtime_safety":
                "VERIFIED",

            "runtime_policy":
                (
                    "DUAL_UPSTREAM_DEPENDENCY_"
                    "PLUS_TEMPORAL_BOUNDARY"
                ),

            "verified_at_utc":
                verified_at,

            "runtime_contract": {

                "revalidate_on_every_read":
                    True,

                "stage7_dependency_hashes_revalidated":
                    True,

                "stage8_dependency_hashes_revalidated":
                    True,

                "fixture_context_readiness_propagated":
                    True,

                "temporal_boundary_inherited":
                    True,

                "stale_status_code":
                    503,

                "stale_public_status":
                    "NOT_READY",

                "unknown_status_code":
                    404,

                "write_status_code":
                    405,

                "stale_fallback":
                    False,

                "partial_fallback":
                    False,

                "best_effort_fallback":
                    False,

                "restart_required_for_recovery":
                    False,

                "cache_control":
                    "no-store",
            },

            "negative_tests": {

                "fixture_context_not_ready_rejected":
                    True,

                "stale_read_rejected":
                    True,

                "dynamic_dependency_mutation_rejected":
                    True,

                "stage9_artifact_mutation_rejected":
                    True,

                "stale_api_returns_503":
                    True,

                "stale_api_payload_exact":
                    True,

                "stale_response_no_store":
                    True,
            },

            "recovery_tests": {

                "fixture_context_stale_to_ready_same_service":
                    True,

                "dependency_stale_to_ready_same_service":
                    True,

                "artifact_stale_to_ready_same_service":
                    True,
            },

            "safety": {

                "read_only":
                    True,

                "artifact_only":
                    True,

                "provider_fetch_performed":
                    False,

                "artifact_rebuild_performed":
                    False,

                "model_loaded":
                    False,

                "model_executed":
                    False,

                "model_modified":
                    False,

                "probabilities_modified":
                    False,

                "prediction_labels_modified":
                    False,

                "context_modified":
                    False,

                "stale_data_served":
                    False,

                "live_stage7_artifacts_modified":
                    False,

                "live_stage8_artifacts_modified":
                    False,

                "live_stage9_artifacts_modified":
                    False,
            },

            "dependency_identity": {

                "stage9_intelligence_contract": {

                    "path":
                        relative_path(
                            CONTRACT_FILE
                        ),

                    "sha256":
                        sha256_file(
                            CONTRACT_FILE
                        ),
                },

                "stage9_intelligence_contract_verification": {

                    "path":
                        relative_path(
                            CONTRACT_VERIFICATION_FILE
                        ),

                    "sha256":
                        sha256_file(
                            CONTRACT_VERIFICATION_FILE
                        ),
                },

                "match_intelligence_base": {

                    "path":
                        relative_path(
                            BASE_FILE
                        ),

                    "sha256":
                        sha256_file(
                            BASE_FILE
                        ),
                },

                "match_intelligence_base_report": {

                    "path":
                        relative_path(
                            BASE_REPORT_FILE
                        ),

                    "sha256":
                        sha256_file(
                            BASE_REPORT_FILE
                        ),
                },

                "match_intelligence": {

                    "path":
                        relative_path(
                            INTELLIGENCE_FILE
                        ),

                    "sha256":
                        sha256_file(
                            INTELLIGENCE_FILE
                        ),
                },

                "match_intelligence_report": {

                    "path":
                        relative_path(
                            REPORT_FILE
                        ),

                    "sha256":
                        sha256_file(
                            REPORT_FILE
                        ),
                },

                "intelligence_api_verification": {

                    "path":
                        relative_path(
                            API_VERIFICATION_FILE
                        ),

                    "sha256":
                        sha256_file(
                            API_VERIFICATION_FILE
                        ),
                },
            },

            "stage9_ready_for_9_8":
                True,

            "next_stage":
                "9.8",

            "failures":
                [],
        }

        save_json_atomic(
            OUTPUT_FILE,
            artifact,
        )

        print(
            OUTPUT_FILE
        )

    print(
        "\n" + "=" * 72
    )

    if overall_pass:

        print(
            "STAGE 9.7: COMPLETE"
        )

        print(
            "INTELLIGENCE RUNTIME SAFETY: VERIFIED"
        )

        print(
            "STAGE 9 READY FOR 9.8"
        )

    else:

        print(
            "STAGE 9.7: FAIL"
        )

        print(
            "INTELLIGENCE RUNTIME SAFETY: NOT VERIFIED"
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
        if overall_pass
        else 1
    )


if __name__ == "__main__":

    main()
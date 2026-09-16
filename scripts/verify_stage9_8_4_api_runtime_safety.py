"""
FixtureIQ Stage 9.8.4
API / RUNTIME / SAFETY VERIFICATION

Purpose
-------
Independently verify the final public/runtime behavior of the completed
Stage 9 Match Intelligence layer.

Verifies:
- 9.8.1 / 9.8.2 / 9.8.3 evidence remains current
- Stage 9.6 REST API verification remains current
- Stage 9.7 runtime-safety verification remains current
- live MatchIntelligenceService is READY
- exact five-route intelligence API surface
- GET-only / read-only contract
- healthy 200 READY responses
- unknown fixture/team -> 404 NOT_FOUND
- write attempts -> 405
- stale dependencies -> 503 NOT_READY
- no-store policy on healthy, stale, 404 and 405 responses
- same-process stale -> healthy recovery
- no stale fallback
- no provider fetch
- no rebuild
- no model execution
- no protected artifact mutation

This gate DOES NOT promote Stage 9.

Only Stage 9.8.5 may perform final promotion.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


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

INTELLIGENCE_REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_report.json"
)

API_VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "intelligence_api_verification.json"
)

RUNTIME_VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "intelligence_runtime_verification.json"
)

FOUNDATION_FILE = (
    INTELLIGENCE_DIR
    / "stage9_8_1_foundation_verification.json"
)

PREDICTION_INTEGRITY_FILE = (
    INTELLIGENCE_DIR
    / "stage9_8_2_prediction_integrity_verification.json"
)

INTELLIGENCE_INTEGRITY_FILE = (
    INTELLIGENCE_DIR
    / "stage9_8_3_intelligence_integrity_verification.json"
)

OUTPUT_FILE = (
    INTELLIGENCE_DIR
    / "stage9_8_4_api_runtime_safety_verification.json"
)


# ============================================================
# Exact public Stage 9 API
# ============================================================

EXPECTED_INTELLIGENCE_ROUTES = {

    "/api/v1/intelligence/status",

    "/api/v1/intelligence/matches",

    "/api/v1/intelligence/matches/<fixture_id>",

    "/api/v1/intelligence/team/<path:team_name>",

    "/api/v1/intelligence/upcoming",
}


EXPECTED_RUNTIME_POLICY = (
    "DUAL_UPSTREAM_DEPENDENCY_"
    "PLUS_TEMPORAL_BOUNDARY"
)


# ============================================================
# Helpers
# ============================================================

def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise RuntimeError(
            f"Missing JSON artifact: {path}"
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


def save_json_atomic(
    path: Path,
    payload: dict,
) -> None:

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

        raise RuntimeError(
            f"Missing artifact: {path}"
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
            path.resolve().relative_to(
                BASE_DIR.resolve()
            )
        )
        .replace(
            "\\",
            "/",
        )
    )


def resolve_project_path(
    value: str,
) -> Path:

    raw = Path(
        str(value)
    )

    if raw.is_absolute():

        result = raw.resolve()

    else:

        result = (
            BASE_DIR
            / raw
        ).resolve()

    try:

        result.relative_to(
            BASE_DIR.resolve()
        )

    except ValueError as exc:

        raise RuntimeError(
            (
                "Evidence dependency escapes "
                "FixtureIQ project root: "
                f"{value}"
            )
        ) from exc

    return result


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


def response_body(
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
        ==
        "no-cache"
        and
        expires
        ==
        "0"
    )


def validate_dependency_identity(
    evidence: dict,
    failures: list[str],
    label_prefix: str,
) -> None:

    dependency_identity = (
        evidence.get(
            "dependency_identity",
            {}
        )
    )

    check(
        f"{label_prefix} dependency identity is object",
        isinstance(
            dependency_identity,
            dict,
        ),
        failures,
    )

    if not isinstance(
        dependency_identity,
        dict,
    ):

        return

    for (
        path_text,
        item,
    ) in dependency_identity.items():

        if not isinstance(
            item,
            dict,
        ):

            check(
                (
                    f"{label_prefix}: "
                    f"{path_text} identity valid"
                ),
                False,
                failures,
            )

            continue

        expected_sha = str(
            item.get(
                "sha256",
                "",
            )
        ).strip()

        try:

            path = resolve_project_path(
                path_text
            )

            current = (
                path.exists()
                and
                expected_sha
                ==
                sha256_file(
                    path
                )
            )

        except Exception:

            current = False

        check(
            (
                f"{label_prefix}: "
                f"{Path(path_text).name} current"
            ),
            current,
            failures,
        )


# ============================================================
# Toggleable Stage 8 readiness
# ============================================================

class ToggleFixtureContextService:

    def __init__(
        self,
    ) -> None:

        self.ready = True

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
                (
                    "Stage 9.8.4 forced "
                    "upstream stale state."
                ),
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
                (
                    "Stage 9.8.4 forced "
                    "runtime stale state."
                ),
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
        "FixtureIQ Stage 9.8.4"
    )

    print(
        "API / RUNTIME / SAFETY VERIFICATION"
    )

    print("=" * 72)

    failures: list[str] = []

    # ========================================================
    # 1. Required artifacts
    # ========================================================

    print(
        "\n1. REQUIRED FINAL-GATE ARTIFACTS"
    )

    required_files = [

        CONTRACT_FILE,
        CONTRACT_VERIFICATION_FILE,

        BASE_FILE,
        BASE_REPORT_FILE,

        INTELLIGENCE_FILE,
        INTELLIGENCE_REPORT_FILE,

        API_VERIFICATION_FILE,
        RUNTIME_VERIFICATION_FILE,

        FOUNDATION_FILE,
        PREDICTION_INTEGRITY_FILE,
        INTELLIGENCE_INTEGRITY_FILE,
    ]

    for path in required_files:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        print(
            "\n" + "=" * 72
        )

        print(
            "STAGE 9.8.4: FAIL"
        )

        print(
            "API / RUNTIME / SAFETY: NOT VERIFIED"
        )

        print("=" * 72)

        sys.exit(1)

    protected_before = {

        relative_path(
            path
        ):
            sha256_file(
                path
            )

        for path in required_files
    }

    # ========================================================
    # 2. 9.8.1 / 9.8.2 / 9.8.3 chain
    # ========================================================

    print(
        "\n2. PREVIOUS FINAL-GATE CHAIN"
    )

    foundation = load_json(
        FOUNDATION_FILE
    )

    prediction_integrity = load_json(
        PREDICTION_INTEGRITY_FILE
    )

    intelligence_integrity = load_json(
        INTELLIGENCE_INTEGRITY_FILE
    )

    check(
        "Stage 9.8.1 PASS",
        foundation.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )

    check(
        "Foundation VERIFIED",
        foundation.get(
            "foundation_verification"
        )
        ==
        "VERIFIED",
        failures,
    )

    check(
        "Stage 9.8.2 PASS",
        prediction_integrity.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )

    check(
        "Prediction integrity VERIFIED",
        prediction_integrity.get(
            "prediction_integrity"
        )
        ==
        "VERIFIED",
        failures,
    )

    check(
        "Stage 9.8.3 PASS",
        intelligence_integrity.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )

    check(
        "Intelligence integrity VERIFIED",
        intelligence_integrity.get(
            "intelligence_integrity"
        )
        ==
        "VERIFIED",
        failures,
    )

    check(
        "Stage 9.8.3 authorized 9.8.4",
        intelligence_integrity.get(
            "stage9_ready_for_9_8_4"
        )
        is True,
        failures,
    )

    # ========================================================
    # 3. Previous-gate freshness
    # ========================================================

    print(
        "\n3. FINAL-GATE EVIDENCE FRESHNESS"
    )

    validate_dependency_identity(
        prediction_integrity,
        failures,
        "9.8.2",
    )

    validate_dependency_identity(
        intelligence_integrity,
        failures,
        "9.8.3",
    )

    # Foundation has API/runtime identities we specifically
    # want to ensure remain current.

    foundation_dependencies = (
        foundation.get(
            "dependency_identity",
            {}
        )
    )

    for path in [

        API_VERIFICATION_FILE,
        RUNTIME_VERIFICATION_FILE,
        INTELLIGENCE_FILE,
        INTELLIGENCE_REPORT_FILE,
    ]:

        key = relative_path(
            path
        )

        item = foundation_dependencies.get(
            key,
            {}
        )

        check(
            (
                f"{path.name} unchanged "
                "since 9.8.1"
            ),
            item.get(
                "sha256"
            )
            ==
            sha256_file(
                path
            ),
            failures,
        )

    # ========================================================
    # 4. Stage 9.6 API evidence
    # ========================================================

    print(
        "\n4. STAGE 9.6 REST API EVIDENCE"
    )

    api_verification = load_json(
        API_VERIFICATION_FILE
    )

    check(
        "Stage 9.6 verification PASS",
        api_verification.get(
            "status"
        )
        ==
        "PASS",
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
        "Match Intelligence REST API VERIFIED",
        api_verification.get(
            "match_intelligence_rest_api"
        )
        ==
        "VERIFIED",
        failures,
    )

    check(
        "Stage 9.6 authorized 9.7",
        api_verification.get(
            "stage9_ready_for_9_7"
        )
        is True,
        failures,
    )

    # ========================================================
    # 5. Stage 9.7 runtime evidence
    # ========================================================

    print(
        "\n5. STAGE 9.7 RUNTIME-SAFETY EVIDENCE"
    )

    runtime_verification = load_json(
        RUNTIME_VERIFICATION_FILE
    )

    check(
        "Stage 9.7 verification PASS",
        runtime_verification.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )

    check(
        "Stage 9.7 COMPLETE",
        runtime_verification.get(
            "stage_9_7_complete"
        )
        is True,
        failures,
    )

    check(
        "Runtime safety VERIFIED",
        runtime_verification.get(
            "intelligence_runtime_safety"
        )
        ==
        "VERIFIED",
        failures,
    )

    check(
        "Runtime policy exact",
        runtime_verification.get(
            "runtime_policy"
        )
        ==
        EXPECTED_RUNTIME_POLICY,
        failures,
    )

    check(
        "Stage 9.7 authorized Stage 9.8",
        runtime_verification.get(
            "stage9_ready_for_9_8"
        )
        is True,
        failures,
    )

    runtime_contract = (
        runtime_verification.get(
            "runtime_contract",
            {}
        )
    )

    check(
        "Revalidate on every read",
        runtime_contract.get(
            "revalidate_on_every_read"
        )
        is True,
        failures,
    )

    check(
        "Stage 7 hashes revalidated",
        runtime_contract.get(
            "stage7_dependency_hashes_revalidated"
        )
        is True,
        failures,
    )

    check(
        "Stage 8 hashes revalidated",
        runtime_contract.get(
            "stage8_dependency_hashes_revalidated"
        )
        is True,
        failures,
    )

    check(
        "Fixture-context readiness propagated",
        runtime_contract.get(
            "fixture_context_readiness_propagated"
        )
        is True,
        failures,
    )

    check(
        "Temporal boundary inherited",
        runtime_contract.get(
            "temporal_boundary_inherited"
        )
        is True,
        failures,
    )

    check(
        "Stale fallback disabled",
        runtime_contract.get(
            "stale_fallback"
        )
        is False,
        failures,
    )

    check(
        "Partial fallback disabled",
        runtime_contract.get(
            "partial_fallback"
        )
        is False,
        failures,
    )

    check(
        "Best-effort fallback disabled",
        runtime_contract.get(
            "best_effort_fallback"
        )
        is False,
        failures,
    )

    check(
        "Recovery does not require restart",
        runtime_contract.get(
            "restart_required_for_recovery"
        )
        is False,
        failures,
    )

    check(
        "Stale status code = 503",
        runtime_contract.get(
            "stale_status_code"
        )
        ==
        503,
        failures,
    )

    check(
        "Unknown status code = 404",
        runtime_contract.get(
            "unknown_status_code"
        )
        ==
        404,
        failures,
    )

    check(
        "Write status code = 405",
        runtime_contract.get(
            "write_status_code"
        )
        ==
        405,
        failures,
    )

    # ========================================================
    # 6. Stage 9.7 negative / recovery evidence
    # ========================================================

    print(
        "\n6. STAGE 9.7 NEGATIVE / RECOVERY EVIDENCE"
    )

    negative_tests = (
        runtime_verification.get(
            "negative_tests",
            {}
        )
    )

    for name in [

        "fixture_context_not_ready_rejected",
        "stale_read_rejected",
        "dynamic_dependency_mutation_rejected",
        "stage9_artifact_mutation_rejected",
        "stale_api_returns_503",
        "stale_api_payload_exact",
        "stale_response_no_store",
    ]:

        check(
            f"Negative test {name}",
            negative_tests.get(
                name
            )
            is True,
            failures,
        )

    recovery_tests = (
        runtime_verification.get(
            "recovery_tests",
            {}
        )
    )

    for name in [

        "fixture_context_stale_to_ready_same_service",
        "dependency_stale_to_ready_same_service",
        "artifact_stale_to_ready_same_service",
    ]:

        check(
            f"Recovery test {name}",
            recovery_tests.get(
                name
            )
            is True,
            failures,
        )

    # ========================================================
    # 7. Live service
    # ========================================================

    print(
        "\n7. LIVE MATCH INTELLIGENCE SERVICE"
    )

    service = (
        MatchIntelligenceService()
    )

    live_status = (
        service.get_status()
    )

    if (
        live_status.get(
            "status"
        )
        !=
        "READY"
    ):

        print(
            "Runtime reason:",
            live_status.get(
                "reason"
            ),
        )

    check(
        "Live service READY",
        live_status.get(
            "status"
        )
        ==
        "READY",
        failures,
    )

    check(
        "Live service stage 9.7",
        live_status.get(
            "stage"
        )
        ==
        "9.7",
        failures,
    )

    check(
        "Live runtime policy exact",
        live_status.get(
            "runtime_policy"
        )
        ==
        EXPECTED_RUNTIME_POLICY,
        failures,
    )

    check(
        "Live stale fallback false",
        live_status.get(
            "stale_fallback"
        )
        is False,
        failures,
    )

    matches = []

    if (
        live_status.get(
            "status"
        )
        ==
        "READY"
    ):

        try:

            matches = (
                service.get_all_matches()
            )

        except Exception as exc:

            print(
                "Live intelligence read error:",
                exc,
            )

            matches = []

    check(
        "Live intelligence rows > 0",
        len(
            matches
        )
        >
        0,
        failures,
    )

    if matches:

        check(
            "Live fixture count matches status",
            len(
                matches
            )
            ==
            live_status.get(
                "fixture_count"
            ),
            failures,
        )

    # ========================================================
    # 8. Same-process stale -> healthy recovery
    # ========================================================

    print(
        "\n8. SAME-PROCESS RUNTIME RECOVERY"
    )

    toggle_context = (
        ToggleFixtureContextService()
    )

    recovery_service = (
        MatchIntelligenceService(
            fixture_context_service_factory=
                lambda:
                    toggle_context,
        )
    )

    initial_ready = (
        recovery_service.get_status()
    )

    check(
        "Injected READY -> intelligence READY",
        initial_ready.get(
            "status"
        )
        ==
        "READY",
        failures,
    )

    toggle_context.ready = False

    forced_stale = (
        recovery_service.get_status()
    )

    check(
        "Injected NOT_READY -> intelligence NOT_READY",
        forced_stale.get(
            "status"
        )
        ==
        "NOT_READY",
        failures,
    )

    stale_read_rejected = False

    try:

        recovery_service.get_all_matches()

    except MatchIntelligenceNotReadyError:

        stale_read_rejected = True

    except Exception:

        stale_read_rejected = True

    check(
        "No stale-row fallback",
        stale_read_rejected,
        failures,
    )

    toggle_context.ready = True

    recovered = (
        recovery_service.get_status()
    )

    check(
        "Same service object recovers to READY",
        recovered.get(
            "status"
        )
        ==
        "READY",
        failures,
    )

    recovered_rows = []

    try:

        recovered_rows = (
            recovery_service.get_all_matches()
        )

    except Exception:

        recovered_rows = []

    check(
        "Recovered service serves rows",
        len(
            recovered_rows
        )
        >
        0,
        failures,
    )

    # ========================================================
    # 9. Exact REST route surface
    # ========================================================

    print(
        "\n9. EXACT REST API SURFACE"
    )

    intelligence_rules = [

        rule

        for rule in app.url_map.iter_rules()

        if rule.rule.startswith(
            "/api/v1/intelligence"
        )
    ]

    actual_routes = {

        rule.rule

        for rule in intelligence_rules
    }

    check(
        "Exactly 5 intelligence routes",
        len(
            actual_routes
        )
        ==
        5,
        failures,
    )

    check(
        "Intelligence route set exact",
        actual_routes
        ==
        EXPECTED_INTELLIGENCE_ROUTES,
        failures,
    )

    for rule in intelligence_rules:

        methods = set(
            rule.methods
        )

        check(
            f"{rule.rule}: GET enabled",
            "GET"
            in methods,
            failures,
        )

        check(
            f"{rule.rule}: POST disabled",
            "POST"
            not in methods,
            failures,
        )

        check(
            f"{rule.rule}: PUT disabled",
            "PUT"
            not in methods,
            failures,
        )

        check(
            f"{rule.rule}: DELETE disabled",
            "DELETE"
            not in methods,
            failures,
        )

    # ========================================================
    # 10. Existing application surface preserved
    # ========================================================

    print(
        "\n10. EXISTING APPLICATION SURFACE"
    )

    all_routes = {

        rule.rule

        for rule in app.url_map.iter_rules()
    }

    check(
        "/api/health preserved",
        "/api/health"
        in
        all_routes,
        failures,
    )

    check(
        "Production API routes preserved",
        any(
            route.startswith(
                "/api/v1/production"
            )

            for route in all_routes
        ),
        failures,
    )

    check(
        "Context API routes preserved",
        any(
            route.startswith(
                "/api/v1/context"
            )

            for route in all_routes
        ),
        failures,
    )

    health_response = (
        app.test_client().get(
            "/api/health"
        )
    )

    check(
        "/api/health -> 200",
        health_response.status_code
        ==
        200,
        failures,
    )

    # ========================================================
    # 11. Healthy API
    # ========================================================

    print(
        "\n11. HEALTHY INTELLIGENCE API"
    )

    client = app.test_client()

    healthy_paths = [

        "/api/v1/intelligence/status",

        "/api/v1/intelligence/matches",

        "/api/v1/intelligence/upcoming",
    ]

    if matches:

        first = matches[0]

        fixture_id = str(
            first.get(
                "fixture_id",
                "",
            )
        )

        team_name = str(
            first.get(
                "home_team_name",
                "",
            )
        )

        healthy_paths.extend(
            [

                (
                    "/api/v1/intelligence/matches/"
                    f"{fixture_id}"
                ),

                (
                    "/api/v1/intelligence/team/"
                    f"{team_name}"
                ),
            ]
        )

    for path in healthy_paths:

        response = client.get(
            path
        )

        check(
            f"GET {path} -> 200",
            response.status_code
            ==
            200,
            failures,
        )

        payload = response_body(
            response
        )

        check(
            f"GET {path} -> READY",
            payload.get(
                "status"
            )
            ==
            "READY",
            failures,
        )

        check(
            f"GET {path} -> no-store",
            has_no_store(
                response
            ),
            failures,
        )

    # ========================================================
    # 12. Public projection safety
    # ========================================================

    print(
        "\n12. PUBLIC RESPONSE SAFETY"
    )

    matches_response = client.get(
        "/api/v1/intelligence/matches"
    )

    matches_payload = response_body(
        matches_response
    )

    public_matches = (
        matches_payload.get(
            "matches",
            []
        )
    )

    projection_safe = True

    forbidden_public_fragments = [

        "model_path",
        "model_sha",
        "sha256",
        "feature_schema",
        "artifact_path",
        "api_key",
        "provider_response",
    ]

    required_public_fields = {

        "fixture_id",

        "home_team_name",
        "away_team_name",

        "stage7_prob_home_win",
        "stage7_prob_draw",
        "stage7_prob_away_win",

        "stage7_predicted_label",
        "stage7_confidence",

        "stage9_top_probability",
        "stage9_probability_margin",

        "stage9_confidence_band",
        "stage9_uncertainty_band",

        "stage9_context_support_score",
        "stage9_context_alignment",

        "stage9_explanation_headline",
        "stage9_explanation_summary",
    }

    if not public_matches:

        projection_safe = False

    else:

        first_public = public_matches[0]

        if not required_public_fields.issubset(
            set(
                first_public.keys()
            )
        ):

            projection_safe = False

        lowered_keys = {

            str(key).casefold()

            for key in first_public.keys()
        }

        for forbidden in forbidden_public_fragments:

            if any(
                forbidden
                in key

                for key in lowered_keys
            ):

                projection_safe = False

    check(
        "Public projection contains required intelligence",
        projection_safe,
        failures,
    )

    # ========================================================
    # 13. Unknown fixture / team = 404
    # ========================================================

    print(
        "\n13. UNKNOWN IDENTITY CONTRACT"
    )

    unknown_fixture = client.get(
        (
            "/api/v1/intelligence/matches/"
            "__fixtureiq_stage9_8_4_unknown_fixture__"
        )
    )

    check(
        "Unknown fixture -> 404",
        unknown_fixture.status_code
        ==
        404,
        failures,
    )

    check(
        "Unknown fixture payload exact",
        response_body(
            unknown_fixture
        )
        ==
        {
            "status":
                "NOT_FOUND",

            "service":
                "match_intelligence",
        },
        failures,
    )

    check(
        "Unknown fixture -> no-store",
        has_no_store(
            unknown_fixture
        ),
        failures,
    )

    unknown_team = client.get(
        (
            "/api/v1/intelligence/team/"
            "__fixtureiq_stage9_8_4_unknown_team__"
        )
    )

    check(
        "Unknown team -> 404",
        unknown_team.status_code
        ==
        404,
        failures,
    )

    check(
        "Unknown team payload exact",
        response_body(
            unknown_team
        )
        ==
        {
            "status":
                "NOT_FOUND",

            "service":
                "match_intelligence",
        },
        failures,
    )

    check(
        "Unknown team -> no-store",
        has_no_store(
            unknown_team
        ),
        failures,
    )

    # ========================================================
    # 14. Read-only contract = 405
    # ========================================================

    print(
        "\n14. READ-ONLY API CONTRACT"
    )

    write_targets = [

        "/api/v1/intelligence/status",

        "/api/v1/intelligence/matches",

        "/api/v1/intelligence/upcoming",
    ]

    if matches:

        first = matches[0]

        write_targets.extend(
            [

                (
                    "/api/v1/intelligence/matches/"
                    f"{first['fixture_id']}"
                ),

                (
                    "/api/v1/intelligence/team/"
                    f"{first['home_team_name']}"
                ),
            ]
        )

    for path in write_targets:

        for method in [
            "post",
            "put",
            "delete",
        ]:

            response = getattr(
                client,
                method,
            )(
                path
            )

            check(
                (
                    f"{method.upper()} "
                    f"{path} -> 405"
                ),
                response.status_code
                ==
                405,
                failures,
            )

            check(
                (
                    f"{method.upper()} "
                    f"{path} -> no-store"
                ),
                has_no_store(
                    response
                ),
                failures,
            )

    # ========================================================
    # 15. Forced stale API = exact 503
    # ========================================================

    print(
        "\n15. FAIL-CLOSED 503 API"
    )

    stale_test_paths = [

        "/api/v1/intelligence/status",

        "/api/v1/intelligence/matches",

        "/api/v1/intelligence/upcoming",

        (
            "/api/v1/intelligence/matches/"
            "__forced_stale_fixture__"
        ),

        (
            "/api/v1/intelligence/team/"
            "__forced_stale_team__"
        ),
    ]

    with patch(
        (
            "backend.routes.intelligence_api."
            "MatchIntelligenceService"
        ),
        ForcedNotReadyService,
    ):

        stale_client = (
            app.test_client()
        )

        for path in stale_test_paths:

            response = stale_client.get(
                path
            )

            check(
                f"Forced stale {path} -> 503",
                response.status_code
                ==
                503,
                failures,
            )

            check(
                (
                    f"Forced stale {path} "
                    "payload exact"
                ),
                response_body(
                    response
                )
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
                f"Forced stale {path} -> no-store",
                has_no_store(
                    response
                ),
                failures,
            )

    # ========================================================
    # 16. Runtime safety declarations
    # ========================================================

    print(
        "\n16. RUNTIME SAFETY DECLARATIONS"
    )

    runtime_safety = (
        runtime_verification.get(
            "safety",
            {}
        )
    )

    check(
        "Runtime layer read-only",
        runtime_safety.get(
            "read_only"
        )
        is True,
        failures,
    )

    check(
        "Runtime layer artifact-only",
        runtime_safety.get(
            "artifact_only"
        )
        is True,
        failures,
    )

    check(
        "No provider fetch performed",
        runtime_safety.get(
            "provider_fetch_performed"
        )
        is False,
        failures,
    )

    check(
        "No artifact rebuild performed",
        runtime_safety.get(
            "artifact_rebuild_performed"
        )
        is False,
        failures,
    )

    check(
        "Model not loaded",
        runtime_safety.get(
            "model_loaded"
        )
        is False,
        failures,
    )

    check(
        "Model not executed",
        runtime_safety.get(
            "model_executed"
        )
        is False,
        failures,
    )

    check(
        "Probabilities not modified",
        runtime_safety.get(
            "probabilities_modified"
        )
        is False,
        failures,
    )

    check(
        "Prediction labels not modified",
        runtime_safety.get(
            "prediction_labels_modified"
        )
        is False,
        failures,
    )

    check(
        "Context not modified",
        runtime_safety.get(
            "context_modified"
        )
        is False,
        failures,
    )

    check(
        "Stale data not served",
        runtime_safety.get(
            "stale_data_served"
        )
        is False,
        failures,
    )

    # ========================================================
    # 17. Write protection
    # ========================================================

    print(
        "\n17. FINAL RUNTIME WRITE PROTECTION"
    )

    for path in required_files:

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
    # 18. Save Stage 9.8.4 evidence
    # ========================================================

    print(
        "\n18. SAVE STAGE 9.8.4 EVIDENCE"
    )

    overall_pass = (
        len(
            failures
        )
        ==
        0
    )

    if overall_pass:

        verified_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        evidence = {

            "stage":
                "9.8.4",

            "name":
                "API_RUNTIME_SAFETY_VERIFICATION",

            "status":
                "PASS",

            "stage_9_8_4_complete":
                True,

            "api_runtime_safety":
                "VERIFIED",

            "verified_at_utc":
                verified_at,

            "runtime_policy":
                EXPECTED_RUNTIME_POLICY,

            "api": {

                "route_count":
                    5,

                "route_set_exact":
                    True,

                "get_only":
                    True,

                "healthy_status_code":
                    200,

                "healthy_public_status":
                    "READY",

                "unknown_status_code":
                    404,

                "unknown_public_status":
                    "NOT_FOUND",

                "write_status_code":
                    405,

                "stale_status_code":
                    503,

                "stale_public_status":
                    "NOT_READY",

                "cache_control_no_store":
                    True,

                "public_projection_safe":
                    True,
            },

            "runtime": {

                "live_service_ready":
                    True,

                "revalidate_on_every_read":
                    True,

                "stage7_dependency_revalidation":
                    True,

                "stage8_dependency_revalidation":
                    True,

                "temporal_boundary_inherited":
                    True,

                "fixture_context_readiness_propagated":
                    True,

                "stale_fallback":
                    False,

                "partial_fallback":
                    False,

                "best_effort_fallback":
                    False,

                "same_process_recovery_verified":
                    True,

                "restart_required_for_recovery":
                    False,
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

                "protected_artifacts_modified":
                    False,
            },

            "dependency_identity": {

                relative_path(
                    path
                ): {
                    "sha256":
                        sha256_file(
                            path
                        )
                }

                for path in required_files
            },

            "promotion": {

                "stage_9_complete":
                    False,

                "stage_9_8_complete":
                    False,

                "promotion_authorized":
                    False,

                "promotion_owner":
                    "9.8.5",
            },

            "stage9_ready_for_9_8_5":
                True,

            "next_stage":
                "9.8.5",

            "failures":
                [],
        }

        save_json_atomic(
            OUTPUT_FILE,
            evidence,
        )

        print(
            OUTPUT_FILE
        )

    # ========================================================
    # Final result
    # ========================================================

    print(
        "\n" + "=" * 72
    )

    if overall_pass:

        print(
            "STAGE 9.8.4: PASS"
        )

        print(
            "API / RUNTIME / SAFETY VERIFICATION: VERIFIED"
        )

        print(
            "FAIL-CLOSED PRODUCTION BEHAVIOR: VERIFIED"
        )

        print(
            "STAGE 9 READY FOR 9.8.5"
        )

        print()

        print(
            "STAGE 9 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 9.8.4: FAIL"
        )

        print(
            "API / RUNTIME / SAFETY VERIFICATION: "
            "NOT VERIFIED"
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
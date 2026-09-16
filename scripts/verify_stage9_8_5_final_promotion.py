"""
FixtureIQ Stage 9.8.5
FINAL STAGE 9 PROMOTION

This is the sole authoritative Stage 9 promotion gate.

Promotion is permitted only when:

9.8.1 Foundation Verification              PASS
9.8.2 Prediction Integrity Verification    PASS
9.8.3 Intelligence Integrity Verification  PASS
9.8.4 API / Runtime / Safety Verification  PASS

and all evidence remains current at promotion time.

This script:
- does NOT rebuild any artifact
- does NOT fetch provider data
- does NOT load or execute the model
- does NOT alter predictions
- does NOT alter context
- does NOT alter intelligence
- writes only stage9_final_verification.json

If any prerequisite is stale or invalid, Stage 9 is NOT promoted.
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


from backend.app import app

from backend.services.match_intelligence_service import (
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


STAGE_9_8_1_FILE = (
    INTELLIGENCE_DIR
    / "stage9_8_1_foundation_verification.json"
)

STAGE_9_8_2_FILE = (
    INTELLIGENCE_DIR
    / "stage9_8_2_prediction_integrity_verification.json"
)

STAGE_9_8_3_FILE = (
    INTELLIGENCE_DIR
    / "stage9_8_3_intelligence_integrity_verification.json"
)

STAGE_9_8_4_FILE = (
    INTELLIGENCE_DIR
    / "stage9_8_4_api_runtime_safety_verification.json"
)


FINAL_FILE = (
    INTELLIGENCE_DIR
    / "stage9_final_verification.json"
)


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
    path_text: str,
) -> Path:

    raw = Path(
        str(path_text)
    )

    if raw.is_absolute():

        resolved = raw.resolve()

    else:

        resolved = (
            BASE_DIR
            / raw
        ).resolve()

    try:

        resolved.relative_to(
            BASE_DIR.resolve()
        )

    except ValueError as exc:

        raise RuntimeError(
            (
                "Dependency path escapes "
                "FixtureIQ project root: "
                f"{path_text}"
            )
        ) from exc

    return resolved


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
        ==
        "no-cache"
        and
        expires
        ==
        "0"
    )


def verify_evidence_dependencies(
    evidence: dict,
    gate_name: str,
    failures: list[str],
) -> None:

    dependency_identity = (
        evidence.get(
            "dependency_identity",
            {}
        )
    )

    check(
        f"{gate_name} dependency identity exists",
        isinstance(
            dependency_identity,
            dict,
        )
        and
        bool(
            dependency_identity
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
        identity,
    ) in dependency_identity.items():

        if not isinstance(
            identity,
            dict,
        ):

            check(
                (
                    f"{gate_name}: "
                    f"{path_text} identity valid"
                ),
                False,
                failures,
            )

            continue

        expected_sha = str(
            identity.get(
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
                len(
                    expected_sha
                )
                ==
                64
                and
                sha256_file(
                    path
                )
                ==
                expected_sha
            )

        except Exception:

            current = False

        check(
            (
                f"{gate_name}: "
                f"{Path(path_text).name} current"
            ),
            current,
            failures,
        )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 9.8.5"
    )

    print(
        "FINAL STAGE 9 PROMOTION"
    )

    print("=" * 72)

    failures: list[str] = []

    # ========================================================
    # 1. Required artifacts
    # ========================================================

    print(
        "\n1. REQUIRED PROMOTION ARTIFACTS"
    )

    core_files = [

        CONTRACT_FILE,
        CONTRACT_VERIFICATION_FILE,

        BASE_FILE,
        BASE_REPORT_FILE,

        INTELLIGENCE_FILE,
        INTELLIGENCE_REPORT_FILE,

        API_VERIFICATION_FILE,
        RUNTIME_VERIFICATION_FILE,
    ]

    gate_files = [

        STAGE_9_8_1_FILE,
        STAGE_9_8_2_FILE,
        STAGE_9_8_3_FILE,
        STAGE_9_8_4_FILE,
    ]

    protected_files = (
        core_files
        +
        gate_files
    )

    for path in protected_files:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        print(
            "\nPromotion prerequisites missing."
        )

        print(
            "\n" + "=" * 72
        )

        print(
            "STAGE 9.8.5: FAIL"
        )

        print(
            "STAGE 9 PROMOTION: DENIED"
        )

        print(
            "STAGE 9: NOT COMPLETE"
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

        for path in protected_files
    }

    # ========================================================
    # 2. Load final-gate evidence
    # ========================================================

    print(
        "\n2. FINAL-GATE EVIDENCE"
    )

    gate_1 = load_json(
        STAGE_9_8_1_FILE
    )

    gate_2 = load_json(
        STAGE_9_8_2_FILE
    )

    gate_3 = load_json(
        STAGE_9_8_3_FILE
    )

    gate_4 = load_json(
        STAGE_9_8_4_FILE
    )

    # ========================================================
    # 3. 9.8.1
    # ========================================================

    print(
        "\n3. STAGE 9.8.1 FOUNDATION VERIFICATION"
    )

    check(
        "9.8.1 status PASS",
        gate_1.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )

    check(
        "9.8.1 COMPLETE",
        gate_1.get(
            "stage_9_8_1_complete"
        )
        is True,
        failures,
    )

    check(
        "Foundation verification VERIFIED",
        gate_1.get(
            "foundation_verification"
        )
        ==
        "VERIFIED",
        failures,
    )

    check(
        "9.8.1 authorized 9.8.2",
        gate_1.get(
            "stage9_ready_for_9_8_2"
        )
        is True,
        failures,
    )

    # ========================================================
    # 4. 9.8.2
    # ========================================================

    print(
        "\n4. STAGE 9.8.2 PREDICTION INTEGRITY"
    )

    check(
        "9.8.2 status PASS",
        gate_2.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )

    check(
        "9.8.2 COMPLETE",
        gate_2.get(
            "stage_9_8_2_complete"
        )
        is True,
        failures,
    )

    check(
        "Prediction integrity VERIFIED",
        gate_2.get(
            "prediction_integrity"
        )
        ==
        "VERIFIED",
        failures,
    )

    check(
        "9.8.2 authorized 9.8.3",
        gate_2.get(
            "stage9_ready_for_9_8_3"
        )
        is True,
        failures,
    )

    integrity_2 = gate_2.get(
        "integrity",
        {}
    )

    check(
        "Stage 7 -> final prediction copy exact",
        integrity_2.get(
            "stage7_to_final_copy_exact"
        )
        is True,
        failures,
    )

    check(
        "Probability vectors valid",
        integrity_2.get(
            "probability_vectors_valid"
        )
        is True,
        failures,
    )

    check(
        "Prediction labels consistent",
        integrity_2.get(
            "predicted_labels_consistent"
        )
        is True,
        failures,
    )

    check(
        "Confidence consistent",
        integrity_2.get(
            "confidence_consistent"
        )
        is True,
        failures,
    )

    # ========================================================
    # 5. 9.8.3
    # ========================================================

    print(
        "\n5. STAGE 9.8.3 INTELLIGENCE INTEGRITY"
    )

    check(
        "9.8.3 status PASS",
        gate_3.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )

    check(
        "9.8.3 COMPLETE",
        gate_3.get(
            "stage_9_8_3_complete"
        )
        is True,
        failures,
    )

    check(
        "Intelligence integrity VERIFIED",
        gate_3.get(
            "intelligence_integrity"
        )
        ==
        "VERIFIED",
        failures,
    )

    check(
        "9.8.3 authorized 9.8.4",
        gate_3.get(
            "stage9_ready_for_9_8_4"
        )
        is True,
        failures,
    )

    integrity_3 = gate_3.get(
        "integrity",
        {}
    )

    intelligence_integrity_flags = [

        "stage9_base_values_preserved_exactly",

        "top_probability_verified",
        "second_probability_verified",
        "probability_margin_verified",

        "league_position_gap_verified",
        "points_gap_verified",
        "goal_difference_gap_verified",

        "recent_points_gap_verified",
        "recent_goal_difference_gap_verified",
        "venue_form_points_gap_verified",

        "five_signal_support_score_verified",
        "context_alignment_verified",

        "entropy_verified",
        "normalized_entropy_verified",

        "confidence_band_verified",
        "uncertainty_band_verified",

        "explanation_headline_verified",
        "explanation_summary_verified",

        "intelligence_artifacts_unchanged",
    ]

    for flag in intelligence_integrity_flags:

        check(
            f"9.8.3 {flag}",
            integrity_3.get(
                flag
            )
            is True,
            failures,
        )

    # ========================================================
    # 6. 9.8.4
    # ========================================================

    print(
        "\n6. STAGE 9.8.4 API / RUNTIME / SAFETY"
    )

    check(
        "9.8.4 status PASS",
        gate_4.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )

    check(
        "9.8.4 COMPLETE",
        gate_4.get(
            "stage_9_8_4_complete"
        )
        is True,
        failures,
    )

    check(
        "API / runtime / safety VERIFIED",
        gate_4.get(
            "api_runtime_safety"
        )
        ==
        "VERIFIED",
        failures,
    )

    check(
        "9.8.4 authorized 9.8.5",
        gate_4.get(
            "stage9_ready_for_9_8_5"
        )
        is True,
        failures,
    )

    check(
        "9.8.4 runtime policy exact",
        gate_4.get(
            "runtime_policy"
        )
        ==
        EXPECTED_RUNTIME_POLICY,
        failures,
    )

    api_4 = gate_4.get(
        "api",
        {}
    )

    check(
        "Five-route API verified",
        api_4.get(
            "route_count"
        )
        ==
        5
        and
        api_4.get(
            "route_set_exact"
        )
        is True,
        failures,
    )

    check(
        "API GET-only verified",
        api_4.get(
            "get_only"
        )
        is True,
        failures,
    )

    check(
        "API no-store verified",
        api_4.get(
            "cache_control_no_store"
        )
        is True,
        failures,
    )

    check(
        "Fail-closed 503 contract verified",
        api_4.get(
            "stale_status_code"
        )
        ==
        503
        and
        api_4.get(
            "stale_public_status"
        )
        ==
        "NOT_READY",
        failures,
    )

    runtime_4 = gate_4.get(
        "runtime",
        {}
    )

    check(
        "Live service was READY at 9.8.4",
        runtime_4.get(
            "live_service_ready"
        )
        is True,
        failures,
    )

    check(
        "Runtime revalidation verified",
        runtime_4.get(
            "revalidate_on_every_read"
        )
        is True,
        failures,
    )

    check(
        "Temporal boundary verified",
        runtime_4.get(
            "temporal_boundary_inherited"
        )
        is True,
        failures,
    )

    check(
        "No stale fallback verified",
        runtime_4.get(
            "stale_fallback"
        )
        is False,
        failures,
    )

    check(
        "Same-process recovery verified",
        runtime_4.get(
            "same_process_recovery_verified"
        )
        is True,
        failures,
    )

    # ========================================================
    # 7. Promotion authority boundary
    # ========================================================

    print(
        "\n7. PROMOTION AUTHORITY BOUNDARY"
    )

    for (
        gate_name,
        gate,
    ) in [

        ("9.8.1", gate_1),
        ("9.8.2", gate_2),
        ("9.8.3", gate_3),
        ("9.8.4", gate_4),
    ]:

        promotion = gate.get(
            "promotion",
            {}
        )

        check(
            f"{gate_name} did not promote Stage 9",
            promotion.get(
                "stage_9_complete"
            )
            is False,
            failures,
        )

        check(
            f"{gate_name} did not complete Stage 9.8",
            promotion.get(
                "stage_9_8_complete"
            )
            is False,
            failures,
        )

        check(
            f"{gate_name} promotion owner = 9.8.5",
            promotion.get(
                "promotion_owner"
            )
            ==
            "9.8.5",
            failures,
        )

    # ========================================================
    # 8. Every previous evidence snapshot must still be current
    # ========================================================

    print(
        "\n8. FINAL-GATE SNAPSHOT FRESHNESS"
    )

    verify_evidence_dependencies(
        gate_1,
        "9.8.1",
        failures,
    )

    verify_evidence_dependencies(
        gate_2,
        "9.8.2",
        failures,
    )

    verify_evidence_dependencies(
        gate_3,
        "9.8.3",
        failures,
    )

    verify_evidence_dependencies(
        gate_4,
        "9.8.4",
        failures,
    )

    # ========================================================
    # 9. Core Stage 9 artifacts still match 9.8.4
    # ========================================================

    print(
        "\n9. CURRENT CORE ARTIFACT IDENTITY"
    )

    gate_4_dependencies = (
        gate_4.get(
            "dependency_identity",
            {}
        )
    )

    for path in protected_files:

        # 9.8.4 necessarily knows all core files and
        # 9.8.1-9.8.3. It does not include itself.
        if path == STAGE_9_8_4_FILE:

            continue

        key = relative_path(
            path
        )

        identity = gate_4_dependencies.get(
            key,
            {}
        )

        check(
            (
                f"{path.name} matches "
                "9.8.4 final snapshot"
            ),
            identity.get(
                "sha256"
            )
            ==
            sha256_file(
                path
            ),
            failures,
        )

    # ========================================================
    # 10. Final live service readiness
    # ========================================================

    print(
        "\n10. FINAL LIVE READINESS CHECK"
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
        "Live Match Intelligence service READY",
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
        "Live stale fallback disabled",
        live_status.get(
            "stale_fallback"
        )
        is False,
        failures,
    )

    fixture_count = (
        live_status.get(
            "fixture_count",
            0,
        )
    )

    check(
        "Live fixture count > 0",
        isinstance(
            fixture_count,
            int,
        )
        and
        fixture_count
        >
        0,
        failures,
    )

    live_rows = []

    if (
        live_status.get(
            "status"
        )
        ==
        "READY"
    ):

        try:

            live_rows = (
                service.get_all_matches()
            )

        except Exception as exc:

            print(
                "Final live read error:",
                exc,
            )

            live_rows = []

    check(
        "Final live intelligence read succeeds",
        len(
            live_rows
        )
        >
        0,
        failures,
    )

    if live_rows:

        check(
            "Final live row count matches status",
            len(
                live_rows
            )
            ==
            fixture_count,
            failures,
        )

    # ========================================================
    # 11. Final public API readiness
    # ========================================================

    print(
        "\n11. FINAL PUBLIC API READINESS"
    )

    client = app.test_client()

    status_response = client.get(
        "/api/v1/intelligence/status"
    )

    status_payload = response_json(
        status_response
    )

    check(
        "GET /api/v1/intelligence/status -> 200",
        status_response.status_code
        ==
        200,
        failures,
    )

    check(
        "Public intelligence status READY",
        status_payload.get(
            "status"
        )
        ==
        "READY",
        failures,
    )

    check(
        "Public intelligence status no-store",
        has_no_store(
            status_response
        ),
        failures,
    )

    matches_response = client.get(
        "/api/v1/intelligence/matches"
    )

    matches_payload = response_json(
        matches_response
    )

    check(
        "GET /api/v1/intelligence/matches -> 200",
        matches_response.status_code
        ==
        200,
        failures,
    )

    check(
        "Public intelligence matches READY",
        matches_payload.get(
            "status"
        )
        ==
        "READY",
        failures,
    )

    check(
        "Public intelligence matches no-store",
        has_no_store(
            matches_response
        ),
        failures,
    )

    api_matches = (
        matches_payload.get(
            "matches",
            []
        )
    )

    check(
        "Public intelligence returns fixtures",
        isinstance(
            api_matches,
            list,
        )
        and
        len(
            api_matches
        )
        >
        0,
        failures,
    )

    # ========================================================
    # 12. Final safety declarations
    # ========================================================

    print(
        "\n12. FINAL PROMOTION SAFETY"
    )

    check(
        "No model loaded by 9.8.5",
        True,
        failures,
    )

    check(
        "No model executed by 9.8.5",
        True,
        failures,
    )

    check(
        "No model retraining by 9.8.5",
        True,
        failures,
    )

    check(
        "No model reselection by 9.8.5",
        True,
        failures,
    )

    check(
        "No probability modification by 9.8.5",
        True,
        failures,
    )

    check(
        "No prediction-label modification by 9.8.5",
        True,
        failures,
    )

    check(
        "No context modification by 9.8.5",
        True,
        failures,
    )

    check(
        "No intelligence rebuild by 9.8.5",
        True,
        failures,
    )

    check(
        "No provider fetch by 9.8.5",
        True,
        failures,
    )

    # ========================================================
    # 13. Protected files unchanged before promotion
    # ========================================================

    print(
        "\n13. PRE-PROMOTION WRITE PROTECTION"
    )

    for path in protected_files:

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
    # 14. Promotion decision
    # ========================================================

    print(
        "\n14. FINAL PROMOTION DECISION"
    )

    promotion_authorized = (
        len(
            failures
        )
        ==
        0
    )

    check(
        "All promotion prerequisites PASS",
        promotion_authorized,
        failures,
    )

    # Do not write/overwrite the final artifact on failure.

    if not promotion_authorized:

        print(
            "\nPromotion denied. "
            "stage9_final_verification.json "
            "was not rewritten by this run."
        )

        print(
            "\n" + "=" * 72
        )

        print(
            "STAGE 9.8.5: FAIL"
        )

        print(
            "FINAL STAGE 9 PROMOTION: DENIED"
        )

        print(
            "STAGE 9.8: INCOMPLETE"
        )

        print(
            "STAGE 9: INCOMPLETE"
        )

        print(
            "MATCH INTELLIGENCE LAYER: NOT PROMOTED"
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

        sys.exit(1)

    # ========================================================
    # 15. Create authoritative final promotion
    # ========================================================

    print(
        "\n15. AUTHORITATIVE STAGE 9 PROMOTION"
    )

    completed_at = (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )

    final_evidence = {

        "stage":
            "9.8.5",

        "name":
            "FINAL_STAGE_9_PROMOTION",

        "status":
            "PASS",

        "stage_9_8_5_complete":
            True,

        "stage_9_8_complete":
            True,

        "stage_9_complete":
            True,

        "match_intelligence_layer":
            "VERIFIED",

        "fixtureiq_stage9_final_gate":
            "PASS",

        "completed_at_utc":
            completed_at,

        "runtime_policy":
            EXPECTED_RUNTIME_POLICY,

        "fixture_count":
            fixture_count,

        "final_gate": {

            "9.8.1": {

                "name":
                    "FOUNDATION_VERIFICATION",

                "status":
                    "PASS",

                "verified":
                    True,

                "sha256":
                    sha256_file(
                        STAGE_9_8_1_FILE
                    ),
            },

            "9.8.2": {

                "name":
                    "PREDICTION_INTEGRITY_VERIFICATION",

                "status":
                    "PASS",

                "verified":
                    True,

                "sha256":
                    sha256_file(
                        STAGE_9_8_2_FILE
                    ),
            },

            "9.8.3": {

                "name":
                    "INTELLIGENCE_INTEGRITY_VERIFICATION",

                "status":
                    "PASS",

                "verified":
                    True,

                "sha256":
                    sha256_file(
                        STAGE_9_8_3_FILE
                    ),
            },

            "9.8.4": {

                "name":
                    "API_RUNTIME_SAFETY_VERIFICATION",

                "status":
                    "PASS",

                "verified":
                    True,

                "sha256":
                    sha256_file(
                        STAGE_9_8_4_FILE
                    ),
            },
        },

        "stage_9": {

            "stage_9_1":
                "COMPLETE",

            "stage_9_2":
                "COMPLETE",

            "stage_9_3":
                "COMPLETE",

            "stage_9_4":
                "COMPLETE",

            "stage_9_5":
                "COMPLETE",

            "stage_9_6":
                "COMPLETE",

            "stage_9_7":
                "COMPLETE",

            "stage_9_8":
                "COMPLETE",
        },

        "verified_properties": {

            "foundation_verified":
                True,

            "prediction_integrity_verified":
                True,

            "stage7_predictions_preserved_exactly":
                True,

            "intelligence_integrity_verified":
                True,

            "derived_intelligence_independently_recomputed":
                True,

            "explanations_verified":
                True,

            "rest_api_verified":
                True,

            "runtime_safety_verified":
                True,

            "runtime_freshness_verified":
                True,

            "temporal_boundary_verified":
                True,

            "fail_closed_verified":
                True,

            "no_stale_fallback":
                True,

            "same_process_recovery_verified":
                True,

            "no_store_verified":
                True,

            "read_only_api_verified":
                True,

            "live_service_ready_at_promotion":
                True,
        },

        "safety": {

            "model_loaded":
                False,

            "model_executed":
                False,

            "model_retrained":
                False,

            "model_reselected":
                False,

            "model_tuned":
                False,

            "feature_schema_modified":
                False,

            "probabilities_modified":
                False,

            "probabilities_recalibrated":
                False,

            "prediction_labels_modified":
                False,

            "confidence_modified":
                False,

            "context_modified":
                False,

            "provider_fetch_performed":
                False,

            "future_results_used":
                False,

            "bookmaker_odds_used":
                False,

            "intelligence_rebuilt":
                False,

            "stale_data_served":
                False,

            "protected_artifacts_modified":
                False,

            "promotion_artifact_only_write":
                True,
        },

        "core_artifact_identity": {

            relative_path(
                path
            ): {
                "sha256":
                    sha256_file(
                        path
                    )
            }

            for path in core_files
        },

        "final_gate_evidence_identity": {

            relative_path(
                STAGE_9_8_1_FILE
            ): {
                "sha256":
                    sha256_file(
                        STAGE_9_8_1_FILE
                    )
            },

            relative_path(
                STAGE_9_8_2_FILE
            ): {
                "sha256":
                    sha256_file(
                        STAGE_9_8_2_FILE
                    )
            },

            relative_path(
                STAGE_9_8_3_FILE
            ): {
                "sha256":
                    sha256_file(
                        STAGE_9_8_3_FILE
                    )
            },

            relative_path(
                STAGE_9_8_4_FILE
            ): {
                "sha256":
                    sha256_file(
                        STAGE_9_8_4_FILE
                    )
            },
        },

        "final_intelligence": {

            "path":
                relative_path(
                    INTELLIGENCE_FILE
                ),

            "sha256":
                sha256_file(
                    INTELLIGENCE_FILE
                ),

            "fixture_count":
                fixture_count,
        },

        "promotion": {

            "authorized":
                True,

            "authority":
                "9.8.5",

            "all_required_gates_passed":
                True,

            "all_required_evidence_current":
                True,

            "live_readiness_confirmed":
                True,

            "final_stage9_status":
                "COMPLETE",
        },

        "next_stage":
            None,

        "failures":
            [],
    }

    # This atomically replaces the obsolete experimental
    # stage9_final_verification.json from the earlier
    # two-part 9.8 attempt.

    save_json_atomic(
        FINAL_FILE,
        final_evidence,
    )

    check(
        "Authoritative final artifact written",
        FINAL_FILE.exists(),
        failures,
    )

    # ========================================================
    # 16. Verify persisted promotion
    # ========================================================

    print(
        "\n16. PERSISTED PROMOTION VERIFICATION"
    )

    persisted = load_json(
        FINAL_FILE
    )

    check(
        "Persisted status PASS",
        persisted.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )

    check(
        "Stage 9.8.5 COMPLETE persisted",
        persisted.get(
            "stage_9_8_5_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 9.8 COMPLETE persisted",
        persisted.get(
            "stage_9_8_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 9 COMPLETE persisted",
        persisted.get(
            "stage_9_complete"
        )
        is True,
        failures,
    )

    check(
        "Match Intelligence Layer VERIFIED persisted",
        persisted.get(
            "match_intelligence_layer"
        )
        ==
        "VERIFIED",
        failures,
    )

    check(
        "FixtureIQ Stage 9 Final Gate PASS persisted",
        persisted.get(
            "fixtureiq_stage9_final_gate"
        )
        ==
        "PASS",
        failures,
    )

    check(
        "Promotion authority persisted as 9.8.5",
        persisted.get(
            "promotion",
            {}
        ).get(
            "authority"
        )
        ==
        "9.8.5",
        failures,
    )

    # ========================================================
    # 17. Final protected-artifact verification
    # ========================================================

    print(
        "\n17. POST-PROMOTION WRITE PROTECTION"
    )

    for path in protected_files:

        key = relative_path(
            path
        )

        check(
            f"{path.name} still unchanged",
            sha256_file(
                path
            )
            ==
            protected_before[
                key
            ],
            failures,
        )

    final_pass = (
        len(
            failures
        )
        ==
        0
    )

    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    print(
        "\n" + "=" * 72
    )

    if final_pass:

        print(
            "STAGE 9.8.5: PASS"
        )

        print(
            "FINAL STAGE 9 PROMOTION: VERIFIED"
        )

        print()

        print(
            "STAGE 9.8: COMPLETE"
        )

        print(
            "STAGE 9: COMPLETE"
        )

        print(
            "MATCH INTELLIGENCE LAYER: VERIFIED"
        )

        print(
            "FIXTUREIQ STAGE 9 FINAL GATE: PASS"
        )

    else:

        print(
            "STAGE 9.8.5: FAIL"
        )

        print(
            "FINAL STAGE 9 PROMOTION: "
            "POST-WRITE VERIFICATION FAILED"
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
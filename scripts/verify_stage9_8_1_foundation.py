"""
FixtureIQ Stage 9.8.1
FOUNDATION VERIFICATION

Purpose
-------
Verify that the complete Stage 9 foundation exists, remains internally
consistent, and is current before prediction-integrity verification begins.

This gate DOES NOT:
- recalculate predictions
- validate prediction semantics
- validate derived intelligence semantics
- rebuild artifacts
- fetch provider data
- load or execute the prediction model
- promote Stage 9 to COMPLETE

Only Stage 9.8.5 may perform final Stage 9 promotion.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# Project paths
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

OUTPUT_FILE = (
    INTELLIGENCE_DIR
    / "stage9_8_1_foundation_verification.json"
)


# ============================================================
# Locked Stage 9.1 input set
# ============================================================

EXPECTED_DYNAMIC_INPUTS = {

    "production_predictions",
    "production_prediction_metadata",
    "production_prediction_report",
    "production_prediction_verification",

    "stage7_8_final_verification",
    "stage7_9_final_verification",

    "enriched_upcoming_fixtures",
    "fixture_context_report",
    "context_api_verification",
    "context_runtime_verification",
    "stage8_final_verification",
}


EXPECTED_STAGE9_2_DEPENDENCIES = (
    EXPECTED_DYNAMIC_INPUTS
    |
    {
        "stage9_intelligence_contract",
        "stage9_intelligence_contract_verification",
    }
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

        payload = json.load(file)

    if not isinstance(
        payload,
        dict,
    ):

        raise RuntimeError(
            f"Expected JSON object: {path}"
        )

    return payload


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
                f"{value}"
            )
        ) from exc

    return resolved


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

        failures.append(
            label
        )

    return passed


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 9.8.1"
    )

    print(
        "FOUNDATION VERIFICATION"
    )

    print("=" * 72)

    failures: list[str] = []

    # ========================================================
    # 1. Required artifacts
    # ========================================================

    print(
        "\n1. REQUIRED STAGE 9 FOUNDATION ARTIFACTS"
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
    ]

    for path in required_files:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        print(
            "\nRequired foundation artifacts missing."
        )

        print("=" * 72)

        print(
            "STAGE 9.8.1: FAIL"
        )

        print(
            "FOUNDATION VERIFICATION: NOT VERIFIED"
        )

        print("=" * 72)

        sys.exit(1)

    # Record current protected identities before validation.

    protected_before = {

        relative_path(path):
            sha256_file(path)

        for path in required_files
    }

    # ========================================================
    # Load artifacts
    # ========================================================

    contract = load_json(
        CONTRACT_FILE
    )

    contract_verification = load_json(
        CONTRACT_VERIFICATION_FILE
    )

    base_report = load_json(
        BASE_REPORT_FILE
    )

    intelligence_report = load_json(
        INTELLIGENCE_REPORT_FILE
    )

    api_verification = load_json(
        API_VERIFICATION_FILE
    )

    runtime_verification = load_json(
        RUNTIME_VERIFICATION_FILE
    )

    # ========================================================
    # 2. Stage 9.1 contract foundation
    # ========================================================

    print(
        "\n2. STAGE 9.1 CONTRACT FOUNDATION"
    )

    check(
        "Stage 9.1 contract LOCKED",
        contract.get(
            "status"
        )
        ==
        "LOCKED_MATCH_INTELLIGENCE_CONTRACT",
        failures,
    )

    check(
        "Stage 9.1 COMPLETE",
        contract.get(
            "stage_9_1_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 9.1 verification PASS",
        contract_verification.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )

    check(
        "Stage 9.1 contract SHA current",
        contract_verification.get(
            "contract_sha256"
        )
        ==
        sha256_file(
            CONTRACT_FILE
        ),
        failures,
    )

    allowed_inputs = (
        contract.get(
            "stage_9_1_1",
            {}
        ).get(
            "allowed_inputs",
            {}
        )
    )

    check(
        "Stage 9.1 allowed_inputs is object",
        isinstance(
            allowed_inputs,
            dict,
        ),
        failures,
    )

    if isinstance(
        allowed_inputs,
        dict,
    ):

        check(
            "Exactly 11 dynamic Stage 7/8 inputs",
            set(
                allowed_inputs.keys()
            )
            ==
            EXPECTED_DYNAMIC_INPUTS,
            failures,
        )

        for name in sorted(
            EXPECTED_DYNAMIC_INPUTS
        ):

            item = allowed_inputs.get(
                name,
                {}
            )

            check(
                (
                    f"{name}: downstream-build "
                    "snapshot policy"
                ),
                item.get(
                    "dependency_hash_policy"
                )
                ==
                "CAPTURE_AT_DOWNSTREAM_BUILD",
                failures,
            )

            check(
                (
                    f"{name}: no permanent "
                    "runtime hash pin"
                ),
                item.get(
                    "contract_runtime_hash_pin"
                )
                is False,
                failures,
            )

            check(
                (
                    f"{name}: downstream snapshot "
                    "hash required"
                ),
                item.get(
                    "downstream_snapshot_hash_required"
                )
                is True,
                failures,
            )

            check(
                (
                    f"{name}: runtime content "
                    "may change"
                ),
                item.get(
                    "runtime_content_may_change"
                )
                is True,
                failures,
            )

    # ========================================================
    # 3. Stage 9.2 join foundation
    # ========================================================

    print(
        "\n3. STAGE 9.2 PREDICTION-CONTEXT FOUNDATION"
    )

    check(
        "Stage 9.2 report PASS",
        base_report.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )

    check(
        "Stage 9.2 COMPLETE",
        base_report.get(
            "stage_9_2_complete"
        )
        is True,
        failures,
    )

    check(
        "Prediction-context join VERIFIED",
        base_report.get(
            "prediction_context_join_layer"
        )
        ==
        "VERIFIED",
        failures,
    )

    check(
        "Stage 9.2 base artifact SHA current",
        base_report.get(
            "base_artifact",
            {}
        ).get(
            "sha256"
        )
        ==
        sha256_file(
            BASE_FILE
        ),
        failures,
    )

    dependency_identity = (
        base_report.get(
            "dependency_identity",
            {}
        )
    )

    check(
        "Stage 9.2 dependency identity is object",
        isinstance(
            dependency_identity,
            dict,
        ),
        failures,
    )

    if isinstance(
        dependency_identity,
        dict,
    ):

        check(
            "Stage 9.2 dependency set exact",
            set(
                dependency_identity.keys()
            )
            ==
            EXPECTED_STAGE9_2_DEPENDENCIES,
            failures,
        )

        for name in sorted(
            EXPECTED_STAGE9_2_DEPENDENCIES
        ):

            item = dependency_identity.get(
                name,
                {}
            )

            path_value = str(
                item.get(
                    "path",
                    "",
                )
            ).strip()

            expected_sha = str(
                item.get(
                    "sha256",
                    "",
                )
            ).strip()

            path_ok = bool(
                path_value
            )

            check(
                f"{name}: dependency path recorded",
                path_ok,
                failures,
            )

            check(
                f"{name}: dependency SHA recorded",
                len(
                    expected_sha
                )
                ==
                64,
                failures,
            )

            if (
                path_ok
                and
                len(
                    expected_sha
                )
                ==
                64
            ):

                try:

                    dependency_path = (
                        resolve_project_path(
                            path_value
                        )
                    )

                    current_sha = (
                        sha256_file(
                            dependency_path
                        )
                    )

                    current = (
                        current_sha
                        ==
                        expected_sha
                    )

                except Exception:

                    current = False

                check(
                    f"{name}: current snapshot matches",
                    current,
                    failures,
                )

    # ========================================================
    # 4. Stage 9.3 / 9.4 / 9.5 foundation
    # ========================================================

    print(
        "\n4. STAGE 9.3 - 9.5 INTELLIGENCE FOUNDATION"
    )

    check(
        "Match intelligence report PASS",
        intelligence_report.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )

    check(
        "Stage 9.3 COMPLETE",
        intelligence_report.get(
            "stage_9_3_complete"
        )
        is True,
        failures,
    )

    check(
        "Derived match intelligence VERIFIED",
        intelligence_report.get(
            "derived_match_intelligence"
        )
        ==
        "VERIFIED",
        failures,
    )

    check(
        "Stage 9.4 COMPLETE",
        intelligence_report.get(
            "stage_9_4_complete"
        )
        is True,
        failures,
    )

    check(
        "Confidence / uncertainty VERIFIED",
        intelligence_report.get(
            "confidence_uncertainty_layer"
        )
        ==
        "VERIFIED",
        failures,
    )

    check(
        "Stage 9.5 COMPLETE",
        intelligence_report.get(
            "stage_9_5_complete"
        )
        is True,
        failures,
    )

    check(
        "Explanation engine VERIFIED",
        intelligence_report.get(
            "match_explanation_engine"
        )
        ==
        "VERIFIED",
        failures,
    )

    check(
        "Final intelligence artifact SHA current",
        intelligence_report.get(
            "output_artifact",
            {}
        ).get(
            "sha256"
        )
        ==
        sha256_file(
            INTELLIGENCE_FILE
        ),
        failures,
    )

    # ========================================================
    # 5. Stage 9.6 API foundation
    # ========================================================

    print(
        "\n5. STAGE 9.6 API FOUNDATION"
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
        "Stage 9.6 authorized Stage 9.7",
        api_verification.get(
            "stage9_ready_for_9_7"
        )
        is True,
        failures,
    )

    # ========================================================
    # 6. Stage 9.7 runtime foundation
    # ========================================================

    print(
        "\n6. STAGE 9.7 RUNTIME FOUNDATION"
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
        "Runtime policy locked",
        runtime_verification.get(
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
        "Stage 9.7 authorized Stage 9.8",
        runtime_verification.get(
            "stage9_ready_for_9_8"
        )
        is True,
        failures,
    )

    # ========================================================
    # 7. Stage 9.7 recorded identities
    # ========================================================

    print(
        "\n7. STAGE 9.7 FOUNDATION IDENTITY"
    )

    runtime_dependencies = (
        runtime_verification.get(
            "dependency_identity",
            {}
        )
    )

    expected_runtime_identity = {

        "stage9_intelligence_contract":
            CONTRACT_FILE,

        "stage9_intelligence_contract_verification":
            CONTRACT_VERIFICATION_FILE,

        "match_intelligence_base":
            BASE_FILE,

        "match_intelligence_base_report":
            BASE_REPORT_FILE,

        "match_intelligence":
            INTELLIGENCE_FILE,

        "match_intelligence_report":
            INTELLIGENCE_REPORT_FILE,

        "intelligence_api_verification":
            API_VERIFICATION_FILE,
    }

    check(
        "Stage 9.7 dependency identity is object",
        isinstance(
            runtime_dependencies,
            dict,
        ),
        failures,
    )

    if isinstance(
        runtime_dependencies,
        dict,
    ):

        for name, path in (
            expected_runtime_identity.items()
        ):

            item = runtime_dependencies.get(
                name,
                {}
            )

            check(
                f"{name}: Stage 9.7 SHA current",
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
    # 8. No premature promotion authority
    # ========================================================

    print(
        "\n8. FINAL-PROMOTION BOUNDARY"
    )

    check(
        "9.8.1 does not promote Stage 9",
        True,
        failures,
    )

    check(
        "Final promotion reserved for 9.8.5",
        True,
        failures,
    )

    # ========================================================
    # 9. Foundation write protection
    # ========================================================

    print(
        "\n9. FOUNDATION WRITE PROTECTION"
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
    # 10. Save 9.8.1 evidence
    # ========================================================

    print(
        "\n10. SAVE STAGE 9.8.1 EVIDENCE"
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
                "9.8.1",

            "name":
                "FOUNDATION_VERIFICATION",

            "status":
                "PASS",

            "stage_9_8_1_complete":
                True,

            "foundation_verification":
                "VERIFIED",

            "verified_at_utc":
                verified_at,

            "foundation": {

                "stage_9_1_contract_locked":
                    True,

                "stage_9_1_verification_current":
                    True,

                "dynamic_input_set_exact":
                    True,

                "dynamic_snapshot_policy_verified":
                    True,

                "stage_9_2_join_verified":
                    True,

                "stage_9_2_dependency_snapshot_current":
                    True,

                "stage_9_3_verified":
                    True,

                "stage_9_4_verified":
                    True,

                "stage_9_5_verified":
                    True,

                "stage_9_6_verified":
                    True,

                "stage_9_7_verified":
                    True,

                "foundation_artifacts_unchanged":
                    True,
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

            "dependency_identity": {

                relative_path(path): {
                    "sha256":
                        sha256_file(
                            path
                        )
                }

                for path in required_files
            },

            "stage9_ready_for_9_8_2":
                True,

            "next_stage":
                "9.8.2",

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

    print(
        "\n" + "=" * 72
    )

    if overall_pass:

        print(
            "STAGE 9.8.1: PASS"
        )

        print(
            "FOUNDATION VERIFICATION: VERIFIED"
        )

        print(
            "STAGE 9 READY FOR 9.8.2"
        )

        print()
        print(
            "STAGE 9 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 9.8.1: FAIL"
        )

        print(
            "FOUNDATION VERIFICATION: NOT VERIFIED"
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
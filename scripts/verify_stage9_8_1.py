"""
FixtureIQ Stage 9.8.1
Final Artifact / Provenance / Semantic Integrity Gate.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


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


from backend.services.stage9_final_validator import (
    Stage9FinalValidator,
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

REPORT_FILE = (
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

FINAL_FILE = (
    INTELLIGENCE_DIR
    / "stage9_final_verification.json"
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


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 9.8.1"
    )

    print(
        "FINAL ARTIFACT / PROVENANCE / SEMANTIC INTEGRITY"
    )

    print("=" * 72)

    failures = []

    # ========================================================
    # Required artifacts
    # ========================================================

    print(
        "\n1. REQUIRED STAGE 9 ARTIFACTS"
    )

    required = [

        CONTRACT_FILE,
        CONTRACT_VERIFICATION_FILE,

        BASE_FILE,
        BASE_REPORT_FILE,

        INTELLIGENCE_FILE,
        REPORT_FILE,

        API_VERIFICATION_FILE,
        RUNTIME_VERIFICATION_FILE,
    ]

    for path in required:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        sys.exit(1)

    protected_before = {

        relative_path(
            path
        ):
            sha256_file(
                path
            )

        for path in required
    }

    # ========================================================
    # Independent final validation
    # ========================================================

    print(
        "\n2. INDEPENDENT FULL-CHAIN VALIDATION"
    )

    try:

        result = (
            Stage9FinalValidator()
            .validate()
        )

        valid = (
            result.get(
                "status"
            )
            == "PASS"
        )

    except Exception as exc:

        print(
            "Final validation error:",
            exc,
        )

        result = {}
        valid = False

    check(
        "Independent Stage 9 artifact validation PASS",
        valid,
        failures,
    )

    if valid:

        flags = [

            "base_fixture_set_exact",
            "fixture_order_exact",
            "base_values_preserved_exactly",
            "probabilities_preserved",
            "derived_probability_metrics_exact",
            "entropy_exact",
            "confidence_bands_exact",
            "uncertainty_bands_exact",
            "context_score_range_valid",
            "context_alignment_valid",
            "explanations_complete",
            "dependency_chain_current",
        ]

        for flag in flags:

            check(
                f"{flag} = true",
                result.get(
                    flag
                )
                is True,
                failures,
            )

        check(
            "Fixture count > 0",
            result.get(
                "fixture_count",
                0,
            )
            > 0,
            failures,
        )

        check(
            "Base value comparisons > 0",
            result.get(
                "base_value_comparisons",
                0,
            )
            > 0,
            failures,
        )

        check(
            "Semantic fixture checks = fixture count",
            result.get(
                "semantic_fixture_checks"
            )
            ==
            result.get(
                "fixture_count"
            ),
            failures,
        )

    # ========================================================
    # Write protection
    # ========================================================

    print(
        "\n3. COMPLETE STAGE 9 WRITE PROTECTION"
    )

    for path in required:

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
    # Persist partial Stage 9.8 final gate
    # ========================================================

    print(
        "\n4. SAVE STAGE 9.8.1 EVIDENCE"
    )

    overall_pass = (
        len(
            failures
        )
        == 0
    )

    if overall_pass:

        verified_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        artifact = {

            "stage":
                "9.8",

            "status":
                "PARTIAL_PASS",

            "stage_9_8_complete":
                False,

            "stage_9_complete":
                False,

            "match_intelligence_layer":
                "PENDING_FINAL_RUNTIME_GATE",

            "fixtureiq_stage9_final_gate":
                "PENDING_9_8_2",

            "stage_9_8_1": {

                "status":
                    "PASS",

                "name":
                    (
                        "FINAL_ARTIFACT_PROVENANCE_"
                        "SEMANTIC_INTEGRITY"
                    ),

                "verified_at_utc":
                    verified_at,

                "fixture_count":
                    result[
                        "fixture_count"
                    ],

                "base_fixture_set_exact":
                    True,

                "fixture_order_exact":
                    True,

                "base_values_preserved_exactly":
                    True,

                "probabilities_preserved":
                    True,

                "derived_probability_metrics_exact":
                    True,

                "entropy_exact":
                    True,

                "confidence_bands_exact":
                    True,

                "uncertainty_bands_exact":
                    True,

                "context_score_range_valid":
                    True,

                "context_alignment_valid":
                    True,

                "explanations_complete":
                    True,

                "dependency_chain_current":
                    True,
            },

            "stage_9_8_2": {

                "status":
                    "PENDING",

                "name":
                    "FINAL_RUNTIME_API_SAFETY_GATE",
            },

            "dependency_identity": {

                relative_path(
                    path
                ):
                    sha256_file(
                        path
                    )

                for path in required
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
                    result[
                        "fixture_count"
                    ],

                "column_count":
                    result[
                        "final_column_count"
                    ],
            },

            "next_stage":
                "9.8.2",

            "failures":
                [],
        }

        save_json_atomic(
            FINAL_FILE,
            artifact,
        )

        print(
            FINAL_FILE
        )

    print(
        "\n" + "=" * 72
    )

    if overall_pass:

        print(
            "STAGE 9.8.1: PASS"
        )

        print(
            "FINAL ARTIFACT / PROVENANCE / "
            "SEMANTIC INTEGRITY: VERIFIED"
        )

        print(
            "STAGE 9 READY FOR 9.8.2"
        )

    else:

        print(
            "STAGE 9.8.1: FAIL"
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
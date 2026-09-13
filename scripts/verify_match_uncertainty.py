"""
FixtureIQ Stage 9.4
Independent Confidence & Uncertainty Verification.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


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


from backend.services.match_uncertainty_validator import (
    MatchUncertaintyValidationError,
    MatchUncertaintyValidator,
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


def tamper_uncertainty(
    source: Path,
    destination: Path,
) -> None:

    shutil.copy2(
        source,
        destination,
    )

    with destination.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        fields = list(
            reader.fieldnames
            or []
        )

        rows = list(
            reader
        )

    if not rows:

        raise RuntimeError(
            "Cannot tamper empty artifact."
        )

    original = rows[
        0
    ][
        "stage9_uncertainty_band"
    ]

    rows[
        0
    ][
        "stage9_uncertainty_band"
    ] = (
        "VERY_LOW"
        if original
        != "VERY_LOW"
        else
        "VERY_HIGH"
    )

    with destination.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields,
        )

        writer.writeheader()
        writer.writerows(
            rows
        )


def main() -> None:

    print("=" * 72)
    print("FixtureIQ Stage 9.4")
    print("INDEPENDENT CONFIDENCE & UNCERTAINTY VERIFICATION")
    print("=" * 72)

    failures = []

    required = [

        CONTRACT_FILE,
        CONTRACT_VERIFICATION_FILE,
        BASE_FILE,
        BASE_REPORT_FILE,
        INTELLIGENCE_FILE,
        REPORT_FILE,
    ]

    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    for path in required:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        sys.exit(1)

    # ========================================================
    # Protection snapshot
    # ========================================================

    protected = {

        "contract":
            sha256_file(
                CONTRACT_FILE
            ),

        "contract_verification":
            sha256_file(
                CONTRACT_VERIFICATION_FILE
            ),

        "base":
            sha256_file(
                BASE_FILE
            ),

        "base_report":
            sha256_file(
                BASE_REPORT_FILE
            ),

        "intelligence":
            sha256_file(
                INTELLIGENCE_FILE
            ),
    }

    # ========================================================
    # Independent verification
    # ========================================================

    print(
        "\n2. INDEPENDENT RECONSTRUCTION"
    )

    try:

        result = (
            MatchUncertaintyValidator()
            .validate()
        )

        validation_ok = (
            result.get(
                "status"
            )
            == "PASS"
        )

    except Exception as exc:

        print(
            "Validation error:",
            exc,
        )

        result = {}
        validation_ok = False

    check(
        "Independent Stage 9.4 validation PASS",
        validation_ok,
        failures,
    )

    if validation_ok:

        flags = [

            "schema_exact",
            "fixture_sets_exact",
            "stage9_2_values_exact",
            "stage9_3_values_preserved",
            "entropy_exact",
            "normalized_entropy_exact",
            "confidence_bands_exact",
            "uncertainty_bands_exact",
            "stage9_5_fields_blank",
            "dependency_identity_current",
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
            "Stage 9.4 comparisons = fixture count x 4",
            result.get(
                "stage9_4_value_comparisons"
            )
            ==
            (
                result.get(
                    "fixture_count"
                )
                * 4
            ),
            failures,
        )

    # ========================================================
    # Threshold contract
    # ========================================================

    print(
        "\n3. FIXED THRESHOLD CONTRACT"
    )

    report = load_json(
        REPORT_FILE
    )

    confidence_rule = report.get(
        "confidence_band_rule",
        {}
    )

    uncertainty_rule = report.get(
        "uncertainty_band_rule",
        {}
    )

    check(
        "Confidence source = stage7_confidence",
        confidence_rule.get(
            "source"
        )
        == "stage7_confidence",
        failures,
    )

    check(
        "Confidence VERY_LOW threshold exact",
        confidence_rule.get(
            "VERY_LOW"
        )
        == "[0.00, 0.40)",
        failures,
    )

    check(
        "Confidence LOW threshold exact",
        confidence_rule.get(
            "LOW"
        )
        == "[0.40, 0.50)",
        failures,
    )

    check(
        "Confidence MODERATE threshold exact",
        confidence_rule.get(
            "MODERATE"
        )
        == "[0.50, 0.60)",
        failures,
    )

    check(
        "Confidence HIGH threshold exact",
        confidence_rule.get(
            "HIGH"
        )
        == "[0.60, 0.70)",
        failures,
    )

    check(
        "Confidence VERY_HIGH threshold exact",
        confidence_rule.get(
            "VERY_HIGH"
        )
        == "[0.70, 1.00]",
        failures,
    )

    check(
        "Confidence thresholds not outcome tuned",
        confidence_rule.get(
            "outcome_tuning_used"
        )
        is False,
        failures,
    )

    check(
        "Uncertainty source normalized entropy",
        uncertainty_rule.get(
            "source"
        )
        ==
        "stage9_normalized_entropy",
        failures,
    )

    check(
        "Uncertainty VERY_LOW threshold exact",
        uncertainty_rule.get(
            "VERY_LOW"
        )
        == "[0.00, 0.20)",
        failures,
    )

    check(
        "Uncertainty LOW threshold exact",
        uncertainty_rule.get(
            "LOW"
        )
        == "[0.20, 0.40)",
        failures,
    )

    check(
        "Uncertainty MODERATE threshold exact",
        uncertainty_rule.get(
            "MODERATE"
        )
        == "[0.40, 0.60)",
        failures,
    )

    check(
        "Uncertainty HIGH threshold exact",
        uncertainty_rule.get(
            "HIGH"
        )
        == "[0.60, 0.80)",
        failures,
    )

    check(
        "Uncertainty VERY_HIGH threshold exact",
        uncertainty_rule.get(
            "VERY_HIGH"
        )
        == "[0.80, 1.00]",
        failures,
    )

    check(
        "Uncertainty thresholds not outcome tuned",
        uncertainty_rule.get(
            "outcome_tuning_used"
        )
        is False,
        failures,
    )

    # ========================================================
    # Negative tamper test
    # ========================================================

    print(
        "\n4. NEGATIVE TEST - UNCERTAINTY TAMPER"
    )

    with tempfile.TemporaryDirectory() as temp_dir:

        tampered_file = (
            Path(
                temp_dir
            )
            / "match_intelligence.csv"
        )

        tamper_uncertainty(
            INTELLIGENCE_FILE,
            tampered_file,
        )

        tamper_rejected = False

        try:

            MatchUncertaintyValidator(
                intelligence_file=
                    tampered_file,
            ).validate()

        except MatchUncertaintyValidationError:

            tamper_rejected = True

        except Exception:

            tamper_rejected = True

        check(
            "Tampered uncertainty value rejected",
            tamper_rejected,
            failures,
        )

    # ========================================================
    # Safety
    # ========================================================

    print(
        "\n5. SAFETY"
    )

    safety = report.get(
        "safety",
        {}
    )

    check(
        "Interpretation only",
        safety.get(
            "interpretation_only"
        )
        is True,
        failures,
    )

    false_flags = [

        "model_loaded",
        "model_executed",
        "model_modified",
        "probabilities_modified",
        "probabilities_recalibrated",
        "prediction_labels_modified",
        "source_confidence_modified",
        "stage7_artifacts_modified",
        "stage8_artifacts_modified",
        "stage9_2_artifacts_modified",
        "stage9_3_context_fields_modified",
        "bookmaker_odds_used",
        "future_results_used",
        "final_test_accessed",
        "outcome_based_threshold_tuning",
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
    # Protection
    # ========================================================

    print(
        "\n6. WRITE PROTECTION"
    )

    check(
        "Intelligence artifact unchanged by validator",
        sha256_file(
            INTELLIGENCE_FILE
        )
        ==
        protected[
            "intelligence"
        ],
        failures,
    )

    check(
        "Stage 9.1 contract unchanged",
        sha256_file(
            CONTRACT_FILE
        )
        ==
        protected[
            "contract"
        ],
        failures,
    )

    check(
        "Stage 9.1 verification unchanged",
        sha256_file(
            CONTRACT_VERIFICATION_FILE
        )
        ==
        protected[
            "contract_verification"
        ],
        failures,
    )

    check(
        "Stage 9.2 base unchanged",
        sha256_file(
            BASE_FILE
        )
        ==
        protected[
            "base"
        ],
        failures,
    )

    check(
        "Stage 9.2 report unchanged",
        sha256_file(
            BASE_REPORT_FILE
        )
        ==
        protected[
            "base_report"
        ],
        failures,
    )

    # ========================================================
    # Promote verified Stage 9.4
    # ========================================================

    print(
        "\n7. FINAL STAGE 9.4 PROMOTION"
    )

    overall_pass = (
        len(
            failures
        )
        == 0
    )

    if overall_pass:

        updated = load_json(
            REPORT_FILE
        )

        verified_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        updated[
            "confidence_uncertainty_layer"
        ] = "VERIFIED"

        updated[
            "stage_9_4_verified_at_utc"
        ] = verified_at

        updated[
            "independent_stage_9_4_validation"
        ] = {

            "status":
                "VERIFIED",

            "fixture_count":
                result[
                    "fixture_count"
                ],

            "schema_exact":
                True,

            "fixture_sets_exact":
                True,

            "stage9_2_values_exact":
                True,

            "stage9_3_values_preserved":
                True,

            "entropy_exact":
                True,

            "normalized_entropy_exact":
                True,

            "confidence_bands_exact":
                True,

            "uncertainty_bands_exact":
                True,

            "stage9_5_fields_blank":
                True,

            "dependency_identity_current":
                True,

            "tampered_uncertainty_rejected":
                True,
        }

        updated[
            "stage9_ready_for_9_5"
        ] = True

        updated[
            "next_stage"
        ] = "9.5"

        updated[
            "failures"
        ] = []

        save_json_atomic(
            REPORT_FILE,
            updated,
        )

        persisted = load_json(
            REPORT_FILE
        )

        check(
            "Stage 9.4 COMPLETE persisted",
            persisted.get(
                "stage_9_4_complete"
            )
            is True,
            failures,
        )

        check(
            "Confidence & Uncertainty VERIFIED persisted",
            persisted.get(
                "confidence_uncertainty_layer"
            )
            == "VERIFIED",
            failures,
        )

        check(
            "Stage 9 ready for 9.5 persisted",
            persisted.get(
                "stage9_ready_for_9_5"
            )
            is True,
            failures,
        )

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
            "STAGE 9.4: COMPLETE"
        )

        print(
            "CONFIDENCE & UNCERTAINTY LAYER: VERIFIED"
        )

        print(
            "STAGE 9 READY FOR 9.5"
        )

    else:

        print(
            "STAGE 9.4: FAIL"
        )

        print(
            "CONFIDENCE & UNCERTAINTY LAYER: NOT VERIFIED"
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
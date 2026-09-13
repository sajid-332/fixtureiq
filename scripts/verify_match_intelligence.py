"""
FixtureIQ Stage 9.3
Independent Derived Match Intelligence Verification.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
import tempfile
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


from backend.services.match_intelligence_validator import (
    MatchIntelligenceValidationError,
    MatchIntelligenceValidator,
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

OUTPUT_FILE = (
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


def tamper_output(
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
            "Cannot tamper empty Stage 9.3 output."
        )

    current = rows[
        0
    ][
        "stage9_context_support_score"
    ]

    rows[
        0
    ][
        "stage9_context_support_score"
    ] = (
        "5"
        if current
        != "5"
        else
        "-5"
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
    print("FixtureIQ Stage 9.3")
    print("INDEPENDENT DERIVED INTELLIGENCE VERIFICATION")
    print("=" * 72)

    failures = []

    # ========================================================
    # Required artifacts
    # ========================================================

    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    required = [

        CONTRACT_FILE,
        CONTRACT_VERIFICATION_FILE,
        BASE_FILE,
        BASE_REPORT_FILE,
        OUTPUT_FILE,
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

    output_before = sha256_file(
        OUTPUT_FILE
    )

    contract_before = sha256_file(
        CONTRACT_FILE
    )

    base_before = sha256_file(
        BASE_FILE
    )

    base_report_before = sha256_file(
        BASE_REPORT_FILE
    )

    # ========================================================
    # Independent reconstruction
    # ========================================================

    print(
        "\n2. INDEPENDENT RECONSTRUCTION"
    )

    validator = MatchIntelligenceValidator()

    try:

        result = validator.validate()

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
        "Independent Stage 9.3 validation PASS",
        validation_ok,
        failures,
    )

    if validation_ok:

        flags = [

            "fixture_sets_exact",
            "fixture_order_preserved",
            "base_schema_exact",
            "final_schema_exact",
            "base_values_exact",
            "probability_metrics_exact",
            "context_gaps_exact",
            "context_support_score_exact",
            "context_alignment_exact",
            "stage9_4_fields_blank",
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
            "Base comparisons > 0",
            result.get(
                "base_value_comparisons",
                0,
            )
            > 0,
            failures,
        )

        check(
            "Derived comparisons > 0",
            result.get(
                "derived_value_comparisons",
                0,
            )
            > 0,
            failures,
        )

    # ========================================================
    # Negative tamper test
    # ========================================================

    print(
        "\n3. NEGATIVE TEST - DERIVED VALUE TAMPER"
    )

    with tempfile.TemporaryDirectory() as temp_dir:

        temp_output = (
            Path(
                temp_dir
            )
            / "match_intelligence.csv"
        )

        tamper_output(
            OUTPUT_FILE,
            temp_output,
        )

        tampered_validator = (
            MatchIntelligenceValidator(
                output_file=
                    temp_output,
            )
        )

        tamper_rejected = False

        try:

            tampered_validator.validate()

        except MatchIntelligenceValidationError:

            tamper_rejected = True

        except Exception:

            tamper_rejected = True

        check(
            "Tampered Stage 9.3 value rejected",
            tamper_rejected,
            failures,
        )

    # ========================================================
    # Report rule checks
    # ========================================================

    print(
        "\n4. RULE CONTRACT"
    )

    report = load_json(
        REPORT_FILE
    )

    check(
        "Stage 9.3 report PASS",
        report.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 9.3 COMPLETE",
        report.get(
            "stage_9_3_complete"
        )
        is True,
        failures,
    )

    check(
        "Derived Match Intelligence VERIFIED",
        report.get(
            "derived_match_intelligence"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Rule version exact",
        report.get(
            "rule_version"
        )
        ==
        "STAGE9_3_DERIVED_INTELLIGENCE_V1",
        failures,
    )

    support_rule = report.get(
        "context_support_rule",
        {}
    )

    check(
        "Context component count = 5",
        support_rule.get(
            "component_count"
        )
        == 5,
        failures,
    )

    check(
        "Context minimum score = -5",
        support_rule.get(
            "minimum_score"
        )
        == -5,
        failures,
    )

    check(
        "Context maximum score = 5",
        support_rule.get(
            "maximum_score"
        )
        == 5,
        failures,
    )

    check(
        "Missing venue sample is neutral",
        support_rule.get(
            "missing_venue_sample_policy"
        )
        ==
        "NEUTRAL_ZERO_VOTE",
        failures,
    )

    check(
        "No outcome tuning",
        support_rule.get(
            "outcome_tuning_used"
        )
        is False,
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
        "bookmaker_odds_used",
        "future_results_used",
        "final_test_accessed",
        "outcome_based_tuning_used",
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

    check(
        "Stage 9 ready for 9.4",
        report.get(
            "stage9_ready_for_9_4"
        )
        is True,
        failures,
    )

    # ========================================================
    # Write protection
    # ========================================================

    print(
        "\n6. WRITE PROTECTION"
    )

    check(
        "Output unchanged by validator",
        sha256_file(
            OUTPUT_FILE
        )
        == output_before,
        failures,
    )

    check(
        "Stage 9.1 contract unchanged",
        sha256_file(
            CONTRACT_FILE
        )
        == contract_before,
        failures,
    )

    check(
        "Stage 9.2 base unchanged",
        sha256_file(
            BASE_FILE
        )
        == base_before,
        failures,
    )

    check(
        "Stage 9.2 report unchanged",
        sha256_file(
            BASE_REPORT_FILE
        )
        == base_report_before,
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
            "STAGE 9.3: COMPLETE"
        )

        print(
            "DERIVED MATCH INTELLIGENCE: VERIFIED"
        )

        print(
            "STAGE 9 READY FOR 9.4"
        )

    else:

        print(
            "STAGE 9.3: FAIL"
        )

        print(
            "DERIVED MATCH INTELLIGENCE: NOT VERIFIED"
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
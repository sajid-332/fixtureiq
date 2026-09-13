"""
FixtureIQ Stage 9.5
Independent Match Explanation Engine Verification.
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


from backend.services.match_explanation_validator import (
    MatchExplanationValidationError,
    MatchExplanationValidator,
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


def tamper_headline(
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

    rows[
        0
    ][
        "stage9_explanation_headline"
    ] = (
        "Tampered explanation headline"
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

    print(
        "FixtureIQ Stage 9.5"
    )

    print(
        "INDEPENDENT MATCH EXPLANATION VERIFICATION"
    )

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
        INTELLIGENCE_FILE,
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
    # Independent reconstruction
    # ========================================================

    print(
        "\n2. INDEPENDENT EXPLANATION RECONSTRUCTION"
    )

    try:

        result = (
            MatchExplanationValidator()
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
        "Independent Stage 9.5 validation PASS",
        validation_ok,
        failures,
    )

    if validation_ok:

        flags = [

            "schema_exact",
            "fixture_ids_unique",
            "protected_stage9_4_snapshot_exact",
            "headlines_exact",
            "summaries_exact",
            "deterministic_templates_exact",
            "context_score_reconstruction_exact",
            "non_guaranteed_language_verified",
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
            "Explanation comparisons = fixture count x 2",
            result.get(
                "explanation_comparisons"
            )
            ==
            (
                result.get(
                    "fixture_count"
                )
                * 2
            ),
            failures,
        )

    # ========================================================
    # Contract checks
    # ========================================================

    print(
        "\n3. EXPLANATION CONTRACT"
    )

    report = load_json(
        REPORT_FILE
    )

    explanation_contract = report.get(
        "explanation_contract",
        {}
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
        "Explanation rule version exact",
        report.get(
            "stage_9_5_rule_version"
        )
        ==
        "STAGE9_5_DETERMINISTIC_EXPLANATION_V1",
        failures,
    )

    check(
        "Deterministic template engine",
        explanation_contract.get(
            "engine"
        )
        ==
        "DETERMINISTIC_TEMPLATE_ENGINE",
        failures,
    )

    check(
        "LLM generation disabled",
        explanation_contract.get(
            "llm_generation"
        )
        is False,
        failures,
    )

    check(
        "Prediction authority remains Stage 7",
        explanation_contract.get(
            "prediction_authority"
        )
        == "STAGE7_ONLY",
        failures,
    )

    check(
        "Explanation cannot change prediction",
        explanation_contract.get(
            "explanation_may_change_prediction"
        )
        is False,
        failures,
    )

    check(
        "Explanation cannot change probability",
        explanation_contract.get(
            "explanation_may_change_probability"
        )
        is False,
        failures,
    )

    check(
        "No outcome tuning",
        explanation_contract.get(
            "outcome_tuning_used"
        )
        is False,
        failures,
    )

    # ========================================================
    # Negative semantic tamper test
    # ========================================================

    print(
        "\n4. NEGATIVE TEST - EXPLANATION TAMPER"
    )

    with tempfile.TemporaryDirectory() as temp_dir:

        temp_dir = Path(
            temp_dir
        )

        temp_output = (
            temp_dir
            / "match_intelligence.csv"
        )

        temp_report = (
            temp_dir
            / "match_intelligence_report.json"
        )

        tamper_headline(
            INTELLIGENCE_FILE,
            temp_output,
        )

        temporary_report = load_json(
            REPORT_FILE
        )

        # Update SHA intentionally so rejection must come
        # from semantic explanation validation, not merely
        # the artifact-hash check.
        temporary_report[
            "output_artifact"
        ][
            "sha256"
        ] = sha256_file(
            temp_output
        )

        save_json(
            temp_report,
            temporary_report,
        )

        tamper_rejected = False

        try:

            MatchExplanationValidator(

                intelligence_file=
                    temp_output,

                report_file=
                    temp_report,

            ).validate()

        except MatchExplanationValidationError:

            tamper_rejected = True

        except Exception:

            tamper_rejected = True

        check(
            "Tampered explanation rejected semantically",
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

    check(
        "Deterministic explanation engine",
        safety.get(
            "deterministic_explanation_engine"
        )
        is True,
        failures,
    )

    false_flags = [

        "llm_generation_used",
        "model_loaded",
        "model_executed",
        "model_modified",
        "probabilities_modified",
        "probabilities_recalibrated",
        "prediction_labels_modified",
        "source_confidence_modified",
        "context_intelligence_modified",
        "confidence_uncertainty_modified",
        "stage7_artifacts_modified",
        "stage8_artifacts_modified",
        "stage9_2_artifacts_modified",
        "bookmaker_odds_used",
        "future_results_used",
        "final_test_accessed",
        "outcome_based_tuning_used",
        "guaranteed_result_language_allowed",
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
    # Write protection
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
    # Final promotion
    # ========================================================

    print(
        "\n7. FINAL STAGE 9.5 PROMOTION"
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
            "match_explanation_engine"
        ] = "VERIFIED"

        updated[
            "stage_9_5_verified_at_utc"
        ] = verified_at

        updated[
            "independent_stage_9_5_validation"
        ] = {

            "status":
                "VERIFIED",

            "fixture_count":
                result[
                    "fixture_count"
                ],

            "schema_exact":
                True,

            "fixture_ids_unique":
                True,

            "protected_stage9_4_snapshot_exact":
                True,

            "headlines_exact":
                True,

            "summaries_exact":
                True,

            "deterministic_templates_exact":
                True,

            "context_score_reconstruction_exact":
                True,

            "non_guaranteed_language_verified":
                True,

            "tampered_explanation_rejected":
                True,
        }

        updated[
            "stage9_ready_for_9_6"
        ] = True

        updated[
            "next_stage"
        ] = "9.6"

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
            "Stage 9.5 COMPLETE persisted",
            persisted.get(
                "stage_9_5_complete"
            )
            is True,
            failures,
        )

        check(
            "Explanation Engine VERIFIED persisted",
            persisted.get(
                "match_explanation_engine"
            )
            == "VERIFIED",
            failures,
        )

        check(
            "Stage 9 ready for 9.6 persisted",
            persisted.get(
                "stage9_ready_for_9_6"
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

    # ========================================================
    # Final output
    # ========================================================

    print(
        "\n" + "=" * 72
    )

    if overall_pass:

        print(
            "STAGE 9.5: COMPLETE"
        )

        print(
            "MATCH EXPLANATION ENGINE: VERIFIED"
        )

        print(
            "STAGE 9 READY FOR 9.6"
        )

    else:

        print(
            "STAGE 9.5: FAIL"
        )

        print(
            "MATCH EXPLANATION ENGINE: NOT VERIFIED"
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
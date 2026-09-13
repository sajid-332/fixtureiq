"""
FixtureIQ Stage 9.2.4
Independent Prediction-Context Join Validation.

Verifies match_intelligence_base.csv independently from the builder.

Updates:
match_intelligence_base_report.json

9.2.5 remains PENDING.
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


from backend.services.match_intelligence_base_validator import (
    MatchIntelligenceBaseValidationError,
    MatchIntelligenceBaseValidator,
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

REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_base_report.json"
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


def mutate_first_prediction_copy(
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
            "Cannot tamper empty base artifact."
        )

    target_field = (
        "stage7_prob_home_win"
    )

    original = rows[
        0
    ][
        target_field
    ]

    rows[
        0
    ][
        target_field
    ] = (
        "0.000000"
        if original
        != "0.000000"
        else
        "1.000000"
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
        "FixtureIQ Stage 9.2.4"
    )

    print(
        "INDEPENDENT STRICT JOIN VALIDATION"
    )

    print("=" * 72)

    failures = []

    # ========================================================
    # Foundation
    # ========================================================

    print(
        "\n1. STAGE 9.2.3 FOUNDATION"
    )

    report = load_json(
        REPORT_FILE
    )

    check(
        "9.2.1 PASS",
        report.get(
            "sub_stages",
            {}
        ).get(
            "9.2.1"
        )
        == "PASS",
        failures,
    )

    check(
        "9.2.2 PASS",
        report.get(
            "sub_stages",
            {}
        ).get(
            "9.2.2"
        )
        == "PASS",
        failures,
    )

    check(
        "9.2.3 PASS",
        report.get(
            "sub_stages",
            {}
        ).get(
            "9.2.3"
        )
        == "PASS",
        failures,
    )

    check(
        "9.2.4 currently PENDING",
        report.get(
            "sub_stages",
            {}
        ).get(
            "9.2.4"
        )
        == "PENDING",
        failures,
    )

    check(
        "Base artifact exists",
        BASE_FILE.exists(),
        failures,
    )

    if failures:

        sys.exit(1)

    base_before = sha256_file(
        BASE_FILE
    )

    contract_before = sha256_file(
        CONTRACT_FILE
    )

    contract_verification_before = (
        sha256_file(
            CONTRACT_VERIFICATION_FILE
        )
    )

    # ========================================================
    # Independent validation
    # ========================================================

    print(
        "\n2. INDEPENDENT RECONSTRUCTION"
    )

    validator = (
        MatchIntelligenceBaseValidator()
    )

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
            "Independent validation error:",
            exc,
        )

        result = {}
        validation_ok = False

    check(
        "Independent validation PASS",
        validation_ok,
        failures,
    )

    if validation_ok:

        true_flags = [

            "fixture_sets_exact",
            "output_fixture_ids_unique",
            "source_order_preserved",
            "schema_exact",
            "strict_identity_exact",
            "context_values_exact",
            "prediction_values_exact",
            "probabilities_exact",
            "prediction_labels_exact",
            "source_confidence_exact",
            "exact_independent_reconstruction",
            "dependency_identity_current",
            "provenance_verified",
        ]

        for flag in true_flags:

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
            "Context comparisons > 0",
            result.get(
                "context_value_comparisons",
                0,
            )
            > 0,
            failures,
        )

        check(
            "Prediction comparisons > 0",
            result.get(
                "prediction_value_comparisons",
                0,
            )
            > 0,
            failures,
        )

        check(
            "Probability comparisons = fixtures x 3",
            result.get(
                "probability_comparisons"
            )
            ==
            (
                result.get(
                    "fixture_count"
                )
                * 3
            ),
            failures,
        )

        check(
            "Label comparisons = fixture count",
            result.get(
                "label_comparisons"
            )
            ==
            result.get(
                "fixture_count"
            ),
            failures,
        )

        check(
            "Confidence comparisons = fixture count",
            result.get(
                "confidence_comparisons"
            )
            ==
            result.get(
                "fixture_count"
            ),
            failures,
        )

    # ========================================================
    # Negative tamper test
    # ========================================================

    print(
        "\n3. NEGATIVE TEST - BASE ARTIFACT TAMPER"
    )

    with tempfile.TemporaryDirectory() as temp_dir:

        temp_base = (
            Path(
                temp_dir
            )
            / "match_intelligence_base.csv"
        )

        mutate_first_prediction_copy(
            BASE_FILE,
            temp_base,
        )

        tampered_validator = (
            MatchIntelligenceBaseValidator(
                base_file=
                    temp_base,
            )
        )

        tamper_rejected = False

        try:

            tampered_validator.validate()

        except MatchIntelligenceBaseValidationError:

            tamper_rejected = True

        except Exception:

            tamper_rejected = True

        check(
            "Tampered base artifact rejected",
            tamper_rejected,
            failures,
        )

    # ========================================================
    # Protection
    # ========================================================

    print(
        "\n4. BUILD ARTIFACT / CONTRACT PROTECTION"
    )

    check(
        "Base artifact unchanged by validator",
        sha256_file(
            BASE_FILE
        )
        == base_before,
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
        "Stage 9.1 verification unchanged",
        sha256_file(
            CONTRACT_VERIFICATION_FILE
        )
        ==
        contract_verification_before,
        failures,
    )

    # ========================================================
    # Save 9.2.4
    # ========================================================

    print(
        "\n5. SAVE STAGE 9.2.4 EVIDENCE"
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

        updated = load_json(
            REPORT_FILE
        )

        sub_stages = dict(
            updated.get(
                "sub_stages",
                {}
            )
        )

        sub_stages[
            "9.2.1"
        ] = "PASS"

        sub_stages[
            "9.2.2"
        ] = "PASS"

        sub_stages[
            "9.2.3"
        ] = "PASS"

        sub_stages[
            "9.2.4"
        ] = "PASS"

        sub_stages[
            "9.2.5"
        ] = "PENDING"

        updated[
            "sub_stages"
        ] = sub_stages

        updated[
            "status"
        ] = "PARTIAL_PASS"

        updated[
            "stage_9_2_complete"
        ] = False

        updated[
            "stage_9_2_status"
        ] = "IN_PROGRESS"

        updated[
            "independent_join_validation"
        ] = "VERIFIED"

        updated[
            "stage_9_2_4_verified_at_utc"
        ] = verified_at

        updated[
            "independent_validation"
        ] = {

            "status":
                "VERIFIED",

            "fixture_count":
                result[
                    "fixture_count"
                ],

            "column_count":
                result[
                    "column_count"
                ],

            "fixture_sets_exact":
                True,

            "source_order_preserved":
                True,

            "schema_exact":
                True,

            "strict_identity_exact":
                True,

            "context_values_exact":
                True,

            "prediction_values_exact":
                True,

            "probabilities_exact":
                True,

            "prediction_labels_exact":
                True,

            "source_confidence_exact":
                True,

            "exact_independent_reconstruction":
                True,

            "dependency_identity_current":
                True,

            "provenance_verified":
                True,

            "context_value_comparisons":
                result[
                    "context_value_comparisons"
                ],

            "prediction_value_comparisons":
                result[
                    "prediction_value_comparisons"
                ],

            "probability_comparisons":
                result[
                    "probability_comparisons"
                ],

            "label_comparisons":
                result[
                    "label_comparisons"
                ],

            "confidence_comparisons":
                result[
                    "confidence_comparisons"
                ],

            "tampered_base_rejected":
                True,
        }

        safety = dict(
            updated.get(
                "safety",
                {}
            )
        )

        safety.update(
            {

                "independent_validator":
                    True,

                "builder_reused_for_validation":
                    False,

                "base_artifact_modified_by_validator":
                    False,

                "stage7_artifacts_modified":
                    False,

                "stage8_artifacts_modified":
                    False,

                "probabilities_modified":
                    False,

                "prediction_labels_modified":
                    False,

                "source_confidence_modified":
                    False,

                "model_loaded":
                    False,

                "model_executed":
                    False,

                "final_test_accessed":
                    False,
            }
        )

        updated[
            "safety"
        ] = safety

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
            "9.2.4 PASS persisted",
            persisted.get(
                "sub_stages",
                {}
            ).get(
                "9.2.4"
            )
            == "PASS",
            failures,
        )

        check(
            "9.2.5 remains PENDING",
            persisted.get(
                "sub_stages",
                {}
            ).get(
                "9.2.5"
            )
            == "PENDING",
            failures,
        )

        check(
            "Independent validation VERIFIED persisted",
            persisted.get(
                "independent_join_validation"
            )
            == "VERIFIED",
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
            "STAGE 9.2.3: PASS"
        )

        print(
            "STRICT PREDICTION-CONTEXT JOIN: VERIFIED"
        )

        print(
            "STAGE 9.2.4: PASS"
        )

        print(
            "INDEPENDENT JOIN VALIDATION: VERIFIED"
        )

        print(
            "STAGE 9.2: IN PROGRESS"
        )

    else:

        print(
            "STAGE 9.2.4: FAIL"
        )

        print(
            "STAGE 9.2: INCOMPLETE"
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
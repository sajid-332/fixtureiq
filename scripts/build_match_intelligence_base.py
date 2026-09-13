"""
FixtureIQ Stage 9.2.3
Strict Prediction-Context Join.

Creates:
data/processed/intelligence/match_intelligence_base.csv

Updates:
data/processed/intelligence/match_intelligence_base_report.json

9.2.4 and 9.2.5 remain pending.
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

if str(BASE_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(BASE_DIR),
    )


from backend.services.match_intelligence_base_builder import (
    MatchIntelligenceBaseBuilder,
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


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 9.2.3"
    )

    print(
        "STRICT PREDICTION-CONTEXT JOIN"
    )

    print("=" * 72)

    failures = []

    contract = load_json(
        CONTRACT_FILE
    )

    verification = load_json(
        CONTRACT_VERIFICATION_FILE
    )

    report = load_json(
        REPORT_FILE
    )

    # ========================================================
    # Foundation
    # ========================================================

    print(
        "\n1. STAGE 9.2 FOUNDATION"
    )

    check(
        "Stage 9.1 contract locked",
        contract.get(
            "status"
        )
        ==
        "LOCKED_MATCH_INTELLIGENCE_CONTRACT",
        failures,
    )

    check(
        "Stage 9.1 verification PASS",
        verification.get(
            "status"
        )
        == "PASS",
        failures,
    )

    sub_stages = report.get(
        "sub_stages",
        {}
    )

    check(
        "9.2.1 already PASS",
        sub_stages.get(
            "9.2.1"
        )
        == "PASS",
        failures,
    )

    check(
        "9.2.2 already PASS",
        sub_stages.get(
            "9.2.2"
        )
        == "PASS",
        failures,
    )

    check(
        "9.2.3 currently PENDING",
        sub_stages.get(
            "9.2.3"
        )
        == "PENDING",
        failures,
    )

    # ========================================================
    # Output contract
    # ========================================================

    print(
        "\n2. OUTPUT CONTRACT"
    )

    outputs = (
        contract.get(
            "stage_9_1_3",
            {}
        ).get(
            "output_artifact_contract",
            {}
        ).get(
            "outputs",
            {}
        )
    )

    check(
        "Base CSV path locked",
        outputs.get(
            "match_intelligence_base",
            {}
        ).get(
            "path"
        )
        ==
        relative_path(
            BASE_FILE
        ),
        failures,
    )

    check(
        "Base report path locked",
        outputs.get(
            "match_intelligence_base_report",
            {}
        ).get(
            "path"
        )
        ==
        relative_path(
            REPORT_FILE
        ),
        failures,
    )

    if failures:

        sys.exit(1)

    # ========================================================
    # Protect upstream dependencies
    # ========================================================

    allowed_inputs = (
        contract.get(
            "stage_9_1_1",
            {}
        ).get(
            "allowed_inputs",
            {}
        )
    )

    protected_before = {}

    for name, item in allowed_inputs.items():

        source_path = (
            BASE_DIR
            / item[
                "path"
            ]
        )

        protected_before[
            name
        ] = sha256_file(
            source_path
        )

    protected_before[
        "stage9_contract"
    ] = sha256_file(
        CONTRACT_FILE
    )

    protected_before[
        "stage9_contract_verification"
    ] = sha256_file(
        CONTRACT_VERIFICATION_FILE
    )

    # ========================================================
    # Build
    # ========================================================

    print(
        "\n3. BUILD STRICT JOIN"
    )

    builder = (
        MatchIntelligenceBaseBuilder()
    )

    try:

        result = (
            builder.build_and_write()
        )

        build_ok = (
            result.get(
                "status"
            )
            == "PASS"
        )

    except Exception as exc:

        print(
            "Build error:",
            exc,
        )

        result = {}
        build_ok = False

    check(
        "Strict join build PASS",
        build_ok,
        failures,
    )

    if build_ok:

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
            "Fixture sets exact",
            result.get(
                "fixture_sets_exact"
            )
            is True,
            failures,
        )

        check(
            "Strict fixture_id join",
            result.get(
                "strict_fixture_id_join"
            )
            is True,
            failures,
        )

        check(
            "Identity revalidated",
            result.get(
                "strict_identity_revalidated"
            )
            is True,
            failures,
        )

        check(
            "Context values copied exactly",
            result.get(
                "context_values_copied_exactly"
            )
            is True,
            failures,
        )

        check(
            "Prediction values copied exactly",
            result.get(
                "prediction_values_copied_exactly"
            )
            is True,
            failures,
        )

        check(
            "Source order preserved",
            result.get(
                "source_order_preserved"
            )
            is True,
            failures,
        )

        check(
            "Probabilities not modified",
            result.get(
                "probabilities_modified"
            )
            is False,
            failures,
        )

        check(
            "Prediction labels not modified",
            result.get(
                "prediction_labels_modified"
            )
            is False,
            failures,
        )

        check(
            "Source confidence not modified",
            result.get(
                "source_confidence_modified"
            )
            is False,
            failures,
        )

        check(
            "Fuzzy matching not used",
            result.get(
                "fuzzy_matching_used"
            )
            is False,
            failures,
        )

        check(
            "Best-effort fallback not used",
            result.get(
                "best_effort_fallback_used"
            )
            is False,
            failures,
        )

        check(
            "Base CSV exists",
            BASE_FILE.exists(),
            failures,
        )

    # ========================================================
    # Upstream write protection
    # ========================================================

    print(
        "\n4. UPSTREAM WRITE PROTECTION"
    )

    for name, item in allowed_inputs.items():

        source_path = (
            BASE_DIR
            / item[
                "path"
            ]
        )

        check(
            f"{name} unchanged",
            sha256_file(
                source_path
            )
            ==
            protected_before[
                name
            ],
            failures,
        )

    check(
        "Stage 9.1 contract unchanged",
        sha256_file(
            CONTRACT_FILE
        )
        ==
        protected_before[
            "stage9_contract"
        ],
        failures,
    )

    check(
        "Stage 9.1 verification unchanged",
        sha256_file(
            CONTRACT_VERIFICATION_FILE
        )
        ==
        protected_before[
            "stage9_contract_verification"
        ],
        failures,
    )

    # ========================================================
    # Persist 9.2.3 evidence
    # ========================================================

    print(
        "\n5. SAVE STAGE 9.2.3 EVIDENCE"
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

        updated_report = dict(
            report
        )

        updated_sub_stages = dict(
            updated_report.get(
                "sub_stages",
                {}
            )
        )

        updated_sub_stages[
            "9.2.1"
        ] = "PASS"

        updated_sub_stages[
            "9.2.2"
        ] = "PASS"

        updated_sub_stages[
            "9.2.3"
        ] = "PASS"

        updated_sub_stages[
            "9.2.4"
        ] = "PENDING"

        updated_sub_stages[
            "9.2.5"
        ] = "PENDING"

        updated_report[
            "sub_stages"
        ] = updated_sub_stages

        updated_report[
            "status"
        ] = "PARTIAL_PASS"

        updated_report[
            "stage_9_2_complete"
        ] = False

        updated_report[
            "stage_9_2_status"
        ] = "IN_PROGRESS"

        updated_report[
            "strict_prediction_context_join"
        ] = "VERIFIED"

        updated_report[
            "stage_9_2_3_verified_at_utc"
        ] = verified_at

        updated_report[
            "base_artifact"
        ] = {

            "path":
                relative_path(
                    BASE_FILE
                ),

            "sha256":
                sha256_file(
                    BASE_FILE
                ),

            "fixture_count":
                result[
                    "fixture_count"
                ],

            "column_count":
                result[
                    "column_count"
                ],

            "context_column_count":
                result[
                    "context_column_count"
                ],

            "prediction_copy_field_count":
                result[
                    "prediction_copy_field_count"
                ],

            "source_order_preserved":
                True,

            "strict_fixture_id_join":
                True,

            "strict_identity_revalidated":
                True,

            "context_values_copied_exactly":
                True,

            "prediction_values_copied_exactly":
                True,
        }

        dependency_identity = {

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
        }

        for name, item in allowed_inputs.items():

            source_path = (
                BASE_DIR
                / item[
                    "path"
                ]
            )

            dependency_identity[
                name
            ] = {

                "path":
                    item[
                        "path"
                    ],

                "sha256":
                    sha256_file(
                        source_path
                    ),
            }

        updated_report[
            "dependency_identity"
        ] = dependency_identity

        updated_report[
            "provenance"
        ] = {

            "generated_at_utc":
                verified_at,

            "hash_algorithm":
                "SHA256",

            "prediction_source":
                relative_path(
                    PRODUCTION_DIR
                    / "production_predictions.csv"
                ),

            "context_source":
                relative_path(
                    CONTEXT_DIR
                    / "enriched_upcoming_fixtures.csv"
                ),

            "prediction_sha256":
                result[
                    "prediction_source_sha256"
                ],

            "context_sha256":
                result[
                    "context_source_sha256"
                ],

            "base_output_sha256":
                sha256_file(
                    BASE_FILE
                ),

            "fixture_identity_validation":
                "EXACT",

            "prediction_value_preservation":
                "EXACT",

            "context_value_preservation":
                "EXACT",
        }

        updated_report[
            "safety"
        ] = {

            "read_only_upstream":
                True,

            "interpretation_only":
                True,

            "provider_fetch_performed":
                False,

            "model_loaded":
                False,

            "model_executed":
                False,

            "model_modified":
                False,

            "probabilities_modified":
                False,

            "probabilities_recalibrated":
                False,

            "prediction_labels_modified":
                False,

            "source_confidence_modified":
                False,

            "stage7_artifacts_modified":
                False,

            "stage8_artifacts_modified":
                False,

            "fuzzy_matching_used":
                False,

            "best_effort_identity_fallback_used":
                False,

            "future_results_used":
                False,

            "final_test_accessed":
                False,
        }

        updated_report[
            "failures"
        ] = []

        save_json_atomic(
            REPORT_FILE,
            updated_report,
        )

        print(
            REPORT_FILE
        )

        persisted = load_json(
            REPORT_FILE
        )

        check(
            "9.2.3 PASS persisted",
            persisted.get(
                "sub_stages",
                {}
            ).get(
                "9.2.3"
            )
            == "PASS",
            failures,
        )

        check(
            "9.2.4 remains PENDING",
            persisted.get(
                "sub_stages",
                {}
            ).get(
                "9.2.4"
            )
            == "PENDING",
            failures,
        )

        check(
            "Strict join VERIFIED persisted",
            persisted.get(
                "strict_prediction_context_join"
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
            "STAGE 9.2: IN PROGRESS"
        )

    else:

        print(
            "STAGE 9.2.3: FAIL"
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
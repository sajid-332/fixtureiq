"""
FixtureIQ Stage 7.9.1
Independent Production Serving Contract Verification.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
)

PRODUCTION_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "production"
)

CONTRACT_FILE = (
    MODEL_DIR
    / "production_serving_contract.json"
)

INFERENCE_CONTRACT_FILE = (
    MODEL_DIR
    / "production_inference_contract.json"
)

MODEL_FILE = (
    MODEL_DIR
    / "selected"
    / "selected_model.joblib"
)

STAGE_7_8_FINAL_FILE = (
    PRODUCTION_DIR
    / "stage7_8_final_verification.json"
)

OUTPUT_FILE = (
    MODEL_DIR
    / "production_serving_contract_verification.json"
)


EXPECTED_MODEL_ID = "random_forest"
EXPECTED_FEATURE_COUNT = 86


def load_json(path: Path) -> dict:

    if not path.exists():
        raise FileNotFoundError(path)

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        payload = json.load(file)

    if not isinstance(payload, dict):
        raise RuntimeError(
            f"Expected JSON object: {path}"
        )

    return payload


def sha256_file(path: Path) -> str:

    digest = hashlib.sha256()

    with path.open("rb") as file:

        for chunk in iter(
            lambda: file.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def check(
    label: str,
    condition,
    failures: list[str],
):

    passed = bool(condition)

    print(
        f"{label}: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    if not passed:
        failures.append(label)


def main():

    print("=" * 64)
    print("FixtureIQ Stage 7.9.1")
    print("Production Serving Contract Verification")
    print("=" * 64)

    failures = []

    print("\n1. REQUIRED ARTIFACTS")

    for path in [
        CONTRACT_FILE,
        INFERENCE_CONTRACT_FILE,
        MODEL_FILE,
        STAGE_7_8_FINAL_FILE,
    ]:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:
        sys.exit(1)

    contract = load_json(CONTRACT_FILE)

    inference_contract = load_json(
        INFERENCE_CONTRACT_FILE
    )

    stage_7_8 = load_json(
        STAGE_7_8_FINAL_FILE
    )

    print("\n2. CONTRACT IDENTITY")

    check(
        "Stage = 7.9.1",
        contract.get("stage")
        == "7.9.1",
        failures,
    )

    check(
        "Contract version = 1.0.0",
        contract.get("contract_version")
        == "1.0.0",
        failures,
    )

    check(
        "Status = LOCKED_SERVING_CONTRACT",
        contract.get("status")
        == "LOCKED_SERVING_CONTRACT",
        failures,
    )

    print("\n3. UPSTREAM DEPENDENCY")

    dependency = contract.get(
        "depends_on",
        {},
    )

    check(
        "Depends on 7.8.5",
        dependency.get("stage")
        == "7.8.5",
        failures,
    )

    check(
        "Requires Stage 7.8.5 PASS",
        dependency.get("required_status")
        == "PASS",
        failures,
    )

    check(
        "Requires Stage 7.8 COMPLETE",
        dependency.get(
            "required_stage_7_8_status"
        )
        == "COMPLETE",
        failures,
    )

    check(
        "Actual Stage 7.8.5 PASS",
        stage_7_8.get("status")
        == "PASS",
        failures,
    )

    check(
        "Actual Stage 7.8 COMPLETE",
        stage_7_8.get(
            "stage_7_8_status"
        )
        == "COMPLETE",
        failures,
    )

    print("\n4. MODEL CONTRACT")

    model = contract.get(
        "model",
        {},
    )

    actual_model_hash = sha256_file(
        MODEL_FILE
    ).lower()

    check(
        "Model ID",
        model.get("model_id")
        == EXPECTED_MODEL_ID,
        failures,
    )

    check(
        "Model status",
        model.get("status")
        == "LOCKED",
        failures,
    )

    check(
        "Feature count = 86",
        model.get("feature_count")
        == EXPECTED_FEATURE_COUNT,
        failures,
    )

    check(
        "Contract model SHA256",
        str(
            model.get("sha256", "")
        ).lower()
        ==
        actual_model_hash,
        failures,
    )

    check(
        "Stage 7.8 model SHA256",
        str(
            stage_7_8.get(
                "model_sha256",
                "",
            )
        ).lower()
        ==
        actual_model_hash,
        failures,
    )

    inference_model = inference_contract.get(
        "model",
        {},
    )

    check(
        "Inference model ID",
        inference_model.get(
            "candidate_id"
        )
        == EXPECTED_MODEL_ID,
        failures,
    )

    print("\n5. TARGET CONTRACT")

    check(
        "Target mapping",
        contract.get(
            "target_mapping"
        )
        ==
        {
            "0": "Draw",
            "1": "Home Win",
            "2": "Away Win",
        },
        failures,
    )

    check(
        "Probability mapping",
        contract.get(
            "probability_mapping"
        )
        ==
        {
            "0": "prob_draw",
            "1": "prob_home_win",
            "2": "prob_away_win",
        },
        failures,
    )

    print("\n6. PUBLIC SCHEMA")

    public_schema = contract.get(
        "public_prediction_schema",
        {},
    )

    required_fields = public_schema.get(
        "required_fields",
        [],
    )

    optional_fields = public_schema.get(
        "optional_fields",
        [],
    )

    field_order = public_schema.get(
        "field_order",
        [],
    )

    check(
        "Required schema defined",
        len(required_fields) >= 12,
        failures,
    )

    check(
        "Optional fields defined",
        optional_fields
        == [
            "provider_fixture_id",
            "round",
        ],
        failures,
    )

    check(
        "fixture_id public",
        "fixture_id"
        in field_order,
        failures,
    )

    check(
        "Probability fields public",
        all(
            value in field_order
            for value in [
                "prob_home_win",
                "prob_draw",
                "prob_away_win",
            ]
        ),
        failures,
    )

    check(
        "Internal model SHA not public",
        "model_sha256"
        not in field_order,
        failures,
    )

    print("\n7. SERVING POLICY")

    policy = contract.get(
        "serving_policy",
        {},
    )

    check(
        "Read-only mode",
        policy.get("mode")
        == "READ_ONLY",
        failures,
    )

    check(
        "Fail-closed validation",
        policy.get("validation")
        == "FAIL_CLOSED",
        failures,
    )

    check(
        "Future fixture rule",
        policy.get("kickoff_rule")
        == "FIXTURE_DATE_GT_CURRENT_UTC",
        failures,
    )

    check(
        "Stale -> NOT_READY",
        policy.get(
            "stale_snapshot_action"
        )
        == "NOT_READY",
        failures,
    )

    check(
        "Partial stale serving disabled",
        policy.get(
            "allow_partial_stale_snapshot"
        )
        is False,
        failures,
    )

    print("\n8. PROTECTION")

    protection = contract.get(
        "protection",
        {},
    )

    protected_flags = [
        "model_loading_allowed",
        "prediction_execution_allowed",
        "provider_fetching_allowed",
        "feature_construction_allowed",
        "training_allowed",
        "retraining_allowed",
        "model_selection_allowed",
        "hyperparameter_tuning_allowed",
        "model_modification_allowed",
        "final_test_evaluation_artifact_access_allowed",
    ]

    for key in protected_flags:

        check(
            f"{key} = false",
            protection.get(key)
            is False,
            failures,
        )

    print("\n9. CONTRACT HASH")

    contract_hash = sha256_file(
        CONTRACT_FILE
    ).lower()

    print(
        f"Contract SHA256: "
        f"{contract_hash}"
    )

    status = (
        "PASS"
        if not failures
        else "FAIL"
    )

    report = {

        "stage":
            "7.9.1",

        "status":
            status,

        "serving_contract_status":
            (
                "LOCKED"
                if not failures
                else "INVALID"
            ),

        "verified_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "contract_sha256":
            contract_hash,

        "model_id":
            EXPECTED_MODEL_ID,

        "model_sha256":
            actual_model_hash,

        "feature_count":
            EXPECTED_FEATURE_COUNT,

        "failures":
            failures,

        "model_loaded":
            False,

        "prediction_executed":
            False,

        "training_executed":
            False,

        "final_test_evaluation_artifacts_used":
            False,
    }

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
        )

    print("\n10. OUTPUT")
    print(OUTPUT_FILE)

    print("\n" + "=" * 64)

    if failures:

        print("STAGE 7.9.1: FAIL")

        for failure in failures:
            print(
                f"  - {failure}"
            )

    else:

        print("STAGE 7.9.1: PASS")
        print(
            "SERVING CONTRACT: LOCKED"
        )

    print("=" * 64)

    sys.exit(
        0 if not failures else 1
    )


if __name__ == "__main__":
    main()
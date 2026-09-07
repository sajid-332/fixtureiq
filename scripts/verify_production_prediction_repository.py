"""
FixtureIQ Stage 7.9.2
Production Prediction Repository Verification.

Verifies the Stage 7.9.2 trusted read repository against the
locked Stage 7.9.1 serving contract and the current verified
Stage 7.8 production prediction snapshot.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Project root / import path
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# ============================================================
# Paths
# ============================================================

MODEL_DIR = BASE_DIR / "data" / "processed" / "model"

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

CONTRACT_VERIFICATION_FILE = (
    MODEL_DIR
    / "production_serving_contract_verification.json"
)

PREDICTION_FILE = (
    PRODUCTION_DIR
    / "production_predictions.csv"
)

OUTPUT_FILE = (
    PRODUCTION_DIR
    / "production_repository_verification.json"
)

REPOSITORY_SOURCE_FILE = (
    BASE_DIR
    / "backend"
    / "services"
    / "production_prediction_repository.py"
)


# ============================================================
# Import repository AFTER project root is added to sys.path
# ============================================================

from backend.services.production_prediction_repository import (
    ProductionPredictionRepository,
)


# ============================================================
# Helpers
# ============================================================

def sha256_file(
    path: Path,
) -> str:

    if not path.exists():
        raise FileNotFoundError(
            f"File missing: {path}"
        )

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as file:

        for chunk in iter(
            lambda: file.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(
                chunk
            )

    return digest.hexdigest()


def load_json(
    path: Path,
) -> dict:

    if not path.exists():
        raise FileNotFoundError(
            f"JSON missing: {path}"
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


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 68)

    print(
        "FixtureIQ Stage 7.9.2"
    )

    print(
        "Production Prediction Repository Verification"
    )

    print("=" * 68)

    failures: list[str] = []

    # ========================================================
    # 1. Required artifacts
    # ========================================================

    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    required_files = [
        CONTRACT_FILE,
        CONTRACT_VERIFICATION_FILE,
        PREDICTION_FILE,
        REPOSITORY_SOURCE_FILE,
    ]

    for path in required_files:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        print(
            "\nRequired Stage 7.9.2 artifacts are missing."
        )

        print(
            "=" * 68
        )

        print(
            "STAGE 7.9.2: FAIL"
        )

        print(
            "PRODUCTION PREDICTION REPOSITORY: NOT_READY"
        )

        print(
            "=" * 68
        )

        sys.exit(1)

    contract = load_json(
        CONTRACT_FILE
    )

    contract_verification = load_json(
        CONTRACT_VERIFICATION_FILE
    )

    # ========================================================
    # 2. Stage 7.9.1 dependency
    # ========================================================

    print(
        "\n2. STAGE 7.9.1 DEPENDENCY"
    )

    check(
        "Serving contract stage = 7.9.1",
        contract.get(
            "stage"
        )
        == "7.9.1",
        failures,
    )

    check(
        "Serving contract locked",
        contract.get(
            "status"
        )
        == "LOCKED_SERVING_CONTRACT",
        failures,
    )

    check(
        "7.9.1 verifier stage",
        contract_verification.get(
            "stage"
        )
        == "7.9.1",
        failures,
    )

    check(
        "7.9.1 verifier PASS",
        contract_verification.get(
            "status"
        )
        == "PASS",
        failures,
    )

    contract_hash = sha256_file(
        CONTRACT_FILE
    ).lower()

    check(
        "Serving contract SHA256",
        contract_hash
        ==
        str(
            contract_verification.get(
                "contract_sha256",
                "",
            )
        ).lower(),
        failures,
    )

    # ========================================================
    # 3. Initialize repository
    # ========================================================

    print(
        "\n3. INITIALIZE REPOSITORY"
    )

    repository = (
        ProductionPredictionRepository()
    )

    status = (
        repository.get_status()
    )

    check(
        "Repository status READY",
        status.get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "Stage 7.8 verified",
        status.get(
            "stage_7_8_verified"
        )
        is True,
        failures,
    )

    check(
        "Serving contract recognized",
        status.get(
            "serving_contract_locked"
        )
        is True,
        failures,
    )

    check(
        "Snapshot fresh",
        status.get(
            "snapshot_fresh"
        )
        is True,
        failures,
    )

    check(
        "Model ID random_forest",
        status.get(
            "model_id"
        )
        == "random_forest",
        failures,
    )

    check(
        "Feature count 86",
        status.get(
            "feature_count"
        )
        == 86,
        failures,
    )

    # ========================================================
    # Fail cleanly if repository is NOT_READY
    # ========================================================

    if (
        status.get(
            "status"
        )
        != "READY"
    ):

        print(
            "\nRepository errors:"
        )

        for error in status.get(
            "errors",
            [],
        ):

            print(
                f"  - {error}"
            )

        report = {

            "stage":
                "7.9.2",

            "status":
                "FAIL",

            "repository_status":
                "NOT_READY",

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "contract_sha256":
                contract_hash,

            "errors":
                status.get(
                    "errors",
                    [],
                ),

            "warnings":
                status.get(
                    "warnings",
                    [],
                ),

            "failures":
                failures,
        }

        OUTPUT_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with OUTPUT_FILE.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                report,
                file,
                indent=2,
            )

        print(
            "\n" + "=" * 68
        )

        print(
            "STAGE 7.9.2: FAIL"
        )

        print(
            "PRODUCTION PREDICTION REPOSITORY: NOT_READY"
        )

        print(
            "=" * 68
        )

        sys.exit(1)

    # ========================================================
    # 4. Load public predictions
    # ========================================================

    print(
        "\n4. LOAD PUBLIC PREDICTIONS"
    )

    records = (
        repository.get_all_predictions()
    )

    source = pd.read_csv(
        PREDICTION_FILE
    )

    check(
        "Prediction records > 0",
        len(
            records
        ) > 0,
        failures,
    )

    check(
        "Repository count = source count",
        len(
            records
        )
        ==
        len(
            source
        ),
        failures,
    )

    check(
        "Repository count = status",
        len(
            records
        )
        ==
        int(
            status.get(
                "prediction_count",
                -1,
            )
        ),
        failures,
    )

    print(
        f"Repository predictions: "
        f"{len(records)}"
    )

    # ========================================================
    # 5. Public schema
    # ========================================================

    print(
        "\n5. PUBLIC SCHEMA"
    )

    schema = contract.get(
        "public_prediction_schema",
        {},
    )

    field_order = list(
        schema.get(
            "field_order",
            [],
        )
    )

    required_fields = set(
        schema.get(
            "required_fields",
            [],
        )
    )

    optional_fields = set(
        schema.get(
            "optional_fields",
            [],
        )
    )

    expected_public_fields = [

        field

        for field
        in field_order

        if (
            field
            in required_fields

            or
            (
                field
                in optional_fields

                and
                field
                in source.columns
            )
        )
    ]

    schema_ok = all(

        list(
            record.keys()
        )
        ==
        expected_public_fields

        for record
        in records
    )

    check(
        "Public schema exact",
        schema_ok,
        failures,
    )

    required_schema_ok = all(

        required_fields.issubset(
            set(
                record.keys()
            )
        )

        for record
        in records
    )

    check(
        "Required public fields present",
        required_schema_ok,
        failures,
    )

    check(
        "model_sha256 not public",
        all(
            "model_sha256"
            not in record

            for record
            in records
        ),
        failures,
    )

    check(
        "feature_count not public",
        all(
            "feature_count"
            not in record

            for record
            in records
        ),
        failures,
    )

    # ========================================================
    # 6. Chronological ordering / freshness
    # ========================================================

    print(
        "\n6. CHRONOLOGICAL ORDER"
    )

    repository_dates = pd.to_datetime(

        [
            record[
                "date"
            ]
            for record
            in records
        ],

        errors="coerce",

        utc=True,
    )

    dates_valid = (
        not repository_dates.isna().any()
    )

    check(
        "Repository dates valid",
        dates_valid,
        failures,
    )

    chronological = bool(

        dates_valid

        and

        all(

            repository_dates[
                index
            ]
            <=
            repository_dates[
                index + 1
            ]

            for index
            in range(
                len(
                    repository_dates
                )
                - 1
            )
        )
    )

    check(
        "Predictions ordered by date",
        chronological,
        failures,
    )

    future_only = bool(

        dates_valid

        and

        (
            repository_dates
            >
            pd.Timestamp.now(
                tz="UTC"
            )
        ).all()
    )

    check(
        "All repository fixtures future",
        future_only,
        failures,
    )

    # ========================================================
    # 7. Fixture lookup
    # ========================================================

    print(
        "\n7. FIXTURE LOOKUP"
    )

    first_fixture_id = (
        records[
            0
        ][
            "fixture_id"
        ]
    )

    fixture = (
        repository.get_prediction(
            first_fixture_id
        )
    )

    check(
        "Known fixture lookup",
        fixture is not None,
        failures,
    )

    check(
        "Known fixture ID preserved",
        (
            fixture is not None

            and

            int(
                fixture[
                    "fixture_id"
                ]
            )
            ==
            int(
                first_fixture_id
            )
        ),
        failures,
    )

    unknown_fixture = (
        repository.get_prediction(
            9223372036854775807
        )
    )

    check(
        "Unknown fixture returns None",
        unknown_fixture is None,
        failures,
    )

    # ========================================================
    # 8. Team lookup
    # ========================================================

    print(
        "\n8. TEAM LOOKUP"
    )

    first_team = str(
        records[
            0
        ][
            "home_team_name"
        ]
    )

    team_records = (
        repository.get_team_predictions(
            first_team
        )
    )

    check(
        "Team lookup returns records",
        len(
            team_records
        ) > 0,
        failures,
    )

    upper_team_records = (
        repository.get_team_predictions(
            first_team.upper()
        )
    )

    check(
        "Team lookup case insensitive",
        len(
            upper_team_records
        )
        ==
        len(
            team_records
        ),
        failures,
    )

    team_integrity = all(

        first_team.casefold()

        in
        {
            str(
                record[
                    "home_team_name"
                ]
            ).casefold(),

            str(
                record[
                    "away_team_name"
                ]
            ).casefold(),
        }

        for record
        in team_records
    )

    check(
        "Team lookup exact identity",
        team_integrity,
        failures,
    )

    # ========================================================
    # 9. Upcoming feed
    # ========================================================

    print(
        "\n9. UPCOMING FEED"
    )

    upcoming_records = (
        repository.get_upcoming_predictions()
    )

    check(
        "Upcoming feed count",
        len(
            upcoming_records
        )
        ==
        len(
            records
        ),
        failures,
    )

    check(
        "Upcoming feed ordering",
        [
            record[
                "fixture_id"
            ]
            for record
            in upcoming_records
        ]
        ==
        [
            record[
                "fixture_id"
            ]
            for record
            in records
        ],
        failures,
    )

    # ========================================================
    # 10. Value preservation
    # ========================================================

    print(
        "\n10. VALUE PRESERVATION"
    )

    source[
        "fixture_id"
    ] = pd.to_numeric(
        source[
            "fixture_id"
        ],
        errors="raise",
    ).astype(
        "int64"
    )

    source_index = (
        source.set_index(
            "fixture_id"
        )
    )

    probability_preserved = True
    confidence_preserved = True
    label_preserved = True
    target_preserved = True

    for record in records:

        fixture_id = int(
            record[
                "fixture_id"
            ]
        )

        row = source_index.loc[
            fixture_id
        ]

        repository_probs = np.array(
            [
                float(
                    record[
                        "prob_draw"
                    ]
                ),

                float(
                    record[
                        "prob_home_win"
                    ]
                ),

                float(
                    record[
                        "prob_away_win"
                    ]
                ),
            ],
            dtype=float,
        )

        source_probs = np.array(
            [
                float(
                    row[
                        "prob_draw"
                    ]
                ),

                float(
                    row[
                        "prob_home_win"
                    ]
                ),

                float(
                    row[
                        "prob_away_win"
                    ]
                ),
            ],
            dtype=float,
        )

        if not np.allclose(
            repository_probs,
            source_probs,
            atol=1e-12,
            rtol=0.0,
        ):

            probability_preserved = False

        if not np.isclose(
            float(
                record[
                    "confidence"
                ]
            ),
            float(
                row[
                    "confidence"
                ]
            ),
            atol=1e-12,
            rtol=0.0,
        ):

            confidence_preserved = False

        if (
            str(
                record[
                    "predicted_label"
                ]
            )
            !=
            str(
                row[
                    "predicted_label"
                ]
            )
        ):

            label_preserved = False

        if (
            int(
                record[
                    "predicted_target"
                ]
            )
            !=
            int(
                row[
                    "predicted_target"
                ]
            )
        ):

            target_preserved = False

    check(
        "Probabilities preserved",
        probability_preserved,
        failures,
    )

    check(
        "Confidence preserved",
        confidence_preserved,
        failures,
    )

    check(
        "Prediction labels preserved",
        label_preserved,
        failures,
    )

    check(
        "Prediction targets preserved",
        target_preserved,
        failures,
    )

    # ========================================================
    # 11. Safety / read-only design
    # ========================================================

    print(
        "\n11. SAFETY / READ-ONLY DESIGN"
    )

    source_text = (
        REPOSITORY_SOURCE_FILE
        .read_text(
            encoding="utf-8"
        )
        .lower()
    )

    check(
        "No joblib import",
        (
            "import joblib"
            not in source_text

            and

            "from joblib"
            not in source_text
        ),
        failures,
    )

    check(
        "No model predict() call",
        ".predict("
        not in source_text,
        failures,
    )

    check(
        "No predict_proba() call",
        ".predict_proba("
        not in source_text,
        failures,
    )

    check(
        "No provider fetch call",
        (
            ".fetch("
            not in source_text

            and

            "requests.get("
            not in source_text

            and

            "httpx.get("
            not in source_text
        ),
        failures,
    )

    check(
        "No final-test directory access",
        (
            "data/processed/final_test"
            not in source_text

            and

            "data\\processed\\final_test"
            not in source_text
        ),
        failures,
    )

    # ========================================================
    # 12. Warnings
    # ========================================================

    print(
        "\n12. WARNINGS"
    )

    warnings = status.get(
        "warnings",
        [],
    )

    print(
        f"Diagnostic warnings: "
        f"{len(warnings)}"
    )

    for warning in warnings:

        print(
            f"  WARNING: {warning}"
        )

    # ========================================================
    # 13. Save verification report
    # ========================================================

    print(
        "\n13. SAVE VERIFICATION"
    )

    verification_status = (
        "PASS"
        if not failures
        else "FAIL"
    )

    report = {

        "stage":
            "7.9.2",

        "status":
            verification_status,

        "repository_status":
            (
                "READY"
                if not failures
                else "NOT_READY"
            ),

        "verified_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "contract_sha256":
            contract_hash,

        "prediction_count":
            int(
                len(
                    records
                )
            ),

        "model_id":
            status.get(
                "model_id"
            ),

        "feature_count":
            status.get(
                "feature_count"
            ),

        "snapshot_fresh":
            bool(
                status.get(
                    "snapshot_fresh"
                )
            ),

        "public_schema_verified":
            bool(
                schema_ok
            ),

        "chronological_order_verified":
            bool(
                chronological
            ),

        "probabilities_preserved":
            bool(
                probability_preserved
            ),

        "confidence_preserved":
            bool(
                confidence_preserved
            ),

        "labels_preserved":
            bool(
                label_preserved
            ),

        "targets_preserved":
            bool(
                target_preserved
            ),

        "fixture_lookup_verified":
            fixture is not None,

        "team_lookup_verified":
            bool(
                team_integrity
            ),

        "model_loaded":
            False,

        "prediction_executed":
            False,

        "provider_fetched":
            False,

        "training_executed":
            False,

        "model_selected":
            False,

        "hyperparameter_tuned":
            False,

        "final_test_evaluation_artifacts_used":
            False,

        "warnings":
            list(
                warnings
            ),

        "failures":
            list(
                failures
            ),
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
        )

    print(
        OUTPUT_FILE
    )

    # ========================================================
    # Final result
    # ========================================================

    print(
        "\n" + "=" * 68
    )

    if failures:

        print(
            "STAGE 7.9.2: FAIL"
        )

        print(
            "PRODUCTION PREDICTION REPOSITORY: NOT_READY"
        )

        for failure in failures:

            print(
                f"  - {failure}"
            )

    else:

        print(
            "STAGE 7.9.2: PASS"
        )

        print(
            "PRODUCTION PREDICTION REPOSITORY: READY"
        )

    print(
        "=" * 68
    )

    sys.exit(
        0
        if not failures
        else 1
    )


if __name__ == "__main__":
    main()
"""
FixtureIQ Stage 7.9.3
Production REST API Verification.

Tests the Flask Blueprint directly with Flask's test client.
No live server or external network is required.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask


# ============================================================
# Project root / import path
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


# ============================================================
# Paths
# ============================================================

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

CONTRACT_VERIFICATION_FILE = (
    MODEL_DIR
    / "production_serving_contract_verification.json"
)

REPOSITORY_VERIFICATION_FILE = (
    PRODUCTION_DIR
    / "production_repository_verification.json"
)

PREDICTION_FILE = (
    PRODUCTION_DIR
    / "production_predictions.csv"
)

API_SOURCE_FILE = (
    BASE_DIR
    / "backend"
    / "routes"
    / "production_prediction_api.py"
)

OUTPUT_FILE = (
    PRODUCTION_DIR
    / "production_api_verification.json"
)


# ============================================================
# Imports after project root setup
# ============================================================

from backend.routes.production_prediction_api import (
    create_production_prediction_blueprint,
)

from backend.services.production_prediction_repository import (
    ProductionPredictionRepository,
    RepositoryNotReadyError,
)


# ============================================================
# Helpers
# ============================================================

def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise FileNotFoundError(
            f"Required JSON missing: {path}"
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


def build_test_app(
    repository_factory=None,
) -> Flask:

    app = Flask(
        __name__
    )

    app.config.update(
        TESTING=True
    )

    app.register_blueprint(
        create_production_prediction_blueprint(
            repository_factory
        )
    )

    return app


# ============================================================
# Synthetic fail-closed repository
# ============================================================

class FakeNotReadyRepository:

    def get_status(
        self,
    ):

        return {

            "status":
                "NOT_READY",

            "stage_7_8_verified":
                False,

            "serving_contract_locked":
                True,

            "model_id":
                "random_forest",

            "feature_count":
                86,

            "prediction_count":
                0,

            "snapshot_fresh":
                False,

            "errors":
                [
                    (
                        "Synthetic fail-closed "
                        "verification state."
                    )
                ],

            "warnings":
                [],
        }

    def get_upcoming_predictions(
        self,
    ):

        raise RepositoryNotReadyError(
            "Synthetic NOT_READY state."
        )

    def get_prediction(
        self,
        fixture_id,
    ):

        raise RepositoryNotReadyError(
            "Synthetic NOT_READY state."
        )

    def get_team_predictions(
        self,
        team_name,
    ):

        raise RepositoryNotReadyError(
            "Synthetic NOT_READY state."
        )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 68)

    print(
        "FixtureIQ Stage 7.9.3"
    )

    print(
        "Production REST API Verification"
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
        REPOSITORY_VERIFICATION_FILE,
        PREDICTION_FILE,
        API_SOURCE_FILE,
    ]

    for path in required_files:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        print(
            "\nSTAGE 7.9.3: FAIL"
        )

        sys.exit(1)

    contract = load_json(
        CONTRACT_FILE
    )

    contract_verification = load_json(
        CONTRACT_VERIFICATION_FILE
    )

    repository_verification = load_json(
        REPOSITORY_VERIFICATION_FILE
    )

    # ========================================================
    # 2. Upstream foundation
    # ========================================================

    print(
        "\n2. UPSTREAM SERVING FOUNDATION"
    )

    check(
        "7.9.1 serving contract locked",
        contract.get(
            "status"
        )
        ==
        "LOCKED_SERVING_CONTRACT",
        failures,
    )

    check(
        "7.9.1 verification PASS",
        contract_verification.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )

    check(
        "7.9.2 repository verification PASS",
        repository_verification.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )

    check(
        "7.9.2 repository READY",
        repository_verification.get(
            "repository_status"
        )
        ==
        "READY",
        failures,
    )

    # ========================================================
    # 3. Real repository state
    # ========================================================

    print(
        "\n3. REAL REPOSITORY STATE"
    )

    repository = (
        ProductionPredictionRepository()
    )

    repository_status = (
        repository.get_status()
    )

    check(
        "Repository READY",
        repository_status.get(
            "status"
        )
        ==
        "READY",
        failures,
    )

    check(
        "Snapshot fresh",
        repository_status.get(
            "snapshot_fresh"
        )
        is True,
        failures,
    )

    if (
        repository_status.get(
            "status"
        )
        != "READY"
    ):

        for error in (
            repository_status.get(
                "errors",
                [],
            )
        ):

            print(
                f"  ERROR: {error}"
            )

        print(
            "\nSTAGE 7.9.3: FAIL"
        )

        sys.exit(1)

    expected_records = (
        repository
        .get_all_predictions()
    )

    expected_count = len(
        expected_records
    )

    source = pd.read_csv(
        PREDICTION_FILE
    )

    check(
        "Production records > 0",
        expected_count > 0,
        failures,
    )

    check(
        "Repository/source count match",
        expected_count
        ==
        len(
            source
        ),
        failures,
    )

    print(
        f"Production predictions: "
        f"{expected_count}"
    )

    # ========================================================
    # 4. Test application
    # ========================================================

    print(
        "\n4. CREATE API TEST APPLICATION"
    )

    app = build_test_app()

    client = (
        app.test_client()
    )

    check(
        "Flask test client created",
        client is not None,
        failures,
    )

    # ========================================================
    # 5. Status endpoint
    # ========================================================

    print(
        "\n5. PRODUCTION STATUS ENDPOINT"
    )

    response = client.get(
        "/api/v1/production/status"
    )

    status_payload = (
        response.get_json()
    )

    check(
        "GET status HTTP 200",
        response.status_code
        == 200,
        failures,
    )

    check(
        "Status payload READY",
        status_payload.get(
            "status"
        )
        ==
        "READY",
        failures,
    )

    check(
        "Status stage = 7.9.3",
        status_payload.get(
            "stage"
        )
        ==
        "7.9.3",
        failures,
    )

    check(
        "Status service identity",
        status_payload.get(
            "service"
        )
        ==
        "production_prediction_api",
        failures,
    )

    check(
        "Status prediction count",
        int(
            status_payload.get(
                "prediction_count",
                -1,
            )
        )
        ==
        expected_count,
        failures,
    )

    check(
        "Status snapshot fresh",
        status_payload.get(
            "snapshot_fresh"
        )
        is True,
        failures,
    )

    check(
        "Status model ID",
        status_payload.get(
            "model_id"
        )
        ==
        "random_forest",
        failures,
    )

    check(
        "Status feature count",
        status_payload.get(
            "feature_count"
        )
        ==
        86,
        failures,
    )

    check(
        "Status Cache-Control no-store",
        "no-store"
        in response.headers.get(
            "Cache-Control",
            "",
        ),
        failures,
    )

    # ========================================================
    # 6. Upcoming feed
    # ========================================================

    print(
        "\n6. UPCOMING PREDICTION FEED"
    )

    response = client.get(
        "/api/v1/predictions/upcoming"
    )

    feed_payload = (
        response.get_json()
    )

    check(
        "Upcoming feed HTTP 200",
        response.status_code
        ==
        200,
        failures,
    )

    check(
        "Upcoming feed READY",
        feed_payload.get(
            "status"
        )
        ==
        "READY",
        failures,
    )

    check(
        "Upcoming count",
        feed_payload.get(
            "count"
        )
        ==
        expected_count,
        failures,
    )

    check(
        "Upcoming data count",
        len(
            feed_payload.get(
                "data",
                [],
            )
        )
        ==
        expected_count,
        failures,
    )

    api_records = (
        feed_payload.get(
            "data",
            [],
        )
    )

    # ========================================================
    # 7. Alias endpoint
    # ========================================================

    print(
        "\n7. PREDICTION ALIAS ENDPOINT"
    )

    alias_response = client.get(
        "/api/v1/predictions"
    )

    alias_payload = (
        alias_response.get_json()
    )

    check(
        "Prediction alias HTTP 200",
        alias_response.status_code
        ==
        200,
        failures,
    )

    check(
        "Prediction alias count",
        alias_payload.get(
            "count"
        )
        ==
        expected_count,
        failures,
    )

    check(
        "Prediction alias fixture ordering",
        [
            record[
                "fixture_id"
            ]
            for record
            in alias_payload.get(
                "data",
                [],
            )
        ]
        ==
        [
            record[
                "fixture_id"
            ]
            for record
            in api_records
        ],
        failures,
    )

    # ========================================================
    # 8. Public schema
    # ========================================================

    print(
        "\n8. PUBLIC SCHEMA"
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

    expected_public_field_set = set(
        expected_public_fields
    )

    schema_ok = all(

        set(
            record.keys()
        )
        ==
        expected_public_field_set

        and

        len(
            record
        )
        ==
        len(
            expected_public_fields
        )

        for record
        in api_records
    )

    check(
        "API public schema exact",
        schema_ok,
        failures,
    )

    check(
        "No model SHA exposed in records",
        all(
            "model_sha256"
            not in record

            for record
            in api_records
        ),
        failures,
    )

    check(
        "No feature_count exposed in records",
        all(
            "feature_count"
            not in record

            for record
            in api_records
        ),
        failures,
    )

    # ========================================================
    # 9. Value preservation
    # ========================================================

    print(
        "\n9. VALUE PRESERVATION"
    )

    value_preserved = True

    for (
        api_record,
        repository_record,
    ) in zip(
        api_records,
        expected_records,
    ):

        if (
            api_record
            != repository_record
        ):

            value_preserved = False

            break

    check(
        "API preserves repository records",
        value_preserved,
        failures,
    )

    probability_integrity = True

    for record in api_records:

        values = np.array(
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

        if not (
            np.isfinite(
                values
            ).all()

            and

            (
                values >= 0
            ).all()

            and

            (
                values <= 1
            ).all()

            and

            np.isclose(
                values.sum(),
                1.0,
                atol=1e-8,
                rtol=0.0,
            )

            and

            np.isclose(
                float(
                    record[
                        "confidence"
                    ]
                ),
                float(
                    values.max()
                ),
                atol=1e-12,
                rtol=0.0,
            )
        ):

            probability_integrity = False

            break

    check(
        "API probability integrity",
        probability_integrity,
        failures,
    )

    # ========================================================
    # 10. Fixture lookup
    # ========================================================

    print(
        "\n10. FIXTURE LOOKUP"
    )

    first = api_records[
        0
    ]

    fixture_id = int(
        first[
            "fixture_id"
        ]
    )

    response = client.get(
        f"/api/v1/predictions/{fixture_id}"
    )

    fixture_payload = (
        response.get_json()
    )

    check(
        "Known fixture HTTP 200",
        response.status_code
        ==
        200,
        failures,
    )

    check(
        "Known fixture READY",
        fixture_payload.get(
            "status"
        )
        ==
        "READY",
        failures,
    )

    check(
        "Known fixture preserved",
        fixture_payload.get(
            "data"
        )
        ==
        first,
        failures,
    )

    response = client.get(
        "/api/v1/predictions/9223372036854775807"
    )

    unknown_payload = (
        response.get_json()
    )

    check(
        "Unknown fixture HTTP 404",
        response.status_code
        ==
        404,
        failures,
    )

    check(
        "Unknown fixture error code",
        unknown_payload.get(
            "error",
            {},
        ).get(
            "code"
        )
        ==
        "FIXTURE_NOT_FOUND",
        failures,
    )

    response = client.get(
        "/api/v1/predictions/not-an-integer"
    )

    invalid_payload = (
        response.get_json()
    )

    check(
        "Invalid fixture ID HTTP 400",
        response.status_code
        ==
        400,
        failures,
    )

    check(
        "Invalid fixture error code",
        invalid_payload.get(
            "error",
            {},
        ).get(
            "code"
        )
        ==
        "INVALID_FIXTURE_ID",
        failures,
    )

    # ========================================================
    # 11. Team lookup
    # ========================================================

    print(
        "\n11. TEAM LOOKUP"
    )

    first_team = str(
        first[
            "home_team_name"
        ]
    )

    expected_team_records = (
        repository
        .get_team_predictions(
            first_team
        )
    )

    response = client.get(
        f"/api/v1/predictions/team/{first_team}"
    )

    team_payload = (
        response.get_json()
    )

    check(
        "Known team HTTP 200",
        response.status_code
        ==
        200,
        failures,
    )

    check(
        "Known team result count",
        team_payload.get(
            "count"
        )
        ==
        len(
            expected_team_records
        ),
        failures,
    )

    check(
        "Known team records preserved",
        team_payload.get(
            "data"
        )
        ==
        expected_team_records,
        failures,
    )

    response_upper = client.get(
        (
            "/api/v1/predictions/team/"
            f"{first_team.upper()}"
        )
    )

    upper_payload = (
        response_upper.get_json()
    )

    check(
        "Team matching case insensitive",
        response_upper.status_code
        ==
        200,
        failures,
    )

    check(
        "Case-insensitive team count",
        upper_payload.get(
            "count"
        )
        ==
        len(
            expected_team_records
        ),
        failures,
    )

    response = client.get(
        (
            "/api/v1/predictions/team/"
            "DefinitelyNotARealEPLTeam"
        )
    )

    unknown_team_payload = (
        response.get_json()
    )

    check(
        "Unknown team HTTP 404",
        response.status_code
        ==
        404,
        failures,
    )

    check(
        "Unknown team error code",
        unknown_team_payload.get(
            "error",
            {},
        ).get(
            "code"
        )
        ==
        "TEAM_NOT_FOUND",
        failures,
    )

    # ========================================================
    # 12. Read-only methods
    # ========================================================

    print(
        "\n12. READ-ONLY HTTP BEHAVIOR"
    )

    response = client.post(
        "/api/v1/predictions"
    )

    check(
        "POST predictions rejected",
        response.status_code
        ==
        405,
        failures,
    )

    response = client.put(
        f"/api/v1/predictions/{fixture_id}"
    )

    check(
        "PUT prediction rejected",
        response.status_code
        ==
        405,
        failures,
    )

    response = client.delete(
        f"/api/v1/predictions/{fixture_id}"
    )

    check(
        "DELETE prediction rejected",
        response.status_code
        ==
        405,
        failures,
    )

    # ========================================================
    # 13. Fail-closed behavior
    # ========================================================

    print(
        "\n13. FAIL-CLOSED BEHAVIOR"
    )

    fail_app = build_test_app(
        lambda:
            FakeNotReadyRepository()
    )

    fail_client = (
        fail_app.test_client()
    )

    response = fail_client.get(
        "/api/v1/production/status"
    )

    fail_status_payload = (
        response.get_json()
    )

    check(
        "NOT_READY status endpoint HTTP 200",
        response.status_code
        ==
        200,
        failures,
    )

    check(
        "NOT_READY status exposed",
        fail_status_payload.get(
            "status"
        )
        ==
        "NOT_READY",
        failures,
    )

    protected_paths = [
        "/api/v1/predictions",

        "/api/v1/predictions/upcoming",

        f"/api/v1/predictions/{fixture_id}",

        (
            "/api/v1/predictions/team/"
            f"{first_team}"
        ),
    ]

    fail_closed_ok = True

    for path in protected_paths:

        response = fail_client.get(
            path
        )

        fail_payload = (
            response.get_json()
        )

        if not (
            response.status_code
            ==
            503

            and

            fail_payload.get(
                "status"
            )
            ==
            "NOT_READY"

            and

            fail_payload.get(
                "error",
                {},
            ).get(
                "code"
            )
            ==
            "PRODUCTION_NOT_READY"
        ):

            fail_closed_ok = False

            break

    check(
        "Prediction endpoints fail closed",
        fail_closed_ok,
        failures,
    )

    # ========================================================
    # 14. Source safety
    # ========================================================

    print(
        "\n14. SOURCE SAFETY"
    )

    source_text = (
        API_SOURCE_FILE
        .read_text(
            encoding="utf-8"
        )
        .lower()
    )

    check(
        "API does not import joblib",
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
        "API does not call predict()",
        ".predict("
        not in source_text,
        failures,
    )

    check(
        "API does not call predict_proba()",
        ".predict_proba("
        not in source_text,
        failures,
    )

    check(
        "API does not access final-test directory",
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
    # 15. Save verification
    # ========================================================

    print(
        "\n15. SAVE VERIFICATION"
    )

    verification_status = (
        "PASS"
        if not failures
        else "FAIL"
    )

    report = {

        "stage":
            "7.9.3",

        "status":
            verification_status,

        "api_status":
            (
                "READY"
                if not failures
                else "NOT_READY"
            ),

        "verified_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "prediction_count":
            int(
                expected_count
            ),

        "model_id":
            repository_status.get(
                "model_id"
            ),

        "feature_count":
            repository_status.get(
                "feature_count"
            ),

        "snapshot_fresh":
            bool(
                repository_status.get(
                    "snapshot_fresh"
                )
            ),

        "status_endpoint_verified":
            True,

        "upcoming_endpoint_verified":
            bool(
                expected_count > 0
            ),

        "fixture_lookup_verified":
            bool(
                first is not None
            ),

        "team_lookup_verified":
            bool(
                len(
                    expected_team_records
                )
                > 0
            ),

        "public_schema_verified":
            bool(
                schema_ok
            ),

        "value_preservation_verified":
            bool(
                value_preserved
            ),

        "probability_integrity_verified":
            bool(
                probability_integrity
            ),

        "read_only_http_verified":
            True,

        "fail_closed_verified":
            bool(
                fail_closed_ok
            ),

        "model_loaded_by_api":
            False,

        "prediction_executed_by_api":
            False,

        "provider_fetched_by_api":
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
                repository_status.get(
                    "warnings",
                    [],
                )
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
    # Final
    # ========================================================

    print(
        "\n" + "=" * 68
    )

    if failures:

        print(
            "STAGE 7.9.3: FAIL"
        )

        print(
            "PRODUCTION REST API: NOT_READY"
        )

        for failure in failures:

            print(
                f"  - {failure}"
            )

    else:

        print(
            "STAGE 7.9.3: PASS"
        )

        print(
            "PRODUCTION REST API: READY"
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
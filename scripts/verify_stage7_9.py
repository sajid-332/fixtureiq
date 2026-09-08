"""
FixtureIQ Stage 7.9.5
Final Stage 7.9 Production Serving Verification Gate.

Verifies the complete production serving stack:

7.9.1 Production Serving Contract
7.9.2 Production Prediction Repository
7.9.3 Production REST API
7.9.4 Runtime Safety / Serving Guard
7.9.5 Final End-to-End Gate

This verifier:
- does not train
- does not retrain
- does not tune
- does not select models
- does not execute predict()
- does not execute predict_proba()
- does not fetch provider data
- does not build features
- does not access final-test evaluation artifacts

Only the final verification JSON artifact is written.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from flask import Flask


# ============================================================
# Project root
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

API_VERIFICATION_FILE = (
    PRODUCTION_DIR
    / "production_api_verification.json"
)

RUNTIME_VERIFICATION_FILE = (
    PRODUCTION_DIR
    / "production_runtime_safety_verification.json"
)

STAGE7_8_VERIFICATION_FILE = (
    PRODUCTION_DIR
    / "stage7_8_final_verification.json"
)

PREDICTIONS_FILE = (
    PRODUCTION_DIR
    / "production_predictions.csv"
)

API_SOURCE_FILE = (
    BASE_DIR
    / "backend"
    / "routes"
    / "production_prediction_api.py"
)

REPOSITORY_SOURCE_FILE = (
    BASE_DIR
    / "backend"
    / "services"
    / "production_prediction_repository.py"
)

APP_SOURCE_FILE = (
    BASE_DIR
    / "backend"
    / "app.py"
)

OUTPUT_FILE = (
    PRODUCTION_DIR
    / "stage7_9_final_verification.json"
)


# ============================================================
# Serving repository
# ============================================================

from backend.services.production_prediction_repository import (
    ProductionPredictionRepository,
)


# ============================================================
# Helpers
# ============================================================

def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise FileNotFoundError(
            f"Required artifact missing: {path}"
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


def get_real_flask_app():
    """
    Resolve the real production Flask application.

    Supports either:

    backend.app:app

    or:

    backend.app:create_app()
    """

    module = importlib.import_module(
        "backend.app"
    )

    direct_app = getattr(
        module,
        "app",
        None,
    )

    if isinstance(
        direct_app,
        Flask,
    ):

        return (
            direct_app,
            "backend.app:app",
        )

    create_app = getattr(
        module,
        "create_app",
        None,
    )

    if callable(
        create_app
    ):

        candidate = (
            create_app()
        )

        if isinstance(
            candidate,
            Flask,
        ):

            return (
                candidate,
                "backend.app:create_app",
            )

    raise RuntimeError(
        (
            "Could not resolve Flask app from backend.app. "
            "Expected either `app` or `create_app()`."
        )
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 7.9.5"
    )

    print(
        "Final Stage 7.9 Production Serving Verification"
    )

    print("=" * 72)

    failures = []

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
        API_VERIFICATION_FILE,
        RUNTIME_VERIFICATION_FILE,
        STAGE7_8_VERIFICATION_FILE,
        PREDICTIONS_FILE,
        API_SOURCE_FILE,
        REPOSITORY_SOURCE_FILE,
        APP_SOURCE_FILE,
    ]

    for path in required_files:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        print(
            "\n" + "=" * 72
        )

        print(
            "STAGE 7.9.5: FAIL"
        )

        print(
            "STAGE 7.9: INCOMPLETE"
        )

        print("=" * 72)

        sys.exit(1)

    # ========================================================
    # 2. Load upstream verification artifacts
    # ========================================================

    contract_verification = load_json(
        CONTRACT_VERIFICATION_FILE
    )

    repository_verification = load_json(
        REPOSITORY_VERIFICATION_FILE
    )

    api_verification = load_json(
        API_VERIFICATION_FILE
    )

    runtime_verification = load_json(
        RUNTIME_VERIFICATION_FILE
    )

    # ========================================================
    # 3. Stage 7.9.1
    # ========================================================

    print(
        "\n2. STAGE 7.9.1 - SERVING CONTRACT"
    )

    stage_7_9_1_pass = check(
        "7.9.1 verification PASS",
        contract_verification.get(
            "status"
        )
        == "PASS",
        failures,
    )

    # ========================================================
    # 4. Stage 7.9.2
    # ========================================================

    print(
        "\n3. STAGE 7.9.2 - PREDICTION REPOSITORY"
    )

    stage_7_9_2_pass = check(
        "7.9.2 verification PASS",
        repository_verification.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "7.9.2 repository READY",
        repository_verification.get(
            "repository_status"
        )
        == "READY",
        failures,
    )

    # ========================================================
    # 5. Stage 7.9.3
    # ========================================================

    print(
        "\n4. STAGE 7.9.3 - PRODUCTION REST API"
    )

    stage_7_9_3_pass = check(
        "7.9.3 verification PASS",
        api_verification.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "7.9.3 API READY",
        api_verification.get(
            "api_status"
        )
        == "READY",
        failures,
    )

    # ========================================================
    # 6. Stage 7.9.4
    # ========================================================

    print(
        "\n5. STAGE 7.9.4 - RUNTIME SAFETY"
    )

    stage_7_9_4_pass = check(
        "7.9.4 verification PASS",
        runtime_verification.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "7.9.4 runtime SAFE",
        runtime_verification.get(
            "runtime_status"
        )
        == "SAFE",
        failures,
    )

    check(
        "7.9.4 stale rejection verified",
        runtime_verification.get(
            "stale_snapshot_rejection_verified"
        )
        is True,
        failures,
    )

    check(
        "7.9.4 artifact reload verified",
        runtime_verification.get(
            "artifact_change_reload_verified"
        )
        is True,
        failures,
    )

    # ========================================================
    # 7. Real repository state
    # ========================================================

    print(
        "\n6. REAL PRODUCTION REPOSITORY"
    )

    repository = (
        ProductionPredictionRepository()
    )

    repository_status = (
        repository.get_status()
    )

    repository_ready = check(
        "Repository READY",
        repository_status.get(
            "status"
        )
        == "READY",
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

    check(
        "Stage 7.8 verified",
        repository_status.get(
            "stage_7_8_verified"
        )
        is True,
        failures,
    )

    check(
        "Serving contract locked",
        repository_status.get(
            "serving_contract_locked"
        )
        is True,
        failures,
    )

    check(
        "Model ID random_forest",
        repository_status.get(
            "model_id"
        )
        == "random_forest",
        failures,
    )

    check(
        "Feature count = 86",
        int(
            repository_status.get(
                "feature_count",
                0,
            )
            or 0
        )
        == 86,
        failures,
    )

    predictions = (
        repository
        .get_upcoming_predictions()
    )

    prediction_count = len(
        predictions
    )

    check(
        "Production predictions > 0",
        prediction_count
        > 0,
        failures,
    )

    check(
        "Repository count matches records",
        int(
            repository_status.get(
                "prediction_count",
                0,
            )
            or 0
        )
        == prediction_count,
        failures,
    )

    print(
        f"Production predictions: {prediction_count}"
    )

    # ========================================================
    # 8. Real Flask application integration
    # ========================================================

    print(
        "\n7. REAL FLASK APPLICATION INTEGRATION"
    )

    real_app = None
    app_source = None

    try:

        (
            real_app,
            app_source,
        ) = get_real_flask_app()

        check(
            "Flask application resolved",
            True,
            failures,
        )

        print(
            f"Application source: {app_source}"
        )

    except Exception as exc:

        check(
            "Flask application resolved",
            False,
            failures,
        )

        print(
            f"Application resolution error: {exc}"
        )

    required_routes = {
        "/api/v1/production/status",
        "/api/v1/production/health",
        "/api/v1/production/readiness",
        "/api/v1/predictions",
        "/api/v1/predictions/upcoming",
        "/api/v1/predictions/<fixture_id>",
        "/api/v1/predictions/team/<path:team_name>",
    }

    route_strings = set()

    if real_app is not None:

        route_strings = {
            str(
                rule
            )
            for rule in real_app.url_map.iter_rules()
        }

    for route in sorted(
        required_routes
    ):

        check(
            f"Route registered: {route}",
            route in route_strings,
            failures,
        )

    # ========================================================
    # 9. End-to-end real API calls
    # ========================================================

    print(
        "\n8. END-TO-END REAL API"
    )

    if real_app is not None:

        client = (
            real_app.test_client()
        )

        # ----------------------------------------------------
        # Health
        # ----------------------------------------------------

        health_response = client.get(
            "/api/v1/production/health"
        )

        health_payload = (
            health_response.get_json()
            or {}
        )

        check(
            "Health HTTP 200",
            health_response.status_code
            == 200,
            failures,
        )

        check(
            "Health ALIVE",
            health_payload.get(
                "status"
            )
            == "ALIVE",
            failures,
        )

        # ----------------------------------------------------
        # Readiness
        # ----------------------------------------------------

        readiness_response = client.get(
            "/api/v1/production/readiness"
        )

        readiness_payload = (
            readiness_response.get_json()
            or {}
        )

        check(
            "Readiness HTTP 200",
            readiness_response.status_code
            == 200,
            failures,
        )

        check(
            "Readiness READY",
            readiness_payload.get(
                "status"
            )
            == "READY",
            failures,
        )

        # ----------------------------------------------------
        # Production status
        # ----------------------------------------------------

        status_response = client.get(
            "/api/v1/production/status"
        )

        status_payload = (
            status_response.get_json()
            or {}
        )

        check(
            "Status HTTP 200",
            status_response.status_code
            == 200,
            failures,
        )

        check(
            "Status READY",
            status_payload.get(
                "status"
            )
            == "READY",
            failures,
        )

        # ----------------------------------------------------
        # Upcoming feed
        # ----------------------------------------------------

        feed_response = client.get(
            "/api/v1/predictions/upcoming"
        )

        feed_payload = (
            feed_response.get_json()
            or {}
        )

        check(
            "Prediction feed HTTP 200",
            feed_response.status_code
            == 200,
            failures,
        )

        check(
            "Prediction feed READY",
            feed_payload.get(
                "status"
            )
            == "READY",
            failures,
        )

        check(
            "Prediction feed count matches repository",
            int(
                feed_payload.get(
                    "count",
                    -1,
                )
            )
            == prediction_count,
            failures,
        )

        # ----------------------------------------------------
        # Safety headers
        # ----------------------------------------------------

        check(
            "Cache-Control no-store",
            feed_response.headers.get(
                "Cache-Control"
            )
            == "no-store",
            failures,
        )

        check(
            "X-Content-Type-Options nosniff",
            feed_response.headers.get(
                "X-Content-Type-Options"
            )
            == "nosniff",
            failures,
        )

        # ----------------------------------------------------
        # Known fixture
        # ----------------------------------------------------

        if predictions:

            first_record = (
                predictions[
                    0
                ]
            )

            known_fixture_id = (
                first_record[
                    "fixture_id"
                ]
            )

            fixture_response = client.get(
                (
                    "/api/v1/predictions/"
                    f"{known_fixture_id}"
                )
            )

            fixture_payload = (
                fixture_response.get_json()
                or {}
            )

            fixture_data = (
                fixture_payload.get(
                    "data",
                    {}
                )
            )

            check(
                "Known fixture HTTP 200",
                fixture_response.status_code
                == 200,
                failures,
            )

            check(
                "Known fixture preserved",
                str(
                    fixture_data.get(
                        "fixture_id"
                    )
                )
                == str(
                    known_fixture_id
                ),
                failures,
            )

            # ------------------------------------------------
            # Known team
            # ------------------------------------------------

            team_name = str(
                first_record[
                    "home_team_name"
                ]
            )

            encoded_team = quote(
                team_name,
                safe="",
            )

            team_response = client.get(
                (
                    "/api/v1/predictions/team/"
                    f"{encoded_team}"
                )
            )

            team_payload = (
                team_response.get_json()
                or {}
            )

            expected_team_records = (
                repository
                .get_team_predictions(
                    team_name
                )
            )

            check(
                "Known team HTTP 200",
                team_response.status_code
                == 200,
                failures,
            )

            check(
                "Known team count preserved",
                int(
                    team_payload.get(
                        "count",
                        -1,
                    )
                )
                == len(
                    expected_team_records
                ),
                failures,
            )

        # ----------------------------------------------------
        # Read-only HTTP behavior
        # ----------------------------------------------------

        post_response = client.post(
            "/api/v1/predictions"
        )

        check(
            "POST predictions rejected",
            post_response.status_code
            == 405,
            failures,
        )

    else:

        check(
            "End-to-end API available",
            False,
            failures,
        )

    # ========================================================
    # 10. Serving source safety
    # ========================================================

    print(
        "\n9. FINAL SERVING SAFETY"
    )

    api_source_text = (
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
            not in api_source_text
            and
            "from joblib"
            not in api_source_text
        ),
        failures,
    )

    check(
        "API does not call predict()",
        ".predict("
        not in api_source_text,
        failures,
    )

    check(
        "API does not call predict_proba()",
        ".predict_proba("
        not in api_source_text,
        failures,
    )

    check(
        "API does not access final-test evaluation path",
        (
            "data/processed/final_test"
            not in api_source_text
            and
            "data\\processed\\final_test"
            not in api_source_text
        ),
        failures,
    )

    check(
        "7.9.4 says runtime API is read-only",
        runtime_verification.get(
            "read_only"
        )
        is True,
        failures,
    )

    check(
        "7.9.4 says model not loaded by API",
        runtime_verification.get(
            "model_loaded_by_runtime_api"
        )
        is False,
        failures,
    )

    check(
        "7.9.4 says predictions not executed by API",
        runtime_verification.get(
            "prediction_executed_by_runtime_api"
        )
        is False,
        failures,
    )

    check(
        "7.9.4 says provider not fetched",
        runtime_verification.get(
            "provider_fetched"
        )
        is False,
        failures,
    )

    check(
        "7.9.4 says no training",
        runtime_verification.get(
            "training_executed"
        )
        is False,
        failures,
    )

    check(
        "7.9.4 says no model selection",
        runtime_verification.get(
            "model_selected"
        )
        is False,
        failures,
    )

    check(
        "7.9.4 says no tuning",
        runtime_verification.get(
            "hyperparameter_tuned"
        )
        is False,
        failures,
    )

    check(
        "7.9.4 says no final-test evaluation artifact use",
        runtime_verification.get(
            "final_test_evaluation_artifacts_used"
        )
        is False,
        failures,
    )

    # ========================================================
    # 11. Evidence hashes
    # ========================================================

    print(
        "\n10. EVIDENCE HASHES"
    )

    evidence_files = {
        "production_serving_contract":
            CONTRACT_FILE,

        "serving_contract_verification":
            CONTRACT_VERIFICATION_FILE,

        "repository_verification":
            REPOSITORY_VERIFICATION_FILE,

        "api_verification":
            API_VERIFICATION_FILE,

        "runtime_safety_verification":
            RUNTIME_VERIFICATION_FILE,

        "stage7_8_final_verification":
            STAGE7_8_VERIFICATION_FILE,

        "production_predictions":
            PREDICTIONS_FILE,

        "prediction_repository_source":
            REPOSITORY_SOURCE_FILE,

        "prediction_api_source":
            API_SOURCE_FILE,

        "flask_app_source":
            APP_SOURCE_FILE,
    }

    evidence_hashes = {}

    for name, path in evidence_files.items():

        digest = sha256_file(
            path
        )

        evidence_hashes[
            name
        ] = digest

        print(
            f"{name}: {digest}"
        )

    # ========================================================
    # 12. Final result
    # ========================================================

    print(
        "\n11. FINAL STAGE 7.9 DECISION"
    )

    stage_7_9_complete = bool(
        not failures
        and
        stage_7_9_1_pass
        and
        stage_7_9_2_pass
        and
        stage_7_9_3_pass
        and
        stage_7_9_4_pass
        and
        repository_ready
    )

    final_status = (
        "PASS"
        if stage_7_9_complete
        else "FAIL"
    )

    serving_status = (
        "VERIFIED"
        if stage_7_9_complete
        else "NOT_VERIFIED"
    )

    # ========================================================
    # 13. Save final artifact
    # ========================================================

    report = {

        "stage":
            "7.9.5",

        "status":
            final_status,

        "stage_7_9_complete":
            stage_7_9_complete,

        "stage_7_9_status":
            (
                "COMPLETE"
                if stage_7_9_complete
                else "INCOMPLETE"
            ),

        "production_serving_stack":
            serving_status,

        "verified_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "sub_stages":
            {
                "7.9.1":
                    (
                        "PASS"
                        if stage_7_9_1_pass
                        else "FAIL"
                    ),

                "7.9.2":
                    (
                        "PASS"
                        if stage_7_9_2_pass
                        else "FAIL"
                    ),

                "7.9.3":
                    (
                        "PASS"
                        if stage_7_9_3_pass
                        else "FAIL"
                    ),

                "7.9.4":
                    (
                        "PASS"
                        if stage_7_9_4_pass
                        else "FAIL"
                    ),

                "7.9.5":
                    final_status,
            },

        "repository":
            {
                "status":
                    repository_status.get(
                        "status"
                    ),

                "snapshot_fresh":
                    repository_status.get(
                        "snapshot_fresh"
                    ),

                "stage_7_8_verified":
                    repository_status.get(
                        "stage_7_8_verified"
                    ),

                "serving_contract_locked":
                    repository_status.get(
                        "serving_contract_locked"
                    ),

                "model_id":
                    repository_status.get(
                        "model_id"
                    ),

                "feature_count":
                    repository_status.get(
                        "feature_count"
                    ),

                "prediction_count":
                    prediction_count,
            },

        "application":
            {
                "source":
                    app_source,

                "required_routes":
                    sorted(
                        required_routes
                    ),

                "required_routes_verified":
                    required_routes
                    .issubset(
                        route_strings
                    ),
            },

        "safety":
            {
                "read_only":
                    True,

                "fail_closed":
                    True,

                "model_loaded_by_api":
                    False,

                "prediction_executed_by_api":
                    False,

                "provider_fetched_by_api":
                    False,

                "training_executed":
                    False,

                "model_selection_executed":
                    False,

                "hyperparameter_tuning_executed":
                    False,

                "final_test_evaluation_artifacts_used":
                    False,
            },

        "evidence_sha256":
            evidence_hashes,

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
        f"Final verification artifact: {OUTPUT_FILE}"
    )

    # ========================================================
    # Final console output
    # ========================================================

    print(
        "\n" + "=" * 72
    )

    if stage_7_9_complete:

        print(
            "STAGE 7.9.5: PASS"
        )

        print(
            "STAGE 7.9: COMPLETE"
        )

        print(
            "PRODUCTION SERVING STACK: VERIFIED"
        )

    else:

        print(
            "STAGE 7.9.5: FAIL"
        )

        print(
            "STAGE 7.9: INCOMPLETE"
        )

        print(
            "PRODUCTION SERVING STACK: NOT VERIFIED"
        )

        if failures:

            print(
                "\nFailures:"
            )

            for failure in failures:

                print(
                    f"  - {failure}"
                )

    print(
        "=" * 72
    )

    sys.exit(
        0
        if stage_7_9_complete
        else 1
    )


if __name__ == "__main__":

    main()
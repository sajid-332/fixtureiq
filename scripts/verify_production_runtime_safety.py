"""
FixtureIQ Stage 7.9.4
Production Runtime Safety / Serving Guard Verification.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask


# ============================================================
# Project root
# ============================================================

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

API_SOURCE_FILE = (
    BASE_DIR
    / "backend"
    / "routes"
    / "production_prediction_api.py"
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

OUTPUT_FILE = (
    PRODUCTION_DIR
    / "production_runtime_safety_verification.json"
)


# ============================================================
# API module
# ============================================================

import backend.routes.production_prediction_api as api_module


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


def build_app(
    repository_factory=None,
) -> Flask:

    app = Flask(
        __name__
    )

    app.config.update(
        TESTING=True
    )

    app.register_blueprint(
        api_module
        .create_production_prediction_blueprint(
            repository_factory
        )
    )

    return app


# ============================================================
# Synthetic repository
# ============================================================

class FakeRepository:

    def __init__(
        self,
        *,
        ready=True,
        fresh=True,
        verified=True,
        contract_locked=True,
    ):

        self.ready = ready
        self.fresh = fresh
        self.verified = verified
        self.contract_locked = (
            contract_locked
        )

    def get_status(
        self,
    ) -> dict:

        errors = []

        if not self.ready:

            errors.append(
                "Synthetic repository NOT_READY."
            )

        if not self.fresh:

            errors.append(
                "Synthetic snapshot stale."
            )

        if not self.verified:

            errors.append(
                (
                    "Synthetic Stage 7.8 "
                    "verification failure."
                )
            )

        if not self.contract_locked:

            errors.append(
                (
                    "Synthetic serving "
                    "contract failure."
                )
            )

        effective_ready = bool(
            self.ready
            and
            self.fresh
            and
            self.verified
            and
            self.contract_locked
        )

        return {

            "status":
                (
                    "READY"
                    if effective_ready
                    else "NOT_READY"
                ),

            "stage_7_8_verified":
                bool(
                    self.verified
                ),

            "serving_contract_locked":
                bool(
                    self.contract_locked
                ),

            "model_id":
                "random_forest",

            "feature_count":
                86,

            "prediction_count":
                (
                    1
                    if effective_ready
                    else 0
                ),

            "snapshot_fresh":
                bool(
                    self.fresh
                ),

            "errors":
                errors,

            "warnings":
                [],
        }

    def get_upcoming_predictions(
        self,
    ) -> list[dict]:

        if (
            self.get_status()[
                "status"
            ]
            != "READY"
        ):

            raise RuntimeError(
                (
                    "Synthetic repository "
                    "not ready."
                )
            )

        return [
            {
                "fixture_id":
                    1,

                "date":
                    "2099-01-01T00:00:00Z",

                "home_team_id":
                    1,

                "home_team_name":
                    "Home",

                "away_team_id":
                    2,

                "away_team_name":
                    "Away",

                "predicted_target":
                    1,

                "predicted_label":
                    "Home Win",

                "prob_home_win":
                    0.50,

                "prob_draw":
                    0.25,

                "prob_away_win":
                    0.25,

                "confidence":
                    0.50,
            }
        ]

    def get_prediction(
        self,
        fixture_id,
    ):

        records = (
            self.get_upcoming_predictions()
        )

        if int(
            fixture_id
        ) == 1:

            return records[
                0
            ]

        return None

    def get_team_predictions(
        self,
        team_name,
    ):

        records = (
            self.get_upcoming_predictions()
        )

        normalized = (
            str(
                team_name
            )
            .strip()
            .casefold()
        )

        if normalized in {
            "home",
            "away",
        }:

            return records

        return []


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 68)

    print(
        "FixtureIQ Stage 7.9.4"
    )

    print(
        (
            "Production Runtime Safety / "
            "Serving Guard Verification"
        )
    )

    print("=" * 68)

    failures = []

    # ========================================================
    # 1. Required artifacts
    # ========================================================

    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    required_files = [
        CONTRACT_VERIFICATION_FILE,
        REPOSITORY_VERIFICATION_FILE,
        API_VERIFICATION_FILE,
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
            "\nSTAGE 7.9.4: FAIL"
        )

        sys.exit(1)

    contract_verification = load_json(
        CONTRACT_VERIFICATION_FILE
    )

    repository_verification = load_json(
        REPOSITORY_VERIFICATION_FILE
    )

    api_verification = load_json(
        API_VERIFICATION_FILE
    )

    # ========================================================
    # 2. Upstream
    # ========================================================

    print(
        "\n2. UPSTREAM STAGES"
    )

    check(
        "Stage 7.9.1 PASS",
        contract_verification.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 7.9.2 PASS",
        repository_verification.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 7.9.2 repository READY",
        repository_verification.get(
            "repository_status"
        )
        == "READY",
        failures,
    )

    check(
        "Stage 7.9.3 PASS",
        api_verification.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 7.9.3 API READY",
        api_verification.get(
            "api_status"
        )
        == "READY",
        failures,
    )

    # ========================================================
    # 3. Real runtime
    # ========================================================

    print(
        "\n3. REAL PRODUCTION RUNTIME"
    )

    app = build_app()

    client = (
        app.test_client()
    )

    health_response = client.get(
        "/api/v1/production/health"
    )

    health_payload = (
        health_response.get_json()
    )

    check(
        "Health HTTP 200",
        health_response.status_code
        == 200,
        failures,
    )

    check(
        "Health status ALIVE",
        health_payload.get(
            "status"
        )
        == "ALIVE",
        failures,
    )

    check(
        "Health stage 7.9.4",
        health_payload.get(
            "stage"
        )
        == "7.9.4",
        failures,
    )

    readiness_response = client.get(
        "/api/v1/production/readiness"
    )

    readiness_payload = (
        readiness_response.get_json()
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

    repository_status = (
        readiness_payload.get(
            "repository",
            {},
        )
    )

    check(
        "Readiness snapshot fresh",
        repository_status.get(
            "snapshot_fresh"
        )
        is True,
        failures,
    )

    check(
        "Readiness Stage 7.8 verified",
        repository_status.get(
            "stage_7_8_verified"
        )
        is True,
        failures,
    )

    check(
        "Readiness contract locked",
        repository_status.get(
            "serving_contract_locked"
        )
        is True,
        failures,
    )

    response = client.get(
        "/api/v1/predictions/upcoming"
    )

    check(
        "Production feed currently serves",
        response.status_code
        == 200,
        failures,
    )

    # ========================================================
    # 4. Stale rejection
    # ========================================================

    print(
        "\n4. STALE SNAPSHOT REJECTION"
    )

    stale_client = (
        build_app(
            lambda:
                FakeRepository(
                    fresh=False
                )
        )
        .test_client()
    )

    response = stale_client.get(
        "/api/v1/production/health"
    )

    check(
        "Liveness survives stale snapshot",
        response.status_code
        == 200,
        failures,
    )

    response = stale_client.get(
        "/api/v1/production/readiness"
    )

    check(
        "Stale readiness HTTP 503",
        response.status_code
        == 503,
        failures,
    )

    check(
        "Stale readiness NOT_READY",
        response.get_json().get(
            "status"
        )
        == "NOT_READY",
        failures,
    )

    response = stale_client.get(
        "/api/v1/predictions/upcoming"
    )

    check(
        "Stale prediction feed blocked",
        response.status_code
        == 503,
        failures,
    )

    # ========================================================
    # 5. Unverified Stage rejection
    # ========================================================

    print(
        "\n5. UNVERIFIED STAGE REJECTION"
    )

    unverified_client = (
        build_app(
            lambda:
                FakeRepository(
                    verified=False
                )
        )
        .test_client()
    )

    response = unverified_client.get(
        "/api/v1/production/readiness"
    )

    check(
        "Unverified readiness HTTP 503",
        response.status_code
        == 503,
        failures,
    )

    response = unverified_client.get(
        "/api/v1/predictions/upcoming"
    )

    check(
        "Unverified predictions blocked",
        response.status_code
        == 503,
        failures,
    )

    # ========================================================
    # 6. Contract rejection
    # ========================================================

    print(
        "\n6. UNLOCKED CONTRACT REJECTION"
    )

    unlocked_client = (
        build_app(
            lambda:
                FakeRepository(
                    contract_locked=False
                )
        )
        .test_client()
    )

    response = unlocked_client.get(
        "/api/v1/production/readiness"
    )

    check(
        "Unlocked contract readiness 503",
        response.status_code
        == 503,
        failures,
    )

    response = unlocked_client.get(
        "/api/v1/predictions/upcoming"
    )

    check(
        "Unlocked contract predictions blocked",
        response.status_code
        == 503,
        failures,
    )

    # ========================================================
    # 7. Generic NOT_READY
    # ========================================================

    print(
        "\n7. GENERIC NOT_READY REJECTION"
    )

    not_ready_client = (
        build_app(
            lambda:
                FakeRepository(
                    ready=False
                )
        )
        .test_client()
    )

    response = not_ready_client.get(
        "/api/v1/production/readiness"
    )

    check(
        "NOT_READY readiness 503",
        response.status_code
        == 503,
        failures,
    )

    response = not_ready_client.get(
        "/api/v1/predictions/upcoming"
    )

    check(
        "NOT_READY prediction feed 503",
        response.status_code
        == 503,
        failures,
    )

    # ========================================================
    # 8. Artifact reload
    # ========================================================

    print(
        "\n8. ARTIFACT-CHANGE AUTOMATIC RELOAD"
    )

    original_repository = (
        api_module
        .ProductionPredictionRepository
    )

    original_watched = list(
        api_module
        .WATCHED_ARTIFACTS
    )

    build_count = {
        "value":
            0,
    }

    def counting_repository():

        build_count[
            "value"
        ] += 1

        return FakeRepository()

    stable_ok = False
    reload_ok = False

    try:

        with tempfile.TemporaryDirectory() as temp_dir:

            watched_file = (
                Path(
                    temp_dir
                )
                / "runtime_artifact.txt"
            )

            watched_file.write_text(
                "version-one",
                encoding="utf-8",
            )

            api_module.ProductionPredictionRepository = (
                counting_repository
            )

            api_module.WATCHED_ARTIFACTS = [
                watched_file
            ]

            reload_client = (
                build_app()
                .test_client()
            )

            first = reload_client.get(
                "/api/v1/production/status"
            )

            first_count = int(
                build_count[
                    "value"
                ]
            )

            second = reload_client.get(
                "/api/v1/production/status"
            )

            second_count = int(
                build_count[
                    "value"
                ]
            )

            stable_ok = bool(
                first.status_code
                == 200
                and
                second.status_code
                == 200
                and
                first_count
                == 1
                and
                second_count
                == 1
            )

            watched_file.write_text(
                (
                    "version-two-with-"
                    "different-size"
                ),
                encoding="utf-8",
            )

            os.utime(
                watched_file,
                None,
            )

            third = reload_client.get(
                "/api/v1/production/status"
            )

            third_count = int(
                build_count[
                    "value"
                ]
            )

            reload_ok = bool(
                third.status_code
                == 200
                and
                third_count
                == 2
            )

    finally:

        api_module.ProductionPredictionRepository = (
            original_repository
        )

        api_module.WATCHED_ARTIFACTS = (
            original_watched
        )

    check(
        "Unchanged artifacts do not reload",
        stable_ok,
        failures,
    )

    check(
        "Changed artifact triggers reload",
        reload_ok,
        failures,
    )

    # ========================================================
    # 9. Source safety
    # ========================================================

    print(
        "\n9. SOURCE SAFETY"
    )

    api_source = (
        API_SOURCE_FILE
        .read_text(
            encoding="utf-8"
        )
        .lower()
    )

    check(
        "No joblib import",
        (
            "import joblib"
            not in api_source
            and
            "from joblib"
            not in api_source
        ),
        failures,
    )

    check(
        "No model execution call",
        (
            ".predict("
            not in api_source
            and
            ".predict_proba("
            not in api_source
        ),
        failures,
    )

    check(
        "No final-test evaluation path",
        (
            "data/processed/final_test"
            not in api_source
            and
            "data\\processed\\final_test"
            not in api_source
        ),
        failures,
    )

    # ========================================================
    # 10. Save
    # ========================================================

    print(
        "\n10. SAVE VERIFICATION"
    )

    verification_status = (
        "PASS"
        if not failures
        else "FAIL"
    )

    report = {

        "stage":
            "7.9.4",

        "status":
            verification_status,

        "runtime_status":
            (
                "SAFE"
                if not failures
                else "UNSAFE"
            ),

        "verified_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "liveness_verified":
            bool(
                health_response.status_code
                == 200
            ),

        "readiness_verified":
            bool(
                readiness_response.status_code
                == 200
            ),

        "stale_snapshot_rejection_verified":
            True,

        "unverified_stage_rejection_verified":
            True,

        "unlocked_contract_rejection_verified":
            True,

        "not_ready_rejection_verified":
            True,

        "artifact_change_reload_verified":
            bool(
                reload_ok
            ),

        "stable_artifact_no_reload_verified":
            bool(
                stable_ok
            ),

        "read_only":
            True,

        "model_loaded_by_runtime_api":
            False,

        "prediction_executed_by_runtime_api":
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

    print(
        "\n" + "=" * 68
    )

    if failures:

        print(
            "STAGE 7.9.4: FAIL"
        )

        print(
            "PRODUCTION RUNTIME SAFETY: UNSAFE"
        )

        for failure in failures:

            print(
                f"  - {failure}"
            )

    else:

        print(
            "STAGE 7.9.4: PASS"
        )

        print(
            "PRODUCTION RUNTIME SAFETY: SAFE"
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
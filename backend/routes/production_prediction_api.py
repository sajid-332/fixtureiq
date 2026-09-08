"""
FixtureIQ Stage 7.9.3 / 7.9.4
Production REST API with Runtime Safety Guard.

Read-only Flask Blueprint layered on top of the verified
ProductionPredictionRepository.
"""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, jsonify

from backend.services.production_prediction_repository import (
    ProductionPredictionRepository,
    RepositoryNotReadyError,
)


# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

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


WATCHED_ARTIFACTS = [
    MODEL_DIR
    / "production_serving_contract.json",

    MODEL_DIR
    / "production_serving_contract_verification.json",

    PRODUCTION_DIR
    / "stage7_8_final_verification.json",

    PRODUCTION_DIR
    / "production_predictions.csv",

    PRODUCTION_DIR
    / "production_prediction_metadata.json",

    PRODUCTION_DIR
    / "production_prediction_report.json",

    PRODUCTION_DIR
    / "production_features.csv",

    PRODUCTION_DIR
    / "upcoming_fixtures.csv",
]


# ============================================================
# Artifact signature
# ============================================================

def _artifact_signature() -> tuple:

    signature = []

    for path in WATCHED_ARTIFACTS:

        try:

            stat = path.stat()

            signature.append(
                (
                    str(path),
                    int(
                        stat.st_mtime_ns
                    ),
                    int(
                        stat.st_size
                    ),
                )
            )

        except FileNotFoundError:

            signature.append(
                (
                    str(path),
                    None,
                    None,
                )
            )

    return tuple(
        signature
    )


# ============================================================
# Public repository status
# ============================================================

def _public_status(
    status: dict,
) -> dict:

    return {

        "status":
            status.get(
                "status",
                "NOT_READY",
            ),

        "stage_7_8_verified":
            bool(
                status.get(
                    "stage_7_8_verified"
                )
            ),

        "serving_contract_locked":
            bool(
                status.get(
                    "serving_contract_locked"
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

        "prediction_count":
            int(
                status.get(
                    "prediction_count",
                    0,
                )
                or 0
            ),

        "snapshot_fresh":
            bool(
                status.get(
                    "snapshot_fresh"
                )
            ),

        "warnings":
            list(
                status.get(
                    "warnings",
                    [],
                )
            ),

        "errors":
            list(
                status.get(
                    "errors",
                    [],
                )
            ),
    }


# ============================================================
# Blueprint factory
# ============================================================

def create_production_prediction_blueprint(
    repository_factory=None,
) -> Blueprint:

    blueprint = Blueprint(
        "production_predictions_v1",
        __name__,
        url_prefix="/api/v1",
    )

    factory = (
        repository_factory
        if repository_factory is not None
        else ProductionPredictionRepository
    )

    auto_reload = (
        repository_factory is None
    )

    state = {

        "repository":
            None,

        "signature":
            None,
    }

    # ========================================================
    # Repository loader
    # ========================================================

    def get_repository():

        if not auto_reload:

            if (
                state[
                    "repository"
                ]
                is None
            ):

                state[
                    "repository"
                ] = factory()

            return state[
                "repository"
            ]

        signature = (
            _artifact_signature()
        )

        if (
            state[
                "repository"
            ]
            is None

            or

            state[
                "signature"
            ]
            != signature
        ):

            state[
                "repository"
            ] = factory()

            state[
                "signature"
            ] = signature

        return state[
            "repository"
        ]

    # ========================================================
    # NOT_READY response
    # ========================================================

    def not_ready_response(
        repository,
        extra_reason=None,
    ):

        status = _public_status(
            repository.get_status()
        )

        reasons = list(
            status[
                "errors"
            ]
        )

        if (
            extra_reason
            and
            str(
                extra_reason
            )
            not in reasons
        ):

            reasons.append(
                str(
                    extra_reason
                )
            )

        message = (
            "; ".join(
                reasons
            )
            if reasons
            else
            (
                "Production prediction "
                "repository is not ready."
            )
        )

        return (
            jsonify(
                {
                    "status":
                        "NOT_READY",

                    "error":
                        {
                            "code":
                                "PRODUCTION_NOT_READY",

                            "message":
                                message,
                        },

                    "repository":
                        status,
                }
            ),
            503,
        )

    # ========================================================
    # Readiness guard
    # ========================================================

    def require_ready():

        repository = (
            get_repository()
        )

        status = (
            repository.get_status()
        )

        if (
            status.get(
                "status"
            )
            != "READY"
        ):

            return (
                None,
                not_ready_response(
                    repository
                ),
            )

        return (
            repository,
            None,
        )

    # ========================================================
    # Success response
    # ========================================================

    def success_response(
        repository,
        data,
        count=None,
    ):

        status = _public_status(
            repository.get_status()
        )

        # Re-check immediately before serving.
        if (
            status[
                "status"
            ]
            != "READY"
        ):

            return (
                not_ready_response(
                    repository
                )
            )

        payload = {

            "status":
                "READY",

            "repository":
                {
                    "model_id":
                        status[
                            "model_id"
                        ],

                    "feature_count":
                        status[
                            "feature_count"
                        ],

                    "prediction_count":
                        status[
                            "prediction_count"
                        ],

                    "snapshot_fresh":
                        status[
                            "snapshot_fresh"
                        ],

                    "warnings":
                        status[
                            "warnings"
                        ],
                },

            "data":
                data,
        }

        if count is not None:

            payload[
                "count"
            ] = int(
                count
            )

        return (
            jsonify(
                payload
            ),
            200,
        )

    # ========================================================
    # Response safety headers
    # ========================================================

    @blueprint.after_request
    def add_safety_headers(
        response,
    ):

        response.headers[
            "Cache-Control"
        ] = "no-store"

        response.headers[
            "X-Content-Type-Options"
        ] = "nosniff"

        return response

    # ========================================================
    # 7.9.4 Liveness
    # ========================================================

    @blueprint.get(
        "/production/health"
    )
    def production_health():

        return (
            jsonify(
                {
                    "status":
                        "ALIVE",

                    "stage":
                        "7.9.4",

                    "service":
                        "production_prediction_api",
                }
            ),
            200,
        )

    # ========================================================
    # 7.9.4 Readiness
    # ========================================================

    @blueprint.get(
        "/production/readiness"
    )
    def production_readiness():

        repository = (
            get_repository()
        )

        status = _public_status(
            repository.get_status()
        )

        payload = {

            "status":
                (
                    "READY"
                    if status[
                        "status"
                    ]
                    == "READY"
                    else "NOT_READY"
                ),

            "stage":
                "7.9.4",

            "service":
                "production_prediction_api",

            "repository":
                status,
        }

        return (
            jsonify(
                payload
            ),
            (
                200
                if status[
                    "status"
                ]
                == "READY"
                else 503
            ),
        )

    # ========================================================
    # 7.9.3 Production status
    # ========================================================

    @blueprint.get(
        "/production/status"
    )
    def production_status():

        repository = (
            get_repository()
        )

        status = _public_status(
            repository.get_status()
        )

        return (
            jsonify(
                {
                    "stage":
                        "7.9.3",

                    "service":
                        "production_prediction_api",

                    **status,
                }
            ),
            200,
        )

    # ========================================================
    # Prediction feed
    # ========================================================

    @blueprint.get(
        "/predictions"
    )
    @blueprint.get(
        "/predictions/upcoming"
    )
    def prediction_feed():

        (
            repository,
            error,
        ) = require_ready()

        if error is not None:

            return error

        try:

            records = (
                repository
                .get_upcoming_predictions()
            )

        except RepositoryNotReadyError as exc:

            return (
                not_ready_response(
                    repository,
                    exc,
                )
            )

        return (
            success_response(
                repository,
                records,
                count=len(
                    records
                ),
            )
        )

    # ========================================================
    # Team lookup
    # ========================================================

    @blueprint.get(
        "/predictions/team/<path:team_name>"
    )
    def team_predictions(
        team_name,
    ):

        (
            repository,
            error,
        ) = require_ready()

        if error is not None:

            return error

        team_name = (
            team_name.strip()
        )

        if not team_name:

            return (
                jsonify(
                    {
                        "status":
                            "ERROR",

                        "error":
                            {
                                "code":
                                    "INVALID_TEAM_NAME",

                                "message":
                                    (
                                        "team_name cannot "
                                        "be empty."
                                    ),
                            },
                    }
                ),
                400,
            )

        try:

            records = (
                repository
                .get_team_predictions(
                    team_name
                )
            )

        except RepositoryNotReadyError as exc:

            return (
                not_ready_response(
                    repository,
                    exc,
                )
            )

        if not records:

            return (
                jsonify(
                    {
                        "status":
                            "NOT_FOUND",

                        "error":
                            {
                                "code":
                                    "TEAM_NOT_FOUND",

                                "message":
                                    (
                                        "No current production "
                                        "predictions found "
                                        "for team."
                                    ),
                            },
                    }
                ),
                404,
            )

        return (
            success_response(
                repository,
                records,
                count=len(
                    records
                ),
            )
        )

    # ========================================================
    # Fixture lookup
    # ========================================================

    @blueprint.get(
        "/predictions/<fixture_id>"
    )
    def fixture_prediction(
        fixture_id,
    ):

        (
            repository,
            error,
        ) = require_ready()

        if error is not None:

            return error

        try:

            fixture_id = int(
                fixture_id
            )

        except (
            TypeError,
            ValueError,
        ):

            return (
                jsonify(
                    {
                        "status":
                            "ERROR",

                        "error":
                            {
                                "code":
                                    "INVALID_FIXTURE_ID",

                                "message":
                                    (
                                        "fixture_id must "
                                        "be an integer."
                                    ),
                            },
                    }
                ),
                400,
            )

        try:

            record = (
                repository
                .get_prediction(
                    fixture_id
                )
            )

        except RepositoryNotReadyError as exc:

            return (
                not_ready_response(
                    repository,
                    exc,
                )
            )

        if record is None:

            return (
                jsonify(
                    {
                        "status":
                            "NOT_FOUND",

                        "error":
                            {
                                "code":
                                    "FIXTURE_NOT_FOUND",

                                "message":
                                    (
                                        "Prediction not found "
                                        "for fixture_id."
                                    ),
                            },
                    }
                ),
                404,
            )

        return (
            success_response(
                repository,
                record,
            )
        )

    return blueprint


# ============================================================
# Default Blueprint
# ============================================================

production_predictions_bp = (
    create_production_prediction_blueprint()
)
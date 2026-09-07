"""
FixtureIQ Stage 7.9.2
Production Prediction Repository.

Single trusted read layer for production predictions.

The repository:
- validates the locked Stage 7.9.1 serving contract
- validates Stage 7.8 final verification
- validates artifact hashes
- validates prediction integrity
- validates snapshot freshness
- exposes only contract-approved public fields

The repository NEVER:
- loads the ML model
- runs predict()
- runs predict_proba()
- fetches provider data
- builds features
- trains
- tunes
- selects models
- accesses final-test evaluation artifacts
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
)

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


SERVING_CONTRACT_FILE = (
    MODEL_DIR
    / "production_serving_contract.json"
)

SERVING_CONTRACT_VERIFICATION_FILE = (
    MODEL_DIR
    / "production_serving_contract_verification.json"
)

STAGE_7_8_FINAL_FILE = (
    PRODUCTION_DIR
    / "stage7_8_final_verification.json"
)

PREDICTION_FILE = (
    PRODUCTION_DIR
    / "production_predictions.csv"
)

PREDICTION_METADATA_FILE = (
    PRODUCTION_DIR
    / "production_prediction_metadata.json"
)

PREDICTION_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_prediction_report.json"
)

FEATURE_FILE = (
    PRODUCTION_DIR
    / "production_features.csv"
)

UPCOMING_FILE = (
    PRODUCTION_DIR
    / "upcoming_fixtures.csv"
)

MODEL_FILE = (
    MODEL_DIR
    / "selected"
    / "selected_model.joblib"
)


PROBABILITY_COLUMNS = [
    "prob_draw",
    "prob_home_win",
    "prob_away_win",
]


class RepositoryNotReadyError(
    RuntimeError
):
    pass


def sha256_file(
    path: Path,
) -> str:

    if not path.exists():
        raise FileNotFoundError(path)

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
            digest.update(chunk)

    return digest.hexdigest()


def load_json(
    path: Path,
) -> dict:

    if not path.exists():
        raise FileNotFoundError(path)

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        payload = json.load(file)

    if not isinstance(
        payload,
        dict,
    ):
        raise RuntimeError(
            f"Expected JSON object: {path}"
        )

    return payload


def clean_value(value):

    if value is None:
        return None

    if isinstance(
        value,
        np.generic,
    ):
        value = value.item()

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    return value


class ProductionPredictionRepository:

    def __init__(self):

        self.status = "NOT_READY"
        self.errors: list[str] = []
        self.warnings: list[str] = []

        self.contract: dict = {}
        self.contract_verification: dict = {}
        self.stage_7_8: dict = {}

        self.prediction_metadata: dict = {}
        self.prediction_report: dict = {}

        self._predictions = pd.DataFrame()
        self._public_field_order: list[str] = []
        self._required_public_fields: list[str] = []
        self._optional_public_fields: list[str] = []

        self.model_id = None
        self.model_sha256 = None
        self.feature_count = None

        self.reload()

    # ========================================================
    # Core loading
    # ========================================================

    def reload(self):

        self.status = "NOT_READY"
        self.errors = []
        self.warnings = []

        self._predictions = pd.DataFrame()

        try:
            self._load_and_validate()

        except Exception as exc:

            self.errors.append(
                str(exc)
            )

            self.status = "NOT_READY"

        return self.get_status()

    def _fail(
        self,
        message: str,
    ):

        self.errors.append(message)

    def _load_and_validate(self):

        required_files = [
            SERVING_CONTRACT_FILE,
            SERVING_CONTRACT_VERIFICATION_FILE,
            STAGE_7_8_FINAL_FILE,
            PREDICTION_FILE,
            PREDICTION_METADATA_FILE,
            PREDICTION_REPORT_FILE,
            FEATURE_FILE,
            UPCOMING_FILE,
            MODEL_FILE,
        ]

        missing = [
            str(path)
            for path in required_files
            if not path.exists()
        ]

        if missing:

            raise RepositoryNotReadyError(
                "Required production artifact missing: "
                + ", ".join(missing)
            )

        self.contract = load_json(
            SERVING_CONTRACT_FILE
        )

        self.contract_verification = load_json(
            SERVING_CONTRACT_VERIFICATION_FILE
        )

        self.stage_7_8 = load_json(
            STAGE_7_8_FINAL_FILE
        )

        self.prediction_metadata = load_json(
            PREDICTION_METADATA_FILE
        )

        self.prediction_report = load_json(
            PREDICTION_REPORT_FILE
        )

        # ----------------------------------------------------
        # Stage 7.9.1 contract
        # ----------------------------------------------------

        if (
            self.contract.get("stage")
            != "7.9.1"
        ):
            self._fail(
                "Invalid serving contract stage."
            )

        if (
            self.contract.get("status")
            != "LOCKED_SERVING_CONTRACT"
        ):
            self._fail(
                "Serving contract is not locked."
            )

        actual_contract_hash = sha256_file(
            SERVING_CONTRACT_FILE
        ).lower()

        if (
            self.contract_verification.get(
                "stage"
            )
            != "7.9.1"
        ):
            self._fail(
                "Serving contract verification stage mismatch."
            )

        if (
            self.contract_verification.get(
                "status"
            )
            != "PASS"
        ):
            self._fail(
                "Stage 7.9.1 verification did not PASS."
            )

        if (
            str(
                self.contract_verification.get(
                    "contract_sha256",
                    "",
                )
            ).lower()
            != actual_contract_hash
        ):
            self._fail(
                "Serving contract SHA256 mismatch."
            )

        # ----------------------------------------------------
        # Stage 7.8 final state
        # ----------------------------------------------------

        if (
            self.stage_7_8.get("stage")
            != "7.8.5"
        ):
            self._fail(
                "Stage 7.8.5 verification missing."
            )

        if (
            self.stage_7_8.get("status")
            != "PASS"
        ):
            self._fail(
                "Stage 7.8.5 status is not PASS."
            )

        if (
            self.stage_7_8.get(
                "stage_7_8_status"
            )
            != "COMPLETE"
        ):
            self._fail(
                "Stage 7.8 is not COMPLETE."
            )

        if (
            self.stage_7_8.get(
                "stage_7_8_4_verified"
            )
            is not True
        ):
            self._fail(
                "Stage 7.8.4 independent verification missing."
            )

        if (
            self.stage_7_8.get(
                "final_test_status"
            )
            != "CONSUMED"
        ):
            self._fail(
                "Final-test lifecycle is not CONSUMED."
            )

        if (
            self.stage_7_8.get(
                "final_test_evaluation_artifacts_used"
            )
            is not False
        ):
            self._fail(
                "Forbidden final-test artifact usage detected."
            )

        # ----------------------------------------------------
        # Model identity
        # ----------------------------------------------------

        contract_model = self.contract.get(
            "model",
            {},
        )

        self.model_id = contract_model.get(
            "model_id"
        )

        self.model_sha256 = str(
            contract_model.get(
                "sha256",
                "",
            )
        ).lower()

        self.feature_count = contract_model.get(
            "feature_count"
        )

        if self.model_id != "random_forest":
            self._fail(
                "Unexpected production model ID."
            )

        if self.feature_count != 86:
            self._fail(
                "Unexpected feature count."
            )

        actual_model_hash = sha256_file(
            MODEL_FILE
        ).lower()

        if (
            actual_model_hash
            != self.model_sha256
        ):
            self._fail(
                "Production model SHA256 mismatch."
            )

        if (
            str(
                self.stage_7_8.get(
                    "model_sha256",
                    "",
                )
            ).lower()
            != self.model_sha256
        ):
            self._fail(
                "Stage 7.8 model provenance mismatch."
            )

        # ----------------------------------------------------
        # Stage 7.8 artifact hash chain
        # ----------------------------------------------------

        stage_hashes = self.stage_7_8.get(
            "artifact_hashes",
            {},
        )

        actual_prediction_hash = sha256_file(
            PREDICTION_FILE
        ).lower()

        actual_feature_hash = sha256_file(
            FEATURE_FILE
        ).lower()

        actual_upcoming_hash = sha256_file(
            UPCOMING_FILE
        ).lower()

        if (
            actual_prediction_hash
            != str(
                stage_hashes.get(
                    "production_prediction_sha256",
                    "",
                )
            ).lower()
        ):
            self._fail(
                "Production prediction SHA256 mismatch."
            )

        if (
            actual_feature_hash
            != str(
                stage_hashes.get(
                    "production_feature_sha256",
                    "",
                )
            ).lower()
        ):
            self._fail(
                "Production feature SHA256 mismatch."
            )

        if (
            actual_upcoming_hash
            != str(
                stage_hashes.get(
                    "upcoming_fixture_sha256",
                    "",
                )
            ).lower()
        ):
            self._fail(
                "Upcoming fixture SHA256 mismatch."
            )

        if (
            actual_prediction_hash
            != str(
                self.prediction_metadata.get(
                    "prediction_sha256",
                    "",
                )
            ).lower()
        ):
            self._fail(
                "Prediction metadata SHA256 mismatch."
            )

        if (
            actual_prediction_hash
            != str(
                self.prediction_report.get(
                    "prediction_sha256",
                    "",
                )
            ).lower()
        ):
            self._fail(
                "Prediction report SHA256 mismatch."
            )

        # ----------------------------------------------------
        # Load predictions
        # ----------------------------------------------------

        predictions = pd.read_csv(
            PREDICTION_FILE
        )

        if predictions.empty:
            self._fail(
                "Production prediction dataset is empty."
            )

        source_required = self.contract.get(
            "source_required_columns",
            [],
        )

        missing_columns = [
            column
            for column in source_required
            if column not in predictions.columns
        ]

        if missing_columns:
            self._fail(
                "Missing prediction columns: "
                + ", ".join(
                    missing_columns
                )
            )

        public_schema = self.contract.get(
            "public_prediction_schema",
            {},
        )

        self._public_field_order = list(
            public_schema.get(
                "field_order",
                [],
            )
        )

        self._required_public_fields = list(
            public_schema.get(
                "required_fields",
                [],
            )
        )

        self._optional_public_fields = list(
            public_schema.get(
                "optional_fields",
                [],
            )
        )

        if "fixture_id" not in predictions.columns:
            self._fail(
                "fixture_id missing."
            )

        else:

            try:
                predictions[
                    "fixture_id"
                ] = pd.to_numeric(
                    predictions[
                        "fixture_id"
                    ],
                    errors="raise",
                ).astype(
                    "int64"
                )
            except Exception:
                self._fail(
                    "Invalid fixture_id values."
                )

        if (
            "fixture_id"
            in predictions.columns
            and
            not predictions[
                "fixture_id"
            ].is_unique
        ):
            self._fail(
                "Duplicate fixture IDs detected."
            )

        # ----------------------------------------------------
        # Probability integrity
        # ----------------------------------------------------

        probability_ok = all(
            column in predictions.columns
            for column in PROBABILITY_COLUMNS
        )

        if not probability_ok:
            self._fail(
                "Probability columns missing."
            )

        else:

            try:

                probabilities = predictions[
                    PROBABILITY_COLUMNS
                ].to_numpy(
                    dtype=float
                )

                if not (
                    np.isfinite(
                        probabilities
                    ).all()
                    and
                    (
                        probabilities >= 0
                    ).all()
                    and
                    (
                        probabilities <= 1
                    ).all()
                ):
                    self._fail(
                        "Probability range integrity failure."
                    )

                if not np.allclose(
                    probabilities.sum(
                        axis=1
                    ),
                    1.0,
                    atol=1e-8,
                    rtol=0.0,
                ):
                    self._fail(
                        "Probability sum integrity failure."
                    )

                targets = pd.to_numeric(
                    predictions[
                        "predicted_target"
                    ],
                    errors="raise",
                ).astype(
                    int
                ).to_numpy()

                if not set(
                    targets.tolist()
                ).issubset(
                    {0, 1, 2}
                ):
                    self._fail(
                        "Invalid prediction target."
                    )

                expected_targets = np.argmax(
                    probabilities,
                    axis=1,
                ).astype(int)

                if not np.array_equal(
                    targets,
                    expected_targets,
                ):
                    self._fail(
                        "Prediction target is not probability argmax."
                    )

                label_mapping = {
                    0: "Draw",
                    1: "Home Win",
                    2: "Away Win",
                }

                expected_labels = [
                    label_mapping[
                        int(value)
                    ]
                    for value in targets
                ]

                actual_labels = predictions[
                    "predicted_label"
                ].astype(str).tolist()

                if (
                    expected_labels
                    != actual_labels
                ):
                    self._fail(
                        "Prediction label mapping failure."
                    )

                confidence = pd.to_numeric(
                    predictions[
                        "confidence"
                    ],
                    errors="raise",
                ).to_numpy(
                    dtype=float
                )

                if not np.allclose(
                    confidence,
                    np.max(
                        probabilities,
                        axis=1,
                    ),
                    atol=1e-12,
                    rtol=0.0,
                ):
                    self._fail(
                        "Prediction confidence integrity failure."
                    )

            except Exception as exc:

                self._fail(
                    "Prediction integrity exception: "
                    + str(exc)
                )

        # ----------------------------------------------------
        # Row-level model provenance
        # ----------------------------------------------------

        if (
            "model_id"
            in predictions.columns
            and
            set(
                predictions[
                    "model_id"
                ].astype(str)
            )
            != {
                self.model_id
            }
        ):
            self._fail(
                "Row-level model ID mismatch."
            )

        if (
            "model_sha256"
            in predictions.columns
            and
            set(
                predictions[
                    "model_sha256"
                ]
                .astype(str)
                .str.lower()
            )
            != {
                self.model_sha256
            }
        ):
            self._fail(
                "Row-level model SHA256 mismatch."
            )

        if "feature_count" in predictions.columns:

            try:

                feature_counts = pd.to_numeric(
                    predictions[
                        "feature_count"
                    ],
                    errors="raise",
                ).astype(int)

                if set(
                    feature_counts.tolist()
                ) != {
                    self.feature_count
                }:
                    self._fail(
                        "Row-level feature count mismatch."
                    )

            except Exception:

                self._fail(
                    "Invalid feature_count values."
                )

        # ----------------------------------------------------
        # Snapshot freshness
        # ----------------------------------------------------

        if "date" not in predictions.columns:

            self._fail(
                "Prediction kickoff date missing."
            )

        else:

            dates = pd.to_datetime(
                predictions[
                    "date"
                ],
                errors="coerce",
                utc=True,
            )

            if dates.isna().any():

                self._fail(
                    "Invalid fixture dates."
                )

            else:

                predictions[
                    "_kickoff_utc"
                ] = dates

                now = pd.Timestamp.now(
                    tz="UTC"
                )

                if not (
                    dates > now
                ).all():

                    self._fail(
                        "Production prediction snapshot is stale."
                    )

        # ----------------------------------------------------
        # Diagnostics
        # ----------------------------------------------------

        previous_warnings = self.stage_7_8.get(
            "warnings",
            [],
        )

        if isinstance(
            previous_warnings,
            list,
        ):
            self.warnings.extend(
                str(value)
                for value in previous_warnings
            )

        self.warnings = list(
            dict.fromkeys(
                self.warnings
            )
        )

        if self.errors:

            self.status = "NOT_READY"

            return

        predictions = predictions.sort_values(
            [
                "_kickoff_utc",
                "fixture_id",
            ],
            kind="stable",
        ).reset_index(
            drop=True
        )

        self._predictions = predictions

        self.status = "READY"

    # ========================================================
    # Dynamic freshness
    # ========================================================

    def _dynamic_freshness_ok(
        self,
    ) -> bool:

        if self._predictions.empty:
            return False

        if (
            "_kickoff_utc"
            not in self._predictions.columns
        ):
            return False

        now = pd.Timestamp.now(
            tz="UTC"
        )

        return bool(
            (
                self._predictions[
                    "_kickoff_utc"
                ]
                > now
            ).all()
        )

    def get_status(self) -> dict:

        if (
            self.status == "READY"
            and
            not self._dynamic_freshness_ok()
        ):

            self.status = "NOT_READY"

            stale_message = (
                "Production prediction snapshot is stale."
            )

            if stale_message not in self.errors:
                self.errors.append(
                    stale_message
                )

        return {

            "status":
                self.status,

            "stage_7_8_verified":
                bool(
                    self.stage_7_8.get(
                        "status"
                    )
                    == "PASS"
                    and
                    self.stage_7_8.get(
                        "stage_7_8_status"
                    )
                    == "COMPLETE"
                ),

            "serving_contract_locked":
                bool(
                    self.contract.get(
                        "status"
                    )
                    == "LOCKED_SERVING_CONTRACT"
                ),

            "model_id":
                self.model_id,

            "feature_count":
                self.feature_count,

            "prediction_count":
                int(
                    len(
                        self._predictions
                    )
                )
                if self.status == "READY"
                else 0,

            "snapshot_fresh":
                bool(
                    self.status == "READY"
                    and
                    self._dynamic_freshness_ok()
                ),

            "errors":
                list(
                    self.errors
                ),

            "warnings":
                list(
                    self.warnings
                ),
        }

    def _require_ready(self):

        status = self.get_status()

        if (
            status[
                "status"
            ]
            != "READY"
        ):

            reason = (
                "; ".join(
                    status[
                        "errors"
                    ]
                )
                or
                "Repository is not ready."
            )

            raise RepositoryNotReadyError(
                reason
            )

    # ========================================================
    # Public serialization
    # ========================================================

    def _row_to_public(
        self,
        row: pd.Series,
    ) -> dict:

        record = {}

        for field in self._public_field_order:

            if field not in row.index:
                continue

            value = clean_value(
                row[field]
            )

            if field == "date":

                timestamp = pd.to_datetime(
                    value,
                    utc=True,
                )

                value = (
                    timestamp.isoformat()
                    .replace(
                        "+00:00",
                        "Z",
                    )
                )

            record[
                field
            ] = value

        return record

    # ========================================================
    # Repository methods
    # ========================================================

    def get_all_predictions(
        self,
    ) -> list[dict]:

        self._require_ready()

        return [
            self._row_to_public(row)
            for _, row
            in self._predictions.iterrows()
        ]

    def get_upcoming_predictions(
        self,
    ) -> list[dict]:

        return self.get_all_predictions()

    def get_prediction(
        self,
        fixture_id,
    ) -> dict | None:

        self._require_ready()

        try:
            fixture_id = int(
                fixture_id
            )

        except Exception:
            return None

        matches = self._predictions[
            self._predictions[
                "fixture_id"
            ]
            == fixture_id
        ]

        if matches.empty:
            return None

        return self._row_to_public(
            matches.iloc[0]
        )

    def get_team_predictions(
        self,
        team_name: str,
    ) -> list[dict]:

        self._require_ready()

        if not isinstance(
            team_name,
            str,
        ):
            return []

        normalized = (
            team_name
            .strip()
            .casefold()
        )

        if not normalized:
            return []

        home = (
            self._predictions[
                "home_team_name"
            ]
            .astype(str)
            .str.strip()
            .str.casefold()
        )

        away = (
            self._predictions[
                "away_team_name"
            ]
            .astype(str)
            .str.strip()
            .str.casefold()
        )

        matches = self._predictions[
            (home == normalized)
            |
            (away == normalized)
        ]

        return [
            self._row_to_public(row)
            for _, row
            in matches.iterrows()
        ]
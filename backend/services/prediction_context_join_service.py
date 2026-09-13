"""
FixtureIQ Stage 9.2
Prediction + Context Join Foundation.

This service supports:

9.2.1 Prediction Source Gate
9.2.2 Fixture Identity Reconciliation
9.2.3 Strict Prediction-Context Join

Stage 9 principle:
Stage 7 prediction values are authoritative.
Stage 8 context values are authoritative.

This service must never:
- load the ML model
- execute the ML model
- recalibrate probabilities
- modify probabilities
- modify prediction labels
- mutate Stage 7 artifacts
- mutate Stage 8 artifacts
- perform fuzzy fixture matching
- use best-effort identity fallback
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


# ============================================================
# Project paths
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
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


DEFAULT_CONTRACT_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract.json"
)

DEFAULT_CONTRACT_VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract_verification.json"
)

DEFAULT_PREDICTIONS_FILE = (
    PRODUCTION_DIR
    / "production_predictions.csv"
)

DEFAULT_PREDICTION_METADATA_FILE = (
    PRODUCTION_DIR
    / "production_prediction_metadata.json"
)

DEFAULT_PREDICTION_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_prediction_report.json"
)

DEFAULT_PREDICTION_VERIFICATION_FILE = (
    PRODUCTION_DIR
    / "production_prediction_verification.json"
)

DEFAULT_STAGE7_8_FILE = (
    PRODUCTION_DIR
    / "stage7_8_final_verification.json"
)

DEFAULT_STAGE7_9_FILE = (
    PRODUCTION_DIR
    / "stage7_9_final_verification.json"
)

DEFAULT_CONTEXT_FILE = (
    CONTEXT_DIR
    / "enriched_upcoming_fixtures.csv"
)

DEFAULT_FIXTURE_CONTEXT_REPORT_FILE = (
    CONTEXT_DIR
    / "fixture_context_report.json"
)

DEFAULT_CONTEXT_API_VERIFICATION_FILE = (
    CONTEXT_DIR
    / "context_api_verification.json"
)

DEFAULT_CONTEXT_RUNTIME_VERIFICATION_FILE = (
    CONTEXT_DIR
    / "context_runtime_verification.json"
)

DEFAULT_STAGE8_FINAL_FILE = (
    CONTEXT_DIR
    / "stage8_final_verification.json"
)


# ============================================================
# Contract constants
# ============================================================

REQUIRED_IDENTITY_FIELDS = [

    "fixture_id",

    "home_team_id",
    "home_team_name",

    "away_team_id",
    "away_team_name",
]


REQUIRED_PREDICTION_FIELDS = [

    "fixture_id",

    "home_team_id",
    "home_team_name",

    "away_team_id",
    "away_team_name",

    "prob_home_win",
    "prob_draw",
    "prob_away_win",

    "predicted_label",
    "confidence",
]


OPTIONAL_IDENTITY_VALIDATION_FIELDS = [

    "season",
]


DATE_FIELD_CANDIDATES = [

    "date",
    "kickoff_utc",
    "utc_date",
    "kickoff",
    "match_date",
]


# ============================================================
# Exceptions
# ============================================================

class PredictionContextJoinError(
    RuntimeError
):
    """Base Stage 9.2 join error."""


class PredictionSourceNotReadyError(
    PredictionContextJoinError
):
    """Raised when Stage 7 prediction input is not ready."""


class FixtureIdentityError(
    PredictionContextJoinError
):
    """Raised when prediction/context fixture identity disagrees."""


# ============================================================
# Helpers
# ============================================================

def _load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise PredictionContextJoinError(
            f"Required JSON artifact missing: {path}"
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

        raise PredictionContextJoinError(
            f"Expected JSON object: {path}"
        )

    return payload


def _load_csv(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:

    if not path.exists():

        raise PredictionContextJoinError(
            f"Required CSV artifact missing: {path}"
        )

    with path.open(
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

        rows = [

            dict(
                row
            )

            for row in reader
        ]

    if not fields:

        raise PredictionContextJoinError(
            f"CSV has no columns: {path}"
        )

    if not rows:

        raise PredictionContextJoinError(
            f"CSV has no rows: {path}"
        )

    return (
        fields,
        rows,
    )


def _sha256_file(
    path: Path,
) -> str:

    if not path.exists():

        raise PredictionContextJoinError(
            f"Required artifact missing: {path}"
        )

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


def _normalize_scalar(
    value: Any,
) -> str:

    if value is None:

        return ""

    return str(
        value
    ).strip()


def _require_non_empty(
    row: dict[str, str],
    field: str,
    *,
    fixture_id: str,
    source_name: str,
) -> str:

    value = _normalize_scalar(
        row.get(
            field
        )
    )

    if not value:

        raise FixtureIdentityError(
            (
                f"{source_name} fixture "
                f"{fixture_id!r} has empty "
                f"identity field {field!r}."
            )
        )

    return value


def _find_date_field(
    prediction_fields: list[str],
    context_fields: list[str],
) -> str | None:

    for candidate in DATE_FIELD_CANDIDATES:

        if (
            candidate in prediction_fields
            and
            candidate in context_fields
        ):

            return candidate

    return None


# ============================================================
# Service
# ============================================================

class PredictionContextJoinService:

    """
    Read-only foundation for Stage 9.2.

    9.2.1:
        validate_prediction_source()

    9.2.2:
        reconcile_fixture_identity()

    Later 9.2.3 can reuse the same validated inputs for
    strict data joining.
    """

    def __init__(
        self,
        *,
        contract_file: Path = DEFAULT_CONTRACT_FILE,
        contract_verification_file: Path = DEFAULT_CONTRACT_VERIFICATION_FILE,
        predictions_file: Path = DEFAULT_PREDICTIONS_FILE,
        prediction_metadata_file: Path = DEFAULT_PREDICTION_METADATA_FILE,
        prediction_report_file: Path = DEFAULT_PREDICTION_REPORT_FILE,
        prediction_verification_file: Path = DEFAULT_PREDICTION_VERIFICATION_FILE,
        stage7_8_file: Path = DEFAULT_STAGE7_8_FILE,
        stage7_9_file: Path = DEFAULT_STAGE7_9_FILE,
        context_file: Path = DEFAULT_CONTEXT_FILE,
        fixture_context_report_file: Path = DEFAULT_FIXTURE_CONTEXT_REPORT_FILE,
        context_api_verification_file: Path = DEFAULT_CONTEXT_API_VERIFICATION_FILE,
        context_runtime_verification_file: Path = DEFAULT_CONTEXT_RUNTIME_VERIFICATION_FILE,
        stage8_final_file: Path = DEFAULT_STAGE8_FINAL_FILE,
    ) -> None:

        self.contract_file = Path(
            contract_file
        )

        self.contract_verification_file = Path(
            contract_verification_file
        )

        self.predictions_file = Path(
            predictions_file
        )

        self.prediction_metadata_file = Path(
            prediction_metadata_file
        )

        self.prediction_report_file = Path(
            prediction_report_file
        )

        self.prediction_verification_file = Path(
            prediction_verification_file
        )

        self.stage7_8_file = Path(
            stage7_8_file
        )

        self.stage7_9_file = Path(
            stage7_9_file
        )

        self.context_file = Path(
            context_file
        )

        self.fixture_context_report_file = Path(
            fixture_context_report_file
        )

        self.context_api_verification_file = Path(
            context_api_verification_file
        )

        self.context_runtime_verification_file = Path(
            context_runtime_verification_file
        )

        self.stage8_final_file = Path(
            stage8_final_file
        )

    # ========================================================
    # Contract
    # ========================================================

    def _load_locked_contract(
        self,
    ) -> tuple[
        dict,
        dict,
    ]:

        contract = _load_json(
            self.contract_file
        )

        verification = _load_json(
            self.contract_verification_file
        )

        if (
            contract.get(
                "stage"
            )
            != "9.1"
        ):

            raise PredictionContextJoinError(
                "Stage 9.1 contract identity invalid."
            )

        if (
            contract.get(
                "status"
            )
            !=
            "LOCKED_MATCH_INTELLIGENCE_CONTRACT"
        ):

            raise PredictionContextJoinError(
                "Stage 9.1 contract is not locked."
            )

        if (
            contract.get(
                "stage_9_1_complete"
            )
            is not True
        ):

            raise PredictionContextJoinError(
                "Stage 9.1 contract is incomplete."
            )

        if (
            verification.get(
                "status"
            )
            != "PASS"
        ):

            raise PredictionContextJoinError(
                "Stage 9.1 verification is not PASS."
            )

        if (
            verification.get(
                "stage_9_1_complete"
            )
            is not True
        ):

            raise PredictionContextJoinError(
                "Stage 9.1 verification is incomplete."
            )

        if (
            verification.get(
                "contract_sha256"
            )
            !=
            _sha256_file(
                self.contract_file
            )
        ):

            raise PredictionContextJoinError(
                (
                    "Stage 9.1 verification does not "
                    "reference the current locked contract."
                )
            )

        return (
            contract,
            verification,
        )

    def _allowed_input_paths(
        self,
        contract: dict,
    ) -> dict[str, Path]:

        expected = {

            "production_predictions":
                self.predictions_file,

            "production_prediction_metadata":
                self.prediction_metadata_file,

            "production_prediction_report":
                self.prediction_report_file,

            "production_prediction_verification":
                self.prediction_verification_file,

            "stage7_8_final_verification":
                self.stage7_8_file,

            "stage7_9_final_verification":
                self.stage7_9_file,

            "enriched_upcoming_fixtures":
                self.context_file,

            "fixture_context_report":
                self.fixture_context_report_file,

            "context_api_verification":
                self.context_api_verification_file,

            "context_runtime_verification":
                self.context_runtime_verification_file,

            "stage8_final_verification":
                self.stage8_final_file,
        }

        allowed = (
            contract.get(
                "stage_9_1_1",
                {}
            ).get(
                "allowed_inputs",
                {}
            )
        )

        if (
            set(
                allowed.keys()
            )
            !=
            set(
                expected.keys()
            )
        ):

            raise PredictionContextJoinError(
                "Stage 9 allowed-input set changed."
            )

        for name, path in expected.items():

            item = allowed.get(
                name,
                {}
            )

            if (
                item.get(
                    "sha256"
                )
                !=
                _sha256_file(
                    path
                )
            ):

                raise PredictionContextJoinError(
                    (
                        f"Allowed input {name!r} "
                        "no longer matches the locked "
                        "Stage 9.1 dependency hash."
                    )
                )

            if (
                item.get(
                    "read_only"
                )
                is not True
            ):

                raise PredictionContextJoinError(
                    (
                        f"Allowed input {name!r} "
                        "is not marked read-only."
                    )
                )

            if (
                item.get(
                    "stage9_write_allowed"
                )
                is not False
            ):

                raise PredictionContextJoinError(
                    (
                        f"Stage 9 write protection "
                        f"invalid for {name!r}."
                    )
                )

        return expected

    # ========================================================
    # 9.2.1 Prediction Source Gate
    # ========================================================

    def validate_prediction_source(
        self,
    ) -> dict:

        contract, _ = (
            self._load_locked_contract()
        )

        self._allowed_input_paths(
            contract
        )

        metadata = _load_json(
            self.prediction_metadata_file
        )

        report = _load_json(
            self.prediction_report_file
        )

        verification = _load_json(
            self.prediction_verification_file
        )

        stage7_8 = _load_json(
            self.stage7_8_file
        )

        stage7_9 = _load_json(
            self.stage7_9_file
        )

        stage8_final = _load_json(
            self.stage8_final_file
        )

        stage7_evidence = {

            "prediction_metadata":
                metadata,

            "prediction_report":
                report,

            "prediction_verification":
                verification,

            "stage7_8":
                stage7_8,

            "stage7_9":
                stage7_9,
        }

        for name, payload in stage7_evidence.items():

            if (
                payload.get(
                    "status"
                )
                != "PASS"
            ):

                raise PredictionSourceNotReadyError(
                    (
                        f"{name} does not have "
                        "status PASS."
                    )
                )

        if (
            stage8_final.get(
                "status"
            )
            != "PASS"
            or
            stage8_final.get(
                "stage_8_complete"
            )
            is not True
        ):

            raise PredictionSourceNotReadyError(
                "Stage 8 final gate is not ready."
            )

        (
            prediction_fields,
            prediction_rows,
        ) = _load_csv(
            self.predictions_file
        )

        missing_fields = [

            field

            for field in REQUIRED_PREDICTION_FIELDS

            if field not in prediction_fields
        ]

        if missing_fields:

            raise PredictionSourceNotReadyError(
                (
                    "Production prediction schema missing: "
                    f"{missing_fields}"
                )
            )

        fixture_ids = []

        for row in prediction_rows:

            fixture_id = _normalize_scalar(
                row.get(
                    "fixture_id"
                )
            )

            if not fixture_id:

                raise PredictionSourceNotReadyError(
                    (
                        "Production predictions contain "
                        "empty fixture_id."
                    )
                )

            fixture_ids.append(
                fixture_id
            )

            for field in REQUIRED_IDENTITY_FIELDS:

                _require_non_empty(
                    row,
                    field,
                    fixture_id=fixture_id,
                    source_name=
                        "production_predictions",
                )

            probability_values = []

            for field in (

                "prob_home_win",
                "prob_draw",
                "prob_away_win",
            ):

                raw = _normalize_scalar(
                    row.get(
                        field
                    )
                )

                try:

                    value = float(
                        raw
                    )

                except (
                    TypeError,
                    ValueError,
                ) as exc:

                    raise PredictionSourceNotReadyError(
                        (
                            f"Fixture {fixture_id!r} "
                            f"has invalid {field}: "
                            f"{raw!r}"
                        )
                    ) from exc

                if not (
                    0.0
                    <= value
                    <= 1.0
                ):

                    raise PredictionSourceNotReadyError(
                        (
                            f"Fixture {fixture_id!r} "
                            f"has out-of-range {field}: "
                            f"{value}"
                        )
                    )

                probability_values.append(
                    value
                )

            probability_sum = sum(
                probability_values
            )

            if abs(
                probability_sum
                - 1.0
            ) > 1e-6:

                raise PredictionSourceNotReadyError(
                    (
                        f"Fixture {fixture_id!r} "
                        "probabilities do not sum "
                        f"to 1.0: {probability_sum}"
                    )
                )

            if not _normalize_scalar(
                row.get(
                    "predicted_label"
                )
            ):

                raise PredictionSourceNotReadyError(
                    (
                        f"Fixture {fixture_id!r} "
                        "has empty predicted_label."
                    )
                )

            confidence_raw = _normalize_scalar(
                row.get(
                    "confidence"
                )
            )

            try:

                confidence_value = float(
                    confidence_raw
                )

            except (
                TypeError,
                ValueError,
            ) as exc:

                raise PredictionSourceNotReadyError(
                    (
                        f"Fixture {fixture_id!r} "
                        "has invalid confidence."
                    )
                ) from exc

            if not (
                0.0
                <= confidence_value
                <= 1.0
            ):

                raise PredictionSourceNotReadyError(
                    (
                        f"Fixture {fixture_id!r} "
                        "has confidence outside [0,1]."
                    )
                )

        if (
            len(
                fixture_ids
            )
            !=
            len(
                set(
                    fixture_ids
                )
            )
        ):

            raise PredictionSourceNotReadyError(
                (
                    "Production predictions contain "
                    "duplicate fixture_id values."
                )
            )

        return {

            "status":
                "PASS",

            "source":
                "production_predictions",

            "prediction_count":
                len(
                    prediction_rows
                ),

            "column_count":
                len(
                    prediction_fields
                ),

            "fixture_id_unique":
                True,

            "required_schema_present":
                True,

            "identity_complete":
                True,

            "probabilities_valid":
                True,

            "probabilities_sum_to_one":
                True,

            "prediction_labels_present":
                True,

            "confidence_valid":
                True,

            "stage7_8_verified":
                True,

            "stage7_9_verified":
                True,

            "stage8_final_verified":
                True,

            "locked_dependency_hashes_current":
                True,

            "source_sha256":
                _sha256_file(
                    self.predictions_file
                ),
        }

    # ========================================================
    # 9.2.2 Fixture Identity Reconciliation
    # ========================================================

    def reconcile_fixture_identity(
        self,
    ) -> dict:

        source_gate = (
            self.validate_prediction_source()
        )

        (
            prediction_fields,
            prediction_rows,
        ) = _load_csv(
            self.predictions_file
        )

        (
            context_fields,
            context_rows,
        ) = _load_csv(
            self.context_file
        )

        for field in REQUIRED_IDENTITY_FIELDS:

            if (
                field
                not in prediction_fields
            ):

                raise FixtureIdentityError(
                    (
                        "Prediction source missing "
                        f"identity field {field!r}."
                    )
                )

            if (
                field
                not in context_fields
            ):

                raise FixtureIdentityError(
                    (
                        "Context source missing "
                        f"identity field {field!r}."
                    )
                )

        prediction_index = {}

        for row in prediction_rows:

            fixture_id = (
                _require_non_empty(
                    row,
                    "fixture_id",
                    fixture_id=
                        "<unknown>",
                    source_name=
                        "production_predictions",
                )
            )

            if (
                fixture_id
                in prediction_index
            ):

                raise FixtureIdentityError(
                    (
                        "Duplicate prediction fixture_id: "
                        f"{fixture_id}"
                    )
                )

            prediction_index[
                fixture_id
            ] = row

        context_index = {}

        for row in context_rows:

            fixture_id = (
                _require_non_empty(
                    row,
                    "fixture_id",
                    fixture_id=
                        "<unknown>",
                    source_name=
                        "enriched_upcoming_fixtures",
                )
            )

            if (
                fixture_id
                in context_index
            ):

                raise FixtureIdentityError(
                    (
                        "Duplicate context fixture_id: "
                        f"{fixture_id}"
                    )
                )

            context_index[
                fixture_id
            ] = row

        prediction_ids = set(
            prediction_index.keys()
        )

        context_ids = set(
            context_index.keys()
        )

        only_prediction = sorted(
            prediction_ids
            -
            context_ids
        )

        only_context = sorted(
            context_ids
            -
            prediction_ids
        )

        if only_prediction:

            raise FixtureIdentityError(
                (
                    "Prediction fixtures missing from "
                    "context source. Example: "
                    f"{only_prediction[:5]}"
                )
            )

        if only_context:

            raise FixtureIdentityError(
                (
                    "Context fixtures missing from "
                    "prediction source. Example: "
                    f"{only_context[:5]}"
                )
            )

        if (
            len(
                prediction_rows
            )
            !=
            len(
                context_rows
            )
        ):

            raise FixtureIdentityError(
                (
                    "Prediction/context row counts "
                    "do not match."
                )
            )

        identity_mismatches = []

        for fixture_id in sorted(
            prediction_ids
        ):

            prediction = (
                prediction_index[
                    fixture_id
                ]
            )

            context = (
                context_index[
                    fixture_id
                ]
            )

            for field in REQUIRED_IDENTITY_FIELDS:

                prediction_value = (
                    _require_non_empty(
                        prediction,
                        field,
                        fixture_id=fixture_id,
                        source_name=
                            "production_predictions",
                    )
                )

                context_value = (
                    _require_non_empty(
                        context,
                        field,
                        fixture_id=fixture_id,
                        source_name=
                            "enriched_upcoming_fixtures",
                    )
                )

                if (
                    prediction_value
                    !=
                    context_value
                ):

                    identity_mismatches.append(
                        {
                            "fixture_id":
                                fixture_id,

                            "field":
                                field,

                            "prediction":
                                prediction_value,

                            "context":
                                context_value,
                        }
                    )

            for field in OPTIONAL_IDENTITY_VALIDATION_FIELDS:

                if (
                    field
                    in prediction_fields
                    and
                    field
                    in context_fields
                ):

                    prediction_value = (
                        _normalize_scalar(
                            prediction.get(
                                field
                            )
                        )
                    )

                    context_value = (
                        _normalize_scalar(
                            context.get(
                                field
                            )
                        )
                    )

                    if (
                        prediction_value
                        != context_value
                    ):

                        identity_mismatches.append(
                            {
                                "fixture_id":
                                    fixture_id,

                                "field":
                                    field,

                                "prediction":
                                    prediction_value,

                                "context":
                                    context_value,
                            }
                        )

        if identity_mismatches:

            raise FixtureIdentityError(
                (
                    "Prediction/context fixture identity "
                    "mismatch detected. Example: "
                    f"{identity_mismatches[:5]}"
                )
            )

        common_date_field = (
            _find_date_field(
                prediction_fields,
                context_fields,
            )
        )

        date_match_verified = False

        if common_date_field:

            date_mismatches = []

            for fixture_id in sorted(
                prediction_ids
            ):

                prediction_date = (
                    _normalize_scalar(
                        prediction_index[
                            fixture_id
                        ].get(
                            common_date_field
                        )
                    )
                )

                context_date = (
                    _normalize_scalar(
                        context_index[
                            fixture_id
                        ].get(
                            common_date_field
                        )
                    )
                )

                if (
                    prediction_date
                    != context_date
                ):

                    date_mismatches.append(
                        fixture_id
                    )

            if date_mismatches:

                raise FixtureIdentityError(
                    (
                        f"Common date field "
                        f"{common_date_field!r} "
                        "does not match for all fixtures. "
                        f"Example: {date_mismatches[:5]}"
                    )
                )

            date_match_verified = True

        return {

            "status":
                "PASS",

            "prediction_source_gate":
                source_gate,

            "prediction_fixture_count":
                len(
                    prediction_rows
                ),

            "context_fixture_count":
                len(
                    context_rows
                ),

            "fixture_sets_exact":
                True,

            "fixture_id_unique_prediction":
                True,

            "fixture_id_unique_context":
                True,

            "fixture_id_exact_match":
                True,

            "home_team_id_exact_match":
                True,

            "home_team_name_exact_match":
                True,

            "away_team_id_exact_match":
                True,

            "away_team_name_exact_match":
                True,

            "season_exact_match_if_shared":
                True,

            "shared_date_field":
                common_date_field,

            "shared_date_field_exact_match":
                date_match_verified,

            "fuzzy_matching_used":
                False,

            "best_effort_fallback_used":
                False,

            "unmatched_prediction_count":
                0,

            "unmatched_context_count":
                0,

            "identity_mismatch_count":
                0,

            "prediction_sha256":
                _sha256_file(
                    self.predictions_file
                ),

            "context_sha256":
                _sha256_file(
                    self.context_file
                ),
        }
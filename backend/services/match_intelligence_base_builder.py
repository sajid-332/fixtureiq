"""
FixtureIQ Stage 9.2.3
Strict Prediction-Context Join Builder.

Builds the canonical Stage 9 base intelligence dataset.

Rules:
- Stage 8 enriched fixture context is the base row structure.
- Stage 7 prediction values are appended by exact fixture_id join.
- fixture identity must already reconcile exactly.
- Stage 7 probability / label / confidence values are copied exactly.
- Stage 8 context values are copied exactly.
- source context row order is preserved.
- no fuzzy matching.
- no best-effort fallback.
- no model loading.
- no model execution.
- no prediction modification.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from backend.services.prediction_context_join_service import (
    PredictionContextJoinService,
)


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


CONTRACT_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract.json"
)

CONTRACT_VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract_verification.json"
)

PREDICTIONS_FILE = (
    PRODUCTION_DIR
    / "production_predictions.csv"
)

CONTEXT_FILE = (
    CONTEXT_DIR
    / "enriched_upcoming_fixtures.csv"
)

BASE_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_base.csv"
)


# ============================================================
# Exceptions
# ============================================================

class MatchIntelligenceBaseBuildError(
    RuntimeError
):
    """Raised when the Stage 9.2.3 strict join cannot be built."""


# ============================================================
# Helpers
# ============================================================

def _load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise MatchIntelligenceBaseBuildError(
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

        raise MatchIntelligenceBaseBuildError(
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

        raise MatchIntelligenceBaseBuildError(
            f"Required CSV missing: {path}"
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
            dict(row)
            for row in reader
        ]

    if not fields:

        raise MatchIntelligenceBaseBuildError(
            f"CSV has no columns: {path}"
        )

    if not rows:

        raise MatchIntelligenceBaseBuildError(
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

        raise MatchIntelligenceBaseBuildError(
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


def _relative_path(
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


def write_csv_atomic(
    path: Path,
    fields: list[str],
    rows: list[dict[str, str]],
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temporary.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields,
            extrasaction="raise",
        )

        writer.writeheader()

        writer.writerows(
            rows
        )

    temporary.replace(
        path
    )


# ============================================================
# Builder
# ============================================================

class MatchIntelligenceBaseBuilder:

    def __init__(
        self,
        *,
        contract_file: Path = CONTRACT_FILE,
        contract_verification_file: Path = CONTRACT_VERIFICATION_FILE,
        predictions_file: Path = PREDICTIONS_FILE,
        context_file: Path = CONTEXT_FILE,
        base_file: Path = BASE_FILE,
        join_service: PredictionContextJoinService | None = None,
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

        self.context_file = Path(
            context_file
        )

        self.base_file = Path(
            base_file
        )

        self.join_service = (
            join_service
            if join_service is not None
            else PredictionContextJoinService()
        )

    def build(
        self,
    ) -> dict:

        # ====================================================
        # Upstream Stage 9.2.1 / 9.2.2 gates
        # ====================================================

        source_gate = (
            self.join_service
            .validate_prediction_source()
        )

        if (
            source_gate.get(
                "status"
            )
            != "PASS"
        ):

            raise MatchIntelligenceBaseBuildError(
                "Prediction source gate is not PASS."
            )

        reconciliation = (
            self.join_service
            .reconcile_fixture_identity()
        )

        if (
            reconciliation.get(
                "status"
            )
            != "PASS"
        ):

            raise MatchIntelligenceBaseBuildError(
                "Fixture identity reconciliation is not PASS."
            )

        # ====================================================
        # Locked contract
        # ====================================================

        contract = _load_json(
            self.contract_file
        )

        contract_verification = _load_json(
            self.contract_verification_file
        )

        if (
            contract.get(
                "status"
            )
            !=
            "LOCKED_MATCH_INTELLIGENCE_CONTRACT"
        ):

            raise MatchIntelligenceBaseBuildError(
                "Stage 9.1 contract is not locked."
            )

        if (
            contract.get(
                "stage_9_1_complete"
            )
            is not True
        ):

            raise MatchIntelligenceBaseBuildError(
                "Stage 9.1 contract is incomplete."
            )

        if (
            contract_verification.get(
                "status"
            )
            != "PASS"
        ):

            raise MatchIntelligenceBaseBuildError(
                "Stage 9.1 verification is not PASS."
            )

        if (
            contract_verification.get(
                "contract_sha256"
            )
            !=
            _sha256_file(
                self.contract_file
            )
        ):

            raise MatchIntelligenceBaseBuildError(
                "Stage 9.1 contract SHA verification failed."
            )

        # ====================================================
        # Locked schema
        # ====================================================

        schema = (
            contract.get(
                "stage_9_1_3",
                {}
            ).get(
                "canonical_schema",
                {}
            )
        )

        source_context_contract = (
            schema.get(
                "source_context_fields",
                {}
            )
        )

        source_prediction_contract = (
            schema.get(
                "source_prediction_fields",
                {}
            )
        )

        base_schema_contract = (
            schema.get(
                "base_intelligence_schema",
                {}
            )
        )

        output_contract = (
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

        if (
            output_contract.get(
                "match_intelligence_base",
                {}
            ).get(
                "path"
            )
            !=
            _relative_path(
                BASE_FILE
            )
        ):

            raise MatchIntelligenceBaseBuildError(
                "Stage 9 base output path contract invalid."
            )

        # ====================================================
        # Sources
        # ====================================================

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

        contract_context_fields = (
            source_context_contract.get(
                "fields",
                [],
            )
        )

        if (
            context_fields
            != contract_context_fields
        ):

            raise MatchIntelligenceBaseBuildError(
                (
                    "Current Stage 8 context schema differs "
                    "from locked Stage 9.1 schema."
                )
            )

        source_prediction_fields = (
            source_prediction_contract.get(
                "fields",
                [],
            )
        )

        for field in source_prediction_fields:

            if (
                field
                not in prediction_fields
            ):

                raise MatchIntelligenceBaseBuildError(
                    (
                        "Production prediction source missing "
                        f"locked field {field!r}."
                    )
                )

        prediction_mapping = (
            source_prediction_contract.get(
                "copy_mapping",
                {}
            )
        )

        prediction_output_fields = (
            source_prediction_contract.get(
                "copied_output_fields",
                [],
            )
        )

        expected_prediction_output_fields = [

            prediction_mapping[
                source_field
            ]

            for source_field in (
                source_prediction_fields
            )
        ]

        if (
            prediction_output_fields
            !=
            expected_prediction_output_fields
        ):

            raise MatchIntelligenceBaseBuildError(
                "Prediction copy mapping contract inconsistent."
            )

        expected_base_fields = (
            list(
                context_fields
            )
            +
            list(
                prediction_output_fields
            )
        )

        locked_base_fields = (
            base_schema_contract.get(
                "fields",
                [],
            )
        )

        if (
            expected_base_fields
            != locked_base_fields
        ):

            raise MatchIntelligenceBaseBuildError(
                (
                    "Constructed base schema differs from "
                    "locked canonical schema."
                )
            )

        if (
            len(
                locked_base_fields
            )
            !=
            base_schema_contract.get(
                "column_count"
            )
        ):

            raise MatchIntelligenceBaseBuildError(
                "Locked base column count inconsistent."
            )

        # ====================================================
        # Prediction index
        # ====================================================

        prediction_index = {}

        for row in prediction_rows:

            fixture_id = str(
                row.get(
                    "fixture_id",
                    "",
                )
            ).strip()

            if not fixture_id:

                raise MatchIntelligenceBaseBuildError(
                    "Prediction fixture_id cannot be empty."
                )

            if (
                fixture_id
                in prediction_index
            ):

                raise MatchIntelligenceBaseBuildError(
                    (
                        "Duplicate prediction fixture_id: "
                        f"{fixture_id}"
                    )
                )

            prediction_index[
                fixture_id
            ] = row

        # ====================================================
        # Exact strict join
        # ====================================================

        output_rows = []

        seen_context_ids = set()

        for context_row in context_rows:

            fixture_id = str(
                context_row.get(
                    "fixture_id",
                    "",
                )
            ).strip()

            if not fixture_id:

                raise MatchIntelligenceBaseBuildError(
                    "Context fixture_id cannot be empty."
                )

            if (
                fixture_id
                in seen_context_ids
            ):

                raise MatchIntelligenceBaseBuildError(
                    (
                        "Duplicate context fixture_id: "
                        f"{fixture_id}"
                    )
                )

            seen_context_ids.add(
                fixture_id
            )

            prediction_row = (
                prediction_index.get(
                    fixture_id
                )
            )

            if prediction_row is None:

                raise MatchIntelligenceBaseBuildError(
                    (
                        "No exact prediction match for "
                        f"fixture {fixture_id!r}."
                    )
                )

            # -----------------------------------------------
            # Re-check canonical identity at join time
            # -----------------------------------------------

            for identity_field in (

                "fixture_id",

                "home_team_id",
                "home_team_name",

                "away_team_id",
                "away_team_name",
            ):

                prediction_value = str(
                    prediction_row.get(
                        identity_field,
                        "",
                    )
                ).strip()

                context_value = str(
                    context_row.get(
                        identity_field,
                        "",
                    )
                ).strip()

                if (
                    prediction_value
                    != context_value
                ):

                    raise MatchIntelligenceBaseBuildError(
                        (
                            f"Identity mismatch for fixture "
                            f"{fixture_id!r}, field "
                            f"{identity_field!r}."
                        )
                    )

            # -----------------------------------------------
            # Exact context copy
            # -----------------------------------------------

            output_row = {

                field:
                    context_row.get(
                        field,
                        "",
                    )

                for field in context_fields
            }

            # -----------------------------------------------
            # Exact Stage 7 prediction copy
            # -----------------------------------------------

            for source_field in source_prediction_fields:

                output_field = (
                    prediction_mapping[
                        source_field
                    ]
                )

                output_row[
                    output_field
                ] = prediction_row.get(
                    source_field,
                    "",
                )

            if (
                list(
                    output_row.keys()
                )
                != locked_base_fields
            ):

                raise MatchIntelligenceBaseBuildError(
                    (
                        "Output row field order differs "
                        "from locked base schema."
                    )
                )

            output_rows.append(
                output_row
            )

        # ====================================================
        # Exact fixture-set confirmation
        # ====================================================

        prediction_fixture_ids = set(
            prediction_index.keys()
        )

        context_fixture_ids = set(
            seen_context_ids
        )

        if (
            prediction_fixture_ids
            != context_fixture_ids
        ):

            raise MatchIntelligenceBaseBuildError(
                "Prediction/context fixture sets differ."
            )

        if (
            len(
                output_rows
            )
            !=
            len(
                context_rows
            )
            or
            len(
                output_rows
            )
            !=
            len(
                prediction_rows
            )
        ):

            raise MatchIntelligenceBaseBuildError(
                "Strict join row count mismatch."
            )

        # ====================================================
        # Dependency identity
        # ====================================================

        allowed_inputs = (
            contract.get(
                "stage_9_1_1",
                {}
            ).get(
                "allowed_inputs",
                {}
            )
        )

        dependency_identity = {}

        for name, item in allowed_inputs.items():

            source_path = (
                BASE_DIR
                / item.get(
                    "path",
                    "",
                )
            )

            current_sha = (
                _sha256_file(
                    source_path
                )
            )

            if (
                current_sha
                != item.get(
                    "sha256"
                )
            ):

                raise MatchIntelligenceBaseBuildError(
                    (
                        f"Locked dependency {name!r} "
                        "changed before Stage 9.2.3 build."
                    )
                )

            dependency_identity[
                name
            ] = {

                "path":
                    item.get(
                        "path"
                    ),

                "sha256":
                    current_sha,
            }

        return {

            "status":
                "PASS",

            "fields":
                locked_base_fields,

            "rows":
                output_rows,

            "fixture_count":
                len(
                    output_rows
                ),

            "column_count":
                len(
                    locked_base_fields
                ),

            "context_column_count":
                len(
                    context_fields
                ),

            "prediction_copy_field_count":
                len(
                    prediction_output_fields
                ),

            "source_order_preserved":
                True,

            "fixture_sets_exact":
                True,

            "strict_fixture_id_join":
                True,

            "strict_identity_revalidated":
                True,

            "context_values_copied_exactly":
                True,

            "prediction_values_copied_exactly":
                True,

            "probabilities_modified":
                False,

            "prediction_labels_modified":
                False,

            "source_confidence_modified":
                False,

            "fuzzy_matching_used":
                False,

            "best_effort_fallback_used":
                False,

            "dependency_identity":
                dependency_identity,

            "prediction_source_sha256":
                _sha256_file(
                    self.predictions_file
                ),

            "context_source_sha256":
                _sha256_file(
                    self.context_file
                ),
        }

    def build_and_write(
        self,
    ) -> dict:

        result = self.build()

        write_csv_atomic(
            self.base_file,
            result[
                "fields"
            ],
            result[
                "rows"
            ],
        )

        result[
            "output_path"
        ] = _relative_path(
            self.base_file
        )

        result[
            "output_sha256"
        ] = _sha256_file(
            self.base_file
        )

        return result
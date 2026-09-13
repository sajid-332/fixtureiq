"""
FixtureIQ Stage 9.2.4
Independent Strict Join Validator.

This validator does NOT use MatchIntelligenceBaseBuilder.

It independently reconstructs the expected Stage 9.2 base row
from canonical Stage 7 predictions + Stage 8 fixture context and
compares it with match_intelligence_base.csv.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path


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

REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_base_report.json"
)


class MatchIntelligenceBaseValidationError(
    RuntimeError
):
    """Raised when independent Stage 9.2 validation fails."""


def _load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise MatchIntelligenceBaseValidationError(
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

        raise MatchIntelligenceBaseValidationError(
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

        raise MatchIntelligenceBaseValidationError(
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

        raise MatchIntelligenceBaseValidationError(
            f"CSV has no columns: {path}"
        )

    return (
        fields,
        rows,
    )


def _sha256_file(
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


def _parse_aware_timestamp(
    value: str,
) -> datetime:

    if not isinstance(
        value,
        str,
    ):

        raise MatchIntelligenceBaseValidationError(
            "Expected timestamp string."
        )

    normalized = (
        value.replace(
            "Z",
            "+00:00",
        )
    )

    try:

        parsed = datetime.fromisoformat(
            normalized
        )

    except ValueError as exc:

        raise MatchIntelligenceBaseValidationError(
            f"Invalid timestamp: {value}"
        ) from exc

    if (
        parsed.tzinfo
        is None
    ):

        raise MatchIntelligenceBaseValidationError(
            "Timestamp is not timezone-aware."
        )

    return parsed


class MatchIntelligenceBaseValidator:

    def __init__(
        self,
        *,
        contract_file: Path = CONTRACT_FILE,
        contract_verification_file: Path = CONTRACT_VERIFICATION_FILE,
        predictions_file: Path = PREDICTIONS_FILE,
        context_file: Path = CONTEXT_FILE,
        base_file: Path = BASE_FILE,
        report_file: Path = REPORT_FILE,
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

        self.report_file = Path(
            report_file
        )

    def validate(
        self,
    ) -> dict:

        contract = _load_json(
            self.contract_file
        )

        contract_verification = _load_json(
            self.contract_verification_file
        )

        report = _load_json(
            self.report_file
        )

        if (
            contract.get(
                "status"
            )
            !=
            "LOCKED_MATCH_INTELLIGENCE_CONTRACT"
        ):

            raise MatchIntelligenceBaseValidationError(
                "Stage 9.1 contract is not locked."
            )

        if (
            contract_verification.get(
                "status"
            )
            != "PASS"
        ):

            raise MatchIntelligenceBaseValidationError(
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

            raise MatchIntelligenceBaseValidationError(
                "Locked Stage 9.1 contract SHA mismatch."
            )

        if (
            report.get(
                "sub_stages",
                {}
            ).get(
                "9.2.3"
            )
            != "PASS"
        ):

            raise MatchIntelligenceBaseValidationError(
                "Stage 9.2.3 evidence is not PASS."
            )

        if (
            report.get(
                "strict_prediction_context_join"
            )
            != "VERIFIED"
        ):

            raise MatchIntelligenceBaseValidationError(
                "Strict join is not VERIFIED."
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

        (
            base_fields,
            base_rows,
        ) = _load_csv(
            self.base_file
        )

        schema = (
            contract.get(
                "stage_9_1_3",
                {}
            ).get(
                "canonical_schema",
                {}
            )
        )

        locked_context_fields = (
            schema.get(
                "source_context_fields",
                {}
            ).get(
                "fields",
                [],
            )
        )

        source_prediction_fields = (
            schema.get(
                "source_prediction_fields",
                {}
            ).get(
                "fields",
                [],
            )
        )

        prediction_mapping = (
            schema.get(
                "source_prediction_fields",
                {}
            ).get(
                "copy_mapping",
                {},
            )
        )

        locked_base_fields = (
            schema.get(
                "base_intelligence_schema",
                {}
            ).get(
                "fields",
                [],
            )
        )

        if (
            context_fields
            != locked_context_fields
        ):

            raise MatchIntelligenceBaseValidationError(
                "Context schema differs from locked contract."
            )

        if (
            base_fields
            != locked_base_fields
        ):

            raise MatchIntelligenceBaseValidationError(
                "Base output schema differs from locked contract."
            )

        for field in source_prediction_fields:

            if field not in prediction_fields:

                raise MatchIntelligenceBaseValidationError(
                    (
                        "Prediction source missing field: "
                        f"{field}"
                    )
                )

        # ====================================================
        # Unique source indices
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

                raise MatchIntelligenceBaseValidationError(
                    "Empty prediction fixture_id."
                )

            if fixture_id in prediction_index:

                raise MatchIntelligenceBaseValidationError(
                    "Duplicate prediction fixture_id."
                )

            prediction_index[
                fixture_id
            ] = row

        context_index = {}

        context_order = []

        for row in context_rows:

            fixture_id = str(
                row.get(
                    "fixture_id",
                    "",
                )
            ).strip()

            if not fixture_id:

                raise MatchIntelligenceBaseValidationError(
                    "Empty context fixture_id."
                )

            if fixture_id in context_index:

                raise MatchIntelligenceBaseValidationError(
                    "Duplicate context fixture_id."
                )

            context_index[
                fixture_id
            ] = row

            context_order.append(
                fixture_id
            )

        output_index = {}

        output_order = []

        for row in base_rows:

            fixture_id = str(
                row.get(
                    "fixture_id",
                    "",
                )
            ).strip()

            if not fixture_id:

                raise MatchIntelligenceBaseValidationError(
                    "Empty output fixture_id."
                )

            if fixture_id in output_index:

                raise MatchIntelligenceBaseValidationError(
                    "Duplicate output fixture_id."
                )

            output_index[
                fixture_id
            ] = row

            output_order.append(
                fixture_id
            )

        fixture_set = set(
            prediction_index.keys()
        )

        if (
            fixture_set
            !=
            set(
                context_index.keys()
            )
            or
            fixture_set
            !=
            set(
                output_index.keys()
            )
        ):

            raise MatchIntelligenceBaseValidationError(
                "Prediction/context/output fixture sets differ."
            )

        if (
            len(
                prediction_rows
            )
            !=
            len(
                context_rows
            )
            or
            len(
                prediction_rows
            )
            !=
            len(
                base_rows
            )
        ):

            raise MatchIntelligenceBaseValidationError(
                "Prediction/context/output row counts differ."
            )

        if (
            output_order
            != context_order
        ):

            raise MatchIntelligenceBaseValidationError(
                "Stage 8 context source order was not preserved."
            )

        # ====================================================
        # Independent exact reconstruction
        # ====================================================

        context_value_comparisons = 0
        prediction_value_comparisons = 0

        probability_comparisons = 0
        label_comparisons = 0
        confidence_comparisons = 0

        for fixture_id in context_order:

            context_row = (
                context_index[
                    fixture_id
                ]
            )

            prediction_row = (
                prediction_index[
                    fixture_id
                ]
            )

            output_row = (
                output_index[
                    fixture_id
                ]
            )

            # -----------------------------------------------
            # Identity exactness
            # -----------------------------------------------

            for identity_field in (

                "fixture_id",

                "home_team_id",
                "home_team_name",

                "away_team_id",
                "away_team_name",
            ):

                prediction_value = (
                    prediction_row.get(
                        identity_field,
                        "",
                    )
                )

                context_value = (
                    context_row.get(
                        identity_field,
                        "",
                    )
                )

                if (
                    prediction_value
                    != context_value
                ):

                    raise MatchIntelligenceBaseValidationError(
                        (
                            f"Source identity mismatch: "
                            f"{fixture_id}, {identity_field}"
                        )
                    )

            # -----------------------------------------------
            # Stage 8 context exactness
            # -----------------------------------------------

            for field in context_fields:

                if (
                    output_row.get(
                        field
                    )
                    !=
                    context_row.get(
                        field
                    )
                ):

                    raise MatchIntelligenceBaseValidationError(
                        (
                            f"Context value mismatch for "
                            f"fixture {fixture_id}, field {field}"
                        )
                    )

                context_value_comparisons += 1

            # -----------------------------------------------
            # Stage 7 exact copy
            # -----------------------------------------------

            for source_field in source_prediction_fields:

                output_field = (
                    prediction_mapping[
                        source_field
                    ]
                )

                if (
                    output_row.get(
                        output_field
                    )
                    !=
                    prediction_row.get(
                        source_field
                    )
                ):

                    raise MatchIntelligenceBaseValidationError(
                        (
                            f"Prediction copy mismatch for "
                            f"fixture {fixture_id}, "
                            f"field {source_field}"
                        )
                    )

                prediction_value_comparisons += 1

                if source_field in {

                    "prob_home_win",
                    "prob_draw",
                    "prob_away_win",
                }:

                    probability_comparisons += 1

                elif (
                    source_field
                    == "predicted_label"
                ):

                    label_comparisons += 1

                elif (
                    source_field
                    == "confidence"
                ):

                    confidence_comparisons += 1

        # ====================================================
        # Artifact / provenance identity
        # ====================================================

        base_artifact = report.get(
            "base_artifact",
            {}
        )

        if (
            base_artifact.get(
                "sha256"
            )
            !=
            _sha256_file(
                self.base_file
            )
        ):

            raise MatchIntelligenceBaseValidationError(
                "Base artifact SHA mismatch."
            )

        if (
            base_artifact.get(
                "fixture_count"
            )
            !=
            len(
                base_rows
            )
        ):

            raise MatchIntelligenceBaseValidationError(
                "Base artifact fixture count mismatch."
            )

        if (
            base_artifact.get(
                "column_count"
            )
            !=
            len(
                base_fields
            )
        ):

            raise MatchIntelligenceBaseValidationError(
                "Base artifact column count mismatch."
            )

        provenance = report.get(
            "provenance",
            {}
        )

        generated_at = provenance.get(
            "generated_at_utc"
        )

        _parse_aware_timestamp(
            generated_at
        )

        if (
            provenance.get(
                "hash_algorithm"
            )
            != "SHA256"
        ):

            raise MatchIntelligenceBaseValidationError(
                "Provenance hash algorithm is not SHA256."
            )

        if (
            provenance.get(
                "base_output_sha256"
            )
            !=
            _sha256_file(
                self.base_file
            )
        ):

            raise MatchIntelligenceBaseValidationError(
                "Provenance base SHA mismatch."
            )

        # ====================================================
        # Full dependency identity
        # ====================================================

        dependency_identity = report.get(
            "dependency_identity",
            {}
        )

        contract_dependencies = (
            contract.get(
                "stage_9_1_1",
                {}
            ).get(
                "allowed_inputs",
                {}
            )
        )

        for name, item in contract_dependencies.items():

            source_path = (
                BASE_DIR
                / item[
                    "path"
                ]
            )

            current_sha = _sha256_file(
                source_path
            )

            if (
                item.get(
                    "dependency_hash_policy"
                )
                != "CAPTURE_AT_DOWNSTREAM_BUILD"
            ):

                raise MatchIntelligenceBaseValidationError(
                    (
                        f"Dependency {name!r} has invalid "
                        "snapshot hash policy."
                    )
                )

            if (
                item.get(
                    "contract_runtime_hash_pin"
                )
                is not False
            ):

                raise MatchIntelligenceBaseValidationError(
                    (
                        f"Dependency {name!r} incorrectly "
                        "uses a permanent contract hash pin."
                    )
                )

            report_item = (
                dependency_identity.get(
                    name,
                    {}
                )
            )

            if (
                report_item.get(
                    "sha256"
                )
                != current_sha
            ):

                raise MatchIntelligenceBaseValidationError(
                    (
                        f"Report dependency SHA stale: "
                        f"{name}"
                    )
                )

        if (
            dependency_identity.get(
                "stage9_intelligence_contract",
                {}
            ).get(
                "sha256"
            )
            !=
            _sha256_file(
                self.contract_file
            )
        ):

            raise MatchIntelligenceBaseValidationError(
                "Report Stage 9 contract SHA stale."
            )

        if (
            dependency_identity.get(
                "stage9_intelligence_contract_verification",
                {}
            ).get(
                "sha256"
            )
            !=
            _sha256_file(
                self.contract_verification_file
            )
        ):

            raise MatchIntelligenceBaseValidationError(
                "Report Stage 9 verification SHA stale."
            )

        return {

            "status":
                "PASS",

            "fixture_count":
                len(
                    base_rows
                ),

            "column_count":
                len(
                    base_fields
                ),

            "fixture_sets_exact":
                True,

            "output_fixture_ids_unique":
                True,

            "source_order_preserved":
                True,

            "schema_exact":
                True,

            "strict_identity_exact":
                True,

            "context_values_exact":
                True,

            "prediction_values_exact":
                True,

            "probabilities_exact":
                True,

            "prediction_labels_exact":
                True,

            "source_confidence_exact":
                True,

            "exact_independent_reconstruction":
                True,

            "dependency_identity_current":
                True,

            "provenance_verified":
                True,

            "context_value_comparisons":
                context_value_comparisons,

            "prediction_value_comparisons":
                prediction_value_comparisons,

            "probability_comparisons":
                probability_comparisons,

            "label_comparisons":
                label_comparisons,

            "confidence_comparisons":
                confidence_comparisons,

            "output_sha256":
                _sha256_file(
                    self.base_file
                ),
        }
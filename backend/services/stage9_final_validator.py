"""
FixtureIQ Stage 9.8.1
Independent Final Stage 9 Artifact Validator.

Verifies the completed Stage 9 data chain without using
any Stage 9 builder.

Checks:
- Stage 9.1 locked policy
- Stage 9.2 verified base
- Stage 9.3 derived intelligence
- Stage 9.4 confidence / uncertainty
- Stage 9.5 explanations
- Stage 9.6 API verification
- Stage 9.7 runtime verification
- exact canonical schema
- exact preservation of Stage 9.2 base values
- core derived arithmetic
- Stage 7 probability preservation
- final dependency SHA integrity
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from decimal import Decimal, InvalidOperation
from pathlib import Path


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
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

BASE_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_base.csv"
)

BASE_REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_base_report.json"
)

INTELLIGENCE_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence.csv"
)

REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_report.json"
)

API_VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "intelligence_api_verification.json"
)

RUNTIME_VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "intelligence_runtime_verification.json"
)


ALLOWED_BANDS = {
    "VERY_LOW",
    "LOW",
    "MODERATE",
    "HIGH",
    "VERY_HIGH",
}

ALLOWED_ALIGNMENTS = {
    "SUPPORTIVE",
    "MIXED",
    "CONTRADICTORY",
    "NEUTRAL",
}


class Stage9FinalValidationError(
    RuntimeError
):
    pass


def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise Stage9FinalValidationError(
            f"Missing JSON artifact: {path}"
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

        raise Stage9FinalValidationError(
            f"Expected JSON object: {path}"
        )

    return payload


def load_csv(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:

    if not path.exists():

        raise Stage9FinalValidationError(
            f"Missing CSV artifact: {path}"
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

        raise Stage9FinalValidationError(
            f"No columns: {path}"
        )

    if not rows:

        raise Stage9FinalValidationError(
            f"No rows: {path}"
        )

    return (
        fields,
        rows,
    )


def sha256_file(
    path: Path,
) -> str:

    if not path.exists():

        raise Stage9FinalValidationError(
            f"Missing artifact: {path}"
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


def decimal_value(
    row: dict[str, str],
    field: str,
) -> Decimal:

    raw = str(
        row.get(
            field,
            "",
        )
    ).strip()

    if not raw:

        raise Stage9FinalValidationError(
            f"Empty numeric field: {field}"
        )

    try:

        value = Decimal(
            raw
        )

    except InvalidOperation as exc:

        raise Stage9FinalValidationError(
            (
                f"Invalid numeric field "
                f"{field}={raw!r}"
            )
        ) from exc

    if not value.is_finite():

        raise Stage9FinalValidationError(
            f"Non-finite field: {field}"
        )

    return value


def integer_value(
    row: dict[str, str],
    field: str,
) -> int:

    value = decimal_value(
        row,
        field,
    )

    if (
        value
        !=
        value.to_integral_value()
    ):

        raise Stage9FinalValidationError(
            f"{field} is not integer-like."
        )

    return int(
        value
    )


def confidence_band(
    confidence: float,
) -> str:

    if confidence < 0.40:
        return "VERY_LOW"

    if confidence < 0.50:
        return "LOW"

    if confidence < 0.60:
        return "MODERATE"

    if confidence < 0.70:
        return "HIGH"

    return "VERY_HIGH"


def uncertainty_band(
    normalized_entropy: float,
) -> str:

    if normalized_entropy < 0.20:
        return "VERY_LOW"

    if normalized_entropy < 0.40:
        return "LOW"

    if normalized_entropy < 0.60:
        return "MODERATE"

    if normalized_entropy < 0.80:
        return "HIGH"

    return "VERY_HIGH"


class Stage9FinalValidator:

    def validate(
        self,
    ) -> dict:

        contract = load_json(
            CONTRACT_FILE
        )

        contract_verification = load_json(
            CONTRACT_VERIFICATION_FILE
        )

        base_report = load_json(
            BASE_REPORT_FILE
        )

        report = load_json(
            REPORT_FILE
        )

        api_verification = load_json(
            API_VERIFICATION_FILE
        )

        runtime_verification = load_json(
            RUNTIME_VERIFICATION_FILE
        )

        # ====================================================
        # Stage 9.1
        # ====================================================

        if (
            contract.get(
                "status"
            )
            !=
            "LOCKED_MATCH_INTELLIGENCE_CONTRACT"
        ):

            raise Stage9FinalValidationError(
                "Stage 9.1 contract not locked."
            )

        if (
            contract.get(
                "stage_9_1_complete"
            )
            is not True
        ):

            raise Stage9FinalValidationError(
                "Stage 9.1 incomplete."
            )

        if (
            contract_verification.get(
                "status"
            )
            != "PASS"
        ):

            raise Stage9FinalValidationError(
                "Stage 9.1 verification not PASS."
            )

        if (
            contract_verification.get(
                "contract_sha256"
            )
            !=
            sha256_file(
                CONTRACT_FILE
            )
        ):

            raise Stage9FinalValidationError(
                "Stage 9.1 contract SHA mismatch."
            )

        snapshot_policy = contract.get(
            "dependency_snapshot_policy",
            {}
        )

        if (
            snapshot_policy.get(
                "mode"
            )
            !=
            "CAPTURE_AT_DOWNSTREAM_BUILD"
        ):

            raise Stage9FinalValidationError(
                "Dynamic dependency policy mismatch."
            )

        if (
            snapshot_policy.get(
                "contract_permanently_pins_dynamic_hashes"
            )
            is not False
        ):

            raise Stage9FinalValidationError(
                "Permanent snapshot hash pin unexpectedly enabled."
            )

        # ====================================================
        # Stage 9.2
        # ====================================================

        if (
            base_report.get(
                "status"
            )
            != "PASS"
        ):

            raise Stage9FinalValidationError(
                "Stage 9.2 report not PASS."
            )

        if (
            base_report.get(
                "stage_9_2_complete"
            )
            is not True
        ):

            raise Stage9FinalValidationError(
                "Stage 9.2 incomplete."
            )

        if (
            base_report.get(
                "prediction_context_join_layer"
            )
            != "VERIFIED"
        ):

            raise Stage9FinalValidationError(
                "Stage 9.2 join layer not VERIFIED."
            )

        if (
            base_report.get(
                "base_artifact",
                {}
            ).get(
                "sha256"
            )
            !=
            sha256_file(
                BASE_FILE
            )
        ):

            raise Stage9FinalValidationError(
                "Stage 9.2 base SHA mismatch."
            )

        # ====================================================
        # Stage 9.3 → 9.5
        # ====================================================

        if (
            report.get(
                "status"
            )
            != "PASS"
        ):

            raise Stage9FinalValidationError(
                "Match intelligence report not PASS."
            )

        required_stage_flags = {

            "stage_9_3_complete":
                True,

            "stage_9_4_complete":
                True,

            "stage_9_5_complete":
                True,
        }

        for key, expected in (
            required_stage_flags.items()
        ):

            if (
                report.get(
                    key
                )
                is not expected
            ):

                raise Stage9FinalValidationError(
                    f"Missing completed stage flag: {key}"
                )

        if (
            report.get(
                "derived_match_intelligence"
            )
            != "VERIFIED"
        ):

            raise Stage9FinalValidationError(
                "Stage 9.3 not VERIFIED."
            )

        if (
            report.get(
                "confidence_uncertainty_layer"
            )
            != "VERIFIED"
        ):

            raise Stage9FinalValidationError(
                "Stage 9.4 not VERIFIED."
            )

        if (
            report.get(
                "match_explanation_engine"
            )
            != "VERIFIED"
        ):

            raise Stage9FinalValidationError(
                "Stage 9.5 not VERIFIED."
            )

        if (
            report.get(
                "output_artifact",
                {}
            ).get(
                "sha256"
            )
            !=
            sha256_file(
                INTELLIGENCE_FILE
            )
        ):

            raise Stage9FinalValidationError(
                "Final intelligence SHA mismatch."
            )

        # ====================================================
        # Stage 9.6
        # ====================================================

        if (
            api_verification.get(
                "status"
            )
            != "PASS"
            or
            api_verification.get(
                "stage_9_6_complete"
            )
            is not True
            or
            api_verification.get(
                "match_intelligence_rest_api"
            )
            != "VERIFIED"
        ):

            raise Stage9FinalValidationError(
                "Stage 9.6 API gate invalid."
            )

        # ====================================================
        # Stage 9.7
        # ====================================================

        if (
            runtime_verification.get(
                "status"
            )
            != "PASS"
            or
            runtime_verification.get(
                "stage_9_7_complete"
            )
            is not True
            or
            runtime_verification.get(
                "intelligence_runtime_safety"
            )
            != "VERIFIED"
        ):

            raise Stage9FinalValidationError(
                "Stage 9.7 runtime gate invalid."
            )

        if (
            runtime_verification.get(
                "stage9_ready_for_9_8"
            )
            is not True
        ):

            raise Stage9FinalValidationError(
                "Stage 9.7 did not authorize Stage 9.8."
            )

        if (
            runtime_verification.get(
                "runtime_policy"
            )
            !=
            (
                "DUAL_UPSTREAM_DEPENDENCY_"
                "PLUS_TEMPORAL_BOUNDARY"
            )
        ):

            raise Stage9FinalValidationError(
                "Stage 9.7 runtime policy mismatch."
            )

        # ====================================================
        # Dependency chains stored by 9.6 / 9.7
        # ====================================================

        expected_runtime_dependencies = {

            "stage9_intelligence_contract":
                CONTRACT_FILE,

            "stage9_intelligence_contract_verification":
                CONTRACT_VERIFICATION_FILE,

            "match_intelligence_base":
                BASE_FILE,

            "match_intelligence_base_report":
                BASE_REPORT_FILE,

            "match_intelligence":
                INTELLIGENCE_FILE,

            "match_intelligence_report":
                REPORT_FILE,

            "intelligence_api_verification":
                API_VERIFICATION_FILE,
        }

        runtime_dependencies = (
            runtime_verification.get(
                "dependency_identity",
                {}
            )
        )

        for name, path in (
            expected_runtime_dependencies.items()
        ):

            item = runtime_dependencies.get(
                name,
                {}
            )

            if (
                item.get(
                    "sha256"
                )
                !=
                sha256_file(
                    path
                )
            ):

                raise Stage9FinalValidationError(
                    (
                        "Stage 9.7 dependency SHA "
                        f"mismatch: {name}"
                    )
                )

        # ====================================================
        # Canonical CSV schema
        # ====================================================

        (
            base_fields,
            base_rows,
        ) = load_csv(
            BASE_FILE
        )

        (
            final_fields,
            final_rows,
        ) = load_csv(
            INTELLIGENCE_FILE
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

        locked_base_fields = (
            schema.get(
                "base_intelligence_schema",
                {}
            ).get(
                "fields",
                [],
            )
        )

        locked_final_fields = (
            schema.get(
                "final_intelligence_schema",
                {}
            ).get(
                "fields",
                [],
            )
        )

        if (
            base_fields
            != locked_base_fields
        ):

            raise Stage9FinalValidationError(
                "Base schema differs from contract."
            )

        if (
            final_fields
            != locked_final_fields
        ):

            raise Stage9FinalValidationError(
                "Final schema differs from contract."
            )

        if (
            len(
                base_rows
            )
            !=
            len(
                final_rows
            )
        ):

            raise Stage9FinalValidationError(
                "Base/final fixture counts differ."
            )

        base_index = {}
        final_index = {}

        base_order = []
        final_order = []

        for row in base_rows:

            fixture_id = row[
                "fixture_id"
            ]

            if fixture_id in base_index:

                raise Stage9FinalValidationError(
                    "Duplicate base fixture ID."
                )

            base_index[
                fixture_id
            ] = row

            base_order.append(
                fixture_id
            )

        for row in final_rows:

            fixture_id = row[
                "fixture_id"
            ]

            if fixture_id in final_index:

                raise Stage9FinalValidationError(
                    "Duplicate final fixture ID."
                )

            final_index[
                fixture_id
            ] = row

            final_order.append(
                fixture_id
            )

        if (
            set(
                base_index
            )
            !=
            set(
                final_index
            )
        ):

            raise Stage9FinalValidationError(
                "Base/final fixture sets differ."
            )

        if (
            base_order
            !=
            final_order
        ):

            raise Stage9FinalValidationError(
                "Fixture order changed."
            )

        # ====================================================
        # Row-level independent checks
        # ====================================================

        base_value_comparisons = 0

        semantic_checks = 0

        for fixture_id in base_order:

            base_row = base_index[
                fixture_id
            ]

            final_row = final_index[
                fixture_id
            ]

            # Exact Stage 9.2 preservation.
            for field in base_fields:

                if (
                    base_row.get(
                        field
                    )
                    !=
                    final_row.get(
                        field
                    )
                ):

                    raise Stage9FinalValidationError(
                        (
                            "Stage 9.2 value mutated: "
                            f"{fixture_id}, {field}"
                        )
                    )

                base_value_comparisons += 1

            probabilities = [

                decimal_value(
                    final_row,
                    "stage7_prob_home_win",
                ),

                decimal_value(
                    final_row,
                    "stage7_prob_draw",
                ),

                decimal_value(
                    final_row,
                    "stage7_prob_away_win",
                ),
            ]

            if any(
                probability < 0
                or
                probability > 1

                for probability in probabilities
            ):

                raise Stage9FinalValidationError(
                    f"Probability range failure: {fixture_id}"
                )

            probability_sum = sum(
                probabilities
            )

            if (
                abs(
                    probability_sum
                    -
                    Decimal(
                        "1"
                    )
                )
                >
                Decimal(
                    "0.000001"
                )
            ):

                raise Stage9FinalValidationError(
                    f"Probability sum failure: {fixture_id}"
                )

            sorted_probabilities = sorted(
                probabilities,
                reverse=True,
            )

            top = sorted_probabilities[
                0
            ]

            second = sorted_probabilities[
                1
            ]

            margin = top - second

            if (
                decimal_value(
                    final_row,
                    "stage9_top_probability",
                )
                != top
            ):

                raise Stage9FinalValidationError(
                    f"Top probability mismatch: {fixture_id}"
                )

            if (
                decimal_value(
                    final_row,
                    "stage9_second_probability",
                )
                != second
            ):

                raise Stage9FinalValidationError(
                    f"Second probability mismatch: {fixture_id}"
                )

            if (
                decimal_value(
                    final_row,
                    "stage9_probability_margin",
                )
                != margin
            ):

                raise Stage9FinalValidationError(
                    f"Probability margin mismatch: {fixture_id}"
                )

            confidence = float(
                decimal_value(
                    final_row,
                    "stage7_confidence",
                )
            )

            if (
                final_row.get(
                    "stage9_confidence_band"
                )
                !=
                confidence_band(
                    confidence
                )
            ):

                raise Stage9FinalValidationError(
                    f"Confidence band mismatch: {fixture_id}"
                )

            normalized_entropy = float(
                decimal_value(
                    final_row,
                    "stage9_normalized_entropy",
                )
            )

            if not (
                0.0
                <= normalized_entropy
                <= 1.0
            ):

                raise Stage9FinalValidationError(
                    (
                        "Normalized entropy range "
                        f"failure: {fixture_id}"
                    )
                )

            if (
                final_row.get(
                    "stage9_uncertainty_band"
                )
                !=
                uncertainty_band(
                    normalized_entropy
                )
            ):

                raise Stage9FinalValidationError(
                    f"Uncertainty band mismatch: {fixture_id}"
                )

            entropy = float(
                decimal_value(
                    final_row,
                    "stage9_entropy",
                )
            )

            expected_entropy = 0.0

            for probability in probabilities:

                p = float(
                    probability
                )

                if p > 0.0:

                    expected_entropy -= (
                        p
                        *
                        math.log(
                            p
                        )
                    )

            if not math.isclose(
                entropy,
                expected_entropy,
                abs_tol=1e-11,
                rel_tol=0.0,
            ):

                raise Stage9FinalValidationError(
                    f"Entropy mismatch: {fixture_id}"
                )

            support_score = integer_value(
                final_row,
                "stage9_context_support_score",
            )

            if not (
                -5
                <= support_score
                <= 5
            ):

                raise Stage9FinalValidationError(
                    f"Context score range failure: {fixture_id}"
                )

            if (
                final_row.get(
                    "stage9_context_alignment"
                )
                not in ALLOWED_ALIGNMENTS
            ):

                raise Stage9FinalValidationError(
                    f"Invalid alignment: {fixture_id}"
                )

            if (
                final_row.get(
                    "stage9_confidence_band"
                )
                not in ALLOWED_BANDS
            ):

                raise Stage9FinalValidationError(
                    f"Invalid confidence band: {fixture_id}"
                )

            if (
                final_row.get(
                    "stage9_uncertainty_band"
                )
                not in ALLOWED_BANDS
            ):

                raise Stage9FinalValidationError(
                    f"Invalid uncertainty band: {fixture_id}"
                )

            if not str(
                final_row.get(
                    "stage9_explanation_headline",
                    "",
                )
            ).strip():

                raise Stage9FinalValidationError(
                    f"Empty explanation headline: {fixture_id}"
                )

            if not str(
                final_row.get(
                    "stage9_explanation_summary",
                    "",
                )
            ).strip():

                raise Stage9FinalValidationError(
                    f"Empty explanation summary: {fixture_id}"
                )

            semantic_checks += 1

        return {

            "status":
                "PASS",

            "fixture_count":
                len(
                    final_rows
                ),

            "base_column_count":
                len(
                    base_fields
                ),

            "final_column_count":
                len(
                    final_fields
                ),

            "base_fixture_set_exact":
                True,

            "fixture_order_exact":
                True,

            "base_values_preserved_exactly":
                True,

            "probabilities_preserved":
                True,

            "derived_probability_metrics_exact":
                True,

            "entropy_exact":
                True,

            "confidence_bands_exact":
                True,

            "uncertainty_bands_exact":
                True,

            "context_score_range_valid":
                True,

            "context_alignment_valid":
                True,

            "explanations_complete":
                True,

            "dependency_chain_current":
                True,

            "base_value_comparisons":
                base_value_comparisons,

            "semantic_fixture_checks":
                semantic_checks,

            "final_intelligence_sha256":
                sha256_file(
                    INTELLIGENCE_FILE
                ),
        }
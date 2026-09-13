"""
FixtureIQ Stage 9.4
Independent Confidence & Uncertainty Validator.

This implementation does not use MatchUncertaintyBuilder.
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


PRECISION = 12


class MatchUncertaintyValidationError(
    RuntimeError
):
    pass


def load_json(
    path: Path,
) -> dict:

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

        raise MatchUncertaintyValidationError(
            f"Expected JSON object: {path}"
        )

    return payload


def load_csv(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        return (
            list(
                reader.fieldnames
                or []
            ),
            [
                dict(row)
                for row in reader
            ],
        )


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

    try:

        value = Decimal(
            raw
        )

    except InvalidOperation as exc:

        raise MatchUncertaintyValidationError(
            f"Invalid decimal {field}."
        ) from exc

    if not value.is_finite():

        raise MatchUncertaintyValidationError(
            f"Non-finite {field}."
        )

    return value


def confidence_band(
    value: float,
) -> str:

    if value < 0.40:
        return "VERY_LOW"

    if value < 0.50:
        return "LOW"

    if value < 0.60:
        return "MODERATE"

    if value < 0.70:
        return "HIGH"

    return "VERY_HIGH"


def uncertainty_band(
    value: float,
) -> str:

    if value < 0.20:
        return "VERY_LOW"

    if value < 0.40:
        return "LOW"

    if value < 0.60:
        return "MODERATE"

    if value < 0.80:
        return "HIGH"

    return "VERY_HIGH"


def entropy_values(
    probabilities: list[float],
) -> tuple[
    str,
    str,
]:

    if not math.isclose(
        sum(
            probabilities
        ),
        1.0,
        abs_tol=1e-6,
        rel_tol=0.0,
    ):

        raise MatchUncertaintyValidationError(
            "Probability sum invalid."
        )

    entropy = 0.0

    for probability in probabilities:

        if not (
            0.0
            <= probability
            <= 1.0
        ):

            raise MatchUncertaintyValidationError(
                "Probability range invalid."
            )

        if probability > 0.0:

            entropy -= (
                probability
                *
                math.log(
                    probability
                )
            )

    normalized = (
        entropy
        /
        math.log(
            3.0
        )
    )

    normalized = min(
        1.0,
        max(
            0.0,
            normalized,
        ),
    )

    return (
        f"{entropy:.{PRECISION}f}",
        f"{normalized:.{PRECISION}f}",
    )


class MatchUncertaintyValidator:

    def __init__(
        self,
        *,
        contract_file: Path = CONTRACT_FILE,
        contract_verification_file: Path = CONTRACT_VERIFICATION_FILE,
        base_file: Path = BASE_FILE,
        base_report_file: Path = BASE_REPORT_FILE,
        intelligence_file: Path = INTELLIGENCE_FILE,
        report_file: Path = REPORT_FILE,
    ) -> None:

        self.contract_file = Path(
            contract_file
        )

        self.contract_verification_file = Path(
            contract_verification_file
        )

        self.base_file = Path(
            base_file
        )

        self.base_report_file = Path(
            base_report_file
        )

        self.intelligence_file = Path(
            intelligence_file
        )

        self.report_file = Path(
            report_file
        )

    def validate(
        self,
    ) -> dict:

        contract = load_json(
            self.contract_file
        )

        verification = load_json(
            self.contract_verification_file
        )

        base_report = load_json(
            self.base_report_file
        )

        report = load_json(
            self.report_file
        )

        if (
            contract.get(
                "status"
            )
            !=
            "LOCKED_MATCH_INTELLIGENCE_CONTRACT"
        ):

            raise MatchUncertaintyValidationError(
                "Stage 9.1 contract not locked."
            )

        if (
            verification.get(
                "contract_sha256"
            )
            !=
            sha256_file(
                self.contract_file
            )
        ):

            raise MatchUncertaintyValidationError(
                "Stage 9.1 contract SHA mismatch."
            )

        if (
            base_report.get(
                "status"
            )
            != "PASS"
            or
            base_report.get(
                "stage_9_2_complete"
            )
            is not True
        ):

            raise MatchUncertaintyValidationError(
                "Stage 9.2 not complete."
            )

        if (
            report.get(
                "stage_9_3_complete"
            )
            is not True
        ):

            raise MatchUncertaintyValidationError(
                "Stage 9.3 evidence missing."
            )

        if (
            report.get(
                "stage_9_4_complete"
            )
            is not True
        ):

            raise MatchUncertaintyValidationError(
                "Stage 9.4 build evidence missing."
            )

        (
            base_fields,
            base_rows,
        ) = load_csv(
            self.base_file
        )

        (
            fields,
            rows,
        ) = load_csv(
            self.intelligence_file
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

        final_fields = (
            schema.get(
                "final_intelligence_schema",
                {}
            ).get(
                "fields",
                [],
            )
        )

        if fields != final_fields:

            raise MatchUncertaintyValidationError(
                "Final intelligence schema mismatch."
            )

        if len(
            rows
        ) != len(
            base_rows
        ):

            raise MatchUncertaintyValidationError(
                "Fixture count mismatch."
            )

        base_index = {
            row[
                "fixture_id"
            ]:
                row

            for row in base_rows
        }

        if len(
            base_index
        ) != len(
            base_rows
        ):

            raise MatchUncertaintyValidationError(
                "Duplicate Stage 9.2 fixture."
            )

        output_index = {
            row[
                "fixture_id"
            ]:
                row

            for row in rows
        }

        if len(
            output_index
        ) != len(
            rows
        ):

            raise MatchUncertaintyValidationError(
                "Duplicate intelligence fixture."
            )

        if (
            set(
                base_index
            )
            !=
            set(
                output_index
            )
        ):

            raise MatchUncertaintyValidationError(
                "Fixture sets differ."
            )

        stage9_4_comparisons = 0
        base_comparisons = 0

        confidence_counts = {
            "VERY_LOW": 0,
            "LOW": 0,
            "MODERATE": 0,
            "HIGH": 0,
            "VERY_HIGH": 0,
        }

        uncertainty_counts = {
            "VERY_LOW": 0,
            "LOW": 0,
            "MODERATE": 0,
            "HIGH": 0,
            "VERY_HIGH": 0,
        }

        for fixture_id, row in (
            output_index.items()
        ):

            base_row = base_index[
                fixture_id
            ]

            # -----------------------------------------------
            # Stage 9.2 values must still be exact
            # -----------------------------------------------

            for field in base_fields:

                if (
                    row.get(
                        field
                    )
                    !=
                    base_row.get(
                        field
                    )
                ):

                    raise MatchUncertaintyValidationError(
                        (
                            "Stage 9.2 value changed: "
                            f"{fixture_id}, {field}"
                        )
                    )

                base_comparisons += 1

            probabilities = [

                float(
                    decimal_value(
                        row,
                        "stage7_prob_home_win",
                    )
                ),

                float(
                    decimal_value(
                        row,
                        "stage7_prob_draw",
                    )
                ),

                float(
                    decimal_value(
                        row,
                        "stage7_prob_away_win",
                    )
                ),
            ]

            confidence = float(
                decimal_value(
                    row,
                    "stage7_confidence",
                )
            )

            if not math.isclose(
                confidence,
                max(
                    probabilities
                ),
                abs_tol=1e-12,
                rel_tol=0.0,
            ):

                raise MatchUncertaintyValidationError(
                    (
                        "Source confidence mismatch: "
                        f"{fixture_id}"
                    )
                )

            (
                expected_entropy,
                expected_normalized,
            ) = entropy_values(
                probabilities
            )

            expected_confidence_band = (
                confidence_band(
                    confidence
                )
            )

            normalized_float = float(
                expected_normalized
            )

            expected_uncertainty_band = (
                uncertainty_band(
                    normalized_float
                )
            )

            expected = {

                "stage9_entropy":
                    expected_entropy,

                "stage9_normalized_entropy":
                    expected_normalized,

                "stage9_confidence_band":
                    expected_confidence_band,

                "stage9_uncertainty_band":
                    expected_uncertainty_band,
            }

            for field, value in (
                expected.items()
            ):

                if (
                    row.get(
                        field
                    )
                    != value
                ):

                    raise MatchUncertaintyValidationError(
                        (
                            f"Stage 9.4 mismatch: "
                            f"{fixture_id}, {field}; "
                            f"expected {value!r}, "
                            f"got {row.get(field)!r}"
                        )
                    )

                stage9_4_comparisons += 1

            # -----------------------------------------------
            # Stage 9.3 context values remain populated
            # -----------------------------------------------

            for field in (

                "stage9_top_probability",
                "stage9_second_probability",
                "stage9_probability_margin",
                "stage9_league_position_gap",
                "stage9_points_gap",
                "stage9_goal_difference_gap",
                "stage9_recent_points_gap",
                "stage9_recent_goal_difference_gap",
                "stage9_venue_form_points_gap",
                "stage9_context_support_score",
                "stage9_context_alignment",
            ):

                if (
                    row.get(
                        field,
                        ""
                    )
                    == ""
                ):

                    raise MatchUncertaintyValidationError(
                        (
                            "Stage 9.3 value missing: "
                            f"{fixture_id}, {field}"
                        )
                    )

            # -----------------------------------------------
            # Stage 9.5 must remain empty
            # -----------------------------------------------

            for field in (

                "stage9_explanation_headline",
                "stage9_explanation_summary",
            ):

                if (
                    row.get(
                        field,
                        ""
                    )
                    != ""
                ):

                    raise MatchUncertaintyValidationError(
                        (
                            "Stage 9.5 populated early: "
                            f"{fixture_id}, {field}"
                        )
                    )

            confidence_counts[
                expected_confidence_band
            ] += 1

            uncertainty_counts[
                expected_uncertainty_band
            ] += 1

        # ====================================================
        # Report integrity
        # ====================================================

        if (
            report.get(
                "output_artifact",
                {}
            ).get(
                "sha256"
            )
            !=
            sha256_file(
                self.intelligence_file
            )
        ):

            raise MatchUncertaintyValidationError(
                "Output artifact SHA mismatch."
            )

        if (
            report.get(
                "stage_9_4_rule_version"
            )
            !=
            "STAGE9_4_CONFIDENCE_UNCERTAINTY_V1"
        ):

            raise MatchUncertaintyValidationError(
                "Stage 9.4 rule version mismatch."
            )

        statistics = report.get(
            "stage_9_4_statistics",
            {}
        )

        if (
            statistics.get(
                "confidence_band_counts"
            )
            != confidence_counts
        ):

            raise MatchUncertaintyValidationError(
                "Confidence-band counts mismatch."
            )

        if (
            statistics.get(
                "uncertainty_band_counts"
            )
            != uncertainty_counts
        ):

            raise MatchUncertaintyValidationError(
                "Uncertainty-band counts mismatch."
            )

        dependencies = report.get(
            "dependency_identity",
            {}
        )

        expected_dependencies = {

            "stage9_intelligence_contract":
                self.contract_file,

            "stage9_intelligence_contract_verification":
                self.contract_verification_file,

            "match_intelligence_base":
                self.base_file,

            "match_intelligence_base_report":
                self.base_report_file,
        }

        for name, path in (
            expected_dependencies.items()
        ):

            if (
                dependencies.get(
                    name,
                    {}
                ).get(
                    "sha256"
                )
                !=
                sha256_file(
                    path
                )
            ):

                raise MatchUncertaintyValidationError(
                    (
                        "Dependency stale: "
                        f"{name}"
                    )
                )

        return {

            "status":
                "PASS",

            "fixture_count":
                len(
                    rows
                ),

            "schema_exact":
                True,

            "fixture_sets_exact":
                True,

            "stage9_2_values_exact":
                True,

            "stage9_3_values_preserved":
                True,

            "entropy_exact":
                True,

            "normalized_entropy_exact":
                True,

            "confidence_bands_exact":
                True,

            "uncertainty_bands_exact":
                True,

            "stage9_5_fields_blank":
                True,

            "dependency_identity_current":
                True,

            "base_value_comparisons":
                base_comparisons,

            "stage9_4_value_comparisons":
                stage9_4_comparisons,

            "confidence_band_counts":
                confidence_counts,

            "uncertainty_band_counts":
                uncertainty_counts,

            "output_sha256":
                sha256_file(
                    self.intelligence_file
                ),
        }
"""
FixtureIQ Stage 9.4
Confidence & Uncertainty Layer Builder.

Stage 9.4 fills only:

- stage9_entropy
- stage9_normalized_entropy
- stage9_confidence_band
- stage9_uncertainty_band

It does not:
- modify Stage 7 probabilities
- modify Stage 7 prediction label
- modify Stage 7 confidence
- modify Stage 9.3 derived context intelligence
- populate Stage 9.5 explanations
- load or execute the prediction model
- tune thresholds against outcomes
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from decimal import Decimal, InvalidOperation
from pathlib import Path


# ============================================================
# Paths
# ============================================================

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

INTELLIGENCE_REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_report.json"
)


# ============================================================
# Locked Stage 9.4 semantic rules
# ============================================================

ENTROPY_PRECISION = 12

ALLOWED_BANDS = {

    "VERY_LOW",
    "LOW",
    "MODERATE",
    "HIGH",
    "VERY_HIGH",
}


STAGE9_4_FIELDS = [

    "stage9_entropy",
    "stage9_normalized_entropy",
    "stage9_confidence_band",
    "stage9_uncertainty_band",
]


STAGE9_5_FIELDS = [

    "stage9_explanation_headline",
    "stage9_explanation_summary",
]


class MatchUncertaintyBuildError(
    RuntimeError
):
    pass


# ============================================================
# Helpers
# ============================================================

def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise MatchUncertaintyBuildError(
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

        raise MatchUncertaintyBuildError(
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

        raise MatchUncertaintyBuildError(
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

        raise MatchUncertaintyBuildError(
            f"CSV has no columns: {path}"
        )

    if not rows:

        raise MatchUncertaintyBuildError(
            f"CSV has no rows: {path}"
        )

    return (
        fields,
        rows,
    )


def write_csv_atomic(
    path: Path,
    fields: list[str],
    rows: list[dict[str, str]],
) -> None:

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


def sha256_file(
    path: Path,
) -> str:

    if not path.exists():

        raise MatchUncertaintyBuildError(
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

    if raw == "":

        raise MatchUncertaintyBuildError(
            f"Empty numeric value: {field}"
        )

    try:

        value = Decimal(
            raw
        )

    except InvalidOperation as exc:

        raise MatchUncertaintyBuildError(
            (
                f"Invalid numeric value "
                f"{field}={raw!r}"
            )
        ) from exc

    if not value.is_finite():

        raise MatchUncertaintyBuildError(
            f"Non-finite numeric value: {field}"
        )

    return value


def fixed_float(
    value: float,
) -> str:

    return (
        f"{value:.{ENTROPY_PRECISION}f}"
    )


# ============================================================
# Stage 9.4 deterministic rules
# ============================================================

def confidence_band(
    confidence: float,
) -> str:

    if not (
        0.0
        <= confidence
        <= 1.0
    ):

        raise MatchUncertaintyBuildError(
            "Confidence outside [0,1]."
        )

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

    if (
        normalized_entropy < -1e-12
        or
        normalized_entropy > 1.0 + 1e-12
    ):

        raise MatchUncertaintyBuildError(
            (
                "Normalized entropy outside "
                "valid [0,1] range."
            )
        )

    normalized_entropy = min(
        1.0,
        max(
            0.0,
            normalized_entropy,
        ),
    )

    if normalized_entropy < 0.20:

        return "VERY_LOW"

    if normalized_entropy < 0.40:

        return "LOW"

    if normalized_entropy < 0.60:

        return "MODERATE"

    if normalized_entropy < 0.80:

        return "HIGH"

    return "VERY_HIGH"


def shannon_entropy(
    probabilities: list[float],
) -> tuple[
    float,
    float,
]:

    if len(
        probabilities
    ) != 3:

        raise MatchUncertaintyBuildError(
            "Expected exactly three probabilities."
        )

    for probability in probabilities:

        if not (
            0.0
            <= probability
            <= 1.0
        ):

            raise MatchUncertaintyBuildError(
                "Probability outside [0,1]."
            )

    if not math.isclose(
        sum(
            probabilities
        ),
        1.0,
        abs_tol=1e-6,
        rel_tol=0.0,
    ):

        raise MatchUncertaintyBuildError(
            "Stage 7 probabilities do not sum to one."
        )

    entropy = 0.0

    for probability in probabilities:

        if probability > 0.0:

            entropy -= (
                probability
                *
                math.log(
                    probability
                )
            )

    maximum_entropy = math.log(
        3.0
    )

    normalized = (
        entropy
        /
        maximum_entropy
    )

    if (
        normalized < -1e-12
        or
        normalized > 1.0 + 1e-12
    ):

        raise MatchUncertaintyBuildError(
            "Computed normalized entropy invalid."
        )

    normalized = min(
        1.0,
        max(
            0.0,
            normalized,
        ),
    )

    return (
        entropy,
        normalized,
    )


# ============================================================
# Builder
# ============================================================

class MatchUncertaintyBuilder:

    def __init__(
        self,
        *,
        contract_file: Path = CONTRACT_FILE,
        contract_verification_file: Path = CONTRACT_VERIFICATION_FILE,
        base_file: Path = BASE_FILE,
        base_report_file: Path = BASE_REPORT_FILE,
        intelligence_file: Path = INTELLIGENCE_FILE,
        intelligence_report_file: Path = INTELLIGENCE_REPORT_FILE,
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

        self.intelligence_report_file = Path(
            intelligence_report_file
        )

    def build(
        self,
    ) -> dict:

        # ====================================================
        # Stage 9.1
        # ====================================================

        contract = load_json(
            self.contract_file
        )

        verification = load_json(
            self.contract_verification_file
        )

        if (
            contract.get(
                "status"
            )
            !=
            "LOCKED_MATCH_INTELLIGENCE_CONTRACT"
        ):

            raise MatchUncertaintyBuildError(
                "Stage 9.1 contract is not locked."
            )

        if (
            contract.get(
                "stage_9_1_complete"
            )
            is not True
        ):

            raise MatchUncertaintyBuildError(
                "Stage 9.1 is incomplete."
            )

        if (
            verification.get(
                "status"
            )
            != "PASS"
        ):

            raise MatchUncertaintyBuildError(
                "Stage 9.1 verification is not PASS."
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

            raise MatchUncertaintyBuildError(
                "Stage 9.1 contract SHA mismatch."
            )

        # ====================================================
        # Stage 9.2
        # ====================================================

        base_report = load_json(
            self.base_report_file
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

            raise MatchUncertaintyBuildError(
                "Stage 9.2 is not complete."
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
                self.base_file
            )
        ):

            raise MatchUncertaintyBuildError(
                "Stage 9.2 base artifact is stale."
            )

        # ====================================================
        # Stage 9.3
        # ====================================================

        report = load_json(
            self.intelligence_report_file
        )

        if (
            report.get(
                "status"
            )
            != "PASS"
        ):

            raise MatchUncertaintyBuildError(
                "Stage 9.3 report is not PASS."
            )

        if (
            report.get(
                "stage_9_3_complete"
            )
            is not True
        ):

            raise MatchUncertaintyBuildError(
                "Stage 9.3 is incomplete."
            )

        if (
            report.get(
                "derived_match_intelligence"
            )
            != "VERIFIED"
        ):

            raise MatchUncertaintyBuildError(
                "Stage 9.3 is not VERIFIED."
            )

        if (
            report.get(
                "stage9_ready_for_9_4"
            )
            is not True
        ):

            raise MatchUncertaintyBuildError(
                "Stage 9.3 did not authorize Stage 9.4."
            )

        stage9_3_sha = sha256_file(
            self.intelligence_file
        )

        if (
            report.get(
                "output_artifact",
                {}
            ).get(
                "sha256"
            )
            != stage9_3_sha
        ):

            raise MatchUncertaintyBuildError(
                "Stage 9.3 intelligence artifact is stale."
            )

        # ====================================================
        # Locked final schema
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

        final_fields = (
            schema.get(
                "final_intelligence_schema",
                {}
            ).get(
                "fields",
                [],
            )
        )

        if not final_fields:

            raise MatchUncertaintyBuildError(
                "Locked final intelligence schema missing."
            )

        (
            fields,
            rows,
        ) = load_csv(
            self.intelligence_file
        )

        if (
            fields
            != final_fields
        ):

            raise MatchUncertaintyBuildError(
                "Stage 9 intelligence schema changed."
            )

        # ====================================================
        # Validate Stage 9.4 ownership state
        # ====================================================

        for field in STAGE9_4_FIELDS:

            if field not in fields:

                raise MatchUncertaintyBuildError(
                    (
                        "Missing Stage 9.4 field: "
                        f"{field}"
                    )
                )

        for field in STAGE9_5_FIELDS:

            if field not in fields:

                raise MatchUncertaintyBuildError(
                    (
                        "Missing Stage 9.5 field: "
                        f"{field}"
                    )
                )

        # Stage 9.4 starts only from the 9.3 artifact.
        for row in rows:

            fixture_id = row.get(
                "fixture_id",
                ""
            )

            for field in STAGE9_4_FIELDS:

                if (
                    row.get(
                        field,
                        ""
                    )
                    != ""
                ):

                    raise MatchUncertaintyBuildError(
                        (
                            f"Stage 9.4 field already populated "
                            f"for fixture {fixture_id}: {field}"
                        )
                    )

            for field in STAGE9_5_FIELDS:

                if (
                    row.get(
                        field,
                        ""
                    )
                    != ""
                ):

                    raise MatchUncertaintyBuildError(
                        (
                            f"Stage 9.5 field populated early "
                            f"for fixture {fixture_id}: {field}"
                        )
                    )

        # ====================================================
        # Build Stage 9.4 values
        # ====================================================

        output_rows = []

        seen_fixture_ids = set()

        confidence_counts = {
            band: 0
            for band in sorted(
                ALLOWED_BANDS
            )
        }

        uncertainty_counts = {
            band: 0
            for band in sorted(
                ALLOWED_BANDS
            )
        }

        entropy_values = []
        normalized_entropy_values = []

        for row in rows:

            fixture_id = str(
                row.get(
                    "fixture_id",
                    "",
                )
            ).strip()

            if not fixture_id:

                raise MatchUncertaintyBuildError(
                    "Empty fixture_id."
                )

            if fixture_id in seen_fixture_ids:

                raise MatchUncertaintyBuildError(
                    f"Duplicate fixture_id: {fixture_id}"
                )

            seen_fixture_ids.add(
                fixture_id
            )

            probabilities_decimal = [

                decimal_value(
                    row,
                    "stage7_prob_home_win",
                ),

                decimal_value(
                    row,
                    "stage7_prob_draw",
                ),

                decimal_value(
                    row,
                    "stage7_prob_away_win",
                ),
            ]

            probabilities = [
                float(
                    value
                )
                for value in probabilities_decimal
            ]

            top_probability = max(
                probabilities_decimal
            )

            stage9_top_probability = decimal_value(
                row,
                "stage9_top_probability",
            )

            stage7_confidence = decimal_value(
                row,
                "stage7_confidence",
            )

            if (
                stage9_top_probability
                != top_probability
            ):

                raise MatchUncertaintyBuildError(
                    (
                        "Stage 9.3 top probability mismatch "
                        f"for fixture {fixture_id}."
                    )
                )

            if (
                stage7_confidence
                != top_probability
            ):

                raise MatchUncertaintyBuildError(
                    (
                        "Stage 7 confidence does not equal "
                        f"maximum probability for {fixture_id}."
                    )
                )

            (
                entropy,
                normalized_entropy,
            ) = shannon_entropy(
                probabilities
            )

            confidence_class = confidence_band(
                float(
                    stage7_confidence
                )
            )

            uncertainty_class = uncertainty_band(
                normalized_entropy
            )

            if (
                confidence_class
                not in ALLOWED_BANDS
                or
                uncertainty_class
                not in ALLOWED_BANDS
            ):

                raise MatchUncertaintyBuildError(
                    "Invalid derived band."
                )

            output_row = dict(
                row
            )

            output_row[
                "stage9_entropy"
            ] = fixed_float(
                entropy
            )

            output_row[
                "stage9_normalized_entropy"
            ] = fixed_float(
                normalized_entropy
            )

            output_row[
                "stage9_confidence_band"
            ] = confidence_class

            output_row[
                "stage9_uncertainty_band"
            ] = uncertainty_class

            # Stage 9.5 still owns explanations.
            for field in STAGE9_5_FIELDS:

                if (
                    output_row.get(
                        field,
                        ""
                    )
                    != ""
                ):

                    raise MatchUncertaintyBuildError(
                        "Stage 9.5 field changed."
                    )

            output_rows.append(
                output_row
            )

            confidence_counts[
                confidence_class
            ] += 1

            uncertainty_counts[
                uncertainty_class
            ] += 1

            entropy_values.append(
                entropy
            )

            normalized_entropy_values.append(
                normalized_entropy
            )

        return {

            "status":
                "PASS",

            "fields":
                fields,

            "rows":
                output_rows,

            "fixture_count":
                len(
                    output_rows
                ),

            "stage9_3_input_sha256":
                stage9_3_sha,

            "entropy_precision":
                ENTROPY_PRECISION,

            "entropy_min":
                min(
                    entropy_values
                ),

            "entropy_max":
                max(
                    entropy_values
                ),

            "normalized_entropy_min":
                min(
                    normalized_entropy_values
                ),

            "normalized_entropy_max":
                max(
                    normalized_entropy_values
                ),

            "confidence_band_counts":
                confidence_counts,

            "uncertainty_band_counts":
                uncertainty_counts,

            "probabilities_modified":
                False,

            "prediction_labels_modified":
                False,

            "source_confidence_modified":
                False,

            "stage9_3_fields_modified":
                False,

            "stage9_5_fields_modified":
                False,

            "model_loaded":
                False,

            "model_executed":
                False,
        }

    def build_and_write(
        self,
    ) -> dict:

        result = self.build()

        write_csv_atomic(
            self.intelligence_file,
            result[
                "fields"
            ],
            result[
                "rows"
            ],
        )

        result[
            "output_sha256"
        ] = sha256_file(
            self.intelligence_file
        )

        return result
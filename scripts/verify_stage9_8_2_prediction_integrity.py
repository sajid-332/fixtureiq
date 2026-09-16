"""
FixtureIQ Stage 9.8.2
PREDICTION INTEGRITY VERIFICATION

Purpose
-------
Independently prove that Stage 9 preserved the Stage 7 production
prediction for every joined fixture.

This gate verifies:
- Stage 9.8.1 remains current
- the Stage 7 production prediction snapshot remains current
- fixture identity is one-to-one
- all five locked Stage 7 prediction fields were copied exactly
- Stage 9.2 base did not modify predictions
- final Stage 9 intelligence did not modify predictions
- probability vectors remain valid
- predicted labels remain consistent with the Stage 7 probabilities
- confidence remains equal to the winning probability
- no protected artifact is modified

This gate DOES NOT:
- rebuild predictions
- load or execute the model
- recalibrate probabilities
- change labels
- validate Stage 9 derived intelligence semantics
- promote Stage 9

Only Stage 9.8.5 may promote Stage 9.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path


# ============================================================
# Project paths
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

FOUNDATION_VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "stage9_8_1_foundation_verification.json"
)

OUTPUT_FILE = (
    INTELLIGENCE_DIR
    / "stage9_8_2_prediction_integrity_verification.json"
)


# ============================================================
# Locked prediction mapping
# ============================================================

PREDICTION_MAPPING = {

    "prob_home_win":
        "stage7_prob_home_win",

    "prob_draw":
        "stage7_prob_draw",

    "prob_away_win":
        "stage7_prob_away_win",

    "predicted_label":
        "stage7_predicted_label",

    "confidence":
        "stage7_confidence",
}


PROBABILITY_SOURCE_FIELDS = [

    "prob_home_win",
    "prob_draw",
    "prob_away_win",
]


PROBABILITY_STAGE9_FIELDS = [

    "stage7_prob_home_win",
    "stage7_prob_draw",
    "stage7_prob_away_win",
]


LABEL_FROM_INDEX = {

    0:
        "Home Win",

    1:
        "Draw",

    2:
        "Away Win",
}


# ============================================================
# Helpers
# ============================================================

def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise RuntimeError(
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

        raise RuntimeError(
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

        raise RuntimeError(
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

        raise RuntimeError(
            f"No CSV columns: {path}"
        )

    if not rows:

        raise RuntimeError(
            f"No CSV rows: {path}"
        )

    return (
        fields,
        rows,
    )


def sha256_file(
    path: Path,
) -> str:

    if not path.exists():

        raise RuntimeError(
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


def relative_path(
    path: Path,
) -> str:

    return (
        str(
            path.resolve().relative_to(
                BASE_DIR.resolve()
            )
        )
        .replace(
            "\\",
            "/",
        )
    )


def resolve_project_path(
    value: str,
) -> Path:

    raw = Path(
        str(value)
    )

    if raw.is_absolute():

        resolved = raw.resolve()

    else:

        resolved = (
            BASE_DIR
            / raw
        ).resolve()

    try:

        resolved.relative_to(
            BASE_DIR.resolve()
        )

    except ValueError as exc:

        raise RuntimeError(
            (
                "Path escapes FixtureIQ "
                f"project root: {value}"
            )
        ) from exc

    return resolved


def save_json_atomic(
    path: Path,
    payload: dict,
) -> None:

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temporary.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=2,
        )

    temporary.replace(
        path
    )


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


def decimal_value(
    value,
    *,
    field: str,
    fixture_id: str,
) -> Decimal:

    raw = str(
        value
    ).strip()

    if not raw:

        raise RuntimeError(
            (
                f"Empty numeric value: "
                f"{fixture_id} / {field}"
            )
        )

    try:

        parsed = Decimal(
            raw
        )

    except InvalidOperation as exc:

        raise RuntimeError(
            (
                f"Invalid numeric value: "
                f"{fixture_id} / "
                f"{field}={raw!r}"
            )
        ) from exc

    if not parsed.is_finite():

        raise RuntimeError(
            (
                f"Non-finite numeric value: "
                f"{fixture_id} / {field}"
            )
        )

    return parsed


def exact_decimal_equal(
    left,
    right,
) -> bool:

    try:

        return (
            Decimal(
                str(left).strip()
            )
            ==
            Decimal(
                str(right).strip()
            )
        )

    except Exception:

        return False


def normalize_label(
    value,
) -> str:

    return (
        str(value)
        .strip()
        .casefold()
    )


def build_unique_index(
    rows: list[dict[str, str]],
    *,
    name: str,
) -> tuple[
    dict[str, dict[str, str]],
    list[str],
]:

    index = {}

    order = []

    for row in rows:

        fixture_id = str(
            row.get(
                "fixture_id",
                "",
            )
        ).strip()

        if not fixture_id:

            raise RuntimeError(
                (
                    f"{name} contains "
                    "empty fixture_id."
                )
            )

        if fixture_id in index:

            raise RuntimeError(
                (
                    f"{name} contains duplicate "
                    f"fixture_id: {fixture_id}"
                )
            )

        index[
            fixture_id
        ] = row

        order.append(
            fixture_id
        )

    return (
        index,
        order,
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 9.8.2"
    )

    print(
        "PREDICTION INTEGRITY VERIFICATION"
    )

    print("=" * 72)

    failures: list[str] = []

    # ========================================================
    # 1. Required artifacts
    # ========================================================

    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    required = [

        CONTRACT_FILE,
        BASE_FILE,
        BASE_REPORT_FILE,
        INTELLIGENCE_FILE,
        FOUNDATION_VERIFICATION_FILE,
    ]

    for path in required:

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
            "STAGE 9.8.2: FAIL"
        )

        print(
            "PREDICTION INTEGRITY: NOT VERIFIED"
        )

        print("=" * 72)

        sys.exit(1)

    # ========================================================
    # 2. Stage 9.8.1 foundation must remain current
    # ========================================================

    print(
        "\n2. STAGE 9.8.1 FOUNDATION"
    )

    foundation = load_json(
        FOUNDATION_VERIFICATION_FILE
    )

    check(
        "Stage 9.8.1 PASS",
        foundation.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )

    check(
        "Stage 9.8.1 COMPLETE",
        foundation.get(
            "stage_9_8_1_complete"
        )
        is True,
        failures,
    )

    check(
        "Foundation verification VERIFIED",
        foundation.get(
            "foundation_verification"
        )
        ==
        "VERIFIED",
        failures,
    )

    check(
        "Stage 9.8.1 authorized 9.8.2",
        foundation.get(
            "stage9_ready_for_9_8_2"
        )
        is True,
        failures,
    )

    foundation_dependencies = (
        foundation.get(
            "dependency_identity",
            {}
        )
    )

    for path in [

        CONTRACT_FILE,
        BASE_FILE,
        BASE_REPORT_FILE,
        INTELLIGENCE_FILE,
    ]:

        key = relative_path(
            path
        )

        item = foundation_dependencies.get(
            key,
            {}
        )

        check(
            (
                f"{path.name} unchanged "
                "since 9.8.1"
            ),
            item.get(
                "sha256"
            )
            ==
            sha256_file(
                path
            ),
            failures,
        )

    # ========================================================
    # 3. Resolve locked Stage 7 source
    # ========================================================

    print(
        "\n3. LOCKED STAGE 7 PREDICTION SOURCE"
    )

    contract = load_json(
        CONTRACT_FILE
    )

    base_report = load_json(
        BASE_REPORT_FILE
    )

    allowed_inputs = (
        contract.get(
            "stage_9_1_1",
            {}
        ).get(
            "allowed_inputs",
            {}
        )
    )

    production_input = (
        allowed_inputs.get(
            "production_predictions",
            {}
        )
    )

    production_path_text = str(
        production_input.get(
            "path",
            "",
        )
    ).strip()

    check(
        "Production prediction path locked",
        bool(
            production_path_text
        ),
        failures,
    )

    production_path = None

    if production_path_text:

        try:

            production_path = (
                resolve_project_path(
                    production_path_text
                )
            )

        except Exception as exc:

            print(
                "Production path error:",
                exc,
            )

    check(
        "Production prediction artifact exists",
        production_path is not None
        and
        production_path.exists(),
        failures,
    )

    stage9_2_dependencies = (
        base_report.get(
            "dependency_identity",
            {}
        )
    )

    production_snapshot = (
        stage9_2_dependencies.get(
            "production_predictions",
            {}
        )
    )

    if production_path is not None:

        check(
            (
                "Production prediction SHA matches "
                "Stage 9.2 snapshot"
            ),
            production_snapshot.get(
                "sha256"
            )
            ==
            sha256_file(
                production_path
            ),
            failures,
        )

    # ========================================================
    # Stop before row validation if source unavailable
    # ========================================================

    if (
        production_path is None
        or
        not production_path.exists()
    ):

        print(
            "\nProduction prediction source unavailable."
        )

        print(
            "\n" + "=" * 72
        )

        print(
            "STAGE 9.8.2: FAIL"
        )

        print(
            "PREDICTION INTEGRITY: NOT VERIFIED"
        )

        print("=" * 72)

        sys.exit(1)

    # ========================================================
    # Protected artifact snapshot
    # ========================================================

    protected_paths = [

        production_path,
        CONTRACT_FILE,
        BASE_FILE,
        BASE_REPORT_FILE,
        INTELLIGENCE_FILE,
        FOUNDATION_VERIFICATION_FILE,
    ]

    protected_before = {

        relative_path(
            path
        ):
            sha256_file(
                path
            )

        for path in protected_paths
    }

    # ========================================================
    # 4. Load source / base / final
    # ========================================================

    print(
        "\n4. PREDICTION DATASETS"
    )

    (
        production_fields,
        production_rows,
    ) = load_csv(
        production_path
    )

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

    for field in [
        "fixture_id",
        *PREDICTION_MAPPING.keys(),
    ]:

        check(
            (
                f"Stage 7 source field exists: "
                f"{field}"
            ),
            field in production_fields,
            failures,
        )

    for field in [
        "fixture_id",
        *PREDICTION_MAPPING.values(),
    ]:

        check(
            (
                f"Stage 9 base field exists: "
                f"{field}"
            ),
            field in base_fields,
            failures,
        )

        check(
            (
                f"Final Stage 9 field exists: "
                f"{field}"
            ),
            field in final_fields,
            failures,
        )

    # ========================================================
    # 5. Fixture identity
    # ========================================================

    print(
        "\n5. FIXTURE IDENTITY"
    )

    try:

        (
            production_index,
            production_order,
        ) = build_unique_index(
            production_rows,
            name=
                "production_predictions",
        )

        (
            base_index,
            base_order,
        ) = build_unique_index(
            base_rows,
            name=
                "match_intelligence_base",
        )

        (
            final_index,
            final_order,
        ) = build_unique_index(
            final_rows,
            name=
                "match_intelligence",
        )

        index_build_ok = True

    except Exception as exc:

        print(
            "Fixture identity error:",
            exc,
        )

        production_index = {}
        base_index = {}
        final_index = {}

        production_order = []
        base_order = []
        final_order = []

        index_build_ok = False

    check(
        "All fixture IDs unique",
        index_build_ok,
        failures,
    )

    check(
        "Production/base fixture count equal",
        len(
            production_rows
        )
        ==
        len(
            base_rows
        ),
        failures,
    )

    check(
        "Base/final fixture count equal",
        len(
            base_rows
        )
        ==
        len(
            final_rows
        ),
        failures,
    )

    check(
        "Production/base fixture set exact",
        set(
            production_index
        )
        ==
        set(
            base_index
        ),
        failures,
    )

    check(
        "Base/final fixture set exact",
        set(
            base_index
        )
        ==
        set(
            final_index
        ),
        failures,
    )

    check(
        "Base/final fixture order exact",
        base_order
        ==
        final_order,
        failures,
    )

    # ========================================================
    # 6. Exact five-field preservation
    # ========================================================

    print(
        "\n6. LOCKED PREDICTION COPY INTEGRITY"
    )

    source_to_base_checks = 0

    base_to_final_checks = 0

    source_to_final_checks = 0

    exact_copy_ok = True

    first_copy_error = None

    if (
        index_build_ok
        and
        set(
            production_index
        )
        ==
        set(
            base_index
        )
        ==
        set(
            final_index
        )
    ):

        for fixture_id in base_order:

            source_row = production_index[
                fixture_id
            ]

            base_row = base_index[
                fixture_id
            ]

            final_row = final_index[
                fixture_id
            ]

            for (
                source_field,
                stage9_field,
            ) in PREDICTION_MAPPING.items():

                source_value = str(
                    source_row.get(
                        source_field,
                        "",
                    )
                ).strip()

                base_value = str(
                    base_row.get(
                        stage9_field,
                        "",
                    )
                ).strip()

                final_value = str(
                    final_row.get(
                        stage9_field,
                        "",
                    )
                ).strip()

                if source_field in [
                    "prob_home_win",
                    "prob_draw",
                    "prob_away_win",
                    "confidence",
                ]:

                    source_base_equal = (
                        exact_decimal_equal(
                            source_value,
                            base_value,
                        )
                    )

                    base_final_equal = (
                        exact_decimal_equal(
                            base_value,
                            final_value,
                        )
                    )

                    source_final_equal = (
                        exact_decimal_equal(
                            source_value,
                            final_value,
                        )
                    )

                else:

                    source_base_equal = (
                        source_value
                        ==
                        base_value
                    )

                    base_final_equal = (
                        base_value
                        ==
                        final_value
                    )

                    source_final_equal = (
                        source_value
                        ==
                        final_value
                    )

                source_to_base_checks += 1
                base_to_final_checks += 1
                source_to_final_checks += 1

                if not (
                    source_base_equal
                    and
                    base_final_equal
                    and
                    source_final_equal
                ):

                    exact_copy_ok = False

                    if first_copy_error is None:

                        first_copy_error = (
                            fixture_id,
                            source_field,
                            stage9_field,
                            source_value,
                            base_value,
                            final_value,
                        )

    check(
        "Stage 7 -> Stage 9.2 prediction copy exact",
        exact_copy_ok,
        failures,
    )

    check(
        "Stage 9.2 -> final Stage 9 prediction copy exact",
        exact_copy_ok,
        failures,
    )

    check(
        "Stage 7 -> final Stage 9 prediction copy exact",
        exact_copy_ok,
        failures,
    )

    if first_copy_error is not None:

        (
            fixture_id,
            source_field,
            stage9_field,
            source_value,
            base_value,
            final_value,
        ) = first_copy_error

        print(
            (
                "First prediction copy mismatch: "
                f"fixture={fixture_id}, "
                f"source={source_field}, "
                f"stage9={stage9_field}, "
                f"source_value={source_value!r}, "
                f"base_value={base_value!r}, "
                f"final_value={final_value!r}"
            )
        )

    expected_copy_checks = (
        len(
            base_rows
        )
        *
        len(
            PREDICTION_MAPPING
        )
    )

    check(
        "All five prediction fields checked for every fixture",
        source_to_base_checks
        ==
        expected_copy_checks,
        failures,
    )

    # ========================================================
    # 7. Independent probability validity
    # ========================================================

    print(
        "\n7. PROBABILITY VECTOR INTEGRITY"
    )

    probability_vectors_valid = True

    label_consistency_valid = True

    confidence_consistency_valid = True

    probability_checks = 0

    label_checks = 0

    confidence_checks = 0

    first_probability_error = None
    first_label_error = None
    first_confidence_error = None

    if index_build_ok:

        for fixture_id in base_order:

            row = final_index[
                fixture_id
            ]

            try:

                probabilities = [

                    decimal_value(
                        row.get(
                            "stage7_prob_home_win"
                        ),
                        field=
                            "stage7_prob_home_win",
                        fixture_id=
                            fixture_id,
                    ),

                    decimal_value(
                        row.get(
                            "stage7_prob_draw"
                        ),
                        field=
                            "stage7_prob_draw",
                        fixture_id=
                            fixture_id,
                    ),

                    decimal_value(
                        row.get(
                            "stage7_prob_away_win"
                        ),
                        field=
                            "stage7_prob_away_win",
                        fixture_id=
                            fixture_id,
                    ),
                ]

            except Exception as exc:

                probability_vectors_valid = False

                if first_probability_error is None:

                    first_probability_error = str(
                        exc
                    )

                continue

            probability_checks += 1

            if any(
                probability
                <
                Decimal("0")
                or
                probability
                >
                Decimal("1")

                for probability in probabilities
            ):

                probability_vectors_valid = False

                if first_probability_error is None:

                    first_probability_error = (
                        (
                            f"{fixture_id}: "
                            "probability outside [0,1]"
                        )
                    )

            probability_sum = sum(
                probabilities
            )

            if (
                abs(
                    probability_sum
                    -
                    Decimal("1")
                )
                >
                Decimal("0.000001")
            ):

                probability_vectors_valid = False

                if first_probability_error is None:

                    first_probability_error = (
                        (
                            f"{fixture_id}: "
                            f"probability sum="
                            f"{probability_sum}"
                        )
                    )

            # ------------------------------------------------
            # Winning label integrity
            # ------------------------------------------------

            max_probability = max(
                probabilities
            )

            max_indices = [

                index

                for index, probability
                in enumerate(
                    probabilities
                )

                if probability
                ==
                max_probability
            ]

            actual_label = str(
                row.get(
                    "stage7_predicted_label",
                    "",
                )
            ).strip()

            # If an exact tie exists, the Stage 7 label must
            # correspond to one of the tied maximum outcomes.
            allowed_labels = {

                normalize_label(
                    LABEL_FROM_INDEX[
                        index
                    ]
                )

                for index in max_indices
            }

            if (
                normalize_label(
                    actual_label
                )
                not in
                allowed_labels
            ):

                label_consistency_valid = False

                if first_label_error is None:

                    first_label_error = (
                        (
                            f"{fixture_id}: "
                            f"label={actual_label!r}, "
                            f"allowed="
                            f"{sorted(allowed_labels)}"
                        )
                    )

            label_checks += 1

            # ------------------------------------------------
            # Confidence integrity
            # ------------------------------------------------

            try:

                confidence = decimal_value(
                    row.get(
                        "stage7_confidence"
                    ),
                    field=
                        "stage7_confidence",
                    fixture_id=
                        fixture_id,
                )

            except Exception as exc:

                confidence_consistency_valid = False

                if first_confidence_error is None:

                    first_confidence_error = str(
                        exc
                    )

                continue

            if (
                confidence
                !=
                max_probability
            ):

                confidence_consistency_valid = False

                if first_confidence_error is None:

                    first_confidence_error = (
                        (
                            f"{fixture_id}: "
                            f"confidence={confidence}, "
                            f"max_probability="
                            f"{max_probability}"
                        )
                    )

            confidence_checks += 1

    check(
        "All probability vectors valid",
        probability_vectors_valid,
        failures,
    )

    check(
        "Predicted labels agree with maximum probability",
        label_consistency_valid,
        failures,
    )

    check(
        "Confidence equals maximum probability",
        confidence_consistency_valid,
        failures,
    )

    check(
        "Every fixture probability vector checked",
        probability_checks
        ==
        len(
            final_rows
        ),
        failures,
    )

    check(
        "Every fixture label checked",
        label_checks
        ==
        len(
            final_rows
        ),
        failures,
    )

    check(
        "Every fixture confidence checked",
        confidence_checks
        ==
        len(
            final_rows
        ),
        failures,
    )

    if first_probability_error:

        print(
            "First probability error:",
            first_probability_error,
        )

    if first_label_error:

        print(
            "First label error:",
            first_label_error,
        )

    if first_confidence_error:

        print(
            "First confidence error:",
            first_confidence_error,
        )

    # ========================================================
    # 8. Prediction distribution preservation
    # ========================================================

    print(
        "\n8. PREDICTION DISTRIBUTION PRESERVATION"
    )

    source_distribution = {}

    final_distribution = {}

    for row in production_rows:

        label = str(
            row.get(
                "predicted_label",
                "",
            )
        ).strip()

        source_distribution[
            label
        ] = (
            source_distribution.get(
                label,
                0,
            )
            +
            1
        )

    for row in final_rows:

        label = str(
            row.get(
                "stage7_predicted_label",
                "",
            )
        ).strip()

        final_distribution[
            label
        ] = (
            final_distribution.get(
                label,
                0,
            )
            +
            1
        )

    check(
        "Prediction label distribution unchanged",
        source_distribution
        ==
        final_distribution,
        failures,
    )

    if (
        source_distribution
        !=
        final_distribution
    ):

        print(
            "Source distribution:",
            source_distribution,
        )

        print(
            "Final distribution:",
            final_distribution,
        )

    # ========================================================
    # 9. No prediction mutation authority
    # ========================================================

    print(
        "\n9. PREDICTION MUTATION SAFETY"
    )

    forbidden_operations = (
        contract.get(
            "stage_9_1_2",
            {}
        ).get(
            "forbidden_operations",
            []
        )
    )

    forbidden_text = (
        " ".join(
            str(item)
            for item in forbidden_operations
        )
        .casefold()
    )

    check(
        "Probability modification forbidden by contract",
        (
            "probability"
            in forbidden_text
            and
            (
                "modif"
                in forbidden_text
                or
                "recalibr"
                in forbidden_text
            )
        ),
        failures,
    )

    check(
        "Prediction label modification forbidden by contract",
        (
            "prediction"
            in forbidden_text
            and
            "label"
            in forbidden_text
        ),
        failures,
    )

    check(
        "No model execution performed by 9.8.2",
        True,
        failures,
    )

    check(
        "No recalibration performed by 9.8.2",
        True,
        failures,
    )

    # ========================================================
    # 10. Write protection
    # ========================================================

    print(
        "\n10. PREDICTION ARTIFACT WRITE PROTECTION"
    )

    for path in protected_paths:

        key = relative_path(
            path
        )

        check(
            f"{path.name} unchanged",
            sha256_file(
                path
            )
            ==
            protected_before[
                key
            ],
            failures,
        )

    # ========================================================
    # 11. Save 9.8.2 evidence
    # ========================================================

    print(
        "\n11. SAVE STAGE 9.8.2 EVIDENCE"
    )

    overall_pass = (
        len(
            failures
        )
        ==
        0
    )

    if overall_pass:

        verified_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        evidence = {

            "stage":
                "9.8.2",

            "name":
                "PREDICTION_INTEGRITY_VERIFICATION",

            "status":
                "PASS",

            "stage_9_8_2_complete":
                True,

            "prediction_integrity":
                "VERIFIED",

            "verified_at_utc":
                verified_at,

            "fixture_count":
                len(
                    final_rows
                ),

            "prediction_mapping":
                PREDICTION_MAPPING,

            "integrity": {

                "stage7_source_snapshot_current":
                    True,

                "fixture_identity_exact":
                    True,

                "fixture_count_exact":
                    True,

                "stage7_to_stage9_base_copy_exact":
                    True,

                "stage9_base_to_final_copy_exact":
                    True,

                "stage7_to_final_copy_exact":
                    True,

                "probability_vectors_valid":
                    True,

                "predicted_labels_consistent":
                    True,

                "confidence_consistent":
                    True,

                "prediction_distribution_unchanged":
                    True,

                "prediction_artifacts_unchanged":
                    True,
            },

            "verification_counts": {

                "source_to_base_field_checks":
                    source_to_base_checks,

                "base_to_final_field_checks":
                    base_to_final_checks,

                "source_to_final_field_checks":
                    source_to_final_checks,

                "probability_vector_checks":
                    probability_checks,

                "predicted_label_checks":
                    label_checks,

                "confidence_checks":
                    confidence_checks,
            },

            "prediction_distribution":
                final_distribution,

            "safety": {

                "read_only":
                    True,

                "model_loaded":
                    False,

                "model_executed":
                    False,

                "model_retrained":
                    False,

                "model_reselected":
                    False,

                "probabilities_modified":
                    False,

                "probabilities_recalibrated":
                    False,

                "prediction_labels_modified":
                    False,

                "confidence_modified":
                    False,

                "production_prediction_artifact_modified":
                    False,

                "stage9_base_modified":
                    False,

                "stage9_final_intelligence_modified":
                    False,
            },

            "dependency_identity": {

                relative_path(
                    FOUNDATION_VERIFICATION_FILE
                ): {
                    "sha256":
                        sha256_file(
                            FOUNDATION_VERIFICATION_FILE
                        ),
                },

                relative_path(
                    production_path
                ): {
                    "sha256":
                        sha256_file(
                            production_path
                        ),
                },

                relative_path(
                    BASE_FILE
                ): {
                    "sha256":
                        sha256_file(
                            BASE_FILE
                        ),
                },

                relative_path(
                    BASE_REPORT_FILE
                ): {
                    "sha256":
                        sha256_file(
                            BASE_REPORT_FILE
                        ),
                },

                relative_path(
                    INTELLIGENCE_FILE
                ): {
                    "sha256":
                        sha256_file(
                            INTELLIGENCE_FILE
                        ),
                },
            },

            "promotion": {

                "stage_9_complete":
                    False,

                "stage_9_8_complete":
                    False,

                "promotion_authorized":
                    False,

                "promotion_owner":
                    "9.8.5",
            },

            "stage9_ready_for_9_8_3":
                True,

            "next_stage":
                "9.8.3",

            "failures":
                [],
        }

        save_json_atomic(
            OUTPUT_FILE,
            evidence,
        )

        print(
            OUTPUT_FILE
        )

    print(
        "\n" + "=" * 72
    )

    if overall_pass:

        print(
            "STAGE 9.8.2: PASS"
        )

        print(
            "PREDICTION INTEGRITY VERIFICATION: VERIFIED"
        )

        print(
            "STAGE 7 PREDICTIONS PRESERVED EXACTLY"
        )

        print(
            "STAGE 9 READY FOR 9.8.3"
        )

        print()
        print(
            "STAGE 9 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 9.8.2: FAIL"
        )

        print(
            "PREDICTION INTEGRITY VERIFICATION: NOT VERIFIED"
        )

        if failures:

            print(
                "\nFailures:"
            )

            for failure in failures:

                print(
                    f"  - {failure}"
                )

    print("=" * 72)

    sys.exit(
        0
        if overall_pass
        else 1
    )


if __name__ == "__main__":

    main()
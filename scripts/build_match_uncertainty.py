"""
FixtureIQ Stage 9.4
Build Confidence & Uncertainty Layer.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


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


from backend.services.match_uncertainty_builder import (
    MatchUncertaintyBuilder,
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


def load_json(
    path: Path,
) -> dict:

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(
            file
        )


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


def relative_path(
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


def main() -> None:

    print("=" * 72)
    print("FixtureIQ Stage 9.4")
    print("CONFIDENCE & UNCERTAINTY LAYER")
    print("=" * 72)

    failures = []

    report = load_json(
        REPORT_FILE
    )

    print(
        "\n1. STAGE 9.3 FOUNDATION"
    )

    check(
        "Stage 9.3 PASS",
        report.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 9.3 COMPLETE",
        report.get(
            "stage_9_3_complete"
        )
        is True,
        failures,
    )

    check(
        "Derived Match Intelligence VERIFIED",
        report.get(
            "derived_match_intelligence"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Stage 9 ready for 9.4",
        report.get(
            "stage9_ready_for_9_4"
        )
        is True,
        failures,
    )

    if failures:

        sys.exit(1)

    # ========================================================
    # Protect immutable dependencies
    # ========================================================

    protected = {

        "contract":
            sha256_file(
                CONTRACT_FILE
            ),

        "contract_verification":
            sha256_file(
                CONTRACT_VERIFICATION_FILE
            ),

        "base":
            sha256_file(
                BASE_FILE
            ),

        "base_report":
            sha256_file(
                BASE_REPORT_FILE
            ),
    }

    stage9_3_sha = sha256_file(
        INTELLIGENCE_FILE
    )

    # ========================================================
    # Build
    # ========================================================

    print(
        "\n2. BUILD CONFIDENCE / UNCERTAINTY"
    )

    try:

        result = (
            MatchUncertaintyBuilder()
            .build_and_write()
        )

        build_ok = (
            result.get(
                "status"
            )
            == "PASS"
        )

    except Exception as exc:

        print(
            "Build error:",
            exc,
        )

        result = {}
        build_ok = False

    check(
        "Stage 9.4 build PASS",
        build_ok,
        failures,
    )

    if build_ok:

        check(
            "Fixture count > 0",
            result.get(
                "fixture_count",
                0,
            )
            > 0,
            failures,
        )

        check(
            "Stage 9.3 input SHA captured",
            result.get(
                "stage9_3_input_sha256"
            )
            == stage9_3_sha,
            failures,
        )

        check(
            "Probabilities unchanged",
            result.get(
                "probabilities_modified"
            )
            is False,
            failures,
        )

        check(
            "Prediction labels unchanged",
            result.get(
                "prediction_labels_modified"
            )
            is False,
            failures,
        )

        check(
            "Source confidence unchanged",
            result.get(
                "source_confidence_modified"
            )
            is False,
            failures,
        )

        check(
            "Stage 9.3 fields unchanged",
            result.get(
                "stage9_3_fields_modified"
            )
            is False,
            failures,
        )

        check(
            "Stage 9.5 fields untouched",
            result.get(
                "stage9_5_fields_modified"
            )
            is False,
            failures,
        )

    # ========================================================
    # Upstream protection
    # ========================================================

    print(
        "\n3. UPSTREAM PROTECTION"
    )

    check(
        "Stage 9.1 contract unchanged",
        sha256_file(
            CONTRACT_FILE
        )
        ==
        protected[
            "contract"
        ],
        failures,
    )

    check(
        "Stage 9.1 verification unchanged",
        sha256_file(
            CONTRACT_VERIFICATION_FILE
        )
        ==
        protected[
            "contract_verification"
        ],
        failures,
    )

    check(
        "Stage 9.2 base unchanged",
        sha256_file(
            BASE_FILE
        )
        ==
        protected[
            "base"
        ],
        failures,
    )

    check(
        "Stage 9.2 report unchanged",
        sha256_file(
            BASE_REPORT_FILE
        )
        ==
        protected[
            "base_report"
        ],
        failures,
    )

    overall_pass = (
        len(
            failures
        )
        == 0
    )

    # ========================================================
    # Promote report
    # ========================================================

    print(
        "\n4. SAVE STAGE 9.4 EVIDENCE"
    )

    if overall_pass:

        generated_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        updated = load_json(
            REPORT_FILE
        )

        updated[
            "stage"
        ] = "9.4"

        updated[
            "status"
        ] = "PASS"

        updated[
            "stage_9_4_complete"
        ] = True

        updated[
            "stage_9_4_status"
        ] = "COMPLETE"

        updated[
            "confidence_uncertainty_layer"
        ] = "BUILT"

        updated[
            "stage_9_4_generated_at_utc"
        ] = generated_at

        updated[
            "stage_9_4_rule_version"
        ] = (
            "STAGE9_4_CONFIDENCE_UNCERTAINTY_V1"
        )

        updated[
            "entropy_rule"
        ] = {

            "type":
                "SHANNON_ENTROPY",

            "log_base":
                "NATURAL_LOG",

            "formula":
                "-SUM(p_i * ln(p_i))",

            "class_count":
                3,

            "maximum_entropy":
                "ln(3)",

            "normalized_formula":
                "entropy / ln(3)",

            "normalized_minimum":
                0.0,

            "normalized_maximum":
                1.0,

            "decimal_places":
                result[
                    "entropy_precision"
                ],

            "outcome_tuning_used":
                False,
        }

        updated[
            "confidence_band_rule"
        ] = {

            "source":
                "stage7_confidence",

            "meaning":
                (
                    "Descriptive bucket only; "
                    "does not replace source confidence."
                ),

            "VERY_LOW":
                "[0.00, 0.40)",

            "LOW":
                "[0.40, 0.50)",

            "MODERATE":
                "[0.50, 0.60)",

            "HIGH":
                "[0.60, 0.70)",

            "VERY_HIGH":
                "[0.70, 1.00]",

            "outcome_tuning_used":
                False,
        }

        updated[
            "uncertainty_band_rule"
        ] = {

            "source":
                "stage9_normalized_entropy",

            "direction":
                (
                    "higher normalized entropy "
                    "means greater uncertainty"
                ),

            "VERY_LOW":
                "[0.00, 0.20)",

            "LOW":
                "[0.20, 0.40)",

            "MODERATE":
                "[0.40, 0.60)",

            "HIGH":
                "[0.60, 0.80)",

            "VERY_HIGH":
                "[0.80, 1.00]",

            "outcome_tuning_used":
                False,
        }

        updated[
            "stage_9_4_statistics"
        ] = {

            "fixture_count":
                result[
                    "fixture_count"
                ],

            "entropy_min":
                result[
                    "entropy_min"
                ],

            "entropy_max":
                result[
                    "entropy_max"
                ],

            "normalized_entropy_min":
                result[
                    "normalized_entropy_min"
                ],

            "normalized_entropy_max":
                result[
                    "normalized_entropy_max"
                ],

            "confidence_band_counts":
                result[
                    "confidence_band_counts"
                ],

            "uncertainty_band_counts":
                result[
                    "uncertainty_band_counts"
                ],
        }

        updated[
            "stage_9_3_snapshot"
        ] = {

            "input_sha256":
                result[
                    "stage9_3_input_sha256"
                ],

            "preserved":
                True,
        }

        updated[
            "output_artifact"
        ] = {

            "path":
                relative_path(
                    INTELLIGENCE_FILE
                ),

            "sha256":
                result[
                    "output_sha256"
                ],
        }

        dependency_identity = dict(
            updated.get(
                "dependency_identity",
                {}
            )
        )

        dependency_identity[
            "stage9_intelligence_contract"
        ] = {

            "path":
                relative_path(
                    CONTRACT_FILE
                ),

            "sha256":
                sha256_file(
                    CONTRACT_FILE
                ),
        }

        dependency_identity[
            "stage9_intelligence_contract_verification"
        ] = {

            "path":
                relative_path(
                    CONTRACT_VERIFICATION_FILE
                ),

            "sha256":
                sha256_file(
                    CONTRACT_VERIFICATION_FILE
                ),
        }

        dependency_identity[
            "match_intelligence_base"
        ] = {

            "path":
                relative_path(
                    BASE_FILE
                ),

            "sha256":
                sha256_file(
                    BASE_FILE
                ),
        }

        dependency_identity[
            "match_intelligence_base_report"
        ] = {

            "path":
                relative_path(
                    BASE_REPORT_FILE
                ),

            "sha256":
                sha256_file(
                    BASE_REPORT_FILE
                ),
        }

        updated[
            "dependency_identity"
        ] = dependency_identity

        safety = dict(
            updated.get(
                "safety",
                {}
            )
        )

        safety.update(
            {

                "interpretation_only":
                    True,

                "model_loaded":
                    False,

                "model_executed":
                    False,

                "model_modified":
                    False,

                "probabilities_modified":
                    False,

                "probabilities_recalibrated":
                    False,

                "prediction_labels_modified":
                    False,

                "source_confidence_modified":
                    False,

                "stage7_artifacts_modified":
                    False,

                "stage8_artifacts_modified":
                    False,

                "stage9_2_artifacts_modified":
                    False,

                "stage9_3_context_fields_modified":
                    False,

                "bookmaker_odds_used":
                    False,

                "future_results_used":
                    False,

                "final_test_accessed":
                    False,

                "outcome_based_threshold_tuning":
                    False,
            }
        )

        updated[
            "safety"
        ] = safety

        updated[
            "next_stage"
        ] = "9.5"

        # Verification script promotes this to true.
        updated[
            "stage9_ready_for_9_5"
        ] = False

        updated[
            "failures"
        ] = []

        save_json_atomic(
            REPORT_FILE,
            updated,
        )

        print(
            REPORT_FILE
        )

    print(
        "\n" + "=" * 72
    )

    if overall_pass:

        print(
            "STAGE 9.4: BUILT"
        )

        print(
            "CONFIDENCE & UNCERTAINTY LAYER: BUILT"
        )

        print(
            "STAGE 9 READY FOR 9.4 VERIFICATION"
        )

    else:

        print(
            "STAGE 9.4: FAIL"
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
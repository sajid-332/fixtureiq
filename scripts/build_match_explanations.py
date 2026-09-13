"""
FixtureIQ Stage 9.5
Build Deterministic Match Explanations.
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


from backend.services.match_explanation_builder import (
    MatchExplanationBuilder,
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

    print(
        "FixtureIQ Stage 9.5"
    )

    print(
        "MATCH EXPLANATION ENGINE"
    )

    print("=" * 72)

    failures = []

    # ========================================================
    # Stage 9.4 foundation
    # ========================================================

    print(
        "\n1. STAGE 9.4 FOUNDATION"
    )

    report = load_json(
        REPORT_FILE
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
        "Stage 9.4 COMPLETE",
        report.get(
            "stage_9_4_complete"
        )
        is True,
        failures,
    )

    check(
        "Confidence & Uncertainty VERIFIED",
        report.get(
            "confidence_uncertainty_layer"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Stage 9 ready for 9.5",
        report.get(
            "stage9_ready_for_9_5"
        )
        is True,
        failures,
    )

    if failures:

        sys.exit(1)

    # ========================================================
    # Protection
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

    stage9_4_sha = sha256_file(
        INTELLIGENCE_FILE
    )

    # ========================================================
    # Build
    # ========================================================

    print(
        "\n2. BUILD DETERMINISTIC EXPLANATIONS"
    )

    try:

        result = (
            MatchExplanationBuilder()
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
        "Stage 9.5 build PASS",
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
            "Stage 9.4 input SHA captured",
            result.get(
                "stage9_4_input_sha256"
            )
            == stage9_4_sha,
            failures,
        )

        check(
            "Protected snapshot unchanged",
            result.get(
                "protected_snapshot_sha256"
            )
            ==
            result.get(
                "output_protected_snapshot_sha256"
            ),
            failures,
        )

        check(
            "Deterministic templates only",
            result.get(
                "deterministic_templates"
            )
            is True,
            failures,
        )

        check(
            "LLM generation not used",
            result.get(
                "llm_generation_used"
            )
            is False,
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
            "Context intelligence unchanged",
            result.get(
                "context_intelligence_modified"
            )
            is False,
            failures,
        )

        check(
            "Confidence/uncertainty unchanged",
            result.get(
                "confidence_uncertainty_modified"
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
    # Save Stage 9.5 build evidence
    # ========================================================

    print(
        "\n4. SAVE STAGE 9.5 EVIDENCE"
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
        ] = "9.5"

        updated[
            "status"
        ] = "PASS"

        updated[
            "stage_9_5_complete"
        ] = True

        updated[
            "stage_9_5_status"
        ] = "COMPLETE"

        updated[
            "match_explanation_engine"
        ] = "BUILT"

        updated[
            "stage_9_5_generated_at_utc"
        ] = generated_at

        updated[
            "stage_9_5_rule_version"
        ] = (
            result[
                "explanation_version"
            ]
        )

        updated[
            "explanation_contract"
        ] = {

            "engine":
                "DETERMINISTIC_TEMPLATE_ENGINE",

            "llm_generation":
                False,

            "prediction_authority":
                "STAGE7_ONLY",

            "explanation_may_change_prediction":
                False,

            "explanation_may_change_probability":
                False,

            "explanation_may_change_context":
                False,

            "source_fields": [

                "stage7_predicted_label",
                "stage9_top_probability",
                "stage9_probability_margin",
                "stage9_context_support_score",
                "stage9_context_alignment",
                "stage9_confidence_band",
                "stage9_uncertainty_band",
                "stage9_league_position_gap",
                "stage9_points_gap",
                "stage9_goal_difference_gap",
                "stage9_recent_points_gap",
                "stage9_venue_form_points_gap",
            ],

            "context_signal_count":
                5,

            "language_rule":
                (
                    "DESCRIPTIVE_NON_GUARANTEED"
                ),

            "outcome_tuning_used":
                False,
        }

        updated[
            "stage_9_5_statistics"
        ] = {

            "fixture_count":
                result[
                    "fixture_count"
                ],

            "prediction_counts":
                result[
                    "prediction_counts"
                ],

            "alignment_counts":
                result[
                    "alignment_counts"
                ],
        }

        updated[
            "stage_9_4_snapshot"
        ] = {

            "input_sha256":
                result[
                    "stage9_4_input_sha256"
                ],

            "protected_columns_sha256":
                result[
                    "protected_snapshot_sha256"
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

                "deterministic_explanation_engine":
                    True,

                "llm_generation_used":
                    False,

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

                "context_intelligence_modified":
                    False,

                "confidence_uncertainty_modified":
                    False,

                "stage7_artifacts_modified":
                    False,

                "stage8_artifacts_modified":
                    False,

                "stage9_2_artifacts_modified":
                    False,

                "bookmaker_odds_used":
                    False,

                "future_results_used":
                    False,

                "final_test_accessed":
                    False,

                "outcome_based_tuning_used":
                    False,

                "guaranteed_result_language_allowed":
                    False,
            }
        )

        updated[
            "safety"
        ] = safety

        updated[
            "next_stage"
        ] = "9.6"

        # Independent verifier promotes this.
        updated[
            "stage9_ready_for_9_6"
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
            "STAGE 9.5: BUILT"
        )

        print(
            "MATCH EXPLANATION ENGINE: BUILT"
        )

        print(
            "STAGE 9 READY FOR 9.5 VERIFICATION"
        )

    else:

        print(
            "STAGE 9.5: FAIL"
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
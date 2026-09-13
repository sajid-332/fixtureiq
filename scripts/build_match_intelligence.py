"""
FixtureIQ Stage 9.3
Build Derived Match Intelligence.
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


from backend.services.match_intelligence_builder import (
    MatchIntelligenceBuilder,
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

OUTPUT_FILE = (
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


def save_json_atomic(
    path: Path,
    payload: dict,
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
    print("FixtureIQ Stage 9.3")
    print("DERIVED MATCH INTELLIGENCE")
    print("=" * 72)

    failures = []

    # ========================================================
    # Foundation
    # ========================================================

    print(
        "\n1. STAGE 9.2 FOUNDATION"
    )

    contract = load_json(
        CONTRACT_FILE
    )

    base_report = load_json(
        BASE_REPORT_FILE
    )

    check(
        "Stage 9.1 contract locked",
        contract.get(
            "status"
        )
        ==
        "LOCKED_MATCH_INTELLIGENCE_CONTRACT",
        failures,
    )

    check(
        "Stage 9.2 status PASS",
        base_report.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 9.2 COMPLETE",
        base_report.get(
            "stage_9_2_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 9 ready for 9.3",
        base_report.get(
            "final_gate",
            {}
        ).get(
            "stage9_ready_for_9_3"
        )
        is True,
        failures,
    )

    if failures:

        sys.exit(1)

    # ========================================================
    # Protect dependencies
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

    # ========================================================
    # Build
    # ========================================================

    print(
        "\n2. DERIVE MATCH INTELLIGENCE"
    )

    builder = MatchIntelligenceBuilder()

    try:

        result = builder.build_and_write()

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
        "Derived intelligence build PASS",
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
            "Base values preserved exactly",
            result.get(
                "base_values_preserved_exactly"
            )
            is True,
            failures,
        )

        check(
            "Probabilities not modified",
            result.get(
                "probabilities_modified"
            )
            is False,
            failures,
        )

        check(
            "Prediction labels not modified",
            result.get(
                "prediction_labels_modified"
            )
            is False,
            failures,
        )

        check(
            "Source confidence not modified",
            result.get(
                "source_confidence_modified"
            )
            is False,
            failures,
        )

        check(
            "Context support components = 5",
            result.get(
                "context_support_component_count"
            )
            == 5,
            failures,
        )

        check(
            "Output artifact exists",
            OUTPUT_FILE.exists(),
            failures,
        )

    # ========================================================
    # Dependency protection
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

    # ========================================================
    # Report
    # ========================================================

    print(
        "\n4. SAVE STAGE 9.3 REPORT"
    )

    overall_pass = (
        len(
            failures
        )
        == 0
    )

    if overall_pass:

        generated_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        report = {

            "stage":
                "9.3",

            "status":
                "PASS",

            "stage_9_3_complete":
                True,

            "stage_9_3_status":
                "COMPLETE",

            "derived_match_intelligence":
                "VERIFIED",

            "generated_at_utc":
                generated_at,

            "rule_version":
                "STAGE9_3_DERIVED_INTELLIGENCE_V1",

            "fixture_count":
                result[
                    "fixture_count"
                ],

            "column_count":
                result[
                    "column_count"
                ],

            "stage9_3_populated_field_count":
                result[
                    "stage9_3_populated_field_count"
                ],

            "stage9_4_reserved_field_count":
                result[
                    "stage9_4_reserved_field_count"
                ],

            "stage9_5_reserved_field_count":
                result[
                    "stage9_5_reserved_field_count"
                ],

            "probability_metrics": {

                "top_probability":
                    "MAX_OF_STAGE7_PROBABILITIES",

                "second_probability":
                    "SECOND_HIGHEST_STAGE7_PROBABILITY",

                "probability_margin":
                    (
                        "TOP_PROBABILITY_MINUS_"
                        "SECOND_PROBABILITY"
                    ),

                "probability_mutation":
                    False,
            },

            "context_gap_semantics": {

                "positive":
                    "HOME_ADVANTAGE",

                "negative":
                    "AWAY_ADVANTAGE",

                "zero":
                    "TIED",

                "league_position_gap":
                    (
                        "away_position-minus-home_position"
                    ),

                "points_gap":
                    "home_points-minus-away_points",

                "goal_difference_gap":
                    (
                        "home_goal_difference-minus-"
                        "away_goal_difference"
                    ),

                "recent_points_gap":
                    (
                        "home_recent_points-minus-"
                        "away_recent_points"
                    ),

                "recent_goal_difference_gap":
                    (
                        "home_recent_goal_difference-minus-"
                        "away_recent_goal_difference"
                    ),

                "venue_form_points_gap":
                    (
                        "home_home_recent_points-minus-"
                        "away_away_recent_points"
                    ),
            },

            "context_support_rule": {

                "component_count":
                    5,

                "components": [

                    "league_position",
                    "points",
                    "goal_difference",
                    "recent_points",
                    "venue_recent_points",
                ],

                "home_advantage_vote":
                    1,

                "away_advantage_vote":
                    -1,

                "tie_or_unavailable_vote":
                    0,

                "minimum_score":
                    -5,

                "maximum_score":
                    5,

                "missing_venue_sample_policy":
                    "NEUTRAL_ZERO_VOTE",

                "outcome_tuning_used":
                    False,
            },

            "context_alignment_rule": {

                "Home Win": {

                    "SUPPORTIVE":
                        "score >= 2",

                    "CONTRADICTORY":
                        "score <= -2",

                    "NEUTRAL":
                        "score == 0",

                    "MIXED":
                        "score in {-1, 1}",
                },

                "Away Win": {

                    "SUPPORTIVE":
                        "score <= -2",

                    "CONTRADICTORY":
                        "score >= 2",

                    "NEUTRAL":
                        "score == 0",

                    "MIXED":
                        "score in {-1, 1}",
                },

                "Draw": {

                    "SUPPORTIVE":
                        "abs(score) <= 1",

                    "MIXED":
                        "abs(score) == 2",

                    "CONTRADICTORY":
                        "abs(score) >= 3",
                },

                "outcome_tuning_used":
                    False,
            },

            "stage_ownership": {

                "stage_9_3":
                    "DERIVED_MATCH_INTELLIGENCE",

                "stage_9_4":
                    "CONFIDENCE_AND_UNCERTAINTY_PENDING",

                "stage_9_5":
                    "EXPLANATION_PENDING",
            },

            "output_artifact": {

                "path":
                    relative_path(
                        OUTPUT_FILE
                    ),

                "sha256":
                    sha256_file(
                        OUTPUT_FILE
                    ),
            },

            "dependency_identity": {

                "stage9_intelligence_contract": {

                    "path":
                        relative_path(
                            CONTRACT_FILE
                        ),

                    "sha256":
                        sha256_file(
                            CONTRACT_FILE
                        ),
                },

                "stage9_intelligence_contract_verification": {

                    "path":
                        relative_path(
                            CONTRACT_VERIFICATION_FILE
                        ),

                    "sha256":
                        sha256_file(
                            CONTRACT_VERIFICATION_FILE
                        ),
                },

                "match_intelligence_base": {

                    "path":
                        relative_path(
                            BASE_FILE
                        ),

                    "sha256":
                        sha256_file(
                            BASE_FILE
                        ),
                },

                "match_intelligence_base_report": {

                    "path":
                        relative_path(
                            BASE_REPORT_FILE
                        ),

                    "sha256":
                        sha256_file(
                            BASE_REPORT_FILE
                        ),
                },
            },

            "safety": {

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

                "bookmaker_odds_used":
                    False,

                "future_results_used":
                    False,

                "final_test_accessed":
                    False,

                "outcome_based_tuning_used":
                    False,
            },

            "next_stage":
                "9.4",

            "stage9_ready_for_9_4":
                True,

            "failures":
                [],
        }

        save_json_atomic(
            REPORT_FILE,
            report,
        )

        print(
            REPORT_FILE
        )

    print(
        "\n" + "=" * 72
    )

    if overall_pass:

        print(
            "STAGE 9.3: COMPLETE"
        )

        print(
            "DERIVED MATCH INTELLIGENCE: BUILT"
        )

        print(
            "STAGE 9 READY FOR 9.3 VERIFICATION"
        )

    else:

        print(
            "STAGE 9.3: FAIL"
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
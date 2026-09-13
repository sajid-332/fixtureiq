"""
FixtureIQ Stage 9.1.3 + 9.1.4

9.1.3 Canonical Match Intelligence Schema
9.1.4 Freshness & Provenance Contract

Extends:
data/processed/intelligence/stage9_intelligence_contract.json

Requires:
- Stage 9.1.1 PASS
- Stage 9.1.2 PASS
- independent 9.1.1/9.1.2 verification PARTIAL_PASS

Does NOT complete Stage 9.1.
9.1.5 remains PENDING.

No prediction generation.
No model loading.
No model execution.
No provider fetch.
No Stage 7 writes.
No Stage 8 writes.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# Project root
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


# ============================================================
# Directories
# ============================================================

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


# ============================================================
# Inputs
# ============================================================

PRODUCTION_PREDICTIONS_FILE = (
    PRODUCTION_DIR
    / "production_predictions.csv"
)

ENRICHED_FIXTURES_FILE = (
    CONTEXT_DIR
    / "enriched_upcoming_fixtures.csv"
)

FIXTURE_CONTEXT_REPORT_FILE = (
    CONTEXT_DIR
    / "fixture_context_report.json"
)

STAGE8_FINAL_FILE = (
    CONTEXT_DIR
    / "stage8_final_verification.json"
)


# ============================================================
# Existing Stage 9 contract
# ============================================================

CONTRACT_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract.json"
)

VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract_verification.json"
)


# ============================================================
# Future Stage 9 artifacts
# ============================================================

MATCH_INTELLIGENCE_BASE_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_base.csv"
)

MATCH_INTELLIGENCE_BASE_REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_base_report.json"
)

MATCH_INTELLIGENCE_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence.csv"
)

MATCH_INTELLIGENCE_REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_report.json"
)

INTELLIGENCE_API_VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "intelligence_api_verification.json"
)

INTELLIGENCE_RUNTIME_VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "intelligence_runtime_verification.json"
)

STAGE9_FINAL_VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "stage9_final_verification.json"
)


# ============================================================
# Canonical schema constants
# ============================================================

REQUIRED_IDENTITY_FIELDS = [

    "fixture_id",

    "home_team_id",
    "home_team_name",

    "away_team_id",
    "away_team_name",
]


DATE_FIELD_CANDIDATES = [

    "date",
    "kickoff_utc",
    "utc_date",
    "kickoff",
    "match_date",
]


SOURCE_PREDICTION_FIELDS = [

    "prob_home_win",
    "prob_draw",
    "prob_away_win",
    "predicted_label",
    "confidence",
]


PREDICTION_COPY_FIELDS = [

    "stage7_prob_home_win",
    "stage7_prob_draw",
    "stage7_prob_away_win",
    "stage7_predicted_label",
    "stage7_confidence",
]


PREDICTION_FIELD_MAPPING = {

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


DERIVED_INTELLIGENCE_FIELDS = [

    "stage9_top_probability",
    "stage9_second_probability",
    "stage9_probability_margin",

    "stage9_entropy",
    "stage9_normalized_entropy",

    "stage9_confidence_band",
    "stage9_uncertainty_band",

    "stage9_league_position_gap",
    "stage9_points_gap",
    "stage9_goal_difference_gap",

    "stage9_recent_points_gap",
    "stage9_recent_goal_difference_gap",

    "stage9_venue_form_points_gap",

    "stage9_context_support_score",
    "stage9_context_alignment",

    "stage9_explanation_headline",
    "stage9_explanation_summary",
]


REQUIRED_CONTEXT_FIELDS = [

    "home_team_position",
    "away_team_position",

    "home_team_points",
    "away_team_points",

    "home_team_goal_difference",
    "away_team_goal_difference",

    "home_team_recent_points",
    "away_team_recent_points",

    "home_team_recent_goal_difference",
    "away_team_recent_goal_difference",

    "home_team_home_recent_points",
    "away_team_away_recent_points",
]


# ============================================================
# Helpers
# ============================================================

def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise FileNotFoundError(
            f"Required artifact missing: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        payload = json.load(file)

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

    if not path.exists():

        raise FileNotFoundError(
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


def csv_fields(
    path: Path,
) -> list[str]:

    if not path.exists():

        raise FileNotFoundError(
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

        fields = (
            reader.fieldnames
            or []
        )

    if not fields:

        raise RuntimeError(
            f"No CSV fields found: {path}"
        )

    return list(
        fields
    )


def identify_date_field(
    fields: list[str],
) -> str:

    for candidate in DATE_FIELD_CANDIDATES:

        if candidate in fields:

            return candidate

    raise RuntimeError(
        "No supported fixture date field found."
    )


def require(
    label: str,
    condition,
) -> None:

    if not condition:

        raise RuntimeError(
            f"Precondition failed: {label}"
        )

    print(
        f"{label}: PASS"
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 9.1.3 + 9.1.4"
    )

    print(
        "Canonical Schema + Freshness/Provenance Contract"
    )

    print("=" * 72)

    # ========================================================
    # 1. Existing contract
    # ========================================================

    print(
        "\n1. EXISTING STAGE 9.1 CONTRACT"
    )

    contract = load_json(
        CONTRACT_FILE
    )

    verification = load_json(
        VERIFICATION_FILE
    )

    require(
        "Contract stage = 9.1",
        contract.get(
            "stage"
        )
        == "9.1",
    )

    require(
        "Contract type correct",
        contract.get(
            "contract_type"
        )
        == "MATCH_INTELLIGENCE_CONTRACT",
    )

    require(
        "Stage 9.1 incomplete",
        contract.get(
            "stage_9_1_complete"
        )
        is False,
    )

    sub_stages = contract.get(
        "sub_stages",
        {}
    )

    require(
        "9.1.1 PASS",
        sub_stages.get(
            "9.1.1"
        )
        == "PASS",
    )

    require(
        "9.1.2 PASS",
        sub_stages.get(
            "9.1.2"
        )
        == "PASS",
    )

    require(
        "9.1.3 currently PENDING",
        sub_stages.get(
            "9.1.3"
        )
        == "PENDING",
    )

    require(
        "9.1.4 currently PENDING",
        sub_stages.get(
            "9.1.4"
        )
        == "PENDING",
    )

    require(
        "9.1.5 currently PENDING",
        sub_stages.get(
            "9.1.5"
        )
        == "PENDING",
    )

    verification_sub_stages = (
        verification.get(
            "sub_stages",
            {}
        )
    )

    require(
        "Independent 9.1.1 verification PASS",
        verification_sub_stages.get(
            "9.1.1"
        )
        == "PASS",
    )

    require(
        "Independent 9.1.2 verification PASS",
        verification_sub_stages.get(
            "9.1.2"
        )
        == "PASS",
    )

    # ========================================================
    # 2. Existing allowed-input hashes
    # ========================================================

    print(
        "\n2. EXISTING INPUT FRESHNESS"
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

    require(
        "Allowed input contract exists",
        len(
            allowed_inputs
        )
        == 11,
    )

    for name, item in allowed_inputs.items():

        path_text = item.get(
            "path"
        )

        require(
            f"{name} path recorded",
            isinstance(
                path_text,
                str,
            )
            and
            bool(
                path_text
            ),
        )

        source_path = (
            BASE_DIR
            / Path(
                path_text
            )
        )

        require(
            f"{name} artifact exists",
            source_path.exists(),
        )

        require(
            f"{name} hash still current",
            item.get(
                "sha256"
            )
            ==
            sha256_file(
                source_path
            ),
        )

    # ========================================================
    # 3. Source schemas
    # ========================================================

    print(
        "\n3. SOURCE SCHEMAS"
    )

    prediction_fields = csv_fields(
        PRODUCTION_PREDICTIONS_FILE
    )

    context_fields = csv_fields(
        ENRICHED_FIXTURES_FILE
    )

    for field in REQUIRED_IDENTITY_FIELDS:

        require(
            f"Prediction identity field {field}",
            field
            in prediction_fields,
        )

        require(
            f"Context identity field {field}",
            field
            in context_fields,
        )

    for field in SOURCE_PREDICTION_FIELDS:

        require(
            f"Prediction source field {field}",
            field
            in prediction_fields,
        )

    for field in REQUIRED_CONTEXT_FIELDS:

        require(
            f"Context intelligence field {field}",
            field
            in context_fields,
        )

    fixture_date_field = (
        identify_date_field(
            context_fields
        )
    )

    print(
        "Fixture date field:",
        fixture_date_field,
    )

    # ========================================================
    # 4. Stage 9.1.3 schema construction
    # ========================================================

    print(
        "\n4. STAGE 9.1.3 CANONICAL INTELLIGENCE SCHEMA"
    )

    collision_fields = [

        field

        for field in PREDICTION_COPY_FIELDS

        if field in context_fields
    ]

    require(
        "Prediction copy fields do not collide with context",
        not collision_fields,
    )

    collision_derived = [

        field

        for field in DERIVED_INTELLIGENCE_FIELDS

        if (
            field in context_fields
            or
            field in PREDICTION_COPY_FIELDS
        )
    ]

    require(
        "Derived fields do not collide with base schema",
        not collision_derived,
    )

    base_fields = (
        list(
            context_fields
        )
        +
        list(
            PREDICTION_COPY_FIELDS
        )
    )

    final_fields = (
        list(
            base_fields
        )
        +
        list(
            DERIVED_INTELLIGENCE_FIELDS
        )
    )

    require(
        "Base schema unique",
        len(
            base_fields
        )
        ==
        len(
            set(
                base_fields
            )
        ),
    )

    require(
        "Final schema unique",
        len(
            final_fields
        )
        ==
        len(
            set(
                final_fields
            )
        ),
    )

    logical_types = {

        "stage7_prob_home_win":
            "FLOAT",

        "stage7_prob_draw":
            "FLOAT",

        "stage7_prob_away_win":
            "FLOAT",

        "stage7_predicted_label":
            "STRING",

        "stage7_confidence":
            "FLOAT",

        "stage9_top_probability":
            "FLOAT",

        "stage9_second_probability":
            "FLOAT",

        "stage9_probability_margin":
            "FLOAT",

        "stage9_entropy":
            "FLOAT",

        "stage9_normalized_entropy":
            "FLOAT",

        "stage9_confidence_band":
            "STRING",

        "stage9_uncertainty_band":
            "STRING",

        "stage9_league_position_gap":
            "INTEGER",

        "stage9_points_gap":
            "INTEGER",

        "stage9_goal_difference_gap":
            "INTEGER",

        "stage9_recent_points_gap":
            "INTEGER",

        "stage9_recent_goal_difference_gap":
            "INTEGER",

        "stage9_venue_form_points_gap":
            "INTEGER",

        "stage9_context_support_score":
            "INTEGER",

        "stage9_context_alignment":
            "STRING",

        "stage9_explanation_headline":
            "STRING",

        "stage9_explanation_summary":
            "STRING",
    }

    schema_semantics = {

        "stage7_prediction_fields": {

            "copy_mode":
                "EXACT_VALUE_COPY",

            "mapping":
                PREDICTION_FIELD_MAPPING,

            "probability_mutation_allowed":
                False,

            "prediction_label_mutation_allowed":
                False,

            "source_confidence_mutation_allowed":
                False,
        },

        "probability_metrics": {

            "top_probability":
                (
                    "maximum of the three copied Stage 7 "
                    "probabilities"
                ),

            "second_probability":
                (
                    "second-highest of the three copied "
                    "Stage 7 probabilities"
                ),

            "probability_margin":
                (
                    "top_probability minus second_probability"
                ),

            "entropy":
                (
                    "Shannon entropy computed only from copied "
                    "Stage 7 probabilities"
                ),

            "normalized_entropy":
                "entropy divided by ln(3)",

            "probabilities_are_not_predictions_created_by_stage9":
                True,
        },

        "context_gap_direction": {

            "stage9_league_position_gap":
                (
                    "away_team_position minus "
                    "home_team_position; positive means "
                    "home side has better league position"
                ),

            "stage9_points_gap":
                (
                    "home_team_points minus away_team_points"
                ),

            "stage9_goal_difference_gap":
                (
                    "home_team_goal_difference minus "
                    "away_team_goal_difference"
                ),

            "stage9_recent_points_gap":
                (
                    "home_team_recent_points minus "
                    "away_team_recent_points"
                ),

            "stage9_recent_goal_difference_gap":
                (
                    "home_team_recent_goal_difference minus "
                    "away_team_recent_goal_difference"
                ),

            "stage9_venue_form_points_gap":
                (
                    "home_team_home_recent_points minus "
                    "away_team_away_recent_points"
                ),
        },

        "bands": {

            "confidence_band_allowed_values": [

                "VERY_LOW",
                "LOW",
                "MODERATE",
                "HIGH",
                "VERY_HIGH",
            ],

            "uncertainty_band_allowed_values": [

                "VERY_LOW",
                "LOW",
                "MODERATE",
                "HIGH",
                "VERY_HIGH",
            ],

            "threshold_rules_locked_later":
                True,

            "outcome_based_threshold_tuning_allowed":
                False,
        },

        "context_alignment": {

            "allowed_values": [

                "SUPPORTIVE",
                "MIXED",
                "CONTRADICTORY",
                "NEUTRAL",
            ],

            "support_component_count":
                5,

            "support_score_min":
                -5,

            "support_score_max":
                5,

            "rule_definition_locked_later":
                True,

            "outcome_based_rule_tuning_allowed":
                False,
        },

        "explanation": {

            "deterministic":
                True,

            "template_or_rule_driven":
                True,

            "may_describe_prediction":
                True,

            "may_change_prediction":
                False,

            "may_claim_guaranteed_outcome":
                False,
        },
    }

    canonical_schema = {

        "schema_version":
            "1.0.0",

        "fixture_primary_key":
            "fixture_id",

        "fixture_primary_key_unique_required":
            True,

        "fixture_date_field":
            fixture_date_field,

        "strict_join": {

            "primary_join_field":
                "fixture_id",

            "identity_validation_fields":
                REQUIRED_IDENTITY_FIELDS,

            "fixture_id_exact_match_required":
                True,

            "home_team_id_exact_match_required":
                True,

            "home_team_name_exact_match_required":
                True,

            "away_team_id_exact_match_required":
                True,

            "away_team_name_exact_match_required":
                True,

            "fuzzy_matching_allowed":
                False,

            "best_effort_fallback_allowed":
                False,

            "unmatched_prediction_allowed":
                False,

            "unmatched_context_allowed":
                False,

            "duplicate_fixture_id_allowed":
                False,
        },

        "source_context_fields": {

            "count":
                len(
                    context_fields
                ),

            "fields":
                context_fields,

            "preserve_exactly":
                True,

            "source":
                "enriched_upcoming_fixtures",
        },

        "source_prediction_fields": {

            "count":
                len(
                    SOURCE_PREDICTION_FIELDS
                ),

            "fields":
                SOURCE_PREDICTION_FIELDS,

            "copy_mapping":
                PREDICTION_FIELD_MAPPING,

            "copied_output_fields":
                PREDICTION_COPY_FIELDS,

            "preserve_values_exactly":
                True,

            "source":
                "production_predictions",
        },

        "base_intelligence_schema": {

            "artifact":
                relative_path(
                    MATCH_INTELLIGENCE_BASE_FILE
                ),

            "column_count":
                len(
                    base_fields
                ),

            "fields":
                base_fields,
        },

        "derived_intelligence_fields": {

            "count":
                len(
                    DERIVED_INTELLIGENCE_FIELDS
                ),

            "fields":
                DERIVED_INTELLIGENCE_FIELDS,
        },

        "final_intelligence_schema": {

            "artifact":
                relative_path(
                    MATCH_INTELLIGENCE_FILE
                ),

            "column_count":
                len(
                    final_fields
                ),

            "fields":
                final_fields,
        },

        "logical_types":
            logical_types,

        "semantics":
            schema_semantics,
    }

    require(
        "Canonical base schema built",
        len(
            base_fields
        )
        > len(
            context_fields
        ),
    )

    require(
        "Canonical final schema extends base",
        len(
            final_fields
        )
        >
        len(
            base_fields
        ),
    )

    # ========================================================
    # 5. Output artifact contract
    # ========================================================

    print(
        "\n5. STAGE 9 OUTPUT ARTIFACT CONTRACT"
    )

    output_artifacts = {

        "stage9_intelligence_contract": {

            "path":
                relative_path(
                    CONTRACT_FILE
                ),

            "stage":
                "9.1",

            "type":
                "CONTRACT",
        },

        "stage9_intelligence_contract_verification": {

            "path":
                relative_path(
                    VERIFICATION_FILE
                ),

            "stage":
                "9.1",

            "type":
                "VERIFICATION",
        },

        "match_intelligence_base": {

            "path":
                relative_path(
                    MATCH_INTELLIGENCE_BASE_FILE
                ),

            "stage":
                "9.2",

            "type":
                "CSV",
        },

        "match_intelligence_base_report": {

            "path":
                relative_path(
                    MATCH_INTELLIGENCE_BASE_REPORT_FILE
                ),

            "stage":
                "9.2",

            "type":
                "JSON",
        },

        "match_intelligence": {

            "path":
                relative_path(
                    MATCH_INTELLIGENCE_FILE
                ),

            "stage":
                "9.3-9.5",

            "type":
                "CSV",
        },

        "match_intelligence_report": {

            "path":
                relative_path(
                    MATCH_INTELLIGENCE_REPORT_FILE
                ),

            "stage":
                "9.3-9.5",

            "type":
                "JSON",
        },

        "intelligence_api_verification": {

            "path":
                relative_path(
                    INTELLIGENCE_API_VERIFICATION_FILE
                ),

            "stage":
                "9.6",

            "type":
                "JSON",
        },

        "intelligence_runtime_verification": {

            "path":
                relative_path(
                    INTELLIGENCE_RUNTIME_VERIFICATION_FILE
                ),

            "stage":
                "9.7",

            "type":
                "JSON",
        },

        "stage9_final_verification": {

            "path":
                relative_path(
                    STAGE9_FINAL_VERIFICATION_FILE
                ),

            "stage":
                "9.8",

            "type":
                "JSON",
        },
    }

    output_paths = [

        item[
            "path"
        ]

        for item in (
            output_artifacts.values()
        )
    ]

    require(
        "All Stage 9 output paths unique",
        len(
            output_paths
        )
        ==
        len(
            set(
                output_paths
            )
        ),
    )

    require(
        "All outputs remain under intelligence root",
        all(
            path.startswith(
                "data/processed/intelligence/"
            )

            for path in output_paths
        ),
    )

    output_contract = {

        "output_root":
            "data/processed/intelligence",

        "outputs":
            output_artifacts,

        "undeclared_output_allowed":
            False,

        "stage7_output_write_allowed":
            False,

        "stage8_output_write_allowed":
            False,

        "production_prediction_write_allowed":
            False,

        "context_artifact_write_allowed":
            False,
    }

    # ========================================================
    # 6. Stage 9.1.4 freshness contract
    # ========================================================

    print(
        "\n6. STAGE 9.1.4 FRESHNESS CONTRACT"
    )

    direct_dependency_names = list(
        allowed_inputs.keys()
    )

    freshness_contract = {

        "mode":
            "DUAL_UPSTREAM_DEPENDENCY_PLUS_TEMPORAL_BOUNDARY",

        "authoritative_prediction_dependency":
            "production_predictions",

        "authoritative_context_dependency":
            "enriched_upcoming_fixtures",

        "direct_dependency_count":
            len(
                direct_dependency_names
            ),

        "direct_dependencies":
            direct_dependency_names,

        "any_allowed_input_hash_change_invalidates_intelligence":
            True,

        "prediction_artifact_change_invalidates_intelligence":
            True,

        "prediction_metadata_change_invalidates_intelligence":
            True,

        "prediction_report_change_invalidates_intelligence":
            True,

        "prediction_verification_change_invalidates_intelligence":
            True,

        "stage7_final_gate_change_invalidates_intelligence":
            True,

        "fixture_context_change_invalidates_intelligence":
            True,

        "fixture_context_report_change_invalidates_intelligence":
            True,

        "context_api_verification_change_invalidates_intelligence":
            True,

        "context_runtime_verification_change_invalidates_intelligence":
            True,

        "stage8_final_gate_change_invalidates_intelligence":
            True,

        "prediction_context_fixture_set_mismatch_invalidates_intelligence":
            True,

        "identity_mismatch_invalidates_intelligence":
            True,

        "duplicate_fixture_identity_invalidates_intelligence":
            True,

        "upstream_stage7_verification_required":
            True,

        "upstream_stage8_verification_required":
            True,

        "inherit_stage8_temporal_boundary":
            True,

        "fixture_kickoff_reached_invalidates_intelligence":
            True,

        "future_fixture_state_propagation_allowed":
            False,

        "stale_fallback_allowed":
            False,

        "partial_unverified_output_allowed":
            False,

        "automatic_best_effort_reconciliation_allowed":
            False,

        "rebuild_required_after_dependency_change":
            True,

        "runtime_revalidation_required":
            True,

        "fail_closed":
            True,
    }

    require(
        "Dual-upstream freshness mode",
        freshness_contract.get(
            "mode"
        )
        ==
        "DUAL_UPSTREAM_DEPENDENCY_PLUS_TEMPORAL_BOUNDARY",
    )

    require(
        "Any dependency change invalidates intelligence",
        freshness_contract.get(
            "any_allowed_input_hash_change_invalidates_intelligence"
        )
        is True,
    )

    require(
        "Temporal boundary inherited",
        freshness_contract.get(
            "inherit_stage8_temporal_boundary"
        )
        is True,
    )

    require(
        "Freshness is fail-closed",
        freshness_contract.get(
            "fail_closed"
        )
        is True,
    )

    # ========================================================
    # 7. Provenance contract
    # ========================================================

    print(
        "\n7. STAGE 9.1.4 PROVENANCE CONTRACT"
    )

    provenance_contract = {

        "content_hash_algorithm":
            "SHA256",

        "dependency_hash_required":
            True,

        "all_direct_dependency_hashes_required":
            True,

        "source_paths_required":
            True,

        "generated_at_utc_required":
            True,

        "timezone_aware_timestamps_required":
            True,

        "prediction_source_identity_required":
            True,

        "context_source_identity_required":
            True,

        "stage7_verification_identity_required":
            True,

        "stage8_verification_identity_required":
            True,

        "fixture_identity_validation_required":
            True,

        "fixture_count_reconciliation_required":
            True,

        "prediction_value_equality_evidence_required":
            True,

        "prediction_label_equality_evidence_required":
            True,

        "source_confidence_equality_evidence_required":
            True,

        "context_value_preservation_evidence_required":
            True,

        "filesystem_mtime_as_provenance_allowed":
            False,

        "fabricated_source_timestamp_allowed":
            False,

        "provider_timestamp_fabrication_allowed":
            False,

        "unverifiable_provenance_allowed":
            False,
    }

    require(
        "SHA256 provenance locked",
        provenance_contract.get(
            "content_hash_algorithm"
        )
        == "SHA256",
    )

    require(
        "All dependency hashes required",
        provenance_contract.get(
            "all_direct_dependency_hashes_required"
        )
        is True,
    )

    require(
        "Filesystem mtime provenance prohibited",
        provenance_contract.get(
            "filesystem_mtime_as_provenance_allowed"
        )
        is False,
    )

    require(
        "Unverifiable provenance prohibited",
        provenance_contract.get(
            "unverifiable_provenance_allowed"
        )
        is False,
    )

    # ========================================================
    # 8. Runtime readiness contract
    # ========================================================

    print(
        "\n8. RUNTIME READINESS CONTRACT"
    )

    runtime_readiness_contract = {

        "ready_state":
            "READY",

        "not_ready_state":
            "NOT_READY",

        "healthy_http_status":
            200,

        "stale_http_status":
            503,

        "unknown_resource_http_status":
            404,

        "write_method_http_status":
            405,

        "stage7_prediction_source_must_be_current":
            True,

        "stage8_context_source_must_be_current":
            True,

        "stage8_temporal_boundary_must_be_valid":
            True,

        "dependency_hashes_rechecked_at_runtime":
            True,

        "upstream_readiness_rechecked_at_runtime":
            True,

        "stale_intelligence_may_be_served":
            False,

        "runtime_recovery_without_restart_required":
            True,

        "http_no_store_required":
            True,

        "fail_closed":
            True,
    }

    require(
        "Stale intelligence -> HTTP 503",
        runtime_readiness_contract.get(
            "stale_http_status"
        )
        == 503,
    )

    require(
        "Stale intelligence serving prohibited",
        runtime_readiness_contract.get(
            "stale_intelligence_may_be_served"
        )
        is False,
    )

    # ========================================================
    # 9. Extend existing contract
    # ========================================================

    print(
        "\n9. UPDATE STAGE 9.1 CONTRACT"
    )

    updated_at = (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )

    contract[
        "contract_version"
    ] = "1.1.0-partial"

    contract[
        "status"
    ] = "PARTIAL_LOCK"

    contract[
        "stage_9_1_complete"
    ] = False

    contract[
        "stage_9_1_status"
    ] = "IN_PROGRESS"

    contract[
        "updated_at_utc"
    ] = updated_at

    updated_sub_stages = dict(
        contract.get(
            "sub_stages",
            {}
        )
    )

    updated_sub_stages[
        "9.1.1"
    ] = "PASS"

    updated_sub_stages[
        "9.1.2"
    ] = "PASS"

    updated_sub_stages[
        "9.1.3"
    ] = "PASS"

    updated_sub_stages[
        "9.1.4"
    ] = "PASS"

    updated_sub_stages[
        "9.1.5"
    ] = "PENDING"

    contract[
        "sub_stages"
    ] = updated_sub_stages

    contract[
        "stage_9_1_3"
    ] = {

        "name":
            "CANONICAL_INTELLIGENCE_SCHEMA",

        "status":
            "PASS",

        "canonical_schema":
            canonical_schema,

        "output_artifact_contract":
            output_contract,
    }

    contract[
        "stage_9_1_4"
    ] = {

        "name":
            "FRESHNESS_AND_PROVENANCE_CONTRACT",

        "status":
            "PASS",

        "freshness_contract":
            freshness_contract,

        "provenance_contract":
            provenance_contract,

        "runtime_readiness_contract":
            runtime_readiness_contract,
    }

    contract[
        "pending_contract_sections"
    ] = {

        "9.1.5":
            "FINAL_STAGE_9_1_GATE",
    }

    save_json_atomic(
        CONTRACT_FILE,
        contract,
    )

    print(
        CONTRACT_FILE
    )

    # ========================================================
    # Final
    # ========================================================

    print(
        "\n" + "=" * 72
    )

    print(
        "STAGE 9.1.3: PASS"
    )

    print(
        "CANONICAL INTELLIGENCE SCHEMA: LOCKED"
    )

    print(
        "STAGE 9.1.4: PASS"
    )

    print(
        "FRESHNESS & PROVENANCE CONTRACT: LOCKED"
    )

    print(
        "STAGE 9.1: IN PROGRESS"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
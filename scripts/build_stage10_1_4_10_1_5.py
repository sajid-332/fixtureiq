from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


# ============================================================
# Inputs
# ============================================================

AUDIT_FILE = (
    ROOT
    / "docs"
    / "stage10"
    / "frontend_audit.json"
)

RESPONSIBILITY_FILE = (
    ROOT
    / "docs"
    / "stage10"
    / "frontend_responsibility_contract.json"
)

ENDPOINT_CONTRACT_FILE = (
    ROOT
    / "docs"
    / "stage10"
    / "frontend_api_endpoint_contract.json"
)

STAGE_10_1_3_VERIFICATION_FILE = (
    ROOT
    / "data"
    / "processed"
    / "frontend"
    / "stage10_1_3_verification.json"
)


# ============================================================
# Outputs
# ============================================================

ROUTE_CONTRACT_FILE = (
    ROOT
    / "docs"
    / "stage10"
    / "frontend_route_architecture.json"
)

DOMAIN_CONTRACT_FILE = (
    ROOT
    / "docs"
    / "stage10"
    / "frontend_domain_model_contract.json"
)

DOMAIN_TYPES_FILE = (
    ROOT
    / "frontend"
    / "lib"
    / "domain"
    / "types.ts"
)


# ============================================================
# Helpers
# ============================================================

def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise RuntimeError(
            f"Missing required artifact: {path}"
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


def sha256_file(
    path: Path,
) -> str:

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as file:

        for chunk in iter(
            lambda:
                file.read(
                    1024 * 1024
                ),
            b"",
        ):

            digest.update(
                chunk
            )

    return digest.hexdigest()


def relative(
    path: Path,
) -> str:

    return (
        str(
            path.resolve()
            .relative_to(
                ROOT.resolve()
            )
        )
        .replace(
            "\\",
            "/",
        )
    )


def save_text_atomic(
    path: Path,
    text: str,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        text,
        encoding="utf-8",
    )

    temporary.replace(
        path
    )


def save_json_atomic(
    path: Path,
    payload: dict,
) -> None:

    save_text_atomic(
        path,
        (
            json.dumps(
                payload,
                indent=2,
            )
            +
            "\n"
        ),
    )


# ============================================================
# TypeScript source
# ============================================================

DOMAIN_TYPES_SOURCE = """/*
 * FixtureIQ Stage 10.1.5
 * Frontend domain models.
 *
 * Authority boundaries:
 *
 * Stage 7 = prediction authority
 * Stage 8 = context authority
 * Stage 9 = intelligence authority
 * Stage 10 = presentation authority
 *
 * These types do not implement prediction or intelligence logic.
 * Runtime response validation is introduced in Stage 10.2.6.
 */


// ============================================================
// Common scalar / enum domains
// ============================================================

export const OUTCOME_LABELS = [
  "Home Win",
  "Draw",
  "Away Win",
] as const;

export type OutcomeLabel =
  (typeof OUTCOME_LABELS)[number];


export const FIVE_LEVEL_BANDS = [
  "VERY_LOW",
  "LOW",
  "MODERATE",
  "HIGH",
  "VERY_HIGH",
] as const;

export type FiveLevelBand =
  (typeof FIVE_LEVEL_BANDS)[number];

export type ConfidenceBand =
  FiveLevelBand;

export type UncertaintyBand =
  FiveLevelBand;


export const CONTEXT_ALIGNMENTS = [
  "SUPPORTIVE",
  "MIXED",
  "CONTRADICTORY",
  "NEUTRAL",
] as const;

export type ContextAlignment =
  (typeof CONTEXT_ALIGNMENTS)[number];


export const SERVICE_STATES = [
  "READY",
  "NOT_READY",
  "NOT_FOUND",
] as const;

export type ServiceState =
  (typeof SERVICE_STATES)[number];


export type FixtureId =
  string | number;

export type NullableNumber =
  number | null;


export type ContextSupportScore =
  | -5
  | -4
  | -3
  | -2
  | -1
  | 0
  | 1
  | 2
  | 3
  | 4
  | 5;


// ============================================================
// Fixture identity
// ============================================================

export type FixtureIdentity = Readonly<{
  fixture_id: FixtureId;
  home_team_name: string;
  away_team_name: string;
}>;


// ============================================================
// Stage 7 prediction authority
// ============================================================

export type Stage7Prediction = Readonly<{
  stage7_prob_home_win: number;
  stage7_prob_draw: number;
  stage7_prob_away_win: number;

  stage7_predicted_label:
    OutcomeLabel;

  stage7_confidence:
    number;
}>;


// ============================================================
// Stage 9 intelligence authority
// ============================================================

export type Stage9Intelligence = Readonly<{
  stage9_top_probability:
    number;

  stage9_probability_margin:
    number;

  stage9_confidence_band:
    ConfidenceBand;

  stage9_uncertainty_band:
    UncertaintyBand;

  stage9_context_support_score:
    ContextSupportScore;

  stage9_context_alignment:
    ContextAlignment;

  stage9_explanation_headline:
    string;

  stage9_explanation_summary:
    string;
}>;


// ============================================================
// Core match-intelligence model
// ============================================================

export type MatchIntelligence =
  Readonly<
    FixtureIdentity
    &
    Stage7Prediction
    &
    Stage9Intelligence
  >;


// ============================================================
// Stage 8 context presentation model
//
// Stage 10 may present these values.
// It may NOT calculate or replace Stage 8 context.
// ============================================================

export type ComparisonMetric =
  Readonly<{
    home: NullableNumber;
    away: NullableNumber;
  }>;


export type MatchContextView =
  Readonly<{
    leaguePosition:
      ComparisonMetric;

    points:
      ComparisonMetric;

    goalDifference:
      ComparisonMetric;

    recentPoints:
      ComparisonMetric;

    recentGoalDifference:
      ComparisonMetric;

    venueRecentPoints:
      ComparisonMetric;
  }>;


// ============================================================
// Page-facing models
//
// TypeScript utility types are used to avoid duplicating the
// authoritative prediction/intelligence shape.
// ============================================================

export type MatchCardModel =
  Readonly<
    Pick<
      MatchIntelligence,
      | "fixture_id"
      | "home_team_name"
      | "away_team_name"
      | "stage7_prob_home_win"
      | "stage7_prob_draw"
      | "stage7_prob_away_win"
      | "stage7_predicted_label"
      | "stage7_confidence"
      | "stage9_confidence_band"
      | "stage9_uncertainty_band"
      | "stage9_context_alignment"
      | "stage9_explanation_headline"
    >
  >;


export type MatchDetailModel =
  Readonly<{
    intelligence:
      MatchIntelligence;

    context:
      MatchContextView | null;
  }>;


export type TeamMatchModel =
  MatchCardModel;


// ============================================================
// Next.js dynamic route parameters
// ============================================================

export type FixtureRouteParams =
  Readonly<{
    fixtureId: string;
  }>;


export type TeamRouteParams =
  Readonly<{
    teamName: string;
  }>;


// ============================================================
// UI runtime states
//
// Detailed HTTP/error handling is locked in Stage 10.1.6.
// ============================================================

export type UiDataState =
  | Readonly<{
      state: "READY";
    }>
  | Readonly<{
      state: "LOADING";
    }>
  | Readonly<{
      state: "NOT_FOUND";
    }>
  | Readonly<{
      state: "NOT_READY";
    }>
  | Readonly<{
      state: "CONNECTION_ERROR";
    }>;


// ============================================================
// Presentation integrity
// ============================================================

export type ProbabilityDisplay =
  Readonly<{
    raw: number;
    formatted: string;
  }>;


/*
 * `formatted` may differ visually from `raw`
 * because display rounding is allowed.
 *
 * `raw` remains the authoritative backend value.
 *
 * Stage 10 must never create replacement probabilities from
 * the formatted value.
 */
"""


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.1.4 + 10.1.5"
    )

    print(
        "ROUTE ARCHITECTURE + TYPESCRIPT DOMAIN MODEL BUILD"
    )

    print("=" * 72)

    audit = load_json(
        AUDIT_FILE
    )

    responsibility = load_json(
        RESPONSIBILITY_FILE
    )

    endpoint_contract = load_json(
        ENDPOINT_CONTRACT_FILE
    )

    previous = load_json(
        STAGE_10_1_3_VERIFICATION_FILE
    )

    if (
        previous.get(
            "status"
        )
        !=
        "PASS"
    ):

        raise RuntimeError(
            "Stage 10.1.3 is not PASS."
        )

    if (
        previous.get(
            "stage10_ready_for_10_1_4"
        )
        is not True
    ):

        raise RuntimeError(
            "Stage 10.1.3 did not authorize 10.1.4."
        )

    if (
        responsibility.get(
            "status"
        )
        !=
        "LOCKED"
    ):

        raise RuntimeError(
            "Stage 10.1.2 responsibility boundary is not LOCKED."
        )

    if (
        endpoint_contract.get(
            "status"
        )
        !=
        "LOCKED"
    ):

        raise RuntimeError(
            "Stage 10.1.3 endpoint contract is not LOCKED."
        )

    app_root = (
        audit.get(
            "routing",
            {}
        )
        .get(
            "app_root"
        )
    )

    if not app_root:

        raise RuntimeError(
            "Next.js App Router root not found in 10.1.1 audit."
        )

    locked_backend_routes = set(
        endpoint_contract.get(
            "route_set",
            []
        )
    )

    required_backend_routes = {
        "/api/v1/intelligence/upcoming",
        "/api/v1/intelligence/matches/<fixture_id>",
        "/api/v1/intelligence/team/<path:team_name>",
        "/api/v1/intelligence/status",
    }

    missing_backend_routes = (
        required_backend_routes
        -
        locked_backend_routes
    )

    if missing_backend_routes:

        raise RuntimeError(
            (
                "Required Stage 9 routes are not "
                "present in the locked API contract: "
                f"{sorted(missing_backend_routes)}"
            )
        )

    # ========================================================
    # Stage 10.1.4
    # ========================================================

    route_contract = {
        "stage":
            "10.1.4",

        "version":
            "1.0.0",

        "name":
            "FRONTEND_ROUTE_ARCHITECTURE",

        "status":
            "LOCKED",

        "router":
            "NEXTJS_APP_ROUTER",

        "app_root":
            app_root,

        "routing_principles": {
            "file_system_router":
                True,

            "backend_is_prediction_authority":
                True,

            "frontend_prediction_routes":
                False,

            "frontend_api_route_handlers_required":
                False,

            "direct_backend_artifact_routes":
                False,

            "primary_user_data_source":
                "/api/v1/intelligence",

            "server_first":
                True,

            "client_components_only_when_required":
                True,
        },

        "routes": [
            {
                "path":
                    "/",

                "kind":
                    "INDEX",

                "purpose":
                    "UPCOMING_MATCHES_DASHBOARD",

                "implementation_owner":
                    "10.4",

                "page_file":
                    f"{app_root}/page.tsx",

                "dynamic_params":
                    [],

                "primary_backend_route":
                    "/api/v1/intelligence/upcoming",

                "readiness_backend_route":
                    "/api/v1/intelligence/status",

                "prediction_authority":
                    "STAGE7",

                "context_authority":
                    "STAGE8",

                "intelligence_authority":
                    "STAGE9",

                "presentation_authority":
                    "STAGE10",
            },

            {
                "path":
                    "/matches/[fixtureId]",

                "kind":
                    "DYNAMIC_MATCH",

                "purpose":
                    "MATCH_INTELLIGENCE_DETAIL",

                "implementation_owner":
                    "10.5",

                "page_file":
                    (
                        f"{app_root}/matches/"
                        "[fixtureId]/page.tsx"
                    ),

                "dynamic_params": [
                    "fixtureId"
                ],

                "primary_backend_route":
                    (
                        "/api/v1/intelligence/"
                        "matches/<fixture_id>"
                    ),

                "readiness_backend_route":
                    "/api/v1/intelligence/status",

                "prediction_authority":
                    "STAGE7",

                "context_authority":
                    "STAGE8",

                "intelligence_authority":
                    "STAGE9",

                "presentation_authority":
                    "STAGE10",
            },

            {
                "path":
                    "/teams/[teamName]",

                "kind":
                    "DYNAMIC_TEAM",

                "purpose":
                    "TEAM_INTELLIGENCE_VIEW",

                "implementation_owner":
                    "10.6",

                "page_file":
                    (
                        f"{app_root}/teams/"
                        "[teamName]/page.tsx"
                    ),

                "dynamic_params": [
                    "teamName"
                ],

                "primary_backend_route":
                    (
                        "/api/v1/intelligence/"
                        "team/<path:team_name>"
                    ),

                "readiness_backend_route":
                    "/api/v1/intelligence/status",

                "prediction_authority":
                    "STAGE7",

                "context_authority":
                    "STAGE8",

                "intelligence_authority":
                    "STAGE9",

                "presentation_authority":
                    "STAGE10",
            },
        ],

        "framework_files": {
            "layout":
                f"{app_root}/layout.tsx",

            "not_found_owner":
                "10.8",

            "loading_owner":
                "10.8",

            "error_boundary_owner":
                "10.8",

            "global_navigation_owner":
                "10.3",
        },

        "route_creation_policy": {
            "10_1_4_creates_page_files":
                False,

            "route_files_created_by_feature_stage":
                True,

            "dashboard_page_owner":
                "10.4",

            "match_page_owner":
                "10.5",

            "team_page_owner":
                "10.6",
        },

        "dependency_identity": {
            relative(
                AUDIT_FILE
            ): {
                "sha256":
                    sha256_file(
                        AUDIT_FILE
                    )
            },

            relative(
                RESPONSIBILITY_FILE
            ): {
                "sha256":
                    sha256_file(
                        RESPONSIBILITY_FILE
                    )
            },

            relative(
                ENDPOINT_CONTRACT_FILE
            ): {
                "sha256":
                    sha256_file(
                        ENDPOINT_CONTRACT_FILE
                    )
            },

            relative(
                STAGE_10_1_3_VERIFICATION_FILE
            ): {
                "sha256":
                    sha256_file(
                        STAGE_10_1_3_VERIFICATION_FILE
                    )
            },
        },

        "promotion": {
            "stage10_1_4_complete":
                False,

            "stage10_1_complete":
                False,

            "stage10_complete":
                False,
        },
    }

    save_json_atomic(
        ROUTE_CONTRACT_FILE,
        route_contract,
    )

    # ========================================================
    # Stage 10.1.5
    # ========================================================

    save_text_atomic(
        DOMAIN_TYPES_FILE,
        DOMAIN_TYPES_SOURCE,
    )

    domain_contract = {
        "stage":
            "10.1.5",

        "version":
            "1.0.0",

        "name":
            "FRONTEND_TYPESCRIPT_DOMAIN_MODELS",

        "status":
            "LOCKED",

        "typescript_source":
            relative(
                DOMAIN_TYPES_FILE
            ),

        "typescript_sha256":
            sha256_file(
                DOMAIN_TYPES_FILE
            ),

        "design": {
            "immutable_models":
                True,

            "typescript_readonly_utility":
                True,

            "typescript_pick_utility":
                True,

            "prediction_authority":
                "STAGE7",

            "context_authority":
                "STAGE8",

            "intelligence_authority":
                "STAGE9",

            "presentation_authority":
                "STAGE10",

            "frontend_prediction_logic":
                False,

            "frontend_context_recalculation":
                False,

            "frontend_intelligence_recalculation":
                False,
        },

        "exported_domains": [
            "OutcomeLabel",
            "FiveLevelBand",
            "ConfidenceBand",
            "UncertaintyBand",
            "ContextAlignment",
            "ServiceState",
            "FixtureId",
            "NullableNumber",
            "ContextSupportScore",
            "FixtureIdentity",
            "Stage7Prediction",
            "Stage9Intelligence",
            "MatchIntelligence",
            "ComparisonMetric",
            "MatchContextView",
            "MatchCardModel",
            "MatchDetailModel",
            "TeamMatchModel",
            "FixtureRouteParams",
            "TeamRouteParams",
            "UiDataState",
            "ProbabilityDisplay"
        ],

        "core_stage9_fields": [
            "fixture_id",
            "home_team_name",
            "away_team_name",

            "stage7_prob_home_win",
            "stage7_prob_draw",
            "stage7_prob_away_win",
            "stage7_predicted_label",
            "stage7_confidence",

            "stage9_top_probability",
            "stage9_probability_margin",
            "stage9_confidence_band",
            "stage9_uncertainty_band",
            "stage9_context_support_score",
            "stage9_context_alignment",
            "stage9_explanation_headline",
            "stage9_explanation_summary"
        ],

        "route_param_models": {
            "fixture":
                "FixtureRouteParams",

            "team":
                "TeamRouteParams",
        },

        "display_rules": {
            "display_rounding_allowed":
                True,

            "display_rounding_may_change_source":
                False,

            "raw_probability_retained":
                True,
        },

        "runtime_validation": {
            "implemented_in_10_1_5":
                False,

            "owner":
                "10.2.6",

            "reason":
                (
                    "10.1.5 defines compile-time domain "
                    "models; runtime API response validation "
                    "belongs to the API client layer."
                ),
        },

        "wire_schema": {
            "fully_locked_in_10_1_5":
                False,

            "finalization_owner":
                "10.2.6",

            "domain_models_may_be_narrower_than_wire_payload":
                True,
        },

        "dependency_identity": {
            relative(
                ROUTE_CONTRACT_FILE
            ): {
                "sha256":
                    sha256_file(
                        ROUTE_CONTRACT_FILE
                    )
            },

            relative(
                RESPONSIBILITY_FILE
            ): {
                "sha256":
                    sha256_file(
                        RESPONSIBILITY_FILE
                    )
            },

            relative(
                ENDPOINT_CONTRACT_FILE
            ): {
                "sha256":
                    sha256_file(
                        ENDPOINT_CONTRACT_FILE
                    )
            },
        },

        "promotion": {
            "stage10_1_5_complete":
                False,

            "stage10_1_complete":
                False,

            "stage10_complete":
                False,
        },

        "generated_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }

    save_json_atomic(
        DOMAIN_CONTRACT_FILE,
        domain_contract,
    )

    print()

    print(
        "Stage 10.1.4 route architecture:"
    )

    for route in route_contract[
        "routes"
    ]:

        print(
            f"  {route['path']} "
            f"-> {route['primary_backend_route']}"
        )

    print()

    print(
        "TypeScript domain source:"
    )

    print(
        f"  {relative(DOMAIN_TYPES_FILE)}"
    )

    print()

    print(
        "Route contract:"
    )

    print(
        f"  {relative(ROUTE_CONTRACT_FILE)}"
    )

    print()

    print(
        "Domain contract:"
    )

    print(
        f"  {relative(DOMAIN_CONTRACT_FILE)}"
    )

    print()

    print("=" * 72)

    print(
        "STAGE 10.1.4 ROUTE ARCHITECTURE: BUILT"
    )

    print(
        "STAGE 10.1.5 TYPESCRIPT DOMAIN MODELS: BUILT"
    )

    print(
        "STAGE 10 IS NOT YET PROMOTED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
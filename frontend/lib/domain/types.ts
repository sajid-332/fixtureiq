/*
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

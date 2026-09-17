import "server-only";

import {
  CONTEXT_ALIGNMENTS,
  FIVE_LEVEL_BANDS,
  OUTCOME_LABELS,
} from "../domain/types";

import type {
  ConfidenceBand,
  ContextAlignment,
  ContextSupportScore,
  FixtureId,
  MatchIntelligence,
  OutcomeLabel,
  UncertaintyBand,
} from "../domain/types";

import type {
  JsonValue,
} from "../api/validation";


type JsonObject =
  Readonly<{
    [key: string]:
      JsonValue;
  }>;


export type UpcomingDashboardMatch =
  Readonly<
    MatchIntelligence
    &
    {
      kickoffUtc:
        string;
    }
  >;


export const UPCOMING_KICKOFF_SOURCE_FIELD =
  "date" as const;


const outcomeLabels =
  new Set<string>(
    OUTCOME_LABELS,
  );


const fiveLevelBands =
  new Set<string>(
    FIVE_LEVEL_BANDS,
  );


const contextAlignments =
  new Set<string>(
    CONTEXT_ALIGNMENTS,
  );


function isObject(
  value: JsonValue,
): value is JsonObject {

  return (
    typeof value === "object"
    &&
    value !== null
    &&
    !Array.isArray(
      value,
    )
  );
}


function isFixtureId(
  value: JsonValue | undefined,
): value is FixtureId {

  return (
    (
      typeof value === "string"
      &&
      value.length > 0
    )
    ||
    (
      typeof value === "number"
      &&
      Number.isFinite(
        value,
      )
    )
  );
}


function isProbability(
  value: JsonValue | undefined,
): value is number {

  return (
    typeof value === "number"
    &&
    Number.isFinite(
      value,
    )
    &&
    value >= 0
    &&
    value <= 1
  );
}


function isOutcomeLabel(
  value: JsonValue | undefined,
): value is OutcomeLabel {

  return (
    typeof value === "string"
    &&
    outcomeLabels.has(
      value,
    )
  );
}


function isConfidenceBand(
  value: JsonValue | undefined,
): value is ConfidenceBand {

  return (
    typeof value === "string"
    &&
    fiveLevelBands.has(
      value,
    )
  );
}


function isUncertaintyBand(
  value: JsonValue | undefined,
): value is UncertaintyBand {

  return (
    typeof value === "string"
    &&
    fiveLevelBands.has(
      value,
    )
  );
}


function isContextAlignment(
  value: JsonValue | undefined,
): value is ContextAlignment {

  return (
    typeof value === "string"
    &&
    contextAlignments.has(
      value,
    )
  );
}


function isContextSupportScore(
  value: JsonValue | undefined,
): value is ContextSupportScore {

  return (
    typeof value === "number"
    &&
    Number.isInteger(
      value,
    )
    &&
    value >= -5
    &&
    value <= 5
  );
}


function isFiniteNumber(
  value: JsonValue | undefined,
): value is number {

  return (
    typeof value === "number"
    &&
    Number.isFinite(
      value,
    )
  );
}


function requireString(
  value: JsonValue | undefined,
  field: string,
): string {

  if (
    typeof value !== "string"
    ||
    value.length === 0
  ) {
    throw new TypeError(
      `Invalid dashboard field: ${field}`,
    );
  }

  return value;
}


function looksLikeMatch(
  value: JsonObject,
): boolean {

  return (
    "fixture_id"
    in value
    &&
    "stage7_prob_home_win"
    in value
    &&
    "stage9_context_alignment"
    in value
  );
}



const NUMERIC_TRANSPORT_FIELDS =
  new Set<string>(
    [
      "stage7_prob_home_win",
      "stage7_prob_draw",
      "stage7_prob_away_win",
      "stage7_confidence",
      "stage9_top_probability",
      "stage9_probability_margin",
      "stage9_context_support_score",
    ],
  );


function normalizeTransportRecord(
  value: JsonObject,
): JsonObject {

  const normalized: {
    [key: string]:
      JsonValue;
  } = {
    ...value,
  };


  for (
    const field
    of
    NUMERIC_TRANSPORT_FIELDS
  ) {

    const current =
      normalized[
        field
      ];


    if (
      typeof current === "string"
      &&
      current.trim().length > 0
    ) {

      const parsed =
        Number(
          current,
        );


      if (
        Number.isFinite(
          parsed,
        )
      ) {

        normalized[
          field
        ] = parsed;
      }
    }
  }


  return normalized;
}


function parseMatch(
  value: JsonObject,
): UpcomingDashboardMatch {

  const fixtureId =
    value.fixture_id;

  const homeTeamName =
    value.home_team_name;

  const awayTeamName =
    value.away_team_name;

  const probHome =
    value.stage7_prob_home_win;

  const probDraw =
    value.stage7_prob_draw;

  const probAway =
    value.stage7_prob_away_win;

  const predictedLabel =
    value.stage7_predicted_label;

  const confidence =
    value.stage7_confidence;

  const topProbability =
    value.stage9_top_probability;

  const probabilityMargin =
    value.stage9_probability_margin;

  const confidenceBand =
    value.stage9_confidence_band;

  const uncertaintyBand =
    value.stage9_uncertainty_band;

  const supportScore =
    value.stage9_context_support_score;

  const alignment =
    value.stage9_context_alignment;

  const headline =
    value.stage9_explanation_headline;

  const summary =
    value.stage9_explanation_summary;

  const kickoff =
    value[
      UPCOMING_KICKOFF_SOURCE_FIELD
    ];


  if (
    !isFixtureId(
      fixtureId,
    )
  ) {
    throw new TypeError(
      "Invalid dashboard fixture_id.",
    );
  }


  if (
    !isProbability(
      probHome,
    )
    ||
    !isProbability(
      probDraw,
    )
    ||
    !isProbability(
      probAway,
    )
    ||
    !isProbability(
      confidence,
    )
    ||
    !isProbability(
      topProbability,
    )
  ) {
    throw new TypeError(
      "Invalid dashboard probability field.",
    );
  }


  if (
    !isFiniteNumber(
      probabilityMargin,
    )
    ||
    probabilityMargin < 0
    ||
    probabilityMargin > 1
  ) {
    throw new TypeError(
      "Invalid dashboard probability margin.",
    );
  }


  if (
    !isOutcomeLabel(
      predictedLabel,
    )
  ) {
    throw new TypeError(
      "Invalid dashboard outcome label.",
    );
  }


  if (
    !isConfidenceBand(
      confidenceBand,
    )
    ||
    !isUncertaintyBand(
      uncertaintyBand,
    )
  ) {
    throw new TypeError(
      "Invalid dashboard intelligence band.",
    );
  }


  if (
    !isContextSupportScore(
      supportScore,
    )
  ) {
    throw new TypeError(
      "Invalid dashboard context support score.",
    );
  }


  if (
    !isContextAlignment(
      alignment,
    )
  ) {
    throw new TypeError(
      "Invalid dashboard context alignment.",
    );
  }


  const kickoffUtc =
    requireString(
      kickoff,
      UPCOMING_KICKOFF_SOURCE_FIELD,
    );


  if (
    Number.isNaN(
      Date.parse(
        kickoffUtc,
      ),
    )
  ) {
    throw new TypeError(
      "Invalid dashboard kickoff timestamp.",
    );
  }


  return {
    fixture_id:
      fixtureId,

    home_team_name:
      requireString(
        homeTeamName,
        "home_team_name",
      ),

    away_team_name:
      requireString(
        awayTeamName,
        "away_team_name",
      ),

    stage7_prob_home_win:
      probHome,

    stage7_prob_draw:
      probDraw,

    stage7_prob_away_win:
      probAway,

    stage7_predicted_label:
      predictedLabel,

    stage7_confidence:
      confidence,

    stage9_top_probability:
      topProbability,

    stage9_probability_margin:
      probabilityMargin,

    stage9_confidence_band:
      confidenceBand,

    stage9_uncertainty_band:
      uncertaintyBand,

    stage9_context_support_score:
      supportScore,

    stage9_context_alignment:
      alignment,

    stage9_explanation_headline:
      requireString(
        headline,
        "stage9_explanation_headline",
      ),

    stage9_explanation_summary:
      requireString(
        summary,
        "stage9_explanation_summary",
      ),

    kickoffUtc,
  };
}


function collectMatches(
  value: JsonValue,
  output:
    UpcomingDashboardMatch[],
  seen:
    Set<string>,
): void {

  if (
    Array.isArray(
      value,
    )
  ) {

    for (
      const item
      of
      value
    ) {
      collectMatches(
        item,
        output,
        seen,
      );
    }

    return;
  }


  if (
    !isObject(
      value,
    )
  ) {
    return;
  }


  if (
    looksLikeMatch(
      value,
    )
  ) {

    const match =
      parseMatch(
        normalizeTransportRecord(
          value,
        ),
      );


    const identity =
      `${typeof match.fixture_id}:${
        String(
          match.fixture_id,
        )
      }`;


    if (
      seen.has(
        identity,
      )
    ) {
      throw new Error(
        "Duplicate fixture_id in upcoming intelligence response.",
      );
    }


    seen.add(
      identity,
    );

    output.push(
      match,
    );

    return;
  }


  for (
    const child
    of
    Object.values(
      value,
    )
  ) {
    collectMatches(
      child,
      output,
      seen,
    );
  }
}


export function extractUpcomingDashboardMatches(
  data: JsonValue,
): readonly UpcomingDashboardMatch[] {

  const output:
    UpcomingDashboardMatch[] =
      [];

  const seen =
    new Set<string>();


  collectMatches(
    data,
    output,
    seen,
  );


  return output;
}

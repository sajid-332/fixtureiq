import "server-only";

import {
  CONTEXT_ALIGNMENTS,
} from "../domain/types";

import type {
  ContextAlignment,
  ContextSupportScore,
  FixtureId,
} from "../domain/types";

import type {
  JsonValue,
} from "../api/validation";


type JsonObject =
  Readonly<{
    [key: string]:
      JsonValue;
  }>;


export type MatchIntelligenceDetailRecord =
  Readonly<{
    fixture_id:
      FixtureId;

    home_team_home_form_matches_available:
      number;

    home_team_home_recent_points:
      number;

    away_team_away_form_matches_available:
      number;

    away_team_away_recent_points:
      number;

    stage9_context_support_score:
      ContextSupportScore;

    stage9_context_alignment:
      ContextAlignment;

    stage9_explanation_headline:
      string;

    stage9_explanation_summary:
      string;
  }>;


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


function transportInteger(
  value: JsonValue | undefined,
  field: string,
): number {

  if (
    typeof value === "number"
    &&
    Number.isFinite(
      value,
    )
    &&
    Number.isInteger(
      value,
    )
  ) {
    return value;
  }


  if (
    typeof value === "string"
    &&
    value.trim().length > 0
  ) {

    const parsed =
      Number(
        value,
      );


    if (
      Number.isFinite(
        parsed,
      )
      &&
      Number.isInteger(
        parsed,
      )
    ) {
      return parsed;
    }
  }


  throw new TypeError(
    `Invalid integer intelligence field: ${field}`,
  );
}


function nonNegativeInteger(
  value: JsonValue | undefined,
  field: string,
): number {

  const parsed =
    transportInteger(
      value,
      field,
    );


  if (
    parsed < 0
  ) {
    throw new RangeError(
      `Negative intelligence field: ${field}`,
    );
  }


  return parsed;
}


function supportScore(
  value: JsonValue | undefined,
): ContextSupportScore {

  const parsed =
    transportInteger(
      value,
      "stage9_context_support_score",
    );


  if (
    parsed < -5
    ||
    parsed > 5
  ) {
    throw new RangeError(
      "Stage 9 context-support score must be within -5..5.",
    );
  }


  return parsed as ContextSupportScore;
}


function contextAlignment(
  value: JsonValue | undefined,
): ContextAlignment {

  if (
    typeof value !== "string"
    ||
    !contextAlignments.has(
      value,
    )
  ) {
    throw new TypeError(
      "Invalid Stage 9 context alignment.",
    );
  }


  return value as ContextAlignment;
}


function requiredText(
  value: JsonValue | undefined,
  field: string,
): string {

  if (
    typeof value !== "string"
    ||
    value.trim().length === 0
  ) {
    throw new TypeError(
      `Invalid intelligence text field: ${field}`,
    );
  }


  return value;
}


function looksLikeIntelligenceRecord(
  value: JsonObject,
): boolean {

  return (
    "fixture_id"
    in value
    &&
    "home_team_home_form_matches_available"
    in value
    &&
    "home_team_home_recent_points"
    in value
    &&
    "away_team_away_form_matches_available"
    in value
    &&
    "away_team_away_recent_points"
    in value
    &&
    "stage9_context_support_score"
    in value
    &&
    "stage9_context_alignment"
    in value
    &&
    "stage9_explanation_headline"
    in value
    &&
    "stage9_explanation_summary"
    in value
  );
}


function parseIntelligenceRecord(
  value: JsonObject,
): MatchIntelligenceDetailRecord {

  const fixtureId =
    value.fixture_id;


  if (
    !isFixtureId(
      fixtureId,
    )
  ) {
    throw new TypeError(
      "Invalid intelligence fixture_id.",
    );
  }


  return {
    fixture_id:
      fixtureId,

    home_team_home_form_matches_available:
      nonNegativeInteger(
        value.home_team_home_form_matches_available,
        "home_team_home_form_matches_available",
      ),

    home_team_home_recent_points:
      nonNegativeInteger(
        value.home_team_home_recent_points,
        "home_team_home_recent_points",
      ),

    away_team_away_form_matches_available:
      nonNegativeInteger(
        value.away_team_away_form_matches_available,
        "away_team_away_form_matches_available",
      ),

    away_team_away_recent_points:
      nonNegativeInteger(
        value.away_team_away_recent_points,
        "away_team_away_recent_points",
      ),

    stage9_context_support_score:
      supportScore(
        value.stage9_context_support_score,
      ),

    stage9_context_alignment:
      contextAlignment(
        value.stage9_context_alignment,
      ),

    stage9_explanation_headline:
      requiredText(
        value.stage9_explanation_headline,
        "stage9_explanation_headline",
      ),

    stage9_explanation_summary:
      requiredText(
        value.stage9_explanation_summary,
        "stage9_explanation_summary",
      ),
  };
}


function collectIntelligenceRecord(
  value: JsonValue,
  expectedFixtureId: string,
  output: MatchIntelligenceDetailRecord[],
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

      collectIntelligenceRecord(
        item,
        expectedFixtureId,
        output,
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
    looksLikeIntelligenceRecord(
      value,
    )
  ) {

    const record =
      parseIntelligenceRecord(
        value,
      );


    if (
      String(
        record.fixture_id,
      )
      ===
      expectedFixtureId
    ) {

      output.push(
        record,
      );
    }

    return;
  }


  for (
    const child
    of
    Object.values(
      value,
    )
  ) {

    collectIntelligenceRecord(
      child,
      expectedFixtureId,
      output,
    );
  }
}


export function extractMatchIntelligenceDetailRecord(
  data: JsonValue,
  expectedFixtureId: string,
): MatchIntelligenceDetailRecord {

  const records:
    MatchIntelligenceDetailRecord[] =
      [];


  collectIntelligenceRecord(
    data,
    expectedFixtureId,
    records,
  );


  if (
    records.length === 0
  ) {
    throw new Error(
      "Requested Stage 9 intelligence detail is absent from the READY response.",
    );
  }


  if (
    records.length !== 1
  ) {
    throw new Error(
      "Requested Stage 9 intelligence detail appears more than once.",
    );
  }


  return records[0];
}

import "server-only";

import {
  CONTEXT_ALIGNMENTS,
  FIVE_LEVEL_BANDS,
  OUTCOME_LABELS,
} from "../domain/types";

import type {
  ConfidenceBand,
  ContextAlignment,
  FixtureId,
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


export type TeamPredictionRecord =
  Readonly<{
    fixture_id:
      FixtureId;

    date:
      string;

    home_team_name:
      string;

    away_team_name:
      string;

    stage7_prob_home_win:
      number;

    stage7_prob_draw:
      number;

    stage7_prob_away_win:
      number;

    stage7_predicted_label:
      OutcomeLabel;

    stage7_confidence:
      number;

    stage9_confidence_band:
      ConfidenceBand;

    stage9_uncertainty_band:
      UncertaintyBand;

    stage9_context_alignment:
      ContextAlignment;
  }>;


export type TeamPageData =
  Readonly<{
    teamName:
      string;

    matches:
      readonly TeamPredictionRecord[];
  }>;


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


function requiredString(
  value: JsonValue | undefined,
  field: string,
): string {

  if (
    typeof value !== "string"
    ||
    value.length === 0
  ) {
    throw new TypeError(
      `Invalid team intelligence field: ${field}`,
    );
  }


  return value;
}


function transportNumber(
  value: JsonValue | undefined,
  field: string,
): number {

  if (
    typeof value === "number"
    &&
    Number.isFinite(
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
    ) {
      return parsed;
    }
  }


  throw new TypeError(
    `Invalid numeric team intelligence field: ${field}`,
  );
}


function probability(
  value: JsonValue | undefined,
  field: string,
): number {

  const parsed =
    transportNumber(
      value,
      field,
    );


  if (
    parsed < 0
    ||
    parsed > 1
  ) {
    throw new RangeError(
      `Invalid probability field: ${field}`,
    );
  }


  return parsed;
}


function outcomeLabel(
  value: JsonValue | undefined,
): OutcomeLabel {

  if (
    typeof value !== "string"
    ||
    !outcomeLabels.has(
      value,
    )
  ) {
    throw new TypeError(
      "Invalid Stage 7 predicted label.",
    );
  }


  return value as OutcomeLabel;
}


function confidenceBand(
  value: JsonValue | undefined,
): ConfidenceBand {

  if (
    typeof value !== "string"
    ||
    !fiveLevelBands.has(
      value,
    )
  ) {
    throw new TypeError(
      "Invalid Stage 9 confidence band.",
    );
  }


  return value as ConfidenceBand;
}


function uncertaintyBand(
  value: JsonValue | undefined,
): UncertaintyBand {

  if (
    typeof value !== "string"
    ||
    !fiveLevelBands.has(
      value,
    )
  ) {
    throw new TypeError(
      "Invalid Stage 9 uncertainty band.",
    );
  }


  return value as UncertaintyBand;
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


function looksLikeTeamPredictionRecord(
  value: JsonObject,
): boolean {

  return (
    "fixture_id"
    in value
    &&
    "date"
    in value
    &&
    "home_team_name"
    in value
    &&
    "away_team_name"
    in value
    &&
    "stage7_prob_home_win"
    in value
    &&
    "stage7_prob_draw"
    in value
    &&
    "stage7_prob_away_win"
    in value
    &&
    "stage7_predicted_label"
    in value
    &&
    "stage7_confidence"
    in value
    &&
    "stage9_confidence_band"
    in value
    &&
    "stage9_uncertainty_band"
    in value
    &&
    "stage9_context_alignment"
    in value
  );
}


function parseTeamPredictionRecord(
  value: JsonObject,
): TeamPredictionRecord {

  const fixtureId =
    value.fixture_id;


  if (
    !isFixtureId(
      fixtureId,
    )
  ) {
    throw new TypeError(
      "Invalid team prediction fixture_id.",
    );
  }


  const date =
    requiredString(
      value.date,
      "date",
    );


  if (
    Number.isNaN(
      Date.parse(
        date,
      ),
    )
  ) {
    throw new TypeError(
      "Invalid team prediction kickoff date.",
    );
  }


  return {
    fixture_id:
      fixtureId,

    date,

    home_team_name:
      requiredString(
        value.home_team_name,
        "home_team_name",
      ),

    away_team_name:
      requiredString(
        value.away_team_name,
        "away_team_name",
      ),

    stage7_prob_home_win:
      probability(
        value.stage7_prob_home_win,
        "stage7_prob_home_win",
      ),

    stage7_prob_draw:
      probability(
        value.stage7_prob_draw,
        "stage7_prob_draw",
      ),

    stage7_prob_away_win:
      probability(
        value.stage7_prob_away_win,
        "stage7_prob_away_win",
      ),

    stage7_predicted_label:
      outcomeLabel(
        value.stage7_predicted_label,
      ),

    stage7_confidence:
      probability(
        value.stage7_confidence,
        "stage7_confidence",
      ),

    stage9_confidence_band:
      confidenceBand(
        value.stage9_confidence_band,
      ),

    stage9_uncertainty_band:
      uncertaintyBand(
        value.stage9_uncertainty_band,
      ),

    stage9_context_alignment:
      contextAlignment(
        value.stage9_context_alignment,
      ),
  };
}


function collectRecords(
  value: JsonValue,
  output: TeamPredictionRecord[],
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

      collectRecords(
        item,
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
    looksLikeTeamPredictionRecord(
      value,
    )
  ) {

    output.push(
      parseTeamPredictionRecord(
        value,
      ),
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

    collectRecords(
      child,
      output,
    );
  }
}


export function extractTeamPageData(
  data: JsonValue,
  requestedTeamName: string,
): TeamPageData {

  if (
    requestedTeamName.length === 0
  ) {
    throw new TypeError(
      "Team route parameter cannot be empty.",
    );
  }


  const records:
    TeamPredictionRecord[] =
      [];


  collectRecords(
    data,
    records,
  );


  const fixtureIds =
    new Set<string>();


  for (
    const record
    of
    records
  ) {

    const belongsToRequestedTeam =
      (
        record.home_team_name
        ===
        requestedTeamName
      )
      ||
      (
        record.away_team_name
        ===
        requestedTeamName
      );


    if (
      !belongsToRequestedTeam
    ) {
      throw new Error(
        "Team endpoint returned a fixture outside the requested team identity.",
      );
    }


    const fixtureKey =
      String(
        record.fixture_id,
      );


    if (
      fixtureIds.has(
        fixtureKey,
      )
    ) {
      throw new Error(
        "Team endpoint returned duplicate fixture identity.",
      );
    }


    fixtureIds.add(
      fixtureKey,
    );
  }


  return {
    teamName:
      requestedTeamName,

    matches:
      records,
  };
}

import "server-only";

import {
  FIVE_LEVEL_BANDS,
  OUTCOME_LABELS,
} from "../domain/types";

import type {
  ConfidenceBand,
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


export type MatchPredictionRecord =
  Readonly<{
    fixture_id:
      FixtureId;

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
  }>;


const outcomeLabels =
  new Set<string>(
    OUTCOME_LABELS,
  );


const fiveLevelBands =
  new Set<string>(
    FIVE_LEVEL_BANDS,
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
    `Invalid numeric match field: ${field}`,
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
      `Invalid probability match field: ${field}`,
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


function looksLikePredictionRecord(
  value: JsonObject,
): boolean {

  return (
    "fixture_id"
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
  );
}


function parsePredictionRecord(
  value: JsonObject,
): MatchPredictionRecord {

  const fixtureId =
    value.fixture_id;


  if (
    !isFixtureId(
      fixtureId,
    )
  ) {
    throw new TypeError(
      "Invalid match prediction fixture_id.",
    );
  }


  return {
    fixture_id:
      fixtureId,

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
  };
}


function collectPredictionRecord(
  value: JsonValue,
  expectedFixtureId: string,
  output: MatchPredictionRecord[],
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

      collectPredictionRecord(
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
    looksLikePredictionRecord(
      value,
    )
  ) {

    const record =
      parsePredictionRecord(
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

    collectPredictionRecord(
      child,
      expectedFixtureId,
      output,
    );
  }
}


export function extractMatchPredictionRecord(
  data: JsonValue,
  expectedFixtureId: string,
): MatchPredictionRecord {

  const records:
    MatchPredictionRecord[] =
      [];


  collectPredictionRecord(
    data,
    expectedFixtureId,
    records,
  );


  if (
    records.length === 0
  ) {
    throw new Error(
      "Requested fixture prediction is absent from the READY match-intelligence response.",
    );
  }


  if (
    records.length !== 1
  ) {
    throw new Error(
      "Requested fixture prediction appears more than once.",
    );
  }


  return records[0];
}

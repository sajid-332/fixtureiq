/*
 * FixtureIQ Stage 10.2.6
 *
 * Runtime validation for backend JSON responses.
 *
 * This module intentionally uses native TypeScript / JavaScript
 * runtime facilities instead of introducing a new dependency
 * that would mutate the already-locked package dependency chain.
 *
 * Stage 7 = prediction authority
 * Stage 8 = context authority
 * Stage 9 = intelligence authority
 * Stage 10 = presentation only
 */


export type JsonPrimitive =
  | string
  | number
  | boolean
  | null;


export type JsonValue =
  | JsonPrimitive
  | JsonValue[]
  | {
      readonly [key: string]:
        JsonValue;
    };


export type JsonObject =
  Readonly<
    Record<
      string,
      JsonValue
    >
  >;


export const OUTCOME_LABELS =
  new Set(
    [
      "Home Win",
      "Draw",
      "Away Win",
    ] as const
  );


export const FIVE_LEVEL_BANDS =
  new Set(
    [
      "VERY_LOW",
      "LOW",
      "MODERATE",
      "HIGH",
      "VERY_HIGH",
    ] as const
  );


export const CONTEXT_ALIGNMENTS =
  new Set(
    [
      "SUPPORTIVE",
      "MIXED",
      "CONTRADICTORY",
      "NEUTRAL",
    ] as const
  );


export class ApiValidationError
  extends TypeError {

  constructor(
    message: string
  ) {
    super(message);

    this.name =
      "ApiValidationError";
  }
}


function fail(
  path: string,
  message: string
): never {
  throw new ApiValidationError(
    `${path}: ${message}`
  );
}


function isObject(
  value: unknown
): value is Record<
  string,
  unknown
> {
  return (
    typeof value === "object"
    &&
    value !== null
    &&
    !Array.isArray(value)
  );
}


function assertFiniteNumber(
  value: unknown,
  path: string
): asserts value is number {
  if (
    typeof value !== "number"
    ||
    !Number.isFinite(value)
  ) {
    fail(
      path,
      "expected a finite number"
    );
  }
}


function assertProbability(
  value: unknown,
  path: string
): asserts value is number {
  assertFiniteNumber(
    value,
    path
  );

  if (
    value < 0
    ||
    value > 1
  ) {
    fail(
      path,
      "expected probability in [0, 1]"
    );
  }
}


function assertString(
  value: unknown,
  path: string
): asserts value is string {
  if (
    typeof value !== "string"
  ) {
    fail(
      path,
      "expected a string"
    );
  }
}


function assertFixtureId(
  value: unknown,
  path: string
): asserts value is string | number {
  if (
    typeof value === "string"
  ) {
    return;
  }

  if (
    typeof value === "number"
    &&
    Number.isFinite(value)
  ) {
    return;
  }

  fail(
    path,
    "expected fixture ID as string or finite number"
  );
}


function assertIntegerRange(
  value: unknown,
  minimum: number,
  maximum: number,
  path: string
): asserts value is number {
  assertFiniteNumber(
    value,
    path
  );

  if (
    !Number.isInteger(value)
    ||
    value < minimum
    ||
    value > maximum
  ) {
    fail(
      path,
      (
        "expected integer between "
        +
        `${minimum} and ${maximum}`
      )
    );
  }
}


function assertSetMember(
  value: unknown,
  allowed:
    ReadonlySet<string>,
  path: string
): asserts value is string {
  assertString(
    value,
    path
  );

  if (
    !allowed.has(value)
  ) {
    fail(
      path,
      `unexpected value: ${value}`
    );
  }
}


export function assertJsonValue(
  value: unknown,
  path = "$"
): asserts value is JsonValue {

  if (
    value === null
    ||
    typeof value === "string"
    ||
    typeof value === "boolean"
  ) {
    return;
  }

  if (
    typeof value === "number"
  ) {
    if (
      !Number.isFinite(value)
    ) {
      fail(
        path,
        "JSON number must be finite"
      );
    }

    return;
  }

  if (
    Array.isArray(value)
  ) {
    value.forEach(
      (
        item,
        index
      ) => {
        assertJsonValue(
          item,
          `${path}[${index}]`
        );
      }
    );

    return;
  }

  if (
    isObject(value)
  ) {
    for (
      const [
        key,
        item,
      ]
      of
      Object.entries(value)
    ) {
      assertJsonValue(
        item,
        `${path}.${key}`
      );
    }

    return;
  }

  fail(
    path,
    "expected valid JSON value"
  );
}


function visitObjects(
  value: JsonValue,
  visitor: (
    value: JsonObject,
    path: string
  ) => void,
  path = "$"
): void {

  if (
    Array.isArray(value)
  ) {
    value.forEach(
      (
        item,
        index
      ) => {
        visitObjects(
          item,
          visitor,
          `${path}[${index}]`
        );
      }
    );

    return;
  }

  if (
    typeof value !== "object"
    ||
    value === null
  ) {
    return;
  }

  visitor(
    value,
    path
  );

  for (
    const [
      key,
      item,
    ]
    of
    Object.entries(value)
  ) {
    visitObjects(
      item,
      visitor,
      `${path}.${key}`
    );
  }
}


function validateStatusField(
  value: JsonObject,
  path: string
): void {
  if (
    "status"
    in
    value
  ) {
    assertString(
      value.status,
      `${path}.status`
    );
  }
}


const PRODUCTION_MARKERS =
  new Set(
    [
      "prob_home_win",
      "prob_draw",
      "prob_away_win",
      "predicted_label",
    ]
  );


function looksLikeProductionPrediction(
  value: JsonObject
): boolean {
  return Array.from(
    PRODUCTION_MARKERS
  ).some(
    (key) =>
      key
      in
      value
  );
}


function validateProductionPrediction(
  value: JsonObject,
  path: string
): void {

  assertFixtureId(
    value.fixture_id,
    `${path}.fixture_id`
  );

  assertString(
    value.home_team_name,
    `${path}.home_team_name`
  );

  assertString(
    value.away_team_name,
    `${path}.away_team_name`
  );

  assertProbability(
    value.prob_home_win,
    `${path}.prob_home_win`
  );

  assertProbability(
    value.prob_draw,
    `${path}.prob_draw`
  );

  assertProbability(
    value.prob_away_win,
    `${path}.prob_away_win`
  );

  assertSetMember(
    value.predicted_label,
    OUTCOME_LABELS,
    `${path}.predicted_label`
  );

  assertProbability(
    value.confidence,
    `${path}.confidence`
  );
}


const INTELLIGENCE_MARKERS =
  new Set(
    [
      "stage9_top_probability",
      "stage9_probability_margin",
      "stage9_context_alignment",
      "stage9_context_support_score",
    ]
  );


function looksLikeIntelligenceRecord(
  value: JsonObject
): boolean {
  return Array.from(
    INTELLIGENCE_MARKERS
  ).some(
    (key) =>
      key
      in
      value
  );
}


function validateIntelligenceRecord(
  value: JsonObject,
  path: string
): void {

  assertFixtureId(
    value.fixture_id,
    `${path}.fixture_id`
  );

  assertString(
    value.home_team_name,
    `${path}.home_team_name`
  );

  assertString(
    value.away_team_name,
    `${path}.away_team_name`
  );


  assertProbability(
    value.stage7_prob_home_win,
    `${path}.stage7_prob_home_win`
  );

  assertProbability(
    value.stage7_prob_draw,
    `${path}.stage7_prob_draw`
  );

  assertProbability(
    value.stage7_prob_away_win,
    `${path}.stage7_prob_away_win`
  );

  assertSetMember(
    value.stage7_predicted_label,
    OUTCOME_LABELS,
    `${path}.stage7_predicted_label`
  );

  assertProbability(
    value.stage7_confidence,
    `${path}.stage7_confidence`
  );


  assertProbability(
    value.stage9_top_probability,
    `${path}.stage9_top_probability`
  );

  assertProbability(
    value.stage9_probability_margin,
    `${path}.stage9_probability_margin`
  );

  assertSetMember(
    value.stage9_confidence_band,
    FIVE_LEVEL_BANDS,
    `${path}.stage9_confidence_band`
  );

  assertSetMember(
    value.stage9_uncertainty_band,
    FIVE_LEVEL_BANDS,
    `${path}.stage9_uncertainty_band`
  );

  assertIntegerRange(
    value.stage9_context_support_score,
    -5,
    5,
    `${path}.stage9_context_support_score`
  );

  assertSetMember(
    value.stage9_context_alignment,
    CONTEXT_ALIGNMENTS,
    `${path}.stage9_context_alignment`
  );

  assertString(
    value.stage9_explanation_headline,
    `${path}.stage9_explanation_headline`
  );

  assertString(
    value.stage9_explanation_summary,
    `${path}.stage9_explanation_summary`
  );
}


function validateContextIdentity(
  value: JsonObject,
  path: string
): void {

  if (
    "fixture_id"
    in
    value
  ) {
    assertFixtureId(
      value.fixture_id,
      `${path}.fixture_id`
    );

    if (
      "home_team_name"
      in
      value
      ||
      "away_team_name"
      in
      value
    ) {
      assertString(
        value.home_team_name,
        `${path}.home_team_name`
      );

      assertString(
        value.away_team_name,
        `${path}.away_team_name`
      );
    }
  }

  if (
    "team_name"
    in
    value
  ) {
    assertString(
      value.team_name,
      `${path}.team_name`
    );
  }
}


function validateBasePayload(
  input: unknown
): JsonValue {

  assertJsonValue(input);

  visitObjects(
    input,
    (
      value,
      path
    ) => {
      validateStatusField(
        value,
        path
      );
    }
  );

  return input;
}


export function validateProductionApiPayload(
  input: unknown
): JsonValue {

  const value =
    validateBasePayload(
      input
    );

  visitObjects(
    value,
    (
      candidate,
      path
    ) => {
      if (
        looksLikeProductionPrediction(
          candidate
        )
      ) {
        validateProductionPrediction(
          candidate,
          path
        );
      }
    }
  );

  return value;
}


export function validateIntelligenceApiPayload(
  input: unknown
): JsonValue {

  const value =
    validateBasePayload(
      input
    );

  visitObjects(
    value,
    (
      candidate,
      path
    ) => {
      if (
        looksLikeIntelligenceRecord(
          candidate
        )
      ) {
        validateIntelligenceRecord(
          candidate,
          path
        );
      }
    }
  );

  return value;
}


export function validateContextApiPayload(
  input: unknown
): JsonValue {

  const value =
    validateBasePayload(
      input
    );

  visitObjects(
    value,
    (
      candidate,
      path
    ) => {
      validateContextIdentity(
        candidate,
        path
      );
    }
  );

  return value;
}

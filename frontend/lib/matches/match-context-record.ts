import "server-only";

import type {
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


export type MatchContextRecord =
  Readonly<{
    fixture_id:
      FixtureId;

    home_team_position:
      number;

    away_team_position:
      number;

    home_team_points:
      number;

    away_team_points:
      number;

    home_team_goal_difference:
      number;

    away_team_goal_difference:
      number;

    home_team_form_matches_available:
      number;

    away_team_form_matches_available:
      number;

    home_team_recent_results:
      string;

    away_team_recent_results:
      string;
  }>;


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
    `Invalid integer match context field: ${field}`,
  );
}


function recentResults(
  value: JsonValue | undefined,
  field: string,
): string {

  if (
    typeof value !== "string"
  ) {
    throw new TypeError(
      `Invalid recent-results field: ${field}`,
    );
  }


  if (
    !/^[WDL]*$/.test(
      value,
    )
  ) {
    throw new TypeError(
      `Unexpected recent-results value: ${field}`,
    );
  }


  return value;
}


function looksLikeContextRecord(
  value: JsonObject,
): boolean {

  return (
    "fixture_id"
    in value
    &&
    "home_team_position"
    in value
    &&
    "away_team_position"
    in value
    &&
    "home_team_points"
    in value
    &&
    "away_team_points"
    in value
    &&
    "home_team_goal_difference"
    in value
    &&
    "away_team_goal_difference"
    in value
    &&
    "home_team_form_matches_available"
    in value
    &&
    "away_team_form_matches_available"
    in value
    &&
    "home_team_recent_results"
    in value
    &&
    "away_team_recent_results"
    in value
  );
}


function parseContextRecord(
  value: JsonObject,
): MatchContextRecord {

  const fixtureId =
    value.fixture_id;


  if (
    !isFixtureId(
      fixtureId,
    )
  ) {
    throw new TypeError(
      "Invalid match context fixture_id.",
    );
  }


  const homePosition =
    transportInteger(
      value.home_team_position,
      "home_team_position",
    );

  const awayPosition =
    transportInteger(
      value.away_team_position,
      "away_team_position",
    );


  if (
    homePosition < 1
    ||
    awayPosition < 1
  ) {
    throw new RangeError(
      "League positions must be positive integers.",
    );
  }


  const homePoints =
    transportInteger(
      value.home_team_points,
      "home_team_points",
    );

  const awayPoints =
    transportInteger(
      value.away_team_points,
      "away_team_points",
    );


  if (
    homePoints < 0
    ||
    awayPoints < 0
  ) {
    throw new RangeError(
      "League points cannot be negative.",
    );
  }


  const homeMatchesAvailable =
    transportInteger(
      value.home_team_form_matches_available,
      "home_team_form_matches_available",
    );

  const awayMatchesAvailable =
    transportInteger(
      value.away_team_form_matches_available,
      "away_team_form_matches_available",
    );


  if (
    homeMatchesAvailable < 0
    ||
    awayMatchesAvailable < 0
  ) {
    throw new RangeError(
      "Form-match availability cannot be negative.",
    );
  }


  return {
    fixture_id:
      fixtureId,

    home_team_position:
      homePosition,

    away_team_position:
      awayPosition,

    home_team_points:
      homePoints,

    away_team_points:
      awayPoints,

    home_team_goal_difference:
      transportInteger(
        value.home_team_goal_difference,
        "home_team_goal_difference",
      ),

    away_team_goal_difference:
      transportInteger(
        value.away_team_goal_difference,
        "away_team_goal_difference",
      ),

    home_team_form_matches_available:
      homeMatchesAvailable,

    away_team_form_matches_available:
      awayMatchesAvailable,

    home_team_recent_results:
      recentResults(
        value.home_team_recent_results,
        "home_team_recent_results",
      ),

    away_team_recent_results:
      recentResults(
        value.away_team_recent_results,
        "away_team_recent_results",
      ),
  };
}


function collectContextRecord(
  value: JsonValue,
  expectedFixtureId: string,
  output: MatchContextRecord[],
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

      collectContextRecord(
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
    looksLikeContextRecord(
      value,
    )
  ) {

    const record =
      parseContextRecord(
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

    collectContextRecord(
      child,
      expectedFixtureId,
      output,
    );
  }
}


export function extractMatchContextRecord(
  data: JsonValue,
  expectedFixtureId: string,
): MatchContextRecord {

  const records:
    MatchContextRecord[] =
      [];


  collectContextRecord(
    data,
    expectedFixtureId,
    records,
  );


  if (
    records.length === 0
  ) {
    throw new Error(
      "Requested fixture context is absent from the READY match-intelligence response.",
    );
  }


  if (
    records.length !== 1
  ) {
    throw new Error(
      "Requested fixture context appears more than once.",
    );
  }


  return records[0];
}

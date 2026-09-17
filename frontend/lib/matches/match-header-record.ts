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


export type MatchFixtureHeaderRecord =
  Readonly<{
    fixture_id:
      FixtureId;

    home_team_name:
      string;

    away_team_name:
      string;

    date:
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
      `Invalid match header field: ${field}`,
    );
  }

  return value;
}


function looksLikeMatchRecord(
  value: JsonObject,
): boolean {

  return (
    "fixture_id"
    in value
    &&
    "home_team_name"
    in value
    &&
    "away_team_name"
    in value
    &&
    "date"
    in value
  );
}


function collectExactFixture(
  value: JsonValue,
  expectedFixtureId: string,
  output: MatchFixtureHeaderRecord[],
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

      collectExactFixture(
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
    looksLikeMatchRecord(
      value,
    )
  ) {

    const fixtureId =
      value.fixture_id;


    if (
      !isFixtureId(
        fixtureId,
      )
    ) {
      throw new TypeError(
        "Invalid match header fixture_id.",
      );
    }


    if (
      String(
        fixtureId,
      )
      !==
      expectedFixtureId
    ) {
      return;
    }


    const date =
      requireString(
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
        "Invalid match header date.",
      );
    }


    output.push(
      {
        fixture_id:
          fixtureId,

        home_team_name:
          requireString(
            value.home_team_name,
            "home_team_name",
          ),

        away_team_name:
          requireString(
            value.away_team_name,
            "away_team_name",
          ),

        date,
      },
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

    collectExactFixture(
      child,
      expectedFixtureId,
      output,
    );
  }
}


export function extractMatchFixtureHeader(
  data: JsonValue,
  expectedFixtureId: string,
): MatchFixtureHeaderRecord {

  const records:
    MatchFixtureHeaderRecord[] =
      [];


  collectExactFixture(
    data,
    expectedFixtureId,
    records,
  );


  if (
    records.length === 0
  ) {
    throw new Error(
      "Requested fixture is absent from the READY match-intelligence response.",
    );
  }


  if (
    records.length !== 1
  ) {
    throw new Error(
      "Requested fixture appears more than once in the match-intelligence response.",
    );
  }


  return records[0];
}

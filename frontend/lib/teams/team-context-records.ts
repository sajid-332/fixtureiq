import "server-only";

import type {
  JsonValue,
} from "../api/validation";


type JsonObject =
  Readonly<{
    [key: string]:
      JsonValue;
  }>;


export type TeamStandingsRecord =
  Readonly<{
    team_name:
      string;

    position:
      number;

    played:
      number;

    won:
      number;

    drawn:
      number;

    lost:
      number;

    goals_for:
      number;

    goals_against:
      number;

    goal_difference:
      number;

    points:
      number;
  }>;


export type TeamFormRecord =
  Readonly<{
    team_name:
      string;

    form_matches_available:
      number;

    recent_results:
      string;

    recent_points:
      number;

    recent_wins:
      number;

    recent_draws:
      number;

    recent_losses:
      number;

    recent_goals_for:
      number;

    recent_goals_against:
      number;

    recent_goal_difference:
      number;

    home_form_matches_available:
      number;

    home_recent_results:
      string;

    home_recent_points:
      number;

    home_recent_wins:
      number;

    home_recent_draws:
      number;

    home_recent_losses:
      number;

    home_recent_goals_for:
      number;

    home_recent_goals_against:
      number;

    home_recent_goal_difference:
      number;

    away_form_matches_available:
      number;

    away_recent_results:
      string;

    away_recent_points:
      number;

    away_recent_wins:
      number;

    away_recent_draws:
      number;

    away_recent_losses:
      number;

    away_recent_goals_for:
      number;

    away_recent_goals_against:
      number;

    away_recent_goal_difference:
      number;
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
      `Invalid team-context string field: ${field}`,
    );
  }


  return value;
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
    `Invalid team-context integer field: ${field}`,
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
      `Negative team-context field: ${field}`,
    );
  }


  return parsed;
}


function recentResults(
  value: JsonValue | undefined,
  field: string,
): string {

  if (
    typeof value !== "string"
    ||
    !/^[WDL]*$/.test(
      value,
    )
  ) {
    throw new TypeError(
      `Invalid recent-results field: ${field}`,
    );
  }


  return value;
}


function looksLikeStandingsRecord(
  value: JsonObject,
): boolean {

  return (
    "team_name" in value
    &&
    "position" in value
    &&
    "played" in value
    &&
    "won" in value
    &&
    "drawn" in value
    &&
    "lost" in value
    &&
    "goals_for" in value
    &&
    "goals_against" in value
    &&
    "goal_difference" in value
    &&
    "points" in value
  );
}


function looksLikeFormRecord(
  value: JsonObject,
): boolean {

  return (
    "team_name" in value
    &&
    "form_matches_available" in value
    &&
    "recent_results" in value
    &&
    "recent_points" in value
    &&
    "recent_wins" in value
    &&
    "recent_draws" in value
    &&
    "recent_losses" in value
    &&
    "recent_goals_for" in value
    &&
    "recent_goals_against" in value
    &&
    "recent_goal_difference" in value
    &&
    "home_form_matches_available" in value
    &&
    "home_recent_results" in value
    &&
    "home_recent_points" in value
    &&
    "home_recent_wins" in value
    &&
    "home_recent_draws" in value
    &&
    "home_recent_losses" in value
    &&
    "home_recent_goals_for" in value
    &&
    "home_recent_goals_against" in value
    &&
    "home_recent_goal_difference" in value
    &&
    "away_form_matches_available" in value
    &&
    "away_recent_results" in value
    &&
    "away_recent_points" in value
    &&
    "away_recent_wins" in value
    &&
    "away_recent_draws" in value
    &&
    "away_recent_losses" in value
    &&
    "away_recent_goals_for" in value
    &&
    "away_recent_goals_against" in value
    &&
    "away_recent_goal_difference" in value
  );
}


function parseStandingsRecord(
  value: JsonObject,
): TeamStandingsRecord {

  const position =
    transportInteger(
      value.position,
      "position",
    );


  if (
    position < 1
  ) {
    throw new RangeError(
      "Team position must be positive.",
    );
  }


  return {
    team_name:
      requiredString(
        value.team_name,
        "team_name",
      ),

    position,

    played:
      nonNegativeInteger(
        value.played,
        "played",
      ),

    won:
      nonNegativeInteger(
        value.won,
        "won",
      ),

    drawn:
      nonNegativeInteger(
        value.drawn,
        "drawn",
      ),

    lost:
      nonNegativeInteger(
        value.lost,
        "lost",
      ),

    goals_for:
      nonNegativeInteger(
        value.goals_for,
        "goals_for",
      ),

    goals_against:
      nonNegativeInteger(
        value.goals_against,
        "goals_against",
      ),

    goal_difference:
      transportInteger(
        value.goal_difference,
        "goal_difference",
      ),

    points:
      nonNegativeInteger(
        value.points,
        "points",
      ),
  };
}


function parseFormRecord(
  value: JsonObject,
): TeamFormRecord {

  return {
    team_name:
      requiredString(
        value.team_name,
        "team_name",
      ),

    form_matches_available:
      nonNegativeInteger(
        value.form_matches_available,
        "form_matches_available",
      ),

    recent_results:
      recentResults(
        value.recent_results,
        "recent_results",
      ),

    recent_points:
      nonNegativeInteger(
        value.recent_points,
        "recent_points",
      ),

    recent_wins:
      nonNegativeInteger(
        value.recent_wins,
        "recent_wins",
      ),

    recent_draws:
      nonNegativeInteger(
        value.recent_draws,
        "recent_draws",
      ),

    recent_losses:
      nonNegativeInteger(
        value.recent_losses,
        "recent_losses",
      ),

    recent_goals_for:
      nonNegativeInteger(
        value.recent_goals_for,
        "recent_goals_for",
      ),

    recent_goals_against:
      nonNegativeInteger(
        value.recent_goals_against,
        "recent_goals_against",
      ),

    recent_goal_difference:
      transportInteger(
        value.recent_goal_difference,
        "recent_goal_difference",
      ),

    home_form_matches_available:
      nonNegativeInteger(
        value.home_form_matches_available,
        "home_form_matches_available",
      ),

    home_recent_results:
      recentResults(
        value.home_recent_results,
        "home_recent_results",
      ),

    home_recent_points:
      nonNegativeInteger(
        value.home_recent_points,
        "home_recent_points",
      ),

    home_recent_wins:
      nonNegativeInteger(
        value.home_recent_wins,
        "home_recent_wins",
      ),

    home_recent_draws:
      nonNegativeInteger(
        value.home_recent_draws,
        "home_recent_draws",
      ),

    home_recent_losses:
      nonNegativeInteger(
        value.home_recent_losses,
        "home_recent_losses",
      ),

    home_recent_goals_for:
      nonNegativeInteger(
        value.home_recent_goals_for,
        "home_recent_goals_for",
      ),

    home_recent_goals_against:
      nonNegativeInteger(
        value.home_recent_goals_against,
        "home_recent_goals_against",
      ),

    home_recent_goal_difference:
      transportInteger(
        value.home_recent_goal_difference,
        "home_recent_goal_difference",
      ),

    away_form_matches_available:
      nonNegativeInteger(
        value.away_form_matches_available,
        "away_form_matches_available",
      ),

    away_recent_results:
      recentResults(
        value.away_recent_results,
        "away_recent_results",
      ),

    away_recent_points:
      nonNegativeInteger(
        value.away_recent_points,
        "away_recent_points",
      ),

    away_recent_wins:
      nonNegativeInteger(
        value.away_recent_wins,
        "away_recent_wins",
      ),

    away_recent_draws:
      nonNegativeInteger(
        value.away_recent_draws,
        "away_recent_draws",
      ),

    away_recent_losses:
      nonNegativeInteger(
        value.away_recent_losses,
        "away_recent_losses",
      ),

    away_recent_goals_for:
      nonNegativeInteger(
        value.away_recent_goals_for,
        "away_recent_goals_for",
      ),

    away_recent_goals_against:
      nonNegativeInteger(
        value.away_recent_goals_against,
        "away_recent_goals_against",
      ),

    away_recent_goal_difference:
      transportInteger(
        value.away_recent_goal_difference,
        "away_recent_goal_difference",
      ),
  };
}


function collectStandings(
  value: JsonValue,
  requestedTeamName: string,
  output: TeamStandingsRecord[],
): void {

  if (
    Array.isArray(
      value,
    )
  ) {

    for (
      const child
      of
      value
    ) {

      collectStandings(
        child,
        requestedTeamName,
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
    looksLikeStandingsRecord(
      value,
    )
  ) {

    const record =
      parseStandingsRecord(
        value,
      );


    if (
      record.team_name
      ===
      requestedTeamName
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

    collectStandings(
      child,
      requestedTeamName,
      output,
    );
  }
}


function collectForm(
  value: JsonValue,
  requestedTeamName: string,
  output: TeamFormRecord[],
): void {

  if (
    Array.isArray(
      value,
    )
  ) {

    for (
      const child
      of
      value
    ) {

      collectForm(
        child,
        requestedTeamName,
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
    looksLikeFormRecord(
      value,
    )
  ) {

    const record =
      parseFormRecord(
        value,
      );


    if (
      record.team_name
      ===
      requestedTeamName
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

    collectForm(
      child,
      requestedTeamName,
      output,
    );
  }
}


export function extractTeamStandingsRecord(
  data: JsonValue,
  requestedTeamName: string,
): TeamStandingsRecord {

  const records:
    TeamStandingsRecord[] =
      [];


  collectStandings(
    data,
    requestedTeamName,
    records,
  );


  if (
    records.length !== 1
  ) {
    throw new Error(
      "Expected exactly one Stage 8 standings record for the requested team.",
    );
  }


  return records[0];
}


export function extractTeamFormRecord(
  data: JsonValue,
  requestedTeamName: string,
): TeamFormRecord {

  const records:
    TeamFormRecord[] =
      [];


  collectForm(
    data,
    requestedTeamName,
    records,
  );


  if (
    records.length !== 1
  ) {
    throw new Error(
      "Expected exactly one Stage 8 form record for the requested team.",
    );
  }


  return records[0];
}

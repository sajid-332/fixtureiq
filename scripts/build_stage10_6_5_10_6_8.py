from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"

DOCS = ROOT / "docs" / "stage10"

FRONTEND_DATA = (
    ROOT
    / "data"
    / "processed"
    / "frontend"
)


PREVIOUS_FILE = (
    FRONTEND_DATA
    / "stage10_6_1_10_6_4_verification.json"
)

PREVIOUS_CARD_CONTRACT_FILE = (
    DOCS
    / "frontend_team_prediction_cards_contract.json"
)


STANDINGS_CONTRACT_FILE = (
    DOCS
    / "frontend_team_standings_contract.json"
)

RECENT_FORM_CONTRACT_FILE = (
    DOCS
    / "frontend_team_recent_form_contract.json"
)

VENUE_FORM_CONTRACT_FILE = (
    DOCS
    / "frontend_team_home_away_form_contract.json"
)

FIXTURE_LINKS_CONTRACT_FILE = (
    DOCS
    / "frontend_team_fixture_links_contract.json"
)


TEAM_ROUTE_FILE = (
    FRONTEND
    / "app"
    / "teams"
    / "[teamName]"
    / "page.tsx"
)

TEAM_LOADER_FILE = (
    FRONTEND
    / "lib"
    / "teams"
    / "load-team-intelligence.ts"
)

TEAM_CONTEXT_LOADER_FILE = (
    FRONTEND
    / "lib"
    / "teams"
    / "load-team-context.ts"
)

TEAM_RECORDS_FILE = (
    FRONTEND
    / "lib"
    / "teams"
    / "team-records.ts"
)

TEAM_CONTEXT_RECORDS_FILE = (
    FRONTEND
    / "lib"
    / "teams"
    / "team-context-records.ts"
)


TEAM_HEADER_FILE = (
    FRONTEND
    / "components"
    / "teams"
    / "team-identity-header.tsx"
)

TEAM_UPCOMING_FILE = (
    FRONTEND
    / "components"
    / "teams"
    / "team-upcoming-matches.tsx"
)

TEAM_PREDICTION_CARD_FILE = (
    FRONTEND
    / "components"
    / "teams"
    / "team-prediction-card.tsx"
)

TEAM_STANDINGS_FILE = (
    FRONTEND
    / "components"
    / "teams"
    / "team-standings.tsx"
)

TEAM_RECENT_FORM_FILE = (
    FRONTEND
    / "components"
    / "teams"
    / "team-recent-form.tsx"
)

TEAM_VENUE_FORM_FILE = (
    FRONTEND
    / "components"
    / "teams"
    / "team-home-away-form.tsx"
)


MAPPED_API_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "mapped.ts"
)

RESULT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "result.ts"
)

DOMAIN_TYPES_FILE = (
    FRONTEND
    / "lib"
    / "domain"
    / "types.ts"
)


TEAM_CONTEXT_LOADER_SOURCE = '''import "server-only";

import {
  getContextFormByTeamNameResult,
  getContextStandingsByTeamNameResult,
} from "../api/mapped";


export function loadTeamContext(
  teamName: string,
) {

  return Promise.all(
    [
      getContextStandingsByTeamNameResult(
        teamName,
      ),

      getContextFormByTeamNameResult(
        teamName,
      ),
    ] as const,
  );
}
'''


TEAM_CONTEXT_RECORDS_SOURCE = '''import "server-only";

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
'''


TEAM_STANDINGS_SOURCE = '''const signedIntegerFormatter =
  new Intl.NumberFormat(
    "en-GB",
    {
      maximumFractionDigits: 0,
      signDisplay: "exceptZero",
    },
  );


type TeamStandingsProps =
  Readonly<{
    position:
      number;

    points:
      number;

    played:
      number;

    won:
      number;

    drawn:
      number;

    lost:
      number;

    goalsFor:
      number;

    goalsAgainst:
      number;

    goalDifference:
      number;
  }>;


export function TeamStandings({
  position,
  points,
  played,
  won,
  drawn,
  lost,
  goalsFor,
  goalsAgainst,
  goalDifference,
}: TeamStandingsProps) {

  return (
    <section
      aria-labelledby="team-standings-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="team-standings"
    >
      <h2
        id="team-standings-heading"
        className="
          text-lg font-bold
          text-slate-950
        "
      >
        League standing
      </h2>

      <dl
        className="
          mt-5 grid
          grid-cols-2 gap-4
          sm:grid-cols-3
        "
      >
        <div>
          <dt className="text-xs text-slate-500">
            Position
          </dt>

          <dd
            className="mt-1 text-xl font-bold text-slate-950"
            data-stage8-field="position"
          >
            #{position}
          </dd>
        </div>

        <div>
          <dt className="text-xs text-slate-500">
            Points
          </dt>

          <dd
            className="mt-1 text-xl font-bold text-slate-950"
            data-stage8-field="points"
          >
            {points}
          </dd>
        </div>

        <div>
          <dt className="text-xs text-slate-500">
            Played
          </dt>

          <dd
            className="mt-1 font-semibold text-slate-950"
            data-stage8-field="played"
          >
            {played}
          </dd>
        </div>

        <div>
          <dt className="text-xs text-slate-500">
            W-D-L
          </dt>

          <dd className="mt-1 font-semibold text-slate-950">
            <span data-stage8-field="won">
              {won}
            </span>
            {" - "}
            <span data-stage8-field="drawn">
              {drawn}
            </span>
            {" - "}
            <span data-stage8-field="lost">
              {lost}
            </span>
          </dd>
        </div>

        <div>
          <dt className="text-xs text-slate-500">
            Goals
          </dt>

          <dd className="mt-1 font-semibold text-slate-950">
            <span data-stage8-field="goals_for">
              {goalsFor}
            </span>
            {" - "}
            <span data-stage8-field="goals_against">
              {goalsAgainst}
            </span>
          </dd>
        </div>

        <div>
          <dt className="text-xs text-slate-500">
            Goal difference
          </dt>

          <dd
            className="mt-1 font-semibold text-slate-950"
            data-stage8-field="goal_difference"
          >
            {signedIntegerFormatter.format(
              goalDifference,
            )}
          </dd>
        </div>
      </dl>
    </section>
  );
}
'''


TEAM_RECENT_FORM_SOURCE = '''const signedIntegerFormatter =
  new Intl.NumberFormat(
    "en-GB",
    {
      maximumFractionDigits: 0,
      signDisplay: "exceptZero",
    },
  );


type TeamRecentFormProps =
  Readonly<{
    matchesAvailable:
      number;

    results:
      string;

    points:
      number;

    wins:
      number;

    draws:
      number;

    losses:
      number;

    goalsFor:
      number;

    goalsAgainst:
      number;

    goalDifference:
      number;
  }>;


export function TeamRecentForm({
  matchesAvailable,
  results,
  points,
  wins,
  draws,
  losses,
  goalsFor,
  goalsAgainst,
  goalDifference,
}: TeamRecentFormProps) {

  return (
    <section
      aria-labelledby="team-recent-form-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="team-recent-form"
    >
      <h2
        id="team-recent-form-heading"
        className="
          text-lg font-bold
          text-slate-950
        "
      >
        Recent form
      </h2>

      <p
        className="
          mt-4 font-mono
          text-lg font-semibold
          tracking-widest
          text-slate-950
        "
        data-stage8-field="recent_results"
      >
        {results || "No results"}
      </p>

      <p
        className="
          mt-1 text-xs
          text-slate-500
        "
        data-stage8-field="form_matches_available"
      >
        {matchesAvailable} matches available
      </p>

      <dl
        className="
          mt-5 grid
          grid-cols-2 gap-4
          sm:grid-cols-3
        "
      >
        <div>
          <dt className="text-xs text-slate-500">
            Points
          </dt>

          <dd
            className="mt-1 font-semibold text-slate-950"
            data-stage8-field="recent_points"
          >
            {points}
          </dd>
        </div>

        <div>
          <dt className="text-xs text-slate-500">
            W-D-L
          </dt>

          <dd className="mt-1 font-semibold text-slate-950">
            <span data-stage8-field="recent_wins">
              {wins}
            </span>
            {" - "}
            <span data-stage8-field="recent_draws">
              {draws}
            </span>
            {" - "}
            <span data-stage8-field="recent_losses">
              {losses}
            </span>
          </dd>
        </div>

        <div>
          <dt className="text-xs text-slate-500">
            Goals
          </dt>

          <dd className="mt-1 font-semibold text-slate-950">
            <span data-stage8-field="recent_goals_for">
              {goalsFor}
            </span>
            {" - "}
            <span data-stage8-field="recent_goals_against">
              {goalsAgainst}
            </span>
          </dd>
        </div>

        <div>
          <dt className="text-xs text-slate-500">
            Goal difference
          </dt>

          <dd
            className="mt-1 font-semibold text-slate-950"
            data-stage8-field="recent_goal_difference"
          >
            {signedIntegerFormatter.format(
              goalDifference,
            )}
          </dd>
        </div>
      </dl>

      <p
        className="
          mt-5 text-xs
          text-slate-500
        "
      >
        W = win, D = draw, L = loss.
      </p>
    </section>
  );
}
'''


TEAM_VENUE_FORM_SOURCE = '''const signedIntegerFormatter =
  new Intl.NumberFormat(
    "en-GB",
    {
      maximumFractionDigits: 0,
      signDisplay: "exceptZero",
    },
  );


type VenueFormBlockProps =
  Readonly<{
    label:
      string;

    matchesAvailable:
      number;

    results:
      string;

    points:
      number;

    wins:
      number;

    draws:
      number;

    losses:
      number;

    goalsFor:
      number;

    goalsAgainst:
      number;

    goalDifference:
      number;

    fieldPrefix:
      "home"
      |
      "away";
  }>;


function VenueFormBlock({
  label,
  matchesAvailable,
  results,
  points,
  wins,
  draws,
  losses,
  goalsFor,
  goalsAgainst,
  goalDifference,
  fieldPrefix,
}: VenueFormBlockProps) {

  return (
    <div>
      <h3
        className="
          text-sm font-bold
          text-slate-950
        "
      >
        {label}
      </h3>

      <p
        className="
          mt-3 font-mono
          font-semibold tracking-widest
          text-slate-950
        "
        data-stage8-venue-results={
          fieldPrefix
        }
      >
        {results || "No results"}
      </p>

      <p
        className="
          mt-1 text-xs
          text-slate-500
        "
        data-stage8-venue-matches={
          fieldPrefix
        }
      >
        {matchesAvailable} matches available
      </p>

      <dl
        className="
          mt-4 space-y-2
        "
      >
        <div className="flex justify-between gap-4">
          <dt className="text-sm text-slate-600">
            Points
          </dt>

          <dd
            className="font-semibold text-slate-950"
            data-stage8-venue-points={
              fieldPrefix
            }
          >
            {points}
          </dd>
        </div>

        <div className="flex justify-between gap-4">
          <dt className="text-sm text-slate-600">
            W-D-L
          </dt>

          <dd className="font-semibold text-slate-950">
            {wins} - {draws} - {losses}
          </dd>
        </div>

        <div className="flex justify-between gap-4">
          <dt className="text-sm text-slate-600">
            Goals
          </dt>

          <dd className="font-semibold text-slate-950">
            {goalsFor} - {goalsAgainst}
          </dd>
        </div>

        <div className="flex justify-between gap-4">
          <dt className="text-sm text-slate-600">
            Goal difference
          </dt>

          <dd className="font-semibold text-slate-950">
            {signedIntegerFormatter.format(
              goalDifference,
            )}
          </dd>
        </div>
      </dl>
    </div>
  );
}


type TeamHomeAwayFormProps =
  Readonly<{
    homeMatchesAvailable:
      number;

    homeResults:
      string;

    homePoints:
      number;

    homeWins:
      number;

    homeDraws:
      number;

    homeLosses:
      number;

    homeGoalsFor:
      number;

    homeGoalsAgainst:
      number;

    homeGoalDifference:
      number;

    awayMatchesAvailable:
      number;

    awayResults:
      string;

    awayPoints:
      number;

    awayWins:
      number;

    awayDraws:
      number;

    awayLosses:
      number;

    awayGoalsFor:
      number;

    awayGoalsAgainst:
      number;

    awayGoalDifference:
      number;
  }>;


export function TeamHomeAwayForm({
  homeMatchesAvailable,
  homeResults,
  homePoints,
  homeWins,
  homeDraws,
  homeLosses,
  homeGoalsFor,
  homeGoalsAgainst,
  homeGoalDifference,
  awayMatchesAvailable,
  awayResults,
  awayPoints,
  awayWins,
  awayDraws,
  awayLosses,
  awayGoalsFor,
  awayGoalsAgainst,
  awayGoalDifference,
}: TeamHomeAwayFormProps) {

  return (
    <section
      aria-labelledby="team-home-away-form-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="team-home-away-form"
    >
      <h2
        id="team-home-away-form-heading"
        className="
          text-lg font-bold
          text-slate-950
        "
      >
        Home / away form
      </h2>

      <div
        className="
          mt-5 grid gap-6
          md:grid-cols-2
        "
      >
        <VenueFormBlock
          label="Recent home form"
          matchesAvailable={
            homeMatchesAvailable
          }
          results={
            homeResults
          }
          points={
            homePoints
          }
          wins={
            homeWins
          }
          draws={
            homeDraws
          }
          losses={
            homeLosses
          }
          goalsFor={
            homeGoalsFor
          }
          goalsAgainst={
            homeGoalsAgainst
          }
          goalDifference={
            homeGoalDifference
          }
          fieldPrefix="home"
        />

        <VenueFormBlock
          label="Recent away form"
          matchesAvailable={
            awayMatchesAvailable
          }
          results={
            awayResults
          }
          points={
            awayPoints
          }
          wins={
            awayWins
          }
          draws={
            awayDraws
          }
          losses={
            awayLosses
          }
          goalsFor={
            awayGoalsFor
          }
          goalsAgainst={
            awayGoalsAgainst
          }
          goalDifference={
            awayGoalDifference
          }
          fieldPrefix="away"
        />
      </div>
    </section>
  );
}
'''


def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise RuntimeError(
            f"Missing artifact: {path}"
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


def optional_json(
    path: Path,
) -> dict | None:

    if not path.exists():

        return None

    return load_json(
        path
    )


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


def identity(
    path: Path,
) -> dict:

    return {
        "sha256":
            sha256_file(
                path
            )
    }


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
        json.dumps(
            payload,
            indent=2,
        )
        +
        "\n",
    )


def replace_once(
    source: str,
    old: str,
    new: str,
    label: str,
) -> str:

    count = source.count(
        old
    )

    if count != 1:

        raise RuntimeError(
            (
                f"{label}: expected exactly "
                f"one anchor, found {count}."
            )
        )

    return source.replace(
        old,
        new,
        1,
    )


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.6.5 - 10.6.8"
    )

    print(
        "STANDINGS + RECENT FORM + HOME/AWAY FORM + FIXTURE LINKS"
    )

    print("=" * 72)


    previous = load_json(
        PREVIOUS_FILE
    )

    previous_card_contract = load_json(
        PREVIOUS_CARD_CONTRACT_FILE
    )


    if (
        previous.get(
            "status"
        )
        !=
        "PASS"
    ):

        raise RuntimeError(
            "10.6.1-10.6.4 verification is not PASS."
        )


    for key in [
        "stage_10_6_1_complete",
        "stage_10_6_2_complete",
        "stage_10_6_3_complete",
        "stage_10_6_4_complete",
    ]:

        if (
            previous.get(
                key
            )
            is not True
        ):

            raise RuntimeError(
                f"Previous stage flag incomplete: {key}"
            )


    if (
        previous.get(
            "stage10_ready_for_10_6_5"
        )
        is not True
    ):

        raise RuntimeError(
            "10.6.4 did not authorize 10.6.5."
        )


    required = [
        TEAM_ROUTE_FILE,
        TEAM_LOADER_FILE,
        TEAM_RECORDS_FILE,
        TEAM_HEADER_FILE,
        TEAM_UPCOMING_FILE,
        TEAM_PREDICTION_CARD_FILE,
        MAPPED_API_FILE,
        RESULT_FILE,
        DOMAIN_TYPES_FILE,
    ]


    for path in required:

        if not path.exists():

            raise RuntimeError(
                f"Missing source: {path}"
            )


    expected_route_sha = (
        previous_card_contract.get(
            "route_page_after_10_6_4_sha256"
        )
    )

    expected_card_sha = (
        previous_card_contract.get(
            "component_sha256"
        )
    )


    final_contract = optional_json(
        FIXTURE_LINKS_CONTRACT_FILE
    )


    if (
        final_contract
        and
        TEAM_CONTEXT_LOADER_FILE.exists()
        and
        TEAM_CONTEXT_RECORDS_FILE.exists()
        and
        TEAM_STANDINGS_FILE.exists()
        and
        TEAM_RECENT_FORM_FILE.exists()
        and
        TEAM_VENUE_FORM_FILE.exists()
        and
        sha256_file(
            TEAM_ROUTE_FILE
        )
        ==
        final_contract.get(
            "route_page_after_10_6_8_sha256"
        )
        and
        sha256_file(
            TEAM_PREDICTION_CARD_FILE
        )
        ==
        final_contract.get(
            "prediction_card_after_10_6_8_sha256"
        )
    ):

        print()

        print(
            "10.6.5 - 10.6.8 already built."
        )

        print("=" * 72)

        print(
            "STAGE 10.6.5 STANDINGS: BUILT"
        )

        print(
            "STAGE 10.6.6 RECENT FORM: BUILT"
        )

        print(
            "STAGE 10.6.7 HOME / AWAY FORM: BUILT"
        )

        print(
            "STAGE 10.6.8 FIXTURE LINKS: BUILT"
        )

        print(
            "VERIFICATION STILL REQUIRED"
        )

        print("=" * 72)

        return


    if (
        sha256_file(
            TEAM_ROUTE_FILE
        )
        !=
        expected_route_sha
    ):

        raise RuntimeError(
            (
                "Team route no longer matches "
                "verified 10.6.4 output."
            )
        )


    if (
        sha256_file(
            TEAM_PREDICTION_CARD_FILE
        )
        !=
        expected_card_sha
    ):

        raise RuntimeError(
            (
                "Team prediction card no longer matches "
                "verified 10.6.4 output."
            )
        )


    mapped_source = (
        MAPPED_API_FILE.read_text(
            encoding="utf-8"
        )
    )


    for wrapper in [
        "getContextStandingsByTeamNameResult",
        "getContextFormByTeamNameResult",
    ]:

        if (
            wrapper
            not in
            mapped_source
        ):

            raise RuntimeError(
                f"Required mapped client missing: {wrapper}"
            )


    route_before_sha = sha256_file(
        TEAM_ROUTE_FILE
    )

    card_before_sha = sha256_file(
        TEAM_PREDICTION_CARD_FILE
    )


    save_text_atomic(
        TEAM_CONTEXT_LOADER_FILE,
        TEAM_CONTEXT_LOADER_SOURCE,
    )

    save_text_atomic(
        TEAM_CONTEXT_RECORDS_FILE,
        TEAM_CONTEXT_RECORDS_SOURCE,
    )

    save_text_atomic(
        TEAM_STANDINGS_FILE,
        TEAM_STANDINGS_SOURCE,
    )

    save_text_atomic(
        TEAM_RECENT_FORM_FILE,
        TEAM_RECENT_FORM_SOURCE,
    )

    save_text_atomic(
        TEAM_VENUE_FORM_FILE,
        TEAM_VENUE_FORM_SOURCE,
    )


    # ========================================================
    # Patch team route
    # ========================================================

    route_source = (
        TEAM_ROUTE_FILE.read_text(
            encoding="utf-8"
        )
    )


    card_import = '''import {
  TeamPredictionCard,
} from "../../../components/teams/team-prediction-card";

'''


    new_component_imports = '''import {
  TeamStandings,
} from "../../../components/teams/team-standings";

import {
  TeamRecentForm,
} from "../../../components/teams/team-recent-form";

import {
  TeamHomeAwayForm,
} from "../../../components/teams/team-home-away-form";

'''


    route_source = replace_once(
        route_source,
        card_import,
        (
            card_import
            +
            new_component_imports
        ),
        "team context component imports",
    )


    team_loader_import = '''import {
  loadTeamIntelligence,
} from "../../../lib/teams/load-team-intelligence";

'''


    context_loader_import = '''import {
  loadTeamContext,
} from "../../../lib/teams/load-team-context";

'''


    route_source = replace_once(
        route_source,
        team_loader_import,
        (
            team_loader_import
            +
            context_loader_import
        ),
        "team context loader import",
    )


    records_import = '''import {
  extractTeamPageData,
} from "../../../lib/teams/team-records";

'''


    context_records_import = '''import {
  extractTeamFormRecord,
  extractTeamStandingsRecord,
} from "../../../lib/teams/team-context-records";

'''


    route_source = replace_once(
        route_source,
        records_import,
        (
            records_import
            +
            context_records_import
        ),
        "team context record imports",
    )


    team_data_anchor = '''  const team =
    extractTeamPageData(
      result.data,
      teamName,
    );


'''


    context_read = '''  const [
    standingsResult,
    formResult,
  ] = await loadTeamContext(
    teamName,
  );


  if (
    standingsResult.state ===
    "NOT_FOUND"
    ||
    formResult.state ===
    "NOT_FOUND"
  ) {
    notFound();
  }


  if (
    standingsResult.state !==
    "READY"
    ||
    formResult.state !==
    "READY"
  ) {

    return (
      <section
        aria-labelledby="team-context-unavailable-heading"
        data-fixtureiq-team-context-state="UNAVAILABLE"
      >
        <h1
          id="team-context-unavailable-heading"
          className="
            text-2xl font-bold
            tracking-tight
            text-slate-950
          "
        >
          Team context unavailable
        </h1>

        <p
          className="
            mt-3 max-w-2xl
            text-sm leading-6
            text-slate-600
          "
        >
          Current standings or form
          cannot be displayed right now.
        </p>
      </section>
    );
  }


  const standings =
    extractTeamStandingsRecord(
      standingsResult.data,
      teamName,
    );


  const form =
    extractTeamFormRecord(
      formResult.data,
      teamName,
    );


'''


    route_source = replace_once(
        route_source,
        team_data_anchor,
        (
            team_data_anchor
            +
            context_read
        ),
        "team context reads",
    )


    upcoming_anchor = '''      <TeamUpcomingMatches
'''


    context_sections = '''      <div
        className="
          mt-6 grid gap-6
          lg:grid-cols-2
        "
      >
        <TeamStandings
          position={
            standings.position
          }
          points={
            standings.points
          }
          played={
            standings.played
          }
          won={
            standings.won
          }
          drawn={
            standings.drawn
          }
          lost={
            standings.lost
          }
          goalsFor={
            standings.goals_for
          }
          goalsAgainst={
            standings.goals_against
          }
          goalDifference={
            standings.goal_difference
          }
        />

        <TeamRecentForm
          matchesAvailable={
            form.form_matches_available
          }
          results={
            form.recent_results
          }
          points={
            form.recent_points
          }
          wins={
            form.recent_wins
          }
          draws={
            form.recent_draws
          }
          losses={
            form.recent_losses
          }
          goalsFor={
            form.recent_goals_for
          }
          goalsAgainst={
            form.recent_goals_against
          }
          goalDifference={
            form.recent_goal_difference
          }
        />
      </div>

      <div
        className="
          mt-6
        "
      >
        <TeamHomeAwayForm
          homeMatchesAvailable={
            form.home_form_matches_available
          }
          homeResults={
            form.home_recent_results
          }
          homePoints={
            form.home_recent_points
          }
          homeWins={
            form.home_recent_wins
          }
          homeDraws={
            form.home_recent_draws
          }
          homeLosses={
            form.home_recent_losses
          }
          homeGoalsFor={
            form.home_recent_goals_for
          }
          homeGoalsAgainst={
            form.home_recent_goals_against
          }
          homeGoalDifference={
            form.home_recent_goal_difference
          }
          awayMatchesAvailable={
            form.away_form_matches_available
          }
          awayResults={
            form.away_recent_results
          }
          awayPoints={
            form.away_recent_points
          }
          awayWins={
            form.away_recent_wins
          }
          awayDraws={
            form.away_recent_draws
          }
          awayLosses={
            form.away_recent_losses
          }
          awayGoalsFor={
            form.away_recent_goals_for
          }
          awayGoalsAgainst={
            form.away_recent_goals_against
          }
          awayGoalDifference={
            form.away_recent_goal_difference
          }
        />
      </div>

'''


    route_source = replace_once(
        route_source,
        upcoming_anchor,
        (
            context_sections
            +
            upcoming_anchor
        ),
        "team standings and form sections",
    )


    save_text_atomic(
        TEAM_ROUTE_FILE,
        route_source,
    )


    # ========================================================
    # Patch prediction card with fixture link
    # ========================================================

    card_source = (
        TEAM_PREDICTION_CARD_FILE.read_text(
            encoding="utf-8"
        )
    )


    first_import = '''import type {
  ConfidenceBand,
'''


    link_import = '''import Link from "next/link";

'''


    card_source = replace_once(
        card_source,
        first_import,
        (
            link_import
            +
            first_import
        ),
        "Next Link import",
    )


    article_close = '''    </article>
'''


    link_section = '''      <div
        className="
          mt-5 border-t
          border-slate-100
          pt-4
        "
      >
        <Link
          href={`/matches/${encodeURIComponent(
            String(
              fixtureId,
            ),
          )}`}
          className="
            inline-flex items-center
            text-sm font-semibold
            text-slate-900
            underline
            underline-offset-4
          "
        >
          View match intelligence
        </Link>
      </div>

'''


    card_source = replace_once(
        card_source,
        article_close,
        (
            link_section
            +
            article_close
        ),
        "fixture detail link",
    )


    save_text_atomic(
        TEAM_PREDICTION_CARD_FILE,
        card_source,
    )


    route_after_sha = sha256_file(
        TEAM_ROUTE_FILE
    )

    card_after_sha = sha256_file(
        TEAM_PREDICTION_CARD_FILE
    )


    protected = {
        "team_loader_sha256":
            sha256_file(
                TEAM_LOADER_FILE
            ),

        "team_records_sha256":
            sha256_file(
                TEAM_RECORDS_FILE
            ),

        "team_header_sha256":
            sha256_file(
                TEAM_HEADER_FILE
            ),

        "team_upcoming_sha256":
            sha256_file(
                TEAM_UPCOMING_FILE
            ),

        "mapped_api_sha256":
            sha256_file(
                MAPPED_API_FILE
            ),

        "result_mapping_sha256":
            sha256_file(
                RESULT_FILE
            ),

        "domain_types_sha256":
            sha256_file(
                DOMAIN_TYPES_FILE
            ),
    }


    standings_contract = {
        "stage":
            "10.6.5",

        "version":
            "1.0.0",

        "name":
            "TEAM_STANDINGS",

        "status":
            "LOCKED",

        "source_authority":
            "STAGE_8_CONTEXT",

        "backend_endpoint":
            "/api/v1/context/standings/<path:team_name>",

        "mapped_client":
            "getContextStandingsByTeamNameResult",

        "loader_source":
            relative(
                TEAM_CONTEXT_LOADER_FILE
            ),

        "record_source":
            relative(
                TEAM_CONTEXT_RECORDS_FILE
            ),

        "component_source":
            relative(
                TEAM_STANDINGS_FILE
            ),

        "source_fields": [
            "team_name",
            "position",
            "played",
            "won",
            "drawn",
            "lost",
            "goals_for",
            "goals_against",
            "goal_difference",
            "points",
        ],

        "presentation": {
            "values_direct":
                True,

            "frontend_table_calculation":
                False,

            "frontend_points_calculation":
                False,
        },

        "route_page_before_10_6_5_sha256":
            route_before_sha,

        "route_page_after_10_6_5_to_10_6_8_sha256":
            route_after_sha,

        "component_sha256":
            sha256_file(
                TEAM_STANDINGS_FILE
            ),

        "context_loader_sha256":
            sha256_file(
                TEAM_CONTEXT_LOADER_FILE
            ),

        "context_records_sha256":
            sha256_file(
                TEAM_CONTEXT_RECORDS_FILE
            ),

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                PREVIOUS_FILE
            ):
                identity(
                    PREVIOUS_FILE
                ),

            relative(
                PREVIOUS_CARD_CONTRACT_FILE
            ):
                identity(
                    PREVIOUS_CARD_CONTRACT_FILE
                ),

            relative(
                MAPPED_API_FILE
            ):
                identity(
                    MAPPED_API_FILE
                ),
        },

        "promotion": {
            "stage10_6_5_complete":
                False,

            "stage10_6_complete":
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
        STANDINGS_CONTRACT_FILE,
        standings_contract,
    )


    recent_form_contract = {
        "stage":
            "10.6.6",

        "version":
            "1.0.0",

        "name":
            "TEAM_RECENT_FORM",

        "status":
            "LOCKED",

        "source_authority":
            "STAGE_8_CONTEXT",

        "backend_endpoint":
            "/api/v1/context/form/<path:team_name>",

        "mapped_client":
            "getContextFormByTeamNameResult",

        "component_source":
            relative(
                TEAM_RECENT_FORM_FILE
            ),

        "source_fields": [
            "form_matches_available",
            "recent_results",
            "recent_points",
            "recent_wins",
            "recent_draws",
            "recent_losses",
            "recent_goals_for",
            "recent_goals_against",
            "recent_goal_difference",
        ],

        "presentation": {
            "backend_results_direct":
                True,

            "backend_aggregates_direct":
                True,

            "frontend_form_calculation":
                False,

            "frontend_points_calculation":
                False,
        },

        "component_sha256":
            sha256_file(
                TEAM_RECENT_FORM_FILE
            ),

        "route_page_sha256":
            route_after_sha,

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                STANDINGS_CONTRACT_FILE
            ):
                identity(
                    STANDINGS_CONTRACT_FILE
                ),
        },

        "promotion": {
            "stage10_6_6_complete":
                False,

            "stage10_6_complete":
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
        RECENT_FORM_CONTRACT_FILE,
        recent_form_contract,
    )


    venue_form_contract = {
        "stage":
            "10.6.7",

        "version":
            "1.0.0",

        "name":
            "TEAM_HOME_AWAY_FORM",

        "status":
            "LOCKED",

        "source_authority":
            "STAGE_8_CONTEXT",

        "backend_endpoint":
            "/api/v1/context/form/<path:team_name>",

        "component_source":
            relative(
                TEAM_VENUE_FORM_FILE
            ),

        "source_field_groups": [
            "home_*",
            "away_*",
        ],

        "presentation": {
            "home_context_direct":
                True,

            "away_context_direct":
                True,

            "frontend_venue_comparison_score":
                False,

            "frontend_form_calculation":
                False,
        },

        "component_sha256":
            sha256_file(
                TEAM_VENUE_FORM_FILE
            ),

        "route_page_sha256":
            route_after_sha,

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                RECENT_FORM_CONTRACT_FILE
            ):
                identity(
                    RECENT_FORM_CONTRACT_FILE
                ),

            relative(
                TEAM_CONTEXT_RECORDS_FILE
            ):
                identity(
                    TEAM_CONTEXT_RECORDS_FILE
                ),
        },

        "promotion": {
            "stage10_6_7_complete":
                False,

            "stage10_6_complete":
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
        VENUE_FORM_CONTRACT_FILE,
        venue_form_contract,
    )


    fixture_links_contract = {
        "stage":
            "10.6.8",

        "version":
            "1.0.0",

        "name":
            "TEAM_FIXTURE_LINKS",

        "status":
            "LOCKED",

        "source_authority":
            "STAGE_9_FIXTURE_IDENTITY",

        "component_source":
            relative(
                TEAM_PREDICTION_CARD_FILE
            ),

        "target_route":
            "/matches/[fixtureId]",

        "source_field":
            "fixture_id",

        "routing": {
            "next_link":
                True,

            "encodeURIComponent":
                True,

            "one_click_to_match_detail":
                True,

            "frontend_fixture_lookup":
                False,
        },

        "prediction_card_before_10_6_8_sha256":
            card_before_sha,

        "prediction_card_after_10_6_8_sha256":
            card_after_sha,

        "route_page_after_10_6_8_sha256":
            route_after_sha,

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                VENUE_FORM_CONTRACT_FILE
            ):
                identity(
                    VENUE_FORM_CONTRACT_FILE
                ),

            relative(
                PREVIOUS_CARD_CONTRACT_FILE
            ):
                identity(
                    PREVIOUS_CARD_CONTRACT_FILE
                ),
        },

        "promotion": {
            "stage10_6_8_complete":
                False,

            "stage10_6_complete":
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
        FIXTURE_LINKS_CONTRACT_FILE,
        fixture_links_contract,
    )


    print()

    print(
        "Stage 8 team context loader:"
    )

    print(
        f"  {relative(TEAM_CONTEXT_LOADER_FILE)}"
    )

    print(
        "Stage 8 team context records:"
    )

    print(
        f"  {relative(TEAM_CONTEXT_RECORDS_FILE)}"
    )

    print()

    print(
        "Components:"
    )

    for path in [
        TEAM_STANDINGS_FILE,
        TEAM_RECENT_FORM_FILE,
        TEAM_VENUE_FORM_FILE,
        TEAM_PREDICTION_CARD_FILE,
    ]:

        print(
            f"  {relative(path)}"
        )


    print()

    print("=" * 72)

    print(
        "STAGE 10.6.5 STANDINGS: BUILT"
    )

    print(
        "STAGE 10.6.6 RECENT FORM: BUILT"
    )

    print(
        "STAGE 10.6.7 HOME / AWAY FORM: BUILT"
    )

    print(
        "STAGE 10.6.8 FIXTURE LINKS: BUILT"
    )

    print(
        "VERIFICATION STILL REQUIRED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
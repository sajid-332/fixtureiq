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
    / "stage10_5_3_10_5_6_verification.json"
)

UNCERTAINTY_CONTRACT_FILE = (
    DOCS
    / "frontend_match_uncertainty_contract.json"
)


LEAGUE_POSITION_CONTRACT_FILE = (
    DOCS
    / "frontend_match_league_position_comparison_contract.json"
)

POINTS_CONTRACT_FILE = (
    DOCS
    / "frontend_match_points_comparison_contract.json"
)

GOAL_DIFFERENCE_CONTRACT_FILE = (
    DOCS
    / "frontend_match_goal_difference_comparison_contract.json"
)

RECENT_FORM_CONTRACT_FILE = (
    DOCS
    / "frontend_match_recent_form_contract.json"
)


ROUTE_PAGE_FILE = (
    FRONTEND
    / "app"
    / "matches"
    / "[fixtureId]"
    / "page.tsx"
)


CONTEXT_RECORD_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "match-context-record.ts"
)


LEAGUE_POSITION_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-league-position-comparison.tsx"
)

POINTS_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-points-comparison.tsx"
)

GOAL_DIFFERENCE_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-goal-difference-comparison.tsx"
)

RECENT_FORM_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-recent-form.tsx"
)


HEADER_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-fixture-header.tsx"
)

HEADER_RECORD_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "match-header-record.ts"
)

MATCH_LOADER_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "load-match-intelligence.ts"
)

PREDICTION_RECORD_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "match-prediction-record.ts"
)

OVERVIEW_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-prediction-overview.tsx"
)

PROBABILITY_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-probability-visualization.tsx"
)

CONFIDENCE_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-confidence.tsx"
)

UNCERTAINTY_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-uncertainty.tsx"
)


DOMAIN_TYPES_FILE = (
    FRONTEND
    / "lib"
    / "domain"
    / "types.ts"
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

KICKOFF_FORMATTER_FILE = (
    FRONTEND
    / "lib"
    / "formatters"
    / "kickoff.ts"
)

PROBABILITY_FORMATTER_FILE = (
    FRONTEND
    / "lib"
    / "formatters"
    / "probability.ts"
)


CONTEXT_RECORD_SOURCE = '''import "server-only";

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
'''


LEAGUE_POSITION_COMPONENT_SOURCE = '''type MatchLeaguePositionComparisonProps =
  Readonly<{
    homeTeamName:
      string;

    awayTeamName:
      string;

    homePosition:
      number;

    awayPosition:
      number;
  }>;


export function MatchLeaguePositionComparison({
  homeTeamName,
  awayTeamName,
  homePosition,
  awayPosition,
}: MatchLeaguePositionComparisonProps) {

  return (
    <section
      aria-labelledby="league-position-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-league-position-comparison"
    >
      <h2
        id="league-position-heading"
        className="
          text-base font-bold
          text-slate-950
        "
      >
        League position
      </h2>

      <dl
        className="
          mt-4 space-y-3
        "
      >
        <div
          className="
            flex items-center
            justify-between gap-4
          "
        >
          <dt
            className="
              min-w-0 break-words
              text-sm text-slate-600
            "
          >
            {homeTeamName}
          </dt>

          <dd
            className="
              shrink-0 text-sm
              font-semibold text-slate-950
            "
            data-stage8-field="home_team_position"
          >
            #{homePosition}
          </dd>
        </div>

        <div
          className="
            flex items-center
            justify-between gap-4
          "
        >
          <dt
            className="
              min-w-0 break-words
              text-sm text-slate-600
            "
          >
            {awayTeamName}
          </dt>

          <dd
            className="
              shrink-0 text-sm
              font-semibold text-slate-950
            "
            data-stage8-field="away_team_position"
          >
            #{awayPosition}
          </dd>
        </div>
      </dl>
    </section>
  );
}
'''


POINTS_COMPONENT_SOURCE = '''type MatchPointsComparisonProps =
  Readonly<{
    homeTeamName:
      string;

    awayTeamName:
      string;

    homePoints:
      number;

    awayPoints:
      number;
  }>;


export function MatchPointsComparison({
  homeTeamName,
  awayTeamName,
  homePoints,
  awayPoints,
}: MatchPointsComparisonProps) {

  return (
    <section
      aria-labelledby="points-comparison-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-points-comparison"
    >
      <h2
        id="points-comparison-heading"
        className="
          text-base font-bold
          text-slate-950
        "
      >
        League points
      </h2>

      <dl
        className="
          mt-4 space-y-3
        "
      >
        <div
          className="
            flex items-center
            justify-between gap-4
          "
        >
          <dt
            className="
              min-w-0 break-words
              text-sm text-slate-600
            "
          >
            {homeTeamName}
          </dt>

          <dd
            className="
              shrink-0 text-sm
              font-semibold text-slate-950
            "
            data-stage8-field="home_team_points"
          >
            {homePoints}
          </dd>
        </div>

        <div
          className="
            flex items-center
            justify-between gap-4
          "
        >
          <dt
            className="
              min-w-0 break-words
              text-sm text-slate-600
            "
          >
            {awayTeamName}
          </dt>

          <dd
            className="
              shrink-0 text-sm
              font-semibold text-slate-950
            "
            data-stage8-field="away_team_points"
          >
            {awayPoints}
          </dd>
        </div>
      </dl>
    </section>
  );
}
'''


GOAL_DIFFERENCE_COMPONENT_SOURCE = '''const signedIntegerFormatter =
  new Intl.NumberFormat(
    "en-GB",
    {
      maximumFractionDigits: 0,
      signDisplay: "always",
    },
  );


type MatchGoalDifferenceComparisonProps =
  Readonly<{
    homeTeamName:
      string;

    awayTeamName:
      string;

    homeGoalDifference:
      number;

    awayGoalDifference:
      number;
  }>;


export function MatchGoalDifferenceComparison({
  homeTeamName,
  awayTeamName,
  homeGoalDifference,
  awayGoalDifference,
}: MatchGoalDifferenceComparisonProps) {

  return (
    <section
      aria-labelledby="goal-difference-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-goal-difference-comparison"
    >
      <h2
        id="goal-difference-heading"
        className="
          text-base font-bold
          text-slate-950
        "
      >
        Goal difference
      </h2>

      <dl
        className="
          mt-4 space-y-3
        "
      >
        <div
          className="
            flex items-center
            justify-between gap-4
          "
        >
          <dt
            className="
              min-w-0 break-words
              text-sm text-slate-600
            "
          >
            {homeTeamName}
          </dt>

          <dd
            className="
              shrink-0 text-sm
              font-semibold text-slate-950
            "
            data-stage8-field="home_team_goal_difference"
          >
            {signedIntegerFormatter.format(
              homeGoalDifference,
            )}
          </dd>
        </div>

        <div
          className="
            flex items-center
            justify-between gap-4
          "
        >
          <dt
            className="
              min-w-0 break-words
              text-sm text-slate-600
            "
          >
            {awayTeamName}
          </dt>

          <dd
            className="
              shrink-0 text-sm
              font-semibold text-slate-950
            "
            data-stage8-field="away_team_goal_difference"
          >
            {signedIntegerFormatter.format(
              awayGoalDifference,
            )}
          </dd>
        </div>
      </dl>
    </section>
  );
}
'''


RECENT_FORM_COMPONENT_SOURCE = '''type MatchRecentFormProps =
  Readonly<{
    homeTeamName:
      string;

    awayTeamName:
      string;

    homeResults:
      string;

    awayResults:
      string;

    homeMatchesAvailable:
      number;

    awayMatchesAvailable:
      number;
  }>;


export function MatchRecentForm({
  homeTeamName,
  awayTeamName,
  homeResults,
  awayResults,
  homeMatchesAvailable,
  awayMatchesAvailable,
}: MatchRecentFormProps) {

  return (
    <section
      aria-labelledby="recent-form-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-recent-form"
    >
      <h2
        id="recent-form-heading"
        className="
          text-lg font-bold
          text-slate-950
        "
      >
        Recent form
      </h2>

      <div
        className="
          mt-5 grid gap-5
          sm:grid-cols-2
        "
      >
        <div>
          <p
            className="
              text-sm font-semibold
              text-slate-700
            "
          >
            {homeTeamName}
          </p>

          <p
            className="
              mt-2 font-mono text-base
              font-semibold tracking-widest
              text-slate-950
            "
            data-stage8-field="home_team_recent_results"
          >
            {homeResults || "No results"}
          </p>

          <p
            className="
              mt-1 text-xs
              text-slate-500
            "
            data-stage8-field="home_team_form_matches_available"
          >
            {homeMatchesAvailable} matches available
          </p>
        </div>

        <div>
          <p
            className="
              text-sm font-semibold
              text-slate-700
            "
          >
            {awayTeamName}
          </p>

          <p
            className="
              mt-2 font-mono text-base
              font-semibold tracking-widest
              text-slate-950
            "
            data-stage8-field="away_team_recent_results"
          >
            {awayResults || "No results"}
          </p>

          <p
            className="
              mt-1 text-xs
              text-slate-500
            "
            data-stage8-field="away_team_form_matches_available"
          >
            {awayMatchesAvailable} matches available
          </p>
        </div>
      </div>

      <p
        className="
          mt-5 text-xs
          leading-5 text-slate-500
        "
      >
        W = win, D = draw, L = loss.
      </p>
    </section>
  );
}
'''


COMPONENT_IMPORTS = '''import {
  MatchLeaguePositionComparison,
} from "../../../components/matches/match-league-position-comparison";

import {
  MatchPointsComparison,
} from "../../../components/matches/match-points-comparison";

import {
  MatchGoalDifferenceComparison,
} from "../../../components/matches/match-goal-difference-comparison";

import {
  MatchRecentForm,
} from "../../../components/matches/match-recent-form";

'''


CONTEXT_RECORD_IMPORT = '''import {
  extractMatchContextRecord,
} from "../../../lib/matches/match-context-record";

'''


CONTEXT_READ = '''  const context =
    extractMatchContextRecord(
      result.data,
      fixtureId,
    );


'''


CONTEXT_SECTIONS = '''      <div
        className="
          mt-6 grid gap-6
          lg:grid-cols-3
        "
      >
        <MatchLeaguePositionComparison
          homeTeamName={
            header.home_team_name
          }
          awayTeamName={
            header.away_team_name
          }
          homePosition={
            context.home_team_position
          }
          awayPosition={
            context.away_team_position
          }
        />

        <MatchPointsComparison
          homeTeamName={
            header.home_team_name
          }
          awayTeamName={
            header.away_team_name
          }
          homePoints={
            context.home_team_points
          }
          awayPoints={
            context.away_team_points
          }
        />

        <MatchGoalDifferenceComparison
          homeTeamName={
            header.home_team_name
          }
          awayTeamName={
            header.away_team_name
          }
          homeGoalDifference={
            context.home_team_goal_difference
          }
          awayGoalDifference={
            context.away_team_goal_difference
          }
        />
      </div>

      <div
        className="
          mt-6
        "
      >
        <MatchRecentForm
          homeTeamName={
            header.home_team_name
          }
          awayTeamName={
            header.away_team_name
          }
          homeResults={
            context.home_team_recent_results
          }
          awayResults={
            context.away_team_recent_results
          }
          homeMatchesAvailable={
            context.home_team_form_matches_available
          }
          awayMatchesAvailable={
            context.away_team_form_matches_available
          }
        />
      </div>
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


def protected_state() -> dict:

    paths = {
        "header_component_sha256":
            HEADER_COMPONENT_FILE,

        "header_record_sha256":
            HEADER_RECORD_FILE,

        "match_loader_sha256":
            MATCH_LOADER_FILE,

        "prediction_record_sha256":
            PREDICTION_RECORD_FILE,

        "prediction_overview_sha256":
            OVERVIEW_COMPONENT_FILE,

        "probability_visualization_sha256":
            PROBABILITY_COMPONENT_FILE,

        "confidence_sha256":
            CONFIDENCE_COMPONENT_FILE,

        "uncertainty_sha256":
            UNCERTAINTY_COMPONENT_FILE,

        "domain_types_sha256":
            DOMAIN_TYPES_FILE,

        "mapped_api_sha256":
            MAPPED_API_FILE,

        "result_sha256":
            RESULT_FILE,

        "kickoff_formatter_sha256":
            KICKOFF_FORMATTER_FILE,

        "probability_formatter_sha256":
            PROBABILITY_FORMATTER_FILE,
    }


    return {
        key:
            sha256_file(
                path
            )

        for key, path
        in paths.items()
    }


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.5.7 - 10.5.10"
    )

    print(
        "LEAGUE POSITION + POINTS + GOAL DIFFERENCE + RECENT FORM"
    )

    print("=" * 72)


    previous = load_json(
        PREVIOUS_FILE
    )

    uncertainty_contract = load_json(
        UNCERTAINTY_CONTRACT_FILE
    )


    if (
        previous.get(
            "status"
        )
        !=
        "PASS"
    ):
        raise RuntimeError(
            "10.5.3-10.5.6 verification is not PASS."
        )


    for key in [
        "stage_10_5_3_complete",
        "stage_10_5_4_complete",
        "stage_10_5_5_complete",
        "stage_10_5_6_complete",
    ]:

        if (
            previous.get(
                key
            )
            is not True
        ):

            raise RuntimeError(
                f"Previous stage flag is not complete: {key}"
            )


    if (
        previous.get(
            "stage10_ready_for_10_5_7"
        )
        is not True
    ):

        raise RuntimeError(
            "10.5.6 did not authorize 10.5.7."
        )


    required = [
        ROUTE_PAGE_FILE,
        HEADER_COMPONENT_FILE,
        HEADER_RECORD_FILE,
        MATCH_LOADER_FILE,
        PREDICTION_RECORD_FILE,
        OVERVIEW_COMPONENT_FILE,
        PROBABILITY_COMPONENT_FILE,
        CONFIDENCE_COMPONENT_FILE,
        UNCERTAINTY_COMPONENT_FILE,
        DOMAIN_TYPES_FILE,
        MAPPED_API_FILE,
        RESULT_FILE,
        KICKOFF_FORMATTER_FILE,
        PROBABILITY_FORMATTER_FILE,
    ]


    for path in required:

        if not path.exists():

            raise RuntimeError(
                f"Missing source: {path}"
            )


    expected_route_sha = (
        uncertainty_contract.get(
            "route_page_after_10_5_6_sha256"
        )
    )


    final_contract = optional_json(
        RECENT_FORM_CONTRACT_FILE
    )


    if (
        final_contract
        and
        CONTEXT_RECORD_FILE.exists()
        and
        LEAGUE_POSITION_COMPONENT_FILE.exists()
        and
        POINTS_COMPONENT_FILE.exists()
        and
        GOAL_DIFFERENCE_COMPONENT_FILE.exists()
        and
        RECENT_FORM_COMPONENT_FILE.exists()
        and
        sha256_file(
            ROUTE_PAGE_FILE
        )
        ==
        final_contract.get(
            "route_page_after_10_5_10_sha256"
        )
        and
        sha256_file(
            RECENT_FORM_COMPONENT_FILE
        )
        ==
        final_contract.get(
            "component_sha256"
        )
    ):

        print()

        print(
            "10.5.7 - 10.5.10 already built."
        )

        print("=" * 72)

        print(
            "STAGE 10.5.7 LEAGUE POSITION COMPARISON: BUILT"
        )

        print(
            "STAGE 10.5.8 POINTS COMPARISON: BUILT"
        )

        print(
            "STAGE 10.5.9 GOAL DIFFERENCE COMPARISON: BUILT"
        )

        print(
            "STAGE 10.5.10 RECENT FORM: BUILT"
        )

        print(
            "VERIFICATION STILL REQUIRED"
        )

        print("=" * 72)

        return


    if (
        sha256_file(
            ROUTE_PAGE_FILE
        )
        !=
        expected_route_sha
    ):

        raise RuntimeError(
            (
                "Match detail route no longer matches "
                "verified 10.5.6 output."
            )
        )


    route_before_sha = (
        sha256_file(
            ROUTE_PAGE_FILE
        )
    )


    # ========================================================
    # Build new sources
    # ========================================================

    save_text_atomic(
        CONTEXT_RECORD_FILE,
        CONTEXT_RECORD_SOURCE,
    )

    save_text_atomic(
        LEAGUE_POSITION_COMPONENT_FILE,
        LEAGUE_POSITION_COMPONENT_SOURCE,
    )

    save_text_atomic(
        POINTS_COMPONENT_FILE,
        POINTS_COMPONENT_SOURCE,
    )

    save_text_atomic(
        GOAL_DIFFERENCE_COMPONENT_FILE,
        GOAL_DIFFERENCE_COMPONENT_SOURCE,
    )

    save_text_atomic(
        RECENT_FORM_COMPONENT_FILE,
        RECENT_FORM_COMPONENT_SOURCE,
    )


    # ========================================================
    # Evolve detail route
    # ========================================================

    route_source = (
        ROUTE_PAGE_FILE.read_text(
            encoding="utf-8"
        )
    )


    uncertainty_import = '''import {
  MatchUncertainty,
} from "../../../components/matches/match-uncertainty";

'''


    route_source = replace_once(
        route_source,
        uncertainty_import,
        (
            uncertainty_import
            +
            COMPONENT_IMPORTS
        ),
        "context component imports",
    )


    prediction_record_import = '''import {
  extractMatchPredictionRecord,
} from "../../../lib/matches/match-prediction-record";

'''


    route_source = replace_once(
        route_source,
        prediction_record_import,
        (
            prediction_record_import
            +
            CONTEXT_RECORD_IMPORT
        ),
        "context record import",
    )


    return_anchor = '''  return (
    <article
'''


    route_source = replace_once(
        route_source,
        return_anchor,
        (
            CONTEXT_READ
            +
            return_anchor
        ),
        "context extraction",
    )


    article_close = '''    </article>
'''


    route_source = replace_once(
        route_source,
        article_close,
        (
            CONTEXT_SECTIONS
            +
            article_close
        ),
        "context presentation sections",
    )


    save_text_atomic(
        ROUTE_PAGE_FILE,
        route_source,
    )


    route_after_sha = (
        sha256_file(
            ROUTE_PAGE_FILE
        )
    )


    protected = (
        protected_state()
    )


    # ========================================================
    # 10.5.7
    # ========================================================

    league_contract = {
        "stage":
            "10.5.7",

        "version":
            "1.0.0",

        "name":
            "MATCH_LEAGUE_POSITION_COMPARISON",

        "status":
            "LOCKED",

        "source_authority":
            "STAGE_8_CONTEXT",

        "transport_path":
            "STAGE_9_INTELLIGENCE_API_JOIN",

        "component_source":
            relative(
                LEAGUE_POSITION_COMPONENT_FILE
            ),

        "record_source":
            relative(
                CONTEXT_RECORD_FILE
            ),

        "source_fields": [
            "home_team_position",
            "away_team_position",
        ],

        "presentation": {
            "direct_home_value":
                True,

            "direct_away_value":
                True,

            "frontend_gap_calculation":
                False,

            "stage9_gap_used":
                False,
        },

        "component_sha256":
            sha256_file(
                LEAGUE_POSITION_COMPONENT_FILE
            ),

        "context_record_sha256":
            sha256_file(
                CONTEXT_RECORD_FILE
            ),

        "route_page_before_10_5_7_sha256":
            route_before_sha,

        "route_page_after_10_5_7_to_10_5_10_sha256":
            route_after_sha,

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
                UNCERTAINTY_CONTRACT_FILE
            ):
                identity(
                    UNCERTAINTY_CONTRACT_FILE
                ),
        },

        "promotion": {
            "stage10_5_7_complete":
                False,

            "stage10_5_complete":
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
        LEAGUE_POSITION_CONTRACT_FILE,
        league_contract,
    )


    # ========================================================
    # 10.5.8
    # ========================================================

    points_contract = {
        "stage":
            "10.5.8",

        "version":
            "1.0.0",

        "name":
            "MATCH_POINTS_COMPARISON",

        "status":
            "LOCKED",

        "source_authority":
            "STAGE_8_CONTEXT",

        "transport_path":
            "STAGE_9_INTELLIGENCE_API_JOIN",

        "component_source":
            relative(
                POINTS_COMPONENT_FILE
            ),

        "source_fields": [
            "home_team_points",
            "away_team_points",
        ],

        "presentation": {
            "direct_home_value":
                True,

            "direct_away_value":
                True,

            "frontend_gap_calculation":
                False,

            "stage9_gap_used":
                False,
        },

        "component_sha256":
            sha256_file(
                POINTS_COMPONENT_FILE
            ),

        "route_page_after_10_5_8_sha256":
            route_after_sha,

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                LEAGUE_POSITION_CONTRACT_FILE
            ):
                identity(
                    LEAGUE_POSITION_CONTRACT_FILE
                ),
        },

        "promotion": {
            "stage10_5_8_complete":
                False,

            "stage10_5_complete":
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
        POINTS_CONTRACT_FILE,
        points_contract,
    )


    # ========================================================
    # 10.5.9
    # ========================================================

    goal_difference_contract = {
        "stage":
            "10.5.9",

        "version":
            "1.0.0",

        "name":
            "MATCH_GOAL_DIFFERENCE_COMPARISON",

        "status":
            "LOCKED",

        "source_authority":
            "STAGE_8_CONTEXT",

        "transport_path":
            "STAGE_9_INTELLIGENCE_API_JOIN",

        "component_source":
            relative(
                GOAL_DIFFERENCE_COMPONENT_FILE
            ),

        "source_fields": [
            "home_team_goal_difference",
            "away_team_goal_difference",
        ],

        "presentation": {
            "direct_home_value":
                True,

            "direct_away_value":
                True,

            "display_sign_formatting_only":
                True,

            "frontend_gap_calculation":
                False,

            "stage9_gap_used":
                False,
        },

        "component_sha256":
            sha256_file(
                GOAL_DIFFERENCE_COMPONENT_FILE
            ),

        "route_page_after_10_5_9_sha256":
            route_after_sha,

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                POINTS_CONTRACT_FILE
            ):
                identity(
                    POINTS_CONTRACT_FILE
                ),
        },

        "promotion": {
            "stage10_5_9_complete":
                False,

            "stage10_5_complete":
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
        GOAL_DIFFERENCE_CONTRACT_FILE,
        goal_difference_contract,
    )


    # ========================================================
    # 10.5.10
    # ========================================================

    recent_form_contract = {
        "stage":
            "10.5.10",

        "version":
            "1.0.0",

        "name":
            "MATCH_RECENT_FORM",

        "status":
            "LOCKED",

        "source_authority":
            "STAGE_8_CONTEXT",

        "transport_path":
            "STAGE_9_INTELLIGENCE_API_JOIN",

        "component_source":
            relative(
                RECENT_FORM_COMPONENT_FILE
            ),

        "source_fields": [
            "home_team_recent_results",
            "away_team_recent_results",
            "home_team_form_matches_available",
            "away_team_form_matches_available",
        ],

        "presentation": {
            "results_direct":
                True,

            "matches_available_direct":
                True,

            "recent_points_calculated":
                False,

            "win_draw_loss_counts_calculated":
                False,

            "reusable_recent_form_component_deferred_to":
                "10.7.9",

            "venue_form_used":
                False,
        },

        "component_sha256":
            sha256_file(
                RECENT_FORM_COMPONENT_FILE
            ),

        "context_record_sha256":
            sha256_file(
                CONTEXT_RECORD_FILE
            ),

        "route_page_after_10_5_10_sha256":
            route_after_sha,

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                GOAL_DIFFERENCE_CONTRACT_FILE
            ):
                identity(
                    GOAL_DIFFERENCE_CONTRACT_FILE
                ),

            relative(
                CONTEXT_RECORD_FILE
            ):
                identity(
                    CONTEXT_RECORD_FILE
                ),
        },

        "promotion": {
            "stage10_5_10_complete":
                False,

            "stage10_5_complete":
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


    print()

    print(
        "Context record:"
    )

    print(
        f"  {relative(CONTEXT_RECORD_FILE)}"
    )

    print()

    print(
        "Components:"
    )

    for path in [
        LEAGUE_POSITION_COMPONENT_FILE,
        POINTS_COMPONENT_FILE,
        GOAL_DIFFERENCE_COMPONENT_FILE,
        RECENT_FORM_COMPONENT_FILE,
    ]:

        print(
            f"  {relative(path)}"
        )


    print()

    print("=" * 72)

    print(
        "STAGE 10.5.7 LEAGUE POSITION COMPARISON: BUILT"
    )

    print(
        "STAGE 10.5.8 POINTS COMPARISON: BUILT"
    )

    print(
        "STAGE 10.5.9 GOAL DIFFERENCE COMPARISON: BUILT"
    )

    print(
        "STAGE 10.5.10 RECENT FORM: BUILT"
    )

    print(
        "VERIFICATION STILL REQUIRED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
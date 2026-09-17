from __future__ import annotations

import hashlib
import json
import re
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
    / "stage10_5_final_verification.json"
)

MATCH_STATUS_CONTRACT_FILE = (
    DOCS
    / "frontend_match_freshness_status_contract.json"
)


ROUTE_CONTRACT_FILE = (
    DOCS
    / "frontend_team_dynamic_route_contract.json"
)

IDENTITY_CONTRACT_FILE = (
    DOCS
    / "frontend_team_identity_header_contract.json"
)

UPCOMING_CONTRACT_FILE = (
    DOCS
    / "frontend_team_upcoming_matches_contract.json"
)

PREDICTION_CARDS_CONTRACT_FILE = (
    DOCS
    / "frontend_team_prediction_cards_contract.json"
)


PACKAGE_FILE = (
    FRONTEND
    / "package.json"
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


MATCH_DETAIL_ROUTE_FILE = (
    FRONTEND
    / "app"
    / "matches"
    / "[fixtureId]"
    / "page.tsx"
)


TEAM_ROUTE_DIR = (
    FRONTEND
    / "app"
    / "teams"
    / "[teamName]"
)

TEAM_ROUTE_FILE = (
    TEAM_ROUTE_DIR
    / "page.tsx"
)

TEAM_LOADER_FILE = (
    FRONTEND
    / "lib"
    / "teams"
    / "load-team-intelligence.ts"
)

TEAM_RECORDS_FILE = (
    FRONTEND
    / "lib"
    / "teams"
    / "team-records.ts"
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


TEAM_LOADER_SOURCE = '''import "server-only";

import {
  getTeamIntelligenceResult,
} from "../api/mapped";


export function loadTeamIntelligence(
  teamName: string,
) {
  return getTeamIntelligenceResult(
    teamName,
  );
}
'''


TEAM_RECORDS_SOURCE = '''import "server-only";

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
'''


TEAM_HEADER_SOURCE = '''type TeamIdentityHeaderProps =
  Readonly<{
    teamName:
      string;
  }>;


export function TeamIdentityHeader({
  teamName,
}: TeamIdentityHeaderProps) {

  return (
    <header
      aria-labelledby="team-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-6
        shadow-sm
        sm:px-7 sm:py-8
      "
      data-fixtureiq-component="team-identity-header"
    >
      <p
        className="
          text-sm font-semibold
          uppercase tracking-wide
          text-slate-500
        "
      >
        Team intelligence
      </p>

      <h1
        id="team-heading"
        className="
          mt-2 break-words
          text-2xl font-bold
          tracking-tight
          text-slate-950
          sm:text-3xl
        "
        data-team-name
      >
        {teamName}
      </h1>
    </header>
  );
}
'''


TEAM_UPCOMING_SOURCE = '''import type {
  ReactNode,
} from "react";


type TeamUpcomingMatchesProps =
  Readonly<{
    teamName:
      string;

    matchCount:
      number;

    children:
      ReactNode;
  }>;


export function TeamUpcomingMatches({
  teamName,
  matchCount,
  children,
}: TeamUpcomingMatchesProps) {

  return (
    <section
      aria-labelledby="team-upcoming-heading"
      className="
        mt-6
      "
      data-fixtureiq-component="team-upcoming-matches"
      data-team-match-count={
        matchCount
      }
    >
      <div
        className="
          flex flex-wrap
          items-end justify-between
          gap-3
        "
      >
        <div>
          <p
            className="
              text-xs font-medium
              uppercase tracking-wide
              text-slate-500
            "
          >
            {teamName}
          </p>

          <h2
            id="team-upcoming-heading"
            className="
              mt-1 text-xl font-bold
              tracking-tight
              text-slate-950
            "
          >
            Upcoming matches
          </h2>
        </div>

        <p
          className="
            text-sm
            text-slate-500
          "
        >
          {matchCount} matches
        </p>
      </div>

      <div
        className="
          mt-5 grid gap-5
          xl:grid-cols-2
        "
      >
        {children}
      </div>
    </section>
  );
}
'''


TEAM_PREDICTION_CARD_SOURCE = '''import type {
  ConfidenceBand,
  ContextAlignment,
  FixtureId,
  OutcomeLabel,
  UncertaintyBand,
} from "../../lib/domain/types";

import {
  formatKickoffUtc,
} from "../../lib/formatters/kickoff";

import {
  formatProbability,
} from "../../lib/formatters/probability";


type TeamPredictionCardProps =
  Readonly<{
    fixtureId:
      FixtureId;

    homeTeamName:
      string;

    awayTeamName:
      string;

    kickoffUtc:
      string;

    homeProbability:
      number;

    drawProbability:
      number;

    awayProbability:
      number;

    predictedLabel:
      OutcomeLabel;

    confidence:
      number;

    confidenceBand:
      ConfidenceBand;

    uncertaintyBand:
      UncertaintyBand;

    contextAlignment:
      ContextAlignment;
  }>;


type ProbabilityValueProps =
  Readonly<{
    label:
      string;

    value:
      number;

    sourceField:
      string;
  }>;


function ProbabilityValue({
  label,
  value,
  sourceField,
}: ProbabilityValueProps) {

  return (
    <div>
      <dt
        className="
          text-xs font-medium
          text-slate-500
        "
      >
        {label}
      </dt>

      <dd
        className="
          mt-1 text-sm font-semibold
          text-slate-950
        "
        data-stage7-field={
          sourceField
        }
      >
        {formatProbability(
          value,
        )}
      </dd>
    </div>
  );
}


export function TeamPredictionCard({
  fixtureId,
  homeTeamName,
  awayTeamName,
  kickoffUtc,
  homeProbability,
  drawProbability,
  awayProbability,
  predictedLabel,
  confidence,
  confidenceBand,
  uncertaintyBand,
  contextAlignment,
}: TeamPredictionCardProps) {

  return (
    <article
      aria-label={`${homeTeamName} vs ${awayTeamName}`}
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="team-prediction-card"
      data-fixture-id={
        String(
          fixtureId,
        )
      }
    >
      <header>
        <p
          className="
            text-xs font-medium
            uppercase tracking-wide
            text-slate-500
          "
        >
          Upcoming fixture
        </p>

        <div
          className="
            mt-3 grid
            grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]
            items-center gap-3
          "
        >
          <p
            className="
              min-w-0 break-words
              font-semibold text-slate-950
            "
          >
            {homeTeamName}
          </p>

          <span
            aria-hidden="true"
            className="
              text-xs font-medium
              text-slate-400
            "
          >
            vs
          </span>

          <p
            className="
              min-w-0 break-words
              text-right font-semibold
              text-slate-950
            "
          >
            {awayTeamName}
          </p>
        </div>

        <time
          dateTime={
            kickoffUtc
          }
          className="
            mt-3 block
            text-sm text-slate-600
          "
          data-stage9-field="date"
        >
          {formatKickoffUtc(
            kickoffUtc,
          )} UTC
        </time>
      </header>

      <dl
        className="
          mt-5 grid grid-cols-3
          gap-3 border-t
          border-slate-100 pt-4
        "
      >
        <ProbabilityValue
          label="Home"
          value={
            homeProbability
          }
          sourceField="stage7_prob_home_win"
        />

        <ProbabilityValue
          label="Draw"
          value={
            drawProbability
          }
          sourceField="stage7_prob_draw"
        />

        <ProbabilityValue
          label="Away"
          value={
            awayProbability
          }
          sourceField="stage7_prob_away_win"
        />
      </dl>

      <dl
        className="
          mt-5 space-y-3
          border-t border-slate-100
          pt-4
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
              text-sm text-slate-600
            "
          >
            Prediction
          </dt>

          <dd
            className="
              text-sm font-semibold
              text-slate-950
            "
            data-stage7-field="stage7_predicted_label"
          >
            {predictedLabel}
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
              text-sm text-slate-600
            "
          >
            Confidence
          </dt>

          <dd
            className="
              text-sm font-semibold
              text-slate-950
            "
            data-stage7-field="stage7_confidence"
          >
            {formatProbability(
              confidence,
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
              text-sm text-slate-600
            "
          >
            Confidence band
          </dt>

          <dd
            className="
              text-sm font-semibold
              text-slate-950
            "
            data-stage9-field="stage9_confidence_band"
          >
            {confidenceBand}
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
              text-sm text-slate-600
            "
          >
            Uncertainty
          </dt>

          <dd
            className="
              text-sm font-semibold
              text-slate-950
            "
            data-stage9-field="stage9_uncertainty_band"
          >
            {uncertaintyBand}
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
              text-sm text-slate-600
            "
          >
            Context alignment
          </dt>

          <dd
            className="
              text-sm font-semibold
              text-slate-950
            "
            data-stage9-field="stage9_context_alignment"
          >
            {contextAlignment}
          </dd>
        </div>
      </dl>
    </article>
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


def detect_next_major() -> tuple[
    int,
    str,
]:

    package = load_json(
        PACKAGE_FILE
    )

    dependencies = {
        **package.get(
            "dependencies",
            {},
        ),
        **package.get(
            "devDependencies",
            {},
        ),
    }

    version = dependencies.get(
        "next"
    )


    if not isinstance(
        version,
        str,
    ):
        raise RuntimeError(
            "Next.js dependency not found."
        )


    match = re.search(
        r"(\d+)",
        version,
    )


    if match is None:
        raise RuntimeError(
            f"Cannot parse Next.js version: {version!r}"
        )


    return (
        int(
            match.group(1)
        ),
        version,
    )


def build_route_source(
    async_params: bool,
) -> str:

    if async_params:

        props = '''type TeamPageProps =
  Readonly<{
    params:
      Promise<
        TeamRouteParams
      >;
  }>;
'''

        param_read = '''  const {
    teamName,
  } = await params;
'''

    else:

        props = '''type TeamPageProps =
  Readonly<{
    params:
      TeamRouteParams;
  }>;
'''

        param_read = '''  const {
    teamName,
  } = params;
'''


    return f'''import {{
  notFound,
}} from "next/navigation";

import {{
  TeamIdentityHeader,
}} from "../../../components/teams/team-identity-header";

import {{
  TeamUpcomingMatches,
}} from "../../../components/teams/team-upcoming-matches";

import {{
  TeamPredictionCard,
}} from "../../../components/teams/team-prediction-card";

import {{
  loadTeamIntelligence,
}} from "../../../lib/teams/load-team-intelligence";

import {{
  extractTeamPageData,
}} from "../../../lib/teams/team-records";

import type {{
  TeamRouteParams,
}} from "../../../lib/domain/types";


export const dynamic =
  "force-dynamic";


{props}

export default async function TeamPage({{
  params,
}}: TeamPageProps) {{

{param_read}

  const result =
    await loadTeamIntelligence(
      teamName,
    );


  if (
    result.state ===
    "NOT_FOUND"
  ) {{
    notFound();
  }}


  if (
    result.state !==
    "READY"
  ) {{

    return (
      <section
        aria-labelledby="team-unavailable-heading"
        data-fixtureiq-team-state={{
          result.state
        }}
      >
        <h1
          id="team-unavailable-heading"
          className="
            text-2xl font-bold
            tracking-tight
            text-slate-950
          "
        >
          Team intelligence unavailable
        </h1>

        <p
          className="
            mt-3 max-w-2xl
            text-sm leading-6
            text-slate-600
          "
        >
          This team cannot be displayed
          right now.
        </p>
      </section>
    );
  }}


  const team =
    extractTeamPageData(
      result.data,
      teamName,
    );


  return (
    <article
      data-fixtureiq-route="team-intelligence"
      data-fixtureiq-team-state="READY"
    >
      <TeamIdentityHeader
        teamName={{
          team.teamName
        }}
      />

      <TeamUpcomingMatches
        teamName={{
          team.teamName
        }}
        matchCount={{
          team.matches.length
        }}
      >
        {{
          team.matches.map(
            (
              match,
            ) => (
              <TeamPredictionCard
                key={{
                  String(
                    match.fixture_id,
                  )
                }}
                fixtureId={{
                  match.fixture_id
                }}
                homeTeamName={{
                  match.home_team_name
                }}
                awayTeamName={{
                  match.away_team_name
                }}
                kickoffUtc={{
                  match.date
                }}
                homeProbability={{
                  match.stage7_prob_home_win
                }}
                drawProbability={{
                  match.stage7_prob_draw
                }}
                awayProbability={{
                  match.stage7_prob_away_win
                }}
                predictedLabel={{
                  match.stage7_predicted_label
                }}
                confidence={{
                  match.stage7_confidence
                }}
                confidenceBand={{
                  match.stage9_confidence_band
                }}
                uncertaintyBand={{
                  match.stage9_uncertainty_band
                }}
                contextAlignment={{
                  match.stage9_context_alignment
                }}
              />
            ),
          )
        }}
      </TeamUpcomingMatches>
    </article>
  );
}}
'''


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.6.1 - 10.6.4"
    )

    print(
        "TEAM ROUTE + IDENTITY + UPCOMING MATCHES + PREDICTION CARDS"
    )

    print("=" * 72)


    previous = load_json(
        PREVIOUS_FILE
    )

    match_status_contract = load_json(
        MATCH_STATUS_CONTRACT_FILE
    )


    if (
        previous.get(
            "status"
        )
        !=
        "PASS"
    ):
        raise RuntimeError(
            "Stage 10.5 final verification is not PASS."
        )


    if (
        previous.get(
            "stage10_5_complete"
        )
        is not True
    ):
        raise RuntimeError(
            "Stage 10.5 is not complete."
        )


    if (
        previous.get(
            "stage10_ready_for_10_6_1"
        )
        is not True
    ):
        raise RuntimeError(
            "Stage 10.5 did not authorize 10.6.1."
        )


    required = [
        PACKAGE_FILE,
        DOMAIN_TYPES_FILE,
        MAPPED_API_FILE,
        RESULT_FILE,
        KICKOFF_FORMATTER_FILE,
        PROBABILITY_FORMATTER_FILE,
        MATCH_DETAIL_ROUTE_FILE,
    ]


    for path in required:

        if not path.exists():
            raise RuntimeError(
                f"Missing source: {path}"
            )


    domain_source = (
        DOMAIN_TYPES_FILE.read_text(
            encoding="utf-8"
        )
    )


    if (
        "export type TeamRouteParams"
        not in
        domain_source
        or
        "teamName: string"
        not in
        domain_source
    ):
        raise RuntimeError(
            "Locked TeamRouteParams type is missing."
        )


    mapped_source = (
        MAPPED_API_FILE.read_text(
            encoding="utf-8"
        )
    )


    if (
        "getTeamIntelligenceResult"
        not in
        mapped_source
    ):
        raise RuntimeError(
            "Mapped Stage 9 team intelligence client is missing."
        )


    locked_match_route_sha = (
        match_status_contract.get(
            "route_page_after_10_5_15_sha256"
        )
    )


    if (
        not isinstance(
            locked_match_route_sha,
            str,
        )
        or
        sha256_file(
            MATCH_DETAIL_ROUTE_FILE
        )
        !=
        locked_match_route_sha
    ):
        raise RuntimeError(
            "Verified Stage 10.5 match detail route changed."
        )


    existing_final = optional_json(
        PREDICTION_CARDS_CONTRACT_FILE
    )


    if (
        existing_final
        and
        TEAM_ROUTE_FILE.exists()
        and
        TEAM_LOADER_FILE.exists()
        and
        TEAM_RECORDS_FILE.exists()
        and
        TEAM_HEADER_FILE.exists()
        and
        TEAM_UPCOMING_FILE.exists()
        and
        TEAM_PREDICTION_CARD_FILE.exists()
        and
        sha256_file(
            TEAM_ROUTE_FILE
        )
        ==
        existing_final.get(
            "route_page_after_10_6_4_sha256"
        )
    ):

        print()

        print(
            "10.6.1 - 10.6.4 already built."
        )

        print("=" * 72)

        print(
            "STAGE 10.6.1 DYNAMIC TEAM ROUTE: BUILT"
        )

        print(
            "STAGE 10.6.2 TEAM IDENTITY HEADER: BUILT"
        )

        print(
            "STAGE 10.6.3 UPCOMING TEAM MATCHES: BUILT"
        )

        print(
            "STAGE 10.6.4 PREDICTION CARDS: BUILT"
        )

        print(
            "VERIFICATION STILL REQUIRED"
        )

        print("=" * 72)

        return


    if (
        TEAM_ROUTE_FILE.exists()
    ):
        raise RuntimeError(
            (
                "Team dynamic route already exists without "
                "matching Stage 10.6 contract. "
                "Refusing to overwrite it."
            )
        )


    (
        next_major,
        next_version,
    ) = detect_next_major()


    async_params = (
        next_major >= 15
    )


    save_text_atomic(
        TEAM_LOADER_FILE,
        TEAM_LOADER_SOURCE,
    )

    save_text_atomic(
        TEAM_RECORDS_FILE,
        TEAM_RECORDS_SOURCE,
    )

    save_text_atomic(
        TEAM_HEADER_FILE,
        TEAM_HEADER_SOURCE,
    )

    save_text_atomic(
        TEAM_UPCOMING_FILE,
        TEAM_UPCOMING_SOURCE,
    )

    save_text_atomic(
        TEAM_PREDICTION_CARD_FILE,
        TEAM_PREDICTION_CARD_SOURCE,
    )


    route_source = build_route_source(
        async_params
    )


    save_text_atomic(
        TEAM_ROUTE_FILE,
        route_source,
    )


    route_sha = sha256_file(
        TEAM_ROUTE_FILE
    )


    protected = {
        "stage10_5_match_route_sha256":
            sha256_file(
                MATCH_DETAIL_ROUTE_FILE
            ),

        "domain_types_sha256":
            sha256_file(
                DOMAIN_TYPES_FILE
            ),

        "mapped_api_sha256":
            sha256_file(
                MAPPED_API_FILE
            ),

        "result_mapping_sha256":
            sha256_file(
                RESULT_FILE
            ),

        "kickoff_formatter_sha256":
            sha256_file(
                KICKOFF_FORMATTER_FILE
            ),

        "probability_formatter_sha256":
            sha256_file(
                PROBABILITY_FORMATTER_FILE
            ),
    }


    route_contract = {
        "stage":
            "10.6.1",

        "version":
            "1.0.0",

        "name":
            "DYNAMIC_TEAM_ROUTE",

        "status":
            "LOCKED",

        "route":
            "/teams/[teamName]",

        "backend_endpoint":
            "/api/v1/intelligence/team/<path:team_name>",

        "mapped_client":
            "getTeamIntelligenceResult",

        "route_source":
            relative(
                TEAM_ROUTE_FILE
            ),

        "loader_source":
            relative(
                TEAM_LOADER_FILE
            ),

        "route_parameter": {
            "name":
                "teamName",

            "domain_type":
                "TeamRouteParams",

            "next_major":
                next_major,

            "next_version":
                next_version,

            "async_params":
                async_params,
        },

        "runtime": {
            "server_component":
                True,

            "force_dynamic":
                True,

            "not_found_mapping":
                True,

            "non_ready_fail_closed":
                True,

            "direct_fetch":
                False,

            "stale_fallback":
                False,

            "provider_access":
                False,

            "artifact_access":
                False,
        },

        "route_page_after_10_6_1_to_10_6_4_sha256":
            route_sha,

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
                MATCH_STATUS_CONTRACT_FILE
            ):
                identity(
                    MATCH_STATUS_CONTRACT_FILE
                ),

            relative(
                DOMAIN_TYPES_FILE
            ):
                identity(
                    DOMAIN_TYPES_FILE
                ),

            relative(
                MAPPED_API_FILE
            ):
                identity(
                    MAPPED_API_FILE
                ),
        },

        "promotion": {
            "stage10_6_1_complete":
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
        ROUTE_CONTRACT_FILE,
        route_contract,
    )


    identity_contract = {
        "stage":
            "10.6.2",

        "version":
            "1.0.0",

        "name":
            "TEAM_IDENTITY_HEADER",

        "status":
            "LOCKED",

        "component_source":
            relative(
                TEAM_HEADER_FILE
            ),

        "identity_source":
            "BACKEND_ACCEPTED_TEAM_ROUTE_IDENTITY",

        "source_field":
            "teamName",

        "presentation": {
            "team_name":
                True,

            "standings":
                False,

            "recent_form":
                False,

            "venue_form":
                False,
        },

        "component_sha256":
            sha256_file(
                TEAM_HEADER_FILE
            ),

        "route_page_sha256":
            route_sha,

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                ROUTE_CONTRACT_FILE
            ):
                identity(
                    ROUTE_CONTRACT_FILE
                ),
        },

        "promotion": {
            "stage10_6_2_complete":
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
        IDENTITY_CONTRACT_FILE,
        identity_contract,
    )


    upcoming_contract = {
        "stage":
            "10.6.3",

        "version":
            "1.0.0",

        "name":
            "TEAM_UPCOMING_MATCHES",

        "status":
            "LOCKED",

        "source_authority":
            "STAGE_9_TEAM_INTELLIGENCE_API",

        "component_source":
            relative(
                TEAM_UPCOMING_FILE
            ),

        "record_source":
            relative(
                TEAM_RECORDS_FILE
            ),

        "presentation": {
            "backend_order_preserved":
                True,

            "frontend_temporal_filtering":
                False,

            "frontend_sorting":
                False,

            "fixture_links":
                False,
        },

        "component_sha256":
            sha256_file(
                TEAM_UPCOMING_FILE
            ),

        "record_source_sha256":
            sha256_file(
                TEAM_RECORDS_FILE
            ),

        "route_page_sha256":
            route_sha,

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                IDENTITY_CONTRACT_FILE
            ):
                identity(
                    IDENTITY_CONTRACT_FILE
                ),
        },

        "promotion": {
            "stage10_6_3_complete":
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
        UPCOMING_CONTRACT_FILE,
        upcoming_contract,
    )


    prediction_contract = {
        "stage":
            "10.6.4",

        "version":
            "1.0.0",

        "name":
            "TEAM_PREDICTION_CARDS",

        "status":
            "LOCKED",

        "authorities": {
            "fixture_identity":
                "STAGE_9_API_JOIN",

            "kickoff":
                "STAGE_9_API_JOIN",

            "probabilities":
                "STAGE_7",

            "predicted_label":
                "STAGE_7",

            "confidence":
                "STAGE_7",

            "confidence_band":
                "STAGE_9",

            "uncertainty_band":
                "STAGE_9",

            "context_alignment":
                "STAGE_9",
        },

        "component_source":
            relative(
                TEAM_PREDICTION_CARD_FILE
            ),

        "source_fields": [
            "fixture_id",
            "date",
            "home_team_name",
            "away_team_name",
            "stage7_prob_home_win",
            "stage7_prob_draw",
            "stage7_prob_away_win",
            "stage7_predicted_label",
            "stage7_confidence",
            "stage9_confidence_band",
            "stage9_uncertainty_band",
            "stage9_context_alignment",
        ],

        "integrity": {
            "transport_string_to_number_only":
                True,

            "probability_recalculation":
                False,

            "probability_normalization":
                False,

            "frontend_argmax":
                False,

            "confidence_band_derivation":
                False,

            "uncertainty_band_derivation":
                False,

            "alignment_derivation":
                False,

            "fixture_links":
                False,
        },

        "component_sha256":
            sha256_file(
                TEAM_PREDICTION_CARD_FILE
            ),

        "record_source_sha256":
            sha256_file(
                TEAM_RECORDS_FILE
            ),

        "route_page_after_10_6_4_sha256":
            route_sha,

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                UPCOMING_CONTRACT_FILE
            ):
                identity(
                    UPCOMING_CONTRACT_FILE
                ),

            relative(
                TEAM_RECORDS_FILE
            ):
                identity(
                    TEAM_RECORDS_FILE
                ),

            relative(
                PROBABILITY_FORMATTER_FILE
            ):
                identity(
                    PROBABILITY_FORMATTER_FILE
                ),

            relative(
                KICKOFF_FORMATTER_FILE
            ):
                identity(
                    KICKOFF_FORMATTER_FILE
                ),
        },

        "promotion": {
            "stage10_6_4_complete":
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
        PREDICTION_CARDS_CONTRACT_FILE,
        prediction_contract,
    )


    print()

    print(
        "Dynamic route:"
    )

    print(
        f"  {relative(TEAM_ROUTE_FILE)}"
    )

    print(
        "Team loader:"
    )

    print(
        f"  {relative(TEAM_LOADER_FILE)}"
    )

    print(
        "Team records:"
    )

    print(
        f"  {relative(TEAM_RECORDS_FILE)}"
    )

    print()

    print(
        "Components:"
    )

    for path in [
        TEAM_HEADER_FILE,
        TEAM_UPCOMING_FILE,
        TEAM_PREDICTION_CARD_FILE,
    ]:

        print(
            f"  {relative(path)}"
        )


    print()

    print("=" * 72)

    print(
        "STAGE 10.6.1 DYNAMIC TEAM ROUTE: BUILT"
    )

    print(
        "STAGE 10.6.2 TEAM IDENTITY HEADER: BUILT"
    )

    print(
        "STAGE 10.6.3 UPCOMING TEAM MATCHES: BUILT"
    )

    print(
        "STAGE 10.6.4 PREDICTION CARDS: BUILT"
    )

    print(
        "VERIFICATION STILL REQUIRED"
    )

    print("=" * 72)


if __name__ == "__main__":
    main()
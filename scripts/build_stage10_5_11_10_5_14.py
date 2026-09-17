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
    / "stage10_5_7_10_5_10_verification.json"
)

RECENT_FORM_CONTRACT_FILE = (
    DOCS
    / "frontend_match_recent_form_contract.json"
)


VENUE_FORM_CONTRACT_FILE = (
    DOCS
    / "frontend_match_venue_form_contract.json"
)

CONTEXT_SUPPORT_CONTRACT_FILE = (
    DOCS
    / "frontend_match_context_support_contract.json"
)

ALIGNMENT_CONTRACT_FILE = (
    DOCS
    / "frontend_match_context_alignment_contract.json"
)

EXPLANATION_CONTRACT_FILE = (
    DOCS
    / "frontend_match_deterministic_explanation_contract.json"
)


ROUTE_PAGE_FILE = (
    FRONTEND
    / "app"
    / "matches"
    / "[fixtureId]"
    / "page.tsx"
)


INTELLIGENCE_RECORD_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "match-intelligence-detail-record.ts"
)


VENUE_FORM_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-venue-form.tsx"
)

CONTEXT_SUPPORT_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-context-support.tsx"
)

ALIGNMENT_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-context-alignment.tsx"
)

EXPLANATION_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-intelligence-explanation.tsx"
)


# Previously verified sources.
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

CONTEXT_RECORD_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "match-context-record.ts"
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


INTELLIGENCE_RECORD_SOURCE = '''import "server-only";

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
'''


VENUE_FORM_COMPONENT_SOURCE = '''type MatchVenueFormProps =
  Readonly<{
    homeTeamName:
      string;

    awayTeamName:
      string;

    homeRecentPoints:
      number;

    awayRecentPoints:
      number;

    homeMatchesAvailable:
      number;

    awayMatchesAvailable:
      number;
  }>;


export function MatchVenueForm({
  homeTeamName,
  awayTeamName,
  homeRecentPoints,
  awayRecentPoints,
  homeMatchesAvailable,
  awayMatchesAvailable,
}: MatchVenueFormProps) {

  return (
    <section
      aria-labelledby="venue-form-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-venue-form"
    >
      <h2
        id="venue-form-heading"
        className="
          text-lg font-bold
          text-slate-950
        "
      >
        Venue form
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
              text-xs font-medium
              uppercase tracking-wide
              text-slate-500
            "
          >
            Home form
          </p>

          <p
            className="
              mt-1 break-words
              text-sm font-semibold
              text-slate-800
            "
          >
            {homeTeamName}
          </p>

          <p
            className="
              mt-3 text-2xl font-bold
              text-slate-950
            "
            data-stage8-field="home_team_home_recent_points"
          >
            {homeRecentPoints}
          </p>

          <p
            className="
              mt-1 text-xs
              text-slate-500
            "
          >
            recent points
          </p>

          <p
            className="
              mt-2 text-xs
              text-slate-500
            "
            data-stage8-field="home_team_home_form_matches_available"
          >
            {homeMatchesAvailable} home matches available
          </p>
        </div>

        <div>
          <p
            className="
              text-xs font-medium
              uppercase tracking-wide
              text-slate-500
            "
          >
            Away form
          </p>

          <p
            className="
              mt-1 break-words
              text-sm font-semibold
              text-slate-800
            "
          >
            {awayTeamName}
          </p>

          <p
            className="
              mt-3 text-2xl font-bold
              text-slate-950
            "
            data-stage8-field="away_team_away_recent_points"
          >
            {awayRecentPoints}
          </p>

          <p
            className="
              mt-1 text-xs
              text-slate-500
            "
          >
            recent points
          </p>

          <p
            className="
              mt-2 text-xs
              text-slate-500
            "
            data-stage8-field="away_team_away_form_matches_available"
          >
            {awayMatchesAvailable} away matches available
          </p>
        </div>
      </div>
    </section>
  );
}
'''


CONTEXT_SUPPORT_COMPONENT_SOURCE = '''import type {
  ContextSupportScore,
} from "../../lib/domain/types";


const signedScoreFormatter =
  new Intl.NumberFormat(
    "en-GB",
    {
      maximumFractionDigits: 0,
      signDisplay: "exceptZero",
    },
  );


type MatchContextSupportProps =
  Readonly<{
    supportScore:
      ContextSupportScore;
  }>;


export function MatchContextSupport({
  supportScore,
}: MatchContextSupportProps) {

  return (
    <section
      aria-labelledby="context-support-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-context-support"
    >
      <h2
        id="context-support-heading"
        className="
          text-base font-bold
          text-slate-950
        "
      >
        Context support
      </h2>

      <p
        className="
          mt-4 text-3xl font-bold
          text-slate-950
        "
        data-stage9-field="stage9_context_support_score"
      >
        {signedScoreFormatter.format(
          supportScore,
        )}
      </p>

      <p
        className="
          mt-2 text-xs leading-5
          text-slate-500
        "
      >
        Stage 9 fixed context score on the
        locked -5 to +5 scale.
      </p>
    </section>
  );
}
'''


ALIGNMENT_COMPONENT_SOURCE = '''import type {
  ContextAlignment,
} from "../../lib/domain/types";


type MatchContextAlignmentProps =
  Readonly<{
    alignment:
      ContextAlignment;
  }>;


export function MatchContextAlignment({
  alignment,
}: MatchContextAlignmentProps) {

  return (
    <section
      aria-labelledby="context-alignment-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-context-alignment"
    >
      <h2
        id="context-alignment-heading"
        className="
          text-base font-bold
          text-slate-950
        "
      >
        Prediction-context alignment
      </h2>

      <p
        className="
          mt-4 text-lg font-semibold
          text-slate-950
        "
        data-stage9-field="stage9_context_alignment"
      >
        {alignment}
      </p>

      <p
        className="
          mt-2 text-xs leading-5
          text-slate-500
        "
      >
        This label comes directly from
        Stage 9 intelligence.
      </p>
    </section>
  );
}
'''


EXPLANATION_COMPONENT_SOURCE = '''type MatchIntelligenceExplanationProps =
  Readonly<{
    headline:
      string;

    summary:
      string;
  }>;


export function MatchIntelligenceExplanation({
  headline,
  summary,
}: MatchIntelligenceExplanationProps) {

  return (
    <section
      aria-labelledby="intelligence-explanation-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-intelligence-explanation"
    >
      <p
        className="
          text-xs font-medium
          uppercase tracking-wide
          text-slate-500
        "
      >
        FixtureIQ explanation
      </p>

      <h2
        id="intelligence-explanation-heading"
        className="
          mt-2 text-lg font-bold
          text-slate-950
        "
        data-stage9-field="stage9_explanation_headline"
      >
        {headline}
      </h2>

      <p
        className="
          mt-4 max-w-3xl
          text-sm leading-7
          text-slate-700
        "
        data-stage9-field="stage9_explanation_summary"
      >
        {summary}
      </p>
    </section>
  );
}
'''


COMPONENT_IMPORTS = '''import {
  MatchVenueForm,
} from "../../../components/matches/match-venue-form";

import {
  MatchContextSupport,
} from "../../../components/matches/match-context-support";

import {
  MatchContextAlignment,
} from "../../../components/matches/match-context-alignment";

import {
  MatchIntelligenceExplanation,
} from "../../../components/matches/match-intelligence-explanation";

'''


RECORD_IMPORT = '''import {
  extractMatchIntelligenceDetailRecord,
} from "../../../lib/matches/match-intelligence-detail-record";

'''


INTELLIGENCE_READ = '''  const intelligence =
    extractMatchIntelligenceDetailRecord(
      result.data,
      fixtureId,
    );


'''


DETAIL_SECTIONS = '''      <div
        className="
          mt-6
        "
      >
        <MatchVenueForm
          homeTeamName={
            header.home_team_name
          }
          awayTeamName={
            header.away_team_name
          }
          homeRecentPoints={
            intelligence.home_team_home_recent_points
          }
          awayRecentPoints={
            intelligence.away_team_away_recent_points
          }
          homeMatchesAvailable={
            intelligence.home_team_home_form_matches_available
          }
          awayMatchesAvailable={
            intelligence.away_team_away_form_matches_available
          }
        />
      </div>

      <div
        className="
          mt-6 grid gap-6
          md:grid-cols-2
        "
      >
        <MatchContextSupport
          supportScore={
            intelligence.stage9_context_support_score
          }
        />

        <MatchContextAlignment
          alignment={
            intelligence.stage9_context_alignment
          }
        />
      </div>

      <div
        className="
          mt-6
        "
      >
        <MatchIntelligenceExplanation
          headline={
            intelligence.stage9_explanation_headline
          }
          summary={
            intelligence.stage9_explanation_summary
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

        "context_record_sha256":
            CONTEXT_RECORD_FILE,

        "prediction_overview_sha256":
            OVERVIEW_COMPONENT_FILE,

        "probability_visualization_sha256":
            PROBABILITY_COMPONENT_FILE,

        "confidence_sha256":
            CONFIDENCE_COMPONENT_FILE,

        "uncertainty_sha256":
            UNCERTAINTY_COMPONENT_FILE,

        "league_position_sha256":
            LEAGUE_POSITION_COMPONENT_FILE,

        "points_sha256":
            POINTS_COMPONENT_FILE,

        "goal_difference_sha256":
            GOAL_DIFFERENCE_COMPONENT_FILE,

        "recent_form_sha256":
            RECENT_FORM_COMPONENT_FILE,

        "domain_types_sha256":
            DOMAIN_TYPES_FILE,

        "mapped_api_sha256":
            MAPPED_API_FILE,

        "result_sha256":
            RESULT_FILE,
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
        "FixtureIQ Stage 10.5.11 - 10.5.14"
    )
    print(
        "VENUE FORM + CONTEXT SUPPORT + ALIGNMENT + EXPLANATION"
    )
    print("=" * 72)


    previous = load_json(
        PREVIOUS_FILE
    )

    recent_form_contract = load_json(
        RECENT_FORM_CONTRACT_FILE
    )


    if (
        previous.get(
            "status"
        )
        !=
        "PASS"
    ):
        raise RuntimeError(
            "10.5.7-10.5.10 verification is not PASS."
        )


    for key in [
        "stage_10_5_7_complete",
        "stage_10_5_8_complete",
        "stage_10_5_9_complete",
        "stage_10_5_10_complete",
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
            "stage10_ready_for_10_5_11"
        )
        is not True
    ):
        raise RuntimeError(
            "10.5.10 did not authorize 10.5.11."
        )


    required = [
        ROUTE_PAGE_FILE,
        HEADER_COMPONENT_FILE,
        HEADER_RECORD_FILE,
        MATCH_LOADER_FILE,
        PREDICTION_RECORD_FILE,
        CONTEXT_RECORD_FILE,
        OVERVIEW_COMPONENT_FILE,
        PROBABILITY_COMPONENT_FILE,
        CONFIDENCE_COMPONENT_FILE,
        UNCERTAINTY_COMPONENT_FILE,
        LEAGUE_POSITION_COMPONENT_FILE,
        POINTS_COMPONENT_FILE,
        GOAL_DIFFERENCE_COMPONENT_FILE,
        RECENT_FORM_COMPONENT_FILE,
        DOMAIN_TYPES_FILE,
        MAPPED_API_FILE,
        RESULT_FILE,
    ]


    for path in required:

        if not path.exists():
            raise RuntimeError(
                f"Missing source: {path}"
            )


    expected_route_sha = (
        recent_form_contract.get(
            "route_page_after_10_5_10_sha256"
        )
    )


    final_contract = optional_json(
        EXPLANATION_CONTRACT_FILE
    )


    if (
        final_contract
        and
        INTELLIGENCE_RECORD_FILE.exists()
        and
        VENUE_FORM_COMPONENT_FILE.exists()
        and
        CONTEXT_SUPPORT_COMPONENT_FILE.exists()
        and
        ALIGNMENT_COMPONENT_FILE.exists()
        and
        EXPLANATION_COMPONENT_FILE.exists()
        and
        sha256_file(
            ROUTE_PAGE_FILE
        )
        ==
        final_contract.get(
            "route_page_after_10_5_14_sha256"
        )
        and
        sha256_file(
            EXPLANATION_COMPONENT_FILE
        )
        ==
        final_contract.get(
            "component_sha256"
        )
    ):

        print()
        print(
            "10.5.11 - 10.5.14 already built."
        )

        print("=" * 72)
        print(
            "STAGE 10.5.11 VENUE FORM: BUILT"
        )
        print(
            "STAGE 10.5.12 CONTEXT SUPPORT: BUILT"
        )
        print(
            "STAGE 10.5.13 ALIGNMENT: BUILT"
        )
        print(
            "STAGE 10.5.14 DETERMINISTIC EXPLANATION: BUILT"
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
                "verified 10.5.10 output."
            )
        )


    route_before_sha = (
        sha256_file(
            ROUTE_PAGE_FILE
        )
    )


    save_text_atomic(
        INTELLIGENCE_RECORD_FILE,
        INTELLIGENCE_RECORD_SOURCE,
    )

    save_text_atomic(
        VENUE_FORM_COMPONENT_FILE,
        VENUE_FORM_COMPONENT_SOURCE,
    )

    save_text_atomic(
        CONTEXT_SUPPORT_COMPONENT_FILE,
        CONTEXT_SUPPORT_COMPONENT_SOURCE,
    )

    save_text_atomic(
        ALIGNMENT_COMPONENT_FILE,
        ALIGNMENT_COMPONENT_SOURCE,
    )

    save_text_atomic(
        EXPLANATION_COMPONENT_FILE,
        EXPLANATION_COMPONENT_SOURCE,
    )


    route_source = (
        ROUTE_PAGE_FILE.read_text(
            encoding="utf-8"
        )
    )


    recent_form_import = '''import {
  MatchRecentForm,
} from "../../../components/matches/match-recent-form";

'''


    route_source = replace_once(
        route_source,
        recent_form_import,
        (
            recent_form_import
            +
            COMPONENT_IMPORTS
        ),
        "10.5.11-10.5.14 component imports",
    )


    context_record_import = '''import {
  extractMatchContextRecord,
} from "../../../lib/matches/match-context-record";

'''


    route_source = replace_once(
        route_source,
        context_record_import,
        (
            context_record_import
            +
            RECORD_IMPORT
        ),
        "Stage 9 detail record import",
    )


    return_anchor = '''  return (
    <article
'''


    route_source = replace_once(
        route_source,
        return_anchor,
        (
            INTELLIGENCE_READ
            +
            return_anchor
        ),
        "Stage 9 detail extraction",
    )


    article_close = '''    </article>
'''


    route_source = replace_once(
        route_source,
        article_close,
        (
            DETAIL_SECTIONS
            +
            article_close
        ),
        "10.5.11-10.5.14 detail sections",
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


    protected = protected_state()


    venue_contract = {
        "stage":
            "10.5.11",

        "version":
            "1.0.0",

        "name":
            "MATCH_VENUE_FORM",

        "status":
            "LOCKED",

        "source_authority":
            "STAGE_8_CONTEXT",

        "transport_path":
            "STAGE_9_INTELLIGENCE_API_JOIN",

        "component_source":
            relative(
                VENUE_FORM_COMPONENT_FILE
            ),

        "record_source":
            relative(
                INTELLIGENCE_RECORD_FILE
            ),

        "source_fields": [
            "home_team_home_form_matches_available",
            "home_team_home_recent_points",
            "away_team_away_form_matches_available",
            "away_team_away_recent_points",
        ],

        "presentation": {
            "home_home_form_direct":
                True,

            "away_away_form_direct":
                True,

            "venue_gap_calculated_frontend":
                False,

            "stage9_venue_gap_consumed":
                False,
        },

        "component_sha256":
            sha256_file(
                VENUE_FORM_COMPONENT_FILE
            ),

        "record_source_sha256":
            sha256_file(
                INTELLIGENCE_RECORD_FILE
            ),

        "route_page_before_10_5_11_sha256":
            route_before_sha,

        "route_page_after_10_5_11_to_10_5_14_sha256":
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
                RECENT_FORM_CONTRACT_FILE
            ):
                identity(
                    RECENT_FORM_CONTRACT_FILE
                ),
        },

        "promotion": {
            "stage10_5_11_complete":
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
        VENUE_FORM_CONTRACT_FILE,
        venue_contract,
    )


    context_support_contract = {
        "stage":
            "10.5.12",

        "version":
            "1.0.0",

        "name":
            "MATCH_CONTEXT_SUPPORT",

        "status":
            "LOCKED",

        "source_authority":
            "STAGE_9_INTELLIGENCE",

        "component_source":
            relative(
                CONTEXT_SUPPORT_COMPONENT_FILE
            ),

        "source_field":
            "stage9_context_support_score",

        "score_contract": {
            "minimum":
                -5,

            "maximum":
                5,

            "frontend_recalculation":
                False,

            "frontend_signal_counting":
                False,
        },

        "component_sha256":
            sha256_file(
                CONTEXT_SUPPORT_COMPONENT_FILE
            ),

        "route_page_after_10_5_12_sha256":
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
        },

        "promotion": {
            "stage10_5_12_complete":
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
        CONTEXT_SUPPORT_CONTRACT_FILE,
        context_support_contract,
    )


    alignment_contract = {
        "stage":
            "10.5.13",

        "version":
            "1.0.0",

        "name":
            "MATCH_CONTEXT_ALIGNMENT",

        "status":
            "LOCKED",

        "source_authority":
            "STAGE_9_INTELLIGENCE",

        "component_source":
            relative(
                ALIGNMENT_COMPONENT_FILE
            ),

        "source_field":
            "stage9_context_alignment",

        "allowed_values_authority":
            "CONTEXT_ALIGNMENTS_DOMAIN_CONSTANT",

        "presentation": {
            "direct_source_label":
                True,

            "frontend_alignment_rules":
                False,

            "frontend_support_interpretation":
                False,
        },

        "component_sha256":
            sha256_file(
                ALIGNMENT_COMPONENT_FILE
            ),

        "route_page_after_10_5_13_sha256":
            route_after_sha,

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                CONTEXT_SUPPORT_CONTRACT_FILE
            ):
                identity(
                    CONTEXT_SUPPORT_CONTRACT_FILE
                ),
        },

        "promotion": {
            "stage10_5_13_complete":
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
        ALIGNMENT_CONTRACT_FILE,
        alignment_contract,
    )


    explanation_contract = {
        "stage":
            "10.5.14",

        "version":
            "1.0.0",

        "name":
            "MATCH_DETERMINISTIC_EXPLANATION",

        "status":
            "LOCKED",

        "source_authority":
            "STAGE_9_INTELLIGENCE",

        "component_source":
            relative(
                EXPLANATION_COMPONENT_FILE
            ),

        "source_fields": [
            "stage9_explanation_headline",
            "stage9_explanation_summary",
        ],

        "rule_authority":
            "STAGE9_5_DETERMINISTIC_EXPLANATION_V1",

        "presentation": {
            "headline_verbatim":
                True,

            "summary_verbatim":
                True,

            "frontend_generation":
                False,

            "frontend_rewrite":
                False,

            "frontend_truncation":
                False,

            "llm_usage":
                False,

            "fallback_explanation":
                False,
        },

        "component_sha256":
            sha256_file(
                EXPLANATION_COMPONENT_FILE
            ),

        "record_source_sha256":
            sha256_file(
                INTELLIGENCE_RECORD_FILE
            ),

        "route_page_after_10_5_14_sha256":
            route_after_sha,

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                ALIGNMENT_CONTRACT_FILE
            ):
                identity(
                    ALIGNMENT_CONTRACT_FILE
                ),

            relative(
                INTELLIGENCE_RECORD_FILE
            ):
                identity(
                    INTELLIGENCE_RECORD_FILE
                ),
        },

        "promotion": {
            "stage10_5_14_complete":
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
        EXPLANATION_CONTRACT_FILE,
        explanation_contract,
    )


    print()
    print(
        "Stage 9 detail record:"
    )
    print(
        f"  {relative(INTELLIGENCE_RECORD_FILE)}"
    )

    print()
    print(
        "Components:"
    )

    for path in [
        VENUE_FORM_COMPONENT_FILE,
        CONTEXT_SUPPORT_COMPONENT_FILE,
        ALIGNMENT_COMPONENT_FILE,
        EXPLANATION_COMPONENT_FILE,
    ]:
        print(
            f"  {relative(path)}"
        )


    print()
    print("=" * 72)

    print(
        "STAGE 10.5.11 VENUE FORM: BUILT"
    )
    print(
        "STAGE 10.5.12 CONTEXT SUPPORT: BUILT"
    )
    print(
        "STAGE 10.5.13 ALIGNMENT: BUILT"
    )
    print(
        "STAGE 10.5.14 DETERMINISTIC EXPLANATION: BUILT"
    )
    print(
        "VERIFICATION STILL REQUIRED"
    )

    print("=" * 72)


if __name__ == "__main__":
    main()
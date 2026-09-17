from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FRONTEND = ROOT / "frontend"
APP_ROOT = FRONTEND / "app"

DOCS = ROOT / "docs" / "stage10"

FRONTEND_DATA = (
    ROOT
    / "data"
    / "processed"
    / "frontend"
)


PREVIOUS_FILE = (
    FRONTEND_DATA
    / "stage10_4_9_10_4_10_verification.json"
)

EXPLANATION_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_explanation_preview_contract.json"
)

LOADER_CONTRACT_FILE = (
    DOCS
    / "frontend_upcoming_dashboard_loader_contract.json"
)

DETAIL_LINK_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_detail_link_contract.json"
)

DASHBOARD_CONTRACT_FILE = (
    DOCS
    / "frontend_upcoming_dashboard_contract.json"
)


MATCH_CARD_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-card.tsx"
)

PAGE_FILE = (
    FRONTEND
    / "app"
    / "page.tsx"
)

LOADER_FILE = (
    FRONTEND
    / "lib"
    / "dashboard"
    / "load-upcoming-matches.ts"
)

EXTRACTOR_FILE = (
    FRONTEND
    / "lib"
    / "dashboard"
    / "upcoming-records.ts"
)

DOMAIN_TYPES_FILE = (
    FRONTEND
    / "lib"
    / "domain"
    / "types.ts"
)

VALIDATION_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "validation.ts"
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


ROOT_PAGE_RELATIVE = (
    "frontend/app/page.tsx"
)


DETAIL_LINK_SECTION = '''        <div
          className="
            border-t border-slate-100
            pt-5
          "
        >
          <Link
            href={`/matches/${encodeURIComponent(
              String(fixtureId),
            )}`}
            className="
              inline-flex items-center
              text-sm font-semibold
              text-slate-900
              underline-offset-4
              hover:underline
              focus-visible:outline-none
              focus-visible:ring-2
              focus-visible:ring-slate-400
              focus-visible:ring-offset-2
            "
          >
            View match intelligence
          </Link>
        </div>

'''


EXTRACTOR_TEMPLATE = '''import "server-only";

import {
  CONTEXT_ALIGNMENTS,
  FIVE_LEVEL_BANDS,
  OUTCOME_LABELS,
} from "../domain/types";

import type {
  ConfidenceBand,
  ContextAlignment,
  ContextSupportScore,
  FixtureId,
  MatchIntelligence,
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


export type UpcomingDashboardMatch =
  Readonly<
    MatchIntelligence
    &
    {
      kickoffUtc:
        string;
    }
  >;


export const UPCOMING_KICKOFF_SOURCE_FIELD =
  "__KICKOFF_FIELD__" as const;


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


function isProbability(
  value: JsonValue | undefined,
): value is number {

  return (
    typeof value === "number"
    &&
    Number.isFinite(
      value,
    )
    &&
    value >= 0
    &&
    value <= 1
  );
}


function isOutcomeLabel(
  value: JsonValue | undefined,
): value is OutcomeLabel {

  return (
    typeof value === "string"
    &&
    outcomeLabels.has(
      value,
    )
  );
}


function isConfidenceBand(
  value: JsonValue | undefined,
): value is ConfidenceBand {

  return (
    typeof value === "string"
    &&
    fiveLevelBands.has(
      value,
    )
  );
}


function isUncertaintyBand(
  value: JsonValue | undefined,
): value is UncertaintyBand {

  return (
    typeof value === "string"
    &&
    fiveLevelBands.has(
      value,
    )
  );
}


function isContextAlignment(
  value: JsonValue | undefined,
): value is ContextAlignment {

  return (
    typeof value === "string"
    &&
    contextAlignments.has(
      value,
    )
  );
}


function isContextSupportScore(
  value: JsonValue | undefined,
): value is ContextSupportScore {

  return (
    typeof value === "number"
    &&
    Number.isInteger(
      value,
    )
    &&
    value >= -5
    &&
    value <= 5
  );
}


function isFiniteNumber(
  value: JsonValue | undefined,
): value is number {

  return (
    typeof value === "number"
    &&
    Number.isFinite(
      value,
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
      `Invalid dashboard field: ${field}`,
    );
  }

  return value;
}


function looksLikeMatch(
  value: JsonObject,
): boolean {

  return (
    "fixture_id"
    in value
    &&
    "stage7_prob_home_win"
    in value
    &&
    "stage9_context_alignment"
    in value
  );
}



const NUMERIC_TRANSPORT_FIELDS =
  new Set<string>(
    [
      "stage7_prob_home_win",
      "stage7_prob_draw",
      "stage7_prob_away_win",
      "stage7_confidence",
      "stage9_top_probability",
      "stage9_probability_margin",
      "stage9_context_support_score",
    ],
  );


function normalizeTransportRecord(
  value: JsonObject,
): JsonObject {

  const normalized: {
    [key: string]:
      JsonValue;
  } = {
    ...value,
  };


  for (
    const field
    of
    NUMERIC_TRANSPORT_FIELDS
  ) {

    const current =
      normalized[
        field
      ];


    if (
      typeof current === "string"
      &&
      current.trim().length > 0
    ) {

      const parsed =
        Number(
          current,
        );


      if (
        Number.isFinite(
          parsed,
        )
      ) {

        normalized[
          field
        ] = parsed;
      }
    }
  }


  return normalized;
}


function parseMatch(
  value: JsonObject,
): UpcomingDashboardMatch {

  const fixtureId =
    value.fixture_id;

  const homeTeamName =
    value.home_team_name;

  const awayTeamName =
    value.away_team_name;

  const probHome =
    value.stage7_prob_home_win;

  const probDraw =
    value.stage7_prob_draw;

  const probAway =
    value.stage7_prob_away_win;

  const predictedLabel =
    value.stage7_predicted_label;

  const confidence =
    value.stage7_confidence;

  const topProbability =
    value.stage9_top_probability;

  const probabilityMargin =
    value.stage9_probability_margin;

  const confidenceBand =
    value.stage9_confidence_band;

  const uncertaintyBand =
    value.stage9_uncertainty_band;

  const supportScore =
    value.stage9_context_support_score;

  const alignment =
    value.stage9_context_alignment;

  const headline =
    value.stage9_explanation_headline;

  const summary =
    value.stage9_explanation_summary;

  const kickoff =
    value[
      UPCOMING_KICKOFF_SOURCE_FIELD
    ];


  if (
    !isFixtureId(
      fixtureId,
    )
  ) {
    throw new TypeError(
      "Invalid dashboard fixture_id.",
    );
  }


  if (
    !isProbability(
      probHome,
    )
    ||
    !isProbability(
      probDraw,
    )
    ||
    !isProbability(
      probAway,
    )
    ||
    !isProbability(
      confidence,
    )
    ||
    !isProbability(
      topProbability,
    )
  ) {
    throw new TypeError(
      "Invalid dashboard probability field.",
    );
  }


  if (
    !isFiniteNumber(
      probabilityMargin,
    )
    ||
    probabilityMargin < 0
    ||
    probabilityMargin > 1
  ) {
    throw new TypeError(
      "Invalid dashboard probability margin.",
    );
  }


  if (
    !isOutcomeLabel(
      predictedLabel,
    )
  ) {
    throw new TypeError(
      "Invalid dashboard outcome label.",
    );
  }


  if (
    !isConfidenceBand(
      confidenceBand,
    )
    ||
    !isUncertaintyBand(
      uncertaintyBand,
    )
  ) {
    throw new TypeError(
      "Invalid dashboard intelligence band.",
    );
  }


  if (
    !isContextSupportScore(
      supportScore,
    )
  ) {
    throw new TypeError(
      "Invalid dashboard context support score.",
    );
  }


  if (
    !isContextAlignment(
      alignment,
    )
  ) {
    throw new TypeError(
      "Invalid dashboard context alignment.",
    );
  }


  const kickoffUtc =
    requireString(
      kickoff,
      UPCOMING_KICKOFF_SOURCE_FIELD,
    );


  if (
    Number.isNaN(
      Date.parse(
        kickoffUtc,
      ),
    )
  ) {
    throw new TypeError(
      "Invalid dashboard kickoff timestamp.",
    );
  }


  return {
    fixture_id:
      fixtureId,

    home_team_name:
      requireString(
        homeTeamName,
        "home_team_name",
      ),

    away_team_name:
      requireString(
        awayTeamName,
        "away_team_name",
      ),

    stage7_prob_home_win:
      probHome,

    stage7_prob_draw:
      probDraw,

    stage7_prob_away_win:
      probAway,

    stage7_predicted_label:
      predictedLabel,

    stage7_confidence:
      confidence,

    stage9_top_probability:
      topProbability,

    stage9_probability_margin:
      probabilityMargin,

    stage9_confidence_band:
      confidenceBand,

    stage9_uncertainty_band:
      uncertaintyBand,

    stage9_context_support_score:
      supportScore,

    stage9_context_alignment:
      alignment,

    stage9_explanation_headline:
      requireString(
        headline,
        "stage9_explanation_headline",
      ),

    stage9_explanation_summary:
      requireString(
        summary,
        "stage9_explanation_summary",
      ),

    kickoffUtc,
  };
}


function collectMatches(
  value: JsonValue,
  output:
    UpcomingDashboardMatch[],
  seen:
    Set<string>,
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
      collectMatches(
        item,
        output,
        seen,
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
    looksLikeMatch(
      value,
    )
  ) {

    const match =
      parseMatch(
        normalizeTransportRecord(
          value,
        ),
      );


    const identity =
      `${typeof match.fixture_id}:${
        String(
          match.fixture_id,
        )
      }`;


    if (
      seen.has(
        identity,
      )
    ) {
      throw new Error(
        "Duplicate fixture_id in upcoming intelligence response.",
      );
    }


    seen.add(
      identity,
    );

    output.push(
      match,
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
    collectMatches(
      child,
      output,
      seen,
    );
  }
}


export function extractUpcomingDashboardMatches(
  data: JsonValue,
): readonly UpcomingDashboardMatch[] {

  const output:
    UpcomingDashboardMatch[] =
      [];

  const seen =
    new Set<string>();


  collectMatches(
    data,
    output,
    seen,
  );


  return output;
}
'''


PAGE_SOURCE = '''import {
  MatchCard,
} from "../components/matches/match-card";

import {
  loadUpcomingMatches,
} from "../lib/dashboard/load-upcoming-matches";

import {
  extractUpcomingDashboardMatches,
} from "../lib/dashboard/upcoming-records";


export const dynamic =
  "force-dynamic";


export default async function Home() {

  const result =
    await loadUpcomingMatches();


  if (
    result.state !==
    "READY"
  ) {

    return (
      <section
        aria-labelledby="upcoming-heading"
        data-fixtureiq-dashboard-state={
          result.state
        }
      >
        <h1
          id="upcoming-heading"
          className="
            text-2xl font-bold
            tracking-tight text-slate-950
            sm:text-3xl
          "
        >
          Upcoming matches
        </h1>

        <p
          className="
            mt-3 max-w-2xl
            text-sm leading-6
            text-slate-600
          "
        >
          Upcoming match intelligence is
          currently unavailable.
        </p>
      </section>
    );
  }


  const matches =
    extractUpcomingDashboardMatches(
      result.data,
    );


  if (
    matches.length === 0
  ) {

    return (
      <section
        aria-labelledby="upcoming-heading"
        data-fixtureiq-dashboard-state="READY"
        data-fixtureiq-dashboard-empty="true"
      >
        <h1
          id="upcoming-heading"
          className="
            text-2xl font-bold
            tracking-tight text-slate-950
            sm:text-3xl
          "
        >
          Upcoming matches
        </h1>

        <p
          className="
            mt-3 text-sm
            text-slate-600
          "
        >
          No upcoming matches are available.
        </p>
      </section>
    );
  }


  return (
    <section
      aria-labelledby="upcoming-heading"
      data-fixtureiq-dashboard-state="READY"
    >
      <header
        className="
          mb-8
        "
      >
        <p
          className="
            text-sm font-semibold
            uppercase tracking-wide
            text-slate-500
          "
        >
          Premier League
        </p>

        <h1
          id="upcoming-heading"
          className="
            mt-2 text-2xl font-bold
            tracking-tight text-slate-950
            sm:text-3xl
          "
        >
          Upcoming matches
        </h1>

        <p
          className="
            mt-3 max-w-2xl
            text-sm leading-6
            text-slate-600
          "
        >
          Prediction probabilities and
          match intelligence from FixtureIQ.
        </p>
      </header>

      <div
        className="
          grid gap-6
          lg:grid-cols-2
        "
      >
        {matches.map(
          (match) => (
            <MatchCard
              key={
                String(
                  match.fixture_id,
                )
              }
              fixtureId={
                match.fixture_id
              }
              homeTeamName={
                match.home_team_name
              }
              awayTeamName={
                match.away_team_name
              }
              kickoffUtc={
                match.kickoffUtc
              }
              stage7_prob_home_win={
                match.stage7_prob_home_win
              }
              stage7_prob_draw={
                match.stage7_prob_draw
              }
              stage7_prob_away_win={
                match.stage7_prob_away_win
              }
              stage7_predicted_label={
                match.stage7_predicted_label
              }
              stage7_confidence={
                match.stage7_confidence
              }
              confidence_band={
                match.stage9_confidence_band
              }
              uncertainty_band={
                match.stage9_uncertainty_band
              }
              context_alignment={
                match.stage9_context_alignment
              }
              explanation_headline={
                match.stage9_explanation_headline
              }
              explanation_summary={
                match.stage9_explanation_summary
              }
            />
          ),
        )}
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
        payload = json.load(file)

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

    return load_json(path)


def sha256_file(
    path: Path,
) -> str:

    digest = hashlib.sha256()

    with path.open("rb") as file:

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
            sha256_file(path)
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


def current_route_pages() -> dict:

    output = {}

    for path in sorted(
        APP_ROOT.rglob(
            "page.tsx"
        )
    ):

        output[
            relative(path)
        ] = {
            "sha256":
                sha256_file(path)
        }

    return output


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
                f"{label}: "
                f"expected one anchor, "
                f"found {count}."
            )
        )

    return source.replace(
        old,
        new,
        1,
    )


def ensure_domain_import(
    source: str,
    type_name: str,
) -> str:

    pattern = re.compile(
        (
            r'import\s+type\s*\{'
            r'(?P<body>[^}]*)'
            r'\}\s*from\s*'
            r'["\']\.\./\.\./lib/domain/types["\'];'
        )
    )

    matches = list(
        pattern.finditer(
            source
        )
    )

    if len(matches) != 1:

        raise RuntimeError(
            "Expected one MatchCard domain type import."
        )

    match = matches[0]

    names = re.findall(
        r"\b[A-Za-z_$][A-Za-z0-9_$]*\b",
        match.group(
            "body"
        ),
    )

    if type_name in names:
        return source

    names.append(
        type_name
    )

    replacement = (
        "import type {\n"
        +
        "".join(
            f"  {name},\n"
            for name in names
        )
        +
        '} from "../../lib/domain/types";'
    )

    return (
        source[
            :match.start()
        ]
        +
        replacement
        +
        source[
            match.end():
        ]
    )


def add_next_link_import(
    source: str,
) -> str:

    if (
        'from "next/link"'
        in source
        or
        "from 'next/link'"
        in source
    ):
        return source

    react_pattern = re.compile(
        (
            r'import\s+type\s*\{'
            r'[^}]*'
            r'\}\s*from\s*'
            r'["\']react["\'];'
        )
    )

    match = react_pattern.search(
        source
    )

    if match is None:

        raise RuntimeError(
            "ReactNode import not found."
        )

    insertion = (
        match.group(0)
        +
        '\n\nimport Link from "next/link";'
    )

    return (
        source[
            :match.start()
        ]
        +
        insertion
        +
        source[
            match.end():
        ]
    )


def add_detail_link(
    source: str,
) -> str:

    updated = (
        add_next_link_import(
            source
        )
    )

    updated = (
        ensure_domain_import(
            updated,
            "FixtureId",
        )
    )

    updated = replace_once(
        updated,
        (
            "  Readonly<{\n"
            "    homeTeamName: string;\n"
        ),
        (
            "  Readonly<{\n"
            "    fixtureId: FixtureId;\n"
            "    homeTeamName: string;\n"
        ),
        "fixtureId prop",
    )

    updated = replace_once(
        updated,
        (
            "export function MatchCard({\n"
            "  homeTeamName,\n"
        ),
        (
            "export function MatchCard({\n"
            "  fixtureId,\n"
            "  homeTeamName,\n"
        ),
        "fixtureId destructuring",
    )

    updated = replace_once(
        updated,
        "        {children ? (\n",
        (
            DETAIL_LINK_SECTION
            +
            "        {children ? (\n"
        ),
        "detail link section",
    )

    return updated


def discover_kickoff_field(
    source: str,
) -> tuple[
    str,
    list[str],
]:

    start = source.find(
        "function validateIntelligenceRecord("
    )

    end = source.find(
        "export function validateIntelligenceApiPayload",
        start,
    )

    if (
        start < 0
        or
        end < 0
    ):
        raise RuntimeError(
            (
                "Could not locate "
                "validateIntelligenceRecord()."
            )
        )

    body = source[
        start:
        end
    ]

    fields = list(
        dict.fromkeys(
            re.findall(
                (
                    r"\bvalue\."
                    r"([A-Za-z_$][A-Za-z0-9_$]*)"
                ),
                body,
            )
        )
    )

    preferred = [
        "date",
        "kickoff_utc",
        "kickoff",
        "utc_date",
        "match_date",
        "fixture_date",
    ]

    for field in preferred:

        if field in fields:

            return (
                field,
                fields,
            )

    semantic = [
        field
        for field in fields
        if (
            "kickoff"
            in field.lower()
            or
            (
                "fixture"
                in field.lower()
                and
                "date"
                in field.lower()
            )
        )
    ]

    if len(
        semantic
    ) == 1:

        return (
            semantic[0],
            fields,
        )

    # Stage 9 `/api/v1/intelligence/upcoming`
    # is the authoritative intelligence API.
    #
    # Its verified runtime payload exposes the fixture kickoff
    # as `date`. Stage 10.2.6 predates kickoff presentation and
    # therefore does not validate that field explicitly.
    #
    # Keep the fallback exact and fail closed for any unrelated
    # validator shape.
    if (
        "fixture_id"
        in
        fields
        and
        "home_team_name"
        in
        fields
        and
        "away_team_name"
        in
        fields
        and
        "stage7_prob_home_win"
        in
        fields
        and
        "stage9_context_alignment"
        in
        fields
    ):
        return (
            "date",
            fields,
        )

    raise RuntimeError(
        (
            "Could not lock the Stage 9 "
            "kickoff source field. "
            f"Validated fields: {fields}"
        )
    )


def non_root_pages(
    pages: dict,
) -> dict:

    return {
        key:
            value

        for key, value
        in pages.items()

        if key
        !=
        ROOT_PAGE_RELATIVE
    }


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.4.11 + 10.4.12"
    )

    print(
        "DETAIL LINKS + DASHBOARD ASSEMBLY BUILD"
    )

    print("=" * 72)


    previous = load_json(
        PREVIOUS_FILE
    )

    explanation_contract = load_json(
        EXPLANATION_CONTRACT_FILE
    )

    loader_contract = load_json(
        LOADER_CONTRACT_FILE
    )


    if (
        previous.get(
            "status"
        )
        !=
        "PASS"
    ):
        raise RuntimeError(
            "10.4.9/10.4.10 verification is not PASS."
        )


    if (
        previous.get(
            "stage_10_4_9_complete"
        )
        is not True
        or
        previous.get(
            "stage_10_4_10_complete"
        )
        is not True
    ):
        raise RuntimeError(
            "10.4.9/10.4.10 are not complete."
        )


    if (
        previous.get(
            "stage10_ready_for_10_4_11"
        )
        is not True
    ):
        raise RuntimeError(
            "10.4.10 did not authorize 10.4.11."
        )


    required_sources = [
        MATCH_CARD_FILE,
        PAGE_FILE,
        LOADER_FILE,
        DOMAIN_TYPES_FILE,
        VALIDATION_FILE,
        MAPPED_API_FILE,
        RESULT_FILE,
        KICKOFF_FORMATTER_FILE,
        PROBABILITY_FORMATTER_FILE,
    ]


    for path in required_sources:

        if not path.exists():

            raise RuntimeError(
                f"Missing source: {path}"
            )


    protected = (
        explanation_contract.get(
            "protected_state",
            {},
        )
    )

    expected_pages = protected.get(
        "route_page_identity",
        {},
    )


    if (
        not isinstance(
            expected_pages,
            dict,
        )
        or
        not expected_pages
    ):
        raise RuntimeError(
            "10.4.10 protected route identity missing."
        )


    current_pages_before = (
        current_route_pages()
    )


    if (
        current_pages_before
        !=
        expected_pages
    ):
        raise RuntimeError(
            (
                "Route pages changed after "
                "10.4.10."
            )
        )


    if (
        sha256_file(
            LOADER_FILE
        )
        !=
        loader_contract.get(
            "source_sha256"
        )
    ):
        raise RuntimeError(
            "Dashboard loader changed."
        )


    validation_source = (
        VALIDATION_FILE.read_text(
            encoding="utf-8"
        )
    )


    (
        kickoff_field,
        validated_fields,
    ) = discover_kickoff_field(
        validation_source
    )


    print()

    print(
        "Validated kickoff source field:"
    )

    print(
        f"  {kickoff_field}"
    )


    existing_detail = optional_json(
        DETAIL_LINK_CONTRACT_FILE
    )

    existing_dashboard = optional_json(
        DASHBOARD_CONTRACT_FILE
    )


    # ========================================================
    # Fully built
    # ========================================================

    if (
        existing_dashboard
        and
        EXTRACTOR_FILE.exists()
        and
        sha256_file(
            MATCH_CARD_FILE
        )
        ==
        existing_dashboard.get(
            "match_card_sha256"
        )
        and
        sha256_file(
            PAGE_FILE
        )
        ==
        existing_dashboard.get(
            "page_after_dashboard_sha256"
        )
        and
        sha256_file(
            EXTRACTOR_FILE
        )
        ==
        existing_dashboard.get(
            "extractor_sha256"
        )
    ):

        print()

        print(
            "10.4.11 / 10.4.12 assembly already built."
        )

        print("=" * 72)

        print(
            "STAGE 10.4.11 DETAIL LINKS: BUILT"
        )

        print(
            "STAGE 10.4.12 DASHBOARD ASSEMBLY: BUILT"
        )

        print(
            "FINAL VERIFICATION STILL REQUIRED"
        )

        print("=" * 72)

        return


    # ========================================================
    # Stage 10.4.11
    # ========================================================

    current_card_sha = sha256_file(
        MATCH_CARD_FILE
    )


    if (
        existing_detail
        and
        current_card_sha
        ==
        existing_detail.get(
            "match_card_after_detail_link_sha256"
        )
    ):

        detail_contract = (
            existing_detail
        )

        print()

        print(
            "10.4.11 detail link already built."
        )

    else:

        expected_card_sha = (
            explanation_contract.get(
                "match_card_after_explanation_sha256"
            )
        )


        if (
            current_card_sha
            !=
            expected_card_sha
        ):
            raise RuntimeError(
                (
                    "MatchCard no longer matches "
                    "verified 10.4.10 output."
                )
            )


        before_card_sha = (
            current_card_sha
        )


        card_source = (
            MATCH_CARD_FILE.read_text(
                encoding="utf-8"
            )
        )


        updated_card = (
            add_detail_link(
                card_source
            )
        )


        save_text_atomic(
            MATCH_CARD_FILE,
            updated_card,
        )


        after_card_sha = sha256_file(
            MATCH_CARD_FILE
        )


        detail_contract = {
            "stage":
                "10.4.11",

            "version":
                "1.0.0",

            "name":
                "MATCH_DETAIL_LINK",

            "status":
                "LOCKED",

            "source":
                relative(
                    MATCH_CARD_FILE
                ),

            "route_contract":
                "/matches/[fixtureId]",

            "source_field":
                "fixtureId",

            "domain_type":
                "FixtureId",

            "implementation": {
                "next_link":
                    True,

                "encodeURIComponent":
                    True,

                "String":
                    True,

                "server_component":
                    True,

                "api_access":
                    False,

                "prediction_logic":
                    False,

                "navigation_only":
                    True,
            },

            "transition": {
                "match_card_before_detail_link_sha256":
                    before_card_sha,

                "match_card_after_detail_link_sha256":
                    after_card_sha,
            },

            "match_card_after_detail_link_sha256":
                after_card_sha,

            "protected_state": {
                "route_page_identity_before_dashboard":
                    expected_pages,

                "loader_sha256":
                    sha256_file(
                        LOADER_FILE
                    ),

                "domain_types_sha256":
                    sha256_file(
                        DOMAIN_TYPES_FILE
                    ),

                "validation_sha256":
                    sha256_file(
                        VALIDATION_FILE
                    ),

                "mapped_api_sha256":
                    sha256_file(
                        MAPPED_API_FILE
                    ),

                "result_sha256":
                    sha256_file(
                        RESULT_FILE
                    ),
            },

            "dependency_identity": {
                relative(
                    PREVIOUS_FILE
                ):
                    identity(
                        PREVIOUS_FILE
                    ),

                relative(
                    EXPLANATION_CONTRACT_FILE
                ):
                    identity(
                        EXPLANATION_CONTRACT_FILE
                    ),

                relative(
                    DOMAIN_TYPES_FILE
                ):
                    identity(
                        DOMAIN_TYPES_FILE
                    ),
            },

            "promotion": {
                "stage10_4_11_complete":
                    False,

                "stage10_4_complete":
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
            DETAIL_LINK_CONTRACT_FILE,
            detail_contract,
        )


    # ========================================================
    # Stage 10.4.12 dashboard assembly
    # ========================================================

    page_before_sha = (
        sha256_file(
            PAGE_FILE
        )
    )


    expected_root_page = (
        expected_pages.get(
            ROOT_PAGE_RELATIVE,
            {},
        )
        .get(
            "sha256"
        )
    )


    if (
        page_before_sha
        !=
        expected_root_page
    ):
        raise RuntimeError(
            (
                "Root page does not match "
                "the verified pre-dashboard state."
            )
        )


    extractor_source = (
        EXTRACTOR_TEMPLATE.replace(
            "__KICKOFF_FIELD__",
            kickoff_field,
        )
    )


    save_text_atomic(
        EXTRACTOR_FILE,
        extractor_source,
    )


    save_text_atomic(
        PAGE_FILE,
        PAGE_SOURCE,
    )


    pages_after = (
        current_route_pages()
    )


    if (
        non_root_pages(
            pages_after
        )
        !=
        non_root_pages(
            expected_pages
        )
    ):
        raise RuntimeError(
            (
                "A non-root route page changed "
                "during dashboard assembly."
            )
        )


    if (
        sha256_file(
            LOADER_FILE
        )
        !=
        loader_contract.get(
            "source_sha256"
        )
    ):
        raise RuntimeError(
            "Dashboard loader changed during assembly."
        )


    dashboard_contract = {
        "stage":
            "10.4.12",

        "version":
            "1.0.0",

        "name":
            "UPCOMING_MATCHES_DASHBOARD_ASSEMBLY",

        "status":
            "LOCKED_ASSEMBLY",

        "page_source":
            relative(
                PAGE_FILE
            ),

        "extractor_source":
            relative(
                EXTRACTOR_FILE
            ),

        "match_card_source":
            relative(
                MATCH_CARD_FILE
            ),

        "loader_source":
            relative(
                LOADER_FILE
            ),

        "api_authority":
            "/api/v1/intelligence/upcoming",

        "loader_authority":
            "loadUpcomingMatches",

        "result_state_authority":
            "STAGE_10_2_MAPPED_API_RESULT",

        "kickoff": {
            "source_field":
                kickoff_field,

            "discovered_from":
                "STAGE_9_INTELLIGENCE_API_PAYLOAD",

            "validator_note":
                (
                    "Stage 10.2.6 validates the "
                    "intelligence record but does not "
                    "type the kickoff date field."
                ),

            "transport_numeric_string_coercion":
                True,

            "validated_record_fields":
                validated_fields,

            "frontend_alias":
                "kickoffUtc",

            "frontend_fallback":
                False,
        },

        "field_mapping": {
            "fixture_id":
                "fixtureId",

            "home_team_name":
                "homeTeamName",

            "away_team_name":
                "awayTeamName",

            "stage7_prob_home_win":
                "stage7_prob_home_win",

            "stage7_prob_draw":
                "stage7_prob_draw",

            "stage7_prob_away_win":
                "stage7_prob_away_win",

            "stage7_predicted_label":
                "stage7_predicted_label",

            "stage7_confidence":
                "stage7_confidence",

            "stage9_confidence_band":
                "confidence_band",

            "stage9_uncertainty_band":
                "uncertainty_band",

            "stage9_context_alignment":
                "context_alignment",

            "stage9_explanation_headline":
                "explanation_headline",

            "stage9_explanation_summary":
                "explanation_summary",
        },

        "runtime": {
            "server_component":
                True,

            "next_dynamic":
                "force-dynamic",

            "ready_only_data_render":
                True,

            "stale_fallback":
                False,

            "automatic_retry":
                False,

            "sorting":
                False,

            "probability_recalculation":
                False,

            "prediction_derivation":
                False,

            "intelligence_derivation":
                False,

            "direct_fetch":
                False,

            "provider_access":
                False,

            "artifact_access":
                False,
        },

        "transition": {
            "root_page_before_dashboard_sha256":
                page_before_sha,

            "root_page_after_dashboard_sha256":
                sha256_file(
                    PAGE_FILE
                ),
        },

        "page_after_dashboard_sha256":
            sha256_file(
                PAGE_FILE
            ),

        "extractor_sha256":
            sha256_file(
                EXTRACTOR_FILE
            ),

        "match_card_sha256":
            sha256_file(
                MATCH_CARD_FILE
            ),

        "protected_state": {
            "non_root_route_page_identity":
                non_root_pages(
                    expected_pages
                ),

            "loader_sha256":
                sha256_file(
                    LOADER_FILE
                ),

            "domain_types_sha256":
                sha256_file(
                    DOMAIN_TYPES_FILE
                ),

            "validation_sha256":
                sha256_file(
                    VALIDATION_FILE
                ),

            "mapped_api_sha256":
                sha256_file(
                    MAPPED_API_FILE
                ),

            "result_sha256":
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
        },

        "dependency_identity": {
            relative(
                PREVIOUS_FILE
            ):
                identity(
                    PREVIOUS_FILE
                ),

            relative(
                DETAIL_LINK_CONTRACT_FILE
            ):
                identity(
                    DETAIL_LINK_CONTRACT_FILE
                ),

            relative(
                LOADER_FILE
            ):
                identity(
                    LOADER_FILE
                ),

            relative(
                DOMAIN_TYPES_FILE
            ):
                identity(
                    DOMAIN_TYPES_FILE
                ),

            relative(
                VALIDATION_FILE
            ):
                identity(
                    VALIDATION_FILE
                ),

            relative(
                MAPPED_API_FILE
            ):
                identity(
                    MAPPED_API_FILE
                ),

            relative(
                RESULT_FILE
            ):
                identity(
                    RESULT_FILE
                ),
        },

        "promotion": {
            "stage10_4_12_complete":
                False,

            "stage10_4_complete":
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
        DASHBOARD_CONTRACT_FILE,
        dashboard_contract,
    )


    print()

    print(
        "MatchCard:"
    )

    print(
        f"  {relative(MATCH_CARD_FILE)}"
    )

    print()

    print(
        "Dashboard extractor:"
    )

    print(
        f"  {relative(EXTRACTOR_FILE)}"
    )

    print()

    print(
        "Root dashboard page:"
    )

    print(
        f"  {relative(PAGE_FILE)}"
    )

    print()

    print("=" * 72)

    print(
        "STAGE 10.4.11 DETAIL LINKS: BUILT"
    )

    print(
        "STAGE 10.4.12 DASHBOARD ASSEMBLY: BUILT"
    )

    print(
        "FINAL VERIFICATION STILL REQUIRED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
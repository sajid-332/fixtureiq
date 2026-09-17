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


STAGE10_4_FINAL_FILE = (
    FRONTEND_DATA
    / "stage10_4_final_verification.json"
)

STAGE10_4_DASHBOARD_CONTRACT_FILE = (
    DOCS
    / "frontend_upcoming_dashboard_contract.json"
)


ROUTE_CONTRACT_FILE = (
    DOCS
    / "frontend_match_detail_route_contract.json"
)

HEADER_CONTRACT_FILE = (
    DOCS
    / "frontend_match_fixture_header_contract.json"
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


MATCH_LOADER_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "load-match-intelligence.ts"
)

HEADER_RECORD_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "match-header-record.ts"
)

HEADER_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-fixture-header.tsx"
)

ROUTE_DIR = (
    FRONTEND
    / "app"
    / "matches"
    / "[fixtureId]"
)

ROUTE_PAGE_FILE = (
    ROUTE_DIR
    / "page.tsx"
)


MATCH_LOADER_SOURCE = '''import "server-only";

import {
  getIntelligenceMatchResult,
} from "../api/mapped";


export function loadMatchIntelligence(
  fixtureId: string,
) {
  return getIntelligenceMatchResult(
    fixtureId,
  );
}
'''


HEADER_RECORD_SOURCE = '''import "server-only";

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
'''


HEADER_COMPONENT_SOURCE = '''import type {
  FixtureId,
} from "../../lib/domain/types";

import {
  formatKickoffUtc,
} from "../../lib/formatters/kickoff";


type MatchFixtureHeaderProps =
  Readonly<{
    fixtureId:
      FixtureId;

    homeTeamName:
      string;

    awayTeamName:
      string;

    kickoffUtc:
      string;
  }>;


export function MatchFixtureHeader({
  fixtureId,
  homeTeamName,
  awayTeamName,
  kickoffUtc,
}: MatchFixtureHeaderProps) {

  const kickoffLabel =
    formatKickoffUtc(
      kickoffUtc,
    );


  return (
    <header
      aria-labelledby="match-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-6
        shadow-sm
        sm:px-7 sm:py-8
      "
      data-fixtureiq-component="match-fixture-header"
      data-fixture-id={
        String(
          fixtureId,
        )
      }
    >
      <p
        className="
          text-sm font-semibold
          uppercase tracking-wide
          text-slate-500
        "
      >
        Match intelligence
      </p>

      <div
        className="
          mt-5 grid
          grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]
          items-center gap-4
        "
      >
        <div
          className="
            min-w-0
          "
        >
          <p
            className="
              text-xs font-medium
              uppercase tracking-wide
              text-slate-500
            "
          >
            Home
          </p>

          <h1
            id="match-heading"
            className="
              mt-1 break-words
              text-xl font-bold
              tracking-tight
              text-slate-950
              sm:text-2xl
            "
          >
            {homeTeamName}
          </h1>
        </div>

        <span
          aria-hidden="true"
          className="
            text-sm font-semibold
            text-slate-400
          "
        >
          vs
        </span>

        <div
          className="
            min-w-0 text-right
          "
        >
          <p
            className="
              text-xs font-medium
              uppercase tracking-wide
              text-slate-500
            "
          >
            Away
          </p>

          <p
            className="
              mt-1 break-words
              text-xl font-bold
              tracking-tight
              text-slate-950
              sm:text-2xl
            "
          >
            {awayTeamName}
          </p>
        </div>
      </div>

      <div
        className="
          mt-6 border-t
          border-slate-100
          pt-4
        "
      >
        <p
          className="
            text-xs font-medium
            uppercase tracking-wide
            text-slate-500
          "
        >
          Kickoff
        </p>

        <time
          dateTime={
            kickoffUtc
          }
          className="
            mt-1 block
            text-sm font-semibold
            text-slate-700
          "
          data-stage9-field="date"
        >
          {kickoffLabel} UTC
        </time>
      </div>
    </header>
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


def current_route_pages() -> dict:

    output = {}

    for path in sorted(
        APP_ROOT.rglob(
            "page.tsx"
        )
    ):

        output[
            relative(
                path
            )
        ] = {
            "sha256":
                sha256_file(
                    path
                )
        }

    return output


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
            (
                "Could not determine Next.js "
                f"major version from {version!r}."
            )
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

        props = '''type MatchDetailPageProps =
  Readonly<{
    params:
      Promise<
        FixtureRouteParams
      >;
  }>;
'''

        param_read = '''  const {
    fixtureId,
  } = await params;
'''

    else:

        props = '''type MatchDetailPageProps =
  Readonly<{
    params:
      FixtureRouteParams;
  }>;
'''

        param_read = '''  const {
    fixtureId,
  } = params;
'''


    return f'''import {{
  notFound,
}} from "next/navigation";

import {{
  MatchFixtureHeader,
}} from "../../../components/matches/match-fixture-header";

import {{
  loadMatchIntelligence,
}} from "../../../lib/matches/load-match-intelligence";

import {{
  extractMatchFixtureHeader,
}} from "../../../lib/matches/match-header-record";

import type {{
  FixtureRouteParams,
}} from "../../../lib/domain/types";


export const dynamic =
  "force-dynamic";


{props}

export default async function MatchDetailPage({{
  params,
}}: MatchDetailPageProps) {{

{param_read}

  const result =
    await loadMatchIntelligence(
      fixtureId,
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
        aria-labelledby="match-unavailable-heading"
        data-fixtureiq-match-state={{
          result.state
        }}
      >
        <h1
          id="match-unavailable-heading"
          className="
            text-2xl font-bold
            tracking-tight text-slate-950
          "
        >
          Match intelligence unavailable
        </h1>

        <p
          className="
            mt-3 max-w-2xl
            text-sm leading-6
            text-slate-600
          "
        >
          This match cannot be displayed
          right now.
        </p>
      </section>
    );
  }}


  const header =
    extractMatchFixtureHeader(
      result.data,
      fixtureId,
    );


  return (
    <article
      data-fixtureiq-route="match-detail"
      data-fixtureiq-match-state="READY"
    >
      <MatchFixtureHeader
        fixtureId={{
          header.fixture_id
        }}
        homeTeamName={{
          header.home_team_name
        }}
        awayTeamName={{
          header.away_team_name
        }}
        kickoffUtc={{
          header.date
        }}
      />
    </article>
  );
}}
'''


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.5.1 + 10.5.2"
    )

    print(
        "DYNAMIC MATCH ROUTE + FIXTURE HEADER BUILD"
    )

    print("=" * 72)


    stage10_4 = load_json(
        STAGE10_4_FINAL_FILE
    )

    dashboard_contract = load_json(
        STAGE10_4_DASHBOARD_CONTRACT_FILE
    )


    if (
        stage10_4.get(
            "status"
        )
        !=
        "PASS"
    ):

        raise RuntimeError(
            "Stage 10.4 final verification is not PASS."
        )


    if (
        stage10_4.get(
            "stage10_4_complete"
        )
        is not True
    ):

        raise RuntimeError(
            "Stage 10.4 is not complete."
        )


    if (
        stage10_4.get(
            "stage10_ready_for_10_5_1"
        )
        is not True
    ):

        raise RuntimeError(
            "Stage 10.4 did not authorize 10.5.1."
        )


    required = [
        PACKAGE_FILE,
        DOMAIN_TYPES_FILE,
        MAPPED_API_FILE,
        RESULT_FILE,
        KICKOFF_FORMATTER_FILE,
    ]


    for path in required:

        if not path.exists():

            raise RuntimeError(
                f"Missing source: {path}"
            )


    mapped_source = (
        MAPPED_API_FILE.read_text(
            encoding="utf-8"
        )
    )


    if (
        "getIntelligenceMatchResult"
        not in
        mapped_source
    ):

        raise RuntimeError(
            (
                "Mapped Stage 9 single-match "
                "API wrapper is missing."
            )
        )


    domain_source = (
        DOMAIN_TYPES_FILE.read_text(
            encoding="utf-8"
        )
    )


    for required_type in [
        "FixtureId",
        "FixtureRouteParams",
    ]:

        if (
            f"export type {required_type}"
            not in
            domain_source
        ):

            raise RuntimeError(
                (
                    "Required locked domain "
                    f"type missing: {required_type}"
                )
            )


    (
        next_major,
        next_version,
    ) = detect_next_major()


    async_params = (
        next_major >= 15
    )


    print()

    print(
        "Next.js:"
    )

    print(
        f"  {next_version}"
    )

    print(
        "Dynamic route params:"
    )

    print(
        (
            "  Promise<FixtureRouteParams>"
            if async_params
            else
            "  FixtureRouteParams"
        )
    )


    existing_route_contract = (
        optional_json(
            ROUTE_CONTRACT_FILE
        )
    )

    existing_header_contract = (
        optional_json(
            HEADER_CONTRACT_FILE
        )
    )


    if (
        existing_route_contract
        and
        existing_header_contract
        and
        ROUTE_PAGE_FILE.exists()
        and
        MATCH_LOADER_FILE.exists()
        and
        HEADER_RECORD_FILE.exists()
        and
        HEADER_COMPONENT_FILE.exists()
        and
        sha256_file(
            ROUTE_PAGE_FILE
        )
        ==
        existing_header_contract.get(
            "route_page_after_header_sha256"
        )
        and
        sha256_file(
            HEADER_COMPONENT_FILE
        )
        ==
        existing_header_contract.get(
            "header_component_sha256"
        )
    ):

        print()

        print(
            "10.5.1 / 10.5.2 already built."
        )

        print("=" * 72)

        print(
            "STAGE 10.5.1 DYNAMIC MATCH ROUTE: BUILT"
        )

        print(
            "STAGE 10.5.2 FIXTURE HEADER: BUILT"
        )

        print(
            "VERIFICATION STILL REQUIRED"
        )

        print("=" * 72)

        return


    routes_before = (
        current_route_pages()
    )


    if (
        relative(
            ROUTE_PAGE_FILE
        )
        in
        routes_before
    ):

        raise RuntimeError(
            (
                "Dynamic match route already exists "
                "without matching Stage 10.5 contract. "
                "Refusing to overwrite it."
            )
        )


    # ========================================================
    # Stage 10.5.1
    # ========================================================

    save_text_atomic(
        MATCH_LOADER_FILE,
        MATCH_LOADER_SOURCE,
    )

    save_text_atomic(
        HEADER_RECORD_FILE,
        HEADER_RECORD_SOURCE,
    )


    route_source = (
        build_route_source(
            async_params
        )
    )


    save_text_atomic(
        ROUTE_PAGE_FILE,
        route_source,
    )


    route_sha = (
        sha256_file(
            ROUTE_PAGE_FILE
        )
    )


    route_contract = {
        "stage":
            "10.5.1",

        "version":
            "1.0.0",

        "name":
            "DYNAMIC_MATCH_ROUTE",

        "status":
            "LOCKED",

        "route":
            "/matches/[fixtureId]",

        "route_source":
            relative(
                ROUTE_PAGE_FILE
            ),

        "loader_source":
            relative(
                MATCH_LOADER_FILE
            ),

        "record_extractor_source":
            relative(
                HEADER_RECORD_FILE
            ),

        "backend_endpoint":
            "/api/v1/intelligence/matches/<fixture_id>",

        "mapped_client":
            "getIntelligenceMatchResult",

        "route_parameter": {
            "name":
                "fixtureId",

            "domain_type":
                "FixtureRouteParams",

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

            "stale_fallback":
                False,

            "direct_fetch":
                False,

            "provider_access":
                False,

            "artifact_access":
                False,
        },

        "authority": {
            "prediction":
                "STAGE_7",

            "context":
                "STAGE_8",

            "intelligence":
                "STAGE_9",

            "presentation":
                "STAGE_10",
        },

        "protected_state": {
            "route_pages_before_10_5_1":
                routes_before,

            "dashboard_page_sha256":
                dashboard_contract.get(
                    "page_after_dashboard_sha256"
                ),

            "dashboard_match_card_sha256":
                dashboard_contract.get(
                    "match_card_sha256"
                ),

            "domain_types_sha256":
                sha256_file(
                    DOMAIN_TYPES_FILE
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
                STAGE10_4_FINAL_FILE
            ):
                identity(
                    STAGE10_4_FINAL_FILE
                ),

            relative(
                STAGE10_4_DASHBOARD_CONTRACT_FILE
            ):
                identity(
                    STAGE10_4_DASHBOARD_CONTRACT_FILE
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

        "route_page_after_10_5_1_sha256":
            route_sha,

        "promotion": {
            "stage10_5_1_complete":
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
        ROUTE_CONTRACT_FILE,
        route_contract,
    )


    # ========================================================
    # Stage 10.5.2
    # ========================================================

    save_text_atomic(
        HEADER_COMPONENT_FILE,
        HEADER_COMPONENT_SOURCE,
    )


    # Route source already references MatchFixtureHeader.
    # Rewriting is unnecessary; hash remains deterministic.

    header_contract = {
        "stage":
            "10.5.2",

        "version":
            "1.0.0",

        "name":
            "MATCH_FIXTURE_HEADER",

        "status":
            "LOCKED",

        "component_source":
            relative(
                HEADER_COMPONENT_FILE
            ),

        "route_source":
            relative(
                ROUTE_PAGE_FILE
            ),

        "source_fields": [
            "fixture_id",
            "home_team_name",
            "away_team_name",
            "date",
        ],

        "kickoff": {
            "backend_field":
                "date",

            "frontend_prop":
                "kickoffUtc",

            "formatter":
                "formatKickoffUtc",

            "display_timezone":
                "UTC",

            "source_value_modified":
                False,
        },

        "presentation": {
            "home_team":
                True,

            "away_team":
                True,

            "kickoff":
                True,

            "probabilities":
                False,

            "prediction_overview":
                False,

            "confidence":
                False,

            "uncertainty":
                False,

            "context_comparison":
                False,

            "explanation":
                False,
        },

        "implementation": {
            "server_component":
                True,

            "direct_fetch":
                False,

            "prediction_logic":
                False,

            "intelligence_derivation":
                False,

            "provider_access":
                False,

            "artifact_access":
                False,
        },

        "route_page_after_header_sha256":
            sha256_file(
                ROUTE_PAGE_FILE
            ),

        "header_component_sha256":
            sha256_file(
                HEADER_COMPONENT_FILE
            ),

        "header_record_sha256":
            sha256_file(
                HEADER_RECORD_FILE
            ),

        "match_loader_sha256":
            sha256_file(
                MATCH_LOADER_FILE
            ),

        "protected_state": {
            "domain_types_sha256":
                sha256_file(
                    DOMAIN_TYPES_FILE
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
        },

        "dependency_identity": {
            relative(
                ROUTE_CONTRACT_FILE
            ):
                identity(
                    ROUTE_CONTRACT_FILE
                ),

            relative(
                KICKOFF_FORMATTER_FILE
            ):
                identity(
                    KICKOFF_FORMATTER_FILE
                ),
        },

        "promotion": {
            "stage10_5_2_complete":
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
        HEADER_CONTRACT_FILE,
        header_contract,
    )


    print()

    print(
        "Route:"
    )

    print(
        f"  {relative(ROUTE_PAGE_FILE)}"
    )

    print(
        "Loader:"
    )

    print(
        f"  {relative(MATCH_LOADER_FILE)}"
    )

    print(
        "Header record extractor:"
    )

    print(
        f"  {relative(HEADER_RECORD_FILE)}"
    )

    print(
        "Fixture header:"
    )

    print(
        f"  {relative(HEADER_COMPONENT_FILE)}"
    )

    print()

    print("=" * 72)

    print(
        "STAGE 10.5.1 DYNAMIC MATCH ROUTE: BUILT"
    )

    print(
        "STAGE 10.5.2 FIXTURE HEADER: BUILT"
    )

    print(
        "VERIFICATION STILL REQUIRED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
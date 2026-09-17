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
    / "stage10_5_11_10_5_14_verification.json"
)

EXPLANATION_CONTRACT_FILE = (
    DOCS
    / "frontend_match_deterministic_explanation_contract.json"
)

STATUS_CONTRACT_FILE = (
    DOCS
    / "frontend_match_freshness_status_contract.json"
)


ROUTE_PAGE_FILE = (
    FRONTEND
    / "app"
    / "matches"
    / "[fixtureId]"
    / "page.tsx"
)

STATUS_LOADER_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "load-intelligence-status.ts"
)

STATUS_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-freshness-status.tsx"
)


MATCH_LOADER_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "load-match-intelligence.ts"
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

INTELLIGENCE_RECORD_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "match-intelligence-detail-record.ts"
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


STATUS_LOADER_SOURCE = '''import "server-only";

import {
  getIntelligenceStatusResult,
} from "../api/mapped";


export function loadIntelligenceStatus() {
  return getIntelligenceStatusResult();
}
'''


STATUS_COMPONENT_SOURCE = '''import type {
  ApiTerminalState,
} from "../../lib/api/result";


type MatchFreshnessStatusProps =
  Readonly<{
    state:
      ApiTerminalState;

    httpStatus:
      number | null;
  }>;


export function MatchFreshnessStatus({
  state,
  httpStatus,
}: MatchFreshnessStatusProps) {

  const statusLabel =
    httpStatus === null
      ? "No HTTP response"
      : String(
          httpStatus,
        );


  return (
    <section
      aria-labelledby="match-freshness-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-freshness-status"
      data-freshness-state={
        state
      }
    >
      <h2
        id="match-freshness-heading"
        className="
          text-base font-bold
          text-slate-950
        "
      >
        Freshness &amp; service status
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
              text-sm text-slate-600
            "
          >
            Intelligence runtime
          </dt>

          <dd
            className="
              text-sm font-semibold
              text-slate-950
            "
            data-stage9-runtime-state
          >
            {state}
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
            Status request
          </dt>

          <dd
            className="
              text-sm font-semibold
              text-slate-950
            "
            data-stage9-runtime-http-status
          >
            {statusLabel}
          </dd>
        </div>
      </dl>

      <p
        className="
          mt-4 text-xs
          leading-5 text-slate-500
        "
      >
        Freshness is enforced by the
        Stage 9 backend runtime policy.
        This page does not reuse a previous
        freshness response.
      </p>
    </section>
  );
}
'''


STATUS_COMPONENT_IMPORT = '''import {
  MatchFreshnessStatus,
} from "../../../components/matches/match-freshness-status";

'''


STATUS_LOADER_IMPORT = '''import {
  loadIntelligenceStatus,
} from "../../../lib/matches/load-intelligence-status";

'''


STATUS_READ = '''  const statusResult =
    await loadIntelligenceStatus();


'''


STATUS_SECTION = '''      <div
        className="
          mt-6
        "
      >
        <MatchFreshnessStatus
          state={
            statusResult.state
          }
          httpStatus={
            statusResult.status
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
        "match_loader_sha256":
            MATCH_LOADER_FILE,

        "header_component_sha256":
            HEADER_COMPONENT_FILE,

        "header_record_sha256":
            HEADER_RECORD_FILE,

        "prediction_record_sha256":
            PREDICTION_RECORD_FILE,

        "context_record_sha256":
            CONTEXT_RECORD_FILE,

        "intelligence_record_sha256":
            INTELLIGENCE_RECORD_FILE,

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

        "venue_form_sha256":
            VENUE_FORM_COMPONENT_FILE,

        "context_support_sha256":
            CONTEXT_SUPPORT_COMPONENT_FILE,

        "alignment_sha256":
            ALIGNMENT_COMPONENT_FILE,

        "explanation_sha256":
            EXPLANATION_COMPONENT_FILE,

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
        "FixtureIQ Stage 10.5.15"
    )

    print(
        "MATCH FRESHNESS / STATUS BUILD"
    )

    print("=" * 72)


    previous = load_json(
        PREVIOUS_FILE
    )

    explanation_contract = load_json(
        EXPLANATION_CONTRACT_FILE
    )


    if (
        previous.get(
            "status"
        )
        !=
        "PASS"
    ):
        raise RuntimeError(
            "10.5.11-10.5.14 verification is not PASS."
        )


    for key in [
        "stage_10_5_11_complete",
        "stage_10_5_12_complete",
        "stage_10_5_13_complete",
        "stage_10_5_14_complete",
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
            "stage10_ready_for_10_5_15"
        )
        is not True
    ):
        raise RuntimeError(
            "10.5.14 did not authorize 10.5.15."
        )


    required = [
        ROUTE_PAGE_FILE,
        MATCH_LOADER_FILE,
        HEADER_COMPONENT_FILE,
        HEADER_RECORD_FILE,
        PREDICTION_RECORD_FILE,
        CONTEXT_RECORD_FILE,
        INTELLIGENCE_RECORD_FILE,
        OVERVIEW_COMPONENT_FILE,
        PROBABILITY_COMPONENT_FILE,
        CONFIDENCE_COMPONENT_FILE,
        UNCERTAINTY_COMPONENT_FILE,
        LEAGUE_POSITION_COMPONENT_FILE,
        POINTS_COMPONENT_FILE,
        GOAL_DIFFERENCE_COMPONENT_FILE,
        RECENT_FORM_COMPONENT_FILE,
        VENUE_FORM_COMPONENT_FILE,
        CONTEXT_SUPPORT_COMPONENT_FILE,
        ALIGNMENT_COMPONENT_FILE,
        EXPLANATION_COMPONENT_FILE,
        DOMAIN_TYPES_FILE,
        MAPPED_API_FILE,
        RESULT_FILE,
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
        "getIntelligenceStatusResult"
        not in
        mapped_source
    ):
        raise RuntimeError(
            (
                "Locked mapped intelligence "
                "status client is missing."
            )
        )


    expected_route_sha = (
        explanation_contract.get(
            "route_page_after_10_5_14_sha256"
        )
    )


    existing_contract = optional_json(
        STATUS_CONTRACT_FILE
    )


    if (
        existing_contract
        and
        STATUS_LOADER_FILE.exists()
        and
        STATUS_COMPONENT_FILE.exists()
        and
        sha256_file(
            ROUTE_PAGE_FILE
        )
        ==
        existing_contract.get(
            "route_page_after_10_5_15_sha256"
        )
        and
        sha256_file(
            STATUS_COMPONENT_FILE
        )
        ==
        existing_contract.get(
            "component_sha256"
        )
    ):

        print()

        print(
            "10.5.15 already built."
        )

        print("=" * 72)

        print(
            "STAGE 10.5.15 FRESHNESS / STATUS: BUILT"
        )

        print(
            "FINAL 10.5.16 VERIFICATION STILL REQUIRED"
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
                "verified 10.5.14 output."
            )
        )


    route_before_sha = (
        sha256_file(
            ROUTE_PAGE_FILE
        )
    )


    save_text_atomic(
        STATUS_LOADER_FILE,
        STATUS_LOADER_SOURCE,
    )

    save_text_atomic(
        STATUS_COMPONENT_FILE,
        STATUS_COMPONENT_SOURCE,
    )


    route_source = (
        ROUTE_PAGE_FILE.read_text(
            encoding="utf-8"
        )
    )


    explanation_import = '''import {
  MatchIntelligenceExplanation,
} from "../../../components/matches/match-intelligence-explanation";

'''


    route_source = replace_once(
        route_source,
        explanation_import,
        (
            explanation_import
            +
            STATUS_COMPONENT_IMPORT
        ),
        "freshness component import",
    )


    match_loader_import = '''import {
  loadMatchIntelligence,
} from "../../../lib/matches/load-match-intelligence";

'''


    route_source = replace_once(
        route_source,
        match_loader_import,
        (
            match_loader_import
            +
            STATUS_LOADER_IMPORT
        ),
        "freshness loader import",
    )


    header_anchor = '''  const header =
    extractMatchFixtureHeader(
'''


    route_source = replace_once(
        route_source,
        header_anchor,
        (
            STATUS_READ
            +
            header_anchor
        ),
        "freshness status request",
    )


    article_close = '''    </article>
'''


    route_source = replace_once(
        route_source,
        article_close,
        (
            STATUS_SECTION
            +
            article_close
        ),
        "freshness status section",
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


    contract = {
        "stage":
            "10.5.15",

        "version":
            "1.0.0",

        "name":
            "MATCH_FRESHNESS_STATUS",

        "status":
            "LOCKED",

        "backend_authority":
            "STAGE_9_RUNTIME_FRESHNESS",

        "backend_endpoint":
            "/api/v1/intelligence/status",

        "mapped_client":
            "getIntelligenceStatusResult",

        "loader_source":
            relative(
                STATUS_LOADER_FILE
            ),

        "component_source":
            relative(
                STATUS_COMPONENT_FILE
            ),

        "display_fields": [
            "ApiTerminalState",
            "HTTP_STATUS_OR_NULL",
        ],

        "runtime_policy": {
            "backend_freshness_authoritative":
                True,

            "frontend_ttl":
                False,

            "frontend_freshness_timestamp_derivation":
                False,

            "frontend_staleness_calculation":
                False,

            "previous_status_reuse":
                False,

            "stale_fallback":
                False,

            "automatic_retry":
                False,

            "direct_fetch":
                False,

            "provider_access":
                False,

            "artifact_access":
                False,
        },

        "component_sha256":
            sha256_file(
                STATUS_COMPONENT_FILE
            ),

        "loader_sha256":
            sha256_file(
                STATUS_LOADER_FILE
            ),

        "route_page_before_10_5_15_sha256":
            route_before_sha,

        "route_page_after_10_5_15_sha256":
            route_after_sha,

        "protected_state":
            protected_state(),

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
            "stage10_5_15_complete":
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
        STATUS_CONTRACT_FILE,
        contract,
    )


    print()

    print(
        "Status loader:"
    )

    print(
        f"  {relative(STATUS_LOADER_FILE)}"
    )

    print(
        "Status component:"
    )

    print(
        f"  {relative(STATUS_COMPONENT_FILE)}"
    )


    print()

    print("=" * 72)

    print(
        "STAGE 10.5.15 FRESHNESS / STATUS: BUILT"
    )

    print(
        "FINAL 10.5.16 VERIFICATION STILL REQUIRED"
    )

    print("=" * 72)


if __name__ == "__main__":
    main()
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
    / "stage10_7_5_10_7_8_verification.json"
)


UNCERTAINTY_BADGE_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "uncertainty-badge.tsx"
)

CONTEXT_ALIGNMENT_BADGE_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "context-alignment-badge.tsx"
)

CONTEXT_SCORE_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "context-score.tsx"
)

TEAM_COMPARISON_ROW_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "team-comparison-row.tsx"
)


RECENT_FORM_DISPLAY_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "recent-form-display.tsx"
)

INTELLIGENCE_EXPLANATION_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "intelligence-explanation.tsx"
)

FRESHNESS_INDICATOR_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "freshness-indicator.tsx"
)

EMPTY_STATE_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "empty-state.tsx"
)


RESULT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "result.ts"
)


UNCERTAINTY_CONTRACT_FILE = (
    DOCS
    / "frontend_uncertainty_badge_contract.json"
)

ALIGNMENT_CONTRACT_FILE = (
    DOCS
    / "frontend_context_alignment_badge_contract.json"
)

CONTEXT_SCORE_CONTRACT_FILE = (
    DOCS
    / "frontend_context_score_contract.json"
)

TEAM_COMPARISON_CONTRACT_FILE = (
    DOCS
    / "frontend_team_comparison_row_contract.json"
)


RECENT_FORM_CONTRACT_FILE = (
    DOCS
    / "frontend_recent_form_display_contract.json"
)

INTELLIGENCE_EXPLANATION_CONTRACT_FILE = (
    DOCS
    / "frontend_intelligence_explanation_contract.json"
)

FRESHNESS_INDICATOR_CONTRACT_FILE = (
    DOCS
    / "frontend_freshness_indicator_contract.json"
)

EMPTY_STATE_CONTRACT_FILE = (
    DOCS
    / "frontend_empty_state_contract.json"
)


RECENT_FORM_DISPLAY_SOURCE = '''type RecentFormDisplayProps =
  Readonly<{
    label:
      string;

    results:
      string;

    matchesAvailable:
      number;
  }>;


export function RecentFormDisplay({
  label,
  results,
  matchesAvailable,
}: RecentFormDisplayProps) {

  return (
    <div
      aria-label={`${label} recent form`}
      className="
        rounded-lg
        border border-slate-200
        bg-white
        px-4 py-4
      "
      data-fixtureiq-component="recent-form-display"
    >
      <p
        className="
          text-xs font-medium
          uppercase tracking-wide
          text-slate-500
        "
      >
        {label}
      </p>

      <p
        className="
          mt-2 font-mono
          text-lg font-semibold
          tracking-widest
          text-slate-950
        "
        data-recent-form-results
      >
        {results || "No results"}
      </p>

      <p
        className="
          mt-2 text-xs
          text-slate-500
        "
        data-recent-form-matches-available
      >
        {matchesAvailable} matches available
      </p>
    </div>
  );
}
'''


INTELLIGENCE_EXPLANATION_SOURCE = '''type IntelligenceExplanationProps =
  Readonly<{
    headline:
      string;

    summary:
      string;
  }>;


export function IntelligenceExplanation({
  headline,
  summary,
}: IntelligenceExplanationProps) {

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
      data-fixtureiq-component="intelligence-explanation"
    >
      <h2
        id="intelligence-explanation-heading"
        className="
          text-lg font-bold
          text-slate-950
        "
        data-stage9-explanation-headline
      >
        {headline}
      </h2>

      <p
        className="
          mt-3 text-sm
          leading-6
          text-slate-700
        "
        data-stage9-explanation-summary
      >
        {summary}
      </p>
    </section>
  );
}
'''


FRESHNESS_INDICATOR_SOURCE = '''import type {
  ApiTerminalState,
} from "../../lib/api/result";


type FreshnessIndicatorProps =
  Readonly<{
    state:
      ApiTerminalState;

    httpStatus:
      number | null;
  }>;


export function FreshnessIndicator({
  state,
  httpStatus,
}: FreshnessIndicatorProps) {

  const statusLabel =
    httpStatus === null
      ? "No HTTP response"
      : String(
          httpStatus,
        );


  return (
    <div
      aria-label={`Service status: ${state}`}
      className="
        inline-flex flex-wrap
        items-center gap-x-3 gap-y-1
        rounded-lg
        border border-slate-200
        bg-white
        px-3 py-2
        text-xs
        text-slate-700
      "
      data-fixtureiq-component="freshness-indicator"
      data-freshness-state={
        state
      }
    >
      <span
        className="
          font-semibold
          text-slate-950
        "
      >
        {state}
      </span>

      <span
        aria-hidden="true"
        className="text-slate-300"
      >
        •
      </span>

      <span
        data-freshness-http-status
      >
        {statusLabel}
      </span>
    </div>
  );
}
'''


EMPTY_STATE_SOURCE = '''import type {
  ReactNode,
} from "react";


type EmptyStateProps =
  Readonly<{
    title:
      string;

    message:
      string;

    action?:
      ReactNode;
  }>;


export function EmptyState({
  title,
  message,
  action,
}: EmptyStateProps) {

  return (
    <section
      aria-labelledby="fixtureiq-empty-state-heading"
      className="
        rounded-xl
        border border-dashed
        border-slate-300
        bg-white
        px-5 py-8
        text-center
        sm:px-8
      "
      data-fixtureiq-component="empty-state"
    >
      <h2
        id="fixtureiq-empty-state-heading"
        className="
          text-lg font-bold
          text-slate-950
        "
      >
        {title}
      </h2>

      <p
        className="
          mx-auto mt-2
          max-w-xl
          text-sm leading-6
          text-slate-600
        "
      >
        {message}
      </p>

      {
        action
          ? (
              <div
                className="mt-5"
                data-empty-state-action
              >
                {action}
              </div>
            )
          : null
      }
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


def refuse_unknown_existing_file(
    source_file: Path,
    contract_file: Path,
) -> None:

    if not source_file.exists():
        return

    contract = optional_json(
        contract_file
    )

    if (
        contract
        and
        contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            source_file
        )
    ):
        return

    raise RuntimeError(
        (
            f"{relative(source_file)} already exists "
            "without a matching locked Stage 10.7 contract. "
            "Refusing to overwrite it."
        )
    )


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.7.9 - 10.7.12"
    )

    print(
        "REUSABLE FORM + EXPLANATION + FRESHNESS + EMPTY UI BUILD"
    )

    print("=" * 72)


    previous = load_json(
        PREVIOUS_FILE
    )


    if (
        previous.get(
            "status"
        )
        !=
        "PASS"
    ):
        raise RuntimeError(
            "10.7.5-10.7.8 verification is not PASS."
        )


    for key in [
        "stage_10_7_5_complete",
        "stage_10_7_6_complete",
        "stage_10_7_7_complete",
        "stage_10_7_8_complete",
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
            "stage10_ready_for_10_7_9"
        )
        is not True
    ):
        raise RuntimeError(
            "10.7.8 did not authorize 10.7.9."
        )


    required = [
        UNCERTAINTY_BADGE_FILE,
        CONTEXT_ALIGNMENT_BADGE_FILE,
        CONTEXT_SCORE_FILE,
        TEAM_COMPARISON_ROW_FILE,
        RESULT_FILE,
        UNCERTAINTY_CONTRACT_FILE,
        ALIGNMENT_CONTRACT_FILE,
        CONTEXT_SCORE_CONTRACT_FILE,
        TEAM_COMPARISON_CONTRACT_FILE,
    ]


    for path in required:

        if not path.exists():
            raise RuntimeError(
                f"Missing source: {path}"
            )


    previous_comparison_contract = load_json(
        TEAM_COMPARISON_CONTRACT_FILE
    )


    if (
        previous_comparison_contract.get(
            "component_sha256"
        )
        !=
        sha256_file(
            TEAM_COMPARISON_ROW_FILE
        )
    ):
        raise RuntimeError(
            "Verified 10.7.8 TeamComparisonRow changed."
        )


    final_contract = optional_json(
        EMPTY_STATE_CONTRACT_FILE
    )


    if (
        final_contract
        and
        RECENT_FORM_DISPLAY_FILE.exists()
        and
        INTELLIGENCE_EXPLANATION_FILE.exists()
        and
        FRESHNESS_INDICATOR_FILE.exists()
        and
        EMPTY_STATE_FILE.exists()
        and
        final_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            EMPTY_STATE_FILE
        )
    ):

        print()

        print(
            "10.7.9 - 10.7.12 already built."
        )

        print("=" * 72)

        print(
            "STAGE 10.7.9 RECENTFORMDISPLAY: BUILT"
        )

        print(
            "STAGE 10.7.10 INTELLIGENCEEXPLANATION: BUILT"
        )

        print(
            "STAGE 10.7.11 FRESHNESSINDICATOR: BUILT"
        )

        print(
            "STAGE 10.7.12 EMPTYSTATE: BUILT"
        )

        print(
            "VERIFICATION STILL REQUIRED"
        )

        print("=" * 72)

        return


    refuse_unknown_existing_file(
        RECENT_FORM_DISPLAY_FILE,
        RECENT_FORM_CONTRACT_FILE,
    )

    refuse_unknown_existing_file(
        INTELLIGENCE_EXPLANATION_FILE,
        INTELLIGENCE_EXPLANATION_CONTRACT_FILE,
    )

    refuse_unknown_existing_file(
        FRESHNESS_INDICATOR_FILE,
        FRESHNESS_INDICATOR_CONTRACT_FILE,
    )

    refuse_unknown_existing_file(
        EMPTY_STATE_FILE,
        EMPTY_STATE_CONTRACT_FILE,
    )


    protected = {
        "uncertainty_badge_sha256":
            sha256_file(
                UNCERTAINTY_BADGE_FILE
            ),

        "context_alignment_badge_sha256":
            sha256_file(
                CONTEXT_ALIGNMENT_BADGE_FILE
            ),

        "context_score_sha256":
            sha256_file(
                CONTEXT_SCORE_FILE
            ),

        "team_comparison_row_sha256":
            sha256_file(
                TEAM_COMPARISON_ROW_FILE
            ),

        "result_mapping_sha256":
            sha256_file(
                RESULT_FILE
            ),
    }


    save_text_atomic(
        RECENT_FORM_DISPLAY_FILE,
        RECENT_FORM_DISPLAY_SOURCE,
    )

    save_text_atomic(
        INTELLIGENCE_EXPLANATION_FILE,
        INTELLIGENCE_EXPLANATION_SOURCE,
    )

    save_text_atomic(
        FRESHNESS_INDICATOR_FILE,
        FRESHNESS_INDICATOR_SOURCE,
    )

    save_text_atomic(
        EMPTY_STATE_FILE,
        EMPTY_STATE_SOURCE,
    )


    recent_form_contract = {
        "stage":
            "10.7.9",

        "version":
            "1.0.0",

        "name":
            "REUSABLE_RECENT_FORM_DISPLAY",

        "status":
            "LOCKED",

        "source":
            relative(
                RECENT_FORM_DISPLAY_FILE
            ),

        "component":
            "RecentFormDisplay",

        "authority":
            "CALLER_PROVIDED_STAGE_8_FORM",

        "presentation": {
            "results_direct":
                True,

            "matches_available_direct":
                True,

            "points_calculation":
                False,

            "result_aggregation":
                False,

            "form_scoring":
                False,

            "sorting":
                False,
        },

        "component_sha256":
            sha256_file(
                RECENT_FORM_DISPLAY_FILE
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
                TEAM_COMPARISON_CONTRACT_FILE
            ):
                identity(
                    TEAM_COMPARISON_CONTRACT_FILE
                ),
        },

        "promotion": {
            "stage10_7_9_complete":
                False,

            "stage10_7_complete":
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


    explanation_contract = {
        "stage":
            "10.7.10",

        "version":
            "1.0.0",

        "name":
            "REUSABLE_INTELLIGENCE_EXPLANATION",

        "status":
            "LOCKED",

        "source":
            relative(
                INTELLIGENCE_EXPLANATION_FILE
            ),

        "component":
            "IntelligenceExplanation",

        "authority":
            "STAGE_9_DETERMINISTIC_EXPLANATION",

        "rule_version":
            "STAGE9_5_DETERMINISTIC_EXPLANATION_V1",

        "presentation": {
            "headline_direct":
                True,

            "summary_direct":
                True,

            "generation":
                False,

            "rewriting":
                False,

            "truncation":
                False,

            "fallback_explanation":
                False,

            "llm_execution":
                False,
        },

        "component_sha256":
            sha256_file(
                INTELLIGENCE_EXPLANATION_FILE
            ),

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                RECENT_FORM_CONTRACT_FILE
            ):
                identity(
                    RECENT_FORM_CONTRACT_FILE
                ),
        },

        "promotion": {
            "stage10_7_10_complete":
                False,

            "stage10_7_complete":
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
        INTELLIGENCE_EXPLANATION_CONTRACT_FILE,
        explanation_contract,
    )


    freshness_contract = {
        "stage":
            "10.7.11",

        "version":
            "1.0.0",

        "name":
            "REUSABLE_FRESHNESS_INDICATOR",

        "status":
            "LOCKED",

        "source":
            relative(
                FRESHNESS_INDICATOR_FILE
            ),

        "component":
            "FreshnessIndicator",

        "domain_type":
            "ApiTerminalState",

        "authority":
            "BACKEND_RUNTIME_STATE",

        "presentation": {
            "state_direct":
                True,

            "http_status_direct":
                True,

            "null_http_status_supported":
                True,

            "frontend_ttl":
                False,

            "frontend_clock_calculation":
                False,

            "frontend_staleness_derivation":
                False,

            "previous_state_reuse":
                False,
        },

        "component_sha256":
            sha256_file(
                FRESHNESS_INDICATOR_FILE
            ),

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                INTELLIGENCE_EXPLANATION_CONTRACT_FILE
            ):
                identity(
                    INTELLIGENCE_EXPLANATION_CONTRACT_FILE
                ),

            relative(
                RESULT_FILE
            ):
                identity(
                    RESULT_FILE
                ),
        },

        "promotion": {
            "stage10_7_11_complete":
                False,

            "stage10_7_complete":
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
        FRESHNESS_INDICATOR_CONTRACT_FILE,
        freshness_contract,
    )


    empty_contract = {
        "stage":
            "10.7.12",

        "version":
            "1.0.0",

        "name":
            "REUSABLE_EMPTY_STATE",

        "status":
            "LOCKED",

        "source":
            relative(
                EMPTY_STATE_FILE
            ),

        "component":
            "EmptyState",

        "responsibility":
            "PRESENT_CALLER_PROVIDED_EMPTY_STATE",

        "presentation": {
            "title_direct":
                True,

            "message_direct":
                True,

            "optional_action":
                True,

            "data_fetch":
                False,

            "retry_logic":
                False,

            "fallback_data":
                False,

            "empty_condition_derivation":
                False,
        },

        "component_sha256":
            sha256_file(
                EMPTY_STATE_FILE
            ),

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                FRESHNESS_INDICATOR_CONTRACT_FILE
            ):
                identity(
                    FRESHNESS_INDICATOR_CONTRACT_FILE
                ),
        },

        "promotion": {
            "stage10_7_12_complete":
                False,

            "stage10_7_complete":
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
        EMPTY_STATE_CONTRACT_FILE,
        empty_contract,
    )


    print()

    print(
        "Reusable components:"
    )


    for path in [
        RECENT_FORM_DISPLAY_FILE,
        INTELLIGENCE_EXPLANATION_FILE,
        FRESHNESS_INDICATOR_FILE,
        EMPTY_STATE_FILE,
    ]:

        print(
            f"  {relative(path)}"
        )


    print()

    print("=" * 72)

    print(
        "STAGE 10.7.9 RECENTFORMDISPLAY: BUILT"
    )

    print(
        "STAGE 10.7.10 INTELLIGENCEEXPLANATION: BUILT"
    )

    print(
        "STAGE 10.7.11 FRESHNESSINDICATOR: BUILT"
    )

    print(
        "STAGE 10.7.12 EMPTYSTATE: BUILT"
    )

    print(
        "VERIFICATION STILL REQUIRED"
    )

    print("=" * 72)


if __name__ == "__main__":
    main()
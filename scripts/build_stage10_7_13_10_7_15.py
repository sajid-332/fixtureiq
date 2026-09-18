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


VERIFY_1_4_FILE = (
    FRONTEND_DATA
    / "stage10_7_1_10_7_4_verification.json"
)

VERIFY_5_8_FILE = (
    FRONTEND_DATA
    / "stage10_7_5_10_7_8_verification.json"
)

VERIFY_9_12_FILE = (
    FRONTEND_DATA
    / "stage10_7_9_10_7_12_verification.json"
)


MATCH_CARD_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-card.tsx"
)

PROBABILITY_BAR_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "probability-bar.tsx"
)

OUTCOME_BADGE_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "outcome-badge.tsx"
)

CONFIDENCE_BADGE_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "confidence-badge.tsx"
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

ERROR_STATE_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "error-state.tsx"
)

LOADING_STATE_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "loading-state.tsx"
)


MATCH_CARD_CONTRACT = (
    DOCS
    / "frontend_reusable_match_card_contract.json"
)

PROBABILITY_BAR_CONTRACT = (
    DOCS
    / "frontend_probability_bar_contract.json"
)

OUTCOME_BADGE_CONTRACT = (
    DOCS
    / "frontend_outcome_badge_contract.json"
)

CONFIDENCE_BADGE_CONTRACT = (
    DOCS
    / "frontend_confidence_badge_contract.json"
)

UNCERTAINTY_BADGE_CONTRACT = (
    DOCS
    / "frontend_uncertainty_badge_contract.json"
)

CONTEXT_ALIGNMENT_BADGE_CONTRACT = (
    DOCS
    / "frontend_context_alignment_badge_contract.json"
)

CONTEXT_SCORE_CONTRACT = (
    DOCS
    / "frontend_context_score_contract.json"
)

TEAM_COMPARISON_ROW_CONTRACT = (
    DOCS
    / "frontend_team_comparison_row_contract.json"
)

RECENT_FORM_DISPLAY_CONTRACT = (
    DOCS
    / "frontend_recent_form_display_contract.json"
)

INTELLIGENCE_EXPLANATION_CONTRACT = (
    DOCS
    / "frontend_intelligence_explanation_contract.json"
)

FRESHNESS_INDICATOR_CONTRACT = (
    DOCS
    / "frontend_freshness_indicator_contract.json"
)

EMPTY_STATE_CONTRACT = (
    DOCS
    / "frontend_empty_state_contract.json"
)

ERROR_STATE_CONTRACT = (
    DOCS
    / "frontend_error_state_contract.json"
)

LOADING_STATE_CONTRACT = (
    DOCS
    / "frontend_loading_state_contract.json"
)

CONSISTENCY_CONTRACT = (
    DOCS
    / "frontend_reusable_ui_consistency_contract.json"
)


ERROR_STATE_SOURCE = '''import type {
  ReactNode,
} from "react";


type ErrorStateProps =
  Readonly<{
    title:
      string;

    message:
      string;

    action?:
      ReactNode;
  }>;


export function ErrorState({
  title,
  message,
  action,
}: ErrorStateProps) {

  return (
    <section
      aria-labelledby="fixtureiq-error-state-heading"
      className="
        rounded-xl
        border border-slate-300
        bg-white
        px-5 py-8
        text-center
        shadow-sm
        sm:px-8
      "
      data-fixtureiq-component="error-state"
      role="alert"
    >
      <h2
        id="fixtureiq-error-state-heading"
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
                data-error-state-action
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


LOADING_STATE_SOURCE = '''type LoadingStateProps =
  Readonly<{
    label?:
      string;
  }>;


export function LoadingState({
  label = "Loading FixtureIQ data...",
}: LoadingStateProps) {

  return (
    <div
      aria-busy="true"
      aria-live="polite"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-6
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="loading-state"
      role="status"
    >
      <p
        className="
          text-sm font-semibold
          text-slate-700
        "
        data-loading-state-label
      >
        {label}
      </p>

      <div
        aria-hidden="true"
        className="
          mt-4 space-y-3
        "
      >
        <div
          className="
            h-3 w-full
            rounded bg-slate-100
          "
        />

        <div
          className="
            h-3 w-5/6
            rounded bg-slate-100
          "
        />

        <div
          className="
            h-3 w-2/3
            rounded bg-slate-100
          "
        />
      </div>
    </div>
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
            "without matching locked contract. "
            "Refusing to overwrite it."
        )
    )


def verify_existing_component(
    source: Path,
    contract: Path,
) -> None:

    if not source.exists():
        raise RuntimeError(
            f"Missing reusable component: {source}"
        )

    payload = load_json(
        contract
    )

    expected = payload.get(
        "component_sha256"
    )

    if (
        not isinstance(
            expected,
            str,
        )
        or
        sha256_file(
            source
        )
        !=
        expected
    ):
        raise RuntimeError(
            (
                "Previously verified reusable component changed: "
                f"{relative(source)}"
            )
        )


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.7.13 - 10.7.15"
    )

    print(
        "ERROR + LOADING + REUSABLE UI CONSISTENCY BUILD"
    )

    print("=" * 72)


    verify_1_4 = load_json(
        VERIFY_1_4_FILE
    )

    verify_5_8 = load_json(
        VERIFY_5_8_FILE
    )

    verify_9_12 = load_json(
        VERIFY_9_12_FILE
    )


    if (
        verify_9_12.get(
            "status"
        )
        !=
        "PASS"
    ):
        raise RuntimeError(
            "10.7.9-10.7.12 verification is not PASS."
        )


    for key in [
        "stage_10_7_9_complete",
        "stage_10_7_10_complete",
        "stage_10_7_11_complete",
        "stage_10_7_12_complete",
    ]:

        if (
            verify_9_12.get(
                key
            )
            is not True
        ):
            raise RuntimeError(
                f"Previous stage flag incomplete: {key}"
            )


    if (
        verify_9_12.get(
            "stage10_ready_for_10_7_13"
        )
        is not True
    ):
        raise RuntimeError(
            "10.7.12 did not authorize 10.7.13."
        )


    existing = [
        (
            MATCH_CARD_FILE,
            MATCH_CARD_CONTRACT,
        ),
        (
            PROBABILITY_BAR_FILE,
            PROBABILITY_BAR_CONTRACT,
        ),
        (
            OUTCOME_BADGE_FILE,
            OUTCOME_BADGE_CONTRACT,
        ),
        (
            CONFIDENCE_BADGE_FILE,
            CONFIDENCE_BADGE_CONTRACT,
        ),
        (
            UNCERTAINTY_BADGE_FILE,
            UNCERTAINTY_BADGE_CONTRACT,
        ),
        (
            CONTEXT_ALIGNMENT_BADGE_FILE,
            CONTEXT_ALIGNMENT_BADGE_CONTRACT,
        ),
        (
            CONTEXT_SCORE_FILE,
            CONTEXT_SCORE_CONTRACT,
        ),
        (
            TEAM_COMPARISON_ROW_FILE,
            TEAM_COMPARISON_ROW_CONTRACT,
        ),
        (
            RECENT_FORM_DISPLAY_FILE,
            RECENT_FORM_DISPLAY_CONTRACT,
        ),
        (
            INTELLIGENCE_EXPLANATION_FILE,
            INTELLIGENCE_EXPLANATION_CONTRACT,
        ),
        (
            FRESHNESS_INDICATOR_FILE,
            FRESHNESS_INDICATOR_CONTRACT,
        ),
        (
            EMPTY_STATE_FILE,
            EMPTY_STATE_CONTRACT,
        ),
    ]


    for source, contract in existing:

        verify_existing_component(
            source,
            contract,
        )


    existing_consistency = optional_json(
        CONSISTENCY_CONTRACT
    )


    if (
        existing_consistency
        and
        ERROR_STATE_FILE.exists()
        and
        LOADING_STATE_FILE.exists()
        and
        existing_consistency.get(
            "error_state_sha256"
        )
        ==
        sha256_file(
            ERROR_STATE_FILE
        )
        and
        existing_consistency.get(
            "loading_state_sha256"
        )
        ==
        sha256_file(
            LOADING_STATE_FILE
        )
    ):

        print()

        print(
            "10.7.13 - 10.7.15 already built."
        )

        print("=" * 72)

        print(
            "STAGE 10.7.13 ERRORSTATE: BUILT"
        )

        print(
            "STAGE 10.7.14 LOADINGSTATE: BUILT"
        )

        print(
            "STAGE 10.7.15 CONSISTENCY CONTRACT: BUILT"
        )

        print(
            "FINAL VERIFICATION STILL REQUIRED"
        )

        print("=" * 72)

        return


    refuse_unknown_existing_file(
        ERROR_STATE_FILE,
        ERROR_STATE_CONTRACT,
    )

    refuse_unknown_existing_file(
        LOADING_STATE_FILE,
        LOADING_STATE_CONTRACT,
    )


    save_text_atomic(
        ERROR_STATE_FILE,
        ERROR_STATE_SOURCE,
    )

    save_text_atomic(
        LOADING_STATE_FILE,
        LOADING_STATE_SOURCE,
    )


    error_contract = {
        "stage":
            "10.7.13",

        "version":
            "1.0.0",

        "name":
            "REUSABLE_ERROR_STATE",

        "status":
            "LOCKED",

        "source":
            relative(
                ERROR_STATE_FILE
            ),

        "component":
            "ErrorState",

        "responsibility":
            "PRESENT_CALLER_PROVIDED_ERROR",

        "presentation": {
            "title_direct":
                True,

            "message_direct":
                True,

            "optional_action":
                True,

            "built_in_retry_logic":
                False,

            "data_fetch":
                False,

            "stale_fallback":
                False,

            "error_classification":
                False,
        },

        "component_sha256":
            sha256_file(
                ERROR_STATE_FILE
            ),

        "dependency_identity": {
            relative(
                VERIFY_9_12_FILE
            ):
                identity(
                    VERIFY_9_12_FILE
                ),

            relative(
                EMPTY_STATE_CONTRACT
            ):
                identity(
                    EMPTY_STATE_CONTRACT
                ),
        },

        "promotion": {
            "stage10_7_13_complete":
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
        ERROR_STATE_CONTRACT,
        error_contract,
    )


    loading_contract = {
        "stage":
            "10.7.14",

        "version":
            "1.0.0",

        "name":
            "REUSABLE_LOADING_STATE",

        "status":
            "LOCKED",

        "source":
            relative(
                LOADING_STATE_FILE
            ),

        "component":
            "LoadingState",

        "responsibility":
            "PRESENT_LOADING_STATE_ONLY",

        "presentation": {
            "caller_label_supported":
                True,

            "default_label":
                "Loading FixtureIQ data...",

            "role_status":
                True,

            "aria_live":
                "polite",

            "aria_busy":
                True,

            "client_state":
                False,

            "timers":
                False,

            "data_fetch":
                False,
        },

        "component_sha256":
            sha256_file(
                LOADING_STATE_FILE
            ),

        "dependency_identity": {
            relative(
                ERROR_STATE_CONTRACT
            ):
                identity(
                    ERROR_STATE_CONTRACT
                ),
        },

        "promotion": {
            "stage10_7_14_complete":
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
        LOADING_STATE_CONTRACT,
        loading_contract,
    )


    components = {
        "MatchCard": {
            "source":
                MATCH_CARD_FILE,

            "contract":
                MATCH_CARD_CONTRACT,
        },

        "ProbabilityBar": {
            "source":
                PROBABILITY_BAR_FILE,

            "contract":
                PROBABILITY_BAR_CONTRACT,
        },

        "OutcomeBadge": {
            "source":
                OUTCOME_BADGE_FILE,

            "contract":
                OUTCOME_BADGE_CONTRACT,
        },

        "ConfidenceBadge": {
            "source":
                CONFIDENCE_BADGE_FILE,

            "contract":
                CONFIDENCE_BADGE_CONTRACT,
        },

        "UncertaintyBadge": {
            "source":
                UNCERTAINTY_BADGE_FILE,

            "contract":
                UNCERTAINTY_BADGE_CONTRACT,
        },

        "ContextAlignmentBadge": {
            "source":
                CONTEXT_ALIGNMENT_BADGE_FILE,

            "contract":
                CONTEXT_ALIGNMENT_BADGE_CONTRACT,
        },

        "ContextScore": {
            "source":
                CONTEXT_SCORE_FILE,

            "contract":
                CONTEXT_SCORE_CONTRACT,
        },

        "TeamComparisonRow": {
            "source":
                TEAM_COMPARISON_ROW_FILE,

            "contract":
                TEAM_COMPARISON_ROW_CONTRACT,
        },

        "RecentFormDisplay": {
            "source":
                RECENT_FORM_DISPLAY_FILE,

            "contract":
                RECENT_FORM_DISPLAY_CONTRACT,
        },

        "IntelligenceExplanation": {
            "source":
                INTELLIGENCE_EXPLANATION_FILE,

            "contract":
                INTELLIGENCE_EXPLANATION_CONTRACT,
        },

        "FreshnessIndicator": {
            "source":
                FRESHNESS_INDICATOR_FILE,

            "contract":
                FRESHNESS_INDICATOR_CONTRACT,
        },

        "EmptyState": {
            "source":
                EMPTY_STATE_FILE,

            "contract":
                EMPTY_STATE_CONTRACT,
        },

        "ErrorState": {
            "source":
                ERROR_STATE_FILE,

            "contract":
                ERROR_STATE_CONTRACT,
        },

        "LoadingState": {
            "source":
                LOADING_STATE_FILE,

            "contract":
                LOADING_STATE_CONTRACT,
        },
    }


    consistency_components = {}


    for name, value in components.items():

        source = value[
            "source"
        ]

        contract = value[
            "contract"
        ]

        consistency_components[
            name
        ] = {
            "source":
                relative(
                    source
                ),

            "contract":
                relative(
                    contract
                ),

            "component_sha256":
                sha256_file(
                    source
                ),

            "contract_sha256":
                sha256_file(
                    contract
                ),
        }


    consistency_contract = {
        "stage":
            "10.7.15",

        "version":
            "1.0.0",

        "name":
            "REUSABLE_UI_CONSISTENCY",

        "status":
            "LOCKED_PENDING_VERIFICATION",

        "expected_component_count":
            14,

        "components":
            consistency_components,

        "consistency_rules": {
            "stage10_presentation_only":
                True,

            "direct_provider_access":
                False,

            "direct_artifact_access":
                False,

            "direct_fetch":
                False,

            "probability_recalculation":
                False,

            "prediction_derivation":
                False,

            "context_recalculation":
                False,

            "explanation_generation":
                False,

            "frontend_freshness_derivation":
                False,

            "built_in_retry_logic":
                False,

            "server_safe_by_default":
                True,
        },

        "verification_chain": {
            "10.7.1-10.7.4":
                relative(
                    VERIFY_1_4_FILE
                ),

            "10.7.5-10.7.8":
                relative(
                    VERIFY_5_8_FILE
                ),

            "10.7.9-10.7.12":
                relative(
                    VERIFY_9_12_FILE
                ),
        },

        "error_state_sha256":
            sha256_file(
                ERROR_STATE_FILE
            ),

        "loading_state_sha256":
            sha256_file(
                LOADING_STATE_FILE
            ),

        "dependency_identity": {
            relative(
                VERIFY_1_4_FILE
            ):
                identity(
                    VERIFY_1_4_FILE
                ),

            relative(
                VERIFY_5_8_FILE
            ):
                identity(
                    VERIFY_5_8_FILE
                ),

            relative(
                VERIFY_9_12_FILE
            ):
                identity(
                    VERIFY_9_12_FILE
                ),

            relative(
                ERROR_STATE_CONTRACT
            ):
                identity(
                    ERROR_STATE_CONTRACT
                ),

            relative(
                LOADING_STATE_CONTRACT
            ):
                identity(
                    LOADING_STATE_CONTRACT
                ),
        },

        "promotion": {
            "stage10_7_15_complete":
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
        CONSISTENCY_CONTRACT,
        consistency_contract,
    )


    print()

    print(
        f"ErrorState: {relative(ERROR_STATE_FILE)}"
    )

    print(
        f"LoadingState: {relative(LOADING_STATE_FILE)}"
    )

    print(
        (
            "Consistency contract: "
            f"{relative(CONSISTENCY_CONTRACT)}"
        )
    )

    print()

    print("=" * 72)

    print(
        "STAGE 10.7.13 ERRORSTATE: BUILT"
    )

    print(
        "STAGE 10.7.14 LOADINGSTATE: BUILT"
    )

    print(
        "STAGE 10.7.15 CONSISTENCY CONTRACT: BUILT"
    )

    print(
        "FINAL VERIFICATION STILL REQUIRED"
    )

    print("=" * 72)


if __name__ == "__main__":
    main()
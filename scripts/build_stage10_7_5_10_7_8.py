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
    / "stage10_7_1_10_7_4_verification.json"
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


DOMAIN_TYPES_FILE = (
    FRONTEND
    / "lib"
    / "domain"
    / "types.ts"
)


PROBABILITY_BAR_CONTRACT_FILE = (
    DOCS
    / "frontend_probability_bar_contract.json"
)

OUTCOME_BADGE_CONTRACT_FILE = (
    DOCS
    / "frontend_outcome_badge_contract.json"
)

CONFIDENCE_BADGE_CONTRACT_FILE = (
    DOCS
    / "frontend_confidence_badge_contract.json"
)


UNCERTAINTY_BADGE_CONTRACT_FILE = (
    DOCS
    / "frontend_uncertainty_badge_contract.json"
)

CONTEXT_ALIGNMENT_BADGE_CONTRACT_FILE = (
    DOCS
    / "frontend_context_alignment_badge_contract.json"
)

CONTEXT_SCORE_CONTRACT_FILE = (
    DOCS
    / "frontend_context_score_contract.json"
)

TEAM_COMPARISON_ROW_CONTRACT_FILE = (
    DOCS
    / "frontend_team_comparison_row_contract.json"
)


UNCERTAINTY_BADGE_SOURCE = '''import type {
  UncertaintyBand,
} from "../../lib/domain/types";


type UncertaintyBadgeProps =
  Readonly<{
    band:
      UncertaintyBand;
  }>;


export function UncertaintyBadge({
  band,
}: UncertaintyBadgeProps) {

  return (
    <span
      aria-label={`Uncertainty: ${band}`}
      className="
        inline-flex items-center
        rounded-full
        border border-slate-300
        bg-white
        px-3 py-1
        text-xs font-semibold
        text-slate-900
      "
      data-fixtureiq-component="uncertainty-badge"
      data-uncertainty-band={
        band
      }
    >
      {band}
    </span>
  );
}
'''


CONTEXT_ALIGNMENT_BADGE_SOURCE = '''import type {
  ContextAlignment,
} from "../../lib/domain/types";


type ContextAlignmentBadgeProps =
  Readonly<{
    alignment:
      ContextAlignment;
  }>;


export function ContextAlignmentBadge({
  alignment,
}: ContextAlignmentBadgeProps) {

  return (
    <span
      aria-label={`Context alignment: ${alignment}`}
      className="
        inline-flex items-center
        rounded-full
        border border-slate-300
        bg-white
        px-3 py-1
        text-xs font-semibold
        text-slate-900
      "
      data-fixtureiq-component="context-alignment-badge"
      data-context-alignment={
        alignment
      }
    >
      {alignment}
    </span>
  );
}
'''


CONTEXT_SCORE_SOURCE = '''import type {
  ContextSupportScore,
} from "../../lib/domain/types";


const signedIntegerFormatter =
  new Intl.NumberFormat(
    "en-GB",
    {
      maximumFractionDigits: 0,
      signDisplay: "exceptZero",
    },
  );


type ContextScoreProps =
  Readonly<{
    score:
      ContextSupportScore;
  }>;


export function ContextScore({
  score,
}: ContextScoreProps) {

  return (
    <span
      aria-label={`Context support score: ${score}`}
      className="
        inline-flex items-center
        rounded-md
        border border-slate-200
        bg-slate-50
        px-2.5 py-1
        text-sm font-semibold
        tabular-nums
        text-slate-950
      "
      data-fixtureiq-component="context-score"
      data-context-score={
        score
      }
    >
      {signedIntegerFormatter.format(
        score,
      )}
    </span>
  );
}
'''


TEAM_COMPARISON_ROW_SOURCE = '''import type {
  ReactNode,
} from "react";


type TeamComparisonRowProps =
  Readonly<{
    label:
      string;

    homeTeamName:
      string;

    awayTeamName:
      string;

    homeValue:
      ReactNode;

    awayValue:
      ReactNode;
  }>;


export function TeamComparisonRow({
  label,
  homeTeamName,
  awayTeamName,
  homeValue,
  awayValue,
}: TeamComparisonRowProps) {

  return (
    <div
      className="
        grid
        grid-cols-[minmax(0,1fr)_minmax(7rem,auto)_minmax(0,1fr)]
        items-center
        gap-3
        border-b border-slate-100
        py-3
        last:border-b-0
      "
      data-fixtureiq-component="team-comparison-row"
    >
      <div
        className="
          min-w-0 text-left
        "
      >
        <p
          className="
            truncate text-xs
            text-slate-500
          "
        >
          {homeTeamName}
        </p>

        <div
          className="
            mt-1 font-semibold
            text-slate-950
          "
          data-team-comparison-side="home"
        >
          {homeValue}
        </div>
      </div>

      <p
        className="
          text-center text-xs
          font-medium
          text-slate-500
        "
        data-team-comparison-label
      >
        {label}
      </p>

      <div
        className="
          min-w-0 text-right
        "
      >
        <p
          className="
            truncate text-xs
            text-slate-500
          "
        >
          {awayTeamName}
        </p>

        <div
          className="
            mt-1 font-semibold
            text-slate-950
          "
          data-team-comparison-side="away"
        >
          {awayValue}
        </div>
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
            "without matching locked Stage 10.7 contract. "
            "Refusing to overwrite it."
        )
    )


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.7.5 - 10.7.8"
    )

    print(
        "REUSABLE INTELLIGENCE + TEAM COMPARISON UI BUILD"
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
            "10.7.1-10.7.4 verification is not PASS."
        )


    for key in [
        "stage_10_7_1_complete",
        "stage_10_7_2_complete",
        "stage_10_7_3_complete",
        "stage_10_7_4_complete",
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
            "stage10_ready_for_10_7_5"
        )
        is not True
    ):
        raise RuntimeError(
            "10.7.4 did not authorize 10.7.5."
        )


    required = [
        DOMAIN_TYPES_FILE,
        PROBABILITY_BAR_FILE,
        OUTCOME_BADGE_FILE,
        CONFIDENCE_BADGE_FILE,
        PROBABILITY_BAR_CONTRACT_FILE,
        OUTCOME_BADGE_CONTRACT_FILE,
        CONFIDENCE_BADGE_CONTRACT_FILE,
    ]


    for path in required:

        if not path.exists():
            raise RuntimeError(
                f"Missing source: {path}"
            )


    confidence_contract = load_json(
        CONFIDENCE_BADGE_CONTRACT_FILE
    )


    if (
        confidence_contract.get(
            "component_sha256"
        )
        !=
        sha256_file(
            CONFIDENCE_BADGE_FILE
        )
    ):
        raise RuntimeError(
            "Verified 10.7.4 ConfidenceBadge changed."
        )


    domain_source = (
        DOMAIN_TYPES_FILE.read_text(
            encoding="utf-8"
        )
    )


    for domain_type in [
        "UncertaintyBand",
        "ContextAlignment",
        "ContextSupportScore",
    ]:

        if (
            domain_type
            not in
            domain_source
        ):
            raise RuntimeError(
                f"Required domain type missing: {domain_type}"
            )


    final_contract = optional_json(
        TEAM_COMPARISON_ROW_CONTRACT_FILE
    )


    if (
        final_contract
        and
        UNCERTAINTY_BADGE_FILE.exists()
        and
        CONTEXT_ALIGNMENT_BADGE_FILE.exists()
        and
        CONTEXT_SCORE_FILE.exists()
        and
        TEAM_COMPARISON_ROW_FILE.exists()
        and
        final_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            TEAM_COMPARISON_ROW_FILE
        )
    ):

        print()

        print(
            "10.7.5 - 10.7.8 already built."
        )

        print("=" * 72)

        print(
            "STAGE 10.7.5 UNCERTAINTYBADGE: BUILT"
        )

        print(
            "STAGE 10.7.6 CONTEXTALIGNMENTBADGE: BUILT"
        )

        print(
            "STAGE 10.7.7 CONTEXTSCORE: BUILT"
        )

        print(
            "STAGE 10.7.8 TEAMCOMPARISONROW: BUILT"
        )

        print(
            "VERIFICATION STILL REQUIRED"
        )

        print("=" * 72)

        return


    refuse_unknown_existing_file(
        UNCERTAINTY_BADGE_FILE,
        UNCERTAINTY_BADGE_CONTRACT_FILE,
    )

    refuse_unknown_existing_file(
        CONTEXT_ALIGNMENT_BADGE_FILE,
        CONTEXT_ALIGNMENT_BADGE_CONTRACT_FILE,
    )

    refuse_unknown_existing_file(
        CONTEXT_SCORE_FILE,
        CONTEXT_SCORE_CONTRACT_FILE,
    )

    refuse_unknown_existing_file(
        TEAM_COMPARISON_ROW_FILE,
        TEAM_COMPARISON_ROW_CONTRACT_FILE,
    )


    protected = {
        "probability_bar_sha256":
            sha256_file(
                PROBABILITY_BAR_FILE
            ),

        "outcome_badge_sha256":
            sha256_file(
                OUTCOME_BADGE_FILE
            ),

        "confidence_badge_sha256":
            sha256_file(
                CONFIDENCE_BADGE_FILE
            ),

        "domain_types_sha256":
            sha256_file(
                DOMAIN_TYPES_FILE
            ),
    }


    save_text_atomic(
        UNCERTAINTY_BADGE_FILE,
        UNCERTAINTY_BADGE_SOURCE,
    )

    save_text_atomic(
        CONTEXT_ALIGNMENT_BADGE_FILE,
        CONTEXT_ALIGNMENT_BADGE_SOURCE,
    )

    save_text_atomic(
        CONTEXT_SCORE_FILE,
        CONTEXT_SCORE_SOURCE,
    )

    save_text_atomic(
        TEAM_COMPARISON_ROW_FILE,
        TEAM_COMPARISON_ROW_SOURCE,
    )


    uncertainty_contract = {
        "stage":
            "10.7.5",

        "version":
            "1.0.0",

        "name":
            "REUSABLE_UNCERTAINTY_BADGE",

        "status":
            "LOCKED",

        "source":
            relative(
                UNCERTAINTY_BADGE_FILE
            ),

        "component":
            "UncertaintyBadge",

        "domain_type":
            "UncertaintyBand",

        "authority":
            "STAGE_9_UNCERTAINTY_BAND",

        "presentation": {
            "band_direct":
                True,

            "threshold_logic":
                False,

            "entropy_calculation":
                False,

            "band_derivation":
                False,

            "text_always_present":
                True,
        },

        "component_sha256":
            sha256_file(
                UNCERTAINTY_BADGE_FILE
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
                CONFIDENCE_BADGE_CONTRACT_FILE
            ):
                identity(
                    CONFIDENCE_BADGE_CONTRACT_FILE
                ),

            relative(
                DOMAIN_TYPES_FILE
            ):
                identity(
                    DOMAIN_TYPES_FILE
                ),
        },

        "promotion": {
            "stage10_7_5_complete":
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
        UNCERTAINTY_BADGE_CONTRACT_FILE,
        uncertainty_contract,
    )


    alignment_contract = {
        "stage":
            "10.7.6",

        "version":
            "1.0.0",

        "name":
            "REUSABLE_CONTEXT_ALIGNMENT_BADGE",

        "status":
            "LOCKED",

        "source":
            relative(
                CONTEXT_ALIGNMENT_BADGE_FILE
            ),

        "component":
            "ContextAlignmentBadge",

        "domain_type":
            "ContextAlignment",

        "authority":
            "STAGE_9_CONTEXT_ALIGNMENT",

        "presentation": {
            "alignment_direct":
                True,

            "support_score_inspection":
                False,

            "alignment_rules":
                False,

            "classification_logic":
                False,

            "text_always_present":
                True,
        },

        "component_sha256":
            sha256_file(
                CONTEXT_ALIGNMENT_BADGE_FILE
            ),

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                UNCERTAINTY_BADGE_CONTRACT_FILE
            ):
                identity(
                    UNCERTAINTY_BADGE_CONTRACT_FILE
                ),

            relative(
                DOMAIN_TYPES_FILE
            ):
                identity(
                    DOMAIN_TYPES_FILE
                ),
        },

        "promotion": {
            "stage10_7_6_complete":
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
        CONTEXT_ALIGNMENT_BADGE_CONTRACT_FILE,
        alignment_contract,
    )


    score_contract = {
        "stage":
            "10.7.7",

        "version":
            "1.0.0",

        "name":
            "REUSABLE_CONTEXT_SCORE",

        "status":
            "LOCKED",

        "source":
            relative(
                CONTEXT_SCORE_FILE
            ),

        "component":
            "ContextScore",

        "domain_type":
            "ContextSupportScore",

        "authority":
            "STAGE_9_CONTEXT_SUPPORT_SCORE",

        "allowed_range":
            [
                -5,
                5,
            ],

        "presentation": {
            "score_direct":
                True,

            "signed_display_only":
                True,

            "signal_counting":
                False,

            "score_calculation":
                False,

            "alignment_derivation":
                False,
        },

        "component_sha256":
            sha256_file(
                CONTEXT_SCORE_FILE
            ),

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                CONTEXT_ALIGNMENT_BADGE_CONTRACT_FILE
            ):
                identity(
                    CONTEXT_ALIGNMENT_BADGE_CONTRACT_FILE
                ),

            relative(
                DOMAIN_TYPES_FILE
            ):
                identity(
                    DOMAIN_TYPES_FILE
                ),
        },

        "promotion": {
            "stage10_7_7_complete":
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
        CONTEXT_SCORE_CONTRACT_FILE,
        score_contract,
    )


    comparison_contract = {
        "stage":
            "10.7.8",

        "version":
            "1.0.0",

        "name":
            "REUSABLE_TEAM_COMPARISON_ROW",

        "status":
            "LOCKED",

        "source":
            relative(
                TEAM_COMPARISON_ROW_FILE
            ),

        "component":
            "TeamComparisonRow",

        "value_type":
            "ReactNode",

        "responsibility":
            "PRESENT_TWO_TEAM_VALUES_ONLY",

        "presentation": {
            "home_value_direct":
                True,

            "away_value_direct":
                True,

            "label_direct":
                True,

            "team_names_direct":
                True,

            "winner_derivation":
                False,

            "difference_calculation":
                False,

            "ranking_logic":
                False,

            "normalization":
                False,
        },

        "component_sha256":
            sha256_file(
                TEAM_COMPARISON_ROW_FILE
            ),

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                CONTEXT_SCORE_CONTRACT_FILE
            ):
                identity(
                    CONTEXT_SCORE_CONTRACT_FILE
                ),

            relative(
                DOMAIN_TYPES_FILE
            ):
                identity(
                    DOMAIN_TYPES_FILE
                ),
        },

        "promotion": {
            "stage10_7_8_complete":
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
        TEAM_COMPARISON_ROW_CONTRACT_FILE,
        comparison_contract,
    )


    print()

    print(
        "Reusable components:"
    )

    for path in [
        UNCERTAINTY_BADGE_FILE,
        CONTEXT_ALIGNMENT_BADGE_FILE,
        CONTEXT_SCORE_FILE,
        TEAM_COMPARISON_ROW_FILE,
    ]:

        print(
            f"  {relative(path)}"
        )


    print()

    print("=" * 72)

    print(
        "STAGE 10.7.5 UNCERTAINTYBADGE: BUILT"
    )

    print(
        "STAGE 10.7.6 CONTEXTALIGNMENTBADGE: BUILT"
    )

    print(
        "STAGE 10.7.7 CONTEXTSCORE: BUILT"
    )

    print(
        "STAGE 10.7.8 TEAMCOMPARISONROW: BUILT"
    )

    print(
        "VERIFICATION STILL REQUIRED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
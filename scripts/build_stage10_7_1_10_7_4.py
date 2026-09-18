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
    / "stage10_6_final_verification.json"
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


DOMAIN_TYPES_FILE = (
    FRONTEND
    / "lib"
    / "domain"
    / "types.ts"
)

PROBABILITY_FORMATTER_FILE = (
    FRONTEND
    / "lib"
    / "formatters"
    / "probability.ts"
)


MATCH_CARD_CONTRACT_FILE = (
    DOCS
    / "frontend_reusable_match_card_contract.json"
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


PROBABILITY_BAR_SOURCE = '''import {
  formatProbability,
} from "../../lib/formatters/probability";


type ProbabilityBarProps =
  Readonly<{
    label:
      string;

    value:
      number;

    sourceField?:
      string;
  }>;


export function ProbabilityBar({
  label,
  value,
  sourceField,
}: ProbabilityBarProps) {

  return (
    <div
      data-fixtureiq-component="probability-bar"
      data-source-field={
        sourceField
      }
    >
      <div
        className="
          flex items-center
          justify-between gap-4
        "
      >
        <span
          className="
            text-sm font-medium
            text-slate-700
          "
        >
          {label}
        </span>

        <span
          className="
            text-sm font-semibold
            tabular-nums
            text-slate-950
          "
        >
          {formatProbability(
            value,
          )}
        </span>
      </div>

      <progress
        aria-label={`${label} probability`}
        className="
          mt-2 block h-2
          w-full overflow-hidden
          rounded-full
        "
        max={1}
        value={
          value
        }
      >
        {formatProbability(
          value,
        )}
      </progress>
    </div>
  );
}
'''


OUTCOME_BADGE_SOURCE = '''import type {
  OutcomeLabel,
} from "../../lib/domain/types";


type OutcomeBadgeProps =
  Readonly<{
    outcome:
      OutcomeLabel;
  }>;


export function OutcomeBadge({
  outcome,
}: OutcomeBadgeProps) {

  return (
    <span
      aria-label={`Predicted outcome: ${outcome}`}
      className="
        inline-flex items-center
        rounded-full
        border border-slate-300
        bg-slate-50
        px-3 py-1
        text-xs font-semibold
        text-slate-900
      "
      data-fixtureiq-component="outcome-badge"
      data-outcome={
        outcome
      }
    >
      {outcome}
    </span>
  );
}
'''


CONFIDENCE_BADGE_SOURCE = '''import type {
  ConfidenceBand,
} from "../../lib/domain/types";


type ConfidenceBadgeProps =
  Readonly<{
    band:
      ConfidenceBand;
  }>;


export function ConfidenceBadge({
  band,
}: ConfidenceBadgeProps) {

  return (
    <span
      aria-label={`Confidence: ${band}`}
      className="
        inline-flex items-center
        rounded-full
        border border-slate-300
        bg-white
        px-3 py-1
        text-xs font-semibold
        text-slate-900
      "
      data-fixtureiq-component="confidence-badge"
      data-confidence-band={
        band
      }
    >
      {band}
    </span>
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
    sha_key: str,
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
            sha_key
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
        "FixtureIQ Stage 10.7.1 - 10.7.4"
    )

    print(
        "REUSABLE FOOTBALL UI FOUNDATION BUILD"
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
            "Stage 10.6 final verification is not PASS."
        )


    if (
        previous.get(
            "stage10_6_complete"
        )
        is not True
    ):
        raise RuntimeError(
            "Stage 10.6 is not complete."
        )


    if (
        previous.get(
            "stage10_ready_for_10_7_1"
        )
        is not True
    ):
        raise RuntimeError(
            "Stage 10.6 did not authorize 10.7.1."
        )


    required = [
        MATCH_CARD_FILE,
        DOMAIN_TYPES_FILE,
        PROBABILITY_FORMATTER_FILE,
    ]


    for path in required:

        if not path.exists():
            raise RuntimeError(
                f"Missing source: {path}"
            )


    match_card_source = (
        MATCH_CARD_FILE.read_text(
            encoding="utf-8"
        )
    )


    required_match_card_tokens = [
        "export function MatchCard",
        'data-fixtureiq-component="match-card"',
        "homeTeamName",
        "awayTeamName",
        "kickoffUtc",
        "stage7_prob_home_win",
        "stage7_prob_draw",
        "stage7_prob_away_win",
        "stage7_predicted_label",
        "stage7_confidence",
        "confidence_band",
        "uncertainty_band",
        "context_alignment",
        "explanation_headline",
        "explanation_summary",
    ]


    for token in required_match_card_tokens:

        if (
            token
            not in
            match_card_source
        ):
            raise RuntimeError(
                (
                    "Existing MatchCard does not match "
                    f"locked dashboard behavior: {token}"
                )
            )


    match_card_sha = sha256_file(
        MATCH_CARD_FILE
    )


    final_contract = optional_json(
        CONFIDENCE_BADGE_CONTRACT_FILE
    )


    if (
        final_contract
        and
        PROBABILITY_BAR_FILE.exists()
        and
        OUTCOME_BADGE_FILE.exists()
        and
        CONFIDENCE_BADGE_FILE.exists()
        and
        final_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            CONFIDENCE_BADGE_FILE
        )
    ):

        print()

        print(
            "10.7.1 - 10.7.4 already built."
        )

        print("=" * 72)

        print(
            "STAGE 10.7.1 MATCHCARD: BUILT"
        )

        print(
            "STAGE 10.7.2 PROBABILITYBAR: BUILT"
        )

        print(
            "STAGE 10.7.3 OUTCOMEBADGE: BUILT"
        )

        print(
            "STAGE 10.7.4 CONFIDENCEBADGE: BUILT"
        )

        print(
            "VERIFICATION STILL REQUIRED"
        )

        print("=" * 72)

        return


    refuse_unknown_existing_file(
        PROBABILITY_BAR_FILE,
        PROBABILITY_BAR_CONTRACT_FILE,
        "component_sha256",
    )

    refuse_unknown_existing_file(
        OUTCOME_BADGE_FILE,
        OUTCOME_BADGE_CONTRACT_FILE,
        "component_sha256",
    )

    refuse_unknown_existing_file(
        CONFIDENCE_BADGE_FILE,
        CONFIDENCE_BADGE_CONTRACT_FILE,
        "component_sha256",
    )


    save_text_atomic(
        PROBABILITY_BAR_FILE,
        PROBABILITY_BAR_SOURCE,
    )

    save_text_atomic(
        OUTCOME_BADGE_FILE,
        OUTCOME_BADGE_SOURCE,
    )

    save_text_atomic(
        CONFIDENCE_BADGE_FILE,
        CONFIDENCE_BADGE_SOURCE,
    )


    match_card_contract = {
        "stage":
            "10.7.1",

        "version":
            "1.0.0",

        "name":
            "REUSABLE_MATCH_CARD",

        "status":
            "LOCKED",

        "canonical_existing_component":
            True,

        "source":
            relative(
                MATCH_CARD_FILE
            ),

        "component":
            "MatchCard",

        "authority_boundary": {
            "fixture_identity":
                "STAGE_9_JOIN",

            "probabilities":
                "STAGE_7",

            "predicted_outcome":
                "STAGE_7",

            "confidence_value":
                "STAGE_7",

            "confidence_band":
                "STAGE_9",

            "uncertainty_band":
                "STAGE_9",

            "context_alignment":
                "STAGE_9",

            "explanation":
                "STAGE_9",

            "stage10_role":
                "PRESENTATION_ONLY",
        },

        "integrity": {
            "existing_component_rewritten":
                False,

            "prediction_logic":
                False,

            "probability_recalculation":
                False,

            "frontend_argmax":
                False,

            "direct_fetch":
                False,
        },

        "component_sha256":
            match_card_sha,

        "dependency_identity": {
            relative(
                PREVIOUS_FILE
            ):
                identity(
                    PREVIOUS_FILE
                ),

            relative(
                DOMAIN_TYPES_FILE
            ):
                identity(
                    DOMAIN_TYPES_FILE
                ),
        },

        "promotion": {
            "stage10_7_1_complete":
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
        MATCH_CARD_CONTRACT_FILE,
        match_card_contract,
    )


    probability_contract = {
        "stage":
            "10.7.2",

        "version":
            "1.0.0",

        "name":
            "REUSABLE_PROBABILITY_BAR",

        "status":
            "LOCKED",

        "source":
            relative(
                PROBABILITY_BAR_FILE
            ),

        "component":
            "ProbabilityBar",

        "authority":
            "CALLER_PROVIDED_BACKEND_PROBABILITY",

        "presentation": {
            "raw_value_passed_to_progress":
                True,

            "max":
                1,

            "display_formatter":
                "formatProbability",

            "display_rounding_only":
                True,

            "clamping":
                False,

            "normalization":
                False,

            "recalibration":
                False,

            "probability_derivation":
                False,
        },

        "component_sha256":
            sha256_file(
                PROBABILITY_BAR_FILE
            ),

        "dependency_identity": {
            relative(
                MATCH_CARD_CONTRACT_FILE
            ):
                identity(
                    MATCH_CARD_CONTRACT_FILE
                ),

            relative(
                PROBABILITY_FORMATTER_FILE
            ):
                identity(
                    PROBABILITY_FORMATTER_FILE
                ),
        },

        "promotion": {
            "stage10_7_2_complete":
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
        PROBABILITY_BAR_CONTRACT_FILE,
        probability_contract,
    )


    outcome_contract = {
        "stage":
            "10.7.3",

        "version":
            "1.0.0",

        "name":
            "REUSABLE_OUTCOME_BADGE",

        "status":
            "LOCKED",

        "source":
            relative(
                OUTCOME_BADGE_FILE
            ),

        "component":
            "OutcomeBadge",

        "domain_type":
            "OutcomeLabel",

        "authority":
            "STAGE_7_PREDICTED_LABEL",

        "presentation": {
            "label_direct":
                True,

            "frontend_argmax":
                False,

            "probability_inspection":
                False,

            "outcome_reclassification":
                False,

            "text_always_present":
                True,
        },

        "component_sha256":
            sha256_file(
                OUTCOME_BADGE_FILE
            ),

        "dependency_identity": {
            relative(
                PROBABILITY_BAR_CONTRACT_FILE
            ):
                identity(
                    PROBABILITY_BAR_CONTRACT_FILE
                ),

            relative(
                DOMAIN_TYPES_FILE
            ):
                identity(
                    DOMAIN_TYPES_FILE
                ),
        },

        "promotion": {
            "stage10_7_3_complete":
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
        OUTCOME_BADGE_CONTRACT_FILE,
        outcome_contract,
    )


    confidence_contract = {
        "stage":
            "10.7.4",

        "version":
            "1.0.0",

        "name":
            "REUSABLE_CONFIDENCE_BADGE",

        "status":
            "LOCKED",

        "source":
            relative(
                CONFIDENCE_BADGE_FILE
            ),

        "component":
            "ConfidenceBadge",

        "domain_type":
            "ConfidenceBand",

        "authority":
            "STAGE_9_CONFIDENCE_BAND",

        "presentation": {
            "band_direct":
                True,

            "threshold_logic":
                False,

            "band_derivation":
                False,

            "confidence_recalculation":
                False,

            "text_always_present":
                True,
        },

        "component_sha256":
            sha256_file(
                CONFIDENCE_BADGE_FILE
            ),

        "dependency_identity": {
            relative(
                OUTCOME_BADGE_CONTRACT_FILE
            ):
                identity(
                    OUTCOME_BADGE_CONTRACT_FILE
                ),

            relative(
                DOMAIN_TYPES_FILE
            ):
                identity(
                    DOMAIN_TYPES_FILE
                ),
        },

        "promotion": {
            "stage10_7_4_complete":
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
        CONFIDENCE_BADGE_CONTRACT_FILE,
        confidence_contract,
    )


    print()

    print(
        "Canonical MatchCard:"
    )

    print(
        f"  {relative(MATCH_CARD_FILE)}"
    )


    print()

    print(
        "Reusable primitives:"
    )

    for path in [
        PROBABILITY_BAR_FILE,
        OUTCOME_BADGE_FILE,
        CONFIDENCE_BADGE_FILE,
    ]:

        print(
            f"  {relative(path)}"
        )


    print()

    print("=" * 72)

    print(
        "STAGE 10.7.1 MATCHCARD: BUILT"
    )

    print(
        "STAGE 10.7.2 PROBABILITYBAR: BUILT"
    )

    print(
        "STAGE 10.7.3 OUTCOMEBADGE: BUILT"
    )

    print(
        "STAGE 10.7.4 CONFIDENCEBADGE: BUILT"
    )

    print(
        "VERIFICATION STILL REQUIRED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
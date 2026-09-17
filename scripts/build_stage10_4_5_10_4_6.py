from __future__ import annotations

import hashlib
import json
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


PREVIOUS_VERIFICATION_FILE = (
    FRONTEND_DATA
    / "stage10_4_3_10_4_4_verification.json"
)

KICKOFF_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_kickoff_contract.json"
)

LOADER_CONTRACT_FILE = (
    DOCS
    / "frontend_upcoming_dashboard_loader_contract.json"
)

MATCH_CARD_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-card.tsx"
)

LOADER_FILE = (
    FRONTEND
    / "lib"
    / "dashboard"
    / "load-upcoming-matches.ts"
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

PROBABILITY_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_probabilities_contract.json"
)

OUTCOME_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_predicted_outcome_contract.json"
)


PROBABILITY_FORMATTER_SOURCE = '''const probabilityFormatter =
  new Intl.NumberFormat(
    "en-GB",
    {
      style: "percent",
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    },
  );


export function formatProbability(
  value: number,
): string {
  if (
    !Number.isFinite(value)
    ||
    value < 0
    ||
    value > 1
  ) {
    throw new RangeError(
      "Probability must be a finite number between 0 and 1.",
    );
  }

  return probabilityFormatter.format(
    value,
  );
}
'''


PROBABILITY_SOURCE = '''import type {
  ReactNode,
} from "react";

import {
  formatKickoffUtc,
} from "../../lib/formatters/kickoff";

import {
  formatProbability,
} from "../../lib/formatters/probability";


type MatchCardProps =
  Readonly<{
    homeTeamName: string;
    awayTeamName: string;
    kickoffUtc: string;

    stage7_prob_home_win: number;
    stage7_prob_draw: number;
    stage7_prob_away_win: number;

    children?: ReactNode;
  }>;


export function MatchCard({
  homeTeamName,
  awayTeamName,
  kickoffUtc,
  stage7_prob_home_win,
  stage7_prob_draw,
  stage7_prob_away_win,
  children,
}: MatchCardProps) {
  const kickoffLabel =
    formatKickoffUtc(
      kickoffUtc,
    );

  return (
    <article
      aria-label={`${homeTeamName} vs ${awayTeamName}`}
      className="
        overflow-hidden rounded-xl
        border border-slate-200
        bg-white shadow-sm
      "
      data-fixtureiq-component="match-card"
    >
      <header
        className="
          border-b border-slate-100
          px-5 py-5
          sm:px-6
        "
      >
        <div
          className="
            grid
            grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]
            items-center gap-3
          "
        >
          <div className="min-w-0">
            <p
              className="
                text-xs font-medium uppercase
                tracking-wide text-slate-500
              "
            >
              Home
            </p>

            <h2
              className="
                mt-1 break-words
                text-base font-semibold
                text-slate-950
              "
            >
              {homeTeamName}
            </h2>
          </div>

          <span
            aria-hidden="true"
            className="
              text-sm font-medium
              text-slate-400
            "
          >
            vs
          </span>

          <div className="min-w-0 text-right">
            <p
              className="
                text-xs font-medium uppercase
                tracking-wide text-slate-500
              "
            >
              Away
            </p>

            <h2
              className="
                mt-1 break-words
                text-base font-semibold
                text-slate-950
              "
            >
              {awayTeamName}
            </h2>
          </div>
        </div>

        <div
          className="
            mt-4 flex items-center
            justify-center
            text-sm text-slate-600
          "
        >
          <span className="sr-only">
            Kickoff:
          </span>

          <time dateTime={kickoffUtc}>
            {kickoffLabel} UTC
          </time>
        </div>
      </header>

      <div
        className="
          space-y-5
          px-5 py-5
          sm:px-6
        "
      >
        <section
          aria-label="Three-way outcome probabilities"
        >
          <h3
            className="
              text-xs font-semibold uppercase
              tracking-wide text-slate-500
            "
          >
            Outcome probabilities
          </h3>

          <dl
            className="
              mt-3 grid grid-cols-3
              gap-2
            "
          >
            <div
              className="
                rounded-lg bg-slate-50
                px-3 py-3 text-center
              "
            >
              <dt
                className="
                  text-xs font-medium
                  text-slate-500
                "
              >
                Home
              </dt>

              <dd
                className="
                  mt-1 text-base font-semibold
                  tabular-nums text-slate-950
                "
                data-stage7-field="stage7_prob_home_win"
              >
                {formatProbability(
                  stage7_prob_home_win,
                )}
              </dd>
            </div>

            <div
              className="
                rounded-lg bg-slate-50
                px-3 py-3 text-center
              "
            >
              <dt
                className="
                  text-xs font-medium
                  text-slate-500
                "
              >
                Draw
              </dt>

              <dd
                className="
                  mt-1 text-base font-semibold
                  tabular-nums text-slate-950
                "
                data-stage7-field="stage7_prob_draw"
              >
                {formatProbability(
                  stage7_prob_draw,
                )}
              </dd>
            </div>

            <div
              className="
                rounded-lg bg-slate-50
                px-3 py-3 text-center
              "
            >
              <dt
                className="
                  text-xs font-medium
                  text-slate-500
                "
              >
                Away
              </dt>

              <dd
                className="
                  mt-1 text-base font-semibold
                  tabular-nums text-slate-950
                "
                data-stage7-field="stage7_prob_away_win"
              >
                {formatProbability(
                  stage7_prob_away_win,
                )}
              </dd>
            </div>
          </dl>
        </section>

        {children ? (
          <div
            className="
              border-t border-slate-100
              pt-5
            "
          >
            {children}
          </div>
        ) : null}
      </div>
    </article>
  );
}
'''


OUTCOME_SOURCE = '''import type {
  ReactNode,
} from "react";

import type {
  OutcomeLabel,
} from "../../lib/domain/types";

import {
  formatKickoffUtc,
} from "../../lib/formatters/kickoff";

import {
  formatProbability,
} from "../../lib/formatters/probability";


type MatchCardProps =
  Readonly<{
    homeTeamName: string;
    awayTeamName: string;
    kickoffUtc: string;

    stage7_prob_home_win: number;
    stage7_prob_draw: number;
    stage7_prob_away_win: number;

    stage7_predicted_label:
      OutcomeLabel;

    children?: ReactNode;
  }>;


export function MatchCard({
  homeTeamName,
  awayTeamName,
  kickoffUtc,
  stage7_prob_home_win,
  stage7_prob_draw,
  stage7_prob_away_win,
  stage7_predicted_label,
  children,
}: MatchCardProps) {
  const kickoffLabel =
    formatKickoffUtc(
      kickoffUtc,
    );

  return (
    <article
      aria-label={`${homeTeamName} vs ${awayTeamName}`}
      className="
        overflow-hidden rounded-xl
        border border-slate-200
        bg-white shadow-sm
      "
      data-fixtureiq-component="match-card"
    >
      <header
        className="
          border-b border-slate-100
          px-5 py-5
          sm:px-6
        "
      >
        <div
          className="
            grid
            grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]
            items-center gap-3
          "
        >
          <div className="min-w-0">
            <p
              className="
                text-xs font-medium uppercase
                tracking-wide text-slate-500
              "
            >
              Home
            </p>

            <h2
              className="
                mt-1 break-words
                text-base font-semibold
                text-slate-950
              "
            >
              {homeTeamName}
            </h2>
          </div>

          <span
            aria-hidden="true"
            className="
              text-sm font-medium
              text-slate-400
            "
          >
            vs
          </span>

          <div className="min-w-0 text-right">
            <p
              className="
                text-xs font-medium uppercase
                tracking-wide text-slate-500
              "
            >
              Away
            </p>

            <h2
              className="
                mt-1 break-words
                text-base font-semibold
                text-slate-950
              "
            >
              {awayTeamName}
            </h2>
          </div>
        </div>

        <div
          className="
            mt-4 flex items-center
            justify-center
            text-sm text-slate-600
          "
        >
          <span className="sr-only">
            Kickoff:
          </span>

          <time dateTime={kickoffUtc}>
            {kickoffLabel} UTC
          </time>
        </div>
      </header>

      <div
        className="
          space-y-5
          px-5 py-5
          sm:px-6
        "
      >
        <section
          aria-label="Three-way outcome probabilities"
        >
          <h3
            className="
              text-xs font-semibold uppercase
              tracking-wide text-slate-500
            "
          >
            Outcome probabilities
          </h3>

          <dl
            className="
              mt-3 grid grid-cols-3
              gap-2
            "
          >
            <div
              className="
                rounded-lg bg-slate-50
                px-3 py-3 text-center
              "
            >
              <dt
                className="
                  text-xs font-medium
                  text-slate-500
                "
              >
                Home
              </dt>

              <dd
                className="
                  mt-1 text-base font-semibold
                  tabular-nums text-slate-950
                "
                data-stage7-field="stage7_prob_home_win"
              >
                {formatProbability(
                  stage7_prob_home_win,
                )}
              </dd>
            </div>

            <div
              className="
                rounded-lg bg-slate-50
                px-3 py-3 text-center
              "
            >
              <dt
                className="
                  text-xs font-medium
                  text-slate-500
                "
              >
                Draw
              </dt>

              <dd
                className="
                  mt-1 text-base font-semibold
                  tabular-nums text-slate-950
                "
                data-stage7-field="stage7_prob_draw"
              >
                {formatProbability(
                  stage7_prob_draw,
                )}
              </dd>
            </div>

            <div
              className="
                rounded-lg bg-slate-50
                px-3 py-3 text-center
              "
            >
              <dt
                className="
                  text-xs font-medium
                  text-slate-500
                "
              >
                Away
              </dt>

              <dd
                className="
                  mt-1 text-base font-semibold
                  tabular-nums text-slate-950
                "
                data-stage7-field="stage7_prob_away_win"
              >
                {formatProbability(
                  stage7_prob_away_win,
                )}
              </dd>
            </div>
          </dl>
        </section>

        <section
          aria-label="Predicted outcome"
          className="
            rounded-lg
            border border-slate-200
            px-4 py-3
          "
        >
          <p
            className="
              text-xs font-medium uppercase
              tracking-wide text-slate-500
            "
          >
            Predicted outcome
          </p>

          <p
            className="
              mt-1 text-base font-semibold
              text-slate-950
            "
            data-stage7-field="stage7_predicted_label"
          >
            {stage7_predicted_label}
          </p>
        </section>

        {children ? (
          <div
            className="
              border-t border-slate-100
              pt-5
            "
          >
            {children}
          </div>
        ) : null}
      </div>
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

            digest.update(chunk)

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
        .replace("\\", "/")
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

    temporary.replace(path)


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


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.4.5 + 10.4.6"
    )

    print(
        "H/D/A PROBABILITIES + PREDICTED OUTCOME BUILD"
    )

    print("=" * 72)


    previous = load_json(
        PREVIOUS_VERIFICATION_FILE
    )

    kickoff_contract = load_json(
        KICKOFF_CONTRACT_FILE
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
            "10.4.3/10.4.4 verification is not PASS."
        )


    if (
        previous.get(
            "stage_10_4_3_complete"
        )
        is not True
        or
        previous.get(
            "stage_10_4_4_complete"
        )
        is not True
    ):
        raise RuntimeError(
            "10.4.3/10.4.4 are not complete."
        )


    if (
        previous.get(
            "stage10_ready_for_10_4_5"
        )
        is not True
    ):
        raise RuntimeError(
            "10.4.4 did not authorize 10.4.5."
        )


    for path in [
        MATCH_CARD_FILE,
        LOADER_FILE,
        DOMAIN_TYPES_FILE,
    ]:

        if not path.exists():

            raise RuntimeError(
                f"Missing source: {path}"
            )


    expected_pages = (
        kickoff_contract
        .get(
            "protected_state",
            {}
        )
        .get(
            "route_page_identity",
            {},
        )
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
            "Protected route page identity missing."
        )


    if (
        current_route_pages()
        !=
        expected_pages
    ):
        raise RuntimeError(
            "Route pages changed after 10.4.4."
        )


    expected_loader_sha = (
        kickoff_contract
        .get(
            "protected_state",
            {}
        )
        .get(
            "loader_sha256"
        )
    )


    if (
        sha256_file(
            LOADER_FILE
        )
        !=
        expected_loader_sha
        or
        sha256_file(
            LOADER_FILE
        )
        !=
        loader_contract.get(
            "source_sha256"
        )
    ):
        raise RuntimeError(
            "Dashboard loader changed after 10.4.4."
        )


    existing_probability = (
        optional_json(
            PROBABILITY_CONTRACT_FILE
        )
    )

    existing_outcome = (
        optional_json(
            OUTCOME_CONTRACT_FILE
        )
    )


    # --------------------------------------------------------
    # Fully built idempotent state
    # --------------------------------------------------------

    if (
        existing_outcome
        and
        PROBABILITY_FORMATTER_FILE.exists()
        and
        sha256_file(
            MATCH_CARD_FILE
        )
        ==
        existing_outcome.get(
            "match_card_after_outcome_sha256"
        )
        and
        sha256_file(
            PROBABILITY_FORMATTER_FILE
        )
        ==
        existing_outcome.get(
            "probability_formatter_sha256"
        )
    ):

        print()

        print(
            "10.4.5 / 10.4.6 already built."
        )

        print("=" * 72)

        print(
            "STAGE 10.4.5 H/D/A PROBABILITIES: BUILT"
        )

        print(
            "STAGE 10.4.6 PREDICTED OUTCOME: BUILT"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

        print("=" * 72)

        return


    # ========================================================
    # Stage 10.4.5
    # ========================================================

    current_card_sha = (
        sha256_file(
            MATCH_CARD_FILE
        )
    )


    if (
        existing_probability
        and
        current_card_sha
        ==
        existing_probability.get(
            "match_card_after_probabilities_sha256"
        )
        and
        PROBABILITY_FORMATTER_FILE.exists()
        and
        sha256_file(
            PROBABILITY_FORMATTER_FILE
        )
        ==
        existing_probability.get(
            "probability_formatter_sha256"
        )
    ):

        probability_contract = (
            existing_probability
        )

        print()

        print(
            "10.4.5 probabilities already built."
        )

    else:

        expected_kickoff_sha = (
            kickoff_contract.get(
                "match_card_after_kickoff_sha256"
            )
        )


        if (
            current_card_sha
            !=
            expected_kickoff_sha
        ):

            raise RuntimeError(
                (
                    "MatchCard no longer matches "
                    "verified 10.4.4 output."
                )
            )


        before_probability_sha = (
            current_card_sha
        )


        save_text_atomic(
            PROBABILITY_FORMATTER_FILE,
            PROBABILITY_FORMATTER_SOURCE,
        )


        save_text_atomic(
            MATCH_CARD_FILE,
            PROBABILITY_SOURCE,
        )


        after_probability_sha = (
            sha256_file(
                MATCH_CARD_FILE
            )
        )


        probability_contract = {
            "stage":
                "10.4.5",

            "version":
                "1.0.0",

            "name":
                "MATCH_HDA_PROBABILITIES",

            "status":
                "LOCKED",

            "source":
                relative(
                    MATCH_CARD_FILE
                ),

            "formatter_source":
                relative(
                    PROBABILITY_FORMATTER_FILE
                ),

            "authority":
                "STAGE_7_PREDICTION",

            "source_fields": [
                "stage7_prob_home_win",
                "stage7_prob_draw",
                "stage7_prob_away_win",
            ],

            "display_mapping": {
                "stage7_prob_home_win":
                    "Home",

                "stage7_prob_draw":
                    "Draw",

                "stage7_prob_away_win":
                    "Away",
            },

            "formatting": {
                "library":
                    "Intl.NumberFormat",

                "style":
                    "percent",

                "locale":
                    "en-GB",

                "minimum_fraction_digits":
                    1,

                "maximum_fraction_digits":
                    1,

                "display_only":
                    True,

                "source_values_modified":
                    False,
            },

            "validation": {
                "finite_required":
                    True,

                "minimum":
                    0,

                "maximum":
                    1,

                "invalid_value_policy":
                    "THROW_RANGE_ERROR",

                "normalization":
                    False,

                "renormalization":
                    False,
            },

            "implementation": {
                "server_component":
                    True,

                "frontend_prediction_logic":
                    False,

                "argmax":
                    False,

                "probability_arithmetic":
                    False,

                "probability_recalibration":
                    False,

                "sorting":
                    False,

                "api_access":
                    False,

                "provider_access":
                    False,

                "artifact_access":
                    False,
            },

            "transition": {
                "match_card_before_probabilities_sha256":
                    before_probability_sha,

                "match_card_after_probabilities_sha256":
                    after_probability_sha,
            },

            "match_card_after_probabilities_sha256":
                after_probability_sha,

            "probability_formatter_sha256":
                sha256_file(
                    PROBABILITY_FORMATTER_FILE
                ),

            "protected_state": {
                "route_page_identity":
                    expected_pages,

                "loader_sha256":
                    sha256_file(
                        LOADER_FILE
                    ),

                "domain_types_sha256":
                    sha256_file(
                        DOMAIN_TYPES_FILE
                    ),
            },

            "dependency_identity": {
                relative(
                    PREVIOUS_VERIFICATION_FILE
                ):
                    identity(
                        PREVIOUS_VERIFICATION_FILE
                    ),

                relative(
                    KICKOFF_CONTRACT_FILE
                ):
                    identity(
                        KICKOFF_CONTRACT_FILE
                    ),

                relative(
                    LOADER_FILE
                ):
                    identity(
                        LOADER_FILE
                    ),
            },

            "promotion": {
                "stage10_4_5_complete":
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
            PROBABILITY_CONTRACT_FILE,
            probability_contract,
        )


    # ========================================================
    # Stage 10.4.6
    # ========================================================

    expected_probability_sha = (
        probability_contract.get(
            "match_card_after_probabilities_sha256"
        )
    )


    if (
        sha256_file(
            MATCH_CARD_FILE
        )
        !=
        expected_probability_sha
    ):

        raise RuntimeError(
            "10.4.5 MatchCard SHA mismatch."
        )


    before_outcome_sha = (
        sha256_file(
            MATCH_CARD_FILE
        )
    )


    save_text_atomic(
        MATCH_CARD_FILE,
        OUTCOME_SOURCE,
    )


    after_outcome_sha = (
        sha256_file(
            MATCH_CARD_FILE
        )
    )


    outcome_contract = {
        "stage":
            "10.4.6",

        "version":
            "1.0.0",

        "name":
            "MATCH_PREDICTED_OUTCOME",

        "status":
            "LOCKED",

        "source":
            relative(
                MATCH_CARD_FILE
            ),

        "authority":
            "STAGE_7_PREDICTION",

        "source_field":
            "stage7_predicted_label",

        "typescript_type":
            "OutcomeLabel",

        "allowed_labels": [
            "Home Win",
            "Draw",
            "Away Win",
        ],

        "presentation": {
            "heading":
                "Predicted outcome",

            "direct_source_label_display":
                True,

            "derived_from_probabilities":
                False,

            "color_only_meaning":
                False,

            "reusable_outcome_badge":
                False,
        },

        "implementation": {
            "server_component":
                True,

            "frontend_argmax":
                False,

            "frontend_prediction_logic":
                False,

            "probability_comparison":
                False,

            "label_recalculation":
                False,

            "label_replacement":
                False,

            "api_access":
                False,

            "provider_access":
                False,

            "artifact_access":
                False,
        },

        "transition": {
            "match_card_before_outcome_sha256":
                before_outcome_sha,

            "match_card_after_outcome_sha256":
                after_outcome_sha,
        },

        "match_card_after_outcome_sha256":
            after_outcome_sha,

        "probability_formatter_sha256":
            sha256_file(
                PROBABILITY_FORMATTER_FILE
            ),

        "protected_state": {
            "route_page_identity":
                expected_pages,

            "loader_sha256":
                sha256_file(
                    LOADER_FILE
                ),

            "domain_types_sha256":
                sha256_file(
                    DOMAIN_TYPES_FILE
                ),
        },

        "dependency_identity": {
            relative(
                PREVIOUS_VERIFICATION_FILE
            ):
                identity(
                    PREVIOUS_VERIFICATION_FILE
                ),

            relative(
                PROBABILITY_CONTRACT_FILE
            ):
                identity(
                    PROBABILITY_CONTRACT_FILE
                ),

            relative(
                PROBABILITY_FORMATTER_FILE
            ):
                identity(
                    PROBABILITY_FORMATTER_FILE
                ),

            relative(
                DOMAIN_TYPES_FILE
            ):
                identity(
                    DOMAIN_TYPES_FILE
                ),

            relative(
                LOADER_FILE
            ):
                identity(
                    LOADER_FILE
                ),
        },

        "promotion": {
            "stage10_4_6_complete":
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
        OUTCOME_CONTRACT_FILE,
        outcome_contract,
    )


    # ========================================================
    # Final protections
    # ========================================================

    if (
        current_route_pages()
        !=
        expected_pages
    ):

        raise RuntimeError(
            (
                "Route pages changed during "
                "10.4.5/10.4.6."
            )
        )


    if (
        sha256_file(
            LOADER_FILE
        )
        !=
        expected_loader_sha
    ):

        raise RuntimeError(
            (
                "Dashboard loader changed during "
                "10.4.5/10.4.6."
            )
        )


    if (
        sha256_file(
            DOMAIN_TYPES_FILE
        )
        !=
        probability_contract[
            "protected_state"
        ][
            "domain_types_sha256"
        ]
    ):

        raise RuntimeError(
            (
                "Domain types changed during "
                "10.4.5/10.4.6."
            )
        )


    print()

    print(
        "MatchCard probabilities + outcome:"
    )

    print(
        f"  {relative(MATCH_CARD_FILE)}"
    )

    print()

    print(
        "Probability formatter:"
    )

    print(
        f"  {relative(PROBABILITY_FORMATTER_FILE)}"
    )

    print()

    print(
        "Dashboard route pages remain unchanged."
    )

    print()

    print("=" * 72)

    print(
        "STAGE 10.4.5 H/D/A PROBABILITIES: BUILT"
    )

    print(
        "STAGE 10.4.6 PREDICTED OUTCOME: BUILT"
    )

    print(
        "STAGE 10 IS NOT YET PROMOTED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
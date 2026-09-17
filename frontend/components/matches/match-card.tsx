import type {
  ReactNode,
} from "react";

import type {
  OutcomeLabel,
  ConfidenceBand,
  UncertaintyBand,
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

    stage7_confidence: number;
    confidence_band:
      ConfidenceBand;

    uncertainty_band:
      UncertaintyBand;

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
  stage7_confidence,
  confidence_band,
  uncertainty_band,
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

        <section
          aria-label="Prediction confidence"
          className="
            rounded-lg
            border border-slate-200
            px-4 py-3
          "
        >
          <div
            className="
              flex items-end
              justify-between gap-4
            "
          >
            <div>
              <p
                className="
                  text-xs font-medium uppercase
                  tracking-wide text-slate-500
                "
              >
                Confidence
              </p>

              <p
                className="
                  mt-1 text-base font-semibold
                  tabular-nums text-slate-950
                "
                data-stage7-field="stage7_confidence"
              >
                {formatProbability(
                  stage7_confidence,
                )}
              </p>
            </div>

            <p
              className="
                text-sm font-semibold
                text-slate-700
              "
              data-stage9-field="confidence_band"
            >
              {confidence_band}
            </p>
          </div>
        </section>

        <section
          aria-label="Prediction uncertainty"
          className="
            rounded-lg
            border border-slate-200
            px-4 py-3
          "
        >
          <div
            className="
              flex items-center
              justify-between gap-4
            "
          >
            <p
              className="
                text-xs font-medium uppercase
                tracking-wide text-slate-500
              "
            >
              Uncertainty
            </p>

            <p
              className="
                text-sm font-semibold
                text-slate-700
              "
              data-stage9-field="uncertainty_band"
            >
              {uncertainty_band}
            </p>
          </div>
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

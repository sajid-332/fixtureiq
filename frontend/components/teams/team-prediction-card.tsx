import Link from "next/link";

import type {
  ConfidenceBand,
  ContextAlignment,
  FixtureId,
  OutcomeLabel,
  UncertaintyBand,
} from "../../lib/domain/types";

import {
  formatKickoffUtc,
} from "../../lib/formatters/kickoff";

import {
  formatProbability,
} from "../../lib/formatters/probability";


type TeamPredictionCardProps =
  Readonly<{
    fixtureId:
      FixtureId;

    homeTeamName:
      string;

    awayTeamName:
      string;

    kickoffUtc:
      string;

    homeProbability:
      number;

    drawProbability:
      number;

    awayProbability:
      number;

    predictedLabel:
      OutcomeLabel;

    confidence:
      number;

    confidenceBand:
      ConfidenceBand;

    uncertaintyBand:
      UncertaintyBand;

    contextAlignment:
      ContextAlignment;
  }>;


type ProbabilityValueProps =
  Readonly<{
    label:
      string;

    value:
      number;

    sourceField:
      string;
  }>;


function ProbabilityValue({
  label,
  value,
  sourceField,
}: ProbabilityValueProps) {

  return (
    <div>
      <dt
        className="
          text-xs font-medium
          text-slate-500
        "
      >
        {label}
      </dt>

      <dd
        className="
          mt-1 text-sm font-semibold
          text-slate-950
        "
        data-stage7-field={
          sourceField
        }
      >
        {formatProbability(
          value,
        )}
      </dd>
    </div>
  );
}


export function TeamPredictionCard({
  fixtureId,
  homeTeamName,
  awayTeamName,
  kickoffUtc,
  homeProbability,
  drawProbability,
  awayProbability,
  predictedLabel,
  confidence,
  confidenceBand,
  uncertaintyBand,
  contextAlignment,
}: TeamPredictionCardProps) {

  return (
    <article
      aria-label={`${homeTeamName} vs ${awayTeamName}`}
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="team-prediction-card"
      data-fixture-id={
        String(
          fixtureId,
        )
      }
    >
      <header>
        <p
          className="
            text-xs font-medium
            uppercase tracking-wide
            text-slate-500
          "
        >
          Upcoming fixture
        </p>

        <div
          className="
            mt-3 grid
            grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]
            items-center gap-3
          "
        >
          <p
            className="
              min-w-0 break-words
              font-semibold text-slate-950
            "
          >
            {homeTeamName}
          </p>

          <span
            aria-hidden="true"
            className="
              text-xs font-medium
              text-slate-400
            "
          >
            vs
          </span>

          <p
            className="
              min-w-0 break-words
              text-right font-semibold
              text-slate-950
            "
          >
            {awayTeamName}
          </p>
        </div>

        <time
          dateTime={
            kickoffUtc
          }
          className="
            mt-3 block
            text-sm text-slate-600
          "
          data-stage9-field="date"
        >
          {formatKickoffUtc(
            kickoffUtc,
          )} UTC
        </time>
      </header>

      <dl
        className="
          mt-5 grid grid-cols-3
          gap-3 border-t
          border-slate-100 pt-4
        "
      >
        <ProbabilityValue
          label="Home"
          value={
            homeProbability
          }
          sourceField="stage7_prob_home_win"
        />

        <ProbabilityValue
          label="Draw"
          value={
            drawProbability
          }
          sourceField="stage7_prob_draw"
        />

        <ProbabilityValue
          label="Away"
          value={
            awayProbability
          }
          sourceField="stage7_prob_away_win"
        />
      </dl>

      <dl
        className="
          mt-5 space-y-3
          border-t border-slate-100
          pt-4
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
            Prediction
          </dt>

          <dd
            className="
              text-sm font-semibold
              text-slate-950
            "
            data-stage7-field="stage7_predicted_label"
          >
            {predictedLabel}
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
            Confidence
          </dt>

          <dd
            className="
              text-sm font-semibold
              text-slate-950
            "
            data-stage7-field="stage7_confidence"
          >
            {formatProbability(
              confidence,
            )}
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
            Confidence band
          </dt>

          <dd
            className="
              text-sm font-semibold
              text-slate-950
            "
            data-stage9-field="stage9_confidence_band"
          >
            {confidenceBand}
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
            Uncertainty
          </dt>

          <dd
            className="
              text-sm font-semibold
              text-slate-950
            "
            data-stage9-field="stage9_uncertainty_band"
          >
            {uncertaintyBand}
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
            Context alignment
          </dt>

          <dd
            className="
              text-sm font-semibold
              text-slate-950
            "
            data-stage9-field="stage9_context_alignment"
          >
            {contextAlignment}
          </dd>
        </div>
      </dl>
      <div
        className="
          mt-5 border-t
          border-slate-100
          pt-4
        "
      >
        <Link
          href={`/matches/${encodeURIComponent(
            String(
              fixtureId,
            ),
          )}`}
          className="
            inline-flex items-center
            text-sm font-semibold
            text-slate-900
            underline
            underline-offset-4
          "
        >
          View match intelligence
        </Link>
      </div>

    </article>
  );
}

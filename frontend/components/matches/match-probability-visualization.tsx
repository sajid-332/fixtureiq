import {
  formatProbability,
} from "../../lib/formatters/probability";


type MatchProbabilityVisualizationProps =
  Readonly<{
    homeProbability:
      number;

    drawProbability:
      number;

    awayProbability:
      number;
  }>;


type ProbabilityRowProps =
  Readonly<{
    label:
      string;

    probability:
      number;

    sourceField:
      string;
  }>;


function ProbabilityRow({
  label,
  probability,
  sourceField,
}: ProbabilityRowProps) {

  return (
    <div>
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
            text-slate-950
          "
          data-stage7-field={
            sourceField
          }
        >
          {formatProbability(
            probability,
          )}
        </span>
      </div>

      <progress
        aria-label={`${label} probability`}
        className="
          mt-2 block h-2
          w-full
        "
        max={1}
        value={
          probability
        }
      />
    </div>
  );
}


export function MatchProbabilityVisualization({
  homeProbability,
  drawProbability,
  awayProbability,
}: MatchProbabilityVisualizationProps) {

  return (
    <section
      aria-labelledby="match-probabilities-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-probability-visualization"
    >
      <h2
        id="match-probabilities-heading"
        className="
          text-lg font-bold
          text-slate-950
        "
      >
        Outcome probabilities
      </h2>

      <div
        className="
          mt-5 space-y-5
        "
      >
        <ProbabilityRow
          label="Home win"
          probability={
            homeProbability
          }
          sourceField="stage7_prob_home_win"
        />

        <ProbabilityRow
          label="Draw"
          probability={
            drawProbability
          }
          sourceField="stage7_prob_draw"
        />

        <ProbabilityRow
          label="Away win"
          probability={
            awayProbability
          }
          sourceField="stage7_prob_away_win"
        />
      </div>
    </section>
  );
}

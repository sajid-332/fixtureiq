import type {
  OutcomeLabel,
} from "../../lib/domain/types";


type MatchPredictionOverviewProps =
  Readonly<{
    predictedLabel:
      OutcomeLabel;
  }>;


export function MatchPredictionOverview({
  predictedLabel,
}: MatchPredictionOverviewProps) {

  return (
    <section
      aria-labelledby="prediction-overview-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-prediction-overview"
    >
      <p
        className="
          text-xs font-medium
          uppercase tracking-wide
          text-slate-500
        "
      >
        FixtureIQ prediction
      </p>

      <h2
        id="prediction-overview-heading"
        className="
          mt-2 text-lg font-bold
          text-slate-950
        "
      >
        Predicted outcome
      </h2>

      <p
        className="
          mt-3 text-xl font-semibold
          text-slate-900
        "
        data-stage7-field="stage7_predicted_label"
      >
        {predictedLabel}
      </p>
    </section>
  );
}

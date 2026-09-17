import type {
  ConfidenceBand,
} from "../../lib/domain/types";

import {
  formatProbability,
} from "../../lib/formatters/probability";


type MatchConfidenceProps =
  Readonly<{
    confidence:
      number;

    confidenceBand:
      ConfidenceBand;
  }>;


export function MatchConfidence({
  confidence,
  confidenceBand,
}: MatchConfidenceProps) {

  return (
    <section
      aria-labelledby="match-confidence-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-confidence"
    >
      <h2
        id="match-confidence-heading"
        className="
          text-base font-bold
          text-slate-950
        "
      >
        Confidence
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
            Stage 7 confidence
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
      </dl>
    </section>
  );
}

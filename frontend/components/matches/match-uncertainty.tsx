import type {
  UncertaintyBand,
} from "../../lib/domain/types";


type MatchUncertaintyProps =
  Readonly<{
    uncertaintyBand:
      UncertaintyBand;
  }>;


export function MatchUncertainty({
  uncertaintyBand,
}: MatchUncertaintyProps) {

  return (
    <section
      aria-labelledby="match-uncertainty-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-uncertainty"
    >
      <h2
        id="match-uncertainty-heading"
        className="
          text-base font-bold
          text-slate-950
        "
      >
        Uncertainty
      </h2>

      <p
        className="
          mt-4 text-sm
          text-slate-600
        "
      >
        Stage 9 uncertainty band
      </p>

      <p
        className="
          mt-1 text-sm font-semibold
          text-slate-950
        "
        data-stage9-field="stage9_uncertainty_band"
      >
        {uncertaintyBand}
      </p>
    </section>
  );
}

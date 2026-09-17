import type {
  ContextSupportScore,
} from "../../lib/domain/types";


const signedScoreFormatter =
  new Intl.NumberFormat(
    "en-GB",
    {
      maximumFractionDigits: 0,
      signDisplay: "exceptZero",
    },
  );


type MatchContextSupportProps =
  Readonly<{
    supportScore:
      ContextSupportScore;
  }>;


export function MatchContextSupport({
  supportScore,
}: MatchContextSupportProps) {

  return (
    <section
      aria-labelledby="context-support-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-context-support"
    >
      <h2
        id="context-support-heading"
        className="
          text-base font-bold
          text-slate-950
        "
      >
        Context support
      </h2>

      <p
        className="
          mt-4 text-3xl font-bold
          text-slate-950
        "
        data-stage9-field="stage9_context_support_score"
      >
        {signedScoreFormatter.format(
          supportScore,
        )}
      </p>

      <p
        className="
          mt-2 text-xs leading-5
          text-slate-500
        "
      >
        Stage 9 fixed context score on the
        locked -5 to +5 scale.
      </p>
    </section>
  );
}

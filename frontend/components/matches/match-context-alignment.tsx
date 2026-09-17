import type {
  ContextAlignment,
} from "../../lib/domain/types";


type MatchContextAlignmentProps =
  Readonly<{
    alignment:
      ContextAlignment;
  }>;


export function MatchContextAlignment({
  alignment,
}: MatchContextAlignmentProps) {

  return (
    <section
      aria-labelledby="context-alignment-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-context-alignment"
    >
      <h2
        id="context-alignment-heading"
        className="
          text-base font-bold
          text-slate-950
        "
      >
        Prediction-context alignment
      </h2>

      <p
        className="
          mt-4 text-lg font-semibold
          text-slate-950
        "
        data-stage9-field="stage9_context_alignment"
      >
        {alignment}
      </p>

      <p
        className="
          mt-2 text-xs leading-5
          text-slate-500
        "
      >
        This label comes directly from
        Stage 9 intelligence.
      </p>
    </section>
  );
}

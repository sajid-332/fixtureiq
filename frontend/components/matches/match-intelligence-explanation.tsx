type MatchIntelligenceExplanationProps =
  Readonly<{
    headline:
      string;

    summary:
      string;
  }>;


export function MatchIntelligenceExplanation({
  headline,
  summary,
}: MatchIntelligenceExplanationProps) {

  return (
    <section
      aria-labelledby="intelligence-explanation-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-intelligence-explanation"
    >
      <p
        className="
          text-xs font-medium
          uppercase tracking-wide
          text-slate-500
        "
      >
        FixtureIQ explanation
      </p>

      <h2
        id="intelligence-explanation-heading"
        className="
          mt-2 text-lg font-bold
          text-slate-950
        "
        data-stage9-field="stage9_explanation_headline"
      >
        {headline}
      </h2>

      <p
        className="
          mt-4 max-w-3xl
          text-sm leading-7
          text-slate-700
        "
        data-stage9-field="stage9_explanation_summary"
      >
        {summary}
      </p>
    </section>
  );
}

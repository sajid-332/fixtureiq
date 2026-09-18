type IntelligenceExplanationProps =
  Readonly<{
    headline:
      string;

    summary:
      string;
  }>;


export function IntelligenceExplanation({
  headline,
  summary,
}: IntelligenceExplanationProps) {

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
      data-fixtureiq-component="intelligence-explanation"
    >
      <h2
        id="intelligence-explanation-heading"
        className="
          text-lg font-bold
          text-slate-950
        "
        data-stage9-explanation-headline
      >
        {headline}
      </h2>

      <p
        className="
          mt-3 text-sm
          leading-6
          text-slate-700
        "
        data-stage9-explanation-summary
      >
        {summary}
      </p>
    </section>
  );
}

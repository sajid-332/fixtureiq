type MatchPointsComparisonProps =
  Readonly<{
    homeTeamName:
      string;

    awayTeamName:
      string;

    homePoints:
      number;

    awayPoints:
      number;
  }>;


export function MatchPointsComparison({
  homeTeamName,
  awayTeamName,
  homePoints,
  awayPoints,
}: MatchPointsComparisonProps) {

  return (
    <section
      aria-labelledby="points-comparison-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-points-comparison"
    >
      <h2
        id="points-comparison-heading"
        className="
          text-base font-bold
          text-slate-950
        "
      >
        League points
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
              min-w-0 break-words
              text-sm text-slate-600
            "
          >
            {homeTeamName}
          </dt>

          <dd
            className="
              shrink-0 text-sm
              font-semibold text-slate-950
            "
            data-stage8-field="home_team_points"
          >
            {homePoints}
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
              min-w-0 break-words
              text-sm text-slate-600
            "
          >
            {awayTeamName}
          </dt>

          <dd
            className="
              shrink-0 text-sm
              font-semibold text-slate-950
            "
            data-stage8-field="away_team_points"
          >
            {awayPoints}
          </dd>
        </div>
      </dl>
    </section>
  );
}

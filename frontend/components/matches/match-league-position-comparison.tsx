type MatchLeaguePositionComparisonProps =
  Readonly<{
    homeTeamName:
      string;

    awayTeamName:
      string;

    homePosition:
      number;

    awayPosition:
      number;
  }>;


export function MatchLeaguePositionComparison({
  homeTeamName,
  awayTeamName,
  homePosition,
  awayPosition,
}: MatchLeaguePositionComparisonProps) {

  return (
    <section
      aria-labelledby="league-position-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-league-position-comparison"
    >
      <h2
        id="league-position-heading"
        className="
          text-base font-bold
          text-slate-950
        "
      >
        League position
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
            data-stage8-field="home_team_position"
          >
            #{homePosition}
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
            data-stage8-field="away_team_position"
          >
            #{awayPosition}
          </dd>
        </div>
      </dl>
    </section>
  );
}

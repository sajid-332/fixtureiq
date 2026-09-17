const signedIntegerFormatter =
  new Intl.NumberFormat(
    "en-GB",
    {
      maximumFractionDigits: 0,
      signDisplay: "always",
    },
  );


type MatchGoalDifferenceComparisonProps =
  Readonly<{
    homeTeamName:
      string;

    awayTeamName:
      string;

    homeGoalDifference:
      number;

    awayGoalDifference:
      number;
  }>;


export function MatchGoalDifferenceComparison({
  homeTeamName,
  awayTeamName,
  homeGoalDifference,
  awayGoalDifference,
}: MatchGoalDifferenceComparisonProps) {

  return (
    <section
      aria-labelledby="goal-difference-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-goal-difference-comparison"
    >
      <h2
        id="goal-difference-heading"
        className="
          text-base font-bold
          text-slate-950
        "
      >
        Goal difference
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
            data-stage8-field="home_team_goal_difference"
          >
            {signedIntegerFormatter.format(
              homeGoalDifference,
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
            data-stage8-field="away_team_goal_difference"
          >
            {signedIntegerFormatter.format(
              awayGoalDifference,
            )}
          </dd>
        </div>
      </dl>
    </section>
  );
}

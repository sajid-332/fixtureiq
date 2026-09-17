type MatchRecentFormProps =
  Readonly<{
    homeTeamName:
      string;

    awayTeamName:
      string;

    homeResults:
      string;

    awayResults:
      string;

    homeMatchesAvailable:
      number;

    awayMatchesAvailable:
      number;
  }>;


export function MatchRecentForm({
  homeTeamName,
  awayTeamName,
  homeResults,
  awayResults,
  homeMatchesAvailable,
  awayMatchesAvailable,
}: MatchRecentFormProps) {

  return (
    <section
      aria-labelledby="recent-form-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-recent-form"
    >
      <h2
        id="recent-form-heading"
        className="
          text-lg font-bold
          text-slate-950
        "
      >
        Recent form
      </h2>

      <div
        className="
          mt-5 grid gap-5
          sm:grid-cols-2
        "
      >
        <div>
          <p
            className="
              text-sm font-semibold
              text-slate-700
            "
          >
            {homeTeamName}
          </p>

          <p
            className="
              mt-2 font-mono text-base
              font-semibold tracking-widest
              text-slate-950
            "
            data-stage8-field="home_team_recent_results"
          >
            {homeResults || "No results"}
          </p>

          <p
            className="
              mt-1 text-xs
              text-slate-500
            "
            data-stage8-field="home_team_form_matches_available"
          >
            {homeMatchesAvailable} matches available
          </p>
        </div>

        <div>
          <p
            className="
              text-sm font-semibold
              text-slate-700
            "
          >
            {awayTeamName}
          </p>

          <p
            className="
              mt-2 font-mono text-base
              font-semibold tracking-widest
              text-slate-950
            "
            data-stage8-field="away_team_recent_results"
          >
            {awayResults || "No results"}
          </p>

          <p
            className="
              mt-1 text-xs
              text-slate-500
            "
            data-stage8-field="away_team_form_matches_available"
          >
            {awayMatchesAvailable} matches available
          </p>
        </div>
      </div>

      <p
        className="
          mt-5 text-xs
          leading-5 text-slate-500
        "
      >
        W = win, D = draw, L = loss.
      </p>
    </section>
  );
}

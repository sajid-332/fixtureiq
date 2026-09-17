type MatchVenueFormProps =
  Readonly<{
    homeTeamName:
      string;

    awayTeamName:
      string;

    homeRecentPoints:
      number;

    awayRecentPoints:
      number;

    homeMatchesAvailable:
      number;

    awayMatchesAvailable:
      number;
  }>;


export function MatchVenueForm({
  homeTeamName,
  awayTeamName,
  homeRecentPoints,
  awayRecentPoints,
  homeMatchesAvailable,
  awayMatchesAvailable,
}: MatchVenueFormProps) {

  return (
    <section
      aria-labelledby="venue-form-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-venue-form"
    >
      <h2
        id="venue-form-heading"
        className="
          text-lg font-bold
          text-slate-950
        "
      >
        Venue form
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
              text-xs font-medium
              uppercase tracking-wide
              text-slate-500
            "
          >
            Home form
          </p>

          <p
            className="
              mt-1 break-words
              text-sm font-semibold
              text-slate-800
            "
          >
            {homeTeamName}
          </p>

          <p
            className="
              mt-3 text-2xl font-bold
              text-slate-950
            "
            data-stage8-field="home_team_home_recent_points"
          >
            {homeRecentPoints}
          </p>

          <p
            className="
              mt-1 text-xs
              text-slate-500
            "
          >
            recent points
          </p>

          <p
            className="
              mt-2 text-xs
              text-slate-500
            "
            data-stage8-field="home_team_home_form_matches_available"
          >
            {homeMatchesAvailable} home matches available
          </p>
        </div>

        <div>
          <p
            className="
              text-xs font-medium
              uppercase tracking-wide
              text-slate-500
            "
          >
            Away form
          </p>

          <p
            className="
              mt-1 break-words
              text-sm font-semibold
              text-slate-800
            "
          >
            {awayTeamName}
          </p>

          <p
            className="
              mt-3 text-2xl font-bold
              text-slate-950
            "
            data-stage8-field="away_team_away_recent_points"
          >
            {awayRecentPoints}
          </p>

          <p
            className="
              mt-1 text-xs
              text-slate-500
            "
          >
            recent points
          </p>

          <p
            className="
              mt-2 text-xs
              text-slate-500
            "
            data-stage8-field="away_team_away_form_matches_available"
          >
            {awayMatchesAvailable} away matches available
          </p>
        </div>
      </div>
    </section>
  );
}

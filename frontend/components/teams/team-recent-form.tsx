const signedIntegerFormatter =
  new Intl.NumberFormat(
    "en-GB",
    {
      maximumFractionDigits: 0,
      signDisplay: "exceptZero",
    },
  );


type TeamRecentFormProps =
  Readonly<{
    matchesAvailable:
      number;

    results:
      string;

    points:
      number;

    wins:
      number;

    draws:
      number;

    losses:
      number;

    goalsFor:
      number;

    goalsAgainst:
      number;

    goalDifference:
      number;
  }>;


export function TeamRecentForm({
  matchesAvailable,
  results,
  points,
  wins,
  draws,
  losses,
  goalsFor,
  goalsAgainst,
  goalDifference,
}: TeamRecentFormProps) {

  return (
    <section
      aria-labelledby="team-recent-form-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="team-recent-form"
    >
      <h2
        id="team-recent-form-heading"
        className="
          text-lg font-bold
          text-slate-950
        "
      >
        Recent form
      </h2>

      <p
        className="
          mt-4 font-mono
          text-lg font-semibold
          tracking-widest
          text-slate-950
        "
        data-stage8-field="recent_results"
      >
        {results || "No results"}
      </p>

      <p
        className="
          mt-1 text-xs
          text-slate-500
        "
        data-stage8-field="form_matches_available"
      >
        {matchesAvailable} matches available
      </p>

      <dl
        className="
          mt-5 grid
          grid-cols-2 gap-4
          sm:grid-cols-3
        "
      >
        <div>
          <dt className="text-xs text-slate-500">
            Points
          </dt>

          <dd
            className="mt-1 font-semibold text-slate-950"
            data-stage8-field="recent_points"
          >
            {points}
          </dd>
        </div>

        <div>
          <dt className="text-xs text-slate-500">
            W-D-L
          </dt>

          <dd className="mt-1 font-semibold text-slate-950">
            <span data-stage8-field="recent_wins">
              {wins}
            </span>
            {" - "}
            <span data-stage8-field="recent_draws">
              {draws}
            </span>
            {" - "}
            <span data-stage8-field="recent_losses">
              {losses}
            </span>
          </dd>
        </div>

        <div>
          <dt className="text-xs text-slate-500">
            Goals
          </dt>

          <dd className="mt-1 font-semibold text-slate-950">
            <span data-stage8-field="recent_goals_for">
              {goalsFor}
            </span>
            {" - "}
            <span data-stage8-field="recent_goals_against">
              {goalsAgainst}
            </span>
          </dd>
        </div>

        <div>
          <dt className="text-xs text-slate-500">
            Goal difference
          </dt>

          <dd
            className="mt-1 font-semibold text-slate-950"
            data-stage8-field="recent_goal_difference"
          >
            {signedIntegerFormatter.format(
              goalDifference,
            )}
          </dd>
        </div>
      </dl>

      <p
        className="
          mt-5 text-xs
          text-slate-500
        "
      >
        W = win, D = draw, L = loss.
      </p>
    </section>
  );
}

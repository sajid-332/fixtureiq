const signedIntegerFormatter =
  new Intl.NumberFormat(
    "en-GB",
    {
      maximumFractionDigits: 0,
      signDisplay: "exceptZero",
    },
  );


type TeamStandingsProps =
  Readonly<{
    position:
      number;

    points:
      number;

    played:
      number;

    won:
      number;

    drawn:
      number;

    lost:
      number;

    goalsFor:
      number;

    goalsAgainst:
      number;

    goalDifference:
      number;
  }>;


export function TeamStandings({
  position,
  points,
  played,
  won,
  drawn,
  lost,
  goalsFor,
  goalsAgainst,
  goalDifference,
}: TeamStandingsProps) {

  return (
    <section
      aria-labelledby="team-standings-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="team-standings"
    >
      <h2
        id="team-standings-heading"
        className="
          text-lg font-bold
          text-slate-950
        "
      >
        League standing
      </h2>

      <dl
        className="
          mt-5 grid
          grid-cols-2 gap-4
          sm:grid-cols-3
        "
      >
        <div>
          <dt className="text-xs text-slate-500">
            Position
          </dt>

          <dd
            className="mt-1 text-xl font-bold text-slate-950"
            data-stage8-field="position"
          >
            #{position}
          </dd>
        </div>

        <div>
          <dt className="text-xs text-slate-500">
            Points
          </dt>

          <dd
            className="mt-1 text-xl font-bold text-slate-950"
            data-stage8-field="points"
          >
            {points}
          </dd>
        </div>

        <div>
          <dt className="text-xs text-slate-500">
            Played
          </dt>

          <dd
            className="mt-1 font-semibold text-slate-950"
            data-stage8-field="played"
          >
            {played}
          </dd>
        </div>

        <div>
          <dt className="text-xs text-slate-500">
            W-D-L
          </dt>

          <dd className="mt-1 font-semibold text-slate-950">
            <span data-stage8-field="won">
              {won}
            </span>
            {" - "}
            <span data-stage8-field="drawn">
              {drawn}
            </span>
            {" - "}
            <span data-stage8-field="lost">
              {lost}
            </span>
          </dd>
        </div>

        <div>
          <dt className="text-xs text-slate-500">
            Goals
          </dt>

          <dd className="mt-1 font-semibold text-slate-950">
            <span data-stage8-field="goals_for">
              {goalsFor}
            </span>
            {" - "}
            <span data-stage8-field="goals_against">
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
            data-stage8-field="goal_difference"
          >
            {signedIntegerFormatter.format(
              goalDifference,
            )}
          </dd>
        </div>
      </dl>
    </section>
  );
}

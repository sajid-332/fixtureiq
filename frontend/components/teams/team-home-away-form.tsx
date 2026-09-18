const signedIntegerFormatter =
  new Intl.NumberFormat(
    "en-GB",
    {
      maximumFractionDigits: 0,
      signDisplay: "exceptZero",
    },
  );


type VenueFormBlockProps =
  Readonly<{
    label:
      string;

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

    fieldPrefix:
      "home"
      |
      "away";
  }>;


function VenueFormBlock({
  label,
  matchesAvailable,
  results,
  points,
  wins,
  draws,
  losses,
  goalsFor,
  goalsAgainst,
  goalDifference,
  fieldPrefix,
}: VenueFormBlockProps) {

  return (
    <div>
      <h3
        className="
          text-sm font-bold
          text-slate-950
        "
      >
        {label}
      </h3>

      <p
        className="
          mt-3 font-mono
          font-semibold tracking-widest
          text-slate-950
        "
        data-stage8-venue-results={
          fieldPrefix
        }
      >
        {results || "No results"}
      </p>

      <p
        className="
          mt-1 text-xs
          text-slate-500
        "
        data-stage8-venue-matches={
          fieldPrefix
        }
      >
        {matchesAvailable} matches available
      </p>

      <dl
        className="
          mt-4 space-y-2
        "
      >
        <div className="flex justify-between gap-4">
          <dt className="text-sm text-slate-600">
            Points
          </dt>

          <dd
            className="font-semibold text-slate-950"
            data-stage8-venue-points={
              fieldPrefix
            }
          >
            {points}
          </dd>
        </div>

        <div className="flex justify-between gap-4">
          <dt className="text-sm text-slate-600">
            W-D-L
          </dt>

          <dd className="font-semibold text-slate-950">
            {wins} - {draws} - {losses}
          </dd>
        </div>

        <div className="flex justify-between gap-4">
          <dt className="text-sm text-slate-600">
            Goals
          </dt>

          <dd className="font-semibold text-slate-950">
            {goalsFor} - {goalsAgainst}
          </dd>
        </div>

        <div className="flex justify-between gap-4">
          <dt className="text-sm text-slate-600">
            Goal difference
          </dt>

          <dd className="font-semibold text-slate-950">
            {signedIntegerFormatter.format(
              goalDifference,
            )}
          </dd>
        </div>
      </dl>
    </div>
  );
}


type TeamHomeAwayFormProps =
  Readonly<{
    homeMatchesAvailable:
      number;

    homeResults:
      string;

    homePoints:
      number;

    homeWins:
      number;

    homeDraws:
      number;

    homeLosses:
      number;

    homeGoalsFor:
      number;

    homeGoalsAgainst:
      number;

    homeGoalDifference:
      number;

    awayMatchesAvailable:
      number;

    awayResults:
      string;

    awayPoints:
      number;

    awayWins:
      number;

    awayDraws:
      number;

    awayLosses:
      number;

    awayGoalsFor:
      number;

    awayGoalsAgainst:
      number;

    awayGoalDifference:
      number;
  }>;


export function TeamHomeAwayForm({
  homeMatchesAvailable,
  homeResults,
  homePoints,
  homeWins,
  homeDraws,
  homeLosses,
  homeGoalsFor,
  homeGoalsAgainst,
  homeGoalDifference,
  awayMatchesAvailable,
  awayResults,
  awayPoints,
  awayWins,
  awayDraws,
  awayLosses,
  awayGoalsFor,
  awayGoalsAgainst,
  awayGoalDifference,
}: TeamHomeAwayFormProps) {

  return (
    <section
      aria-labelledby="team-home-away-form-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="team-home-away-form"
    >
      <h2
        id="team-home-away-form-heading"
        className="
          text-lg font-bold
          text-slate-950
        "
      >
        Home / away form
      </h2>

      <div
        className="
          mt-5 grid gap-6
          md:grid-cols-2
        "
      >
        <VenueFormBlock
          label="Recent home form"
          matchesAvailable={
            homeMatchesAvailable
          }
          results={
            homeResults
          }
          points={
            homePoints
          }
          wins={
            homeWins
          }
          draws={
            homeDraws
          }
          losses={
            homeLosses
          }
          goalsFor={
            homeGoalsFor
          }
          goalsAgainst={
            homeGoalsAgainst
          }
          goalDifference={
            homeGoalDifference
          }
          fieldPrefix="home"
        />

        <VenueFormBlock
          label="Recent away form"
          matchesAvailable={
            awayMatchesAvailable
          }
          results={
            awayResults
          }
          points={
            awayPoints
          }
          wins={
            awayWins
          }
          draws={
            awayDraws
          }
          losses={
            awayLosses
          }
          goalsFor={
            awayGoalsFor
          }
          goalsAgainst={
            awayGoalsAgainst
          }
          goalDifference={
            awayGoalDifference
          }
          fieldPrefix="away"
        />
      </div>
    </section>
  );
}

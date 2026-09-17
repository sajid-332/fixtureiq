import {
  MatchCard,
} from "../components/matches/match-card";

import {
  loadUpcomingMatches,
} from "../lib/dashboard/load-upcoming-matches";

import {
  extractUpcomingDashboardMatches,
} from "../lib/dashboard/upcoming-records";


export const dynamic =
  "force-dynamic";


export default async function Home() {

  const result =
    await loadUpcomingMatches();


  if (
    result.state !==
    "READY"
  ) {

    return (
      <section
        aria-labelledby="upcoming-heading"
        data-fixtureiq-dashboard-state={
          result.state
        }
      >
        <h1
          id="upcoming-heading"
          className="
            text-2xl font-bold
            tracking-tight text-slate-950
            sm:text-3xl
          "
        >
          Upcoming matches
        </h1>

        <p
          className="
            mt-3 max-w-2xl
            text-sm leading-6
            text-slate-600
          "
        >
          Upcoming match intelligence is
          currently unavailable.
        </p>
      </section>
    );
  }


  const matches =
    extractUpcomingDashboardMatches(
      result.data,
    );


  if (
    matches.length === 0
  ) {

    return (
      <section
        aria-labelledby="upcoming-heading"
        data-fixtureiq-dashboard-state="READY"
        data-fixtureiq-dashboard-empty="true"
      >
        <h1
          id="upcoming-heading"
          className="
            text-2xl font-bold
            tracking-tight text-slate-950
            sm:text-3xl
          "
        >
          Upcoming matches
        </h1>

        <p
          className="
            mt-3 text-sm
            text-slate-600
          "
        >
          No upcoming matches are available.
        </p>
      </section>
    );
  }


  return (
    <section
      aria-labelledby="upcoming-heading"
      data-fixtureiq-dashboard-state="READY"
    >
      <header
        className="
          mb-8
        "
      >
        <p
          className="
            text-sm font-semibold
            uppercase tracking-wide
            text-slate-500
          "
        >
          Premier League
        </p>

        <h1
          id="upcoming-heading"
          className="
            mt-2 text-2xl font-bold
            tracking-tight text-slate-950
            sm:text-3xl
          "
        >
          Upcoming matches
        </h1>

        <p
          className="
            mt-3 max-w-2xl
            text-sm leading-6
            text-slate-600
          "
        >
          Prediction probabilities and
          match intelligence from FixtureIQ.
        </p>
      </header>

      <div
        className="
          grid gap-6
          lg:grid-cols-2
        "
      >
        {matches.map(
          (match) => (
            <MatchCard
              key={
                String(
                  match.fixture_id,
                )
              }
              fixtureId={
                match.fixture_id
              }
              homeTeamName={
                match.home_team_name
              }
              awayTeamName={
                match.away_team_name
              }
              kickoffUtc={
                match.kickoffUtc
              }
              stage7_prob_home_win={
                match.stage7_prob_home_win
              }
              stage7_prob_draw={
                match.stage7_prob_draw
              }
              stage7_prob_away_win={
                match.stage7_prob_away_win
              }
              stage7_predicted_label={
                match.stage7_predicted_label
              }
              stage7_confidence={
                match.stage7_confidence
              }
              confidence_band={
                match.stage9_confidence_band
              }
              uncertainty_band={
                match.stage9_uncertainty_band
              }
              context_alignment={
                match.stage9_context_alignment
              }
              explanation_headline={
                match.stage9_explanation_headline
              }
              explanation_summary={
                match.stage9_explanation_summary
              }
            />
          ),
        )}
      </div>
    </section>
  );
}

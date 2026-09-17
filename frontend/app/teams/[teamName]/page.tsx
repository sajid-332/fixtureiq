import {
  notFound,
} from "next/navigation";

import {
  TeamIdentityHeader,
} from "../../../components/teams/team-identity-header";

import {
  TeamUpcomingMatches,
} from "../../../components/teams/team-upcoming-matches";

import {
  TeamPredictionCard,
} from "../../../components/teams/team-prediction-card";

import {
  loadTeamIntelligence,
} from "../../../lib/teams/load-team-intelligence";

import {
  extractTeamPageData,
} from "../../../lib/teams/team-records";

import type {
  TeamRouteParams,
} from "../../../lib/domain/types";


export const dynamic =
  "force-dynamic";


type TeamPageProps =
  Readonly<{
    params:
      Promise<
        TeamRouteParams
      >;
  }>;


export default async function TeamPage({
  params,
}: TeamPageProps) {

  const {
    teamName,
  } = await params;


  const result =
    await loadTeamIntelligence(
      teamName,
    );


  if (
    result.state ===
    "NOT_FOUND"
  ) {
    notFound();
  }


  if (
    result.state !==
    "READY"
  ) {

    return (
      <section
        aria-labelledby="team-unavailable-heading"
        data-fixtureiq-team-state={
          result.state
        }
      >
        <h1
          id="team-unavailable-heading"
          className="
            text-2xl font-bold
            tracking-tight
            text-slate-950
          "
        >
          Team intelligence unavailable
        </h1>

        <p
          className="
            mt-3 max-w-2xl
            text-sm leading-6
            text-slate-600
          "
        >
          This team cannot be displayed
          right now.
        </p>
      </section>
    );
  }


  const team =
    extractTeamPageData(
      result.data,
      teamName,
    );


  return (
    <article
      data-fixtureiq-route="team-intelligence"
      data-fixtureiq-team-state="READY"
    >
      <TeamIdentityHeader
        teamName={
          team.teamName
        }
      />

      <TeamUpcomingMatches
        teamName={
          team.teamName
        }
        matchCount={
          team.matches.length
        }
      >
        {
          team.matches.map(
            (
              match,
            ) => (
              <TeamPredictionCard
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
                  match.date
                }
                homeProbability={
                  match.stage7_prob_home_win
                }
                drawProbability={
                  match.stage7_prob_draw
                }
                awayProbability={
                  match.stage7_prob_away_win
                }
                predictedLabel={
                  match.stage7_predicted_label
                }
                confidence={
                  match.stage7_confidence
                }
                confidenceBand={
                  match.stage9_confidence_band
                }
                uncertaintyBand={
                  match.stage9_uncertainty_band
                }
                contextAlignment={
                  match.stage9_context_alignment
                }
              />
            ),
          )
        }
      </TeamUpcomingMatches>
    </article>
  );
}

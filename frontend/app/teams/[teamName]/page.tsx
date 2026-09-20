import {
  ConnectionErrorState,
} from "../../../components/runtime/connection-error-state";

import {
  ServiceNotReadyState,
} from "../../../components/runtime/service-not-ready-state";

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
  TeamStandings,
} from "../../../components/teams/team-standings";

import {
  TeamRecentForm,
} from "../../../components/teams/team-recent-form";

import {
  TeamHomeAwayForm,
} from "../../../components/teams/team-home-away-form";

import {
  loadTeamIntelligence,
} from "../../../lib/teams/load-team-intelligence";

import {
  loadTeamContext,
} from "../../../lib/teams/load-team-context";

import {
  extractTeamPageData,
} from "../../../lib/teams/team-records";

import {
  extractTeamFormRecord,
  extractTeamStandingsRecord,
} from "../../../lib/teams/team-context-records";

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
    result.state ===
    "NOT_READY"
  ) {

    return (
      <ServiceNotReadyState
        state="NOT_READY"
        httpStatus={
          result.status
        }
        resource="Team intelligence"
      />
    );
  }


  if (
    result.state ===
    "CONNECTION_ERROR"
  ) {

    return (
      <ConnectionErrorState
        httpStatus={
          result.status
        }
        resource="Team intelligence"
      />
    );
  }


  const team =
    extractTeamPageData(
      result.data,
      teamName,
    );


  const [
    standingsResult,
    formResult,
  ] = await loadTeamContext(
    teamName,
  );


  if (
    standingsResult.state ===
    "NOT_FOUND"
    ||
    formResult.state ===
    "NOT_FOUND"
  ) {
    notFound();
  }


  if (
    standingsResult.state ===
    "NOT_READY"
    ||
    formResult.state ===
    "NOT_READY"
  ) {

    return (
      <ServiceNotReadyState
        state="NOT_READY"
        httpStatus={
          standingsResult.state === "NOT_READY"
            ? standingsResult.status
            : formResult.state === "NOT_READY"
              ? formResult.status
              : null
        }
        resource="Team context"
      />
    );
  }


  if (
    standingsResult.state ===
    "CONNECTION_ERROR"
    ||
    formResult.state ===
    "CONNECTION_ERROR"
  ) {

    return (
      <ConnectionErrorState
        httpStatus={
          standingsResult.state === "CONNECTION_ERROR"
            ? standingsResult.status
            : formResult.state === "CONNECTION_ERROR"
              ? formResult.status
              : null
        }
        resource="Team context"
      />
    );
  }


  if (
    standingsResult.state !==
    "READY"
    ||
    formResult.state !==
    "READY"
  ) {

    return (
      <section
        aria-labelledby="team-context-unavailable-heading"
        data-fixtureiq-team-context-state="UNAVAILABLE"
      >
        <h1
          id="team-context-unavailable-heading"
          className="
            text-2xl font-bold
            tracking-tight
            text-slate-950
          "
        >
          Team context unavailable
        </h1>

        <p
          className="
            mt-3 max-w-2xl
            text-sm leading-6
            text-slate-600
          "
        >
          Current standings or form
          cannot be displayed right now.
        </p>
      </section>
    );
  }


  const standings =
    extractTeamStandingsRecord(
      standingsResult.data,
      teamName,
    );


  const form =
    extractTeamFormRecord(
      formResult.data,
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

      <div
        className="
          mt-6 grid gap-6
          lg:grid-cols-2
        "
      >
        <TeamStandings
          position={
            standings.position
          }
          points={
            standings.points
          }
          played={
            standings.played
          }
          won={
            standings.won
          }
          drawn={
            standings.drawn
          }
          lost={
            standings.lost
          }
          goalsFor={
            standings.goals_for
          }
          goalsAgainst={
            standings.goals_against
          }
          goalDifference={
            standings.goal_difference
          }
        />

        <TeamRecentForm
          matchesAvailable={
            form.form_matches_available
          }
          results={
            form.recent_results
          }
          points={
            form.recent_points
          }
          wins={
            form.recent_wins
          }
          draws={
            form.recent_draws
          }
          losses={
            form.recent_losses
          }
          goalsFor={
            form.recent_goals_for
          }
          goalsAgainst={
            form.recent_goals_against
          }
          goalDifference={
            form.recent_goal_difference
          }
        />
      </div>

      <div
        className="
          mt-6
        "
      >
        <TeamHomeAwayForm
          homeMatchesAvailable={
            form.home_form_matches_available
          }
          homeResults={
            form.home_recent_results
          }
          homePoints={
            form.home_recent_points
          }
          homeWins={
            form.home_recent_wins
          }
          homeDraws={
            form.home_recent_draws
          }
          homeLosses={
            form.home_recent_losses
          }
          homeGoalsFor={
            form.home_recent_goals_for
          }
          homeGoalsAgainst={
            form.home_recent_goals_against
          }
          homeGoalDifference={
            form.home_recent_goal_difference
          }
          awayMatchesAvailable={
            form.away_form_matches_available
          }
          awayResults={
            form.away_recent_results
          }
          awayPoints={
            form.away_recent_points
          }
          awayWins={
            form.away_recent_wins
          }
          awayDraws={
            form.away_recent_draws
          }
          awayLosses={
            form.away_recent_losses
          }
          awayGoalsFor={
            form.away_recent_goals_for
          }
          awayGoalsAgainst={
            form.away_recent_goals_against
          }
          awayGoalDifference={
            form.away_recent_goal_difference
          }
        />
      </div>

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

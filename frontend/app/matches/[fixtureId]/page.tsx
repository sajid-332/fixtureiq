import {
  notFound,
} from "next/navigation";

import {
  MatchFixtureHeader,
} from "../../../components/matches/match-fixture-header";

import {
  MatchPredictionOverview,
} from "../../../components/matches/match-prediction-overview";

import {
  MatchProbabilityVisualization,
} from "../../../components/matches/match-probability-visualization";

import {
  MatchConfidence,
} from "../../../components/matches/match-confidence";

import {
  MatchUncertainty,
} from "../../../components/matches/match-uncertainty";

import {
  MatchLeaguePositionComparison,
} from "../../../components/matches/match-league-position-comparison";

import {
  MatchPointsComparison,
} from "../../../components/matches/match-points-comparison";

import {
  MatchGoalDifferenceComparison,
} from "../../../components/matches/match-goal-difference-comparison";

import {
  MatchRecentForm,
} from "../../../components/matches/match-recent-form";

import {
  MatchVenueForm,
} from "../../../components/matches/match-venue-form";

import {
  MatchContextSupport,
} from "../../../components/matches/match-context-support";

import {
  MatchContextAlignment,
} from "../../../components/matches/match-context-alignment";

import {
  MatchIntelligenceExplanation,
} from "../../../components/matches/match-intelligence-explanation";

import {
  MatchFreshnessStatus,
} from "../../../components/matches/match-freshness-status";

import {
  loadMatchIntelligence,
} from "../../../lib/matches/load-match-intelligence";

import {
  loadIntelligenceStatus,
} from "../../../lib/matches/load-intelligence-status";

import {
  extractMatchFixtureHeader,
} from "../../../lib/matches/match-header-record";

import {
  extractMatchPredictionRecord,
} from "../../../lib/matches/match-prediction-record";

import {
  extractMatchContextRecord,
} from "../../../lib/matches/match-context-record";

import {
  extractMatchIntelligenceDetailRecord,
} from "../../../lib/matches/match-intelligence-detail-record";

import type {
  FixtureRouteParams,
} from "../../../lib/domain/types";


export const dynamic =
  "force-dynamic";


type MatchDetailPageProps =
  Readonly<{
    params:
      Promise<
        FixtureRouteParams
      >;
  }>;


export default async function MatchDetailPage({
  params,
}: MatchDetailPageProps) {

  const {
    fixtureId,
  } = await params;


  const result =
    await loadMatchIntelligence(
      fixtureId,
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
        aria-labelledby="match-unavailable-heading"
        data-fixtureiq-match-state={
          result.state
        }
      >
        <h1
          id="match-unavailable-heading"
          className="
            text-2xl font-bold
            tracking-tight text-slate-950
          "
        >
          Match intelligence unavailable
        </h1>

        <p
          className="
            mt-3 max-w-2xl
            text-sm leading-6
            text-slate-600
          "
        >
          This match cannot be displayed
          right now.
        </p>
      </section>
    );
  }


  const statusResult =
    await loadIntelligenceStatus();


  const header =
    extractMatchFixtureHeader(
      result.data,
      fixtureId,
    );


  const prediction =
    extractMatchPredictionRecord(
      result.data,
      fixtureId,
    );


  const context =
    extractMatchContextRecord(
      result.data,
      fixtureId,
    );


  const intelligence =
    extractMatchIntelligenceDetailRecord(
      result.data,
      fixtureId,
    );


  return (
    <article
      data-fixtureiq-route="match-detail"
      data-fixtureiq-match-state="READY"
    >
      <MatchFixtureHeader
        fixtureId={
          header.fixture_id
        }
        homeTeamName={
          header.home_team_name
        }
        awayTeamName={
          header.away_team_name
        }
        kickoffUtc={
          header.date
        }
      />
      <div
        className="
          mt-6 space-y-6
        "
      >
        <MatchPredictionOverview
          predictedLabel={
            prediction.stage7_predicted_label
          }
        />

        <MatchProbabilityVisualization
          homeProbability={
            prediction.stage7_prob_home_win
          }
          drawProbability={
            prediction.stage7_prob_draw
          }
          awayProbability={
            prediction.stage7_prob_away_win
          }
        />

        <div
          className="
            grid gap-6
            md:grid-cols-2
          "
        >
          <MatchConfidence
            confidence={
              prediction.stage7_confidence
            }
            confidenceBand={
              prediction.stage9_confidence_band
            }
          />

          <MatchUncertainty
            uncertaintyBand={
              prediction.stage9_uncertainty_band
            }
          />
        </div>
      </div>
      <div
        className="
          mt-6 grid gap-6
          lg:grid-cols-3
        "
      >
        <MatchLeaguePositionComparison
          homeTeamName={
            header.home_team_name
          }
          awayTeamName={
            header.away_team_name
          }
          homePosition={
            context.home_team_position
          }
          awayPosition={
            context.away_team_position
          }
        />

        <MatchPointsComparison
          homeTeamName={
            header.home_team_name
          }
          awayTeamName={
            header.away_team_name
          }
          homePoints={
            context.home_team_points
          }
          awayPoints={
            context.away_team_points
          }
        />

        <MatchGoalDifferenceComparison
          homeTeamName={
            header.home_team_name
          }
          awayTeamName={
            header.away_team_name
          }
          homeGoalDifference={
            context.home_team_goal_difference
          }
          awayGoalDifference={
            context.away_team_goal_difference
          }
        />
      </div>

      <div
        className="
          mt-6
        "
      >
        <MatchRecentForm
          homeTeamName={
            header.home_team_name
          }
          awayTeamName={
            header.away_team_name
          }
          homeResults={
            context.home_team_recent_results
          }
          awayResults={
            context.away_team_recent_results
          }
          homeMatchesAvailable={
            context.home_team_form_matches_available
          }
          awayMatchesAvailable={
            context.away_team_form_matches_available
          }
        />
      </div>
      <div
        className="
          mt-6
        "
      >
        <MatchVenueForm
          homeTeamName={
            header.home_team_name
          }
          awayTeamName={
            header.away_team_name
          }
          homeRecentPoints={
            intelligence.home_team_home_recent_points
          }
          awayRecentPoints={
            intelligence.away_team_away_recent_points
          }
          homeMatchesAvailable={
            intelligence.home_team_home_form_matches_available
          }
          awayMatchesAvailable={
            intelligence.away_team_away_form_matches_available
          }
        />
      </div>

      <div
        className="
          mt-6 grid gap-6
          md:grid-cols-2
        "
      >
        <MatchContextSupport
          supportScore={
            intelligence.stage9_context_support_score
          }
        />

        <MatchContextAlignment
          alignment={
            intelligence.stage9_context_alignment
          }
        />
      </div>

      <div
        className="
          mt-6
        "
      >
        <MatchIntelligenceExplanation
          headline={
            intelligence.stage9_explanation_headline
          }
          summary={
            intelligence.stage9_explanation_summary
          }
        />
      </div>
      <div
        className="
          mt-6
        "
      >
        <MatchFreshnessStatus
          state={
            statusResult.state
          }
          httpStatus={
            statusResult.status
          }
        />
      </div>
    </article>
  );
}

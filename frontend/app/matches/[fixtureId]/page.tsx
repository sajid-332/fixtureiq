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
  loadMatchIntelligence,
} from "../../../lib/matches/load-match-intelligence";

import {
  extractMatchFixtureHeader,
} from "../../../lib/matches/match-header-record";

import {
  extractMatchPredictionRecord,
} from "../../../lib/matches/match-prediction-record";

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
    </article>
  );
}

import {
  notFound,
} from "next/navigation";

import {
  MatchFixtureHeader,
} from "../../../components/matches/match-fixture-header";

import {
  loadMatchIntelligence,
} from "../../../lib/matches/load-match-intelligence";

import {
  extractMatchFixtureHeader,
} from "../../../lib/matches/match-header-record";

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
    </article>
  );
}

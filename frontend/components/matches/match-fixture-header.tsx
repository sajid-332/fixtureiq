import type {
  FixtureId,
} from "../../lib/domain/types";

import {
  formatKickoffUtc,
} from "../../lib/formatters/kickoff";


type MatchFixtureHeaderProps =
  Readonly<{
    fixtureId:
      FixtureId;

    homeTeamName:
      string;

    awayTeamName:
      string;

    kickoffUtc:
      string;
  }>;


export function MatchFixtureHeader({
  fixtureId,
  homeTeamName,
  awayTeamName,
  kickoffUtc,
}: MatchFixtureHeaderProps) {

  const kickoffLabel =
    formatKickoffUtc(
      kickoffUtc,
    );


  return (
    <header
      aria-labelledby="match-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-6
        shadow-sm
        sm:px-7 sm:py-8
      "
      data-fixtureiq-component="match-fixture-header"
      data-fixture-id={
        String(
          fixtureId,
        )
      }
    >
      <p
        className="
          text-sm font-semibold
          uppercase tracking-wide
          text-slate-500
        "
      >
        Match intelligence
      </p>

      <div
        className="
          mt-5 grid
          grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]
          items-center gap-4
        "
      >
        <div
          className="
            min-w-0
          "
        >
          <p
            className="
              text-xs font-medium
              uppercase tracking-wide
              text-slate-500
            "
          >
            Home
          </p>

          <h1
            id="match-heading"
            className="
              mt-1 break-words
              text-xl font-bold
              tracking-tight
              text-slate-950
              sm:text-2xl
            "
          >
            {homeTeamName}
          </h1>
        </div>

        <span
          aria-hidden="true"
          className="
            text-sm font-semibold
            text-slate-400
          "
        >
          vs
        </span>

        <div
          className="
            min-w-0 text-right
          "
        >
          <p
            className="
              text-xs font-medium
              uppercase tracking-wide
              text-slate-500
            "
          >
            Away
          </p>

          <p
            className="
              mt-1 break-words
              text-xl font-bold
              tracking-tight
              text-slate-950
              sm:text-2xl
            "
          >
            {awayTeamName}
          </p>
        </div>
      </div>

      <div
        className="
          mt-6 border-t
          border-slate-100
          pt-4
        "
      >
        <p
          className="
            text-xs font-medium
            uppercase tracking-wide
            text-slate-500
          "
        >
          Kickoff
        </p>

        <time
          dateTime={
            kickoffUtc
          }
          className="
            mt-1 block
            text-sm font-semibold
            text-slate-700
          "
          data-stage9-field="date"
        >
          {kickoffLabel} UTC
        </time>
      </div>
    </header>
  );
}

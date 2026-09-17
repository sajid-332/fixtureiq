import type {
  ReactNode,
} from "react";

import {
  formatKickoffUtc,
} from "../../lib/formatters/kickoff";


type MatchCardProps =
  Readonly<{
    homeTeamName: string;
    awayTeamName: string;
    kickoffUtc: string;
    children?: ReactNode;
  }>;


export function MatchCard({
  homeTeamName,
  awayTeamName,
  kickoffUtc,
  children,
}: MatchCardProps) {
  const kickoffLabel =
    formatKickoffUtc(
      kickoffUtc,
    );

  return (
    <article
      aria-label={`${homeTeamName} vs ${awayTeamName}`}
      className="
        overflow-hidden rounded-xl
        border border-slate-200
        bg-white shadow-sm
      "
      data-fixtureiq-component="match-card"
    >
      <header
        className="
          border-b border-slate-100
          px-5 py-5
          sm:px-6
        "
      >
        <div
          className="
            grid
            grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]
            items-center gap-3
          "
        >
          <div className="min-w-0">
            <p
              className="
                text-xs font-medium uppercase
                tracking-wide text-slate-500
              "
            >
              Home
            </p>

            <h2
              className="
                mt-1 break-words
                text-base font-semibold
                text-slate-950
              "
            >
              {homeTeamName}
            </h2>
          </div>

          <span
            aria-hidden="true"
            className="
              text-sm font-medium
              text-slate-400
            "
          >
            vs
          </span>

          <div className="min-w-0 text-right">
            <p
              className="
                text-xs font-medium uppercase
                tracking-wide text-slate-500
              "
            >
              Away
            </p>

            <h2
              className="
                mt-1 break-words
                text-base font-semibold
                text-slate-950
              "
            >
              {awayTeamName}
            </h2>
          </div>
        </div>

        <div
          className="
            mt-4 flex items-center
            justify-center
            text-sm text-slate-600
          "
        >
          <span className="sr-only">
            Kickoff:
          </span>

          <time dateTime={kickoffUtc}>
            {kickoffLabel} UTC
          </time>
        </div>
      </header>

      {children ? (
        <div className="px-5 py-5 sm:px-6">
          {children}
        </div>
      ) : null}
    </article>
  );
}

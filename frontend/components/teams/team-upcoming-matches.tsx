import type {
  ReactNode,
} from "react";


type TeamUpcomingMatchesProps =
  Readonly<{
    teamName:
      string;

    matchCount:
      number;

    children:
      ReactNode;
  }>;


export function TeamUpcomingMatches({
  teamName,
  matchCount,
  children,
}: TeamUpcomingMatchesProps) {

  return (
    <section
      aria-labelledby="team-upcoming-heading"
      className="
        mt-6
      "
      data-fixtureiq-component="team-upcoming-matches"
      data-team-match-count={
        matchCount
      }
    >
      <div
        className="
          flex flex-wrap
          items-end justify-between
          gap-3
        "
      >
        <div>
          <p
            className="
              text-xs font-medium
              uppercase tracking-wide
              text-slate-500
            "
          >
            {teamName}
          </p>

          <h2
            id="team-upcoming-heading"
            className="
              mt-1 text-xl font-bold
              tracking-tight
              text-slate-950
            "
          >
            Upcoming matches
          </h2>
        </div>

        <p
          className="
            text-sm
            text-slate-500
          "
        >
          {matchCount} matches
        </p>
      </div>

      <div
        className="
          mt-5 grid gap-5
          xl:grid-cols-2
        "
      >
        {children}
      </div>
    </section>
  );
}

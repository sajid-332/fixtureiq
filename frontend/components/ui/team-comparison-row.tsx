import type {
  ReactNode,
} from "react";


type TeamComparisonRowProps =
  Readonly<{
    label:
      string;

    homeTeamName:
      string;

    awayTeamName:
      string;

    homeValue:
      ReactNode;

    awayValue:
      ReactNode;
  }>;


export function TeamComparisonRow({
  label,
  homeTeamName,
  awayTeamName,
  homeValue,
  awayValue,
}: TeamComparisonRowProps) {

  return (
    <div
      className="
        grid
        grid-cols-[minmax(0,1fr)_minmax(7rem,auto)_minmax(0,1fr)]
        items-center
        gap-3
        border-b border-slate-100
        py-3
        last:border-b-0
      "
      data-fixtureiq-component="team-comparison-row"
    >
      <div
        className="
          min-w-0 text-left
        "
      >
        <p
          className="
            truncate text-xs
            text-slate-500
          "
        >
          {homeTeamName}
        </p>

        <div
          className="
            mt-1 font-semibold
            text-slate-950
          "
          data-team-comparison-side="home"
        >
          {homeValue}
        </div>
      </div>

      <p
        className="
          text-center text-xs
          font-medium
          text-slate-500
        "
        data-team-comparison-label
      >
        {label}
      </p>

      <div
        className="
          min-w-0 text-right
        "
      >
        <p
          className="
            truncate text-xs
            text-slate-500
          "
        >
          {awayTeamName}
        </p>

        <div
          className="
            mt-1 font-semibold
            text-slate-950
          "
          data-team-comparison-side="away"
        >
          {awayValue}
        </div>
      </div>
    </div>
  );
}

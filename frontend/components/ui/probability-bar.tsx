import {
  formatProbability,
} from "../../lib/formatters/probability";


type ProbabilityBarProps =
  Readonly<{
    label:
      string;

    value:
      number;

    sourceField?:
      string;
  }>;


export function ProbabilityBar({
  label,
  value,
  sourceField,
}: ProbabilityBarProps) {

  return (
    <div
      data-fixtureiq-component="probability-bar"
      data-source-field={
        sourceField
      }
    >
      <div
        className="
          flex items-center
          justify-between gap-4
        "
      >
        <span
          className="
            text-sm font-medium
            text-slate-700
          "
        >
          {label}
        </span>

        <span
          className="
            text-sm font-semibold
            tabular-nums
            text-slate-950
          "
        >
          {formatProbability(
            value,
          )}
        </span>
      </div>

      <progress
        aria-label={`${label} probability`}
        className="
          mt-2 block h-2
          w-full overflow-hidden
          rounded-full
        "
        max={1}
        value={
          value
        }
      >
        {formatProbability(
          value,
        )}
      </progress>
    </div>
  );
}

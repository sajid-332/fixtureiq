import type {
  OutcomeLabel,
} from "../../lib/domain/types";


type OutcomeBadgeProps =
  Readonly<{
    outcome:
      OutcomeLabel;
  }>;


export function OutcomeBadge({
  outcome,
}: OutcomeBadgeProps) {

  return (
    <span
      aria-label={`Predicted outcome: ${outcome}`}
      className="
        inline-flex items-center
        rounded-full
        border border-slate-300
        bg-slate-50
        px-3 py-1
        text-xs font-semibold
        text-slate-900
      "
      data-fixtureiq-component="outcome-badge"
      data-outcome={
        outcome
      }
    >
      {outcome}
    </span>
  );
}

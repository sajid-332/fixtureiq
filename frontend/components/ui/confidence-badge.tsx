import type {
  ConfidenceBand,
} from "../../lib/domain/types";


type ConfidenceBadgeProps =
  Readonly<{
    band:
      ConfidenceBand;
  }>;


export function ConfidenceBadge({
  band,
}: ConfidenceBadgeProps) {

  return (
    <span
      aria-label={`Confidence: ${band}`}
      className="
        inline-flex items-center
        rounded-full
        border border-slate-300
        bg-white
        px-3 py-1
        text-xs font-semibold
        text-slate-900
      "
      data-fixtureiq-component="confidence-badge"
      data-confidence-band={
        band
      }
    >
      {band}
    </span>
  );
}

import type {
  UncertaintyBand,
} from "../../lib/domain/types";


type UncertaintyBadgeProps =
  Readonly<{
    band:
      UncertaintyBand;
  }>;


export function UncertaintyBadge({
  band,
}: UncertaintyBadgeProps) {

  return (
    <span
      aria-label={`Uncertainty: ${band}`}
      className="
        inline-flex items-center
        rounded-full
        border border-slate-300
        bg-white
        px-3 py-1
        text-xs font-semibold
        text-slate-900
      "
      data-fixtureiq-component="uncertainty-badge"
      data-uncertainty-band={
        band
      }
    >
      {band}
    </span>
  );
}

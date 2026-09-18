import type {
  ContextAlignment,
} from "../../lib/domain/types";


type ContextAlignmentBadgeProps =
  Readonly<{
    alignment:
      ContextAlignment;
  }>;


export function ContextAlignmentBadge({
  alignment,
}: ContextAlignmentBadgeProps) {

  return (
    <span
      aria-label={`Context alignment: ${alignment}`}
      className="
        inline-flex items-center
        rounded-full
        border border-slate-300
        bg-white
        px-3 py-1
        text-xs font-semibold
        text-slate-900
      "
      data-fixtureiq-component="context-alignment-badge"
      data-context-alignment={
        alignment
      }
    >
      {alignment}
    </span>
  );
}

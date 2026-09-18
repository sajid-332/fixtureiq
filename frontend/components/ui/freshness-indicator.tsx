import type {
  ApiTerminalState,
} from "../../lib/api/result";


type FreshnessIndicatorProps =
  Readonly<{
    state:
      ApiTerminalState;

    httpStatus:
      number | null;
  }>;


export function FreshnessIndicator({
  state,
  httpStatus,
}: FreshnessIndicatorProps) {

  const statusLabel =
    httpStatus === null
      ? "No HTTP response"
      : String(
          httpStatus,
        );


  return (
    <div
      aria-label={`Service status: ${state}`}
      className="
        inline-flex flex-wrap
        items-center gap-x-3 gap-y-1
        rounded-lg
        border border-slate-200
        bg-white
        px-3 py-2
        text-xs
        text-slate-700
      "
      data-fixtureiq-component="freshness-indicator"
      data-freshness-state={
        state
      }
    >
      <span
        className="
          font-semibold
          text-slate-950
        "
      >
        {state}
      </span>

      <span
        aria-hidden="true"
        className="text-slate-300"
      >
        •
      </span>

      <span
        data-freshness-http-status
      >
        {statusLabel}
      </span>
    </div>
  );
}

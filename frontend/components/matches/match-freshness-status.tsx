import type {
  ApiTerminalState,
} from "../../lib/api/result";


type MatchFreshnessStatusProps =
  Readonly<{
    state:
      ApiTerminalState;

    httpStatus:
      number | null;
  }>;


export function MatchFreshnessStatus({
  state,
  httpStatus,
}: MatchFreshnessStatusProps) {

  const statusLabel =
    httpStatus === null
      ? "No HTTP response"
      : String(
          httpStatus,
        );


  return (
    <section
      aria-labelledby="match-freshness-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-freshness-status"
      data-freshness-state={
        state
      }
    >
      <h2
        id="match-freshness-heading"
        className="
          text-base font-bold
          text-slate-950
        "
      >
        Freshness &amp; service status
      </h2>

      <dl
        className="
          mt-4 space-y-3
        "
      >
        <div
          className="
            flex items-center
            justify-between gap-4
          "
        >
          <dt
            className="
              text-sm text-slate-600
            "
          >
            Intelligence runtime
          </dt>

          <dd
            className="
              text-sm font-semibold
              text-slate-950
            "
            data-stage9-runtime-state
          >
            {state}
          </dd>
        </div>

        <div
          className="
            flex items-center
            justify-between gap-4
          "
        >
          <dt
            className="
              text-sm text-slate-600
            "
          >
            Status request
          </dt>

          <dd
            className="
              text-sm font-semibold
              text-slate-950
            "
            data-stage9-runtime-http-status
          >
            {statusLabel}
          </dd>
        </div>
      </dl>

      <p
        className="
          mt-4 text-xs
          leading-5 text-slate-500
        "
      >
        Freshness is enforced by the
        Stage 9 backend runtime policy.
        This page does not reuse a previous
        freshness response.
      </p>
    </section>
  );
}

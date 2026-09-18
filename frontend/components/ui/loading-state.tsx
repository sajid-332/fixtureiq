type LoadingStateProps =
  Readonly<{
    label?:
      string;
  }>;


export function LoadingState({
  label = "Loading FixtureIQ data...",
}: LoadingStateProps) {

  return (
    <div
      aria-busy="true"
      aria-live="polite"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-6
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="loading-state"
      role="status"
    >
      <p
        className="
          text-sm font-semibold
          text-slate-700
        "
        data-loading-state-label
      >
        {label}
      </p>

      <div
        aria-hidden="true"
        className="
          mt-4 space-y-3
        "
      >
        <div
          className="
            h-3 w-full
            rounded bg-slate-100
          "
        />

        <div
          className="
            h-3 w-5/6
            rounded bg-slate-100
          "
        />

        <div
          className="
            h-3 w-2/3
            rounded bg-slate-100
          "
        />
      </div>
    </div>
  );
}

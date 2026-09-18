type RecentFormDisplayProps =
  Readonly<{
    label:
      string;

    results:
      string;

    matchesAvailable:
      number;
  }>;


export function RecentFormDisplay({
  label,
  results,
  matchesAvailable,
}: RecentFormDisplayProps) {

  return (
    <div
      aria-label={`${label} recent form`}
      className="
        rounded-lg
        border border-slate-200
        bg-white
        px-4 py-4
      "
      data-fixtureiq-component="recent-form-display"
    >
      <p
        className="
          text-xs font-medium
          uppercase tracking-wide
          text-slate-500
        "
      >
        {label}
      </p>

      <p
        className="
          mt-2 font-mono
          text-lg font-semibold
          tracking-widest
          text-slate-950
        "
        data-recent-form-results
      >
        {results || "No results"}
      </p>

      <p
        className="
          mt-2 text-xs
          text-slate-500
        "
        data-recent-form-matches-available
      >
        {matchesAvailable} matches available
      </p>
    </div>
  );
}

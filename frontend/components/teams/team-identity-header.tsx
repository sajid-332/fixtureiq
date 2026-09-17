type TeamIdentityHeaderProps =
  Readonly<{
    teamName:
      string;
  }>;


export function TeamIdentityHeader({
  teamName,
}: TeamIdentityHeaderProps) {

  return (
    <header
      aria-labelledby="team-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-6
        shadow-sm
        sm:px-7 sm:py-8
      "
      data-fixtureiq-component="team-identity-header"
    >
      <p
        className="
          text-sm font-semibold
          uppercase tracking-wide
          text-slate-500
        "
      >
        Team intelligence
      </p>

      <h1
        id="team-heading"
        className="
          mt-2 break-words
          text-2xl font-bold
          tracking-tight
          text-slate-950
          sm:text-3xl
        "
        data-team-name
      >
        {teamName}
      </h1>
    </header>
  );
}

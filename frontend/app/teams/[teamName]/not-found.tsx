import Link from "next/link";


export default function TeamNotFound() {

  return (
    <section
      aria-labelledby="unknown-team-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-8
        shadow-sm
        sm:px-7
      "
      data-fixtureiq-component="team-not-found"
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
        id="unknown-team-heading"
        className="
          mt-2 text-2xl font-bold
          tracking-tight
          text-slate-950
          sm:text-3xl
        "
      >
        Team not found
      </h1>

      <p
        className="
          mt-4 max-w-2xl
          text-sm leading-6
          text-slate-600
        "
      >
        FixtureIQ does not have current
        team intelligence for this team.
      </p>

      <Link
        href="/"
        className="
          mt-6 inline-flex
          text-sm font-semibold
          text-slate-950
          underline
          underline-offset-4
        "
      >
        Back to upcoming matches
      </Link>
    </section>
  );
}

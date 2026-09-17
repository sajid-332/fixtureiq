import Link from "next/link";


export function SiteHeader() {
  return (
    <header
      className="
        border-b border-slate-200
        bg-white
      "
      data-fixtureiq-shell="header"
    >
      <div
        className="
          mx-auto flex min-h-16 w-full
          max-w-7xl items-center
          justify-between gap-4
          px-4 sm:px-6 lg:px-8
        "
      >
        <Link
          href="/"
          aria-label="FixtureIQ home"
          className="
            flex min-w-0 items-center
            gap-3 font-semibold
            tracking-tight text-slate-950
          "
        >
          <span>
            FixtureIQ
          </span>

          <span
            className="
              hidden text-xs font-medium
              text-slate-500 sm:inline
            "
          >
            Premier League Intelligence
          </span>
        </Link>

        <nav
          aria-label="Primary navigation"
        >
          <Link
            href="/"
            className="
              inline-flex min-h-10
              items-center rounded-md
              px-3 text-sm font-medium
              text-slate-700
              transition-colors
              hover:bg-slate-100
              hover:text-slate-950
              focus-visible:outline-none
              focus-visible:ring-2
              focus-visible:ring-slate-400
              focus-visible:ring-offset-2
            "
          >
            Upcoming
          </Link>
        </nav>
      </div>
    </header>
  );
}

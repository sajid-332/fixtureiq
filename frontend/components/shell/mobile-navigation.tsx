import Link from "next/link";


export function MobileNavigation() {
  return (
    <nav
      aria-label="Mobile navigation"
      className="sm:hidden"
      data-fixtureiq-shell="mobile-navigation"
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
  );
}

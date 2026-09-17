export function SiteFooter() {
  return (
    <footer
      className="
        border-t border-slate-200
        bg-white
      "
      data-fixtureiq-shell="footer"
    >
      <div
        className="
          mx-auto flex w-full max-w-7xl
          flex-col gap-3 px-4 py-6
          sm:px-6
          md:flex-row
          md:items-center
          md:justify-between
          lg:px-8
        "
      >
        <div>
          <p
            className="
              text-sm font-semibold
              text-slate-900
            "
          >
            FixtureIQ
          </p>

          <p
            className="
              mt-1 text-sm
              text-slate-500
            "
          >
            Premier League match intelligence
          </p>
        </div>

        <p
          className="
            max-w-xl text-sm
            leading-6 text-slate-500
            md:text-right
          "
        >
          Predictions are estimates,
          not guaranteed outcomes.
        </p>
      </div>
    </footer>
  );
}

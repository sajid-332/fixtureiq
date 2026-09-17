from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FRONTEND = ROOT / "frontend"
APP_ROOT = FRONTEND / "app"

DOCS = ROOT / "docs" / "stage10"

FRONTEND_DATA = (
    ROOT
    / "data"
    / "processed"
    / "frontend"
)


PREVIOUS_VERIFICATION_FILE = (
    FRONTEND_DATA
    / "stage10_4_1_10_4_2_verification.json"
)

BASE_CARD_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_base_contract.json"
)

LOADER_CONTRACT_FILE = (
    DOCS
    / "frontend_upcoming_dashboard_loader_contract.json"
)

MATCH_CARD_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-card.tsx"
)

LOADER_FILE = (
    FRONTEND
    / "lib"
    / "dashboard"
    / "load-upcoming-matches.ts"
)

FORMATTER_FILE = (
    FRONTEND
    / "lib"
    / "formatters"
    / "kickoff.ts"
)

IDENTITY_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_identity_contract.json"
)

KICKOFF_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_kickoff_contract.json"
)


IDENTITY_SOURCE = '''import type {
  ReactNode,
} from "react";


type MatchCardProps =
  Readonly<{
    homeTeamName: string;
    awayTeamName: string;
    children?: ReactNode;
  }>;


export function MatchCard({
  homeTeamName,
  awayTeamName,
  children,
}: MatchCardProps) {
  return (
    <article
      aria-label={`${homeTeamName} vs ${awayTeamName}`}
      className="
        overflow-hidden rounded-xl
        border border-slate-200
        bg-white shadow-sm
      "
      data-fixtureiq-component="match-card"
    >
      <header
        className="
          border-b border-slate-100
          px-5 py-5
          sm:px-6
        "
      >
        <div
          className="
            grid
            grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]
            items-center gap-3
          "
        >
          <div className="min-w-0">
            <p
              className="
                text-xs font-medium uppercase
                tracking-wide text-slate-500
              "
            >
              Home
            </p>

            <h2
              className="
                mt-1 break-words
                text-base font-semibold
                text-slate-950
              "
            >
              {homeTeamName}
            </h2>
          </div>

          <span
            aria-hidden="true"
            className="
              text-sm font-medium
              text-slate-400
            "
          >
            vs
          </span>

          <div className="min-w-0 text-right">
            <p
              className="
                text-xs font-medium uppercase
                tracking-wide text-slate-500
              "
            >
              Away
            </p>

            <h2
              className="
                mt-1 break-words
                text-base font-semibold
                text-slate-950
              "
            >
              {awayTeamName}
            </h2>
          </div>
        </div>
      </header>

      {children ? (
        <div className="px-5 py-5 sm:px-6">
          {children}
        </div>
      ) : null}
    </article>
  );
}
'''


FORMATTER_SOURCE = '''const kickoffFormatter =
  new Intl.DateTimeFormat(
    "en-GB",
    {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "UTC",
    },
  );


export function formatKickoffUtc(
  value: string,
): string {
  const kickoff =
    new Date(value);

  if (
    Number.isNaN(
      kickoff.getTime(),
    )
  ) {
    throw new RangeError(
      "Invalid kickoff timestamp.",
    );
  }

  return kickoffFormatter.format(
    kickoff,
  );
}
'''


KICKOFF_SOURCE = '''import type {
  ReactNode,
} from "react";

import {
  formatKickoffUtc,
} from "../../lib/formatters/kickoff";


type MatchCardProps =
  Readonly<{
    homeTeamName: string;
    awayTeamName: string;
    kickoffUtc: string;
    children?: ReactNode;
  }>;


export function MatchCard({
  homeTeamName,
  awayTeamName,
  kickoffUtc,
  children,
}: MatchCardProps) {
  const kickoffLabel =
    formatKickoffUtc(
      kickoffUtc,
    );

  return (
    <article
      aria-label={`${homeTeamName} vs ${awayTeamName}`}
      className="
        overflow-hidden rounded-xl
        border border-slate-200
        bg-white shadow-sm
      "
      data-fixtureiq-component="match-card"
    >
      <header
        className="
          border-b border-slate-100
          px-5 py-5
          sm:px-6
        "
      >
        <div
          className="
            grid
            grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]
            items-center gap-3
          "
        >
          <div className="min-w-0">
            <p
              className="
                text-xs font-medium uppercase
                tracking-wide text-slate-500
              "
            >
              Home
            </p>

            <h2
              className="
                mt-1 break-words
                text-base font-semibold
                text-slate-950
              "
            >
              {homeTeamName}
            </h2>
          </div>

          <span
            aria-hidden="true"
            className="
              text-sm font-medium
              text-slate-400
            "
          >
            vs
          </span>

          <div className="min-w-0 text-right">
            <p
              className="
                text-xs font-medium uppercase
                tracking-wide text-slate-500
              "
            >
              Away
            </p>

            <h2
              className="
                mt-1 break-words
                text-base font-semibold
                text-slate-950
              "
            >
              {awayTeamName}
            </h2>
          </div>
        </div>

        <div
          className="
            mt-4 flex items-center
            justify-center
            text-sm text-slate-600
          "
        >
          <span className="sr-only">
            Kickoff:
          </span>

          <time dateTime={kickoffUtc}>
            {kickoffLabel} UTC
          </time>
        </div>
      </header>

      {children ? (
        <div className="px-5 py-5 sm:px-6">
          {children}
        </div>
      ) : null}
    </article>
  );
}
'''


def load_json(
    path: Path,
) -> dict:

    if not path.exists():
        raise RuntimeError(
            f"Missing artifact: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        payload = json.load(file)

    if not isinstance(
        payload,
        dict,
    ):
        raise RuntimeError(
            f"Expected JSON object: {path}"
        )

    return payload


def optional_json(
    path: Path,
) -> dict | None:

    if not path.exists():
        return None

    return load_json(path)


def sha256_file(
    path: Path,
) -> str:

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda:
                file.read(
                    1024 * 1024
                ),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def relative(
    path: Path,
) -> str:

    return (
        str(
            path.resolve()
            .relative_to(
                ROOT.resolve()
            )
        )
        .replace("\\", "/")
    )


def identity(
    path: Path,
) -> dict:

    return {
        "sha256":
            sha256_file(path)
    }


def save_text_atomic(
    path: Path,
    text: str,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = (
        path.with_suffix(
            path.suffix + ".tmp"
        )
    )

    temporary.write_text(
        text,
        encoding="utf-8",
    )

    temporary.replace(path)


def save_json_atomic(
    path: Path,
    payload: dict,
) -> None:

    save_text_atomic(
        path,
        json.dumps(
            payload,
            indent=2,
        )
        +
        "\n",
    )


def current_route_pages() -> dict:

    output = {}

    for path in sorted(
        APP_ROOT.rglob(
            "page.tsx"
        )
    ):
        output[
            relative(path)
        ] = {
            "sha256":
                sha256_file(path)
        }

    return output


def main() -> None:

    print("=" * 72)
    print(
        "FixtureIQ Stage 10.4.3 + 10.4.4"
    )
    print(
        "MATCH IDENTITY + KICKOFF BUILD"
    )
    print("=" * 72)


    previous = load_json(
        PREVIOUS_VERIFICATION_FILE
    )

    base_card = load_json(
        BASE_CARD_CONTRACT_FILE
    )

    loader_contract = load_json(
        LOADER_CONTRACT_FILE
    )


    if previous.get(
        "status"
    ) != "PASS":
        raise RuntimeError(
            "10.4.1/10.4.2 verification is not PASS."
        )


    if previous.get(
        "stage10_ready_for_10_4_3"
    ) is not True:
        raise RuntimeError(
            "10.4.2 did not authorize 10.4.3."
        )


    for path in [
        MATCH_CARD_FILE,
        LOADER_FILE,
    ]:
        if not path.exists():
            raise RuntimeError(
                f"Missing source: {path}"
            )


    expected_pages = (
        base_card
        .get(
            "protected_state",
            {}
        )
        .get(
            "route_page_identity",
            {},
        )
    )


    if (
        not isinstance(
            expected_pages,
            dict,
        )
        or
        not expected_pages
    ):
        raise RuntimeError(
            "Protected route identity missing."
        )


    if (
        current_route_pages()
        !=
        expected_pages
    ):
        raise RuntimeError(
            "Route pages changed after 10.4.2."
        )


    if (
        sha256_file(
            LOADER_FILE
        )
        !=
        loader_contract.get(
            "source_sha256"
        )
    ):
        raise RuntimeError(
            "Dashboard loader changed after 10.4.1."
        )


    existing_identity = (
        optional_json(
            IDENTITY_CONTRACT_FILE
        )
    )

    existing_kickoff = (
        optional_json(
            KICKOFF_CONTRACT_FILE
        )
    )


    # --------------------------------------------------------
    # Already fully built
    # --------------------------------------------------------

    if (
        existing_kickoff
        and
        FORMATTER_FILE.exists()
        and
        sha256_file(
            MATCH_CARD_FILE
        )
        ==
        existing_kickoff.get(
            "match_card_after_kickoff_sha256"
        )
        and
        sha256_file(
            FORMATTER_FILE
        )
        ==
        existing_kickoff.get(
            "formatter_sha256"
        )
    ):

        print()
        print(
            "10.4.3 / 10.4.4 already built."
        )

        print("=" * 72)
        print(
            "STAGE 10.4.3 MATCH IDENTITY: BUILT"
        )
        print(
            "STAGE 10.4.4 KICKOFF: BUILT"
        )
        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )
        print("=" * 72)

        return


    # ========================================================
    # Stage 10.4.3
    # ========================================================

    current_card_sha = (
        sha256_file(
            MATCH_CARD_FILE
        )
    )

    base_card_sha = (
        base_card.get(
            "source_sha256"
        )
    )


    if (
        existing_identity
        and
        current_card_sha
        ==
        existing_identity.get(
            "match_card_after_identity_sha256"
        )
    ):

        identity_contract = (
            existing_identity
        )

        print()
        print(
            "10.4.3 identity already built."
        )

    else:

        if (
            current_card_sha
            !=
            base_card_sha
        ):
            raise RuntimeError(
                (
                    "MatchCard no longer matches "
                    "the verified 10.4.2 base."
                )
            )


        before_identity_sha = (
            current_card_sha
        )


        save_text_atomic(
            MATCH_CARD_FILE,
            IDENTITY_SOURCE,
        )


        after_identity_sha = (
            sha256_file(
                MATCH_CARD_FILE
            )
        )


        identity_contract = {
            "stage":
                "10.4.3",

            "version":
                "1.0.0",

            "name":
                "MATCH_IDENTITY",

            "status":
                "LOCKED",

            "source":
                relative(
                    MATCH_CARD_FILE
                ),

            "component":
                "MatchCard",

            "identity_fields": [
                "homeTeamName",
                "awayTeamName",
            ],

            "presentation": {
                "home_label":
                    "Home",

                "away_label":
                    "Away",

                "versus_marker":
                    "vs",

                "semantic_team_heading":
                    "h2",

                "accessible_match_label":
                    True,
            },

            "implementation": {
                "server_component":
                    True,

                "presentation_only":
                    True,

                "api_access":
                    False,

                "probability_logic":
                    False,

                "prediction_logic":
                    False,

                "detail_links":
                    False,
            },

            "transition": {
                "match_card_before_identity_sha256":
                    before_identity_sha,

                "match_card_after_identity_sha256":
                    after_identity_sha,
            },

            "match_card_after_identity_sha256":
                after_identity_sha,

            "protected_state": {
                "route_page_identity":
                    expected_pages,

                "loader_sha256":
                    sha256_file(
                        LOADER_FILE
                    ),
            },

            "dependency_identity": {
                relative(
                    PREVIOUS_VERIFICATION_FILE
                ):
                    identity(
                        PREVIOUS_VERIFICATION_FILE
                    ),

                relative(
                    BASE_CARD_CONTRACT_FILE
                ):
                    identity(
                        BASE_CARD_CONTRACT_FILE
                    ),

                relative(
                    LOADER_FILE
                ):
                    identity(
                        LOADER_FILE
                    ),
            },

            "promotion": {
                "stage10_4_3_complete":
                    False,

                "stage10_4_complete":
                    False,

                "stage10_complete":
                    False,
            },

            "generated_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),
        }


        save_json_atomic(
            IDENTITY_CONTRACT_FILE,
            identity_contract,
        )


    # ========================================================
    # Stage 10.4.4
    # ========================================================

    expected_identity_sha = (
        identity_contract.get(
            "match_card_after_identity_sha256"
        )
    )


    if (
        sha256_file(
            MATCH_CARD_FILE
        )
        !=
        expected_identity_sha
    ):
        raise RuntimeError(
            "10.4.3 MatchCard identity SHA mismatch."
        )


    before_kickoff_sha = (
        sha256_file(
            MATCH_CARD_FILE
        )
    )


    save_text_atomic(
        FORMATTER_FILE,
        FORMATTER_SOURCE,
    )


    save_text_atomic(
        MATCH_CARD_FILE,
        KICKOFF_SOURCE,
    )


    after_kickoff_sha = (
        sha256_file(
            MATCH_CARD_FILE
        )
    )


    kickoff_contract = {
        "stage":
            "10.4.4",

        "version":
            "1.0.0",

        "name":
            "MATCH_KICKOFF",

        "status":
            "LOCKED",

        "source":
            relative(
                MATCH_CARD_FILE
            ),

        "formatter_source":
            relative(
                FORMATTER_FILE
            ),

        "kickoff_field":
            "kickoffUtc",

        "presentation": {
            "semantic_time_element":
                True,

            "date_time_attribute":
                True,

            "display_timezone":
                "UTC",

            "locale":
                "en-GB",

            "formatter":
                "Intl.DateTimeFormat",

            "manual_date_formatting":
                False,
        },

        "validation": {
            "invalid_timestamp":
                "THROW_RANGE_ERROR",

            "fallback_timestamp":
                False,

            "invented_timestamp":
                False,
        },

        "implementation": {
            "server_component":
                True,

            "client_timezone_detection":
                False,

            "api_access":
                False,

            "provider_access":
                False,

            "artifact_access":
                False,

            "prediction_logic":
                False,
        },

        "transition": {
            "match_card_before_kickoff_sha256":
                before_kickoff_sha,

            "match_card_after_kickoff_sha256":
                after_kickoff_sha,
        },

        "match_card_after_kickoff_sha256":
            after_kickoff_sha,

        "formatter_sha256":
            sha256_file(
                FORMATTER_FILE
            ),

        "protected_state": {
            "route_page_identity":
                expected_pages,

            "loader_sha256":
                sha256_file(
                    LOADER_FILE
                ),
        },

        "dependency_identity": {
            relative(
                PREVIOUS_VERIFICATION_FILE
            ):
                identity(
                    PREVIOUS_VERIFICATION_FILE
                ),

            relative(
                IDENTITY_CONTRACT_FILE
            ):
                identity(
                    IDENTITY_CONTRACT_FILE
                ),

            relative(
                LOADER_FILE
            ):
                identity(
                    LOADER_FILE
                ),
        },

        "promotion": {
            "stage10_4_4_complete":
                False,

            "stage10_4_complete":
                False,

            "stage10_complete":
                False,
        },

        "generated_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }


    save_json_atomic(
        KICKOFF_CONTRACT_FILE,
        kickoff_contract,
    )


    # ========================================================
    # Final protections
    # ========================================================

    if (
        current_route_pages()
        !=
        expected_pages
    ):
        raise RuntimeError(
            (
                "Route pages changed during "
                "10.4.3/10.4.4."
            )
        )


    if (
        sha256_file(
            LOADER_FILE
        )
        !=
        loader_contract.get(
            "source_sha256"
        )
    ):
        raise RuntimeError(
            (
                "Dashboard loader changed during "
                "10.4.3/10.4.4."
            )
        )


    print()
    print(
        "MatchCard identity + kickoff:"
    )
    print(
        f"  {relative(MATCH_CARD_FILE)}"
    )

    print()
    print(
        "Kickoff formatter:"
    )
    print(
        f"  {relative(FORMATTER_FILE)}"
    )

    print()
    print(
        "Dashboard route pages remain unchanged."
    )

    print()

    print("=" * 72)

    print(
        "STAGE 10.4.3 MATCH IDENTITY: BUILT"
    )

    print(
        "STAGE 10.4.4 KICKOFF: BUILT"
    )

    print(
        "STAGE 10 IS NOT YET PROMOTED"
    )

    print("=" * 72)


if __name__ == "__main__":
    main()
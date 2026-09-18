from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"

DOCS = ROOT / "docs" / "stage10"

FRONTEND_DATA = (
    ROOT
    / "data"
    / "processed"
    / "frontend"
)


PREVIOUS_FILE = (
    FRONTEND_DATA
    / "stage10_6_5_10_6_8_verification.json"
)

FIXTURE_LINKS_CONTRACT_FILE = (
    DOCS
    / "frontend_team_fixture_links_contract.json"
)

UNKNOWN_TEAM_CONTRACT_FILE = (
    DOCS
    / "frontend_team_unknown_team_contract.json"
)


TEAM_ROUTE_FILE = (
    FRONTEND
    / "app"
    / "teams"
    / "[teamName]"
    / "page.tsx"
)

TEAM_NOT_FOUND_FILE = (
    FRONTEND
    / "app"
    / "teams"
    / "[teamName]"
    / "not-found.tsx"
)


TEAM_LOADER_FILE = (
    FRONTEND
    / "lib"
    / "teams"
    / "load-team-intelligence.ts"
)

TEAM_CONTEXT_LOADER_FILE = (
    FRONTEND
    / "lib"
    / "teams"
    / "load-team-context.ts"
)

TEAM_RECORDS_FILE = (
    FRONTEND
    / "lib"
    / "teams"
    / "team-records.ts"
)

TEAM_CONTEXT_RECORDS_FILE = (
    FRONTEND
    / "lib"
    / "teams"
    / "team-context-records.ts"
)


TEAM_HEADER_FILE = (
    FRONTEND
    / "components"
    / "teams"
    / "team-identity-header.tsx"
)

TEAM_UPCOMING_FILE = (
    FRONTEND
    / "components"
    / "teams"
    / "team-upcoming-matches.tsx"
)

TEAM_PREDICTION_CARD_FILE = (
    FRONTEND
    / "components"
    / "teams"
    / "team-prediction-card.tsx"
)

TEAM_STANDINGS_FILE = (
    FRONTEND
    / "components"
    / "teams"
    / "team-standings.tsx"
)

TEAM_RECENT_FORM_FILE = (
    FRONTEND
    / "components"
    / "teams"
    / "team-recent-form.tsx"
)

TEAM_VENUE_FORM_FILE = (
    FRONTEND
    / "components"
    / "teams"
    / "team-home-away-form.tsx"
)


MAPPED_API_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "mapped.ts"
)

RESULT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "result.ts"
)

DOMAIN_TYPES_FILE = (
    FRONTEND
    / "lib"
    / "domain"
    / "types.ts"
)


NOT_FOUND_SOURCE = '''import Link from "next/link";


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

        payload = json.load(
            file
        )

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

    return load_json(
        path
    )


def sha256_file(
    path: Path,
) -> str:

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as file:

        for chunk in iter(
            lambda:
                file.read(
                    1024 * 1024
                ),
            b"",
        ):

            digest.update(
                chunk
            )

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
        .replace(
            "\\",
            "/",
        )
    )


def identity(
    path: Path,
) -> dict:

    return {
        "sha256":
            sha256_file(
                path
            )
    }


def save_text_atomic(
    path: Path,
    text: str,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        text,
        encoding="utf-8",
    )

    temporary.replace(
        path
    )


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


def protected_state() -> dict:

    paths = {
        "team_route_sha256":
            TEAM_ROUTE_FILE,

        "team_loader_sha256":
            TEAM_LOADER_FILE,

        "team_context_loader_sha256":
            TEAM_CONTEXT_LOADER_FILE,

        "team_records_sha256":
            TEAM_RECORDS_FILE,

        "team_context_records_sha256":
            TEAM_CONTEXT_RECORDS_FILE,

        "team_header_sha256":
            TEAM_HEADER_FILE,

        "team_upcoming_sha256":
            TEAM_UPCOMING_FILE,

        "team_prediction_card_sha256":
            TEAM_PREDICTION_CARD_FILE,

        "team_standings_sha256":
            TEAM_STANDINGS_FILE,

        "team_recent_form_sha256":
            TEAM_RECENT_FORM_FILE,

        "team_home_away_form_sha256":
            TEAM_VENUE_FORM_FILE,

        "mapped_api_sha256":
            MAPPED_API_FILE,

        "result_mapping_sha256":
            RESULT_FILE,

        "domain_types_sha256":
            DOMAIN_TYPES_FILE,
    }


    return {
        key:
            sha256_file(
                path
            )

        for key, path
        in paths.items()
    }


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.6.9"
    )

    print(
        "UNKNOWN TEAM HANDLING BUILD"
    )

    print("=" * 72)


    previous = load_json(
        PREVIOUS_FILE
    )

    links_contract = load_json(
        FIXTURE_LINKS_CONTRACT_FILE
    )


    if (
        previous.get(
            "status"
        )
        !=
        "PASS"
    ):

        raise RuntimeError(
            "10.6.5-10.6.8 verification is not PASS."
        )


    for key in [
        "stage_10_6_5_complete",
        "stage_10_6_6_complete",
        "stage_10_6_7_complete",
        "stage_10_6_8_complete",
    ]:

        if (
            previous.get(
                key
            )
            is not True
        ):

            raise RuntimeError(
                f"Previous stage flag incomplete: {key}"
            )


    if (
        previous.get(
            "stage10_ready_for_10_6_9"
        )
        is not True
    ):

        raise RuntimeError(
            "10.6.8 did not authorize 10.6.9."
        )


    required = [
        TEAM_ROUTE_FILE,
        TEAM_LOADER_FILE,
        TEAM_CONTEXT_LOADER_FILE,
        TEAM_RECORDS_FILE,
        TEAM_CONTEXT_RECORDS_FILE,
        TEAM_HEADER_FILE,
        TEAM_UPCOMING_FILE,
        TEAM_PREDICTION_CARD_FILE,
        TEAM_STANDINGS_FILE,
        TEAM_RECENT_FORM_FILE,
        TEAM_VENUE_FORM_FILE,
        MAPPED_API_FILE,
        RESULT_FILE,
        DOMAIN_TYPES_FILE,
    ]


    for path in required:

        if not path.exists():

            raise RuntimeError(
                f"Missing source: {path}"
            )


    expected_route_sha = (
        links_contract.get(
            "route_page_after_10_6_8_sha256"
        )
    )


    if (
        sha256_file(
            TEAM_ROUTE_FILE
        )
        !=
        expected_route_sha
    ):

        raise RuntimeError(
            (
                "Team route no longer matches "
                "verified 10.6.8 output."
            )
        )


    route_source = (
        TEAM_ROUTE_FILE.read_text(
            encoding="utf-8"
        )
    )


    if (
        "notFound();"
        not in
        route_source
        or
        "NOT_FOUND"
        not in
        route_source
    ):

        raise RuntimeError(
            (
                "Team route does not preserve "
                "NOT_FOUND -> notFound() mapping."
            )
        )


    existing = optional_json(
        UNKNOWN_TEAM_CONTRACT_FILE
    )


    if (
        existing
        and
        TEAM_NOT_FOUND_FILE.exists()
        and
        sha256_file(
            TEAM_NOT_FOUND_FILE
        )
        ==
        existing.get(
            "not_found_page_sha256"
        )
        and
        sha256_file(
            TEAM_ROUTE_FILE
        )
        ==
        existing.get(
            "team_route_sha256"
        )
    ):

        print()

        print(
            "10.6.9 already built."
        )

        print("=" * 72)

        print(
            "STAGE 10.6.9 UNKNOWN TEAM: BUILT"
        )

        print(
            "FINAL 10.6.10 VERIFICATION STILL REQUIRED"
        )

        print("=" * 72)

        return


    if (
        TEAM_NOT_FOUND_FILE.exists()
    ):

        raise RuntimeError(
            (
                "Team not-found page already exists "
                "without matching 10.6.9 contract. "
                "Refusing to overwrite it."
            )
        )


    protected = protected_state()


    save_text_atomic(
        TEAM_NOT_FOUND_FILE,
        NOT_FOUND_SOURCE,
    )


    contract = {
        "stage":
            "10.6.9",

        "version":
            "1.0.0",

        "name":
            "TEAM_UNKNOWN_TEAM_HANDLING",

        "status":
            "LOCKED",

        "route":
            "/teams/[teamName]",

        "not_found_source":
            relative(
                TEAM_NOT_FOUND_FILE
            ),

        "authority": {
            "team_intelligence_404":
                "STAGE_9_INTELLIGENCE_API",

            "standings_404":
                "STAGE_8_CONTEXT_API",

            "form_404":
                "STAGE_8_CONTEXT_API",

            "routing":
                "NEXT_NOT_FOUND",
        },

        "behavior": {
            "not_found_maps_to_404":
                True,

            "route_uses_notFound":
                True,

            "nearest_not_found_boundary":
                True,

            "fuzzy_matching":
                False,

            "team_name_guessing":
                False,

            "automatic_redirect":
                False,

            "suggested_team_substitution":
                False,

            "stale_fallback":
                False,

            "direct_fetch":
                False,

            "provider_access":
                False,

            "artifact_access":
                False,
        },

        "navigation": {
            "back_to_upcoming_matches":
                True,

            "target":
                "/",
        },

        "team_route_sha256":
            sha256_file(
                TEAM_ROUTE_FILE
            ),

        "not_found_page_sha256":
            sha256_file(
                TEAM_NOT_FOUND_FILE
            ),

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                PREVIOUS_FILE
            ):
                identity(
                    PREVIOUS_FILE
                ),

            relative(
                FIXTURE_LINKS_CONTRACT_FILE
            ):
                identity(
                    FIXTURE_LINKS_CONTRACT_FILE
                ),
        },

        "promotion": {
            "stage10_6_9_complete":
                False,

            "stage10_6_complete":
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
        UNKNOWN_TEAM_CONTRACT_FILE,
        contract,
    )


    print()

    print(
        "Unknown-team boundary:"
    )

    print(
        f"  {relative(TEAM_NOT_FOUND_FILE)}"
    )

    print()

    print("=" * 72)

    print(
        "STAGE 10.6.9 UNKNOWN TEAM: BUILT"
    )

    print(
        "FINAL 10.6.10 VERIFICATION STILL REQUIRED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
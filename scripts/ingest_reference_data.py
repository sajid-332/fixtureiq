"""
FixtureIQ Stage 7.2.2
Team & League Reference Data Ingestion

Usage:

    python scripts/ingest_reference_data.py

For explicit testing with an accessible season:

    python scripts/ingest_reference_data.py --season 2024

The season override only affects the current execution.
It does NOT modify .env or backend.config.
"""

import argparse
import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(BASE_DIR))


from backend.config import (
    API_FOOTBALL_LEAGUE_ID,
    API_FOOTBALL_SEASON,
    get_config_summary,
    validate_config,
)

from backend.providers.api_football import (
    APIFootballProvider,
    APIFootballError,
)

from backend.providers.cache import (
    cache_exists,
    get_cache_path,
)


def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "FixtureIQ team and league "
            "reference-data ingestion"
        )
    )

    parser.add_argument(
        "--season",
        type=int,
        default=None,
        help=(
            "Override configured season "
            "for this execution only."
        ),
    )

    return parser.parse_args()


def print_errors(
    label,
    payload,
):

    errors = payload.get(
        "errors",
        {},
    )

    if errors:

        print(
            f"\n{label} API errors:"
        )

        print(
            json.dumps(
                errors,
                indent=2,
                ensure_ascii=False,
            )
        )


def has_plan_error(
    payload,
):

    errors = payload.get(
        "errors",
        {},
    )

    return (
        isinstance(
            errors,
            dict,
        )
        and
        bool(
            errors.get("plan")
        )
    )


def main():

    args = parse_args()

    print("=" * 50)
    print("FixtureIQ Stage 7.2.2")
    print("Team & League Data Ingestion")
    print("=" * 50)

    # --------------------------------------------------------
    # Configuration
    # --------------------------------------------------------

    print(
        "\nConfiguration"
    )

    try:

        validate_config()

    except Exception as exc:

        print(
            "Configuration                 FAIL"
        )

        print(
            f"\nError: {exc}"
        )

        sys.exit(1)

    summary = get_config_summary()

    configured_season = (
        API_FOOTBALL_SEASON
    )

    season = (
        args.season
        if args.season is not None
        else configured_season
    )

    print(
        f"{'Provider':<30}"
        f"{summary['api_provider']}"
    )

    print(
        f"{'League ID':<30}"
        f"{API_FOOTBALL_LEAGUE_ID}"
    )

    print(
        f"{'Configured season':<30}"
        f"{configured_season}"
    )

    print(
        f"{'Active test season':<30}"
        f"{season}"
    )

    print(
        f"{'API key configured':<30}"
        f"{summary['api_key_configured']}"
    )

    if args.season is not None:

        print(
            "\nSeason override:"
        )

        print(
            f"Using season {season} "
            "for this execution only."
        )

        print(
            "Project configuration remains "
            f"{configured_season}."
        )

    provider = APIFootballProvider()

    # ========================================================
    # TEAM INGESTION
    # ========================================================

    print(
        "\n" + "-" * 50
    )

    print(
        "TEAM DATA INGESTION"
    )

    print(
        "-" * 50
    )

    try:

        team_payload = provider.get_teams(
            API_FOOTBALL_LEAGUE_ID,
            season,
        )

    except APIFootballError as exc:

        print(
            "Team ingestion               FAIL"
        )

        print(
            f"\nProvider error: {exc}"
        )

        sys.exit(1)

    team_response = team_payload.get(
        "response",
        [],
    )

    team_errors = team_payload.get(
        "errors",
        {},
    )

    print(
        f"{'Team response':<30}PASS"
    )

    print_errors(
        "Team",
        team_payload,
    )

    print(
        f"{'Teams received':<30}"
        f"{len(team_response)}"
    )

    team_params = {
        "league":
            API_FOOTBALL_LEAGUE_ID,

        "season":
            season,
    }

    team_cache = cache_exists(
        "/teams",
        team_params,
    )

    team_cache_path = get_cache_path(
        "/teams",
        team_params,
    )

    print(
        f"{'Team raw cache':<30}"
        f"{'PASS' if team_cache else 'FAIL'}"
    )

    if team_cache:

        print(
            f"{'Team cache path':<30}"
            f"{team_cache_path}"
        )

    # ========================================================
    # LEAGUE INGESTION
    # ========================================================

    print(
        "\n" + "-" * 50
    )

    print(
        "LEAGUE DATA INGESTION"
    )

    print(
        "-" * 50
    )

    try:

        league_payload = provider.get_leagues(
            API_FOOTBALL_LEAGUE_ID,
            season,
        )

    except APIFootballError as exc:

        print(
            "League ingestion             FAIL"
        )

        print(
            f"\nProvider error: {exc}"
        )

        sys.exit(1)

    league_response = (
        league_payload.get(
            "response",
            [],
        )
    )

    print_errors(
        "League",
        league_payload,
    )

    if has_plan_error(
        league_payload
    ):

        print(
            "League ingestion             "
            "LIMITED_BY_PLAN"
        )

    elif len(league_response) > 0:

        print(
            "League ingestion             PASS"
        )

    else:

        print(
            "League ingestion             NO_DATA"
        )

    print(
        f"{'League records received':<30}"
        f"{len(league_response)}"
    )

    league_params = {
        "id":
            API_FOOTBALL_LEAGUE_ID,

        "season":
            season,
    }

    league_cache = cache_exists(
        "/leagues",
        league_params,
    )

    league_cache_path = get_cache_path(
        "/leagues",
        league_params,
    )

    print(
        f"{'League raw cache':<30}"
        f"{'PASS' if league_cache else 'FAIL'}"
    )

    if league_cache:

        print(
            f"{'League cache path':<30}"
            f"{league_cache_path}"
        )

    # ========================================================
    # FINAL
    # ========================================================

    team_ok = (
        len(team_response) > 0
        and
        team_cache
    )

    league_ok = (
        (
            len(league_response) > 0
            or
            has_plan_error(
                league_payload
            )
        )
        and
        league_cache
    )

    print(
        "\n" + "=" * 50
    )

    print(
        "STAGE 7.2.2 RESULT"
    )

    print(
        "=" * 50
    )

    print(
        "Team ingestion: "
        +
        (
            "PASS"
            if team_ok
            else "FAIL"
        )
    )

    if has_plan_error(
        league_payload
    ):

        print(
            "League ingestion: "
            "PASS WITH PROVIDER LIMITATION"
        )

    else:

        print(
            "League ingestion: "
            +
            (
                "PASS"
                if len(league_response) > 0
                else "FAIL"
            )
        )

    print(
        "Raw caching: "
        +
        (
            "PASS"
            if (
                team_cache
                and
                league_cache
            )
            else "FAIL"
        )
    )

    if team_ok and league_ok:

        print(
            "\nStage 7.2.2: PASS"
        )

    else:

        print(
            "\nStage 7.2.2: FAIL"
        )

        sys.exit(1)


if __name__ == "__main__":
    main()
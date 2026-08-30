"""
FixtureIQ Stage 7.2.1
Fixture Data Ingestion

Fetches fixture data from API-Football.

Usage:

    python scripts/ingest_fixtures.py

For an explicit test-season override:

    python scripts/ingest_fixtures.py --season 2024

The --season argument only affects the current execution.
It does NOT modify backend.config or the .env file.

Production configuration remains unchanged.
"""

import argparse
import json
import sys
from pathlib import Path


# ============================================================
# Project root
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BASE_DIR),
)


# ============================================================
# FixtureIQ imports
# ============================================================

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


# ============================================================
# Command-line arguments
# ============================================================

def parse_args():
    """
    Parse command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description=(
            "FixtureIQ fixture data ingestion"
        )
    )

    parser.add_argument(
        "--season",
        type=int,
        default=None,
        help=(
            "Override the configured season "
            "for this execution only."
        ),
    )

    return parser.parse_args()


# ============================================================
# Utility
# ============================================================

def print_field(
    name: str,
    value,
) -> None:
    """
    Print a consistently formatted field.
    """

    print(
        f"{name:<30}{value}"
    )


def print_api_errors(
    errors,
) -> None:
    """
    Safely print API errors regardless of whether
    the provider returns a dictionary, list, or another
    JSON-compatible structure.
    """

    if not errors:
        return

    print(
        "\nProvider reported errors:"
    )

    print(
        json.dumps(
            errors,
            indent=2,
            ensure_ascii=False,
        )
    )


def has_plan_error(
    errors,
) -> bool:
    """
    Detect an API-Football plan restriction safely.

    API-Football may return:
        {}
    or:
        []
    or:
        {"plan": "..."}
    """

    if not isinstance(
        errors,
        dict,
    ):
        return False

    return bool(
        errors.get("plan")
    )


# ============================================================
# Main
# ============================================================

def main():

    args = parse_args()

    print("=" * 50)
    print(
        "FixtureIQ Stage 7.2.1"
    )
    print(
        "Fixture Data Ingestion"
    )
    print("=" * 50)


    # ========================================================
    # Configuration
    # ========================================================

    print(
        "\nConfiguration"
    )

    try:

        validate_config()

    except Exception as exc:

        print_field(
            "Configuration",
            "FAIL",
        )

        print(
            f"\nError: {exc}"
        )

        sys.exit(1)


    summary = get_config_summary()

    configured_season = (
        API_FOOTBALL_SEASON
    )

    # Explicit test override.
    #
    # If --season is not supplied, the production
    # configuration is used.

    season = (
        args.season
        if args.season is not None
        else configured_season
    )


    print_field(
        "Provider",
        summary["api_provider"],
    )

    print_field(
        "Base URL",
        summary["base_url"],
    )

    print_field(
        "League ID",
        API_FOOTBALL_LEAGUE_ID,
    )

    print_field(
        "Configured season",
        configured_season,
    )

    print_field(
        "Active test season",
        season,
    )

    print_field(
        "API key configured",
        summary["api_key_configured"],
    )


    # ========================================================
    # Explicit season override information
    # ========================================================

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


    # ========================================================
    # Provider
    # ========================================================

    provider = APIFootballProvider()


    # ========================================================
    # Fixture request
    # ========================================================

    print(
        "\nRequesting fixtures..."
    )

    try:

        payload = provider.get_fixtures(
            API_FOOTBALL_LEAGUE_ID,
            season,
        )

    except APIFootballError as exc:

        print(
            "Fixture ingestion            FAIL"
        )

        print(
            f"\nProvider error: {exc}"
        )

        sys.exit(1)


    # ========================================================
    # Validate API response
    # ========================================================

    if not isinstance(
        payload,
        dict,
    ):

        print(
            "API response                FAIL"
        )

        print(
            "\nProvider returned an "
            "unexpected response type."
        )

        sys.exit(1)


    response = payload.get(
        "response",
        [],
    )

    errors = payload.get(
        "errors",
        {},
    )


    if not isinstance(
        response,
        list,
    ):

        print(
            "API response                FAIL"
        )

        print(
            "\nThe 'response' field is not a list."
        )

        sys.exit(1)


    print_field(
        "API response",
        "PASS",
    )


    # ========================================================
    # Provider errors
    # ========================================================

    print_api_errors(
        errors
    )


    # ========================================================
    # Fixture count
    # ========================================================

    fixture_count = len(
        response
    )


    print_field(
        "Fixtures received",
        fixture_count,
    )


    # ========================================================
    # Plan limitation
    # ========================================================

    plan_error = has_plan_error(
        errors
    )


    if plan_error:

        print(
            "\nProvider limitation detected."
        )

        print(
            "The configured production season "
            "was not silently replaced."
        )

        print(
            "The raw provider response has been "
            "cached for diagnostics."
        )


    # ========================================================
    # Raw cache verification
    # ========================================================

    params = {
        "league":
            API_FOOTBALL_LEAGUE_ID,

        "season":
            season,
    }


    cache_path = get_cache_path(
        "/fixtures",
        params,
    )


    cache_created = cache_exists(
        "/fixtures",
        params,
    )


    print(
        "\nRaw cache"
    )


    print_field(
        "Cache created",
        (
            "PASS"
            if cache_created
            else "FAIL"
        ),
    )


    if cache_created:

        print_field(
            "Cache path",
            cache_path,
        )


    # ========================================================
    # Final result
    # ========================================================

    print(
        "\n" + "=" * 50
    )

    print(
        "STAGE 7.2.1 RESULT"
    )

    print(
        "=" * 50
    )


    # --------------------------------------------------------
    # Provider limitation
    # --------------------------------------------------------

    if plan_error:

        print(
            "Fixture ingestion: "
            "PASS WITH PROVIDER LIMITATION"
        )

        print(
            "Raw provider response: CACHED"
        )

        return


    # --------------------------------------------------------
    # No data
    # --------------------------------------------------------

    if fixture_count == 0:

        print(
            "Fixture ingestion: FAIL"
        )

        print(
            "No fixture records were returned."
        )

        sys.exit(1)


    # --------------------------------------------------------
    # Cache failure
    # --------------------------------------------------------

    if not cache_created:

        print(
            "Fixture ingestion: FAIL"
        )

        print(
            "Raw response was not cached."
        )

        sys.exit(1)


    # --------------------------------------------------------
    # Successful ingestion
    # --------------------------------------------------------

    print(
        "Fixture ingestion: PASS"
    )

    print(
        f"Fixtures ingested: {fixture_count}"
    )

    print(
        "Raw response: CACHED"
    )


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":

    main()
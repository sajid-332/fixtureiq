"""
FixtureIQ Stage 7.2.3
Processed Dataset Generation.

Fetches fixtures from API-Football, normalizes and validates
them, then creates/updates the processed fixture dataset.

Usage:

    python scripts/build_processed_dataset.py

Test with an accessible season:

    python scripts/build_processed_dataset.py --season 2024
"""

import argparse
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BASE_DIR),
)


from backend.config import (
    API_FOOTBALL_LEAGUE_ID,
    API_FOOTBALL_SEASON,
    validate_config,
)

from backend.providers.api_football import (
    APIFootballProvider,
    APIFootballError,
)

from backend.providers.processor import (
    FIXTURES_FILE,
    prepare_fixtures,
    update_processed_fixtures,
)


def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "FixtureIQ processed dataset builder"
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


def main():

    args = parse_args()

    print("=" * 50)
    print(
        "FixtureIQ Stage 7.2.3"
    )
    print(
        "Processed Dataset Generation"
    )
    print("=" * 50)

    validate_config()

    configured_season = (
        API_FOOTBALL_SEASON
    )

    season = (
        args.season
        if args.season is not None
        else configured_season
    )

    print(
        f"\nConfigured season: {configured_season}"
    )

    print(
        f"Active test season: {season}"
    )

    if args.season is not None:

        print(
            "Explicit season override active."
        )

    provider = APIFootballProvider()

    print(
        "\nFetching fixtures..."
    )

    try:

        payload = provider.get_fixtures(
            API_FOOTBALL_LEAGUE_ID,
            season,
        )

    except APIFootballError as exc:

        print(
            f"\nProvider error: {exc}"
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

    if (
        isinstance(
            errors,
            dict,
        )
        and
        errors.get("plan")
    ):

        print(
            "\nProvider limitation:"
        )

        print(
            errors["plan"]
        )

        print(
            "\nNo processed dataset was "
            "generated from unavailable data."
        )

        sys.exit(1)

    if not isinstance(
        response,
        list,
    ):

        print(
            "\nInvalid API response."
        )

        sys.exit(1)

    if not response:

        print(
            "\nNo fixture records received."
        )

        sys.exit(1)

    print(
        f"Raw fixtures received: "
        f"{len(response)}"
    )

    dataframe = prepare_fixtures(
        payload
    )

    print(
        f"Valid processed fixtures: "
        f"{len(dataframe)}"
    )

    if dataframe.empty:

        print(
            "\nNo valid fixtures remain "
            "after processing."
        )

        sys.exit(1)

    statistics = update_processed_fixtures(
        dataframe
    )

    print(
        "\nDataset update"
    )

    print(
        f"Existing records: "
        f"{statistics['existing_count']}"
    )

    print(
        f"Incoming records: "
        f"{statistics['incoming_count']}"
    )

    print(
        f"New records: "
        f"{statistics['new_count']}"
    )

    print(
        f"Updated records: "
        f"{statistics['updated_count']}"
    )

    print(
        f"Final records: "
        f"{statistics['final_count']}"
    )

    print(
        f"Duplicate-free: "
        f"{statistics['duplicate_free']}"
    )

    print(
        "\nProcessed dataset:"
    )

    print(
        FIXTURES_FILE
    )

    print(
        "\nSTAGE 7.2.3: PASS"
    )


if __name__ == "__main__":
    main()
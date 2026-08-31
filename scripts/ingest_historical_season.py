"""
FixtureIQ Stage 7.3.1 - 7.3.2
Historical Season Ingestion.

Usage:

    python scripts/ingest_historical_season.py --season 2024

The season must be supplied explicitly.

The production API_FOOTBALL_SEASON setting is never changed.
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
# Imports
# ============================================================

from backend.config import (
    API_FOOTBALL_LEAGUE_ID,
    API_FOOTBALL_SEASON,
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

from backend.providers.historical import (
    HISTORICAL_FILE,
    prepare_historical_fixtures,
    update_historical_fixtures,
)


# ============================================================
# Arguments
# ============================================================

def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "FixtureIQ historical season ingestion"
        )
    )

    parser.add_argument(
        "--season",
        type=int,
        required=True,
        help=(
            "Historical season to ingest. "
            "Example: 2024"
        ),
    )

    return parser.parse_args()


# ============================================================
# Main
# ============================================================

def main():

    args = parse_args()

    season = args.season

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.3.1 - 7.3.2"
    )

    print(
        "Historical Season Ingestion"
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

        print(
            "Configuration: FAIL"
        )

        print(
            f"Error: {exc}"
        )

        sys.exit(1)


    print(
        f"Provider: API-Football"
    )

    print(
        f"League ID: "
        f"{API_FOOTBALL_LEAGUE_ID}"
    )

    print(
        f"Configured production season: "
        f"{API_FOOTBALL_SEASON}"
    )

    print(
        f"Historical ingestion season: "
        f"{season}"
    )

    print(
        "Production configuration: "
        "UNCHANGED"
    )


    # ========================================================
    # Provider
    # ========================================================

    provider = APIFootballProvider()


    print(
        "\nRequesting historical fixtures..."
    )


    try:

        payload = provider.get_fixtures(
            API_FOOTBALL_LEAGUE_ID,
            season,
        )

    except APIFootballError as exc:

        print(
            "\nProvider error:"
        )

        print(
            str(exc)
        )

        sys.exit(1)


    # ========================================================
    # API response
    # ========================================================

    if not isinstance(
        payload,
        dict,
    ):

        print(
            "\nAPI response: FAIL"
        )

        print(
            "Unexpected provider response."
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


    # --------------------------------------------------------
    # Provider plan restriction
    # --------------------------------------------------------

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
            json.dumps(
                errors,
                indent=2,
                ensure_ascii=False,
            )
        )

        sys.exit(1)


    # --------------------------------------------------------
    # Response validation
    # --------------------------------------------------------

    if not isinstance(
        response,
        list,
    ):

        print(
            "\nAPI response: FAIL"
        )

        print(
            "Response field is not a list."
        )

        sys.exit(1)


    print(
        "API response: PASS"
    )

    print(
        f"Fixtures received: "
        f"{len(response)}"
    )


    if not response:

        print(
            "\nNo fixtures received."
        )

        sys.exit(1)


    # ========================================================
    # Raw cache
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


    cache_pass = cache_exists(
        "/fixtures",
        params,
    )


    print(
        "\nRaw cache"
    )

    print(
        f"Cache created: "
        f"{'PASS' if cache_pass else 'FAIL'}"
    )

    print(
        f"Cache path: "
        f"{cache_path}"
    )


    if not cache_pass:

        print(
            "\nRaw cache verification failed."
        )

        sys.exit(1)


    # ========================================================
    # Normalization + validation
    # ========================================================

    print(
        "\nProcessing historical fixtures..."
    )


    dataframe = prepare_historical_fixtures(
        payload,
        season,
    )


    print(
        f"Valid fixtures: "
        f"{len(dataframe)}"
    )


    if dataframe.empty:

        print(
            "\nHistorical processing: FAIL"
        )

        print(
            "No valid fixtures remained."
        )

        sys.exit(1)


    # ========================================================
    # Historical dataset update
    # ========================================================

    statistics = update_historical_fixtures(
        dataframe
    )


    print(
        "\nHistorical dataset update"
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
        f"Historical seasons: "
        f"{statistics['final_seasons']}"
    )

    print(
        f"Duplicate-free: "
        f"{statistics['duplicate_free']}"
    )


    print(
        "\nHistorical dataset:"
    )

    print(
        HISTORICAL_FILE
    )


    # ========================================================
    # Final result
    # ========================================================

    print(
        "\n" + "=" * 50
    )

    print(
        "STAGE 7.3.1 RESULT"
    )

    print(
        "=" * 50
    )

    print(
        "Historical ingestion: PASS"
    )

    print(
        "Multi-season management: PASS"
    )


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":

    main()
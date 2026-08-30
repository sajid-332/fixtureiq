"""
FixtureIQ Stage 7.2.4
Incremental Processed Dataset Test.

Verifies:
- Dataset creation
- Duplicate prevention
- Repeat ingestion safety
- Stable fixture IDs
- Correct new/updated record accounting
"""

import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BASE_DIR),
)


from backend.config import (
    API_FOOTBALL_LEAGUE_ID,
)

from backend.providers.api_football import (
    APIFootballProvider,
)

from backend.providers.processor import (
    FIXTURES_FILE,
    prepare_fixtures,
    load_processed_fixtures,
    update_processed_fixtures,
)


TEST_SEASON = 2024


def main():

    print("=" * 50)
    print(
        "FixtureIQ Stage 7.2.4"
    )
    print(
        "Incremental Dataset Test"
    )
    print("=" * 50)

    provider = APIFootballProvider()

    print(
        f"\nTest season: {TEST_SEASON}"
    )

    payload = provider.get_fixtures(
        API_FOOTBALL_LEAGUE_ID,
        TEST_SEASON,
    )

    dataframe = prepare_fixtures(
        payload
    )

    if dataframe.empty:

        print(
            "Incoming dataset: FAIL"
        )

        sys.exit(1)

    print(
        f"Incoming fixtures: "
        f"{len(dataframe)}"
    )

    # --------------------------------------------------------
    # First update
    # --------------------------------------------------------

    first = update_processed_fixtures(
        dataframe
    )

    print(
        "\nFirst update"
    )

    print(
        f"New: {first['new_count']}"
    )

    print(
        f"Updated: {first['updated_count']}"
    )

    print(
        f"Final: {first['final_count']}"
    )

    # --------------------------------------------------------
    # Second identical update
    # --------------------------------------------------------

    second = update_processed_fixtures(
        dataframe
    )

    print(
        "\nSecond identical update"
    )

    print(
        f"New: {second['new_count']}"
    )

    print(
        f"Updated: {second['updated_count']}"
    )

    print(
        f"Final: {second['final_count']}"
    )

    # --------------------------------------------------------
    # Load final dataset
    # --------------------------------------------------------

    final_dataset = load_processed_fixtures(
        FIXTURES_FILE
    )

    unique_ids = (
        final_dataset["fixture_id"]
        .nunique()
    )

    total_rows = len(
        final_dataset
    )

    duplicate_free = (
        total_rows
        == unique_ids
    )

    file_exists = (
        FIXTURES_FILE.exists()
    )

    # --------------------------------------------------------
    # Tests
    # --------------------------------------------------------

    first_pass = (
        first["final_count"]
        == len(dataframe)
    )

    second_pass = (
        second["new_count"]
        == 0
        and
        second["final_count"]
        == len(dataframe)
    )

    duplicate_pass = (
        duplicate_free
    )

    file_pass = (
        file_exists
    )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    print(
        "\n" + "=" * 50
    )

    print(
        "FINAL RESULT"
    )

    print(
        "=" * 50
    )

    print(
        "Initial dataset creation: "
        +
        (
            "PASS"
            if first_pass
            else "FAIL"
        )
    )

    print(
        "Repeated ingestion safety: "
        +
        (
            "PASS"
            if second_pass
            else "FAIL"
        )
    )

    print(
        "Duplicate prevention: "
        +
        (
            "PASS"
            if duplicate_pass
            else "FAIL"
        )
    )

    print(
        "Processed file exists: "
        +
        (
            "PASS"
            if file_pass
            else "FAIL"
        )
    )

    if (
        first_pass
        and
        second_pass
        and
        duplicate_pass
        and
        file_pass
    ):

        print(
            "\nStage 7.2.4: PASS"
        )

    else:

        print(
            "\nStage 7.2.4: FAIL"
        )

        sys.exit(1)


if __name__ == "__main__":
    main()
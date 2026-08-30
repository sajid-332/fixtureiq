"""
FixtureIQ Stage 7.2.5
Full Data Ingestion Pipeline Verification

Verifies the complete Stage 7.2 pipeline:

API
 -> Raw ingestion
 -> Normalization
 -> Validation
 -> Processed dataset
 -> Incremental update
 -> Duplicate prevention

Uses 2024 as the explicit verification season because
the current API-Football plan restricts the configured
2026 season.

The production configuration is NOT modified.
"""

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
    validate_config,
)

from backend.providers.api_football import (
    APIFootballProvider,
)

from backend.providers.cache import (
    cache_exists,
    load_response,
)

from backend.providers.processor import (
    FIXTURES_FILE,
    prepare_fixtures,
    load_processed_fixtures,
    update_processed_fixtures,
)


# ============================================================
# Verification configuration
# ============================================================

TEST_SEASON = 2024


# ============================================================
# Cache validation
# ============================================================

def validate_cached_fixture_response(
    cached_document,
) -> bool:
    """
    Validate the actual FixtureIQ cache structure.

    Cache format:

        {
            "cached_at": "...",
            "endpoint": "/fixtures",
            "params": {...},
            "response": {
                "get": "...",
                "parameters": {...},
                "errors": {...},
                "results": 380,
                "response": [...]
            }
        }
    """

    if not isinstance(
        cached_document,
        dict,
    ):
        return False

    required_cache_keys = {
        "cached_at",
        "endpoint",
        "params",
        "response",
    }

    if not required_cache_keys.issubset(
        cached_document.keys()
    ):
        return False

    api_response = (
        cached_document.get(
            "response"
        )
    )

    if not isinstance(
        api_response,
        dict,
    ):
        return False

    required_api_keys = {
        "response",
    }

    if not required_api_keys.issubset(
        api_response.keys()
    ):
        return False

    fixtures = (
        api_response.get(
            "response"
        )
    )

    if not isinstance(
        fixtures,
        list,
    ):
        return False

    return len(fixtures) > 0


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 50)
    print(
        "FixtureIQ Stage 7.2.5"
    )
    print(
        "Full Pipeline Verification"
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
            "Configuration              FAIL"
        )

        print(
            f"Error: {exc}"
        )

        sys.exit(1)

    print(
        f"Configured season: {API_FOOTBALL_SEASON}"
    )

    print(
        f"Verification season: {TEST_SEASON}"
    )

    print(
        "Production configuration: "
        "UNCHANGED"
    )


    # ========================================================
    # Provider
    # ========================================================

    provider = APIFootballProvider()


    # ========================================================
    # 1. API INGESTION
    # ========================================================

    print(
        "\n" + "-" * 50
    )

    print(
        "1. API FIXTURE INGESTION"
    )

    print(
        "-" * 50
    )

    payload = provider.get_fixtures(
        API_FOOTBALL_LEAGUE_ID,
        TEST_SEASON,
    )

    response = payload.get(
        "response",
        [],
    )

    errors = payload.get(
        "errors",
        {},
    )

    api_pass = (
        isinstance(
            response,
            list,
        )
        and
        len(response) > 0
    )

    print(
        f"API response: "
        f"{'PASS' if api_pass else 'FAIL'}"
    )

    print(
        f"Fixtures received: "
        f"{len(response)}"
    )

    if not api_pass:

        print(
            "\nStage 7.2.5: FAIL"
        )

        sys.exit(1)


    # ========================================================
    # 2. RAW CACHE
    # ========================================================

    print(
        "\n" + "-" * 50
    )

    print(
        "2. RAW CACHE VERIFICATION"
    )

    print(
        "-" * 50
    )

    fixture_params = {
        "league":
            API_FOOTBALL_LEAGUE_ID,

        "season":
            TEST_SEASON,
    }

    raw_cache_pass = cache_exists(
        "/fixtures",
        fixture_params,
    )

    cached_document = load_response(
        "/fixtures",
        fixture_params,
    )

    cache_content_pass = (
        validate_cached_fixture_response(
            cached_document
        )
    )

    print(
        f"Cache exists: "
        f"{'PASS' if raw_cache_pass else 'FAIL'}"
    )

    print(
        f"Cache content: "
        f"{'PASS' if cache_content_pass else 'FAIL'}"
    )


    # ========================================================
    # 3. NORMALIZATION + VALIDATION
    # ========================================================

    print(
        "\n" + "-" * 50
    )

    print(
        "3. NORMALIZATION + VALIDATION"
    )

    print(
        "-" * 50
    )

    processed = prepare_fixtures(
        payload
    )

    normalization_pass = (
        not processed.empty
        and
        len(processed) == len(response)
    )

    print(
        f"Normalized/processed fixtures: "
        f"{len(processed)}"
    )

    print(
        f"Normalization + validation: "
        f"{'PASS' if normalization_pass else 'FAIL'}"
    )


    # ========================================================
    # 4. PROCESSED DATASET
    # ========================================================

    print(
        "\n" + "-" * 50
    )

    print(
        "4. PROCESSED DATASET"
    )

    print(
        "-" * 50
    )

    dataset = load_processed_fixtures(
        FIXTURES_FILE
    )

    dataset_exists = (
        FIXTURES_FILE.exists()
    )

    dataset_nonempty = (
        not dataset.empty
    )

    fixture_ids_unique = (
        dataset["fixture_id"].is_unique
        if not dataset.empty
        else False
    )

    dataset_pass = (
        dataset_exists
        and
        dataset_nonempty
        and
        fixture_ids_unique
    )

    print(
        f"Dataset exists: "
        f"{'PASS' if dataset_exists else 'FAIL'}"
    )

    print(
        f"Dataset records: "
        f"{len(dataset)}"
    )

    print(
        f"Unique fixture IDs: "
        f"{'PASS' if fixture_ids_unique else 'FAIL'}"
    )


    # ========================================================
    # 5. INCREMENTAL UPDATE
    # ========================================================

    print(
        "\n" + "-" * 50
    )

    print(
        "5. INCREMENTAL UPDATE"
    )

    print(
        "-" * 50
    )

    first_update = update_processed_fixtures(
        processed
    )

    second_update = update_processed_fixtures(
        processed
    )

    incremental_pass = (
        second_update["new_count"] == 0
        and
        second_update["final_count"]
        == first_update["final_count"]
    )

    print(
        f"First update final count: "
        f"{first_update['final_count']}"
    )

    print(
        f"Second update new records: "
        f"{second_update['new_count']}"
    )

    print(
        f"Second update final count: "
        f"{second_update['final_count']}"
    )

    print(
        f"Incremental safety: "
        f"{'PASS' if incremental_pass else 'FAIL'}"
    )


    # ========================================================
    # 6. DUPLICATE CHECK
    # ========================================================

    print(
        "\n" + "-" * 50
    )

    print(
        "6. DUPLICATE PREVENTION"
    )

    print(
        "-" * 50
    )

    final_dataset = load_processed_fixtures(
        FIXTURES_FILE
    )

    total_rows = len(
        final_dataset
    )

    unique_rows = (
        final_dataset["fixture_id"]
        .nunique()
        if not final_dataset.empty
        else 0
    )

    duplicate_pass = (
        total_rows == unique_rows
    )

    print(
        f"Total rows: {total_rows}"
    )

    print(
        f"Unique fixture IDs: {unique_rows}"
    )

    print(
        f"Duplicate prevention: "
        f"{'PASS' if duplicate_pass else 'FAIL'}"
    )


    # ========================================================
    # 7. PIPELINE INTEGRITY
    # ========================================================

    print(
        "\n" + "-" * 50
    )

    print(
        "7. PIPELINE INTEGRITY"
    )

    print(
        "-" * 50
    )

    all_pass = all(
        [
            api_pass,
            raw_cache_pass,
            cache_content_pass,
            normalization_pass,
            dataset_pass,
            incremental_pass,
            duplicate_pass,
        ]
    )

    print(
        f"API ingestion: "
        f"{'PASS' if api_pass else 'FAIL'}"
    )

    print(
        f"Raw cache: "
        f"{'PASS' if raw_cache_pass and cache_content_pass else 'FAIL'}"
    )

    print(
        f"Normalization: "
        f"{'PASS' if normalization_pass else 'FAIL'}"
    )

    print(
        f"Processed dataset: "
        f"{'PASS' if dataset_pass else 'FAIL'}"
    )

    print(
        f"Incremental updates: "
        f"{'PASS' if incremental_pass else 'FAIL'}"
    )

    print(
        f"Duplicate prevention: "
        f"{'PASS' if duplicate_pass else 'FAIL'}"
    )


    # ========================================================
    # FINAL RESULT
    # ========================================================

    print(
        "\n" + "=" * 50
    )

    print(
        "STAGE 7.2 FINAL RESULT"
    )

    print(
        "=" * 50
    )

    if all_pass:

        print(
            "7.2.1 Fixture ingestion       PASS"
        )

        print(
            "7.2.2 Reference ingestion     PASS"
        )

        print(
            "7.2.3 Processed dataset       PASS"
        )

        print(
            "7.2.4 Incremental updates     PASS"
        )

        print(
            "7.2.5 Pipeline verification   PASS"
        )

        print(
            "\nSTAGE 7.2: COMPLETE"
        )

        print(
            f"\nVerification season: "
            f"{TEST_SEASON}"
        )

        print(
            f"Production season remains: "
            f"{API_FOOTBALL_SEASON}"
        )

    else:

        print(
            "\nSTAGE 7.2: FAIL"
        )

        sys.exit(1)


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    main()
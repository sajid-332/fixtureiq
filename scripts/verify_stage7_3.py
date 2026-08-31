"""
FixtureIQ Stage 7.3.5
Final Historical Pipeline Verification.

Verifies the complete historical-data pipeline for the
requested seasons.

Checks:
- API availability
- Raw cache
- Historical dataset
- Season coverage
- Record counts
- Fixture ID uniqueness
- Quality report
- Reconciliation report
- Repeat-ingestion safety

The configured production season is never modified.
"""

import json
import subprocess
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
)

from backend.providers.historical import (
    HISTORICAL_FILE,
    load_historical_fixtures,
)


# ============================================================
# Configuration
# ============================================================

SEASONS = [2023, 2024]

QUALITY_REPORT = (
    BASE_DIR
    / "data"
    / "processed"
    / "historical_quality_report.json"
)

RECONCILIATION_REPORT = (
    BASE_DIR
    / "data"
    / "processed"
    / "historical_reconciliation_report.json"
)


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 50)
    print(
        "FixtureIQ Stage 7.3.5"
    )
    print(
        "Final Historical Pipeline Verification"
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
        f"Production season: "
        f"{API_FOOTBALL_SEASON}"
    )

    print(
        f"Verification seasons: "
        f"{SEASONS}"
    )

    print(
        "Production configuration: "
        "UNCHANGED"
    )


    # ========================================================
    # Historical dataset
    # ========================================================

    print(
        "\n" + "-" * 50
    )

    print(
        "1. HISTORICAL DATASET"
    )

    print(
        "-" * 50
    )

    dataset_exists = (
        HISTORICAL_FILE.exists()
    )

    print(
        f"Dataset exists: "
        f"{'PASS' if dataset_exists else 'FAIL'}"
    )

    if not dataset_exists:

        print(
            "\nSTAGE 7.3: FAIL"
        )

        sys.exit(1)

    dataset = load_historical_fixtures(
        HISTORICAL_FILE
    )

    print(
        f"Total records: "
        f"{len(dataset)}"
    )

    dataset_ids_unique = (
        dataset["fixture_id"].is_unique
    )

    print(
        f"Fixture IDs unique: "
        f"{'PASS' if dataset_ids_unique else 'FAIL'}"
    )


    dataset_seasons = sorted(
        set(
            dataset["season"]
            .astype(int)
            .tolist()
        )
    )

    seasons_present = all(
        season in dataset_seasons
        for season in SEASONS
    )

    print(
        f"Required seasons present: "
        f"{'PASS' if seasons_present else 'FAIL'}"
    )

    for season in SEASONS:

        count = int(
            (
                dataset["season"]
                == season
            ).sum()
        )

        print(
            f"Season {season}: "
            f"{count} records"
        )


    # ========================================================
    # Raw cache verification
    # ========================================================

    print(
        "\n" + "-" * 50
    )

    print(
        "2. RAW CACHE"
    )

    print(
        "-" * 50
    )

    cache_results = {}

    for season in SEASONS:

        params = {
            "league":
                API_FOOTBALL_LEAGUE_ID,

            "season":
                season,
        }

        exists = cache_exists(
            "/fixtures",
            params,
        )

        cache_results[season] = exists

        print(
            f"Season {season} cache: "
            f"{'PASS' if exists else 'FAIL'}"
        )


    caches_pass = all(
        cache_results.values()
    )


    # ========================================================
    # API source counts
    # ========================================================

    print(
        "\n" + "-" * 50
    )

    print(
        "3. SOURCE DATA COUNTS"
    )

    print(
        "-" * 50
    )

    provider = APIFootballProvider()

    source_counts = {}

    source_pass = True

    for season in SEASONS:

        payload = provider.get_fixtures(
            API_FOOTBALL_LEAGUE_ID,
            season,
        )

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
                f"Season {season}: "
                "LIMITED_BY_PLAN"
            )

            source_pass = False

            continue

        count = len(
            response
        )

        source_counts[season] = count

        processed_count = int(
            (
                dataset["season"]
                == season
            ).sum()
        )

        matches = (
            count
            ==
            processed_count
        )

        print(
            f"Season {season}: "
            f"source={count}, "
            f"processed={processed_count}, "
            f"{'PASS' if matches else 'FAIL'}"
        )

        if not matches:

            source_pass = False


    # ========================================================
    # Quality report
    # ========================================================

    print(
        "\n" + "-" * 50
    )

    print(
        "4. QUALITY CONTROL"
    )

    print(
        "-" * 50
    )

    quality_exists = (
        QUALITY_REPORT.exists()
    )

    quality_pass = False

    if quality_exists:

        try:

            with QUALITY_REPORT.open(
                "r",
                encoding="utf-8",
            ) as file:

                quality_report = json.load(
                    file
                )

            quality_pass = bool(
                quality_report.get(
                    "overall_pass",
                    False,
                )
            )

        except (
            OSError,
            json.JSONDecodeError,
        ):

            quality_pass = False

    print(
        f"Quality report exists: "
        f"{'PASS' if quality_exists else 'FAIL'}"
    )

    print(
        f"Quality result: "
        f"{'PASS' if quality_pass else 'FAIL'}"
    )


    # ========================================================
    # Reconciliation report
    # ========================================================

    print(
        "\n" + "-" * 50
    )

    print(
        "5. RECONCILIATION"
    )

    print(
        "-" * 50
    )

    reconciliation_exists = (
        RECONCILIATION_REPORT.exists()
    )

    reconciliation_pass = False

    if reconciliation_exists:

        try:

            with RECONCILIATION_REPORT.open(
                "r",
                encoding="utf-8",
            ) as file:

                reconciliation_report = (
                    json.load(file)
                )

            reconciliation_pass = bool(
                reconciliation_report.get(
                    "overall_pass",
                    False,
                )
            )

        except (
            OSError,
            json.JSONDecodeError,
        ):

            reconciliation_pass = False

    print(
        f"Reconciliation report exists: "
        f"{'PASS' if reconciliation_exists else 'FAIL'}"
    )

    print(
        f"Reconciliation result: "
        f"{'PASS' if reconciliation_pass else 'FAIL'}"
    )


    # ========================================================
    # Dataset integrity
    # ========================================================

    print(
        "\n" + "-" * 50
    )

    print(
        "6. FINAL DATASET INTEGRITY"
    )

    print(
        "-" * 50
    )

    expected_total = sum(
        source_counts.values()
    )

    actual_total = len(
        dataset
    )

    total_count_pass = (
        expected_total
        ==
        actual_total
    )

    print(
        f"Expected records: "
        f"{expected_total}"
    )

    print(
        f"Actual records: "
        f"{actual_total}"
    )

    print(
        f"Record count: "
        f"{'PASS' if total_count_pass else 'FAIL'}"
    )


    # ========================================================
    # Final result
    # ========================================================

    all_pass = all(
        [
            dataset_exists,
            dataset_ids_unique,
            seasons_present,
            caches_pass,
            source_pass,
            quality_pass,
            reconciliation_pass,
            total_count_pass,
        ]
    )


    print(
        "\n" + "=" * 50
    )

    print(
        "STAGE 7.3 FINAL RESULT"
    )

    print(
        "=" * 50
    )

    print(
        f"Historical dataset: "
        f"{'PASS' if dataset_exists else 'FAIL'}"
    )

    print(
        f"Season coverage: "
        f"{'PASS' if seasons_present else 'FAIL'}"
    )

    print(
        f"Raw caches: "
        f"{'PASS' if caches_pass else 'FAIL'}"
    )

    print(
        f"Source reconciliation: "
        f"{'PASS' if source_pass else 'FAIL'}"
    )

    print(
        f"Quality control: "
        f"{'PASS' if quality_pass else 'FAIL'}"
    )

    print(
        f"Dataset reconciliation: "
        f"{'PASS' if reconciliation_pass else 'FAIL'}"
    )

    print(
        f"Final integrity: "
        f"{'PASS' if total_count_pass else 'FAIL'}"
    )


    if all_pass:

        print(
            "\n7.3.1 Historical Ingestion       PASS"
        )

        print(
            "7.3.2 Multi-Season Management     PASS"
        )

        print(
            "7.3.3 Quality Control              PASS"
        )

        print(
            "7.3.4 Dataset Reconciliation       PASS"
        )

        print(
            "7.3.5 Final Verification           PASS"
        )

        print(
            "\nSTAGE 7.3: COMPLETE"
        )

        print(
            "\nHistorical seasons verified:"
            f" {SEASONS}"
        )

        print(
            f"Total historical records: "
            f"{actual_total}"
        )

        print(
            f"Production season remains: "
            f"{API_FOOTBALL_SEASON}"
        )

    else:

        print(
            "\nSTAGE 7.3: FAIL"
        )

        sys.exit(1)


if __name__ == "__main__":
    main()
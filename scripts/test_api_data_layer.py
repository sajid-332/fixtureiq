"""
FixtureIQ Stage 7.1.7 - 7.1.9 data-layer test.

7.1.7 - Response normalization
7.1.8 - Data validation
7.1.9 - Local raw cache

Important:
The configured production season remains unchanged.

If API-Football's free plan blocks the configured season,
the test automatically uses 2024 as a provider test season
because the provider explicitly reports that 2022-2024 are
available on the free plan.

This does NOT modify FixtureIQ's production configuration.
"""

import sys
from pathlib import Path


# =================================================
# Project root
# =================================================

BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BASE_DIR)
)


# =================================================
# FixtureIQ imports
# =================================================

from backend.config import (
    API_FOOTBALL_LEAGUE_ID,
    API_FOOTBALL_SEASON,
)

from backend.providers.api_football import (
    APIFootballProvider,
    APIFootballError,
)

from backend.providers.normalizer import (
    normalize_fixtures,
    normalize_teams,
)

from backend.providers.validators import (
    validate_fixtures,
    validate_teams,
)

from backend.providers.cache import (
    cache_exists,
    load_response,
)


# =================================================
# Constants
# =================================================

FREE_PLAN_TEST_SEASON = 2024


# =================================================
# Helpers
# =================================================


def print_status(
    name: str,
    status: str,
) -> None:

    print(
        f"{name:<34} {status}"
    )


def is_plan_restricted(
    payload,
) -> bool:
    """
    Detect API-Football plan restrictions.
    """

    if not isinstance(
        payload,
        dict,
    ):
        return False

    errors = payload.get(
        "errors",
        {}
    )

    if not isinstance(
        errors,
        dict,
    ):
        return False

    return bool(
        errors.get("plan")
    )


def has_api_data(
    payload,
) -> bool:
    """
    Check whether API response contains
    at least one usable record.
    """

    if not isinstance(
        payload,
        dict,
    ):
        return False

    response = payload.get(
        "response"
    )

    return (
        isinstance(
            response,
            list,
        )
        and
        len(response) > 0
    )


# =================================================
# Main
# =================================================


def main():

    print("=" * 46)
    print(
        "FixtureIQ Stage 7.1.7 - 7.1.9"
    )
    print(
        "Data Layer Test"
    )
    print("=" * 46)


    provider = APIFootballProvider()


    configured_season = (
        API_FOOTBALL_SEASON
    )

    test_season = (
        configured_season
    )


    # =================================================
    # Determine usable test season
    # =================================================

    print(
        "\nProvider test season"
    )

    print(
        f"Configured season: "
        f"{configured_season}"
    )


    try:

        initial_fixture_payload = (
            provider.get_fixtures(
                API_FOOTBALL_LEAGUE_ID,
                configured_season,
            )
        )

    except APIFootballError as exc:

        print_status(
            "Initial provider request",
            "FAIL",
        )

        print(
            f"\nError: {exc}"
        )

        sys.exit(1)


    if is_plan_restricted(
        initial_fixture_payload
    ):

        test_season = (
            FREE_PLAN_TEST_SEASON
        )

        print(
            "Configured season is restricted "
            "by the current API plan."
        )

        print(
            f"Using {test_season} only for "
            "data-layer verification."
        )

    else:

        print(
            "Configured season is available "
            "for data-layer testing."
        )


    print(
        f"Active test season: "
        f"{test_season}"
    )


    # =================================================
    # Fetch fixtures
    # =================================================

    print(
        "\nFetching fixtures..."
    )


    try:

        fixture_payload = (
            initial_fixture_payload
            if test_season
            == configured_season
            else
            provider.get_fixtures(
                API_FOOTBALL_LEAGUE_ID,
                test_season,
            )
        )

    except APIFootballError as exc:

        print_status(
            "Fixture API request",
            "FAIL",
        )

        print(
            f"\nError: {exc}"
        )

        sys.exit(1)


    # =================================================
    # Confirm fixture data
    # =================================================

    if not has_api_data(
        fixture_payload
    ):

        print_status(
            "Fixture API data",
            "FAIL",
        )

        print(
            "\nNo fixture records were "
            "returned for the test season."
        )

        print(
            "The data layer cannot be "
            "validated with zero records."
        )

        sys.exit(1)


    print_status(
        "Fixture API data",
        "PASS",
    )


    # =================================================
    # 7.1.7 Response Normalization
    # =================================================

    print(
        "\n7.1.7 Response Normalization"
    )


    fixtures = normalize_fixtures(
        fixture_payload
    )


    required_fixture_fields = {
        "fixture_id",
        "date",
        "home_team",
        "away_team",
        "league",
        "goals",
    }


    normalization_pass = (
        len(fixtures) > 0
        and
        required_fixture_fields
        .issubset(
            fixtures[0].keys()
        )
    )


    print(
        f"Normalized fixtures: "
        f"{len(fixtures)}"
    )


    print_status(
        "Fixture normalization",
        "PASS"
        if normalization_pass
        else "FAIL",
    )


    # =================================================
    # 7.1.8 Fixture validation
    # =================================================

    print(
        "\n7.1.8 Data Validation"
    )


    fixture_validation = (
        validate_fixtures(
            fixtures
        )
    )


    print(
        f"Total fixtures: "
        f"{fixture_validation['total']}"
    )

    print(
        f"Valid fixtures: "
        f"{fixture_validation['valid_count']}"
    )

    print(
        f"Invalid fixtures: "
        f"{fixture_validation['invalid_count']}"
    )


    fixture_validation_pass = (
        fixture_validation["valid"]
    )


    print_status(
        "Fixture validation",
        "PASS"
        if fixture_validation_pass
        else "FAIL",
    )


    # =================================================
    # Teams
    # =================================================

    print(
        "\nTesting team normalization..."
    )


    try:

        team_payload = (
            provider.get_teams(
                API_FOOTBALL_LEAGUE_ID,
                test_season,
            )
        )

    except APIFootballError as exc:

        print_status(
            "Team API request",
            "FAIL",
        )

        print(
            f"\nError: {exc}"
        )

        sys.exit(1)


    if not has_api_data(
        team_payload
    ):

        print_status(
            "Team API data",
            "FAIL",
        )

        print(
            "\nNo team records were "
            "returned for the test season."
        )

        sys.exit(1)


    teams = normalize_teams(
        team_payload
    )


    team_validation = (
        validate_teams(
            teams
        )
    )


    print(
        f"Normalized teams: "
        f"{len(teams)}"
    )


    team_validation_pass = (
        len(teams) > 0
        and
        team_validation["valid"]
    )


    print_status(
        "Team validation",
        "PASS"
        if team_validation_pass
        else "FAIL",
    )


    # =================================================
    # 7.1.9 Local Raw Cache
    # =================================================

    print(
        "\n7.1.9 Local Raw Cache"
    )


    fixture_params = {
        "league":
            API_FOOTBALL_LEAGUE_ID,

        "season":
            test_season,
    }


    # The provider automatically caches
    # successful HTTP responses.

    cache_status = cache_exists(
        "/fixtures",
        fixture_params,
    )


    print_status(
        "Cache file created",
        "PASS"
        if cache_status
        else "FAIL",
    )


    cached_response = load_response(
        "fixtures",
        fixture_params,
    )


    cache_read_pass = (
        cached_response is not None
        and
        isinstance(
            cached_response,
            dict,
        )
        and
        "response"
        in cached_response
    )


    print_status(
        "Cache read",
        "PASS"
        if cache_read_pass
        else "FAIL",
    )


    # =================================================
    # Cache content validation
    # =================================================

    cache_content_pass = False


    if cache_read_pass:

        cached_api_response = (
            cached_response.get(
                "response"
            )
        )

        cache_content_pass = (
            isinstance(
                cached_api_response,
                dict,
            )
            and
            "response"
            in cached_api_response
        )


    print_status(
        "Cache content validation",
        "PASS"
        if cache_content_pass
        else "FAIL",
    )


    # =================================================
    # Final result
    # =================================================

    overall_pass = (
        normalization_pass
        and
        fixture_validation_pass
        and
        team_validation_pass
        and
        cache_status
        and
        cache_read_pass
        and
        cache_content_pass
    )


    print(
        "\n" + "=" * 46
    )

    print(
        "FINAL RESULT"
    )

    print(
        "=" * 46
    )


    print(
        "7.1.7 Response Normalization     "
        +
        (
            "PASS"
            if normalization_pass
            else "FAIL"
        )
    )


    print(
        "7.1.8 Data Validation             "
        +
        (
            "PASS"
            if (
                fixture_validation_pass
                and
                team_validation_pass
            )
            else "FAIL"
        )
    )


    print(
        "7.1.9 Local Raw Cache             "
        +
        (
            "PASS"
            if (
                cache_status
                and
                cache_read_pass
                and
                cache_content_pass
            )
            else "FAIL"
        )
    )


    if overall_pass:

        print(
            "\nStage 7.1.7 - 7.1.9: PASS"
        )

        if test_season != configured_season:

            print(
                "Provider limitation note:"
            )

            print(
                f"Data-layer verification used "
                f"{test_season} because the "
                f"configured {configured_season} "
                f"season is restricted by the "
                f"current API plan."
            )

    else:

        print(
            "\nStage 7.1.7 - 7.1.9: FAIL"
        )

        sys.exit(1)


if __name__ == "__main__":

    main()
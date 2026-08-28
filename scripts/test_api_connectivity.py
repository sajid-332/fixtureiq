"""
FixtureIQ API-Football connectivity and capability test.

Stage 7.1.4 - 7.1.6

Tests:
- API connectivity
- API response structure
- Provider capabilities
- Free-plan limitations
- Basic error handling
- API key security
"""

import json
import sys
from pathlib import Path


# -------------------------------------------------
# Project root
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(BASE_DIR))


# -------------------------------------------------
# FixtureIQ imports
# -------------------------------------------------

from backend.config import (
    API_FOOTBALL_KEY,
    API_FOOTBALL_LEAGUE_ID,
    API_FOOTBALL_SEASON,
    get_config_summary,
    validate_config,
)

from backend.providers.api_football import (
    APIFootballError,
    APIFootballProvider,
    APIFootballAuthenticationError,
    APIFootballRateLimitError,
    APIFootballConnectionError,
    APIFootballResponseError,
)


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def print_result(name: str, status: str) -> None:
    print(f"{name:<32} {status}")


def validate_api_payload(payload) -> bool:
    """
    Validate the basic API-Football response structure.
    """

    if not isinstance(payload, dict):
        return False

    if "response" not in payload:
        return False

    if not isinstance(payload["response"], list):
        return False

    return True


def is_plan_restriction(payload) -> bool:
    """
    Detect API-Football free-plan restrictions.
    """

    errors = payload.get("errors", {})

    if not isinstance(errors, dict):
        return False

    plan_error = errors.get("plan")

    if not plan_error:
        return False

    return True


# -------------------------------------------------
# Main
# -------------------------------------------------

def main():

    print("=" * 46)
    print("FixtureIQ API-Football Provider Test")
    print("Stage 7.1.4 - 7.1.6")
    print("=" * 46)


    # -------------------------------------------------
    # Configuration
    # -------------------------------------------------

    print("\nConfiguration")

    try:

        validate_config()

        print_result(
            "Configuration",
            "PASS"
        )

    except Exception as exc:

        print_result(
            "Configuration",
            "FAIL"
        )

        print(f"\nError: {exc}")

        sys.exit(1)


    summary = get_config_summary()

    print(f"Provider: {summary['api_provider']}")
    print(f"Base URL: {summary['base_url']}")
    print(f"League ID: {summary['league_id']}")
    print(f"Season: {summary['season']}")
    print(f"Timeout: {summary['timeout']}")
    print(
        f"API key configured: "
        f"{summary['api_key_configured']}"
    )


    # -------------------------------------------------
    # Provider
    # -------------------------------------------------

    provider = APIFootballProvider()


    # -------------------------------------------------
    # 7.1.4 — API Connectivity
    # -------------------------------------------------

    print("\n7.1.4 API Connectivity")

    connectivity_pass = False

    league_payload = None

    try:

        league_payload = provider.get_leagues(
            API_FOOTBALL_LEAGUE_ID,
            API_FOOTBALL_SEASON,
        )

        if validate_api_payload(league_payload):

            connectivity_pass = True

            print_result(
                "API connectivity",
                "PASS"
            )

            print_result(
                "API response structure",
                "PASS"
            )

        else:

            print_result(
                "API connectivity",
                "FAIL"
            )

            print_result(
                "API response structure",
                "FAIL"
            )

    except APIFootballAuthenticationError as exc:

        print_result(
            "API authentication",
            "FAIL"
        )

        print(f"\nError: {exc}")

        sys.exit(1)

    except APIFootballRateLimitError as exc:

        print_result(
            "API rate limit",
            "LIMITED"
        )

        print(f"\nError: {exc}")

        sys.exit(1)

    except APIFootballConnectionError as exc:

        print_result(
            "API connectivity",
            "FAIL"
        )

        print(f"\nError: {exc}")

        sys.exit(1)

    except APIFootballResponseError as exc:

        print_result(
            "API response",
            "FAIL"
        )

        print(f"\nError: {exc}")

        sys.exit(1)


    # -------------------------------------------------
    # 7.1.5 — Provider Capability Verification
    # -------------------------------------------------

    print("\n7.1.5 Provider Capability Verification")


    capability_results = {}


    # -------------------------------------------------
    # League
    # -------------------------------------------------

    if is_plan_restriction(league_payload):

        capability_results["league"] = "LIMITED_BY_PLAN"

        plan_error = league_payload.get(
            "errors",
            {}
        ).get(
            "plan",
            "Provider plan restriction."
        )

        print_result(
            "League",
            "LIMITED_BY_PLAN"
        )

        print(
            f"  Provider limitation: {plan_error}"
        )

    else:

        capability_results["league"] = (
            validate_api_payload(
                league_payload
            )
            and
            len(
                league_payload["response"]
            ) > 0
        )

        print_result(
            "League",
            "PASS"
            if capability_results["league"]
            else "FAIL"
        )


    # -------------------------------------------------
    # Fixtures
    # -------------------------------------------------

    capability_results["fixtures"] = False

    try:

        payload = provider.get_fixtures(
            API_FOOTBALL_LEAGUE_ID,
            API_FOOTBALL_SEASON,
        )

        capability_results["fixtures"] = (
            validate_api_payload(payload)
        )

    except APIFootballError as exc:

        print(
            f"  Fixtures error: {exc}"
        )

    print_result(
        "Fixtures",
        "PASS"
        if capability_results["fixtures"]
        else "FAIL"
    )


    # -------------------------------------------------
    # Teams
    # -------------------------------------------------

    capability_results["teams"] = False

    try:

        payload = provider.get_teams(
            API_FOOTBALL_LEAGUE_ID,
            API_FOOTBALL_SEASON,
        )

        capability_results["teams"] = (
            validate_api_payload(payload)
        )

    except APIFootballError as exc:

        print(
            f"  Teams error: {exc}"
        )

    print_result(
        "Teams",
        "PASS"
        if capability_results["teams"]
        else "FAIL"
    )


    # -------------------------------------------------
    # Standings
    # -------------------------------------------------

    capability_results["standings"] = False

    try:

        payload = provider.get_standings(
            API_FOOTBALL_LEAGUE_ID,
            API_FOOTBALL_SEASON,
        )

        capability_results["standings"] = (
            validate_api_payload(payload)
        )

    except APIFootballError as exc:

        print(
            f"  Standings error: {exc}"
        )

    print_result(
        "Standings",
        "PASS"
        if capability_results["standings"]
        else "FAIL"
    )


    # -------------------------------------------------
    # 7.1.6 — Error Handling
    # -------------------------------------------------

    print("\n7.1.6 Error Handling Baseline")


    error_checks = {
        "missing_key": False,
        "invalid_key": False,
        "timeout": False,
        "response_handling": False,
    }


    # -------------------------------------------------
    # Missing API key
    # -------------------------------------------------

    try:

        APIFootballProvider(
            api_key=None
        ).get(
            "/leagues",
            params={
                "id": API_FOOTBALL_LEAGUE_ID,
                "season": API_FOOTBALL_SEASON,
            },
        )

    except APIFootballAuthenticationError:

        error_checks["missing_key"] = True


    print_result(
        "Missing API key handling",
        "PASS"
        if error_checks["missing_key"]
        else "FAIL"
    )


    # -------------------------------------------------
    # Invalid API key
    # -------------------------------------------------

    try:

        APIFootballProvider(
            api_key="invalid-key-for-test"
        ).get(
            "/leagues",
            params={
                "id": API_FOOTBALL_LEAGUE_ID,
                "season": API_FOOTBALL_SEASON,
            },
        )

    except APIFootballAuthenticationError:

        error_checks["invalid_key"] = True

    except APIFootballError:

        error_checks["invalid_key"] = True


    print_result(
        "Invalid API key handling",
        "PASS"
        if error_checks["invalid_key"]
        else "FAIL"
    )


    # -------------------------------------------------
    # Timeout
    # -------------------------------------------------

    try:

        APIFootballProvider(
            timeout=0.001
        ).get(
            "/leagues",
            params={
                "id": API_FOOTBALL_LEAGUE_ID,
                "season": API_FOOTBALL_SEASON,
            },
        )

    except APIFootballConnectionError:

        error_checks["timeout"] = True

    except APIFootballError:

        error_checks["timeout"] = True


    print_result(
        "Timeout handling",
        "PASS"
        if error_checks["timeout"]
        else "FAIL"
    )


    # -------------------------------------------------
    # Response validation
    # -------------------------------------------------

    error_checks["response_handling"] = (
        league_payload is not None
        and
        validate_api_payload(
            league_payload
        )
    )


    print_result(
        "Response validation",
        "PASS"
        if error_checks["response_handling"]
        else "FAIL"
    )


    # -------------------------------------------------
    # Security
    # -------------------------------------------------

    print("\nSecurity")


    key_not_logged = (
        API_FOOTBALL_KEY
        not in
        json.dumps(
            get_config_summary()
        )
    )


    print_result(
        "API key excluded from summary",
        "PASS"
        if key_not_logged
        else "FAIL"
    )


    # -------------------------------------------------
    # Final evaluation
    # -------------------------------------------------

    required_capabilities_pass = all(
        value is True
        or value == "LIMITED_BY_PLAN"
        for value in capability_results.values()
    )


    all_error_checks_pass = all(
        error_checks.values()
    )


    overall_pass = (
        connectivity_pass
        and
        required_capabilities_pass
        and
        all_error_checks_pass
        and
        key_not_logged
    )


    print("\n" + "=" * 46)
    print("FINAL RESULT")
    print("=" * 46)


    print(
        "7.1.4 API Connectivity          "
        + ("PASS" if connectivity_pass else "FAIL")
    )

    print(
        "7.1.5 Capability Verification  "
        + (
            "PASS"
            if required_capabilities_pass
            else "FAIL"
        )
    )

    print(
        "7.1.6 Error Handling             "
        + (
            "PASS"
            if all_error_checks_pass
            else "FAIL"
        )
    )


    if overall_pass:

        if (
            "LIMITED_BY_PLAN"
            in capability_results.values()
        ):

            print(
                "\nStage 7.1.4 - 7.1.6: "
                "PASS WITH PROVIDER LIMITATION"
            )

        else:

            print(
                "\nStage 7.1.4 - 7.1.6: PASS"
            )

    else:

        print(
            "\nStage 7.1.4 - 7.1.6: FAIL"
        )

        sys.exit(1)


if __name__ == "__main__":
    main()
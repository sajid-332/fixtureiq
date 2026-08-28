"""
FixtureIQ API-Football data validation.

Stage 7.1.8

Validates normalized provider data before it is used
by the FixtureIQ data pipeline.
"""

from datetime import datetime
from typing import Any, Dict, List


def _valid_positive_integer(value) -> bool:
    """
    Check whether a value is a positive integer.
    """

    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value > 0
    )


def _valid_team(team: Dict[str, Any]) -> bool:
    """
    Validate a normalized team.
    """

    if not isinstance(team, dict):
        return False

    if not _valid_positive_integer(
        team.get("id")
    ):
        return False

    if not isinstance(
        team.get("name"),
        str,
    ):
        return False

    if not team.get("name").strip():
        return False

    return True


def validate_fixture(
    fixture: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate one normalized fixture.

    Returns a structured validation result.
    """

    errors: List[str] = []

    if not isinstance(fixture, dict):

        return {
            "valid": False,
            "errors": ["Fixture must be a dictionary."],
        }

    if not _valid_positive_integer(
        fixture.get("fixture_id")
    ):

        errors.append(
            "Invalid or missing fixture_id."
        )

    date_value = fixture.get("date")

    if not isinstance(
        date_value,
        str,
    ) or not date_value.strip():

        errors.append(
            "Invalid or missing fixture date."
        )

    else:

        try:

            datetime.fromisoformat(
                date_value.replace(
                    "Z",
                    "+00:00",
                )
            )

        except ValueError:

            errors.append(
                "Fixture date is not valid ISO format."
            )

    home_team = fixture.get(
        "home_team"
    )

    away_team = fixture.get(
        "away_team"
    )

    if not _valid_team(home_team):

        errors.append(
            "Invalid home team."
        )

    if not _valid_team(away_team):

        errors.append(
            "Invalid away team."
        )

    if (
        _valid_team(home_team)
        and
        _valid_team(away_team)
        and
        home_team["id"]
        == away_team["id"]
    ):

        errors.append(
            "Home and away teams cannot be identical."
        )

    league = fixture.get(
        "league",
        {}
    )

    if not isinstance(
        league,
        dict,
    ):

        errors.append(
            "Invalid league object."
        )

    elif not _valid_positive_integer(
        league.get("id")
    ):

        errors.append(
            "Invalid or missing league ID."
        )

    season = league.get(
        "season"
    )

    if (
        season is not None
        and
        (
            not isinstance(season, int)
            or
            isinstance(season, bool)
        )
    ):

        errors.append(
            "League season must be an integer."
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


def validate_fixtures(
    fixtures: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Validate a list of normalized fixtures.
    """

    if not isinstance(
        fixtures,
        list,
    ):

        return {
            "valid": False,
            "total": 0,
            "valid_count": 0,
            "invalid_count": 0,
            "errors": [
                "Fixtures must be a list."
            ],
        }

    results = []

    seen_ids = set()

    duplicate_ids = []

    for fixture in fixtures:

        result = validate_fixture(
            fixture
        )

        results.append(result)

        fixture_id = (
            fixture.get("fixture_id")
            if isinstance(
                fixture,
                dict,
            )
            else None
        )

        if fixture_id in seen_ids:

            duplicate_ids.append(
                fixture_id
            )

        elif fixture_id is not None:

            seen_ids.add(
                fixture_id
            )

    valid_count = sum(
        result["valid"]
        for result in results
    )

    errors = []

    for index, result in enumerate(results):

        if not result["valid"]:

            errors.append({
                "index": index,
                "errors": result["errors"],
            })

    if duplicate_ids:

        errors.append({
            "duplicate_fixture_ids":
                duplicate_ids
        })

    return {
        "valid": (
            valid_count == len(fixtures)
            and
            len(duplicate_ids) == 0
        ),

        "total": len(fixtures),

        "valid_count": valid_count,

        "invalid_count":
            len(fixtures) - valid_count,

        "errors": errors,
    }


def validate_team(
    team: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate one normalized team.
    """

    errors = []

    if not _valid_team(team):

        errors.append(
            "Invalid team ID or name."
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


def validate_teams(
    teams: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Validate normalized teams.
    """

    if not isinstance(
        teams,
        list,
    ):

        return {
            "valid": False,
            "total": 0,
            "valid_count": 0,
            "invalid_count": 0,
            "errors": [
                "Teams must be a list."
            ],
        }

    results = [
        validate_team(team)
        for team in teams
    ]

    valid_count = sum(
        result["valid"]
        for result in results
    )

    return {
        "valid": (
            valid_count == len(teams)
        ),

        "total": len(teams),

        "valid_count": valid_count,

        "invalid_count":
            len(teams) - valid_count,

        "errors": [
            {
                "index": index,
                "errors": result["errors"],
            }
            for index, result in enumerate(results)
            if not result["valid"]
        ],
    }


def validate_league(
    league: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate one normalized league.
    """

    errors = []

    if not isinstance(
        league,
        dict,
    ):

        return {
            "valid": False,
            "errors": [
                "League must be a dictionary."
            ],
        }

    if not _valid_positive_integer(
        league.get("id")
    ):

        errors.append(
            "Invalid or missing league ID."
        )

    if not isinstance(
        league.get("name"),
        str,
    ):

        errors.append(
            "Invalid or missing league name."
        )

    season = league.get(
        "season"
    )

    if season is not None:

        if (
            not isinstance(
                season,
                int,
            )
            or
            isinstance(
                season,
                bool,
            )
        ):

            errors.append(
                "League season must be an integer."
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }
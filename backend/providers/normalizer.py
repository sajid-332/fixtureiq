"""
FixtureIQ API-Football response normalization.

Stage 7.1.7

Converts provider-specific API-Football responses into
simple FixtureIQ-standard dictionaries.

This module does not modify the ML pipeline.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


def _safe_get(data: Dict[str, Any], *keys, default=None):
    """
    Safely retrieve nested dictionary values.
    """

    current = data

    for key in keys:

        if not isinstance(current, dict):
            return default

        current = current.get(key)

        if current is None:
            return default

    return current


def normalize_team(team: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a team object.
    """

    return {
        "id": team.get("id"),
        "name": team.get("name"),
        "code": team.get("code"),
        "country": team.get("country"),
        "logo": team.get("logo"),
    }


def normalize_league(league: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize league information.
    """

    return {
        "id": league.get("id"),
        "name": league.get("name"),
        "country": league.get("country"),
        "logo": league.get("logo"),
        "type": league.get("type"),
        "season": league.get("season"),
    }


def normalize_fixture(fixture: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize an API-Football fixture.
    """

    fixture_info = fixture.get("fixture", {})
    league_info = fixture.get("league", {})
    teams_info = fixture.get("teams", {})
    goals_info = fixture.get("goals", {})

    home_team = teams_info.get("home", {})
    away_team = teams_info.get("away", {})

    timestamp = fixture_info.get("timestamp")
    date_value = fixture_info.get("date")

    normalized_date = None

    if date_value:

        try:

            normalized_date = datetime.fromisoformat(
                date_value.replace("Z", "+00:00")
            ).isoformat()

        except (ValueError, TypeError):

            normalized_date = date_value

    return {
        "fixture_id": fixture_info.get("id"),

        "date": normalized_date,

        "timestamp": timestamp,

        "timezone": fixture_info.get("timezone"),

        "status": {
            "short": _safe_get(
                fixture_info,
                "status",
                "short",
            ),
            "long": _safe_get(
                fixture_info,
                "status",
                "long",
            ),
            "elapsed": _safe_get(
                fixture_info,
                "status",
                "elapsed",
            ),
        },

        "league": {
            "id": league_info.get("id"),
            "name": league_info.get("name"),
            "country": league_info.get("country"),
            "season": league_info.get("season"),
            "round": league_info.get("round"),
        },

        "home_team": normalize_team(home_team),

        "away_team": normalize_team(away_team),

        "goals": {
            "home": goals_info.get("home"),
            "away": goals_info.get("away"),
        },

        "raw": fixture,
    }


def normalize_fixtures(
    payload: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Normalize a complete fixtures API response.
    """

    response = payload.get("response", [])

    if not isinstance(response, list):
        return []

    return [
        normalize_fixture(fixture)
        for fixture in response
        if isinstance(fixture, dict)
    ]


def normalize_teams(
    payload: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Normalize a complete teams API response.
    """

    response = payload.get("response", [])

    if not isinstance(response, list):
        return []

    normalized = []

    for item in response:

        if not isinstance(item, dict):
            continue

        team = item.get("team", item)

        if isinstance(team, dict):

            normalized.append(
                normalize_team(team)
            )

    return normalized


def normalize_leagues(
    payload: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Normalize a complete leagues API response.
    """

    response = payload.get("response", [])

    if not isinstance(response, list):
        return []

    normalized = []

    for item in response:

        if not isinstance(item, dict):
            continue

        league = item.get(
            "league",
            item,
        )

        seasons = item.get(
            "seasons",
            [],
        )

        if isinstance(seasons, list):

            for season in seasons:

                if isinstance(season, dict):

                    league_copy = dict(league)

                    league_copy[
                        "season"
                    ] = season.get("year")

                    normalized.append(
                        normalize_league(
                            league_copy
                        )
                    )

        else:

            normalized.append(
                normalize_league(league)
            )

    return normalized
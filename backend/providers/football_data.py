"""
FixtureIQ football-data.org provider.

Used for current/upcoming production fixture retrieval.

This provider does NOT replace the historical API-Football layer.
"""

from __future__ import annotations

import os

import requests
from dotenv import load_dotenv


load_dotenv()


class FootballDataError(Exception):
    """football-data.org provider error."""


class FootballDataProvider:

    BASE_URL = "https://api.football-data.org/v4"

    def __init__(self):

        self.api_key = os.getenv(
            "FOOTBALL_DATA_API_KEY"
        )

        if not self.api_key:
            raise FootballDataError(
                "FOOTBALL_DATA_API_KEY is not configured."
            )

        self.session = requests.Session()

        self.session.headers.update(
            {
                "X-Auth-Token": self.api_key,
                "Accept": "application/json",
            }
        )

    def get_premier_league_matches(
        self,
        season: int,
    ) -> dict:

        url = (
            f"{self.BASE_URL}"
            "/competitions/PL/matches"
        )

        try:

            response = self.session.get(
                url,
                params={
                    "season": season,
                },
                timeout=30,
            )

        except requests.RequestException as exc:

            raise FootballDataError(
                f"football-data.org request failed: {exc}"
            ) from exc

        try:

            payload = response.json()

        except ValueError as exc:

            raise FootballDataError(
                "football-data.org returned invalid JSON."
            ) from exc

        if response.status_code != 200:

            message = (
                payload.get("message")
                if isinstance(payload, dict)
                else None
            )

            raise FootballDataError(
                "football-data.org returned "
                f"HTTP {response.status_code}: "
                f"{message or 'Unknown provider error'}"
            )

        if not isinstance(payload, dict):

            raise FootballDataError(
                "Unexpected football-data.org response."
            )

        matches = payload.get(
            "matches"
        )

        if not isinstance(
            matches,
            list,
        ):

            raise FootballDataError(
                "football-data.org response does "
                "not contain a matches list."
            )

        return payload
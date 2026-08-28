"""
FixtureIQ API-Football provider.

Stage 7.1.4 - 7.1.6

Provides a small reusable API request layer for:
- API connectivity
- Provider capability verification
- Basic API error handling

The API key is loaded from backend.config
and is never printed or logged.
"""

from typing import Any, Dict, Optional

import requests

from backend.config import (
    API_FOOTBALL_BASE_URL,
    API_FOOTBALL_KEY,
    API_FOOTBALL_TIMEOUT,
)


class APIFootballError(Exception):
    """Base exception for API-Football errors."""


class APIFootballAuthenticationError(APIFootballError):
    """Raised when API authentication fails."""


class APIFootballRateLimitError(APIFootballError):
    """Raised when API rate limit or quota is exceeded."""


class APIFootballConnectionError(APIFootballError):
    """Raised when API cannot be reached."""


class APIFootballResponseError(APIFootballError):
    """Raised when API returns an invalid response."""


class APIFootballProvider:
    """
    Reusable API-Football provider.

    Authentication uses the x-apisports-key header.
    """

    def __init__(
        self,
        base_url: str = API_FOOTBALL_BASE_URL,
        api_key: Optional[str] = API_FOOTBALL_KEY,
        timeout: int = API_FOOTBALL_TIMEOUT,
    ) -> None:

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        """Create API request headers."""

        if not self.api_key:
            raise APIFootballAuthenticationError(
                "API_FOOTBALL_KEY is not configured."
            )

        return {
            "x-apisports-key": self.api_key
        }

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send a GET request to API-Football.
        """

        endpoint = endpoint.lstrip("/")

        url = f"{self.base_url}/{endpoint}"

        try:
            response = requests.get(
                url,
                headers=self._headers(),
                params=params or {},
                timeout=self.timeout,
            )

        except requests.exceptions.Timeout as exc:
            raise APIFootballConnectionError(
                "API-Football request timed out."
            ) from exc

        except requests.exceptions.ConnectionError as exc:
            raise APIFootballConnectionError(
                "Could not connect to API-Football."
            ) from exc

        except requests.exceptions.RequestException as exc:
            raise APIFootballConnectionError(
                f"API-Football request failed: {exc}"
            ) from exc

        # Authentication errors
        if response.status_code in (401, 403):
            raise APIFootballAuthenticationError(
                "API-Football authentication failed."
            )

        # Rate limit
        if response.status_code == 429:
            raise APIFootballRateLimitError(
                "API-Football rate limit or quota exceeded."
            )

        # Other HTTP errors
        if response.status_code >= 400:
            raise APIFootballResponseError(
                f"API-Football returned HTTP "
                f"{response.status_code}."
            )

        # JSON parsing
        try:
            data = response.json()

        except ValueError as exc:
            raise APIFootballResponseError(
                "API-Football returned invalid JSON."
            ) from exc

        # Basic response validation
        if not isinstance(data, dict):
            raise APIFootballResponseError(
                "API-Football returned an unexpected response format."
            )

        if "response" not in data:
            raise APIFootballResponseError(
                "API-Football response is missing the 'response' field."
            )

        return data

    def get_leagues(
        self,
        league_id: int,
        season: int,
    ) -> Dict[str, Any]:
        """Get league information."""

        return self.get(
            "/leagues",
            params={
                "id": league_id,
                "season": season,
            },
        )

    def get_fixtures(
        self,
        league_id: int,
        season: int,
    ) -> Dict[str, Any]:
        """Get fixtures for a league and season."""

        return self.get(
            "/fixtures",
            params={
                "league": league_id,
                "season": season,
            },
        )

    def get_teams(
        self,
        league_id: int,
        season: int,
    ) -> Dict[str, Any]:
        """Get teams for a league and season."""

        return self.get(
            "/teams",
            params={
                "league": league_id,
                "season": season,
            },
        )

    def get_standings(
        self,
        league_id: int,
        season: int,
    ) -> Dict[str, Any]:
        """Get standings for a league and season."""

        return self.get(
            "/standings",
            params={
                "league": league_id,
                "season": season,
            },
        )
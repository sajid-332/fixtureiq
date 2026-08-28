"""
FixtureIQ API-Football provider.

Stage 7.1.4 - 7.1.9

Responsibilities:
- API-Football connectivity
- Authentication
- Request handling
- Error handling
- Basic response validation
- Raw response caching

The API key is loaded from backend.config.
The API key is never logged or stored in cache files.
"""

from typing import Any, Dict, Optional

import requests

from backend.config import (
    API_FOOTBALL_BASE_URL,
    API_FOOTBALL_KEY,
    API_FOOTBALL_TIMEOUT,
)

from backend.providers.cache import save_response


# =================================================
# Custom Exceptions
# =================================================


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


# =================================================
# Provider
# =================================================


class APIFootballProvider:
    """
    Reusable API-Football provider.

    Authentication:
        x-apisports-key HTTP header

    Configuration:
        Loaded from backend.config
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

    # -------------------------------------------------
    # Request headers
    # -------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        """
        Build request headers.

        The API key is never printed or logged.
        """

        if not self.api_key:

            raise APIFootballAuthenticationError(
                "API_FOOTBALL_KEY is not configured."
            )

        return {
            "x-apisports-key": self.api_key
        }

    # -------------------------------------------------
    # Generic GET request
    # -------------------------------------------------

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send a GET request to API-Football.

        Args:
            endpoint:
                API endpoint such as /fixtures.

            params:
                Query parameters.

        Returns:
            Parsed API-Football JSON response.

        Raises:
            APIFootballAuthenticationError
            APIFootballRateLimitError
            APIFootballConnectionError
            APIFootballResponseError
        """

        endpoint = endpoint.lstrip("/")

        url = f"{self.base_url}/{endpoint}"

        request_params = params or {}

        try:

            response = requests.get(
                url,
                headers=self._headers(),
                params=request_params,
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

        # -------------------------------------------------
        # HTTP authentication errors
        # -------------------------------------------------

        if response.status_code in (401, 403):

            raise APIFootballAuthenticationError(
                "API-Football authentication failed."
            )

        # -------------------------------------------------
        # Rate limit / quota
        # -------------------------------------------------

        if response.status_code == 429:

            raise APIFootballRateLimitError(
                "API-Football rate limit or quota exceeded."
            )

        # -------------------------------------------------
        # Other HTTP errors
        # -------------------------------------------------

        if response.status_code >= 400:

            raise APIFootballResponseError(
                "API-Football returned HTTP "
                f"{response.status_code}."
            )

        # -------------------------------------------------
        # JSON parsing
        # -------------------------------------------------

        try:

            data = response.json()

        except ValueError as exc:

            raise APIFootballResponseError(
                "API-Football returned invalid JSON."
            ) from exc

        # -------------------------------------------------
        # Basic response validation
        # -------------------------------------------------

        if not isinstance(data, dict):

            raise APIFootballResponseError(
                "API-Football returned an unexpected "
                "response format."
            )

        if "response" not in data:

            raise APIFootballResponseError(
                "API-Football response is missing "
                "the 'response' field."
            )

        # -------------------------------------------------
        # Cache successful response
        # -------------------------------------------------

        save_response(
            endpoint=endpoint,
            params=request_params,
            response=data,
        )

        return data

    # =================================================
    # League
    # =================================================

    def get_leagues(
        self,
        league_id: int,
        season: int,
    ) -> Dict[str, Any]:
        """
        Retrieve league information.
        """

        return self.get(
            "/leagues",
            params={
                "id": league_id,
                "season": season,
            },
        )

    # =================================================
    # Fixtures
    # =================================================

    def get_fixtures(
        self,
        league_id: int,
        season: int,
    ) -> Dict[str, Any]:
        """
        Retrieve fixtures for a league and season.
        """

        return self.get(
            "/fixtures",
            params={
                "league": league_id,
                "season": season,
            },
        )

    # =================================================
    # Teams
    # =================================================

    def get_teams(
        self,
        league_id: int,
        season: int,
    ) -> Dict[str, Any]:
        """
        Retrieve teams for a league and season.
        """

        return self.get(
            "/teams",
            params={
                "league": league_id,
                "season": season,
            },
        )

    # =================================================
    # Standings
    # =================================================

    def get_standings(
        self,
        league_id: int,
        season: int,
    ) -> Dict[str, Any]:
        """
        Retrieve league standings.
        """

        return self.get(
            "/standings",
            params={
                "league": league_id,
                "season": season,
            },
        )
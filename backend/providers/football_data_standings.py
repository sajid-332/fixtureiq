"""
FixtureIQ Stage 8.2.1
football-data.org EPL Standings Provider.

Responsibilities:
- read FOOTBALL_DATA_API_KEY safely
- request Premier League standings
- validate provider response
- extract the TOTAL league table
- return provider-native standings rows

This module does NOT:
- normalize teams into FixtureIQ identity
- write production artifacts
- modify Stage 7 files
- execute the prediction model
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
)

ENV_FILE = (
    BASE_DIR
    / ".env"
)


class FootballDataStandingsError(
    RuntimeError
):
    """Raised when the live standings source is unusable."""


def _read_env_file_value(
    key: str,
) -> str | None:

    if not ENV_FILE.exists():

        return None

    with ENV_FILE.open(
        "r",
        encoding="utf-8-sig",
    ) as file:

        for raw_line in file:

            line = (
                raw_line
                .strip()
            )

            if (
                not line
                or
                line.startswith("#")
                or
                "=" not in line
            ):

                continue

            name, value = (
                line.split(
                    "=",
                    1,
                )
            )

            if (
                name.strip()
                != key
            ):

                continue

            value = (
                value
                .strip()
                .strip('"')
                .strip("'")
            )

            return (
                value
                if value
                else None
            )

    return None


def get_football_data_api_key() -> str:

    api_key = (
        os.getenv(
            "FOOTBALL_DATA_API_KEY"
        )
        or
        _read_env_file_value(
            "FOOTBALL_DATA_API_KEY"
        )
    )

    if not api_key:

        raise FootballDataStandingsError(
            (
                "FOOTBALL_DATA_API_KEY is missing. "
                "Set it in the environment or project .env file."
            )
        )

    return api_key


class FootballDataStandingsClient:

    BASE_URL = (
        "https://api.football-data.org/v4"
    )

    def __init__(
        self,
        *,
        competition_code: str = "PL",
        season: int = 2026,
        timeout_seconds: int = 30,
    ):

        self.competition_code = (
            str(
                competition_code
            )
            .strip()
            .upper()
        )

        self.season = int(
            season
        )

        self.timeout_seconds = int(
            timeout_seconds
        )

    def _request_json(
        self,
        url: str,
    ) -> dict:

        api_key = (
            get_football_data_api_key()
        )

        request = Request(
            url,
            method="GET",
            headers={
                "X-Auth-Token":
                    api_key,

                "Accept":
                    "application/json",

                "User-Agent":
                    "FixtureIQ/Stage8",
            },
        )

        try:

            with urlopen(
                request,
                timeout=self.timeout_seconds,
            ) as response:

                raw = response.read()

                status_code = int(
                    getattr(
                        response,
                        "status",
                        200,
                    )
                )

        except HTTPError as exc:

            try:

                body = (
                    exc.read()
                    .decode(
                        "utf-8",
                        errors="replace",
                    )
                )

            except Exception:

                body = ""

            raise FootballDataStandingsError(
                (
                    "football-data.org HTTP error "
                    f"{exc.code}. "
                    f"Response: {body[:500]}"
                )
            ) from exc

        except URLError as exc:

            raise FootballDataStandingsError(
                (
                    "football-data.org connection failed: "
                    f"{exc.reason}"
                )
            ) from exc

        except TimeoutError as exc:

            raise FootballDataStandingsError(
                "football-data.org request timed out."
            ) from exc

        if status_code != 200:

            raise FootballDataStandingsError(
                (
                    "football-data.org returned unexpected "
                    f"HTTP status {status_code}."
                )
            )

        try:

            payload = json.loads(
                raw.decode(
                    "utf-8"
                )
            )

        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:

            raise FootballDataStandingsError(
                (
                    "football-data.org returned "
                    "invalid JSON."
                )
            ) from exc

        if not isinstance(
            payload,
            dict,
        ):

            raise FootballDataStandingsError(
                (
                    "football-data.org standings response "
                    "must be a JSON object."
                )
            )

        return payload

    def fetch_standings(
        self,
    ) -> dict:

        query = urlencode(
            {
                "season":
                    self.season,
            }
        )

        url = (
            f"{self.BASE_URL}"
            f"/competitions/"
            f"{self.competition_code}"
            f"/standings?"
            f"{query}"
        )

        fetched_at_utc = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        payload = (
            self._request_json(
                url
            )
        )

        # ====================================================
        # Competition validation
        # ====================================================

        competition = payload.get(
            "competition",
            {}
        )

        if not isinstance(
            competition,
            dict,
        ):

            raise FootballDataStandingsError(
                "Competition metadata is missing."
            )

        provider_code = (
            str(
                competition.get(
                    "code",
                    ""
                )
            )
            .strip()
            .upper()
        )

        if (
            provider_code
            != self.competition_code
        ):

            raise FootballDataStandingsError(
                (
                    "Competition mismatch. "
                    f"Expected {self.competition_code}, "
                    f"received {provider_code!r}."
                )
            )

        # ====================================================
        # Season validation
        # ====================================================

        season_meta = payload.get(
            "season",
            {}
        )

        if not isinstance(
            season_meta,
            dict,
        ):

            raise FootballDataStandingsError(
                "Season metadata is missing."
            )

        filters = payload.get(
            "filters",
            {}
        )

        response_season = None

        if isinstance(
            filters,
            dict,
        ):

            response_season = (
                filters.get(
                    "season"
                )
            )

        if (
            response_season
            is not None
            and
            str(
                response_season
            )
            != str(
                self.season
            )
        ):

            raise FootballDataStandingsError(
                (
                    "Season mismatch. "
                    f"Requested {self.season}, "
                    f"received {response_season}."
                )
            )

        # ====================================================
        # Find TOTAL standings table
        # ====================================================

        standings_blocks = payload.get(
            "standings"
        )

        if not isinstance(
            standings_blocks,
            list,
        ):

            raise FootballDataStandingsError(
                "Standings array is missing."
            )

        total_block = None

        for block in standings_blocks:

            if not isinstance(
                block,
                dict,
            ):

                continue

            if (
                str(
                    block.get(
                        "type",
                        ""
                    )
                )
                .strip()
                .upper()
                == "TOTAL"
            ):

                total_block = block

                break

        if total_block is None:

            raise FootballDataStandingsError(
                (
                    "TOTAL Premier League standings "
                    "table was not returned."
                )
            )

        table = total_block.get(
            "table"
        )

        if not isinstance(
            table,
            list,
        ):

            raise FootballDataStandingsError(
                (
                    "TOTAL standings block has "
                    "no valid table."
                )
            )

        if len(
            table
        ) != 20:

            raise FootballDataStandingsError(
                (
                    "Expected exactly 20 EPL teams, "
                    f"received {len(table)}."
                )
            )

        # ====================================================
        # Extract provider-native rows
        # ====================================================

        rows = []

        for row in table:

            if not isinstance(
                row,
                dict,
            ):

                raise FootballDataStandingsError(
                    (
                        "Invalid standings row "
                        "returned by provider."
                    )
                )

            team = row.get(
                "team",
                {}
            )

            if not isinstance(
                team,
                dict,
            ):

                raise FootballDataStandingsError(
                    (
                        "Standings row missing "
                        "team metadata."
                    )
                )

            provider_team_id = (
                team.get(
                    "id"
                )
            )

            provider_team_name = (
                str(
                    team.get(
                        "name",
                        ""
                    )
                )
                .strip()
            )

            if (
                provider_team_id
                is None
                or
                not provider_team_name
            ):

                raise FootballDataStandingsError(
                    (
                        "Provider team ID/name "
                        "is missing."
                    )
                )

            try:

                extracted = {

                    "provider_team_id":
                        int(
                            provider_team_id
                        ),

                    "provider_team_name":
                        provider_team_name,

                    "provider_short_name":
                        (
                            str(
                                team.get(
                                    "shortName",
                                    ""
                                )
                            )
                            .strip()
                        ),

                    "provider_tla":
                        (
                            str(
                                team.get(
                                    "tla",
                                    ""
                                )
                            )
                            .strip()
                            .upper()
                        ),

                    "position":
                        int(
                            row[
                                "position"
                            ]
                        ),

                    "played":
                        int(
                            row[
                                "playedGames"
                            ]
                        ),

                    "won":
                        int(
                            row[
                                "won"
                            ]
                        ),

                    "drawn":
                        int(
                            row[
                                "draw"
                            ]
                        ),

                    "lost":
                        int(
                            row[
                                "lost"
                            ]
                        ),

                    "goals_for":
                        int(
                            row[
                                "goalsFor"
                            ]
                        ),

                    "goals_against":
                        int(
                            row[
                                "goalsAgainst"
                            ]
                        ),

                    "goal_difference":
                        int(
                            row[
                                "goalDifference"
                            ]
                        ),

                    "points":
                        int(
                            row[
                                "points"
                            ]
                        ),
                }

            except (
                KeyError,
                TypeError,
                ValueError,
            ) as exc:

                raise FootballDataStandingsError(
                    (
                        "Standings row contains "
                        "invalid numeric fields for "
                        f"{provider_team_name}."
                    )
                ) from exc

            rows.append(
                extracted
            )

        # ====================================================
        # Provider-level uniqueness
        # ====================================================

        provider_ids = [
            row[
                "provider_team_id"
            ]
            for row in rows
        ]

        provider_names = [
            row[
                "provider_team_name"
            ]
            for row in rows
        ]

        positions = [
            row[
                "position"
            ]
            for row in rows
        ]

        if (
            len(
                set(
                    provider_ids
                )
            )
            != 20
        ):

            raise FootballDataStandingsError(
                "Provider team IDs are not unique."
            )

        if (
            len(
                {
                    name.casefold()
                    for name in provider_names
                }
            )
            != 20
        ):

            raise FootballDataStandingsError(
                (
                    "Provider team names "
                    "are not unique."
                )
            )

        if (
            sorted(
                positions
            )
            != list(
                range(
                    1,
                    21,
                )
            )
        ):

            raise FootballDataStandingsError(
                (
                    "Standings positions must "
                    "be exactly 1 through 20."
                )
            )

        source_as_of_utc = (
            competition.get(
                "lastUpdated"
            )
            or
            fetched_at_utc
        )

        return {

            "provider":
                "football-data.org",

            "competition":
                competition.get(
                    "name",
                    "Premier League",
                ),

            "competition_code":
                provider_code,

            "configured_season":
                self.season,

            "provider_season_id":
                season_meta.get(
                    "id"
                ),

            "season_start_date":
                season_meta.get(
                    "startDate"
                ),

            "season_end_date":
                season_meta.get(
                    "endDate"
                ),

            "current_matchday":
                season_meta.get(
                    "currentMatchday"
                ),

            "stage":
                total_block.get(
                    "stage"
                ),

            "standings_type":
                total_block.get(
                    "type"
                ),

            "fetched_at_utc":
                fetched_at_utc,

            "source_as_of_utc":
                source_as_of_utc,

            "row_count":
                len(
                    rows
                ),

            "rows":
                rows,
        }
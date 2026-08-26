"""
FixtureIQ backend configuration.

Loads API-Football configuration from environment variables.
Secrets must never be hardcoded in source code.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


# -------------------------------------------------
# Project root
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]


# -------------------------------------------------
# Load .env
# -------------------------------------------------

ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


# -------------------------------------------------
# API-Football configuration
# -------------------------------------------------

API_FOOTBALL_KEY = os.getenv(
    "API_FOOTBALL_KEY"
)

API_FOOTBALL_BASE_URL = os.getenv(
    "API_FOOTBALL_BASE_URL",
    "https://v3.football.api-sports.io"
).rstrip("/")


API_FOOTBALL_LEAGUE_ID = int(
    os.getenv(
        "API_FOOTBALL_LEAGUE_ID",
        "39"
    )
)


API_FOOTBALL_SEASON = int(
    os.getenv(
        "API_FOOTBALL_SEASON",
        "2026"
    )
)


API_FOOTBALL_TIMEOUT = int(
    os.getenv(
        "API_FOOTBALL_TIMEOUT",
        "15"
    )
)


# -------------------------------------------------
# Configuration validation
# -------------------------------------------------

def validate_config():
    """
    Validate required FixtureIQ backend configuration.
    """

    if not API_FOOTBALL_KEY:

        raise RuntimeError(
            "API_FOOTBALL_KEY is not configured. "
            "Add it to the project .env file."
        )


    if not API_FOOTBALL_BASE_URL:

        raise RuntimeError(
            "API_FOOTBALL_BASE_URL is not configured."
        )


    if API_FOOTBALL_LEAGUE_ID <= 0:

        raise RuntimeError(
            "API_FOOTBALL_LEAGUE_ID must be a positive integer."
        )


    if API_FOOTBALL_SEASON < 2000:

        raise RuntimeError(
            "API_FOOTBALL_SEASON appears to be invalid."
        )


    if API_FOOTBALL_TIMEOUT <= 0:

        raise RuntimeError(
            "API_FOOTBALL_TIMEOUT must be greater than zero."
        )


    return True


# -------------------------------------------------
# Safe configuration summary
# -------------------------------------------------

def get_config_summary():
    """
    Return configuration information that is safe to log.

    The API key itself is deliberately excluded.
    """

    return {

        "api_provider":
            "API-Football",

        "base_url":
            API_FOOTBALL_BASE_URL,

        "league_id":
            API_FOOTBALL_LEAGUE_ID,

        "season":
            API_FOOTBALL_SEASON,

        "timeout":
            API_FOOTBALL_TIMEOUT,

        "api_key_configured":
            bool(API_FOOTBALL_KEY)

    }
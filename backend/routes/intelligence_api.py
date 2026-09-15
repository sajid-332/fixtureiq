"""
FixtureIQ Stage 9.6
Match Intelligence REST API.

Read-only artifact-serving routes.

Runtime freshness / cache hardening belongs to Stage 9.7.
"""

from __future__ import annotations

from flask import (
    Blueprint,
    jsonify,
)

from backend.services.match_intelligence_service import (
    MatchIntelligenceNotFoundError,
    MatchIntelligenceNotReadyError,
    MatchIntelligenceService,
)


# ============================================================
# Blueprint
# ============================================================

intelligence_api_bp = Blueprint(
    "intelligence_api",
    __name__,
)


# ============================================================
# Response helpers
# ============================================================

def _not_ready_response():

    return (

        jsonify(
            {
                "status":
                    "NOT_READY",

                "service":
                    "match_intelligence",
            }
        ),

        503,
    )


def _not_found_response():

    return (

        jsonify(
            {
                "status":
                    "NOT_FOUND",

                "service":
                    "match_intelligence",
            }
        ),

        404,
    )


# ============================================================
# Status
# ============================================================

@intelligence_api_bp.route(
    "/api/v1/intelligence/status",
    methods=["GET"],
)
def intelligence_status():

    service = (
        MatchIntelligenceService()
    )

    status = service.get_status()

    if (
        status.get(
            "status"
        )
        != "READY"
    ):

        return _not_ready_response()

    return jsonify(
        status
    )


# ============================================================
# All matches
# ============================================================

@intelligence_api_bp.route(
    "/api/v1/intelligence/matches",
    methods=["GET"],
)
def intelligence_matches():

    service = (
        MatchIntelligenceService()
    )

    try:

        matches = (
            service.get_all_matches()
        )

    except MatchIntelligenceNotReadyError:

        return _not_ready_response()

    return jsonify(
        {
            "status":
                "READY",

            "service":
                "match_intelligence",

            "count":
                len(
                    matches
                ),

            "matches":
                matches,
        }
    )


# ============================================================
# One fixture
# ============================================================

@intelligence_api_bp.route(
    "/api/v1/intelligence/matches/<fixture_id>",
    methods=["GET"],
)
def intelligence_match(
    fixture_id: str,
):

    service = (
        MatchIntelligenceService()
    )

    try:

        match = (
            service.get_match(
                fixture_id
            )
        )

    except MatchIntelligenceNotReadyError:

        return _not_ready_response()

    except MatchIntelligenceNotFoundError:

        return _not_found_response()

    return jsonify(
        {
            "status":
                "READY",

            "service":
                "match_intelligence",

            "match":
                match,
        }
    )


# ============================================================
# Team fixtures
# ============================================================

@intelligence_api_bp.route(
    "/api/v1/intelligence/team/<path:team_name>",
    methods=["GET"],
)
def intelligence_team(
    team_name: str,
):

    service = (
        MatchIntelligenceService()
    )

    try:

        matches = (
            service.get_team_matches(
                team_name
            )
        )

    except MatchIntelligenceNotReadyError:

        return _not_ready_response()

    except MatchIntelligenceNotFoundError:

        return _not_found_response()

    return jsonify(
        {
            "status":
                "READY",

            "service":
                "match_intelligence",

            "team":
                team_name,

            "count":
                len(
                    matches
                ),

            "matches":
                matches,
        }
    )


# ============================================================
# Upcoming intelligence
# ============================================================

@intelligence_api_bp.route(
    "/api/v1/intelligence/upcoming",
    methods=["GET"],
)
def intelligence_upcoming():

    service = (
        MatchIntelligenceService()
    )

    try:

        matches = (
            service.get_upcoming()
        )

    except MatchIntelligenceNotReadyError:

        return _not_ready_response()

    return jsonify(
        {
            "status":
                "READY",

            "service":
                "match_intelligence",

            "count":
                len(
                    matches
                ),

            "matches":
                matches,
        }
    )
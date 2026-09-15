"""
FixtureIQ Stage 9.7
Runtime-Safe Match Intelligence REST API.

Healthy:
    200 READY

Unknown identity:
    404 NOT_FOUND

Stale / invalid dependency / crossed temporal boundary:
    503 NOT_READY

Write methods:
    405

All intelligence responses:
    Cache-Control: no-store
"""

from __future__ import annotations

from flask import (
    Blueprint,
    jsonify,
    request,
)

from backend.services.match_intelligence_service import (
    MatchIntelligenceNotFoundError,
    MatchIntelligenceNotReadyError,
    MatchIntelligenceService,
)


intelligence_api_bp = Blueprint(
    "intelligence_api",
    __name__,
)


# ============================================================
# No-store policy
# ============================================================

@intelligence_api_bp.after_app_request
def intelligence_no_store(
    response,
):

    if request.path.startswith(
        "/api/v1/intelligence"
    ):

        response.headers[
            "Cache-Control"
        ] = (
            "no-store, no-cache, "
            "must-revalidate, max-age=0"
        )

        response.headers[
            "Pragma"
        ] = "no-cache"

        response.headers[
            "Expires"
        ] = "0"

    return response


# ============================================================
# Public error responses
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
# Fixture
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

        match = service.get_match(
            fixture_id
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
# Team
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
# Upcoming
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

        matches = service.get_upcoming()

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
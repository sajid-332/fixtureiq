"""
FixtureIQ Stage 8.6
Read-Only Context REST API.

Public context endpoints:
- GET /api/v1/context/status

- GET /api/v1/context/standings
- GET /api/v1/context/standings/<team_name>

- GET /api/v1/context/form
- GET /api/v1/context/form/<team_name>

- GET /api/v1/context/teams
- GET /api/v1/context/teams/<team_name>

- GET /api/v1/context/fixtures
- GET /api/v1/context/fixtures/<fixture_id>
- GET /api/v1/context/fixtures/team/<team_name>

Rules:
- read only
- no provider fetch
- no rebuild
- no model execution
- no prediction mutation
- service NOT_READY -> HTTP 503
- unknown resource -> HTTP 404
- public payloads only
"""

from __future__ import annotations

from flask import (
    Blueprint,
    jsonify,
)

from backend.services.standings_service import (
    StandingsService,
)

from backend.services.team_form_service import (
    TeamFormService,
)

from backend.services.team_context_service import (
    TeamContextService,
)

from backend.services.fixture_context_service import (
    FixtureContextService,
)


# ============================================================
# Blueprint
# ============================================================

context_api_bp = Blueprint(
    "context_api",
    __name__,
    url_prefix="/api/v1/context",
)


# ============================================================
# Public contract
# ============================================================

CONTEXT_API_VERSION = "v1"

CONTEXT_API_STAGE = "8.6"

PUBLIC_ROUTES = [

    "/api/v1/context/status",

    "/api/v1/context/standings",
    "/api/v1/context/standings/<path:team_name>",

    "/api/v1/context/form",
    "/api/v1/context/form/<path:team_name>",

    "/api/v1/context/teams",
    "/api/v1/context/teams/<path:team_name>",

    "/api/v1/context/fixtures",
    "/api/v1/context/fixtures/<fixture_id>",
    "/api/v1/context/fixtures/team/<path:team_name>",
]


# ============================================================
# Helpers
# ============================================================

def _not_ready_response(
    service_name: str,
):

    return (
        jsonify(
            {
                "status":
                    "NOT_READY",

                "service":
                    service_name,
            }
        ),
        503,
    )


def _not_found_response(
    resource: str,
):

    return (
        jsonify(
            {
                "status":
                    "NOT_FOUND",

                "resource":
                    resource,
            }
        ),
        404,
    )


def _public_status(
    status: dict,
) -> dict:

    allowed_fields = [

        "status",
        "stage",
        "service",
        "season",

        "team_count",
        "fixture_count",

        "column_count",
        "source_column_count",
        "context_column_count",

        "generated_at_utc",
        "source_as_of_utc",

        "fixture_snapshot_as_of_utc",
        "team_context_source_as_of_utc",

        "earliest_fixture_kickoff_utc",
        "latest_fixture_kickoff_utc",

        "freshness_mode",
    ]

    return {

        field:
            status[field]

        for field in allowed_fields

        if field in status
    }


def _ready(
    service,
) -> tuple[
    bool,
    dict,
]:

    status = service.get_status()

    return (
        status.get(
            "status"
        )
        == "READY",
        status,
    )


# ============================================================
# Overall status
# ============================================================

@context_api_bp.route(
    "/status",
    methods=["GET"],
)
def context_status():

    standings_service = (
        StandingsService()
    )

    form_service = (
        TeamFormService()
    )

    team_context_service = (
        TeamContextService()
    )

    fixture_context_service = (
        FixtureContextService()
    )

    services = {

        "standings":
            standings_service,

        "team_form":
            form_service,

        "team_context":
            team_context_service,

        "fixture_context":
            fixture_context_service,
    }

    layers = {}

    all_ready = True

    for name, service in services.items():

        status = (
            service.get_status()
        )

        public_status = (
            _public_status(
                status
            )
        )

        layers[
            name
        ] = public_status

        if (
            status.get(
                "status"
            )
            != "READY"
        ):

            all_ready = False

    payload = {

        "status":
            (
                "READY"
                if all_ready
                else "NOT_READY"
            ),

        "api":
            "fixtureiq_context",

        "version":
            CONTEXT_API_VERSION,

        "stage":
            CONTEXT_API_STAGE,

        "read_only":
            True,

        "layers":
            layers,
    }

    return (
        jsonify(
            payload
        ),
        (
            200
            if all_ready
            else 503
        ),
    )


# ============================================================
# Standings
# ============================================================

@context_api_bp.route(
    "/standings",
    methods=["GET"],
)
def standings_all():

    service = (
        StandingsService()
    )

    ready, status = _ready(
        service
    )

    if not ready:

        return _not_ready_response(
            "standings"
        )

    rows = (
        service.get_standings()
    )

    return jsonify(
        {
            "status":
                "READY",

            "resource":
                "standings",

            "season":
                status.get(
                    "season",
                    2026,
                ),

            "count":
                len(rows),

            "data":
                rows,
        }
    )


@context_api_bp.route(
    "/standings/<path:team_name>",
    methods=["GET"],
)
def standings_team(
    team_name: str,
):

    service = (
        StandingsService()
    )

    ready, _ = _ready(
        service
    )

    if not ready:

        return _not_ready_response(
            "standings"
        )

    row = (
        service.get_team_standing(
            team_name
        )
    )

    if row is None:

        return _not_found_response(
            "team_standing"
        )

    return jsonify(
        {
            "status":
                "READY",

            "resource":
                "team_standing",

            "data":
                row,
        }
    )


# ============================================================
# Team form
# ============================================================

@context_api_bp.route(
    "/form",
    methods=["GET"],
)
def form_all():

    service = (
        TeamFormService()
    )

    ready, status = _ready(
        service
    )

    if not ready:

        return _not_ready_response(
            "team_form"
        )

    rows = (
        service.get_all_team_form()
    )

    return jsonify(
        {
            "status":
                "READY",

            "resource":
                "team_form",

            "season":
                status.get(
                    "season",
                    2026,
                ),

            "count":
                len(rows),

            "data":
                rows,
        }
    )


@context_api_bp.route(
    "/form/<path:team_name>",
    methods=["GET"],
)
def form_team(
    team_name: str,
):

    service = (
        TeamFormService()
    )

    ready, _ = _ready(
        service
    )

    if not ready:

        return _not_ready_response(
            "team_form"
        )

    row = (
        service.get_team_form(
            team_name
        )
    )

    if row is None:

        return _not_found_response(
            "team_form"
        )

    return jsonify(
        {
            "status":
                "READY",

            "resource":
                "team_form",

            "data":
                row,
        }
    )


# ============================================================
# Unified team context
# ============================================================

@context_api_bp.route(
    "/teams",
    methods=["GET"],
)
def teams_all():

    service = (
        TeamContextService()
    )

    ready, status = _ready(
        service
    )

    if not ready:

        return _not_ready_response(
            "team_context"
        )

    rows = (
        service.get_all_team_context()
    )

    return jsonify(
        {
            "status":
                "READY",

            "resource":
                "team_context",

            "season":
                status.get(
                    "season",
                    2026,
                ),

            "count":
                len(rows),

            "data":
                rows,
        }
    )


@context_api_bp.route(
    "/teams/<path:team_name>",
    methods=["GET"],
)
def teams_team(
    team_name: str,
):

    service = (
        TeamContextService()
    )

    ready, _ = _ready(
        service
    )

    if not ready:

        return _not_ready_response(
            "team_context"
        )

    row = (
        service.get_team_context(
            team_name
        )
    )

    if row is None:

        return _not_found_response(
            "team_context"
        )

    return jsonify(
        {
            "status":
                "READY",

            "resource":
                "team_context",

            "data":
                row,
        }
    )


# ============================================================
# Fixture context
# ============================================================

@context_api_bp.route(
    "/fixtures",
    methods=["GET"],
)
def fixtures_all():

    service = (
        FixtureContextService()
    )

    ready, status = _ready(
        service
    )

    if not ready:

        return _not_ready_response(
            "fixture_context"
        )

    rows = (
        service.get_all_fixture_context()
    )

    return jsonify(
        {
            "status":
                "READY",

            "resource":
                "fixture_context",

            "season":
                status.get(
                    "season",
                    2026,
                ),

            "count":
                len(rows),

            "data":
                rows,
        }
    )


@context_api_bp.route(
    "/fixtures/team/<path:team_name>",
    methods=["GET"],
)
def fixtures_team(
    team_name: str,
):

    service = (
        FixtureContextService()
    )

    ready, _ = _ready(
        service
    )

    if not ready:

        return _not_ready_response(
            "fixture_context"
        )

    rows = (
        service.get_team_fixtures(
            team_name
        )
    )

    if not rows:

        return _not_found_response(
            "team_fixtures"
        )

    return jsonify(
        {
            "status":
                "READY",

            "resource":
                "team_fixtures",

            "team_name":
                team_name,

            "count":
                len(rows),

            "data":
                rows,
        }
    )


@context_api_bp.route(
    "/fixtures/<fixture_id>",
    methods=["GET"],
)
def fixtures_one(
    fixture_id: str,
):

    service = (
        FixtureContextService()
    )

    ready, _ = _ready(
        service
    )

    if not ready:

        return _not_ready_response(
            "fixture_context"
        )

    row = (
        service.get_fixture_context(
            fixture_id
        )
    )

    if row is None:

        return _not_found_response(
            "fixture_context"
        )

    return jsonify(
        {
            "status":
                "READY",

            "resource":
                "fixture_context",

            "data":
                row,
        }
    )
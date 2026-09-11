"""
FixtureIQ Stage 8.6
Context REST API Verification.

Verifies:
8.6.1 Public API contract
8.6.2 Context REST blueprint
8.6.3 Flask integration
8.6.4 Independent HTTP behavior
8.6.5 Final Stage 8.6 gate

Creates:
data/processed/context/context_api_verification.json

No provider fetch.
No model execution.
No Stage 7 writes.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote


# ============================================================
# Project root
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(BASE_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(BASE_DIR),
    )


# ============================================================
# Imports
# ============================================================

from backend.app import app

from backend.routes.context_api import (
    CONTEXT_API_STAGE,
    CONTEXT_API_VERSION,
    PUBLIC_ROUTES,
)

from backend.services.fixture_context_service import (
    FixtureContextService,
)

from backend.services.standings_service import (
    StandingsService,
)

from backend.services.team_context_service import (
    TeamContextService,
)

from backend.services.team_form_service import (
    TeamFormService,
)


# ============================================================
# Paths
# ============================================================

CONTEXT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "context"
)

PRODUCTION_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "production"
)


CONTRACT_FILE = (
    CONTEXT_DIR
    / "stage8_context_contract.json"
)

CONTRACT_VERIFICATION_FILE = (
    CONTEXT_DIR
    / "stage8_context_contract_verification.json"
)

STANDINGS_FILE = (
    CONTEXT_DIR
    / "current_standings.csv"
)

STANDINGS_REPORT_FILE = (
    CONTEXT_DIR
    / "standings_report.json"
)

TEAM_FORM_FILE = (
    CONTEXT_DIR
    / "current_team_form.csv"
)

TEAM_FORM_REPORT_FILE = (
    CONTEXT_DIR
    / "team_form_report.json"
)

TEAM_CONTEXT_FILE = (
    CONTEXT_DIR
    / "team_context.csv"
)

TEAM_CONTEXT_REPORT_FILE = (
    CONTEXT_DIR
    / "team_context_report.json"
)

ENRICHED_FIXTURES_FILE = (
    CONTEXT_DIR
    / "enriched_upcoming_fixtures.csv"
)

FIXTURE_CONTEXT_REPORT_FILE = (
    CONTEXT_DIR
    / "fixture_context_report.json"
)

OUTPUT_FILE = (
    CONTEXT_DIR
    / "context_api_verification.json"
)


# ============================================================
# Helpers
# ============================================================

def load_json(
    path: Path,
) -> dict:

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def save_json(
    path: Path,
    payload: dict,
) -> None:

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=2,
        )


def sha256_file(
    path: Path,
) -> str:

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as file:

        while True:

            chunk = file.read(
                1024 * 1024
            )

            if not chunk:

                break

            digest.update(chunk)

    return digest.hexdigest()


def check(
    label: str,
    condition,
    failures: list[str],
) -> bool:

    passed = bool(condition)

    print(
        f"{label}: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    if not passed:

        failures.append(label)

    return passed


def relative_path(
    path: Path,
) -> str:

    return (
        str(
            path.relative_to(
                BASE_DIR
            )
        )
        .replace(
            "\\",
            "/",
        )
    )


def contains_forbidden_public_key(
    value,
) -> bool:

    forbidden = {

        "sha256",
        "dependency_identity",
        "evidence_sha256",
        "safety",
        "failures",
        "model_sha256",
        "artifact_sha256",
    }

    if isinstance(
        value,
        dict,
    ):

        for key, child in value.items():

            if key in forbidden:

                return True

            if contains_forbidden_public_key(
                child
            ):

                return True

    elif isinstance(
        value,
        list,
    ):

        for child in value:

            if contains_forbidden_public_key(
                child
            ):

                return True

    return False


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.6"
    )

    print(
        "Context REST API Verification"
    )

    print("=" * 72)

    failures = []

    # ========================================================
    # 1. Foundation
    # ========================================================

    print(
        "\n1. STAGE FOUNDATION"
    )

    required = [

        CONTRACT_FILE,
        CONTRACT_VERIFICATION_FILE,

        STANDINGS_FILE,
        STANDINGS_REPORT_FILE,

        TEAM_FORM_FILE,
        TEAM_FORM_REPORT_FILE,

        TEAM_CONTEXT_FILE,
        TEAM_CONTEXT_REPORT_FILE,

        ENRICHED_FIXTURES_FILE,
        FIXTURE_CONTEXT_REPORT_FILE,
    ]

    for path in required:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        sys.exit(1)

    contract = load_json(
        CONTRACT_FILE
    )

    standings_report = load_json(
        STANDINGS_REPORT_FILE
    )

    form_report = load_json(
        TEAM_FORM_REPORT_FILE
    )

    team_context_report = load_json(
        TEAM_CONTEXT_REPORT_FILE
    )

    fixture_context_report = load_json(
        FIXTURE_CONTEXT_REPORT_FILE
    )

    check(
        "Stage 8.1 COMPLETE",
        contract.get(
            "stage_8_1_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 8.2 COMPLETE",
        standings_report.get(
            "stage_8_2_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 8.3 COMPLETE",
        form_report.get(
            "stage_8_3_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 8.4 COMPLETE",
        team_context_report.get(
            "stage_8_4_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 8.5 COMPLETE",
        fixture_context_report.get(
            "stage_8_5_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 8.5 layer VERIFIED",
        fixture_context_report.get(
            "fixture_context_enrichment_layer"
        )
        == "VERIFIED",
        failures,
    )

    # ========================================================
    # 2. Output contract
    # ========================================================

    print(
        "\n2. STAGE 8.6 OUTPUT CONTRACT"
    )

    output_contract = contract.get(
        "output_artifact_contract",
        {}
    )

    outputs = output_contract.get(
        "outputs",
        {}
    )

    check(
        "context_api_verification path locked",
        outputs.get(
            "context_api_verification",
            {}
        ).get(
            "path"
        )
        ==
        relative_path(
            OUTPUT_FILE
        ),
        failures,
    )

    check(
        "Stage 7 writes prohibited",
        output_contract.get(
            "stage7_output_write_allowed"
        )
        is False,
        failures,
    )

    # ========================================================
    # 3. Service readiness
    # ========================================================

    print(
        "\n3. SERVICE READINESS"
    )

    services = {

        "standings":
            StandingsService(),

        "team_form":
            TeamFormService(),

        "team_context":
            TeamContextService(),

        "fixture_context":
            FixtureContextService(),
    }

    service_statuses = {}

    for name, service in services.items():

        status = service.get_status()

        service_statuses[
            name
        ] = status

        if (
            status.get(
                "status"
            )
            != "READY"
        ):

            print(
                f"{name} reason:",
                status.get(
                    "reason"
                ),
            )

        check(
            f"{name} READY",
            status.get(
                "status"
            )
            == "READY",
            failures,
        )

    # ========================================================
    # 4. Flask route registration
    # ========================================================

    print(
        "\n4. FLASK ROUTE REGISTRATION"
    )

    registered_routes = {}

    for rule in app.url_map.iter_rules():

        rule_text = str(rule)

        if rule_text.startswith(
            "/api/v1/context"
        ):

            registered_routes[
                rule_text
            ] = sorted(
                method

                for method in rule.methods

                if method not in {
                    "HEAD",
                    "OPTIONS",
                }
            )

    expected_routes = {

        route:
            ["GET"]

        for route in PUBLIC_ROUTES
    }

    check(
        "Exactly 10 public context routes",
        len(
            registered_routes
        )
        == 10,
        failures,
    )

    check(
        "Public route contract exact",
        registered_routes
        ==
        expected_routes,
        failures,
    )

    check(
        "API version = v1",
        CONTEXT_API_VERSION
        == "v1",
        failures,
    )

    check(
        "API stage = 8.6",
        CONTEXT_API_STAGE
        == "8.6",
        failures,
    )

    # ========================================================
    # 5. HTTP test client
    # ========================================================

    print(
        "\n5. HTTP CONTRACT"
    )

    client = app.test_client()

    status_response = client.get(
        "/api/v1/context/status"
    )

    status_payload = (
        status_response.get_json()
    )

    check(
        "GET /context/status -> 200",
        status_response.status_code
        == 200,
        failures,
    )

    check(
        "Overall context API READY",
        status_payload.get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "Context API read-only",
        status_payload.get(
            "read_only"
        )
        is True,
        failures,
    )

    check(
        "Four context layers exposed",
        set(
            status_payload.get(
                "layers",
                {}
            ).keys()
        )
        ==
        {
            "standings",
            "team_form",
            "team_context",
            "fixture_context",
        },
        failures,
    )

    check(
        "No private status fields exposed",
        not contains_forbidden_public_key(
            status_payload
        ),
        failures,
    )

    # ========================================================
    # 6. Standings API
    # ========================================================

    print(
        "\n6. STANDINGS API"
    )

    response = client.get(
        "/api/v1/context/standings"
    )

    payload = response.get_json()

    check(
        "GET standings -> 200",
        response.status_code
        == 200,
        failures,
    )

    check(
        "Standings count = 20",
        payload.get(
            "count"
        )
        == 20,
        failures,
    )

    standings_data = payload.get(
        "data",
        []
    )

    check(
        "Standings data has 20 rows",
        len(
            standings_data
        )
        == 20,
        failures,
    )

    check(
        "Standings payload public-only",
        not contains_forbidden_public_key(
            payload
        ),
        failures,
    )

    first_team = standings_data[
        0
    ][
        "team_name"
    ]

    encoded_team = quote(
        first_team,
        safe="",
    )

    response = client.get(
        f"/api/v1/context/standings/{encoded_team}"
    )

    check(
        "Single standing lookup -> 200",
        response.status_code
        == 200,
        failures,
    )

    response = client.get(
        "/api/v1/context/standings/Definitely%20Not%20A%20Team"
    )

    check(
        "Unknown standing -> 404",
        response.status_code
        == 404,
        failures,
    )

    # ========================================================
    # 7. Form API
    # ========================================================

    print(
        "\n7. TEAM FORM API"
    )

    response = client.get(
        "/api/v1/context/form"
    )

    payload = response.get_json()

    check(
        "GET form -> 200",
        response.status_code
        == 200,
        failures,
    )

    check(
        "Form count = 20",
        payload.get(
            "count"
        )
        == 20,
        failures,
    )

    check(
        "Form payload public-only",
        not contains_forbidden_public_key(
            payload
        ),
        failures,
    )

    response = client.get(
        f"/api/v1/context/form/{encoded_team}"
    )

    check(
        "Single form lookup -> 200",
        response.status_code
        == 200,
        failures,
    )

    response = client.get(
        "/api/v1/context/form/Definitely%20Not%20A%20Team"
    )

    check(
        "Unknown form team -> 404",
        response.status_code
        == 404,
        failures,
    )

    # ========================================================
    # 8. Unified team context API
    # ========================================================

    print(
        "\n8. UNIFIED TEAM CONTEXT API"
    )

    response = client.get(
        "/api/v1/context/teams"
    )

    payload = response.get_json()

    check(
        "GET teams -> 200",
        response.status_code
        == 200,
        failures,
    )

    check(
        "Team context count = 20",
        payload.get(
            "count"
        )
        == 20,
        failures,
    )

    team_data = payload.get(
        "data",
        []
    )

    check(
        "Team context rows have 38 fields",
        all(
            len(row)
            == 38
            for row in team_data
        ),
        failures,
    )

    check(
        "Team context payload public-only",
        not contains_forbidden_public_key(
            payload
        ),
        failures,
    )

    response = client.get(
        f"/api/v1/context/teams/{encoded_team}"
    )

    check(
        "Single team context -> 200",
        response.status_code
        == 200,
        failures,
    )

    response = client.get(
        "/api/v1/context/teams/Definitely%20Not%20A%20Team"
    )

    check(
        "Unknown team context -> 404",
        response.status_code
        == 404,
        failures,
    )

    # ========================================================
    # 9. Fixture context API
    # ========================================================

    print(
        "\n9. FIXTURE CONTEXT API"
    )

    response = client.get(
        "/api/v1/context/fixtures"
    )

    payload = response.get_json()

    check(
        "GET fixtures -> 200",
        response.status_code
        == 200,
        failures,
    )

    fixture_count = payload.get(
        "count",
        0,
    )

    check(
        "Fixture count > 0",
        fixture_count
        > 0,
        failures,
    )

    fixture_data = payload.get(
        "data",
        []
    )

    check(
        "Fixture data count exact",
        len(
            fixture_data
        )
        == fixture_count,
        failures,
    )

    check(
        "Fixture payload public-only",
        not contains_forbidden_public_key(
            payload
        ),
        failures,
    )

    first_fixture = fixture_data[
        0
    ]

    fixture_id = str(
        first_fixture[
            "fixture_id"
        ]
    )

    encoded_fixture_id = quote(
        fixture_id,
        safe="",
    )

    response = client.get(
        (
            "/api/v1/context/fixtures/"
            f"{encoded_fixture_id}"
        )
    )

    check(
        "Single fixture context -> 200",
        response.status_code
        == 200,
        failures,
    )

    fixture_team = (
        first_fixture[
            "home_team_name"
        ]
    )

    encoded_fixture_team = quote(
        fixture_team,
        safe="",
    )

    response = client.get(
        (
            "/api/v1/context/fixtures/team/"
            f"{encoded_fixture_team}"
        )
    )

    team_fixture_payload = (
        response.get_json()
    )

    check(
        "Team fixture lookup -> 200",
        response.status_code
        == 200,
        failures,
    )

    check(
        "Team fixture list non-empty",
        team_fixture_payload.get(
            "count",
            0
        )
        > 0,
        failures,
    )

    response = client.get(
        (
            "/api/v1/context/fixtures/"
            "fixtureiq-does-not-exist"
        )
    )

    check(
        "Unknown fixture -> 404",
        response.status_code
        == 404,
        failures,
    )

    response = client.get(
        (
            "/api/v1/context/fixtures/team/"
            "Definitely%20Not%20A%20Team"
        )
    )

    check(
        "Unknown fixture team -> 404",
        response.status_code
        == 404,
        failures,
    )

    # ========================================================
    # 10. Read-only HTTP boundary
    # ========================================================

    print(
        "\n10. READ-ONLY HTTP BOUNDARY"
    )

    read_only_test_paths = [

        "/api/v1/context/status",
        "/api/v1/context/standings",
        "/api/v1/context/form",
        "/api/v1/context/teams",
        "/api/v1/context/fixtures",
    ]

    for path in read_only_test_paths:

        response = client.post(
            path,
            json={
                "test":
                    True,
            },
        )

        check(
            f"POST {path} -> 405",
            response.status_code
            == 405,
            failures,
        )

    # ========================================================
    # 11. Existing production API preserved
    # ========================================================

    print(
        "\n11. EXISTING API PRESERVATION"
    )

    health_response = client.get(
        "/api/health"
    )

    health_payload = (
        health_response.get_json()
    )

    check(
        "Existing /api/health -> 200",
        health_response.status_code
        == 200,
        failures,
    )

    check(
        "Existing health project FixtureIQ",
        health_payload.get(
            "project"
        )
        == "FixtureIQ",
        failures,
    )

    production_routes = {

        str(rule)

        for rule in app.url_map.iter_rules()

        if str(rule).startswith(
            "/api/v1/predictions"
        )
        or
        str(rule).startswith(
            "/api/v1/production"
        )
    }

    check(
        "Stage 7 production routes preserved",
        len(
            production_routes
        )
        >= 7,
        failures,
    )

    # ========================================================
    # 12. Safety
    # ========================================================

    print(
        "\n12. STAGE 8.6 SAFETY"
    )

    check(
        "Context API uses verified Stage 8 services",
        all(
            status.get(
                "status"
            )
            == "READY"
            for status in service_statuses.values()
        ),
        failures,
    )

    check(
        "Context API exposes no dependency hashes",
        not any(
            contains_forbidden_public_key(
                response.get_json()
            )
            for response in [
                client.get(
                    "/api/v1/context/status"
                ),
                client.get(
                    "/api/v1/context/standings"
                ),
                client.get(
                    "/api/v1/context/form"
                ),
                client.get(
                    "/api/v1/context/teams"
                ),
                client.get(
                    "/api/v1/context/fixtures"
                ),
            ]
        ),
        failures,
    )

    # ========================================================
    # 13. Final Stage 8.6 decision
    # ========================================================

    print(
        "\n13. STAGE 8.6 FINAL DECISION"
    )

    final_pass = (
        len(
            failures
        )
        == 0
    )

    if final_pass:

        verified_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        verification = {

            "stage":
                "8.6",

            "status":
                "PASS",

            "stage_8_6_complete":
                True,

            "stage_8_6_status":
                "COMPLETE",

            "context_rest_api":
                "VERIFIED",

            "verified_at_utc":
                verified_at,

            "sub_stages": {

                "8.6.1":
                    "PASS",

                "8.6.2":
                    "PASS",

                "8.6.3":
                    "PASS",

                "8.6.4":
                    "PASS",

                "8.6.5":
                    "PASS",
            },

            "api_contract": {

                "version":
                    CONTEXT_API_VERSION,

                "stage":
                    CONTEXT_API_STAGE,

                "read_only":
                    True,

                "route_count":
                    10,

                "routes":
                    PUBLIC_ROUTES,

                "allowed_methods":
                    [
                        "GET"
                    ],

                "unknown_resource_status":
                    404,

                "not_ready_status":
                    503,

                "write_method_status":
                    405,
            },

            "layers": {

                "standings":
                    "READY",

                "team_form":
                    "READY",

                "team_context":
                    "READY",

                "fixture_context":
                    "READY",
            },

            "verification": {

                "flask_registration_verified":
                    True,

                "status_endpoint_verified":
                    True,

                "standings_endpoints_verified":
                    True,

                "form_endpoints_verified":
                    True,

                "team_context_endpoints_verified":
                    True,

                "fixture_context_endpoints_verified":
                    True,

                "single_resource_lookup_verified":
                    True,

                "team_fixture_lookup_verified":
                    True,

                "not_found_behavior_verified":
                    True,

                "read_only_http_boundary_verified":
                    True,

                "public_field_boundary_verified":
                    True,

                "existing_health_route_preserved":
                    True,

                "existing_production_routes_preserved":
                    True,
            },

            "dependency_identity": {

                "stage8_context_contract": {

                    "path":
                        relative_path(
                            CONTRACT_FILE
                        ),

                    "sha256":
                        sha256_file(
                            CONTRACT_FILE
                        ),
                },

                "stage8_context_contract_verification": {

                    "path":
                        relative_path(
                            CONTRACT_VERIFICATION_FILE
                        ),

                    "sha256":
                        sha256_file(
                            CONTRACT_VERIFICATION_FILE
                        ),
                },

                "standings_report": {

                    "path":
                        relative_path(
                            STANDINGS_REPORT_FILE
                        ),

                    "sha256":
                        sha256_file(
                            STANDINGS_REPORT_FILE
                        ),
                },

                "team_form_report": {

                    "path":
                        relative_path(
                            TEAM_FORM_REPORT_FILE
                        ),

                    "sha256":
                        sha256_file(
                            TEAM_FORM_REPORT_FILE
                        ),
                },

                "team_context_report": {

                    "path":
                        relative_path(
                            TEAM_CONTEXT_REPORT_FILE
                        ),

                    "sha256":
                        sha256_file(
                            TEAM_CONTEXT_REPORT_FILE
                        ),
                },

                "fixture_context_report": {

                    "path":
                        relative_path(
                            FIXTURE_CONTEXT_REPORT_FILE
                        ),

                    "sha256":
                        sha256_file(
                            FIXTURE_CONTEXT_REPORT_FILE
                        ),
                },
            },

            "safety": {

                "read_only":
                    True,

                "context_only":
                    True,

                "provider_fetch_performed":
                    False,

                "context_rebuilt":
                    False,

                "model_loaded":
                    False,

                "model_executed":
                    False,

                "model_modified":
                    False,

                "production_predictions_modified":
                    False,

                "feature_schema_modified":
                    False,

                "context_used_as_model_features":
                    False,

                "stage7_artifacts_modified":
                    False,

                "final_test_accessed":
                    False,

                "private_dependency_hashes_exposed":
                    False,
            },

            "failures":
                [],
        }

        save_json(
            OUTPUT_FILE,
            verification,
        )

        print(
            OUTPUT_FILE
        )

        persisted = load_json(
            OUTPUT_FILE
        )

        check(
            "Stage 8.6 verification persisted",
            persisted.get(
                "status"
            )
            == "PASS",
            failures,
        )

        check(
            "Stage 8.6 COMPLETE persisted",
            persisted.get(
                "stage_8_6_complete"
            )
            is True,
            failures,
        )

        check(
            "Context REST API VERIFIED persisted",
            persisted.get(
                "context_rest_api"
            )
            == "VERIFIED",
            failures,
        )

        final_pass = (
            len(
                failures
            )
            == 0
        )

    # ========================================================
    # Final output
    # ========================================================

    print(
        "\n" + "=" * 72
    )

    if final_pass:

        print(
            "STAGE 8.6.1: PASS"
        )

        print(
            "STAGE 8.6.2: PASS"
        )

        print(
            "STAGE 8.6.3: PASS"
        )

        print(
            "STAGE 8.6.4: PASS"
        )

        print(
            "STAGE 8.6.5: PASS"
        )

        print()

        print(
            "STAGE 8.6: COMPLETE"
        )

        print(
            "CONTEXT REST API: VERIFIED"
        )

    else:

        print(
            "STAGE 8.6: FAIL"
        )

        print(
            "CONTEXT REST API: NOT VERIFIED"
        )

        if failures:

            print(
                "\nFailures:"
            )

            for failure in failures:

                print(
                    f"  - {failure}"
                )

    print("=" * 72)

    sys.exit(
        0
        if final_pass
        else 1
    )


if __name__ == "__main__":

    main()
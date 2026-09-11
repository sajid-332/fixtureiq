"""
FixtureIQ Stage 8.7.3 - 8.7.5

8.7.3
No-Stale-Cache / Request Isolation

8.7.4
Runtime Recovery Verification

8.7.5
Final Stage 8.7 Gate

Updates:
data/processed/context/context_runtime_verification.json

Requires:
- Stage 8.7.1 PASS
- Stage 8.7.2 PASS

Proves:
- context responses prohibit HTTP cache storage
- cache policy applies to READY / 404 / 503 responses
- services are constructed at request time
- responses are not reused across requests
- runtime state changes are immediately observed
- stale runtime -> HTTP 503
- restored runtime -> HTTP 200
- recovery does not require Flask restart
- Stage 7 production routes remain intact
- locked model remains unchanged
- Stage 8 remains context-only

No provider fetch.
No context rebuild.
No model execution.
No prediction mutation.
No Stage 7 writes.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


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

PRODUCTION_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "production"
)

CONTEXT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "context"
)

MODEL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
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

UPCOMING_FIXTURES_FILE = (
    PRODUCTION_DIR
    / "upcoming_fixtures.csv"
)

FIXTURE_FETCH_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_fixture_fetch_report.json"
)

ENRICHED_FIXTURES_FILE = (
    CONTEXT_DIR
    / "enriched_upcoming_fixtures.csv"
)

FIXTURE_CONTEXT_REPORT_FILE = (
    CONTEXT_DIR
    / "fixture_context_report.json"
)

HISTORY_FILE = (
    PRODUCTION_DIR
    / "production_history.csv"
)

HISTORY_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_history_report.json"
)

CONTEXT_API_VERIFICATION_FILE = (
    CONTEXT_DIR
    / "context_api_verification.json"
)

RUNTIME_VERIFICATION_FILE = (
    CONTEXT_DIR
    / "context_runtime_verification.json"
)

SELECTED_MODEL_FILE = (
    MODEL_DIR
    / "selected"
    / "selected_model.joblib"
)


# ============================================================
# Runtime code identity
# ============================================================

CONTEXT_API_CODE_FILE = (
    BASE_DIR
    / "backend"
    / "routes"
    / "context_api.py"
)

APP_CODE_FILE = (
    BASE_DIR
    / "backend"
    / "app.py"
)

FIXTURE_CONTEXT_SERVICE_CODE_FILE = (
    BASE_DIR
    / "backend"
    / "services"
    / "fixture_context_service.py"
)

TEAM_CONTEXT_SERVICE_CODE_FILE = (
    BASE_DIR
    / "backend"
    / "services"
    / "team_context_service.py"
)


# ============================================================
# Helpers
# ============================================================

def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise FileNotFoundError(
            f"Required artifact missing: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        payload = json.load(file)

    if not isinstance(
        payload,
        dict,
    ):

        raise RuntimeError(
            f"Expected JSON object: {path}"
        )

    return payload


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

    if not path.exists():

        raise FileNotFoundError(
            f"Required artifact missing: {path}"
        )

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

            digest.update(
                chunk
            )

    return digest.hexdigest()


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


def check(
    label: str,
    condition,
    failures: list[str],
) -> bool:

    passed = bool(
        condition
    )

    print(
        f"{label}: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    if not passed:

        failures.append(
            label
        )

    return passed


def has_no_store_headers(
    response,
) -> bool:

    cache_control = (
        response.headers
        .get(
            "Cache-Control",
            "",
        )
        .lower()
    )

    pragma = (
        response.headers
        .get(
            "Pragma",
            "",
        )
        .lower()
    )

    expires = (
        response.headers
        .get(
            "Expires",
            "",
        )
        .strip()
    )

    return (
        "no-store"
        in cache_control
        and
        "no-cache"
        in cache_control
        and
        "must-revalidate"
        in cache_control
        and
        "max-age=0"
        in cache_control
        and
        pragma
        == "no-cache"
        and
        expires
        == "0"
    )


# ============================================================
# Temporary dependency environment
# ============================================================

def build_test_copy(
    root: Path,
    name: str,
) -> dict[str, Path]:

    sandbox = (
        root
        / name
    )

    sandbox.mkdir(
        parents=True,
        exist_ok=True,
    )

    paths = {

        "contract":
            sandbox
            / "stage8_context_contract.json",

        "contract_verification":
            sandbox
            / "stage8_context_contract_verification.json",

        "standings":
            sandbox
            / "current_standings.csv",

        "standings_report":
            sandbox
            / "standings_report.json",

        "team_form":
            sandbox
            / "current_team_form.csv",

        "team_form_report":
            sandbox
            / "team_form_report.json",

        "team_context":
            sandbox
            / "team_context.csv",

        "team_context_report":
            sandbox
            / "team_context_report.json",

        "upcoming":
            sandbox
            / "upcoming_fixtures.csv",

        "fixture_fetch_report":
            sandbox
            / "production_fixture_fetch_report.json",

        "enriched":
            sandbox
            / "enriched_upcoming_fixtures.csv",

        "fixture_context_report":
            sandbox
            / "fixture_context_report.json",

        "history":
            sandbox
            / "production_history.csv",

        "history_report":
            sandbox
            / "production_history_report.json",
    }

    copy_map = {

        CONTRACT_FILE:
            paths[
                "contract"
            ],

        CONTRACT_VERIFICATION_FILE:
            paths[
                "contract_verification"
            ],

        STANDINGS_FILE:
            paths[
                "standings"
            ],

        STANDINGS_REPORT_FILE:
            paths[
                "standings_report"
            ],

        TEAM_FORM_FILE:
            paths[
                "team_form"
            ],

        TEAM_FORM_REPORT_FILE:
            paths[
                "team_form_report"
            ],

        TEAM_CONTEXT_FILE:
            paths[
                "team_context"
            ],

        TEAM_CONTEXT_REPORT_FILE:
            paths[
                "team_context_report"
            ],

        UPCOMING_FIXTURES_FILE:
            paths[
                "upcoming"
            ],

        FIXTURE_FETCH_REPORT_FILE:
            paths[
                "fixture_fetch_report"
            ],

        ENRICHED_FIXTURES_FILE:
            paths[
                "enriched"
            ],

        FIXTURE_CONTEXT_REPORT_FILE:
            paths[
                "fixture_context_report"
            ],

        HISTORY_FILE:
            paths[
                "history"
            ],

        HISTORY_REPORT_FILE:
            paths[
                "history_report"
            ],
    }

    for source, destination in copy_map.items():

        shutil.copy2(
            source,
            destination,
        )

    return paths


def make_team_context_service(
    paths: dict[str, Path],
) -> TeamContextService:

    return TeamContextService(

        contract_file=
            paths[
                "contract"
            ],

        contract_verification_file=
            paths[
                "contract_verification"
            ],

        standings_file=
            paths[
                "standings"
            ],

        standings_report_file=
            paths[
                "standings_report"
            ],

        team_form_file=
            paths[
                "team_form"
            ],

        team_form_report_file=
            paths[
                "team_form_report"
            ],

        team_context_file=
            paths[
                "team_context"
            ],

        team_context_report_file=
            paths[
                "team_context_report"
            ],

        upcoming_fixtures_file=
            paths[
                "upcoming"
            ],

        history_file=
            paths[
                "history"
            ],

        history_report_file=
            paths[
                "history_report"
            ],
    )


def make_fixture_context_service(
    paths: dict[str, Path],
) -> FixtureContextService:

    upstream = (
        make_team_context_service(
            paths
        )
    )

    return FixtureContextService(

        contract_file=
            paths[
                "contract"
            ],

        contract_verification_file=
            paths[
                "contract_verification"
            ],

        upcoming_fixtures_file=
            paths[
                "upcoming"
            ],

        fixture_fetch_report_file=
            paths[
                "fixture_fetch_report"
            ],

        team_context_file=
            paths[
                "team_context"
            ],

        team_context_report_file=
            paths[
                "team_context_report"
            ],

        enriched_fixtures_file=
            paths[
                "enriched"
            ],

        fixture_context_report_file=
            paths[
                "fixture_context_report"
            ],

        team_context_service=
            upstream,
    )


# ============================================================
# Dynamic service for cache-isolation test
# ============================================================

class DynamicFixtureService:

    def __init__(
        self,
        state: dict,
    ):

        self.state = state

    def get_status(
        self,
    ) -> dict:

        return {

            "status":
                "READY",

            "stage":
                "8.5.4",

            "service":
                "fixture_context",

            "season":
                2026,

            "fixture_count":
                1,

            "column_count":
                1,

            "source_column_count":
                1,

            "context_column_count":
                72,

            "freshness_mode":
                (
                    "DEPENDENCY_BASED_PLUS_"
                    "TEMPORAL_BOUNDARY"
                ),
        }

    def get_all_fixture_context(
        self,
    ) -> list[dict]:

        return [

            {
                "fixture_id":
                    (
                        "runtime-version-"
                        f"{self.state['version']}"
                    ),

                "runtime_version":
                    self.state[
                        "version"
                    ],
            }
        ]


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.7.3 - 8.7.5"
    )

    print(
        "Cache Safety + Runtime Recovery + Final Gate"
    )

    print("=" * 72)

    failures = []

    # ========================================================
    # 1. Required artifacts
    # ========================================================

    print(
        "\n1. REQUIRED ARTIFACTS"
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

        UPCOMING_FIXTURES_FILE,
        FIXTURE_FETCH_REPORT_FILE,

        ENRICHED_FIXTURES_FILE,
        FIXTURE_CONTEXT_REPORT_FILE,

        HISTORY_FILE,
        HISTORY_REPORT_FILE,

        CONTEXT_API_VERIFICATION_FILE,
        RUNTIME_VERIFICATION_FILE,

        SELECTED_MODEL_FILE,

        CONTEXT_API_CODE_FILE,
        APP_CODE_FILE,

        FIXTURE_CONTEXT_SERVICE_CODE_FILE,
        TEAM_CONTEXT_SERVICE_CODE_FILE,
    ]

    for path in required:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        sys.exit(1)

    # ========================================================
    # 2. Previous Stage 8 state
    # ========================================================

    print(
        "\n2. PREVIOUS STAGE STATE"
    )

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

    api_verification = load_json(
        CONTEXT_API_VERIFICATION_FILE
    )

    runtime_report = load_json(
        RUNTIME_VERIFICATION_FILE
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
        "Stage 8.6 COMPLETE",
        api_verification.get(
            "stage_8_6_complete"
        )
        is True,
        failures,
    )

    check(
        "Context REST API VERIFIED",
        api_verification.get(
            "context_rest_api"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Runtime report stage = 8.7",
        runtime_report.get(
            "stage"
        )
        == "8.7",
        failures,
    )

    check(
        "Runtime report PARTIAL_PASS",
        runtime_report.get(
            "status"
        )
        == "PARTIAL_PASS",
        failures,
    )

    runtime_sub_stages = (
        runtime_report.get(
            "sub_stages",
            {}
        )
    )

    check(
        "8.7.1 already PASS",
        runtime_sub_stages.get(
            "8.7.1"
        )
        == "PASS",
        failures,
    )

    check(
        "8.7.2 already PASS",
        runtime_sub_stages.get(
            "8.7.2"
        )
        == "PASS",
        failures,
    )

    check(
        "Runtime freshness contract already VERIFIED",
        runtime_report.get(
            "runtime_freshness_contract"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "HTTP stale-state fail-closed already VERIFIED",
        runtime_report.get(
            "http_stale_state_fail_closed"
        )
        == "VERIFIED",
        failures,
    )

    # ========================================================
    # 3. Output contract
    # ========================================================

    print(
        "\n3. OUTPUT CONTRACT"
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
        "Runtime verification path locked",
        outputs.get(
            "context_runtime_verification",
            {}
        ).get(
            "path"
        )
        ==
        relative_path(
            RUNTIME_VERIFICATION_FILE
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
    # 4. Baseline services
    # ========================================================

    print(
        "\n4. BASELINE SERVICES"
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

    for name, service in services.items():

        status = service.get_status()

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
    # 5. Stage 8.7.3 - HTTP cache policy
    # ========================================================

    print(
        "\n5. STAGE 8.7.3 HTTP CACHE POLICY"
    )

    client = app.test_client()

    baseline_paths = [

        "/api/v1/context/status",
        "/api/v1/context/standings",
        "/api/v1/context/form",
        "/api/v1/context/teams",
        "/api/v1/context/fixtures",
    ]

    for endpoint in baseline_paths:

        response = client.get(
            endpoint
        )

        check(
            f"GET {endpoint} -> 200",
            response.status_code
            == 200,
            failures,
        )

        check(
            f"{endpoint} no-store policy",
            has_no_store_headers(
                response
            ),
            failures,
        )

    # Custom 404 must also be uncacheable.

    not_found_response = client.get(
        (
            "/api/v1/context/fixtures/"
            "fixtureiq-does-not-exist"
        )
    )

    check(
        "Context 404 remains 404",
        not_found_response.status_code
        == 404,
        failures,
    )

    check(
        "Context 404 no-store policy",
        has_no_store_headers(
            not_found_response
        ),
        failures,
    )

    # ========================================================
    # 6. Request isolation
    # ========================================================

    print(
        "\n6. REQUEST ISOLATION"
    )

    dynamic_state = {

        "version":
            1,
    }

    construction_count = {

        "value":
            0,
    }

    def dynamic_fixture_factory():

        construction_count[
            "value"
        ] += 1

        return DynamicFixtureService(
            dynamic_state
        )

    with patch(
        "backend.routes.context_api.FixtureContextService",
        side_effect=dynamic_fixture_factory,
    ):

        first_response = client.get(
            "/api/v1/context/fixtures"
        )

        first_payload = (
            first_response.get_json()
        )

        dynamic_state[
            "version"
        ] = 2

        second_response = client.get(
            "/api/v1/context/fixtures"
        )

        second_payload = (
            second_response.get_json()
        )

    first_data = (
        first_payload.get(
            "data",
            [],
        )
    )

    second_data = (
        second_payload.get(
            "data",
            [],
        )
    )

    first_fixture_id = (
        first_data[
            0
        ].get(
            "fixture_id"
        )
        if first_data
        else None
    )

    second_fixture_id = (
        second_data[
            0
        ].get(
            "fixture_id"
        )
        if second_data
        else None
    )

    check(
        "Dynamic first request -> 200",
        first_response.status_code
        == 200,
        failures,
    )

    check(
        "Dynamic second request -> 200",
        second_response.status_code
        == 200,
        failures,
    )

    check(
        "Fixture service constructed per request",
        construction_count[
            "value"
        ]
        == 2,
        failures,
    )

    check(
        "First request observes runtime version 1",
        first_fixture_id
        == "runtime-version-1",
        failures,
    )

    check(
        "Second request observes runtime version 2",
        second_fixture_id
        == "runtime-version-2",
        failures,
    )

    check(
        "Previous payload not reused",
        first_fixture_id
        != second_fixture_id,
        failures,
    )

    check(
        "Dynamic responses are no-store",
        (
            has_no_store_headers(
                first_response
            )
            and
            has_no_store_headers(
                second_response
            )
        ),
        failures,
    )

    # ========================================================
    # 7. Stage 8.7.4 runtime recovery setup
    # ========================================================

    print(
        "\n7. STAGE 8.7.4 RUNTIME RECOVERY"
    )

    with tempfile.TemporaryDirectory() as temp_dir:

        root = Path(
            temp_dir
        )

        stale_paths = build_test_copy(
            root,
            "runtime_recovery",
        )

        # Deliberately invalidate the exact fixture dependency.

        with stale_paths[
            "upcoming"
        ].open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                "\n"
            )

        stale_fixture_service = (
            make_fixture_context_service(
                stale_paths
            )
        )

        stale_service_status = (
            stale_fixture_service
            .get_status()
        )

        check(
            "Recovery test stale service NOT_READY",
            stale_service_status.get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # A healthy live service represents the state after
        # dependencies have been refreshed/restored.
        #
        # We do not run a rebuild here. We switch the runtime
        # dependency source to the already verified canonical
        # service to prove Flask does not require a restart.

        healthy_fixture_service = (
            FixtureContextService()
        )

        healthy_service_status = (
            healthy_fixture_service
            .get_status()
        )

        check(
            "Recovery target service READY",
            healthy_service_status.get(
                "status"
            )
            == "READY",
            failures,
        )

        runtime_state = {

            "service":
                stale_fixture_service,
        }

        factory_count = {

            "value":
                0,
        }

        def runtime_fixture_factory():

            factory_count[
                "value"
            ] += 1

            return runtime_state[
                "service"
            ]

        with patch(
            "backend.routes.context_api.FixtureContextService",
            side_effect=runtime_fixture_factory,
        ):

            # -----------------------------------------------
            # Same Flask app/client while stale
            # -----------------------------------------------

            stale_fixture_response = (
                client.get(
                    "/api/v1/context/fixtures"
                )
            )

            stale_global_response = (
                client.get(
                    "/api/v1/context/status"
                )
            )

            # -----------------------------------------------
            # Restore runtime source without restarting Flask
            # -----------------------------------------------

            runtime_state[
                "service"
            ] = healthy_fixture_service

            recovered_fixture_response = (
                client.get(
                    "/api/v1/context/fixtures"
                )
            )

            recovered_global_response = (
                client.get(
                    "/api/v1/context/status"
                )
            )

    check(
        "Runtime stale fixture response -> 503",
        stale_fixture_response.status_code
        == 503,
        failures,
    )

    check(
        "Runtime stale global status -> 503",
        stale_global_response.status_code
        == 503,
        failures,
    )

    stale_payload = (
        stale_fixture_response.get_json()
    )

    check(
        "Stale fixture payload NOT_READY",
        stale_payload.get(
            "status"
        )
        == "NOT_READY",
        failures,
    )

    check(
        "Stale 503 no-store",
        has_no_store_headers(
            stale_fixture_response
        ),
        failures,
    )

    check(
        "Recovered fixture response -> 200",
        recovered_fixture_response.status_code
        == 200,
        failures,
    )

    recovered_payload = (
        recovered_fixture_response.get_json()
    )

    check(
        "Recovered fixture payload READY",
        recovered_payload.get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "Recovered fixture count > 0",
        recovered_payload.get(
            "count",
            0,
        )
        > 0,
        failures,
    )

    check(
        "Recovered global status -> 200",
        recovered_global_response.status_code
        == 200,
        failures,
    )

    recovered_global_payload = (
        recovered_global_response.get_json()
    )

    check(
        "Recovered global payload READY",
        recovered_global_payload.get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "Recovered response still no-store",
        has_no_store_headers(
            recovered_fixture_response
        ),
        failures,
    )

    check(
        "Recovery occurred through repeated request-time construction",
        factory_count[
            "value"
        ]
        >= 4,
        failures,
    )

    check(
        "503 -> 200 recovery without Flask restart",
        (
            stale_fixture_response.status_code
            == 503
            and
            recovered_fixture_response.status_code
            == 200
        ),
        failures,
    )

    # ========================================================
    # 8. Existing API isolation
    # ========================================================

    print(
        "\n8. EXISTING API ISOLATION"
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
        "Health project remains FixtureIQ",
        health_payload.get(
            "project"
        )
        == "FixtureIQ",
        failures,
    )

    production_routes = {

        str(rule)

        for rule in app.url_map.iter_rules()

        if (
            str(rule).startswith(
                "/api/v1/predictions"
            )
            or
            str(rule).startswith(
                "/api/v1/production"
            )
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
    # 9. Locked ML boundary
    # ========================================================

    print(
        "\n9. LOCKED ML BOUNDARY"
    )

    locked_model = contract.get(
        "locked_model",
        {}
    )

    actual_model_sha = (
        sha256_file(
            SELECTED_MODEL_FILE
        )
    )

    check(
        "Locked model = random_forest",
        locked_model.get(
            "model_id"
        )
        == "random_forest",
        failures,
    )

    check(
        "Locked feature count = 86",
        locked_model.get(
            "feature_count"
        )
        == 86,
        failures,
    )

    check(
        "Locked model SHA unchanged",
        locked_model.get(
            "sha256"
        )
        == actual_model_sha,
        failures,
    )

    check(
        "Stage 8 remains context-only",
        contract.get(
            "context_only"
        )
        is True,
        failures,
    )

    # ========================================================
    # 10. Stage 8.7.5 final preconditions
    # ========================================================

    print(
        "\n10. STAGE 8.7.5 FINAL PRECONDITIONS"
    )

    current_services = {

        "standings":
            StandingsService(),

        "team_form":
            TeamFormService(),

        "team_context":
            TeamContextService(),

        "fixture_context":
            FixtureContextService(),
    }

    all_services_ready = True

    for name, service in current_services.items():

        status = (
            service.get_status()
        )

        ready = (
            status.get(
                "status"
            )
            == "READY"
        )

        check(
            f"Final {name} READY",
            ready,
            failures,
        )

        if not ready:

            all_services_ready = False

            print(
                f"{name} reason:",
                status.get(
                    "reason"
                ),
            )

    final_http_status = (
        client.get(
            "/api/v1/context/status"
        )
    )

    check(
        "Final context status endpoint -> 200",
        final_http_status.status_code
        == 200,
        failures,
    )

    check(
        "Final context status READY",
        final_http_status
        .get_json()
        .get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "Final context status no-store",
        has_no_store_headers(
            final_http_status
        ),
        failures,
    )

    # ========================================================
    # 11. Persist Stage 8.7 completion
    # ========================================================

    print(
        "\n11. SAVE STAGE 8.7 FINAL EVIDENCE"
    )

    overall_pass = (
        len(failures)
        == 0
        and
        all_services_ready
    )

    if overall_pass:

        verified_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        final_report = load_json(
            RUNTIME_VERIFICATION_FILE
        )

        sub_stages = dict(
            final_report.get(
                "sub_stages",
                {}
            )
        )

        sub_stages[
            "8.7.1"
        ] = "PASS"

        sub_stages[
            "8.7.2"
        ] = "PASS"

        sub_stages[
            "8.7.3"
        ] = "PASS"

        sub_stages[
            "8.7.4"
        ] = "PASS"

        sub_stages[
            "8.7.5"
        ] = "PASS"

        final_report[
            "sub_stages"
        ] = sub_stages

        final_report[
            "status"
        ] = "PASS"

        final_report[
            "stage_8_7_complete"
        ] = True

        final_report[
            "stage_8_7_status"
        ] = "COMPLETE"

        final_report[
            "context_runtime_safety"
        ] = "VERIFIED"

        final_report[
            "stage_8_7_3_verified_at_utc"
        ] = verified_at

        final_report[
            "stage_8_7_4_verified_at_utc"
        ] = verified_at

        final_report[
            "stage_8_7_5_verified_at_utc"
        ] = verified_at

        final_report[
            "cache_and_request_isolation"
        ] = {

            "status":
                "VERIFIED",

            "cache_control":
                (
                    "no-store, no-cache, "
                    "must-revalidate, max-age=0"
                ),

            "pragma":
                "no-cache",

            "expires":
                "0",

            "ready_response_no_store":
                True,

            "not_found_response_no_store":
                True,

            "not_ready_response_no_store":
                True,

            "service_constructed_per_request":
                True,

            "runtime_state_rechecked_per_request":
                True,

            "response_payload_reused":
                False,

            "stale_response_reuse_allowed":
                False,

            "http_cache_storage_allowed":
                False,
        }

        final_report[
            "runtime_recovery"
        ] = {

            "status":
                "VERIFIED",

            "initial_state":
                "NOT_READY",

            "initial_http_status":
                503,

            "restored_state":
                "READY",

            "restored_http_status":
                200,

            "same_flask_application":
                True,

            "same_test_client":
                True,

            "flask_restart_required":
                False,

            "request_time_revalidation":
                True,

            "global_status_recovered":
                True,

            "recovered_payload_ready":
                True,

            "recovered_response_no_store":
                True,
        }

        final_report[
            "runtime_code_identity"
        ] = {

            "context_api": {

                "path":
                    relative_path(
                        CONTEXT_API_CODE_FILE
                    ),

                "sha256":
                    sha256_file(
                        CONTEXT_API_CODE_FILE
                    ),
            },

            "flask_app": {

                "path":
                    relative_path(
                        APP_CODE_FILE
                    ),

                "sha256":
                    sha256_file(
                        APP_CODE_FILE
                    ),
            },

            "fixture_context_service": {

                "path":
                    relative_path(
                        FIXTURE_CONTEXT_SERVICE_CODE_FILE
                    ),

                "sha256":
                    sha256_file(
                        FIXTURE_CONTEXT_SERVICE_CODE_FILE
                    ),
            },

            "team_context_service": {

                "path":
                    relative_path(
                        TEAM_CONTEXT_SERVICE_CODE_FILE
                    ),

                "sha256":
                    sha256_file(
                        TEAM_CONTEXT_SERVICE_CODE_FILE
                    ),
            },
        }

        final_report[
            "final_gate"
        ] = {

            "stage":
                "8.7.5",

            "status":
                "PASS",

            "verified_at_utc":
                verified_at,

            "runtime_freshness_contract_verified":
                True,

            "http_stale_state_fail_closed_verified":
                True,

            "no_stale_cache_verified":
                True,

            "request_isolation_verified":
                True,

            "runtime_recovery_verified":
                True,

            "dependency_freshness_verified":
                True,

            "transitive_freshness_verified":
                True,

            "temporal_freshness_verified":
                True,

            "http_503_fail_closed_verified":
                True,

            "runtime_503_to_200_verified":
                True,

            "all_context_services_ready":
                True,

            "context_api_ready":
                True,

            "stage7_routes_preserved":
                True,

            "locked_model_unchanged":
                True,

            "locked_feature_count":
                86,

            "context_only":
                True,

            "fail_closed":
                True,
        }

        safety = dict(
            final_report.get(
                "safety",
                {}
            )
        )

        safety.update(
            {

                "read_only":
                    True,

                "context_only":
                    True,

                "provider_fetch_performed":
                    False,

                "context_rebuilt":
                    False,

                "stage7_artifacts_modified":
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

                "final_test_accessed":
                    False,

                "stale_data_served":
                    False,

                "http_cache_storage_allowed":
                    False,

                "runtime_recovery_verified":
                    True,
            }
        )

        final_report[
            "safety"
        ] = safety

        final_report[
            "failures"
        ] = []

        save_json(
            RUNTIME_VERIFICATION_FILE,
            final_report,
        )

        print(
            RUNTIME_VERIFICATION_FILE
        )

        # ====================================================
        # Persisted artifact verification
        # ====================================================

        persisted = load_json(
            RUNTIME_VERIFICATION_FILE
        )

        check(
            "Final runtime status PASS persisted",
            persisted.get(
                "status"
            )
            == "PASS",
            failures,
        )

        check(
            "stage_8_7_complete persisted",
            persisted.get(
                "stage_8_7_complete"
            )
            is True,
            failures,
        )

        check(
            "Stage 8.7 COMPLETE persisted",
            persisted.get(
                "stage_8_7_status"
            )
            == "COMPLETE",
            failures,
        )

        check(
            "Runtime safety VERIFIED persisted",
            persisted.get(
                "context_runtime_safety"
            )
            == "VERIFIED",
            failures,
        )

        for stage in (
            "8.7.1",
            "8.7.2",
            "8.7.3",
            "8.7.4",
            "8.7.5",
        ):

            check(
                f"{stage} PASS persisted",
                persisted.get(
                    "sub_stages",
                    {}
                ).get(
                    stage
                )
                == "PASS",
                failures,
            )

        check(
            "Cache safety VERIFIED persisted",
            persisted.get(
                "cache_and_request_isolation",
                {}
            ).get(
                "status"
            )
            == "VERIFIED",
            failures,
        )

        check(
            "Runtime recovery VERIFIED persisted",
            persisted.get(
                "runtime_recovery",
                {}
            ).get(
                "status"
            )
            == "VERIFIED",
            failures,
        )

        check(
            "Final gate PASS persisted",
            persisted.get(
                "final_gate",
                {}
            ).get(
                "status"
            )
            == "PASS",
            failures,
        )

        # ====================================================
        # Final runtime smoke check after promotion
        # ====================================================

        post_response = client.get(
            "/api/v1/context/status"
        )

        check(
            "Context API remains READY after promotion",
            (
                post_response.status_code
                == 200
                and
                post_response
                .get_json()
                .get(
                    "status"
                )
                == "READY"
            ),
            failures,
        )

        check(
            "No-store remains active after promotion",
            has_no_store_headers(
                post_response
            ),
            failures,
        )

        overall_pass = (
            len(failures)
            == 0
        )

    # ========================================================
    # Final output
    # ========================================================

    print(
        "\n" + "=" * 72
    )

    if overall_pass:

        print(
            "STAGE 8.7.1: PASS"
        )

        print(
            "STAGE 8.7.2: PASS"
        )

        print(
            "STAGE 8.7.3: PASS"
        )

        print(
            "STAGE 8.7.4: PASS"
        )

        print(
            "STAGE 8.7.5: PASS"
        )

        print()

        print(
            "STAGE 8.7: COMPLETE"
        )

        print(
            "CONTEXT RUNTIME SAFETY: VERIFIED"
        )

    else:

        print(
            "STAGE 8.7: FAIL"
        )

        print(
            "CONTEXT RUNTIME SAFETY: NOT VERIFIED"
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
        if overall_pass
        else 1
    )


if __name__ == "__main__":

    main()
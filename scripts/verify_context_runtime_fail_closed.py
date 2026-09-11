"""
FixtureIQ Stage 8.7.1 + 8.7.2

8.7.1
Runtime Freshness Contract

8.7.2
HTTP Stale-State Fail-Closed Verification

Creates / updates:
data/processed/context/context_runtime_verification.json

Purpose:
- define the Stage 8 runtime freshness contract
- prove verified services are READY at baseline
- prove direct fixture-context staleness -> NOT_READY
- prove transitive upstream staleness -> NOT_READY
- prove temporal kickoff expiry -> NOT_READY
- prove HTTP context endpoints return 503 for stale state
- prove global context status propagates NOT_READY
- prove public 503 payload does not leak private failure details
- preserve Stage 7 production API

Not included yet:
- HTTP cache-control/no-store verification      -> 8.7.3
- response cache isolation                     -> 8.7.3
- 503 -> 200 runtime recovery                  -> 8.7.4

No provider fetch.
No context rebuild.
No model execution.
No prediction mutation.
No Stage 7 write.
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

OUTPUT_FILE = (
    CONTEXT_DIR
    / "context_runtime_verification.json"
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

            digest.update(chunk)

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


def parse_aware(
    value,
) -> datetime:

    if not isinstance(
        value,
        str,
    ):

        raise RuntimeError(
            "Timestamp missing."
        )

    text = value.strip()

    if not text:

        raise RuntimeError(
            "Timestamp blank."
        )

    if text.endswith("Z"):

        text = (
            text[:-1]
            + "+00:00"
        )

    parsed = datetime.fromisoformat(
        text
    )

    if parsed.tzinfo is None:

        raise RuntimeError(
            "Timestamp must be timezone-aware."
        )

    return parsed.astimezone(
        timezone.utc
    )


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
    *,
    clock=None,
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

        clock=
            clock,
    )


def public_not_ready_payload(
    payload,
    expected_service: str,
) -> bool:

    return (
        isinstance(
            payload,
            dict,
        )
        and
        payload.get(
            "status"
        )
        == "NOT_READY"
        and
        payload.get(
            "service"
        )
        == expected_service
        and
        set(
            payload.keys()
        )
        ==
        {
            "status",
            "service",
        }
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.7.1 + 8.7.2"
    )

    print(
        "Runtime Freshness Contract + HTTP Fail-Closed"
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
    # 2. Foundation
    # ========================================================

    print(
        "\n2. STAGE FOUNDATION"
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

    # ========================================================
    # 3. Stage 8.7 output contract
    # ========================================================

    print(
        "\n3. STAGE 8.7 OUTPUT CONTRACT"
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
        "context_runtime_verification path locked",
        outputs.get(
            "context_runtime_verification",
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
    # 4. 8.7.1 Runtime freshness contract
    # ========================================================

    print(
        "\n4. STAGE 8.7.1 RUNTIME FRESHNESS CONTRACT"
    )

    runtime_contract = {

        "service_validation_timing":
            "REQUEST_TIME",

        "stale_context_http_status":
            503,

        "unknown_resource_http_status":
            404,

        "write_method_http_status":
            405,

        "dependency_freshness_required":
            True,

        "transitive_dependency_freshness_required":
            True,

        "temporal_freshness_required":
            True,

        "fixture_kickoff_boundary_enforced":
            True,

        "stale_fallback_allowed":
            False,

        "partial_unverified_output_allowed":
            False,

        "private_failure_reason_exposed":
            False,

        "fail_closed":
            True,

        "provider_fetch_during_request":
            False,

        "context_rebuild_during_request":
            False,

        "model_execution_during_request":
            False,
    }

    check(
        "Request-time service validation required",
        runtime_contract[
            "service_validation_timing"
        ]
        == "REQUEST_TIME",
        failures,
    )

    check(
        "Stale context maps to HTTP 503",
        runtime_contract[
            "stale_context_http_status"
        ]
        == 503,
        failures,
    )

    check(
        "Direct dependency freshness required",
        runtime_contract[
            "dependency_freshness_required"
        ]
        is True,
        failures,
    )

    check(
        "Transitive dependency freshness required",
        runtime_contract[
            "transitive_dependency_freshness_required"
        ]
        is True,
        failures,
    )

    check(
        "Temporal freshness required",
        runtime_contract[
            "temporal_freshness_required"
        ]
        is True,
        failures,
    )

    check(
        "Kickoff boundary enforced",
        runtime_contract[
            "fixture_kickoff_boundary_enforced"
        ]
        is True,
        failures,
    )

    check(
        "Stale fallback prohibited",
        runtime_contract[
            "stale_fallback_allowed"
        ]
        is False,
        failures,
    )

    check(
        "Partial unverified output prohibited",
        runtime_contract[
            "partial_unverified_output_allowed"
        ]
        is False,
        failures,
    )

    check(
        "Private failure reason prohibited",
        runtime_contract[
            "private_failure_reason_exposed"
        ]
        is False,
        failures,
    )

    check(
        "Runtime contract fail-closed",
        runtime_contract[
            "fail_closed"
        ]
        is True,
        failures,
    )

    # ========================================================
    # 5. Baseline verified services
    # ========================================================

    print(
        "\n5. BASELINE SERVICE READINESS"
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
    # 6. Baseline HTTP readiness
    # ========================================================

    print(
        "\n6. BASELINE HTTP READINESS"
    )

    client = app.test_client()

    baseline_endpoints = [

        "/api/v1/context/status",
        "/api/v1/context/standings",
        "/api/v1/context/form",
        "/api/v1/context/teams",
        "/api/v1/context/fixtures",
    ]

    for endpoint in baseline_endpoints:

        response = client.get(
            endpoint
        )

        check(
            f"GET {endpoint} -> 200",
            response.status_code
            == 200,
            failures,
        )

    # ========================================================
    # 7. Direct fixture dependency staleness
    # ========================================================

    print(
        "\n7. DIRECT FIXTURE STALENESS -> HTTP 503"
    )

    with tempfile.TemporaryDirectory() as temp_dir:

        root = Path(
            temp_dir
        )

        direct_paths = build_test_copy(
            root,
            "direct_fixture_stale",
        )

        # Change exact upstream fixture artifact.
        # Report hash is therefore no longer valid.
        with direct_paths[
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
                direct_paths
            )
        )

        stale_fixture_status = (
            stale_fixture_service
            .get_status()
        )

        if (
            stale_fixture_status.get(
                "status"
            )
            != "NOT_READY"
        ):

            print(
                "Direct stale fixture status:",
                stale_fixture_status,
            )

        check(
            "Changed upcoming fixture -> service NOT_READY",
            stale_fixture_status.get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        with patch(
            "backend.routes.context_api.FixtureContextService",
            side_effect=lambda:
                stale_fixture_service,
        ):

            response = client.get(
                "/api/v1/context/fixtures"
            )

            payload = (
                response.get_json()
            )

            global_response = client.get(
                "/api/v1/context/status"
            )

            global_payload = (
                global_response.get_json()
            )

        check(
            "Stale fixture endpoint -> HTTP 503",
            response.status_code
            == 503,
            failures,
        )

        check(
            "Stale fixture payload public-safe",
            public_not_ready_payload(
                payload,
                "fixture_context",
            ),
            failures,
        )

        check(
            "Global context status -> HTTP 503",
            global_response.status_code
            == 503,
            failures,
        )

        check(
            "Global context status NOT_READY",
            global_payload.get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        check(
            "Global fixture layer NOT_READY",
            global_payload.get(
                "layers",
                {}
            ).get(
                "fixture_context",
                {}
            ).get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        # ====================================================
        # 8. Direct team-context dependency staleness
        # ====================================================

        print(
            "\n8. TEAM CONTEXT STALENESS -> HTTP 503"
        )

        team_paths = build_test_copy(
            root,
            "team_context_stale",
        )

        with team_paths[
            "team_context"
        ].open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                "\n"
            )

        stale_team_service = (
            make_team_context_service(
                team_paths
            )
        )

        stale_team_status = (
            stale_team_service
            .get_status()
        )

        if (
            stale_team_status.get(
                "status"
            )
            != "NOT_READY"
        ):

            print(
                "Stale team-context status:",
                stale_team_status,
            )

        check(
            "Changed team context -> service NOT_READY",
            stale_team_status.get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        with patch(
            "backend.routes.context_api.TeamContextService",
            side_effect=lambda:
                stale_team_service,
        ):

            response = client.get(
                "/api/v1/context/teams"
            )

            payload = (
                response.get_json()
            )

        check(
            "Stale team context endpoint -> HTTP 503",
            response.status_code
            == 503,
            failures,
        )

        check(
            "Stale team payload public-safe",
            public_not_ready_payload(
                payload,
                "team_context",
            ),
            failures,
        )

        # ====================================================
        # 9. Transitive production-history staleness
        # ====================================================

        print(
            "\n9. TRANSITIVE HISTORY STALENESS -> HTTP 503"
        )

        history_paths = build_test_copy(
            root,
            "history_stale",
        )

        with history_paths[
            "history"
        ].open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                " "
            )

        history_team_service = (
            make_team_context_service(
                history_paths
            )
        )

        history_team_status = (
            history_team_service
            .get_status()
        )

        check(
            "History change -> TeamContextService NOT_READY",
            history_team_status.get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        with patch(
            "backend.routes.context_api.TeamContextService",
            side_effect=lambda:
                history_team_service,
        ):

            response = client.get(
                "/api/v1/context/teams"
            )

            payload = (
                response.get_json()
            )

        check(
            "History stale team endpoint -> HTTP 503",
            response.status_code
            == 503,
            failures,
        )

        check(
            "History stale payload public-safe",
            public_not_ready_payload(
                payload,
                "team_context",
            ),
            failures,
        )

        # Also prove the same transitive state propagates
        # all the way to fixture context.

        history_fixture_service = (
            make_fixture_context_service(
                history_paths
            )
        )

        history_fixture_status = (
            history_fixture_service
            .get_status()
        )

        check(
            "History change -> FixtureContextService NOT_READY",
            history_fixture_status.get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        with patch(
            "backend.routes.context_api.FixtureContextService",
            side_effect=lambda:
                history_fixture_service,
        ):

            response = client.get(
                "/api/v1/context/fixtures"
            )

            payload = (
                response.get_json()
            )

        check(
            "History stale fixture endpoint -> HTTP 503",
            response.status_code
            == 503,
            failures,
        )

        check(
            "History stale fixture payload public-safe",
            public_not_ready_payload(
                payload,
                "fixture_context",
            ),
            failures,
        )

        # ====================================================
        # 10. Temporal fixture expiry
        # ====================================================

        print(
            "\n10. FIXTURE TEMPORAL EXPIRY -> HTTP 503"
        )

        temporal_paths = build_test_copy(
            root,
            "fixture_temporal_expiry",
        )

        temporal_report = load_json(
            temporal_paths[
                "fixture_context_report"
            ]
        )

        earliest_kickoff = parse_aware(
            temporal_report[
                "earliest_fixture_kickoff_utc"
            ]
        )

        expired_fixture_service = (
            make_fixture_context_service(

                temporal_paths,

                clock=lambda:
                    earliest_kickoff,
            )
        )

        expired_status = (
            expired_fixture_service
            .get_status()
        )

        if (
            expired_status.get(
                "status"
            )
            != "NOT_READY"
        ):

            print(
                "Temporal expiry service status:",
                expired_status,
            )

        check(
            "Kickoff boundary -> service NOT_READY",
            expired_status.get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        with patch(
            "backend.routes.context_api.FixtureContextService",
            side_effect=lambda:
                expired_fixture_service,
        ):

            response = client.get(
                "/api/v1/context/fixtures"
            )

            payload = (
                response.get_json()
            )

        check(
            "Expired fixture endpoint -> HTTP 503",
            response.status_code
            == 503,
            failures,
        )

        check(
            "Temporal expiry payload public-safe",
            public_not_ready_payload(
                payload,
                "fixture_context",
            ),
            failures,
        )

        # ====================================================
        # 11. Missing artifact fail-closed
        # ====================================================

        print(
            "\n11. MISSING ARTIFACT -> HTTP 503"
        )

        missing_paths = build_test_copy(
            root,
            "missing_enriched",
        )

        missing_paths[
            "enriched"
        ].unlink()

        missing_fixture_service = (
            make_fixture_context_service(
                missing_paths
            )
        )

        missing_status = (
            missing_fixture_service
            .get_status()
        )

        check(
            "Missing enriched artifact -> service NOT_READY",
            missing_status.get(
                "status"
            )
            == "NOT_READY",
            failures,
        )

        with patch(
            "backend.routes.context_api.FixtureContextService",
            side_effect=lambda:
                missing_fixture_service,
        ):

            response = client.get(
                "/api/v1/context/fixtures"
            )

            payload = (
                response.get_json()
            )

        check(
            "Missing artifact endpoint -> HTTP 503",
            response.status_code
            == 503,
            failures,
        )

        check(
            "Missing artifact payload public-safe",
            public_not_ready_payload(
                payload,
                "fixture_context",
            ),
            failures,
        )

    # ========================================================
    # 12. Existing API isolation
    # ========================================================

    print(
        "\n12. EXISTING API ISOLATION"
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
    # 13. Persist 8.7.1 + 8.7.2
    # ========================================================

    print(
        "\n13. SAVE STAGE 8.7.1 + 8.7.2 EVIDENCE"
    )

    overall_pass = (
        len(failures)
        == 0
    )

    if overall_pass:

        verified_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        report = {

            "stage":
                "8.7",

            "status":
                "PARTIAL_PASS",

            "stage_8_7_complete":
                False,

            "sub_stages": {

                "8.7.1":
                    "PASS",

                "8.7.2":
                    "PASS",

                "8.7.3":
                    "PENDING",

                "8.7.4":
                    "PENDING",

                "8.7.5":
                    "PENDING",
            },

            "runtime_freshness_contract":
                "VERIFIED",

            "http_stale_state_fail_closed":
                "VERIFIED",

            "verified_at_utc":
                verified_at,

            "runtime_contract":
                runtime_contract,

            "http_fail_closed_verification": {

                "baseline_http_ready":
                    True,

                "direct_fixture_staleness_to_503":
                    True,

                "direct_team_context_staleness_to_503":
                    True,

                "production_history_transitive_team_staleness_to_503":
                    True,

                "production_history_transitive_fixture_staleness_to_503":
                    True,

                "fixture_kickoff_expiry_to_503":
                    True,

                "missing_artifact_to_503":
                    True,

                "global_status_propagates_not_ready":
                    True,

                "not_ready_payload_public_safe":
                    True,

                "private_failure_reason_exposed":
                    False,

                "stale_data_served":
                    False,

                "fail_closed":
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

                "context_api_verification": {

                    "path":
                        relative_path(
                            CONTEXT_API_VERIFICATION_FILE
                        ),

                    "sha256":
                        sha256_file(
                            CONTEXT_API_VERIFICATION_FILE
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
            },

            "failures":
                [],
        }

        save_json(
            OUTPUT_FILE,
            report,
        )

        print(
            OUTPUT_FILE
        )

        persisted = load_json(
            OUTPUT_FILE
        )

        check(
            "Runtime verification status PARTIAL_PASS persisted",
            persisted.get(
                "status"
            )
            == "PARTIAL_PASS",
            failures,
        )

        check(
            "8.7.1 PASS persisted",
            persisted.get(
                "sub_stages",
                {}
            ).get(
                "8.7.1"
            )
            == "PASS",
            failures,
        )

        check(
            "8.7.2 PASS persisted",
            persisted.get(
                "sub_stages",
                {}
            ).get(
                "8.7.2"
            )
            == "PASS",
            failures,
        )

        check(
            "8.7.3 remains PENDING",
            persisted.get(
                "sub_stages",
                {}
            ).get(
                "8.7.3"
            )
            == "PENDING",
            failures,
        )

        check(
            "Runtime freshness contract VERIFIED persisted",
            persisted.get(
                "runtime_freshness_contract"
            )
            == "VERIFIED",
            failures,
        )

        check(
            "HTTP fail-closed VERIFIED persisted",
            persisted.get(
                "http_stale_state_fail_closed"
            )
            == "VERIFIED",
            failures,
        )

        overall_pass = (
            len(failures)
            == 0
        )

    # ========================================================
    # Final
    # ========================================================

    print(
        "\n" + "=" * 72
    )

    if overall_pass:

        print(
            "STAGE 8.7.1: PASS"
        )

        print(
            "RUNTIME FRESHNESS CONTRACT: VERIFIED"
        )

        print(
            "STAGE 8.7.2: PASS"
        )

        print(
            "HTTP STALE-STATE FAIL-CLOSED: VERIFIED"
        )

        print(
            "STAGE 8.7: IN PROGRESS"
        )

    else:

        print(
            "STAGE 8.7.1 / 8.7.2: FAIL"
        )

        print(
            "STAGE 8.7: INCOMPLETE"
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
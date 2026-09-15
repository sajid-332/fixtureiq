"""
FixtureIQ Stage 9.8.2
Final Runtime / REST API / Safety Gate.

Promotes Stage 9 to COMPLETE only if:
- 9.8.1 remains current
- live intelligence service is READY
- full API surface is healthy
- 404 / 405 semantics remain correct
- no-store policy remains active
- fail-closed 503 behavior remains correct
- Stage 9.7 negative/recovery evidence remains verified
- no Stage 9 artifact changes during final verification
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(
    BASE_DIR
) not in sys.path:

    sys.path.insert(
        0,
        str(
            BASE_DIR
        ),
    )


from backend.app import app

from backend.services.match_intelligence_service import (
    MatchIntelligenceNotReadyError,
    MatchIntelligenceService,
)


INTELLIGENCE_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "intelligence"
)

CONTRACT_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract.json"
)

CONTRACT_VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract_verification.json"
)

BASE_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_base.csv"
)

BASE_REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_base_report.json"
)

INTELLIGENCE_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence.csv"
)

REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_report.json"
)

API_VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "intelligence_api_verification.json"
)

RUNTIME_VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "intelligence_runtime_verification.json"
)

FINAL_FILE = (
    INTELLIGENCE_DIR
    / "stage9_final_verification.json"
)


EXPECTED_ROUTES = {

    "/api/v1/intelligence/status",

    "/api/v1/intelligence/matches",

    "/api/v1/intelligence/matches/<fixture_id>",

    "/api/v1/intelligence/team/<path:team_name>",

    "/api/v1/intelligence/upcoming",
}


class ForcedNotReadyService:

    def get_status(
        self,
    ) -> dict:

        return {

            "status":
                "NOT_READY",

            "stage":
                "9.7",

            "service":
                "match_intelligence",

            "reason":
                "Stage 9.8.2 forced stale-state test.",
        }

    def get_all_matches(
        self,
    ):

        raise MatchIntelligenceNotReadyError(
            "Forced stale state."
        )

    def get_match(
        self,
        fixture_id,
    ):

        raise MatchIntelligenceNotReadyError(
            "Forced stale state."
        )

    def get_team_matches(
        self,
        team_name,
    ):

        raise MatchIntelligenceNotReadyError(
            "Forced stale state."
        )

    def get_upcoming(
        self,
    ):

        raise MatchIntelligenceNotReadyError(
            "Forced stale state."
        )


def load_json(
    path: Path,
) -> dict:

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        payload = json.load(
            file
        )

    if not isinstance(
        payload,
        dict,
    ):

        raise RuntimeError(
            f"Expected JSON object: {path}"
        )

    return payload


def save_json_atomic(
    path: Path,
    payload: dict,
) -> None:

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temporary.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=2,
        )

    temporary.replace(
        path
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


def body(
    response,
) -> dict:

    payload = response.get_json(
        silent=True
    )

    if isinstance(
        payload,
        dict,
    ):

        return payload

    return {}


def no_store(
    response,
) -> bool:

    cache_control = str(
        response.headers.get(
            "Cache-Control",
            "",
        )
    ).lower()

    pragma = str(
        response.headers.get(
            "Pragma",
            "",
        )
    ).lower()

    expires = str(
        response.headers.get(
            "Expires",
            "",
        )
    )

    return (
        "no-store"
        in cache_control
        and
        "no-cache"
        in cache_control
        and
        pragma
        == "no-cache"
        and
        expires
        == "0"
    )


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 9.8.2"
    )

    print(
        "FINAL RUNTIME / REST API / SAFETY GATE"
    )

    print("=" * 72)

    failures = []

    # ========================================================
    # 1. 9.8.1 foundation
    # ========================================================

    print(
        "\n1. STAGE 9.8.1 FOUNDATION"
    )

    if not FINAL_FILE.exists():

        print(
            "stage9_final_verification.json: FAIL"
        )

        sys.exit(1)

    final_report = load_json(
        FINAL_FILE
    )

    check(
        "Stage 9.8.1 PASS",
        final_report.get(
            "stage_9_8_1",
            {}
        ).get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 9.8.2 currently PENDING",
        final_report.get(
            "stage_9_8_2",
            {}
        ).get(
            "status"
        )
        == "PENDING",
        failures,
    )

    # ========================================================
    # 2. 9.8.1 dependency snapshot still current
    # ========================================================

    print(
        "\n2. FINAL-GATE SNAPSHOT FRESHNESS"
    )

    dependencies = (
        final_report.get(
            "dependency_identity",
            {}
        )
    )

    expected_paths = [

        CONTRACT_FILE,
        CONTRACT_VERIFICATION_FILE,

        BASE_FILE,
        BASE_REPORT_FILE,

        INTELLIGENCE_FILE,
        REPORT_FILE,

        API_VERIFICATION_FILE,
        RUNTIME_VERIFICATION_FILE,
    ]

    for path in expected_paths:

        key = relative_path(
            path
        )

        check(
            f"{path.name} unchanged since 9.8.1",
            dependencies.get(
                key
            )
            ==
            sha256_file(
                path
            ),
            failures,
        )

    # ========================================================
    # 3. Stage 9.7 evidence
    # ========================================================

    print(
        "\n3. STAGE 9.7 FINAL SAFETY EVIDENCE"
    )

    runtime = load_json(
        RUNTIME_VERIFICATION_FILE
    )

    check(
        "Stage 9.7 PASS",
        runtime.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 9.7 COMPLETE",
        runtime.get(
            "stage_9_7_complete"
        )
        is True,
        failures,
    )

    check(
        "Runtime safety VERIFIED",
        runtime.get(
            "intelligence_runtime_safety"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Stage 9 ready for 9.8",
        runtime.get(
            "stage9_ready_for_9_8"
        )
        is True,
        failures,
    )

    check(
        "Runtime policy exact",
        runtime.get(
            "runtime_policy"
        )
        ==
        (
            "DUAL_UPSTREAM_DEPENDENCY_"
            "PLUS_TEMPORAL_BOUNDARY"
        ),
        failures,
    )

    runtime_contract = runtime.get(
        "runtime_contract",
        {}
    )

    check(
        "Runtime revalidates every read",
        runtime_contract.get(
            "revalidate_on_every_read"
        )
        is True,
        failures,
    )

    check(
        "Temporal boundary inherited",
        runtime_contract.get(
            "temporal_boundary_inherited"
        )
        is True,
        failures,
    )

    check(
        "Stale fallback false",
        runtime_contract.get(
            "stale_fallback"
        )
        is False,
        failures,
    )

    check(
        "Partial fallback false",
        runtime_contract.get(
            "partial_fallback"
        )
        is False,
        failures,
    )

    check(
        "Best effort fallback false",
        runtime_contract.get(
            "best_effort_fallback"
        )
        is False,
        failures,
    )

    check(
        "Recovery requires no restart",
        runtime_contract.get(
            "restart_required_for_recovery"
        )
        is False,
        failures,
    )

    negative_tests = runtime.get(
        "negative_tests",
        {}
    )

    for name in [

        "fixture_context_not_ready_rejected",
        "stale_read_rejected",
        "dynamic_dependency_mutation_rejected",
        "stage9_artifact_mutation_rejected",
        "stale_api_returns_503",
        "stale_api_payload_exact",
        "stale_response_no_store",
    ]:

        check(
            f"Runtime negative test {name}",
            negative_tests.get(
                name
            )
            is True,
            failures,
        )

    recovery_tests = runtime.get(
        "recovery_tests",
        {}
    )

    for name in [

        "fixture_context_stale_to_ready_same_service",
        "dependency_stale_to_ready_same_service",
        "artifact_stale_to_ready_same_service",
    ]:

        check(
            f"Runtime recovery test {name}",
            recovery_tests.get(
                name
            )
            is True,
            failures,
        )

    # ========================================================
    # 4. Live service
    # ========================================================

    print(
        "\n4. LIVE MATCH INTELLIGENCE SERVICE"
    )

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

        print(
            "Runtime reason:",
            status.get(
                "reason"
            ),
        )

    check(
        "Live service READY",
        status.get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "Live service stage 9.7",
        status.get(
            "stage"
        )
        == "9.7",
        failures,
    )

    check(
        "Live runtime policy exact",
        status.get(
            "runtime_policy"
        )
        ==
        (
            "DUAL_UPSTREAM_DEPENDENCY_"
            "PLUS_TEMPORAL_BOUNDARY"
        ),
        failures,
    )

    check(
        "Live stale fallback false",
        status.get(
            "stale_fallback"
        )
        is False,
        failures,
    )

    matches = []

    if (
        status.get(
            "status"
        )
        == "READY"
    ):

        try:

            matches = service.get_all_matches()

        except Exception as exc:

            print(
                "Live read error:",
                exc,
            )

    check(
        "Live intelligence rows > 0",
        len(
            matches
        )
        > 0,
        failures,
    )

    # ========================================================
    # 5. REST route contract
    # ========================================================

    print(
        "\n5. FINAL REST API SURFACE"
    )

    actual_routes = {

        rule.rule

        for rule in app.url_map.iter_rules()

        if rule.rule.startswith(
            "/api/v1/intelligence"
        )
    }

    check(
        "Exactly 5 intelligence routes",
        len(
            actual_routes
        )
        == 5,
        failures,
    )

    check(
        "Intelligence route set exact",
        actual_routes
        ==
        EXPECTED_ROUTES,
        failures,
    )

    for rule in app.url_map.iter_rules():

        if not rule.rule.startswith(
            "/api/v1/intelligence"
        ):

            continue

        methods = set(
            rule.methods
        )

        check(
            f"{rule.rule} GET enabled",
            "GET"
            in methods,
            failures,
        )

        check(
            f"{rule.rule} POST disabled",
            "POST"
            not in methods,
            failures,
        )

        check(
            f"{rule.rule} PUT disabled",
            "PUT"
            not in methods,
            failures,
        )

        check(
            f"{rule.rule} DELETE disabled",
            "DELETE"
            not in methods,
            failures,
        )

    # ========================================================
    # 6. Healthy API
    # ========================================================

    print(
        "\n6. LIVE REST API"
    )

    client = app.test_client()

    healthy_paths = [

        "/api/v1/intelligence/status",
        "/api/v1/intelligence/matches",
        "/api/v1/intelligence/upcoming",
    ]

    if matches:

        first = matches[
            0
        ]

        healthy_paths.extend(
            [

                (
                    "/api/v1/intelligence/matches/"
                    f"{first['fixture_id']}"
                ),

                (
                    "/api/v1/intelligence/team/"
                    f"{first['home_team_name']}"
                ),
            ]
        )

    for path in healthy_paths:

        response = client.get(
            path
        )

        check(
            f"GET {path} -> 200",
            response.status_code
            == 200,
            failures,
        )

        check(
            f"GET {path} READY",
            body(
                response
            ).get(
                "status"
            )
            == "READY",
            failures,
        )

        check(
            f"GET {path} no-store",
            no_store(
                response
            ),
            failures,
        )

    # ========================================================
    # 7. 404
    # ========================================================

    print(
        "\n7. UNKNOWN IDENTITY CONTRACT"
    )

    unknown_fixture = client.get(
        (
            "/api/v1/intelligence/matches/"
            "__fixtureiq_stage9_final_unknown__"
        )
    )

    check(
        "Unknown fixture -> 404",
        unknown_fixture.status_code
        == 404,
        failures,
    )

    check(
        "Unknown fixture payload exact",
        body(
            unknown_fixture
        )
        ==
        {
            "status":
                "NOT_FOUND",

            "service":
                "match_intelligence",
        },
        failures,
    )

    check(
        "Unknown fixture no-store",
        no_store(
            unknown_fixture
        ),
        failures,
    )

    unknown_team = client.get(
        (
            "/api/v1/intelligence/team/"
            "__fixtureiq_stage9_final_unknown_team__"
        )
    )

    check(
        "Unknown team -> 404",
        unknown_team.status_code
        == 404,
        failures,
    )

    check(
        "Unknown team no-store",
        no_store(
            unknown_team
        ),
        failures,
    )

    # ========================================================
    # 8. 405
    # ========================================================

    print(
        "\n8. READ-ONLY FINAL CONTRACT"
    )

    write_targets = [

        "/api/v1/intelligence/status",

        "/api/v1/intelligence/matches",

        "/api/v1/intelligence/upcoming",
    ]

    for path in write_targets:

        for method in [
            "post",
            "put",
            "delete",
        ]:

            response = getattr(
                client,
                method,
            )(
                path
            )

            check(
                (
                    f"{method.upper()} "
                    f"{path} -> 405"
                ),
                response.status_code
                == 405,
                failures,
            )

            check(
                (
                    f"{method.upper()} "
                    f"{path} no-store"
                ),
                no_store(
                    response
                ),
                failures,
            )

    # ========================================================
    # 9. Independent forced stale API
    # ========================================================

    print(
        "\n9. FINAL FAIL-CLOSED API TEST"
    )

    with patch(
        (
            "backend.routes.intelligence_api."
            "MatchIntelligenceService"
        ),
        ForcedNotReadyService,
    ):

        stale_client = app.test_client()

        for path in [

            "/api/v1/intelligence/status",
            "/api/v1/intelligence/matches",
            "/api/v1/intelligence/upcoming",
        ]:

            response = stale_client.get(
                path
            )

            check(
                f"Forced stale {path} -> 503",
                response.status_code
                == 503,
                failures,
            )

            check(
                f"Forced stale {path} payload exact",
                body(
                    response
                )
                ==
                {
                    "status":
                        "NOT_READY",

                    "service":
                        "match_intelligence",
                },
                failures,
            )

            check(
                f"Forced stale {path} no-store",
                no_store(
                    response
                ),
                failures,
            )

    # ========================================================
    # 10. Final write protection
    # ========================================================

    print(
        "\n10. FINAL STAGE 9 WRITE PROTECTION"
    )

    dependencies = (
        final_report.get(
            "dependency_identity",
            {}
        )
    )

    for path in expected_paths:

        key = relative_path(
            path
        )

        check(
            f"{path.name} still unchanged",
            dependencies.get(
                key
            )
            ==
            sha256_file(
                path
            ),
            failures,
        )

    # ========================================================
    # 11. Promote final Stage 9 verification
    # ========================================================

    print(
        "\n11. FINAL STAGE 9 PROMOTION"
    )

    overall_pass = (
        len(
            failures
        )
        == 0
    )

    if overall_pass:

        completed_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        final_report[
            "status"
        ] = "PASS"

        final_report[
            "stage_9_8_complete"
        ] = True

        final_report[
            "stage_9_complete"
        ] = True

        final_report[
            "match_intelligence_layer"
        ] = "VERIFIED"

        final_report[
            "fixtureiq_stage9_final_gate"
        ] = "PASS"

        final_report[
            "stage_9_8_2"
        ] = {

            "status":
                "PASS",

            "name":
                "FINAL_RUNTIME_API_SAFETY_GATE",

            "verified_at_utc":
                completed_at,

            "live_service_ready":
                True,

            "runtime_policy_verified":
                True,

            "api_surface_exact":
                True,

            "healthy_api_verified":
                True,

            "not_found_contract_verified":
                True,

            "read_only_contract_verified":
                True,

            "fail_closed_503_verified":
                True,

            "no_store_verified":
                True,

            "stale_fallback":
                False,

            "same_process_recovery_verified":
                True,
        }

        final_report[
            "completed_at_utc"
        ] = completed_at

        final_report[
            "next_stage"
        ] = None

        final_report[
            "failures"
        ] = []

        save_json_atomic(
            FINAL_FILE,
            final_report,
        )

        persisted = load_json(
            FINAL_FILE
        )

        check(
            "Stage 9.8 COMPLETE persisted",
            persisted.get(
                "stage_9_8_complete"
            )
            is True,
            failures,
        )

        check(
            "Stage 9 COMPLETE persisted",
            persisted.get(
                "stage_9_complete"
            )
            is True,
            failures,
        )

        check(
            "Match Intelligence Layer VERIFIED persisted",
            persisted.get(
                "match_intelligence_layer"
            )
            == "VERIFIED",
            failures,
        )

        check(
            "FixtureIQ Stage 9 final gate PASS persisted",
            persisted.get(
                "fixtureiq_stage9_final_gate"
            )
            == "PASS",
            failures,
        )

        overall_pass = (
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

    if overall_pass:

        print(
            "STAGE 9.8.2: PASS"
        )

        print(
            "FINAL RUNTIME / REST API / SAFETY GATE: VERIFIED"
        )

        print()
        print(
            "STAGE 9.8: COMPLETE"
        )

        print(
            "STAGE 9: COMPLETE"
        )

        print(
            "MATCH INTELLIGENCE LAYER: VERIFIED"
        )

        print(
            "FIXTUREIQ STAGE 9 FINAL GATE: PASS"
        )

    else:

        print(
            "STAGE 9.8.2: FAIL"
        )

        print(
            "STAGE 9: INCOMPLETE"
        )

        print(
            "MATCH INTELLIGENCE LAYER: NOT VERIFIED"
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
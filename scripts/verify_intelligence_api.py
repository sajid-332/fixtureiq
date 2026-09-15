"""
FixtureIQ Stage 9.6
Match Intelligence REST API Verification.

Verifies:
- exact Stage 9 API surface
- healthy responses
- public-field projection
- fixture lookup
- team lookup
- unknown fixture/team -> 404
- writes -> 405
- artifact-only behavior
- existing Stage 7 / Stage 8 routes preserved
- no source artifact mutation

Stage 9.7 will add runtime freshness/cache/fail-closed
transition verification.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


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


from backend.app import app

from backend.services.match_intelligence_service import (
    MatchIntelligenceService,
)


# ============================================================
# Paths
# ============================================================

INTELLIGENCE_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "intelligence"
)

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

OUTPUT_FILE = (
    INTELLIGENCE_DIR
    / "intelligence_api_verification.json"
)


# ============================================================
# Expected API
# ============================================================

EXPECTED_STAGE9_ROUTES = {

    "/api/v1/intelligence/status",

    "/api/v1/intelligence/matches",

    "/api/v1/intelligence/matches/<fixture_id>",

    "/api/v1/intelligence/team/<path:team_name>",

    "/api/v1/intelligence/upcoming",
}


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

        return json.load(
            file
        )


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


def json_body(
    response,
) -> dict:

    payload = response.get_json(
        silent=True
    )

    if not isinstance(
        payload,
        dict,
    ):

        return {}

    return payload


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 9.6"
    )

    print(
        "MATCH INTELLIGENCE REST API VERIFICATION"
    )

    print("=" * 72)

    failures = []

    # ========================================================
    # 1. Foundation
    # ========================================================

    print(
        "\n1. STAGE 9.5 FOUNDATION"
    )

    report = load_json(
        REPORT_FILE
    )

    check(
        "Stage 9.3 COMPLETE",
        report.get(
            "stage_9_3_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 9.4 COMPLETE",
        report.get(
            "stage_9_4_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 9.5 COMPLETE",
        report.get(
            "stage_9_5_complete"
        )
        is True,
        failures,
    )

    check(
        "Explanation Engine VERIFIED",
        report.get(
            "match_explanation_engine"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Stage 9 ready for 9.6",
        report.get(
            "stage9_ready_for_9_6"
        )
        is True,
        failures,
    )

    if failures:

        sys.exit(1)

    # ========================================================
    # Protected files
    # ========================================================

    protected_paths = [

        CONTRACT_FILE,
        CONTRACT_VERIFICATION_FILE,

        BASE_FILE,
        BASE_REPORT_FILE,

        INTELLIGENCE_FILE,
        REPORT_FILE,

        PRODUCTION_DIR
        / "production_predictions.csv",

        CONTEXT_DIR
        / "enriched_upcoming_fixtures.csv",
    ]

    protected_before = {

        relative_path(
            path
        ):
            sha256_file(
                path
            )

        for path in protected_paths
    }

    # ========================================================
    # 2. Service readiness
    # ========================================================

    print(
        "\n2. INTELLIGENCE SERVICE"
    )

    service = (
        MatchIntelligenceService()
    )

    status = service.get_status()

    check(
        "Service READY",
        status.get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "Service name exact",
        status.get(
            "service"
        )
        == "match_intelligence",
        failures,
    )

    check(
        "Fixture count > 0",
        status.get(
            "fixture_count",
            0,
        )
        > 0,
        failures,
    )

    matches = (
        service.get_all_matches()
    )

    check(
        "Service count consistent",
        len(
            matches
        )
        ==
        status.get(
            "fixture_count"
        ),
        failures,
    )

    first_match = (
        matches[
            0
        ]
        if matches
        else {}
    )

    fixture_id = str(
        first_match.get(
            "fixture_id",
            "",
        )
    )

    home_team_name = str(
        first_match.get(
            "home_team_name",
            "",
        )
    )

    check(
        "Fixture ID available",
        bool(
            fixture_id
        ),
        failures,
    )

    check(
        "Home team available",
        bool(
            home_team_name
        ),
        failures,
    )

    # ========================================================
    # 3. Exact route surface
    # ========================================================

    print(
        "\n3. REST ROUTE SURFACE"
    )

    stage9_routes = {

        rule.rule

        for rule in app.url_map.iter_rules()

        if rule.rule.startswith(
            "/api/v1/intelligence"
        )
    }

    check(
        "Exactly 5 Stage 9 intelligence routes",
        len(
            stage9_routes
        )
        == 5,
        failures,
    )

    check(
        "Stage 9 route set exact",
        stage9_routes
        ==
        EXPECTED_STAGE9_ROUTES,
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
    # Flask test client
    # ========================================================

    client = app.test_client()

    # ========================================================
    # 4. Status endpoint
    # ========================================================

    print(
        "\n4. STATUS ENDPOINT"
    )

    response = client.get(
        "/api/v1/intelligence/status"
    )

    payload = json_body(
        response
    )

    check(
        "Status HTTP 200",
        response.status_code
        == 200,
        failures,
    )

    check(
        "Status READY",
        payload.get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "Status service exact",
        payload.get(
            "service"
        )
        == "match_intelligence",
        failures,
    )

    check(
        "Status fixture count consistent",
        payload.get(
            "fixture_count"
        )
        ==
        len(
            matches
        ),
        failures,
    )

    # ========================================================
    # 5. All matches endpoint
    # ========================================================

    print(
        "\n5. ALL MATCHES ENDPOINT"
    )

    response = client.get(
        "/api/v1/intelligence/matches"
    )

    payload = json_body(
        response
    )

    api_matches = payload.get(
        "matches",
        []
    )

    check(
        "Matches HTTP 200",
        response.status_code
        == 200,
        failures,
    )

    check(
        "Matches READY",
        payload.get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "Matches count exact",
        payload.get(
            "count"
        )
        ==
        len(
            matches
        ),
        failures,
    )

    check(
        "Matches array exact count",
        len(
            api_matches
        )
        ==
        len(
            matches
        ),
        failures,
    )

    # ========================================================
    # Public projection
    # ========================================================

    if api_matches:

        public = api_matches[
            0
        ]

        required_public = [

            "fixture_id",

            "home_team_id",
            "home_team_name",

            "away_team_id",
            "away_team_name",

            "stage7_prob_home_win",
            "stage7_prob_draw",
            "stage7_prob_away_win",

            "stage7_predicted_label",
            "stage7_confidence",

            "stage9_top_probability",
            "stage9_second_probability",
            "stage9_probability_margin",

            "stage9_entropy",
            "stage9_normalized_entropy",

            "stage9_confidence_band",
            "stage9_uncertainty_band",

            "stage9_context_support_score",
            "stage9_context_alignment",

            "stage9_explanation_headline",
            "stage9_explanation_summary",
        ]

        for field in required_public:

            check(
                f"Public field {field}",
                field in public,
                failures,
            )

        forbidden_public = [

            "model_sha256",
            "model_id",
            "feature_count",
            "target",
            "result",
            "full_time_home_goals",
            "full_time_away_goals",
        ]

        for field in forbidden_public:

            check(
                f"Private/internal field {field} not exposed",
                field not in public,
                failures,
            )

    # ========================================================
    # 6. Fixture endpoint
    # ========================================================

    print(
        "\n6. FIXTURE ENDPOINT"
    )

    response = client.get(
        (
            "/api/v1/intelligence/matches/"
            f"{fixture_id}"
        )
    )

    payload = json_body(
        response
    )

    match_payload = payload.get(
        "match",
        {}
    )

    check(
        "Fixture HTTP 200",
        response.status_code
        == 200,
        failures,
    )

    check(
        "Fixture READY",
        payload.get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "Fixture ID exact",
        str(
            match_payload.get(
                "fixture_id"
            )
        )
        ==
        fixture_id,
        failures,
    )

    # ========================================================
    # 7. Team endpoint
    # ========================================================

    print(
        "\n7. TEAM ENDPOINT"
    )

    response = client.get(
        (
            "/api/v1/intelligence/team/"
            f"{home_team_name}"
        )
    )

    payload = json_body(
        response
    )

    team_matches = payload.get(
        "matches",
        []
    )

    check(
        "Team HTTP 200",
        response.status_code
        == 200,
        failures,
    )

    check(
        "Team READY",
        payload.get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "Team count > 0",
        payload.get(
            "count",
            0,
        )
        > 0,
        failures,
    )

    check(
        "Every returned fixture contains team",
        all(

            _team_matches(
                item,
                home_team_name,
            )

            for item in team_matches
        ),
        failures,
    )

    # Case-only variation should still resolve.
    response = client.get(
        (
            "/api/v1/intelligence/team/"
            f"{home_team_name.upper()}"
        )
    )

    check(
        "Team case-insensitive exact lookup HTTP 200",
        response.status_code
        == 200,
        failures,
    )

    # ========================================================
    # 8. Upcoming endpoint
    # ========================================================

    print(
        "\n8. UPCOMING ENDPOINT"
    )

    response = client.get(
        "/api/v1/intelligence/upcoming"
    )

    payload = json_body(
        response
    )

    check(
        "Upcoming HTTP 200",
        response.status_code
        == 200,
        failures,
    )

    check(
        "Upcoming READY",
        payload.get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "Upcoming count exact",
        payload.get(
            "count"
        )
        ==
        len(
            matches
        ),
        failures,
    )

    # ========================================================
    # 9. Unknown identities
    # ========================================================

    print(
        "\n9. UNKNOWN IDENTITY RESPONSES"
    )

    response = client.get(
        (
            "/api/v1/intelligence/matches/"
            "__fixtureiq_unknown_fixture__"
        )
    )

    payload = json_body(
        response
    )

    check(
        "Unknown fixture HTTP 404",
        response.status_code
        == 404,
        failures,
    )

    check(
        "Unknown fixture status NOT_FOUND",
        payload.get(
            "status"
        )
        == "NOT_FOUND",
        failures,
    )

    response = client.get(
        (
            "/api/v1/intelligence/team/"
            "__fixtureiq_unknown_team__"
        )
    )

    payload = json_body(
        response
    )

    check(
        "Unknown team HTTP 404",
        response.status_code
        == 404,
        failures,
    )

    check(
        "Unknown team status NOT_FOUND",
        payload.get(
            "status"
        )
        == "NOT_FOUND",
        failures,
    )

    # ========================================================
    # 10. Write methods
    # ========================================================

    print(
        "\n10. READ-ONLY HTTP CONTRACT"
    )

    write_targets = [

        "/api/v1/intelligence/status",

        "/api/v1/intelligence/matches",

        (
            "/api/v1/intelligence/matches/"
            f"{fixture_id}"
        ),

        (
            "/api/v1/intelligence/team/"
            f"{home_team_name}"
        ),

        "/api/v1/intelligence/upcoming",
    ]

    for path in write_targets:

        check(
            f"POST {path} -> 405",
            client.post(
                path
            ).status_code
            == 405,
            failures,
        )

        check(
            f"PUT {path} -> 405",
            client.put(
                path
            ).status_code
            == 405,
            failures,
        )

        check(
            f"DELETE {path} -> 405",
            client.delete(
                path
            ).status_code
            == 405,
            failures,
        )

    # ========================================================
    # 11. Existing APIs preserved
    # ========================================================

    print(
        "\n11. EXISTING API PRESERVATION"
    )

    check(
        "Global health route preserved",
        client.get(
            "/api/health"
        ).status_code
        == 200,
        failures,
    )

    check(
        "Stage 7 production status route preserved",
        (
            "/api/v1/production/status"
            in {
                rule.rule
                for rule in app.url_map.iter_rules()
            }
        ),
        failures,
    )

    check(
        "Stage 8 context status route preserved",
        (
            "/api/v1/context/status"
            in {
                rule.rule
                for rule in app.url_map.iter_rules()
            }
        ),
        failures,
    )

    # ========================================================
    # 12. Artifact-only safety
    # ========================================================

    print(
        "\n12. ARTIFACT-ONLY SAFETY"
    )

    for path in protected_paths:

        key = relative_path(
            path
        )

        check(
            f"{path.name} unchanged",
            sha256_file(
                path
            )
            ==
            protected_before[
                key
            ],
            failures,
        )

    check(
        "API verification did not modify intelligence",
        sha256_file(
            INTELLIGENCE_FILE
        )
        ==
        protected_before[
            relative_path(
                INTELLIGENCE_FILE
            )
        ],
        failures,
    )

    # ========================================================
    # 13. Save Stage 9.6 verification
    # ========================================================

    print(
        "\n13. SAVE STAGE 9.6 VERIFICATION"
    )

    overall_pass = (
        len(
            failures
        )
        == 0
    )

    if overall_pass:

        verified_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        artifact = {

            "stage":
                "9.6",

            "status":
                "PASS",

            "stage_9_6_complete":
                True,

            "stage_9_6_status":
                "COMPLETE",

            "match_intelligence_rest_api":
                "VERIFIED",

            "verified_at_utc":
                verified_at,

            "service":
                "match_intelligence",

            "route_count":
                5,

            "routes": [

                "GET /api/v1/intelligence/status",

                "GET /api/v1/intelligence/matches",

                (
                    "GET /api/v1/intelligence/"
                    "matches/<fixture_id>"
                ),

                (
                    "GET /api/v1/intelligence/"
                    "team/<team_name>"
                ),

                "GET /api/v1/intelligence/upcoming",
            ],

            "fixture_count":
                len(
                    matches
                ),

            "api_contract": {

                "read_only":
                    True,

                "artifact_only":
                    True,

                "healthy_status_code":
                    200,

                "unknown_status_code":
                    404,

                "not_ready_status_code":
                    503,

                "write_status_code":
                    405,

                "unknown_status":
                    "NOT_FOUND",

                "not_ready_status":
                    "NOT_READY",

                "service_name":
                    "match_intelligence",

                "provider_fetch_in_request":
                    False,

                "artifact_rebuild_in_request":
                    False,

                "model_load_in_request":
                    False,

                "model_execution_in_request":
                    False,

                "probability_mutation":
                    False,
            },

            "dependency_identity": {

                "stage9_intelligence_contract": {

                    "path":
                        relative_path(
                            CONTRACT_FILE
                        ),

                    "sha256":
                        sha256_file(
                            CONTRACT_FILE
                        ),
                },

                "stage9_intelligence_contract_verification": {

                    "path":
                        relative_path(
                            CONTRACT_VERIFICATION_FILE
                        ),

                    "sha256":
                        sha256_file(
                            CONTRACT_VERIFICATION_FILE
                        ),
                },

                "match_intelligence_base": {

                    "path":
                        relative_path(
                            BASE_FILE
                        ),

                    "sha256":
                        sha256_file(
                            BASE_FILE
                        ),
                },

                "match_intelligence_base_report": {

                    "path":
                        relative_path(
                            BASE_REPORT_FILE
                        ),

                    "sha256":
                        sha256_file(
                            BASE_REPORT_FILE
                        ),
                },

                "match_intelligence": {

                    "path":
                        relative_path(
                            INTELLIGENCE_FILE
                        ),

                    "sha256":
                        sha256_file(
                            INTELLIGENCE_FILE
                        ),
                },

                "match_intelligence_report": {

                    "path":
                        relative_path(
                            REPORT_FILE
                        ),

                    "sha256":
                        sha256_file(
                            REPORT_FILE
                        ),
                },
            },

            "safety": {

                "read_only":
                    True,

                "artifact_only":
                    True,

                "provider_fetch_performed":
                    False,

                "artifact_rebuild_performed":
                    False,

                "model_loaded":
                    False,

                "model_executed":
                    False,

                "model_modified":
                    False,

                "probabilities_modified":
                    False,

                "prediction_labels_modified":
                    False,

                "context_modified":
                    False,

                "explanations_generated_at_request_time":
                    False,

                "stage7_routes_preserved":
                    True,

                "stage8_routes_preserved":
                    True,
            },

            "stage9_ready_for_9_7":
                True,

            "next_stage":
                "9.7",

            "failures":
                [],
        }

        save_json_atomic(
            OUTPUT_FILE,
            artifact,
        )

        print(
            OUTPUT_FILE
        )

    print(
        "\n" + "=" * 72
    )

    if overall_pass:

        print(
            "STAGE 9.6: COMPLETE"
        )

        print(
            "MATCH INTELLIGENCE REST API: VERIFIED"
        )

        print(
            "STAGE 9 READY FOR 9.7"
        )

    else:

        print(
            "STAGE 9.6: FAIL"
        )

        print(
            "MATCH INTELLIGENCE REST API: NOT VERIFIED"
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


def _team_matches(
    item: dict,
    team_name: str,
) -> bool:

    requested = (
        str(
            team_name
        )
        .strip()
        .casefold()
    )

    home = (
        str(
            item.get(
                "home_team_name",
                "",
            )
        )
        .strip()
        .casefold()
    )

    away = (
        str(
            item.get(
                "away_team_name",
                "",
            )
        )
        .strip()
        .casefold()
    )

    return (
        requested == home
        or
        requested == away
    )


if __name__ == "__main__":

    main()
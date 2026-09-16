from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(ROOT) not in sys.path:

    sys.path.insert(
        0,
        str(ROOT),
    )


from backend.app import app


CONTRACT_FILE = (
    ROOT
    / "docs"
    / "stage10"
    / "frontend_api_endpoint_contract.json"
)

RESPONSIBILITY_FILE = (
    ROOT
    / "docs"
    / "stage10"
    / "frontend_responsibility_contract.json"
)

PREVIOUS_VERIFICATION_FILE = (
    ROOT
    / "data"
    / "processed"
    / "frontend"
    / "stage10_1_1_10_1_2_verification.json"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "processed"
    / "frontend"
    / "stage10_1_3_verification.json"
)


ALLOWED_PREFIXES = (
    "/api/health",
    "/api/v1/production",
    "/api/v1/context",
    "/api/v1/intelligence",
)

AUTOMATIC_METHODS = {
    "HEAD",
    "OPTIONS",
}

WRITE_METHODS = {
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
}


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


def sha256_file(
    path: Path,
) -> str:

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as file:

        for chunk in iter(
            lambda:
                file.read(
                    1024 * 1024
                ),
            b"",
        ):

            digest.update(
                chunk
            )

    return digest.hexdigest()


def relative(
    path: Path,
) -> str:

    return (
        str(
            path.resolve()
            .relative_to(
                ROOT.resolve()
            )
        )
        .replace(
            "\\",
            "/",
        )
    )


def resolve_project_path(
    value: str,
) -> Path:

    raw = Path(
        str(value)
    )

    if raw.is_absolute():

        resolved = raw.resolve()

    else:

        resolved = (
            ROOT
            / raw
        ).resolve()

    resolved.relative_to(
        ROOT.resolve()
    )

    return resolved


def save_json_atomic(
    path: Path,
    payload: dict,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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

        file.write(
            "\n"
        )

    temporary.replace(
        path
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


def is_frontend_namespace(
    route: str,
) -> bool:

    return (
        route == "/api/health"
        or
        route.startswith(
            "/api/v1/production"
        )
        or
        route.startswith(
            "/api/v1/context"
        )
        or
        route.startswith(
            "/api/v1/intelligence"
        )
    )


def current_routes() -> list[dict]:

    result = []

    for rule in app.url_map.iter_rules():

        if not is_frontend_namespace(
            rule.rule
        ):

            continue

        methods = sorted(
            set(
                rule.methods
            )
        )

        explicit_methods = sorted(
            method

            for method in methods

            if method
            not in
            AUTOMATIC_METHODS
        )

        result.append(
            {
                "route":
                    rule.rule,

                "endpoint":
                    rule.endpoint,

                "methods":
                    methods,

                "explicit_methods":
                    explicit_methods,
            }
        )

    result.sort(
        key=lambda item:
            item[
                "route"
            ]
    )

    return result


def verify_dependency_identity(
    payload: dict,
    failures: list[str],
) -> None:

    identities = payload.get(
        "dependency_identity",
        {}
    )

    check(
        "Contract dependency identity exists",
        isinstance(
            identities,
            dict,
        )
        and
        bool(
            identities
        ),
        failures,
    )

    if not isinstance(
        identities,
        dict,
    ):

        return

    for (
        path_text,
        identity,
    ) in identities.items():

        expected_sha = (
            identity.get(
                "sha256",
                ""
            )
            if isinstance(
                identity,
                dict,
            )
            else ""
        )

        try:

            path = resolve_project_path(
                path_text
            )

            current = (
                path.exists()
                and
                sha256_file(
                    path
                )
                ==
                expected_sha
            )

        except Exception:

            current = False

        check(
            (
                f"Dependency current: "
                f"{Path(path_text).name}"
            ),
            current,
            failures,
        )


def verify_source_identity(
    contract: dict,
    failures: list[str],
) -> None:

    identities = contract.get(
        "source_identity",
        {}
    )

    check(
        "Route source identity exists",
        isinstance(
            identities,
            dict,
        )
        and
        bool(
            identities
        ),
        failures,
    )

    if not isinstance(
        identities,
        dict,
    ):

        return

    for (
        path_text,
        identity,
    ) in identities.items():

        try:

            path = resolve_project_path(
                path_text
            )

            expected_sha = str(
                identity.get(
                    "sha256",
                    ""
                )
            )

            current = (
                path.exists()
                and
                sha256_file(
                    path
                )
                ==
                expected_sha
            )

        except Exception:

            current = False

        check(
            (
                f"Route source current: "
                f"{Path(path_text).name}"
            ),
            current,
            failures,
        )


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.1.3"
    )

    print(
        "ALLOWED BACKEND API ENDPOINT VERIFICATION"
    )

    print("=" * 72)

    failures: list[str] = []

    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    for path in [
        CONTRACT_FILE,
        RESPONSIBILITY_FILE,
        PREVIOUS_VERIFICATION_FILE,
    ]:

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

    responsibility = load_json(
        RESPONSIBILITY_FILE
    )

    previous = load_json(
        PREVIOUS_VERIFICATION_FILE
    )

    print(
        "\n2. PREVIOUS STAGE 10 FOUNDATION"
    )

    check(
        "10.1.1-10.1.2 status PASS",
        previous.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )

    check(
        "10.1.1 complete",
        previous.get(
            "stage_10_1_1_complete"
        )
        is True,
        failures,
    )

    check(
        "10.1.2 complete",
        previous.get(
            "stage_10_1_2_complete"
        )
        is True,
        failures,
    )

    check(
        "10.1.2 boundary LOCKED",
        responsibility.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )

    check(
        "10.1.2 authorized 10.1.3",
        previous.get(
            "stage10_ready_for_10_1_3"
        )
        is True,
        failures,
    )

    print(
        "\n3. ENDPOINT CONTRACT"
    )

    check(
        "Contract stage exact",
        contract.get(
            "stage"
        )
        ==
        "10.1.3",
        failures,
    )

    check(
        "Contract version exact",
        contract.get(
            "version"
        )
        ==
        "1.0.0",
        failures,
    )

    check(
        "Contract status LOCKED",
        contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )

    check(
        "Flask URL map is source of truth",
        contract.get(
            "source_of_truth"
        )
        ==
        "FLASK_APP_URL_MAP",
        failures,
    )

    check(
        "Transport HTTP JSON",
        contract.get(
            "frontend_transport"
        )
        ==
        "HTTP_JSON",
        failures,
    )

    check(
        "GET is only allowed frontend method",
        contract.get(
            "allowed_http_methods"
        )
        ==
        ["GET"],
        failures,
    )

    check(
        "Primary user-facing source is Stage 9 intelligence",
        contract.get(
            "primary_user_facing_source"
        )
        ==
        "/api/v1/intelligence",
        failures,
    )

    print(
        "\n4. CURRENT FLASK ROUTE MAP"
    )

    current = current_routes()

    current_route_strings = sorted(
        item[
            "route"
        ]

        for item in current
    )

    locked_route_strings = sorted(
        contract.get(
            "route_set",
            []
        )
    )

    check(
        "At least one frontend API route exists",
        len(
            current
        )
        >
        0,
        failures,
    )

    check(
        "Current route count matches lock",
        len(
            current
        )
        ==
        contract.get(
            "route_count"
        ),
        failures,
    )

    check(
        "Current route set exactly matches lock",
        current_route_strings
        ==
        locked_route_strings,
        failures,
    )

    locked_by_route = {
        item[
            "route"
        ]:
            item

        for item
        in contract.get(
            "routes",
            []
        )
    }

    for item in current:

        route = item[
            "route"
        ]

        locked = locked_by_route.get(
            route
        )

        check(
            f"{route}: exists in contract",
            locked
            is not None,
            failures,
        )

        if locked is None:

            continue

        check(
            f"{route}: Flask endpoint unchanged",
            locked.get(
                "endpoint"
            )
            ==
            item[
                "endpoint"
            ],
            failures,
        )

        check(
            f"{route}: methods unchanged",
            locked.get(
                "methods"
            )
            ==
            item[
                "methods"
            ],
            failures,
        )

        check(
            f"{route}: GET enabled",
            "GET"
            in item[
                "explicit_methods"
            ],
            failures,
        )

        check(
            f"{route}: no write methods",
            not (
                set(
                    item[
                        "explicit_methods"
                    ]
                )
                &
                WRITE_METHODS
            ),
            failures,
        )

    print(
        "\n5. NAMESPACE AUTHORITY"
    )

    authority = contract.get(
        "authority",
        {}
    )

    check(
        "Production owned by Stage 7",
        authority.get(
            "production"
        )
        ==
        "STAGE7_PREDICTION_AUTHORITY",
        failures,
    )

    check(
        "Context owned by Stage 8",
        authority.get(
            "context"
        )
        ==
        "STAGE8_CONTEXT_AUTHORITY",
        failures,
    )

    check(
        "Intelligence owned by Stage 9",
        authority.get(
            "intelligence"
        )
        ==
        "STAGE9_INTELLIGENCE_AUTHORITY",
        failures,
    )

    check(
        "Frontend presentation-only",
        authority.get(
            "frontend"
        )
        ==
        "PRESENTATION_ONLY",
        failures,
    )

    namespace_counts = contract.get(
        "namespace_counts",
        {}
    )

    check(
        "Health namespace exists",
        namespace_counts.get(
            "health",
            0
        )
        >=
        1,
        failures,
    )

    check(
        "Production namespace exists",
        namespace_counts.get(
            "production",
            0
        )
        >
        0,
        failures,
    )

    check(
        "Context namespace exists",
        namespace_counts.get(
            "context",
            0
        )
        >
        0,
        failures,
    )

    check(
        "Intelligence namespace has exactly 5 routes",
        namespace_counts.get(
            "intelligence"
        )
        ==
        5,
        failures,
    )

    print(
        "\n6. STAGE 9 INTELLIGENCE ROUTE LOCK"
    )

    expected_intelligence = sorted(
        [
            "/api/v1/intelligence/status",
            "/api/v1/intelligence/matches",
            "/api/v1/intelligence/matches/<fixture_id>",
            "/api/v1/intelligence/team/<path:team_name>",
            "/api/v1/intelligence/upcoming",
        ]
    )

    locked_intelligence = sorted(
        contract.get(
            "verified_stage9_intelligence_routes",
            []
        )
    )

    current_intelligence = sorted(
        route

        for route
        in current_route_strings

        if route.startswith(
            "/api/v1/intelligence"
        )
    )

    check(
        "Locked Stage 9 route set exact",
        locked_intelligence
        ==
        expected_intelligence,
        failures,
    )

    check(
        "Current Stage 9 route set exact",
        current_intelligence
        ==
        expected_intelligence,
        failures,
    )

    print(
        "\n7. FRONTEND SAFETY RULES"
    )

    rules = contract.get(
        "frontend_rules",
        {}
    )

    for key in [
        "direct_backend_artifact_access",
        "direct_provider_access",
        "mutating_requests",
        "frontend_prediction_logic",
        "frontend_context_recalculation",
        "frontend_intelligence_recalculation",
        "stale_fallback",
        "unlisted_api_route_access",
    ]:

        check(
            f"{key} forbidden",
            rules.get(
                key
            )
            is False,
            failures,
        )

    print(
        "\n8. CONTRACT DEPENDENCY FRESHNESS"
    )

    verify_dependency_identity(
        contract,
        failures,
    )

    print(
        "\n9. ROUTE SOURCE FRESHNESS"
    )

    verify_source_identity(
        contract,
        failures,
    )

    print(
        "\n10. NO PREMATURE PROMOTION"
    )

    promotion = contract.get(
        "promotion",
        {}
    )

    check(
        "10.1.3 not pre-completed by contract builder",
        promotion.get(
            "stage10_1_3_complete"
        )
        is False,
        failures,
    )

    check(
        "Stage 10.1 not complete",
        promotion.get(
            "stage10_1_complete"
        )
        is False,
        failures,
    )

    check(
        "Stage 10 not complete",
        promotion.get(
            "stage10_complete"
        )
        is False,
        failures,
    )

    check(
        "Promotion not authorized",
        promotion.get(
            "promotion_authorized"
        )
        is False,
        failures,
    )

    print(
        "\n11. SAVE 10.1.3 VERIFICATION"
    )

    passed = (
        len(
            failures
        )
        ==
        0
    )

    if passed:

        evidence = {
            "stage":
                "10.1.3",

            "name":
                "FRONTEND_ALLOWED_BACKEND_API_ENDPOINT_VERIFICATION",

            "status":
                "PASS",

            "stage_10_1_3_complete":
                True,

            "endpoint_contract":
                "LOCKED_AND_VERIFIED",

            "source_of_truth":
                "FLASK_APP_URL_MAP",

            "route_count":
                len(
                    current
                ),

            "namespace_counts":
                namespace_counts,

            "route_set":
                current_route_strings,

            "authority":
                authority,

            "safety": {
                "get_only":
                    True,

                "write_methods_allowed":
                    False,

                "direct_artifact_access":
                    False,

                "direct_provider_access":
                    False,

                "frontend_prediction_logic":
                    False,

                "frontend_context_recalculation":
                    False,

                "frontend_intelligence_recalculation":
                    False,

                "stale_fallback":
                    False,

                "unlisted_routes_allowed":
                    False,
            },

            "dependency_identity": {
                relative(
                    CONTRACT_FILE
                ): {
                    "sha256":
                        sha256_file(
                            CONTRACT_FILE
                        )
                },

                relative(
                    RESPONSIBILITY_FILE
                ): {
                    "sha256":
                        sha256_file(
                            RESPONSIBILITY_FILE
                        )
                },

                relative(
                    PREVIOUS_VERIFICATION_FILE
                ): {
                    "sha256":
                        sha256_file(
                            PREVIOUS_VERIFICATION_FILE
                        )
                },
            },

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "stage10_ready_for_10_1_4":
                True,

            "stage10_1_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.1.4",

            "failures":
                [],
        }

        save_json_atomic(
            OUTPUT_FILE,
            evidence,
        )

        print(
            relative(
                OUTPUT_FILE
            )
        )

    print(
        "\n"
        + "=" * 72
    )

    if passed:

        print(
            "STAGE 10.1.3: PASS"
        )

        print(
            "ALLOWED BACKEND API ENDPOINTS: LOCKED AND VERIFIED"
        )

        print(
            "FLASK ROUTE MAP: SNAPSHOT VERIFIED"
        )

        print(
            "STAGE 10 READY FOR 10.1.4"
        )

        print()

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.1.3: FAIL"
        )

        print(
            "ALLOWED BACKEND API ENDPOINTS: NOT VERIFIED"
        )

        print()

        print(
            "Failures:"
        )

        for failure in failures:

            print(
                f"  - {failure}"
            )

    print(
        "=" * 72
    )

    sys.exit(
        0
        if passed
        else 1
    )


if __name__ == "__main__":

    main()
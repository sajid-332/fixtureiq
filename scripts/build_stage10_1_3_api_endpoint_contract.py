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


DOCS_DIR = (
    ROOT
    / "docs"
    / "stage10"
)

OUTPUT_FILE = (
    DOCS_DIR
    / "frontend_api_endpoint_contract.json"
)

RESPONSIBILITY_CONTRACT_FILE = (
    DOCS_DIR
    / "frontend_responsibility_contract.json"
)

PREVIOUS_VERIFICATION_FILE = (
    ROOT
    / "data"
    / "processed"
    / "frontend"
    / "stage10_1_1_10_1_2_verification.json"
)


ALLOWED_PREFIXES = (
    "/api/health",
    "/api/v1/production",
    "/api/v1/context",
    "/api/v1/intelligence",
)

WRITE_METHODS = {
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
}

FRAMEWORK_AUTOMATIC_METHODS = {
    "HEAD",
    "OPTIONS",
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


def is_allowed_route(
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


def authority_for_route(
    route: str,
) -> str:

    if route == "/api/health":

        return "SYSTEM_HEALTH"

    if route.startswith(
        "/api/v1/production"
    ):

        return "STAGE7_PREDICTION_AUTHORITY"

    if route.startswith(
        "/api/v1/context"
    ):

        return "STAGE8_CONTEXT_AUTHORITY"

    if route.startswith(
        "/api/v1/intelligence"
    ):

        return "STAGE9_INTELLIGENCE_AUTHORITY"

    raise RuntimeError(
        f"Unclassified route: {route}"
    )


def namespace_for_route(
    route: str,
) -> str:

    if route == "/api/health":

        return "health"

    if route.startswith(
        "/api/v1/production"
    ):

        return "production"

    if route.startswith(
        "/api/v1/context"
    ):

        return "context"

    if route.startswith(
        "/api/v1/intelligence"
    ):

        return "intelligence"

    raise RuntimeError(
        f"Unclassified route: {route}"
    )


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.1.3"
    )

    print(
        "BUILD FRONTEND API ENDPOINT CONTRACT"
    )

    print("=" * 72)

    if not RESPONSIBILITY_CONTRACT_FILE.exists():

        raise RuntimeError(
            "Stage 10.1.2 responsibility contract missing."
        )

    if not PREVIOUS_VERIFICATION_FILE.exists():

        raise RuntimeError(
            "Stage 10.1.1-10.1.2 verification evidence missing."
        )

    responsibility = load_json(
        RESPONSIBILITY_CONTRACT_FILE
    )

    previous = load_json(
        PREVIOUS_VERIFICATION_FILE
    )

    if (
        responsibility.get(
            "status"
        )
        !=
        "LOCKED"
    ):

        raise RuntimeError(
            "Stage 10.1.2 responsibility contract is not LOCKED."
        )

    if (
        previous.get(
            "status"
        )
        !=
        "PASS"
    ):

        raise RuntimeError(
            "Stage 10.1.1-10.1.2 verification is not PASS."
        )

    routes = []

    for rule in app.url_map.iter_rules():

        route = rule.rule

        if not is_allowed_route(
            route
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
            FRAMEWORK_AUTOMATIC_METHODS
        )

        write_methods = sorted(
            set(
                explicit_methods
            )
            &
            WRITE_METHODS
        )

        routes.append(
            {
                "route":
                    route,

                "endpoint":
                    rule.endpoint,

                "namespace":
                    namespace_for_route(
                        route
                    ),

                "authority":
                    authority_for_route(
                        route
                    ),

                "methods":
                    methods,

                "frontend_allowed_methods":
                    [
                        method

                        for method
                        in explicit_methods

                        if method
                        ==
                        "GET"
                    ],

                "write_methods":
                    write_methods,

                "read_only":
                    (
                        explicit_methods
                        ==
                        ["GET"]
                    ),

                "frontend_allowed":
                    (
                        "GET"
                        in explicit_methods
                        and
                        not write_methods
                    ),
            }
        )

    routes.sort(
        key=lambda item: (
            item[
                "namespace"
            ],
            item[
                "route"
            ],
        )
    )

    if not routes:

        raise RuntimeError(
            "No frontend-eligible API routes found."
        )

    unsafe = [
        item

        for item in routes

        if not item[
            "frontend_allowed"
        ]
    ]

    if unsafe:

        raise RuntimeError(
            (
                "One or more API routes are not "
                "read-only frontend-safe:\n"
                +
                "\n".join(
                    (
                        f"{item['route']} "
                        f"{item['methods']}"
                    )

                    for item
                    in unsafe
                )
            )
        )

    namespace_counts = {
        "health": 0,
        "production": 0,
        "context": 0,
        "intelligence": 0,
    }

    for item in routes:

        namespace_counts[
            item[
                "namespace"
            ]
        ] += 1

    route_strings = [
        item[
            "route"
        ]

        for item in routes
    ]

    intelligence_routes = [
        item[
            "route"
        ]

        for item in routes

        if item[
            "namespace"
        ]
        ==
        "intelligence"
    ]

    expected_intelligence_routes = sorted(
        [
            "/api/v1/intelligence/status",
            "/api/v1/intelligence/matches",
            "/api/v1/intelligence/matches/<fixture_id>",
            "/api/v1/intelligence/team/<path:team_name>",
            "/api/v1/intelligence/upcoming",
        ]
    )

    if (
        sorted(
            intelligence_routes
        )
        !=
        expected_intelligence_routes
    ):

        raise RuntimeError(
            (
                "Stage 9 intelligence API does not match "
                "the verified five-route contract."
            )
        )

    source_files = [
        ROOT
        / "backend"
        / "app.py",

        ROOT
        / "backend"
        / "routes"
        / "production_prediction_api.py",

        ROOT
        / "backend"
        / "routes"
        / "context_api.py",

        ROOT
        / "backend"
        / "routes"
        / "intelligence_api.py",
    ]

    source_identity = {}

    for path in source_files:

        if not path.exists():

            raise RuntimeError(
                f"Missing route source: {path}"
            )

        source_identity[
            relative(
                path
            )
        ] = {
            "sha256":
                sha256_file(
                    path
                )
        }

    contract = {
        "stage":
            "10.1.3",

        "version":
            "1.0.0",

        "name":
            "FRONTEND_ALLOWED_BACKEND_API_ENDPOINTS",

        "status":
            "LOCKED",

        "generated_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "source_of_truth":
            "FLASK_APP_URL_MAP",

        "frontend_transport":
            "HTTP_JSON",

        "allowed_http_methods":
            [
                "GET"
            ],

        "framework_automatic_methods":
            sorted(
                FRAMEWORK_AUTOMATIC_METHODS
            ),

        "allowed_namespaces":
            [
                "/api/health",
                "/api/v1/production",
                "/api/v1/context",
                "/api/v1/intelligence",
            ],

        "authority": {
            "health":
                "SYSTEM_HEALTH",

            "production":
                "STAGE7_PREDICTION_AUTHORITY",

            "context":
                "STAGE8_CONTEXT_AUTHORITY",

            "intelligence":
                "STAGE9_INTELLIGENCE_AUTHORITY",

            "frontend":
                "PRESENTATION_ONLY",
        },

        "primary_user_facing_source":
            "/api/v1/intelligence",

        "route_count":
            len(
                routes
            ),

        "namespace_counts":
            namespace_counts,

        "route_set":
            route_strings,

        "routes":
            routes,

        "verified_stage9_intelligence_routes":
            expected_intelligence_routes,

        "frontend_rules": {
            "direct_backend_artifact_access":
                False,

            "direct_provider_access":
                False,

            "mutating_requests":
                False,

            "frontend_prediction_logic":
                False,

            "frontend_context_recalculation":
                False,

            "frontend_intelligence_recalculation":
                False,

            "stale_fallback":
                False,

            "unlisted_api_route_access":
                False,
        },

        "source_identity":
            source_identity,

        "dependency_identity": {
            relative(
                RESPONSIBILITY_CONTRACT_FILE
            ): {
                "sha256":
                    sha256_file(
                        RESPONSIBILITY_CONTRACT_FILE
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

        "promotion": {
            "stage10_1_3_complete":
                False,

            "stage10_1_complete":
                False,

            "stage10_complete":
                False,

            "promotion_authorized":
                False,
        },
    }

    save_json_atomic(
        OUTPUT_FILE,
        contract,
    )

    print()

    print(
        f"Total frontend-allowed routes: "
        f"{len(routes)}"
    )

    print(
        f"Health routes: "
        f"{namespace_counts['health']}"
    )

    print(
        f"Production routes: "
        f"{namespace_counts['production']}"
    )

    print(
        f"Context routes: "
        f"{namespace_counts['context']}"
    )

    print(
        f"Intelligence routes: "
        f"{namespace_counts['intelligence']}"
    )

    print()

    for item in routes:

        print(
            f"{item['methods']} "
            f"{item['route']}"
        )

    print()

    print(
        f"Saved: "
        f"{relative(OUTPUT_FILE)}"
    )

    print()

    print("=" * 72)

    print(
        "STAGE 10.1.3 ENDPOINT CONTRACT: BUILT"
    )

    print(
        "CONTRACT STATUS: LOCKED"
    )

    print(
        "STAGE 10 IS NOT YET PROMOTED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
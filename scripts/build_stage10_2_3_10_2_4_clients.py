from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FRONTEND = ROOT / "frontend"
DOCS = ROOT / "docs" / "stage10"

FRONTEND_DATA = (
    ROOT
    / "data"
    / "processed"
    / "frontend"
)


ENDPOINT_CONTRACT_FILE = (
    DOCS
    / "frontend_api_endpoint_contract.json"
)

HTTP_CLIENT_CONTRACT_FILE = (
    DOCS
    / "frontend_http_client_contract.json"
)

ENVIRONMENT_CONTRACT_FILE = (
    DOCS
    / "frontend_api_environment_contract.json"
)

PREVIOUS_VERIFICATION_FILE = (
    FRONTEND_DATA
    / "stage10_2_1_10_2_2_verification.json"
)

SHARED_CLIENT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "client.ts"
)


INTELLIGENCE_CLIENT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "intelligence.ts"
)

PRODUCTION_CLIENT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "production.ts"
)


INTELLIGENCE_CONTRACT_FILE = (
    DOCS
    / "frontend_intelligence_api_client_contract.json"
)

PRODUCTION_CONTRACT_FILE = (
    DOCS
    / "frontend_production_api_client_contract.json"
)


EXPECTED_INTELLIGENCE_ROUTES = [
    "/api/v1/intelligence/status",
    "/api/v1/intelligence/matches",
    "/api/v1/intelligence/matches/<fixture_id>",
    "/api/v1/intelligence/team/<path:team_name>",
    "/api/v1/intelligence/upcoming",
]


PARAM_PATTERN = re.compile(
    r"<(?:[^:>]+:)?([A-Za-z_][A-Za-z0-9_]*)>"
)


def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise RuntimeError(
            f"Missing required artifact: {path}"
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

            digest.update(chunk)

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
        .replace("\\", "/")
    )


def save_text_atomic(
    path: Path,
    text: str,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        text,
        encoding="utf-8",
    )

    temporary.replace(path)


def save_json_atomic(
    path: Path,
    payload: dict,
) -> None:

    save_text_atomic(
        path,
        (
            json.dumps(
                payload,
                indent=2,
            )
            +
            "\n"
        ),
    )


def identity(
    path: Path,
) -> dict:

    return {
        "sha256":
            sha256_file(path)
    }


def pascal_case(
    value: str,
) -> str:

    words = re.findall(
        r"[A-Za-z0-9]+",
        value,
    )

    return "".join(
        word[:1].upper()
        +
        word[1:]

        for word in words
    )


def parameter_names(
    route: str,
) -> list[str]:

    return PARAM_PATTERN.findall(
        route
    )


def production_function_name(
    route: str,
) -> str:

    prefix = "/api/v1/production"

    suffix = route[
        len(prefix):
    ].strip("/")

    if not suffix:

        return "getProduction"

    parts = suffix.split("/")

    output = [
        "getProduction"
    ]

    for part in parts:

        match = PARAM_PATTERN.fullmatch(
            part
        )

        if match:

            output.append("By")

            output.append(
                pascal_case(
                    match.group(1)
                )
            )

        else:

            output.append(
                pascal_case(part)
            )

    return "".join(output)


def production_route_key(
    route: str,
) -> str:

    prefix = "/api/v1/production"

    suffix = route[
        len(prefix):
    ].strip("/")

    if not suffix:

        return "ROOT"

    parts = []

    for segment in suffix.split("/"):

        match = PARAM_PATTERN.fullmatch(
            segment
        )

        if match:

            parts.extend(
                [
                    "BY",
                    match.group(1).upper(),
                ]
            )

        else:

            parts.append(
                re.sub(
                    r"[^A-Za-z0-9]+",
                    "_",
                    segment,
                ).upper()
            )

    return "_".join(
        part
        for part in parts
        if part
    )


def camel_case(
    value: str,
) -> str:

    converted = pascal_case(value)

    if not converted:

        raise RuntimeError(
            f"Cannot convert parameter name: {value}"
        )

    return (
        converted[:1].lower()
        +
        converted[1:]
    )


def render_route_expression(
    route: str,
) -> str:

    parameters = parameter_names(
        route
    )

    if not parameters:

        return json.dumps(route)

    pieces = []
    cursor = 0

    for match in PARAM_PATTERN.finditer(
        route
    ):

        pieces.append(
            route[
                cursor:
                match.start()
            ]
        )

        variable = camel_case(
            match.group(1)
        )

        pieces.append(
            "${encodeURIComponent("
            f"String({variable})"
            ")}"
        )

        cursor = match.end()

    pieces.append(
        route[cursor:]
    )

    return (
        "`"
        +
        "".join(pieces)
        +
        "`"
    )


def build_intelligence_source() -> str:

    return '''import "server-only";

import {
  fixtureIqApiGet,
  type FixtureIqApiGetOptions,
  type FixtureIqApiJsonResponse,
} from "./client";


export const INTELLIGENCE_API_ROUTES = {
  STATUS:
    "/api/v1/intelligence/status",

  MATCHES:
    "/api/v1/intelligence/matches",

  MATCH:
    "/api/v1/intelligence/matches/<fixture_id>",

  TEAM:
    "/api/v1/intelligence/team/<path:team_name>",

  UPCOMING:
    "/api/v1/intelligence/upcoming",
} as const;


export type IntelligenceApiResponse =
  FixtureIqApiJsonResponse<unknown>;


export function getIntelligenceStatus(
  options: FixtureIqApiGetOptions = {}
): Promise<IntelligenceApiResponse> {
  return fixtureIqApiGet<unknown>(
    "/api/v1/intelligence/status",
    options
  );
}


export function getIntelligenceMatches(
  options: FixtureIqApiGetOptions = {}
): Promise<IntelligenceApiResponse> {
  return fixtureIqApiGet<unknown>(
    "/api/v1/intelligence/matches",
    options
  );
}


export function getIntelligenceMatch(
  fixtureId: string | number,
  options: FixtureIqApiGetOptions = {}
): Promise<IntelligenceApiResponse> {
  const encodedFixtureId =
    encodeURIComponent(
      String(fixtureId)
    );

  return fixtureIqApiGet<unknown>(
    `/api/v1/intelligence/matches/${encodedFixtureId}`,
    options
  );
}


export function getTeamIntelligence(
  teamName: string,
  options: FixtureIqApiGetOptions = {}
): Promise<IntelligenceApiResponse> {
  const encodedTeamName =
    encodeURIComponent(
      teamName
    );

  return fixtureIqApiGet<unknown>(
    `/api/v1/intelligence/team/${encodedTeamName}`,
    options
  );
}


export function getUpcomingIntelligence(
  options: FixtureIqApiGetOptions = {}
): Promise<IntelligenceApiResponse> {
  return fixtureIqApiGet<unknown>(
    "/api/v1/intelligence/upcoming",
    options
  );
}
'''


def build_production_source(
    production_routes: list[str],
) -> tuple[str, list[dict]]:

    route_entries = []

    seen_keys = set()
    seen_functions = set()

    for route in production_routes:

        key = production_route_key(
            route
        )

        function_name = (
            production_function_name(
                route
            )
        )

        if key in seen_keys:

            raise RuntimeError(
                f"Duplicate generated production route key: {key}"
            )

        if function_name in seen_functions:

            raise RuntimeError(
                (
                    "Duplicate generated production "
                    f"function name: {function_name}"
                )
            )

        seen_keys.add(key)
        seen_functions.add(
            function_name
        )

        route_entries.append(
            {
                "key":
                    key,

                "function":
                    function_name,

                "route":
                    route,

                "parameters":
                    parameter_names(
                        route
                    ),
            }
        )

    lines = [
        'import "server-only";',
        "",
        "import {",
        "  fixtureIqApiGet,",
        "  type FixtureIqApiGetOptions,",
        "  type FixtureIqApiJsonResponse,",
        '} from "./client";',
        "",
        "",
        "export const PRODUCTION_API_ROUTES = {",
    ]

    for entry in route_entries:

        lines.extend(
            [
                f"  {entry['key']}:",
                f"    {json.dumps(entry['route'])},",
                "",
            ]
        )

    lines.extend(
        [
            "} as const;",
            "",
            "",
            "export type ProductionApiResponse =",
            "  FixtureIqApiJsonResponse<unknown>;",
            "",
        ]
    )

    for entry in route_entries:

        params = [
            camel_case(parameter)
            for parameter
            in entry["parameters"]
        ]

        lines.append(
            (
                f"export function "
                f"{entry['function']}("
            )
        )

        for parameter in params:

            lines.append(
                (
                    f"  {parameter}: "
                    "string | number,"
                )
            )

        lines.append(
            (
                "  options: "
                "FixtureIqApiGetOptions = {}"
            )
        )

        lines.append(
            "): Promise<ProductionApiResponse> {"
        )

        lines.append(
            "  return fixtureIqApiGet<unknown>("
        )

        lines.append(
            (
                "    "
                +
                render_route_expression(
                    entry["route"]
                )
                +
                ","
            )
        )

        lines.append(
            "    options"
        )

        lines.append(
            "  );"
        )

        lines.append(
            "}"
        )

        lines.append(
            ""
        )

        lines.append(
            ""
        )

    return (
        "\n".join(lines).rstrip()
        +
        "\n",
        route_entries,
    )


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.2.3 + 10.2.4"
    )

    print(
        "INTELLIGENCE + PRODUCTION API CLIENT BUILD"
    )

    print("=" * 72)

    endpoint_contract = load_json(
        ENDPOINT_CONTRACT_FILE
    )

    http_contract = load_json(
        HTTP_CLIENT_CONTRACT_FILE
    )

    environment_contract = load_json(
        ENVIRONMENT_CONTRACT_FILE
    )

    previous = load_json(
        PREVIOUS_VERIFICATION_FILE
    )

    if (
        previous.get("status")
        !=
        "PASS"
    ):

        raise RuntimeError(
            "10.2.1-10.2.2 verification is not PASS."
        )

    if (
        previous.get(
            "stage10_ready_for_10_2_3"
        )
        is not True
    ):

        raise RuntimeError(
            "10.2.2 did not authorize 10.2.3."
        )

    if (
        endpoint_contract.get(
            "status"
        )
        !=
        "LOCKED"
    ):

        raise RuntimeError(
            "10.1.3 endpoint contract is not LOCKED."
        )

    if (
        http_contract.get(
            "status"
        )
        !=
        "LOCKED"
    ):

        raise RuntimeError(
            "10.2.1 HTTP client contract is not LOCKED."
        )

    if (
        environment_contract.get(
            "status"
        )
        !=
        "LOCKED"
    ):

        raise RuntimeError(
            "10.2.2 environment contract is not LOCKED."
        )

    locked_routes = sorted(
        endpoint_contract.get(
            "route_set",
            []
        )
    )

    intelligence_routes = sorted(
        route
        for route in locked_routes
        if route.startswith(
            "/api/v1/intelligence"
        )
    )

    production_routes = sorted(
        route
        for route in locked_routes
        if route.startswith(
            "/api/v1/production"
        )
    )

    if (
        intelligence_routes
        !=
        sorted(
            EXPECTED_INTELLIGENCE_ROUTES
        )
    ):

        raise RuntimeError(
            "Locked intelligence route set changed."
        )

    if not production_routes:

        raise RuntimeError(
            "No locked Stage 7 production routes found."
        )

    intelligence_source = (
        build_intelligence_source()
    )

    (
        production_source,
        production_functions,
    ) = build_production_source(
        production_routes
    )

    save_text_atomic(
        INTELLIGENCE_CLIENT_FILE,
        intelligence_source,
    )

    save_text_atomic(
        PRODUCTION_CLIENT_FILE,
        production_source,
    )

    intelligence_contract = {
        "stage":
            "10.2.3",

        "version":
            "1.0.0",

        "name":
            "FRONTEND_INTELLIGENCE_API_CLIENT",

        "status":
            "LOCKED",

        "source":
            relative(
                INTELLIGENCE_CLIENT_FILE
            ),

        "server_only":
            True,

        "shared_transport":
            relative(
                SHARED_CLIENT_FILE
            ),

        "authority":
            "STAGE9_INTELLIGENCE",

        "routes":
            intelligence_routes,

        "route_count":
            len(
                intelligence_routes
            ),

        "functions": {
            "getIntelligenceStatus":
                "/api/v1/intelligence/status",

            "getIntelligenceMatches":
                "/api/v1/intelligence/matches",

            "getIntelligenceMatch":
                "/api/v1/intelligence/matches/<fixture_id>",

            "getTeamIntelligence":
                "/api/v1/intelligence/team/<path:team_name>",

            "getUpcomingIntelligence":
                "/api/v1/intelligence/upcoming",
        },

        "implementation": {
            "shared_http_client_only":
                True,

            "direct_fetch":
                False,

            "get_only":
                True,

            "dynamic_segments_encoded":
                True,

            "runtime_schema_validation":
                False,

            "runtime_schema_validation_owner":
                "10.2.6",

            "semantic_error_mapping":
                False,

            "semantic_error_mapping_owner":
                "10.2.7",

            "stale_fallback":
                False,
        },

        "source_sha256":
            sha256_file(
                INTELLIGENCE_CLIENT_FILE
            ),

        "dependency_identity": {
            relative(
                ENDPOINT_CONTRACT_FILE
            ):
                identity(
                    ENDPOINT_CONTRACT_FILE
                ),

            relative(
                HTTP_CLIENT_CONTRACT_FILE
            ):
                identity(
                    HTTP_CLIENT_CONTRACT_FILE
                ),

            relative(
                ENVIRONMENT_CONTRACT_FILE
            ):
                identity(
                    ENVIRONMENT_CONTRACT_FILE
                ),

            relative(
                PREVIOUS_VERIFICATION_FILE
            ):
                identity(
                    PREVIOUS_VERIFICATION_FILE
                ),

            relative(
                SHARED_CLIENT_FILE
            ):
                identity(
                    SHARED_CLIENT_FILE
                ),
        },

        "promotion": {
            "stage10_2_3_complete":
                False,

            "stage10_2_complete":
                False,

            "stage10_complete":
                False,
        },

        "generated_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }

    production_contract = {
        "stage":
            "10.2.4",

        "version":
            "1.0.0",

        "name":
            "FRONTEND_PRODUCTION_API_CLIENT",

        "status":
            "LOCKED",

        "source":
            relative(
                PRODUCTION_CLIENT_FILE
            ),

        "server_only":
            True,

        "shared_transport":
            relative(
                SHARED_CLIENT_FILE
            ),

        "authority":
            "STAGE7_PREDICTION",

        "route_source":
            "STAGE10_1_3_LOCKED_ENDPOINT_CONTRACT",

        "routes":
            production_routes,

        "route_count":
            len(
                production_routes
            ),

        "generated_functions":
            production_functions,

        "implementation": {
            "routes_manually_guessed":
                False,

            "shared_http_client_only":
                True,

            "direct_fetch":
                False,

            "get_only":
                True,

            "dynamic_segments_encoded":
                True,

            "prediction_recalculation":
                False,

            "model_access":
                False,

            "runtime_schema_validation":
                False,

            "runtime_schema_validation_owner":
                "10.2.6",

            "semantic_error_mapping":
                False,

            "semantic_error_mapping_owner":
                "10.2.7",

            "stale_fallback":
                False,
        },

        "source_sha256":
            sha256_file(
                PRODUCTION_CLIENT_FILE
            ),

        "dependency_identity": {
            relative(
                ENDPOINT_CONTRACT_FILE
            ):
                identity(
                    ENDPOINT_CONTRACT_FILE
                ),

            relative(
                HTTP_CLIENT_CONTRACT_FILE
            ):
                identity(
                    HTTP_CLIENT_CONTRACT_FILE
                ),

            relative(
                ENVIRONMENT_CONTRACT_FILE
            ):
                identity(
                    ENVIRONMENT_CONTRACT_FILE
                ),

            relative(
                PREVIOUS_VERIFICATION_FILE
            ):
                identity(
                    PREVIOUS_VERIFICATION_FILE
                ),

            relative(
                SHARED_CLIENT_FILE
            ):
                identity(
                    SHARED_CLIENT_FILE
                ),
        },

        "promotion": {
            "stage10_2_4_complete":
                False,

            "stage10_2_complete":
                False,

            "stage10_complete":
                False,
        },

        "generated_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }

    save_json_atomic(
        INTELLIGENCE_CONTRACT_FILE,
        intelligence_contract,
    )

    save_json_atomic(
        PRODUCTION_CONTRACT_FILE,
        production_contract,
    )

    print()

    print(
        "Intelligence routes:"
    )

    for route in intelligence_routes:

        print(
            f"  GET {route}"
        )

    print()

    print(
        "Production routes discovered from 10.1.3:"
    )

    for entry in production_functions:

        print(
            (
                f"  {entry['function']} "
                f"-> {entry['route']}"
            )
        )

    print()

    print(
        f"Intelligence client: "
        f"{relative(INTELLIGENCE_CLIENT_FILE)}"
    )

    print(
        f"Production client: "
        f"{relative(PRODUCTION_CLIENT_FILE)}"
    )

    print()

    print("=" * 72)

    print(
        "STAGE 10.2.3 INTELLIGENCE API CLIENT: BUILT"
    )

    print(
        "STAGE 10.2.4 PRODUCTION API CLIENT: BUILT"
    )

    print(
        "STAGE 10 IS NOT YET PROMOTED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
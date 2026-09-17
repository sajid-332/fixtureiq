from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
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


# ============================================================
# Stage 10.1 foundation
# ============================================================

STAGE10_1_FINAL_FILE = (
    FRONTEND_DATA
    / "stage10_1_final_verification.json"
)

ENDPOINT_CONTRACT_FILE = (
    DOCS
    / "frontend_api_endpoint_contract.json"
)


# ============================================================
# Stage 10.2 verification evidence
# ============================================================

VERIFICATION_10_2_1_2 = (
    FRONTEND_DATA
    / "stage10_2_1_10_2_2_verification.json"
)

VERIFICATION_10_2_3_4 = (
    FRONTEND_DATA
    / "stage10_2_3_10_2_4_verification.json"
)

VERIFICATION_10_2_5_6 = (
    FRONTEND_DATA
    / "stage10_2_5_10_2_6_verification.json"
)

VERIFICATION_10_2_7 = (
    FRONTEND_DATA
    / "stage10_2_7_verification.json"
)


# ============================================================
# Stage 10.2 contracts
# ============================================================

HTTP_CLIENT_CONTRACT_FILE = (
    DOCS
    / "frontend_http_client_contract.json"
)

ENVIRONMENT_CONTRACT_FILE = (
    DOCS
    / "frontend_api_environment_contract.json"
)

INTELLIGENCE_CONTRACT_FILE = (
    DOCS
    / "frontend_intelligence_api_client_contract.json"
)

PRODUCTION_CONTRACT_FILE = (
    DOCS
    / "frontend_production_api_client_contract.json"
)

CONTEXT_CONTRACT_FILE = (
    DOCS
    / "frontend_context_api_client_contract.json"
)

VALIDATION_CONTRACT_FILE = (
    DOCS
    / "frontend_response_validation_contract.json"
)

ERROR_MAPPING_CONTRACT_FILE = (
    DOCS
    / "frontend_http_error_mapping_contract.json"
)


# ============================================================
# Frontend API source
# ============================================================

CONFIG_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "config.ts"
)

CLIENT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "client.ts"
)

INTELLIGENCE_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "intelligence.ts"
)

PRODUCTION_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "production.ts"
)

CONTEXT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "context.ts"
)

VALIDATION_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "validation.ts"
)

VALIDATED_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "validated.ts"
)

RESULT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "result.ts"
)

MAPPED_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "mapped.ts"
)

ENV_EXAMPLE_FILE = (
    FRONTEND
    / ".env.example"
)

PACKAGE_JSON_FILE = (
    FRONTEND
    / "package.json"
)

PACKAGE_LOCK_FILE = (
    FRONTEND
    / "package-lock.json"
)


# ============================================================
# Runtime tests
# ============================================================

VALIDATION_TEST_FILE = (
    FRONTEND
    / "scripts"
    / "verify-stage10-api-validation.mjs"
)

MAPPING_TEST_FILE = (
    FRONTEND
    / "scripts"
    / "verify-stage10-api-result-mapping.mjs"
)


# ============================================================
# Final Stage 10.2 artifact
# ============================================================

OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_2_final_verification.json"
)


EXPECTED_INTELLIGENCE_ROUTES = {
    "/api/v1/intelligence/status",
    "/api/v1/intelligence/matches",
    "/api/v1/intelligence/matches/<fixture_id>",
    "/api/v1/intelligence/team/<path:team_name>",
    "/api/v1/intelligence/upcoming",
}


EXPECTED_ERROR_MAPPING = {
    "HTTP_200":
        "READY",

    "HTTP_404":
        "NOT_FOUND",

    "HTTP_503":
        "NOT_READY",

    "NETWORK_FAILURE":
        "CONNECTION_ERROR",

    "INVALID_RESPONSE":
        "CONNECTION_ERROR",

    "UNEXPECTED_HTTP_STATUS":
        "CONNECTION_ERROR",
}


API_SOURCE_FILES = [
    CONFIG_FILE,
    CLIENT_FILE,
    INTELLIGENCE_FILE,
    PRODUCTION_FILE,
    CONTEXT_FILE,
    VALIDATION_FILE,
    VALIDATED_FILE,
    RESULT_FILE,
    MAPPED_FILE,
]


CONTRACT_FILES = [
    HTTP_CLIENT_CONTRACT_FILE,
    ENVIRONMENT_CONTRACT_FILE,
    INTELLIGENCE_CONTRACT_FILE,
    PRODUCTION_CONTRACT_FILE,
    CONTEXT_CONTRACT_FILE,
    VALIDATION_CONTRACT_FILE,
    ERROR_MAPPING_CONTRACT_FILE,
]


VERIFICATION_FILES = [
    VERIFICATION_10_2_1_2,
    VERIFICATION_10_2_3_4,
    VERIFICATION_10_2_5_6,
    VERIFICATION_10_2_7,
]


# ============================================================
# Helpers
# ============================================================

def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise RuntimeError(
            f"Missing JSON artifact: {path}"
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


def resolve_project_path(
    value: str,
) -> Path:

    raw = Path(value)

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


def identity(
    path: Path,
) -> dict:

    return {
        "sha256":
            sha256_file(path)
    }


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

        file.write("\n")

    temporary.replace(path)


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


def verify_dependencies(
    payload: dict,
    label: str,
    failures: list[str],
) -> None:

    identities = payload.get(
        "dependency_identity",
        {}
    )

    check(
        f"{label} dependency identity exists",
        isinstance(
            identities,
            dict,
        )
        and
        bool(identities),
        failures,
    )

    if not isinstance(
        identities,
        dict,
    ):

        return

    for (
        path_text,
        declared_identity,
    ) in identities.items():

        try:

            path = resolve_project_path(
                path_text
            )

            expected_sha = (
                declared_identity.get(
                    "sha256",
                    "",
                )
                if isinstance(
                    declared_identity,
                    dict,
                )
                else ""
            )

            current = (
                bool(expected_sha)
                and
                path.exists()
                and
                sha256_file(path)
                ==
                expected_sha
            )

        except Exception:

            current = False

        check(
            (
                f"{label}: "
                f"{Path(path_text).name} current"
            ),
            current,
            failures,
        )


def run_command(
    command: list[str],
    cwd: Path,
) -> tuple[
    bool,
    str,
]:

    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )

    output = (
        (result.stdout or "")
        +
        (result.stderr or "")
    ).strip()

    return (
        result.returncode == 0,
        output,
    )


def run_typescript_check() -> tuple[
    bool,
    str,
]:

    npm = (
        shutil.which("npm.cmd")
        or
        shutil.which("npm")
    )

    if npm is None:

        return (
            False,
            "npm executable not found.",
        )

    return run_command(
        [
            npm,
            "exec",
            "--",
            "tsc",
            "--noEmit",
        ],
        FRONTEND,
    )


def run_node_test(
    path: Path,
    success_marker: str,
) -> tuple[
    bool,
    str,
]:

    node = shutil.which(
        "node"
    )

    if node is None:

        return (
            False,
            "Node executable not found.",
        )

    ok, output = run_command(
        [
            node,
            str(path),
        ],
        FRONTEND,
    )

    return (
        ok
        and
        success_marker
        in
        output,
        output,
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.2.8"
    )

    print(
        "FINAL BACKEND API CLIENT LAYER VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    # --------------------------------------------------------
    # 1. Required artifacts
    # --------------------------------------------------------

    print(
        "\n1. REQUIRED ARTIFACTS"
    )


    required_files = [
        STAGE10_1_FINAL_FILE,
        ENDPOINT_CONTRACT_FILE,
        *VERIFICATION_FILES,
        *CONTRACT_FILES,
        *API_SOURCE_FILES,
        ENV_EXAMPLE_FILE,
        PACKAGE_JSON_FILE,
        PACKAGE_LOCK_FILE,
        VALIDATION_TEST_FILE,
        MAPPING_TEST_FILE,
    ]


    for path in required_files:

        check(
            relative(path),
            path.exists(),
            failures,
        )


    if failures:

        print(
            "\nCannot continue final verification "
            "with missing required artifacts."
        )

        print(
            "\n"
            +
            "=" * 72
        )

        print(
            "STAGE 10.2.8: FAIL"
        )

        print(
            "STAGE 10.2: INCOMPLETE"
        )

        print(
            "=" * 72
        )

        sys.exit(1)


    # --------------------------------------------------------
    # Load artifacts
    # --------------------------------------------------------

    stage10_1 = load_json(
        STAGE10_1_FINAL_FILE
    )

    endpoint_contract = load_json(
        ENDPOINT_CONTRACT_FILE
    )


    evidence_1_2 = load_json(
        VERIFICATION_10_2_1_2
    )

    evidence_3_4 = load_json(
        VERIFICATION_10_2_3_4
    )

    evidence_5_6 = load_json(
        VERIFICATION_10_2_5_6
    )

    evidence_7 = load_json(
        VERIFICATION_10_2_7
    )


    http_contract = load_json(
        HTTP_CLIENT_CONTRACT_FILE
    )

    environment_contract = load_json(
        ENVIRONMENT_CONTRACT_FILE
    )

    intelligence_contract = load_json(
        INTELLIGENCE_CONTRACT_FILE
    )

    production_contract = load_json(
        PRODUCTION_CONTRACT_FILE
    )

    context_contract = load_json(
        CONTEXT_CONTRACT_FILE
    )

    validation_contract = load_json(
        VALIDATION_CONTRACT_FILE
    )

    error_mapping_contract = load_json(
        ERROR_MAPPING_CONTRACT_FILE
    )


    sources = {
        relative(path):
            path.read_text(
                encoding="utf-8"
            )

        for path in API_SOURCE_FILES
    }


    # --------------------------------------------------------
    # 2. Stage 10.1 foundation
    # --------------------------------------------------------

    print(
        "\n2. STAGE 10.1 FOUNDATION"
    )


    check(
        "Stage 10.1 final verification PASS",
        stage10_1.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )


    check(
        "Stage 10.1 complete",
        stage10_1.get(
            "stage_10_1_complete"
        )
        is True,
        failures,
    )


    check(
        "Stage 10.1 authorized 10.2.1",
        stage10_1.get(
            "stage10_ready_for_10_2_1"
        )
        is True,
        failures,
    )


    check(
        "Endpoint contract still LOCKED",
        endpoint_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    # --------------------------------------------------------
    # 3. Substage verification evidence
    # --------------------------------------------------------

    print(
        "\n3. STAGE 10.2 SUBSTAGE EVIDENCE"
    )


    evidence_checks = [
        (
            "10.2.1",
            evidence_1_2,
            "stage_10_2_1_complete",
        ),
        (
            "10.2.2",
            evidence_1_2,
            "stage_10_2_2_complete",
        ),
        (
            "10.2.3",
            evidence_3_4,
            "stage_10_2_3_complete",
        ),
        (
            "10.2.4",
            evidence_3_4,
            "stage_10_2_4_complete",
        ),
        (
            "10.2.5",
            evidence_5_6,
            "stage_10_2_5_complete",
        ),
        (
            "10.2.6",
            evidence_5_6,
            "stage_10_2_6_complete",
        ),
        (
            "10.2.7",
            evidence_7,
            "stage_10_2_7_complete",
        ),
    ]


    for (
        stage,
        evidence,
        key,
    ) in evidence_checks:

        check(
            f"{stage} verification status PASS",
            evidence.get(
                "status"
            )
            ==
            "PASS",
            failures,
        )

        check(
            f"{stage} completion persisted",
            evidence.get(
                key
            )
            is True,
            failures,
        )


    check(
        "10.2.7 authorized 10.2.8",
        evidence_7.get(
            "stage10_ready_for_10_2_8"
        )
        is True,
        failures,
    )


    # --------------------------------------------------------
    # 4. Contract chain
    # --------------------------------------------------------

    print(
        "\n4. LOCKED CONTRACT CHAIN"
    )


    contract_expectations = [
        (
            "10.2.1",
            http_contract,
        ),
        (
            "10.2.2",
            environment_contract,
        ),
        (
            "10.2.3",
            intelligence_contract,
        ),
        (
            "10.2.4",
            production_contract,
        ),
        (
            "10.2.5",
            context_contract,
        ),
        (
            "10.2.6",
            validation_contract,
        ),
        (
            "10.2.7",
            error_mapping_contract,
        ),
    ]


    for (
        expected_stage,
        contract,
    ) in contract_expectations:

        check(
            (
                f"{expected_stage} "
                "contract stage exact"
            ),
            contract.get(
                "stage"
            )
            ==
            expected_stage,
            failures,
        )

        check(
            (
                f"{expected_stage} "
                "contract LOCKED"
            ),
            contract.get(
                "status"
            )
            ==
            "LOCKED",
            failures,
        )


    # --------------------------------------------------------
    # 5. Endpoint coverage
    # --------------------------------------------------------

    print(
        "\n5. BACKEND ENDPOINT COVERAGE"
    )


    locked_routes = set(
        endpoint_contract.get(
            "route_set",
            []
        )
    )


    locked_intelligence_routes = {
        route
        for route in locked_routes
        if route.startswith(
            "/api/v1/intelligence"
        )
    }


    locked_production_routes = {
        route
        for route in locked_routes
        if route.startswith(
            "/api/v1/production"
        )
    }


    locked_context_routes = {
        route
        for route in locked_routes
        if route.startswith(
            "/api/v1/context"
        )
    }


    check(
        "Exactly five intelligence routes",
        locked_intelligence_routes
        ==
        EXPECTED_INTELLIGENCE_ROUTES,
        failures,
    )


    check(
        "Exactly ten context routes",
        len(
            locked_context_routes
        )
        ==
        10,
        failures,
    )


    check(
        "Production route set non-empty",
        bool(
            locked_production_routes
        ),
        failures,
    )


    check(
        "Intelligence client coverage exact",
        set(
            intelligence_contract.get(
                "routes",
                []
            )
        )
        ==
        locked_intelligence_routes,
        failures,
    )


    check(
        "Production client coverage exact",
        set(
            production_contract.get(
                "routes",
                []
            )
        )
        ==
        locked_production_routes,
        failures,
    )


    check(
        "Context client coverage exact",
        set(
            context_contract.get(
                "routes",
                []
            )
        )
        ==
        locked_context_routes,
        failures,
    )


    domain_routes = (
        locked_intelligence_routes
        |
        locked_production_routes
        |
        locked_context_routes
    )


    check(
        "No duplicated route ownership",
        (
            len(
                locked_intelligence_routes
            )
            +
            len(
                locked_production_routes
            )
            +
            len(
                locked_context_routes
            )
        )
        ==
        len(
            domain_routes
        ),
        failures,
    )


    # --------------------------------------------------------
    # 6. Shared HTTP client
    # --------------------------------------------------------

    print(
        "\n6. SHARED HTTP TRANSPORT"
    )


    client_source = sources[
        relative(
            CLIENT_FILE
        )
    ]

    config_source = sources[
        relative(
            CONFIG_FILE
        )
    ]


    check(
        "Shared client protected by server-only",
        'import "server-only";'
        in
        client_source,
        failures,
    )


    check(
        "Config protected by server-only",
        'import "server-only";'
        in
        config_source,
        failures,
    )


    check(
        "Shared client uses native fetch",
        re.search(
            r"\bfetch\s*\(",
            client_source,
        )
        is not None,
        failures,
    )


    check(
        "Shared transport GET only",
        re.search(
            r'method\s*:\s*"GET"',
            client_source,
        )
        is not None,
        failures,
    )


    check(
        "Shared transport cache no-store",
        re.search(
            r'cache\s*:\s*"no-store"',
            client_source,
        )
        is not None,
        failures,
    )


    check(
        "Shared transport omits credentials",
        re.search(
            r'credentials\s*:\s*"omit"',
            client_source,
        )
        is not None,
        failures,
    )


    check(
        "Shared transport rejects redirects",
        re.search(
            r'redirect\s*:\s*"error"',
            client_source,
        )
        is not None,
        failures,
    )


    check(
        "API base env variable exact",
        "FIXTUREIQ_API_BASE_URL"
        in
        config_source,
        failures,
    )


    check(
        "Development fallback exact",
        "http://127.0.0.1:5000"
        in
        config_source,
        failures,
    )


    env_lines = {
        line.strip()
        for line
        in
        ENV_EXAMPLE_FILE.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    }


    check(
        "Environment example exact",
        (
            "FIXTUREIQ_API_BASE_URL="
            "http://127.0.0.1:5000"
        )
        in
        env_lines,
        failures,
    )


    # --------------------------------------------------------
    # 7. Server/client safety boundary
    # --------------------------------------------------------

    print(
        "\n7. FRONTEND API SAFETY BOUNDARY"
    )


    direct_fetch_files = [
        path
        for path in API_SOURCE_FILES
        if re.search(
            r"\bfetch\s*\(",
            sources[
                relative(path)
            ],
        )
    ]


    check(
        "Only shared client calls fetch",
        direct_fetch_files
        ==
        [
            CLIENT_FILE
        ],
        failures,
    )


    mutation_pattern = re.compile(
        (
            r'\bmethod\s*:\s*'
            r'["\']'
            r'(?:POST|PUT|PATCH|DELETE)'
            r'["\']'
        ),
        re.IGNORECASE,
    )


    mutating_sources = [
        path
        for path in API_SOURCE_FILES
        if mutation_pattern.search(
            sources[
                relative(path)
            ]
        )
    ]


    check(
        "No mutating HTTP methods",
        not mutating_sources,
        failures,
    )


    all_api_source = "\n".join(
        sources.values()
    )


    check(
        "No NEXT_PUBLIC API configuration",
        "NEXT_PUBLIC"
        not in
        all_api_source
        and
        "NEXT_PUBLIC"
        not in
        ENV_EXAMPLE_FILE.read_text(
            encoding="utf-8"
        ),
        failures,
    )


    check(
        "No localStorage prediction cache",
        "localStorage"
        not in
        all_api_source,
        failures,
    )


    check(
        "No sessionStorage prediction cache",
        "sessionStorage"
        not in
        all_api_source,
        failures,
    )


    forbidden_runtime_terms = [
        "football-data.org",
        "api-football",
        "api-sports",
        "data/processed",
        "data\\processed",
        "data/historical",
        "data\\historical",
        ".joblib",
    ]


    for term in forbidden_runtime_terms:

        check(
            f"Frontend API source excludes: {term}",
            term.lower()
            not in
            all_api_source.lower(),
            failures,
        )


    # --------------------------------------------------------
    # 8. Typed response validation
    # --------------------------------------------------------

    print(
        "\n8. TYPED RESPONSE VALIDATION"
    )


    validation_source = sources[
        relative(
            VALIDATION_FILE
        )
    ]

    validated_source = sources[
        relative(
            VALIDATED_FILE
        )
    ]


    for export_name in [
        "validateProductionApiPayload",
        "validateIntelligenceApiPayload",
        "validateContextApiPayload",
    ]:

        check(
            (
                "Validation export present: "
                f"{export_name}"
            ),
            (
                f"export function {export_name}"
                in
                validation_source
            ),
            failures,
        )


    for runtime_api in [
        "Array.isArray",
        "Object.entries",
        "Number.isFinite",
        "Number.isInteger",
        "new Set",
    ]:

        check(
            (
                "Runtime validation API present: "
                f"{runtime_api}"
            ),
            runtime_api
            in
            validation_source,
            failures,
        )


    check(
        "Validated surface is server-only",
        'import "server-only";'
        in
        validated_source,
        failures,
    )


    check(
        "Validated surface has no direct fetch",
        re.search(
            r"\bfetch\s*\(",
            validated_source,
        )
        is None,
        failures,
    )


    # --------------------------------------------------------
    # 9. HTTP / runtime state mapping
    # --------------------------------------------------------

    print(
        "\n9. HTTP / ERROR-STATE MAPPING"
    )


    check(
        "Final mapping contract exact",
        error_mapping_contract.get(
            "mapping"
        )
        ==
        EXPECTED_ERROR_MAPPING,
        failures,
    )


    result_source = sources[
        relative(
            RESULT_FILE
        )
    ]


    for state in [
        "READY",
        "NOT_FOUND",
        "NOT_READY",
        "CONNECTION_ERROR",
    ]:

        check(
            f"Runtime state present: {state}",
            f'"{state}"'
            in
            result_source,
            failures,
        )


    failure_policy = (
        error_mapping_contract.get(
            "failure_policy",
            {}
        )
    )


    check(
        "Stale fallback prohibited",
        failure_policy.get(
            "stale_fallback"
        )
        is False,
        failures,
    )


    check(
        "Previous READY payload not preserved",
        failure_policy.get(
            "previous_ready_payload_preserved"
        )
        is False,
        failures,
    )


    check(
        "Automatic retry not hidden in client layer",
        failure_policy.get(
            "automatic_retry"
        )
        is False,
        failures,
    )


    check(
        "Client layer fails closed",
        failure_policy.get(
            "fail_closed"
        )
        is True,
        failures,
    )


    # --------------------------------------------------------
    # 10. Mapped public API surface
    # --------------------------------------------------------

    print(
        "\n10. MAPPED API SURFACE"
    )


    mapped_source = sources[
        relative(
            MAPPED_FILE
        )
    ]


    intelligence_count = (
        len(
            intelligence_contract.get(
                "functions",
                {}
            )
        )
    )

    production_count = (
        len(
            production_contract.get(
                "generated_functions",
                []
            )
        )
    )

    context_count = (
        len(
            context_contract.get(
                "generated_functions",
                []
            )
        )
    )


    expected_mapped_count = (
        intelligence_count
        +
        production_count
        +
        context_count
    )


    check(
        "Intelligence mapped count = 5",
        intelligence_count
        ==
        5,
        failures,
    )


    check(
        "Context mapped count = 10",
        context_count
        ==
        10,
        failures,
    )


    check(
        "Mapped API wrapper count exact",
        error_mapping_contract.get(
            "mapped_function_count"
        )
        ==
        expected_mapped_count,
        failures,
    )


    mapped_functions = (
        error_mapping_contract.get(
            "mapped_functions",
            []
        )
    )


    check(
        "Mapped contract function list count exact",
        len(
            mapped_functions
        )
        ==
        expected_mapped_count,
        failures,
    )


    for item in mapped_functions:

        function_name = (
            item.get(
                "result_function"
            )
            if isinstance(
                item,
                dict,
            )
            else None
        )

        check(
            (
                "Mapped export exists: "
                f"{function_name}"
            ),
            isinstance(
                function_name,
                str,
            )
            and
            (
                f"export function "
                f"{function_name}"
            )
            in
            mapped_source,
            failures,
        )


    # --------------------------------------------------------
    # 11. Authority preservation
    # --------------------------------------------------------

    print(
        "\n11. STAGE AUTHORITY PRESERVATION"
    )


    responsibility = (
        error_mapping_contract.get(
            "responsibility",
            {}
        )
    )


    for key in [
        "stage7_prediction_authority",
        "stage8_context_authority",
        "stage9_intelligence_authority",
        "stage10_presentation_authority",
    ]:

        check(
            key,
            responsibility.get(
                key
            )
            is True,
            failures,
        )


    for key in [
        "prediction_logic_added",
        "probabilities_modified",
        "context_modified",
        "intelligence_modified",
        "provider_access",
        "artifact_access",
    ]:

        check(
            key,
            responsibility.get(
                key
            )
            is False,
            failures,
        )


    # --------------------------------------------------------
    # 12. Contract dependency freshness
    # --------------------------------------------------------

    print(
        "\n12. CONTRACT DEPENDENCY FRESHNESS"
    )


    for (
        stage,
        contract,
    ) in contract_expectations:

        verify_dependencies(
            contract,
            stage,
            failures,
        )


    # --------------------------------------------------------
    # 13. Runtime validator tests
    # --------------------------------------------------------

    print(
        "\n13. 10.2.6 RUNTIME VALIDATION TESTS"
    )


    validation_ok, validation_output = (
        run_node_test(
            VALIDATION_TEST_FILE,
            (
                "STAGE 10.2.6 "
                "RUNTIME VALIDATION TESTS: PASS"
            ),
        )
    )


    check(
        "Typed runtime validation test suite",
        validation_ok,
        failures,
    )


    if validation_output:

        print()

        print(
            validation_output
        )


    # --------------------------------------------------------
    # 14. Runtime state mapping tests
    # --------------------------------------------------------

    print(
        "\n14. 10.2.7 RUNTIME MAPPING TESTS"
    )


    mapping_ok, mapping_output = (
        run_node_test(
            MAPPING_TEST_FILE,
            (
                "STAGE 10.2.7 "
                "HTTP / ERROR-STATE MAPPING TESTS: PASS"
            ),
        )
    )


    check(
        "HTTP/error-state runtime test suite",
        mapping_ok,
        failures,
    )


    if mapping_output:

        print()

        print(
            mapping_output
        )


    # --------------------------------------------------------
    # 15. TypeScript compiler
    # --------------------------------------------------------

    print(
        "\n15. TYPESCRIPT COMPILER"
    )


    typescript_ok, typescript_output = (
        run_typescript_check()
    )


    check(
        "TypeScript --noEmit",
        typescript_ok,
        failures,
    )


    if (
        not typescript_ok
        and
        typescript_output
    ):

        print()

        print(
            typescript_output
        )


    # --------------------------------------------------------
    # 16. No premature overall Stage 10 promotion
    # --------------------------------------------------------

    print(
        "\n16. PROMOTION SAFETY"
    )


    for (
        stage,
        contract,
    ) in contract_expectations:

        promotion = contract.get(
            "promotion",
            {}
        )

        if isinstance(
            promotion,
            dict,
        ):

            check(
                (
                    f"{stage} contract does not "
                    "claim overall Stage 10 complete"
                ),
                promotion.get(
                    "stage10_complete"
                )
                is False,
                failures,
            )


    check(
        "Previous Stage 10.2 evidence not prematurely complete",
        evidence_7.get(
            "stage10_2_complete"
        )
        is False,
        failures,
    )


    check(
        "Previous evidence does not promote Stage 10",
        evidence_7.get(
            "stage10_complete"
        )
        is False,
        failures,
    )


    # --------------------------------------------------------
    # 17. Final Stage 10.2 promotion
    # --------------------------------------------------------

    print(
        "\n17. STAGE 10.2.8 FINAL DECISION"
    )


    passed = (
        len(failures)
        ==
        0
    )


    if passed:

        dependency_paths = [
            STAGE10_1_FINAL_FILE,
            ENDPOINT_CONTRACT_FILE,
            *VERIFICATION_FILES,
            *CONTRACT_FILES,
            *API_SOURCE_FILES,
            ENV_EXAMPLE_FILE,
            PACKAGE_JSON_FILE,
            PACKAGE_LOCK_FILE,
            VALIDATION_TEST_FILE,
            MAPPING_TEST_FILE,
        ]


        final_dependency_identity = {
            relative(path):
                identity(path)

            for path in dependency_paths
        }


        final_artifact = {
            "stage":
                "10.2.8",

            "stage_group":
                "10.2",

            "name":
                (
                    "BACKEND_API_CLIENT_LAYER_"
                    "FINAL_VERIFICATION"
                ),

            "status":
                "PASS",

            "stage_10_2_1_complete":
                True,

            "stage_10_2_2_complete":
                True,

            "stage_10_2_3_complete":
                True,

            "stage_10_2_4_complete":
                True,

            "stage_10_2_5_complete":
                True,

            "stage_10_2_6_complete":
                True,

            "stage_10_2_7_complete":
                True,

            "stage_10_2_8_complete":
                True,

            "stage_10_2_complete":
                True,

            "backend_api_client_layer":
                "VERIFIED",

            "transport": {
                "method":
                    "GET_ONLY",

                "cache":
                    "NO_STORE",

                "credentials":
                    "OMIT",

                "redirects":
                    "REJECT",

                "server_only":
                    True,
            },

            "api_clients": {
                "intelligence":
                    "VERIFIED",

                "production":
                    "VERIFIED",

                "context":
                    "VERIFIED",
            },

            "validation": {
                "runtime_validation":
                    "VERIFIED",

                "invalid_payloads_fail_closed":
                    True,

                "probability_values_modified":
                    False,
            },

            "state_mapping": {
                "200":
                    "READY",

                "404":
                    "NOT_FOUND",

                "503":
                    "NOT_READY",

                "network":
                    "CONNECTION_ERROR",

                "invalid_response":
                    "CONNECTION_ERROR",

                "unexpected_http":
                    "CONNECTION_ERROR",
            },

            "safety": {
                "direct_provider_access":
                    False,

                "direct_artifact_access":
                    False,

                "frontend_prediction_logic":
                    False,

                "prediction_probability_mutation":
                    False,

                "context_mutation":
                    False,

                "intelligence_mutation":
                    False,

                "stale_fallback":
                    False,

                "previous_ready_payload_reuse_on_failure":
                    False,

                "mutating_http_methods":
                    False,
            },

            "authority": {
                "stage7":
                    "PREDICTION",

                "stage8":
                    "CONTEXT",

                "stage9":
                    "INTELLIGENCE",

                "stage10":
                    "PRESENTATION",
            },

            "typescript_compiler":
                "PASS",

            "runtime_validation_tests":
                "PASS",

            "runtime_mapping_tests":
                "PASS",

            "dependency_identity":
                final_dependency_identity,

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "stage10_ready_for_10_3_1":
                True,

            "stage10_complete":
                False,

            "next_stage":
                "10.3.1",

            "failures":
                [],
        }


        save_json_atomic(
            OUTPUT_FILE,
            final_artifact,
        )


        print(
            "Final verification artifact:"
        )

        print(
            f"  {relative(OUTPUT_FILE)}"
        )


    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    print(
        "\n"
        +
        "=" * 72
    )


    if passed:

        print(
            "STAGE 10.2.8: PASS"
        )

        print(
            "BACKEND API CLIENT LAYER: VERIFIED"
        )

        print()

        print(
            "STAGE 10.2: COMPLETE"
        )

        print(
            "STAGE 10 READY FOR 10.3.1"
        )

        print()

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.2.8: FAIL"
        )

        print(
            "STAGE 10.2: INCOMPLETE"
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
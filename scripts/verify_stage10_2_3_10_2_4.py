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

SHARED_CLIENT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "client.ts"
)


INTELLIGENCE_CONTRACT_FILE = (
    DOCS
    / "frontend_intelligence_api_client_contract.json"
)

PRODUCTION_CONTRACT_FILE = (
    DOCS
    / "frontend_production_api_client_contract.json"
)

ENDPOINT_CONTRACT_FILE = (
    DOCS
    / "frontend_api_endpoint_contract.json"
)

HTTP_CLIENT_CONTRACT_FILE = (
    DOCS
    / "frontend_http_client_contract.json"
)

PREVIOUS_FILE = (
    FRONTEND_DATA
    / "stage10_2_1_10_2_2_verification.json"
)

OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_2_3_10_2_4_verification.json"
)


EXPECTED_INTELLIGENCE_ROUTES = {
    "/api/v1/intelligence/status",
    "/api/v1/intelligence/matches",
    "/api/v1/intelligence/matches/<fixture_id>",
    "/api/v1/intelligence/team/<path:team_name>",
    "/api/v1/intelligence/upcoming",
}


def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise RuntimeError(
            f"Missing artifact: {path}"
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

    with path.open("rb") as file:

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

    for path_text, identity in (
        identities.items()
    ):

        try:

            path = resolve_project_path(
                path_text
            )

            expected_sha = str(
                identity.get(
                    "sha256",
                    "",
                )
            )

            current = (
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

    result = subprocess.run(
        [
            npm,
            "exec",
            "--",
            "tsc",
            "--noEmit",
        ],
        cwd=FRONTEND,
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


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.2.3 + 10.2.4"
    )

    print(
        "INTELLIGENCE + PRODUCTION API CLIENT VERIFICATION"
    )

    print("=" * 72)

    failures: list[str] = []

    required_files = [
        INTELLIGENCE_FILE,
        PRODUCTION_FILE,
        SHARED_CLIENT_FILE,
        INTELLIGENCE_CONTRACT_FILE,
        PRODUCTION_CONTRACT_FILE,
        ENDPOINT_CONTRACT_FILE,
        HTTP_CLIENT_CONTRACT_FILE,
        PREVIOUS_FILE,
    ]

    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    for path in required_files:

        check(
            relative(path),
            path.exists(),
            failures,
        )

    if failures:

        sys.exit(1)

    intelligence_contract = load_json(
        INTELLIGENCE_CONTRACT_FILE
    )

    production_contract = load_json(
        PRODUCTION_CONTRACT_FILE
    )

    endpoint_contract = load_json(
        ENDPOINT_CONTRACT_FILE
    )

    http_contract = load_json(
        HTTP_CLIENT_CONTRACT_FILE
    )

    previous = load_json(
        PREVIOUS_FILE
    )

    intelligence_source = (
        INTELLIGENCE_FILE.read_text(
            encoding="utf-8"
        )
    )

    production_source = (
        PRODUCTION_FILE.read_text(
            encoding="utf-8"
        )
    )

    print(
        "\n2. 10.2.1 / 10.2.2 FOUNDATION"
    )

    check(
        "Previous verification PASS",
        previous.get("status")
        ==
        "PASS",
        failures,
    )

    check(
        "10.2.1 complete",
        previous.get(
            "stage_10_2_1_complete"
        )
        is True,
        failures,
    )

    check(
        "10.2.2 complete",
        previous.get(
            "stage_10_2_2_complete"
        )
        is True,
        failures,
    )

    check(
        "10.2.2 authorized 10.2.3",
        previous.get(
            "stage10_ready_for_10_2_3"
        )
        is True,
        failures,
    )

    check(
        "Shared client contract remains LOCKED",
        http_contract.get("status")
        ==
        "LOCKED",
        failures,
    )

    check(
        "Endpoint contract remains LOCKED",
        endpoint_contract.get("status")
        ==
        "LOCKED",
        failures,
    )

    print(
        "\n3. STAGE 10.2.3 INTELLIGENCE CLIENT"
    )

    check(
        "Intelligence contract stage exact",
        intelligence_contract.get(
            "stage"
        )
        ==
        "10.2.3",
        failures,
    )

    check(
        "Intelligence contract LOCKED",
        intelligence_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )

    check(
        "Stage 9 remains intelligence authority",
        intelligence_contract.get(
            "authority"
        )
        ==
        "STAGE9_INTELLIGENCE",
        failures,
    )

    locked_routes = set(
        endpoint_contract.get(
            "route_set",
            []
        )
    )

    current_intelligence_routes = {
        route
        for route in locked_routes
        if route.startswith(
            "/api/v1/intelligence"
        )
    }

    check(
        "Stage 9 route set still exact",
        current_intelligence_routes
        ==
        EXPECTED_INTELLIGENCE_ROUTES,
        failures,
    )

    check(
        "Intelligence contract route set exact",
        set(
            intelligence_contract.get(
                "routes",
                []
            )
        )
        ==
        EXPECTED_INTELLIGENCE_ROUTES,
        failures,
    )

    check(
        "Exactly five intelligence routes",
        intelligence_contract.get(
            "route_count"
        )
        ==
        5,
        failures,
    )

    expected_functions = {
        "getIntelligenceStatus",
        "getIntelligenceMatches",
        "getIntelligenceMatch",
        "getTeamIntelligence",
        "getUpcomingIntelligence",
    }

    actual_functions = set(
        intelligence_contract.get(
            "functions",
            {}
        )
    )

    check(
        "Intelligence function set exact",
        actual_functions
        ==
        expected_functions,
        failures,
    )

    for function_name in sorted(
        expected_functions
    ):

        check(
            f"Export exists: {function_name}",
            re.search(
                (
                    r"export\s+function\s+"
                    +
                    re.escape(
                        function_name
                    )
                    +
                    r"\s*\("
                ),
                intelligence_source,
            )
            is not None,
            failures,
        )

    check(
        "Intelligence client is server-only",
        'import "server-only";'
        in
        intelligence_source,
        failures,
    )

    check(
        "Intelligence dynamic path encoding used",
        "encodeURIComponent"
        in
        intelligence_source,
        failures,
    )

    print(
        "\n4. STAGE 10.2.4 PRODUCTION CLIENT"
    )

    check(
        "Production contract stage exact",
        production_contract.get(
            "stage"
        )
        ==
        "10.2.4",
        failures,
    )

    check(
        "Production contract LOCKED",
        production_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )

    check(
        "Stage 7 remains prediction authority",
        production_contract.get(
            "authority"
        )
        ==
        "STAGE7_PREDICTION",
        failures,
    )

    locked_production_routes = {
        route
        for route in locked_routes
        if route.startswith(
            "/api/v1/production"
        )
    }

    contract_production_routes = set(
        production_contract.get(
            "routes",
            []
        )
    )

    check(
        "At least one locked production route exists",
        bool(
            locked_production_routes
        ),
        failures,
    )

    check(
        "Production route set exactly matches 10.1.3",
        contract_production_routes
        ==
        locked_production_routes,
        failures,
    )

    check(
        "Production route count exact",
        production_contract.get(
            "route_count"
        )
        ==
        len(
            locked_production_routes
        ),
        failures,
    )

    generated_functions = (
        production_contract.get(
            "generated_functions",
            []
        )
    )

    check(
        "One generated wrapper per production route",
        len(
            generated_functions
        )
        ==
        len(
            locked_production_routes
        ),
        failures,
    )

    generated_route_set = {
        item.get("route")
        for item in generated_functions
        if isinstance(
            item,
            dict,
        )
    }

    check(
        "Generated wrapper route set exact",
        generated_route_set
        ==
        locked_production_routes,
        failures,
    )

    for item in generated_functions:

        function_name = item.get(
            "function"
        )

        route = item.get(
            "route"
        )

        check(
            f"Production wrapper exists: {function_name}",
            isinstance(
                function_name,
                str,
            )
            and
            re.search(
                (
                    r"export\s+function\s+"
                    +
                    re.escape(
                        function_name
                    )
                    +
                    r"\s*\("
                ),
                production_source,
            )
            is not None,
            failures,
        )

        check(
            f"Production route locked: {route}",
            route
            in
            locked_production_routes,
            failures,
        )

    check(
        "Production client is server-only",
        'import "server-only";'
        in
        production_source,
        failures,
    )

    print(
        "\n5. SHARED TRANSPORT BOUNDARY"
    )

    for label, source in [
        (
            "Intelligence",
            intelligence_source,
        ),
        (
            "Production",
            production_source,
        ),
    ]:

        check(
            f"{label} uses fixtureIqApiGet",
            "fixtureIqApiGet"
            in
            source,
            failures,
        )

        check(
            f"{label} does not call fetch directly",
            re.search(
                r"\bfetch\s*\(",
                source,
            )
            is None,
            failures,
        )

        check(
            f"{label} does not use axios",
            "axios"
            not in
            source.lower(),
            failures,
        )

        check(
            f"{label} has no POST",
            re.search(
                r'\bPOST\b',
                source,
                re.IGNORECASE,
            )
            is None,
            failures,
        )

        check(
            f"{label} has no stale storage",
            (
                "localStorage"
                not in source
                and
                "sessionStorage"
                not in source
            ),
            failures,
        )

    print(
        "\n6. RESPONSIBILITY BOUNDARY"
    )

    intelligence_impl = (
        intelligence_contract.get(
            "implementation",
            {}
        )
    )

    production_impl = (
        production_contract.get(
            "implementation",
            {}
        )
    )

    check(
        "Intelligence runtime validation deferred to 10.2.6",
        (
            intelligence_impl.get(
                "runtime_schema_validation"
            )
            is False
            and
            intelligence_impl.get(
                "runtime_schema_validation_owner"
            )
            ==
            "10.2.6"
        ),
        failures,
    )

    check(
        "Production runtime validation deferred to 10.2.6",
        (
            production_impl.get(
                "runtime_schema_validation"
            )
            is False
            and
            production_impl.get(
                "runtime_schema_validation_owner"
            )
            ==
            "10.2.6"
        ),
        failures,
    )

    check(
        "Intelligence error mapping deferred to 10.2.7",
        (
            intelligence_impl.get(
                "semantic_error_mapping"
            )
            is False
            and
            intelligence_impl.get(
                "semantic_error_mapping_owner"
            )
            ==
            "10.2.7"
        ),
        failures,
    )

    check(
        "Production error mapping deferred to 10.2.7",
        (
            production_impl.get(
                "semantic_error_mapping"
            )
            is False
            and
            production_impl.get(
                "semantic_error_mapping_owner"
            )
            ==
            "10.2.7"
        ),
        failures,
    )

    check(
        "Production routes were not guessed manually",
        production_impl.get(
            "routes_manually_guessed"
        )
        is False,
        failures,
    )

    check(
        "Production prediction recalculation forbidden",
        production_impl.get(
            "prediction_recalculation"
        )
        is False,
        failures,
    )

    check(
        "Production model access forbidden",
        production_impl.get(
            "model_access"
        )
        is False,
        failures,
    )

    print(
        "\n7. SOURCE IDENTITY"
    )

    check(
        "intelligence.ts SHA current",
        intelligence_contract.get(
            "source_sha256"
        )
        ==
        sha256_file(
            INTELLIGENCE_FILE
        ),
        failures,
    )

    check(
        "production.ts SHA current",
        production_contract.get(
            "source_sha256"
        )
        ==
        sha256_file(
            PRODUCTION_FILE
        ),
        failures,
    )

    print(
        "\n8. DEPENDENCY FRESHNESS"
    )

    verify_dependencies(
        intelligence_contract,
        "10.2.3",
        failures,
    )

    verify_dependencies(
        production_contract,
        "10.2.4",
        failures,
    )

    print(
        "\n9. TYPESCRIPT COMPILER"
    )

    compiler_ok, compiler_output = (
        run_typescript_check()
    )

    check(
        "TypeScript --noEmit",
        compiler_ok,
        failures,
    )

    if (
        not compiler_ok
        and
        compiler_output
    ):

        print()

        print(
            compiler_output
        )

    print(
        "\n10. NO PREMATURE PROMOTION"
    )

    intelligence_promotion = (
        intelligence_contract.get(
            "promotion",
            {}
        )
    )

    production_promotion = (
        production_contract.get(
            "promotion",
            {}
        )
    )

    check(
        "10.2.3 contract did not self-promote",
        intelligence_promotion.get(
            "stage10_2_3_complete"
        )
        is False,
        failures,
    )

    check(
        "10.2.4 contract did not self-promote",
        production_promotion.get(
            "stage10_2_4_complete"
        )
        is False,
        failures,
    )

    check(
        "Stage 10.2 remains incomplete",
        (
            intelligence_promotion.get(
                "stage10_2_complete"
            )
            is False
            and
            production_promotion.get(
                "stage10_2_complete"
            )
            is False
        ),
        failures,
    )

    check(
        "Stage 10 remains incomplete",
        (
            intelligence_promotion.get(
                "stage10_complete"
            )
            is False
            and
            production_promotion.get(
                "stage10_complete"
            )
            is False
        ),
        failures,
    )

    print(
        "\n11. SAVE VERIFICATION EVIDENCE"
    )

    passed = (
        len(failures)
        ==
        0
    )

    if passed:

        evidence = {
            "stage":
                "10.2.3-10.2.4",

            "name":
                (
                    "INTELLIGENCE_AND_PRODUCTION_"
                    "API_CLIENT_VERIFICATION"
                ),

            "status":
                "PASS",

            "stage_10_2_3_complete":
                True,

            "stage_10_2_4_complete":
                True,

            "intelligence_api_client":
                "LOCKED_AND_VERIFIED",

            "production_api_client":
                "LOCKED_AND_VERIFIED",

            "intelligence_route_count":
                len(
                    EXPECTED_INTELLIGENCE_ROUTES
                ),

            "production_route_count":
                len(
                    locked_production_routes
                ),

            "transport":
                "SHARED_FIXTUREIQ_HTTP_CLIENT",

            "safety": {
                "get_only":
                    True,

                "direct_fetch":
                    False,

                "direct_provider_access":
                    False,

                "model_access":
                    False,

                "prediction_recalculation":
                    False,

                "runtime_validation":
                    False,

                "semantic_error_mapping":
                    False,

                "stale_fallback":
                    False,
            },

            "dependency_identity": {
                relative(
                    INTELLIGENCE_FILE
                ): {
                    "sha256":
                        sha256_file(
                            INTELLIGENCE_FILE
                        )
                },

                relative(
                    PRODUCTION_FILE
                ): {
                    "sha256":
                        sha256_file(
                            PRODUCTION_FILE
                        )
                },

                relative(
                    INTELLIGENCE_CONTRACT_FILE
                ): {
                    "sha256":
                        sha256_file(
                            INTELLIGENCE_CONTRACT_FILE
                        )
                },

                relative(
                    PRODUCTION_CONTRACT_FILE
                ): {
                    "sha256":
                        sha256_file(
                            PRODUCTION_CONTRACT_FILE
                        )
                },

                relative(
                    ENDPOINT_CONTRACT_FILE
                ): {
                    "sha256":
                        sha256_file(
                            ENDPOINT_CONTRACT_FILE
                        )
                },

                relative(
                    PREVIOUS_FILE
                ): {
                    "sha256":
                        sha256_file(
                            PREVIOUS_FILE
                        )
                },
            },

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "stage10_ready_for_10_2_5":
                True,

            "stage10_2_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.2.5",

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
            "STAGE 10.2.3: PASS"
        )

        print(
            "INTELLIGENCE API CLIENT: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.2.4: PASS"
        )

        print(
            "PRODUCTION API CLIENT: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.2.5"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.2.3 / 10.2.4: FAIL"
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
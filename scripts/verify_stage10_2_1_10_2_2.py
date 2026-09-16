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

DOCS = (
    ROOT
    / "docs"
    / "stage10"
)

FRONTEND_DATA = (
    ROOT
    / "data"
    / "processed"
    / "frontend"
)


CLIENT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "client.ts"
)

CONFIG_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "config.ts"
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

HTTP_CLIENT_CONTRACT_FILE = (
    DOCS
    / "frontend_http_client_contract.json"
)

ENVIRONMENT_CONTRACT_FILE = (
    DOCS
    / "frontend_api_environment_contract.json"
)

ENDPOINT_CONTRACT_FILE = (
    DOCS
    / "frontend_api_endpoint_contract.json"
)

STAGE_10_1_FINAL_FILE = (
    FRONTEND_DATA
    / "stage10_1_final_verification.json"
)

OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_2_1_10_2_2_verification.json"
)


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
            path.resolve().relative_to(
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
    prefix: str,
    failures: list[str],
) -> None:

    identities = payload.get(
        "dependency_identity",
        {}
    )

    check(
        f"{prefix} dependency identity exists",
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

            expected = str(
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
                expected
            )

        except Exception:

            current = False

        check(
            (
                f"{prefix}: "
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
        "FixtureIQ Stage 10.2.1 + 10.2.2"
    )

    print(
        "HTTP CLIENT + API ENVIRONMENT VERIFICATION"
    )

    print("=" * 72)

    failures: list[str] = []

    required = [
        CLIENT_FILE,
        CONFIG_FILE,
        ENV_EXAMPLE_FILE,
        PACKAGE_JSON_FILE,
        PACKAGE_LOCK_FILE,
        HTTP_CLIENT_CONTRACT_FILE,
        ENVIRONMENT_CONTRACT_FILE,
        ENDPOINT_CONTRACT_FILE,
        STAGE_10_1_FINAL_FILE,
    ]

    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    for path in required:

        check(
            relative(path),
            path.exists(),
            failures,
        )

    if failures:

        sys.exit(1)

    client_contract = load_json(
        HTTP_CLIENT_CONTRACT_FILE
    )

    environment_contract = load_json(
        ENVIRONMENT_CONTRACT_FILE
    )

    endpoint_contract = load_json(
        ENDPOINT_CONTRACT_FILE
    )

    previous = load_json(
        STAGE_10_1_FINAL_FILE
    )

    package_json = load_json(
        PACKAGE_JSON_FILE
    )

    client_source = CLIENT_FILE.read_text(
        encoding="utf-8"
    )

    config_source = CONFIG_FILE.read_text(
        encoding="utf-8"
    )

    env_example = ENV_EXAMPLE_FILE.read_text(
        encoding="utf-8"
    )

    print(
        "\n2. STAGE 10.1 FOUNDATION"
    )

    check(
        "Stage 10.1 final PASS",
        previous.get("status")
        ==
        "PASS",
        failures,
    )

    check(
        "Stage 10.1 complete",
        previous.get(
            "stage_10_1_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 10.1 authorized 10.2.1",
        previous.get(
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

    print(
        "\n3. SERVER-ONLY DEPENDENCY"
    )

    dependencies = {
        **package_json.get(
            "dependencies",
            {}
        ),

        **package_json.get(
            "devDependencies",
            {}
        ),
    }

    check(
        "server-only installed directly",
        "server-only"
        in
        dependencies,
        failures,
    )

    check(
        "config.ts protected by server-only",
        'import "server-only";'
        in
        config_source,
        failures,
    )

    check(
        "client.ts protected by server-only",
        'import "server-only";'
        in
        client_source,
        failures,
    )

    print(
        "\n4. STAGE 10.2.2 ENVIRONMENT CONFIG"
    )

    check(
        "Environment contract stage exact",
        environment_contract.get(
            "stage"
        )
        ==
        "10.2.2",
        failures,
    )

    check(
        "Environment contract LOCKED",
        environment_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )

    check(
        "Environment variable exact",
        environment_contract.get(
            "environment_variable"
        )
        ==
        "FIXTUREIQ_API_BASE_URL",
        failures,
    )

    check(
        "No NEXT_PUBLIC environment variable",
        "NEXT_PUBLIC_"
        not in
        config_source,
        failures,
    )

    check(
        "Environment example configured",
        re.search(
            (
                r"(?m)^"
                r"FIXTUREIQ_API_BASE_URL="
                r"http://127\.0\.0\.1:5000"
                r"\s*$"
            ),
            env_example,
        )
        is not None,
        failures,
    )

    check(
        "Production requires explicit base URL",
        environment_contract.get(
            "production",
            {},
        ).get(
            "explicit_environment_value_required"
        )
        is True,
        failures,
    )

    check(
        "Production fallback disabled",
        environment_contract.get(
            "production",
            {},
        ).get(
            "fallback_allowed"
        )
        is False,
        failures,
    )

    check(
        "Development fallback exact",
        environment_contract.get(
            "development",
            {},
        ).get(
            "fallback"
        )
        ==
        "http://127.0.0.1:5000",
        failures,
    )

    base_policy = (
        environment_contract.get(
            "base_url_policy",
            {}
        )
    )

    check(
        "URL API used for normalization",
        base_policy.get(
            "normalization_uses"
        )
        ==
        "URL_API",
        failures,
    )

    check(
        "Base URL origin-only",
        base_policy.get(
            "origin_only"
        )
        is True,
        failures,
    )

    check(
        "Base URL credentials forbidden",
        base_policy.get(
            "credentials_allowed"
        )
        is False,
        failures,
    )

    check(
        "Base URL path forbidden",
        base_policy.get(
            "path_allowed"
        )
        is False,
        failures,
    )

    check(
        "Base URL query forbidden",
        base_policy.get(
            "query_allowed"
        )
        is False,
        failures,
    )

    check(
        "Base URL fragment forbidden",
        base_policy.get(
            "fragment_allowed"
        )
        is False,
        failures,
    )

    check(
        "Config uses native URL",
        "new URL("
        in
        config_source,
        failures,
    )

    print(
        "\n5. STAGE 10.2.1 SHARED HTTP CLIENT"
    )

    check(
        "HTTP client contract stage exact",
        client_contract.get(
            "stage"
        )
        ==
        "10.2.1",
        failures,
    )

    check(
        "HTTP client contract LOCKED",
        client_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )

    check(
        "Native fetch transport",
        client_contract.get(
            "transport"
        )
        ==
        "WEB_FETCH_API",
        failures,
    )

    check(
        "GET-only client contract",
        client_contract.get(
            "allowed_methods"
        )
        ==
        ["GET"],
        failures,
    )

    request_policy = (
        client_contract.get(
            "request_policy",
            {}
        )
    )

    check(
        "Fetch cache = no-store",
        request_policy.get(
            "cache"
        )
        ==
        "no-store",
        failures,
    )

    check(
        "Credentials omitted",
        request_policy.get(
            "credentials"
        )
        ==
        "omit",
        failures,
    )

    check(
        "Redirects rejected",
        request_policy.get(
            "redirect"
        )
        ==
        "error",
        failures,
    )

    check(
        "No automatic retry",
        request_policy.get(
            "automatic_retry"
        )
        is False,
        failures,
    )

    check(
        "No stale fallback",
        request_policy.get(
            "stale_fallback"
        )
        is False,
        failures,
    )

    check(
        "Shared client calls native fetch",
        re.search(
            r"\bfetch\s*\(",
            client_source,
        )
        is not None,
        failures,
    )

    check(
        "Shared client uses method GET",
        re.search(
            r'method\s*:\s*"GET"',
            client_source,
        )
        is not None,
        failures,
    )

    check(
        "Shared client uses no-store",
        re.search(
            r'cache\s*:\s*"no-store"',
            client_source,
        )
        is not None,
        failures,
    )

    check(
        "Shared client omits credentials",
        re.search(
            r'credentials\s*:\s*"omit"',
            client_source,
        )
        is not None,
        failures,
    )

    check(
        "Shared client rejects redirects",
        re.search(
            r'redirect\s*:\s*"error"',
            client_source,
        )
        is not None,
        failures,
    )

    print(
        "\n6. URL / NAMESPACE SAFETY"
    )

    url_policy = client_contract.get(
        "url_policy",
        {}
    )

    check(
        "Relative API paths only",
        url_policy.get(
            "relative_api_paths_only"
        )
        is True,
        failures,
    )

    check(
        "Cross-origin override forbidden",
        url_policy.get(
            "cross_origin_override"
        )
        is False,
        failures,
    )

    check(
        "Protocol-relative override forbidden",
        url_policy.get(
            "protocol_relative_override"
        )
        is False,
        failures,
    )

    check(
        "Unlisted namespaces forbidden",
        url_policy.get(
            "unlisted_namespace_access"
        )
        is False,
        failures,
    )

    for namespace in [
        "/api/health",
        "/api/v1/production",
        "/api/v1/context",
        "/api/v1/intelligence",
    ]:

        check(
            f"Client namespace present: {namespace}",
            namespace
            in
            client_source,
            failures,
        )

    check(
        "Client checks origin equality",
        ".origin"
        in
        client_source
        and
        "url.origin"
        in
        client_source
        and
        "base.origin"
        in
        client_source,
        failures,
    )

    print(
        "\n7. RESPONSIBILITY BOUNDARY"
    )

    response_policy = (
        client_contract.get(
            "response_policy",
            {}
        )
    )

    check(
        "HTTP semantic mapping deferred",
        (
            response_policy.get(
                "semantic_status_mapping_here"
            )
            is False
            and
            response_policy.get(
                "semantic_status_mapping_owner"
            )
            ==
            "10.2.7"
        ),
        failures,
    )

    check(
        "Runtime schema validation deferred",
        (
            response_policy.get(
                "runtime_schema_validation_here"
            )
            is False
            and
            response_policy.get(
                "runtime_schema_validation_owner"
            )
            ==
            "10.2.6"
        ),
        failures,
    )

    check(
        "No localStorage use",
        "localStorage"
        not in
        client_source,
        failures,
    )

    check(
        "No sessionStorage use",
        "sessionStorage"
        not in
        client_source,
        failures,
    )

    check(
        "No direct football-data.org access",
        "football-data.org"
        not in
        client_source.lower(),
        failures,
    )

    check(
        "No direct API-Football access",
        (
            "api-football"
            not in
            client_source.lower()
            and
            "api-sports"
            not in
            client_source.lower()
        ),
        failures,
    )

    print(
        "\n8. CONTRACT DEPENDENCY FRESHNESS"
    )

    verify_dependencies(
        client_contract,
        "10.2.1",
        failures,
    )

    verify_dependencies(
        environment_contract,
        "10.2.2",
        failures,
    )

    check(
        "client.ts SHA current",
        client_contract.get(
            "source_sha256"
        )
        ==
        sha256_file(
            CLIENT_FILE
        ),
        failures,
    )

    check(
        "config.ts SHA current",
        environment_contract.get(
            "source_sha256"
        )
        ==
        sha256_file(
            CONFIG_FILE
        ),
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

    client_promotion = (
        client_contract.get(
            "promotion",
            {}
        )
    )

    env_promotion = (
        environment_contract.get(
            "promotion",
            {}
        )
    )

    check(
        "10.2.1 contract did not self-promote",
        client_promotion.get(
            "stage10_2_1_complete"
        )
        is False,
        failures,
    )

    check(
        "10.2.2 contract did not self-promote",
        env_promotion.get(
            "stage10_2_2_complete"
        )
        is False,
        failures,
    )

    check(
        "Stage 10.2 remains incomplete",
        (
            client_promotion.get(
                "stage10_2_complete"
            )
            is False
            and
            env_promotion.get(
                "stage10_2_complete"
            )
            is False
        ),
        failures,
    )

    check(
        "Stage 10 remains incomplete",
        (
            client_promotion.get(
                "stage10_complete"
            )
            is False
            and
            env_promotion.get(
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
                "10.2.1-10.2.2",

            "name":
                (
                    "SHARED_HTTP_CLIENT_AND_"
                    "API_ENVIRONMENT_VERIFICATION"
                ),

            "status":
                "PASS",

            "stage_10_2_1_complete":
                True,

            "stage_10_2_2_complete":
                True,

            "shared_http_client":
                "LOCKED_AND_VERIFIED",

            "api_environment_config":
                "LOCKED_AND_VERIFIED",

            "transport":
                "WEB_FETCH_API",

            "server_only":
                True,

            "environment_variable":
                "FIXTUREIQ_API_BASE_URL",

            "production_env_required":
                True,

            "development_fallback":
                "http://127.0.0.1:5000",

            "request_policy": {
                "method":
                    "GET",

                "cache":
                    "no-store",

                "credentials":
                    "omit",

                "redirect":
                    "error",

                "automatic_retry":
                    False,

                "stale_fallback":
                    False,
            },

            "safety": {
                "next_public_backend_url":
                    False,

                "direct_provider_access":
                    False,

                "direct_artifact_access":
                    False,

                "write_requests":
                    False,

                "frontend_prediction_logic":
                    False,

                "runtime_schema_validation":
                    False,

                "semantic_error_mapping":
                    False,
            },

            "dependency_identity": {
                relative(
                    CLIENT_FILE
                ): {
                    "sha256":
                        sha256_file(
                            CLIENT_FILE
                        )
                },

                relative(
                    CONFIG_FILE
                ): {
                    "sha256":
                        sha256_file(
                            CONFIG_FILE
                        )
                },

                relative(
                    ENV_EXAMPLE_FILE
                ): {
                    "sha256":
                        sha256_file(
                            ENV_EXAMPLE_FILE
                        )
                },

                relative(
                    PACKAGE_JSON_FILE
                ): {
                    "sha256":
                        sha256_file(
                            PACKAGE_JSON_FILE
                        )
                },

                relative(
                    PACKAGE_LOCK_FILE
                ): {
                    "sha256":
                        sha256_file(
                            PACKAGE_LOCK_FILE
                        )
                },

                relative(
                    HTTP_CLIENT_CONTRACT_FILE
                ): {
                    "sha256":
                        sha256_file(
                            HTTP_CLIENT_CONTRACT_FILE
                        )
                },

                relative(
                    ENVIRONMENT_CONTRACT_FILE
                ): {
                    "sha256":
                        sha256_file(
                            ENVIRONMENT_CONTRACT_FILE
                        )
                },

                relative(
                    STAGE_10_1_FINAL_FILE
                ): {
                    "sha256":
                        sha256_file(
                            STAGE_10_1_FINAL_FILE
                        )
                },
            },

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "stage10_ready_for_10_2_3":
                True,

            "stage10_2_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.2.3",

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
        "\n" + "=" * 72
    )

    if passed:

        print(
            "STAGE 10.2.1: PASS"
        )

        print(
            "SHARED HTTP CLIENT: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.2.2: PASS"
        )

        print(
            "API BASE URL / ENVIRONMENT CONFIG: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.2.3"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.2.1 / 10.2.2: FAIL"
        )

        print()

        print(
            "Failures:"
        )

        for failure in failures:

            print(
                f"  - {failure}"
            )

    print("=" * 72)

    sys.exit(
        0
        if passed
        else 1
    )


if __name__ == "__main__":

    main()
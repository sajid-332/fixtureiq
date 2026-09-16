from __future__ import annotations

import hashlib
import json
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

ENDPOINT_CONTRACT_FILE = (
    DOCS
    / "frontend_api_endpoint_contract.json"
)

STAGE_10_1_FINAL_FILE = (
    FRONTEND_DATA
    / "stage10_1_final_verification.json"
)


HTTP_CLIENT_CONTRACT_FILE = (
    DOCS
    / "frontend_http_client_contract.json"
)

ENVIRONMENT_CONTRACT_FILE = (
    DOCS
    / "frontend_api_environment_contract.json"
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


def identity(
    path: Path,
) -> dict:

    return {
        "sha256":
            sha256_file(path)
    }


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.2.1 + 10.2.2"
    )

    print(
        "BUILD HTTP CLIENT + ENVIRONMENT CONTRACTS"
    )

    print("=" * 72)

    required_files = [
        CLIENT_FILE,
        CONFIG_FILE,
        ENV_EXAMPLE_FILE,
        PACKAGE_JSON_FILE,
        PACKAGE_LOCK_FILE,
        ENDPOINT_CONTRACT_FILE,
        STAGE_10_1_FINAL_FILE,
    ]

    for path in required_files:

        if not path.exists():

            raise RuntimeError(
                f"Missing required file: {path}"
            )

    previous = load_json(
        STAGE_10_1_FINAL_FILE
    )

    endpoint = load_json(
        ENDPOINT_CONTRACT_FILE
    )

    package_json = load_json(
        PACKAGE_JSON_FILE
    )

    if (
        previous.get("status")
        !=
        "PASS"
    ):

        raise RuntimeError(
            "Stage 10.1 final verification is not PASS."
        )

    if (
        previous.get(
            "stage_10_1_complete"
        )
        is not True
    ):

        raise RuntimeError(
            "Stage 10.1 is not complete."
        )

    if (
        previous.get(
            "stage10_ready_for_10_2_1"
        )
        is not True
    ):

        raise RuntimeError(
            "Stage 10.1 did not authorize 10.2.1."
        )

    if (
        endpoint.get("status")
        !=
        "LOCKED"
    ):

        raise RuntimeError(
            "Frontend endpoint contract is not LOCKED."
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

    if (
        "server-only"
        not in
        dependencies
    ):

        raise RuntimeError(
            "server-only is not a direct frontend dependency."
        )

    client_contract = {
        "stage":
            "10.2.1",

        "version":
            "1.0.0",

        "name":
            "FRONTEND_SHARED_HTTP_CLIENT",

        "status":
            "LOCKED",

        "source":
            relative(
                CLIENT_FILE
            ),

        "transport":
            "WEB_FETCH_API",

        "server_only":
            True,

        "allowed_methods": [
            "GET"
        ],

        "allowed_namespaces":
            endpoint.get(
                "allowed_namespaces",
                []
            ),

        "request_policy": {
            "accept":
                "application/json",

            "cache":
                "no-store",

            "credentials":
                "omit",

            "redirect":
                "error",

            "stale_fallback":
                False,

            "automatic_retry":
                False,
        },

        "url_policy": {
            "relative_api_paths_only":
                True,

            "cross_origin_override":
                False,

            "protocol_relative_override":
                False,

            "unlisted_namespace_access":
                False,

            "query_strings_supported":
                False,

            "fragments_supported":
                False,
        },

        "response_policy": {
            "preserve_http_status":
                True,

            "preserve_response_ok":
                True,

            "parse_json":
                True,

            "semantic_status_mapping_here":
                False,

            "semantic_status_mapping_owner":
                "10.2.7",

            "runtime_schema_validation_here":
                False,

            "runtime_schema_validation_owner":
                "10.2.6",
        },

        "forbidden": {
            "post":
                True,

            "put":
                True,

            "patch":
                True,

            "delete":
                True,

            "provider_fetch":
                True,

            "model_access":
                True,

            "artifact_access":
                True,

            "stale_cache":
                True,
        },

        "dependency_identity": {
            relative(
                CONFIG_FILE
            ):
                identity(
                    CONFIG_FILE
                ),

            relative(
                PACKAGE_JSON_FILE
            ):
                identity(
                    PACKAGE_JSON_FILE
                ),

            relative(
                PACKAGE_LOCK_FILE
            ):
                identity(
                    PACKAGE_LOCK_FILE
                ),

            relative(
                ENDPOINT_CONTRACT_FILE
            ):
                identity(
                    ENDPOINT_CONTRACT_FILE
                ),

            relative(
                STAGE_10_1_FINAL_FILE
            ):
                identity(
                    STAGE_10_1_FINAL_FILE
                ),
        },

        "source_sha256":
            sha256_file(
                CLIENT_FILE
            ),

        "promotion": {
            "stage10_2_1_complete":
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

    environment_contract = {
        "stage":
            "10.2.2",

        "version":
            "1.0.0",

        "name":
            "FRONTEND_API_BASE_URL_ENVIRONMENT_CONFIG",

        "status":
            "LOCKED",

        "source":
            relative(
                CONFIG_FILE
            ),

        "server_only":
            True,

        "environment_variable":
            "FIXTUREIQ_API_BASE_URL",

        "next_public_variable":
            False,

        "development": {
            "explicit_environment_value_preferred":
                True,

            "fallback_allowed":
                True,

            "fallback":
                "http://127.0.0.1:5000",
        },

        "production": {
            "explicit_environment_value_required":
                True,

            "fallback_allowed":
                False,
        },

        "base_url_policy": {
            "allowed_protocols": [
                "http",
                "https"
            ],

            "origin_only":
                True,

            "credentials_allowed":
                False,

            "path_allowed":
                False,

            "query_allowed":
                False,

            "fragment_allowed":
                False,

            "normalization_uses":
                "URL_API",

            "normalized_result":
                "ORIGIN",
        },

        "secrets_policy": {
            "provider_key_exposed":
                False,

            "backend_secret_exposed":
                False,

            "next_public_secret":
                False,
        },

        "environment_example":
            relative(
                ENV_EXAMPLE_FILE
            ),

        "dependency_identity": {
            relative(
                CLIENT_FILE
            ):
                identity(
                    CLIENT_FILE
                ),

            relative(
                ENV_EXAMPLE_FILE
            ):
                identity(
                    ENV_EXAMPLE_FILE
                ),

            relative(
                PACKAGE_JSON_FILE
            ):
                identity(
                    PACKAGE_JSON_FILE
                ),

            relative(
                PACKAGE_LOCK_FILE
            ):
                identity(
                    PACKAGE_LOCK_FILE
                ),

            relative(
                STAGE_10_1_FINAL_FILE
            ):
                identity(
                    STAGE_10_1_FINAL_FILE
                ),
        },

        "source_sha256":
            sha256_file(
                CONFIG_FILE
            ),

        "promotion": {
            "stage10_2_2_complete":
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
        HTTP_CLIENT_CONTRACT_FILE,
        client_contract,
    )

    save_json_atomic(
        ENVIRONMENT_CONTRACT_FILE,
        environment_contract,
    )

    print()

    print(
        "Shared client:"
    )

    print(
        f"  {relative(CLIENT_FILE)}"
    )

    print(
        "Environment config:"
    )

    print(
        f"  {relative(CONFIG_FILE)}"
    )

    print(
        "HTTP client contract:"
    )

    print(
        f"  {relative(HTTP_CLIENT_CONTRACT_FILE)}"
    )

    print(
        "Environment contract:"
    )

    print(
        f"  {relative(ENVIRONMENT_CONTRACT_FILE)}"
    )

    print()

    print("=" * 72)

    print(
        "STAGE 10.2.1 SHARED HTTP CLIENT: BUILT"
    )

    print(
        "STAGE 10.2.2 API ENVIRONMENT CONFIG: BUILT"
    )

    print(
        "STAGE 10 IS NOT YET PROMOTED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
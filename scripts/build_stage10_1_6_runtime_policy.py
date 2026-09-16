from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from http import HTTPStatus
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DOCS = ROOT / "docs" / "stage10"
FRONTEND_DATA = ROOT / "data" / "processed" / "frontend"

RESPONSIBILITY_FILE = (
    DOCS
    / "frontend_responsibility_contract.json"
)

ENDPOINT_FILE = (
    DOCS
    / "frontend_api_endpoint_contract.json"
)

ROUTE_FILE = (
    DOCS
    / "frontend_route_architecture.json"
)

DOMAIN_FILE = (
    DOCS
    / "frontend_domain_model_contract.json"
)

PREVIOUS_FILE = (
    FRONTEND_DATA
    / "stage10_1_4_10_1_5_verification.json"
)

TYPES_FILE = (
    ROOT
    / "frontend"
    / "lib"
    / "domain"
    / "types.ts"
)

OUTPUT_FILE = (
    DOCS
    / "frontend_runtime_state_policy.json"
)


def load_json(path: Path) -> dict:

    if not path.exists():

        raise RuntimeError(
            f"Missing artifact: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        payload = json.load(file)

    if not isinstance(payload, dict):

        raise RuntimeError(
            f"Expected JSON object: {path}"
        )

    return payload


def sha256_file(path: Path) -> str:

    digest = hashlib.sha256()

    with path.open("rb") as file:

        for chunk in iter(
            lambda: file.read(
                1024 * 1024
            ),
            b"",
        ):

            digest.update(chunk)

    return digest.hexdigest()


def relative(path: Path) -> str:

    return (
        str(
            path.resolve().relative_to(
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


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.1.6"
    )

    print(
        "FRONTEND FRESHNESS / ERROR-STATE POLICY"
    )

    print("=" * 72)

    responsibility = load_json(
        RESPONSIBILITY_FILE
    )

    endpoint = load_json(
        ENDPOINT_FILE
    )

    route = load_json(
        ROUTE_FILE
    )

    domain = load_json(
        DOMAIN_FILE
    )

    previous = load_json(
        PREVIOUS_FILE
    )

    if (
        previous.get("status")
        !=
        "PASS"
    ):

        raise RuntimeError(
            "10.1.4-10.1.5 verification is not PASS."
        )

    if (
        previous.get(
            "stage10_ready_for_10_1_6"
        )
        is not True
    ):

        raise RuntimeError(
            "10.1.5 did not authorize 10.1.6."
        )

    if (
        responsibility.get("status")
        !=
        "LOCKED"
    ):

        raise RuntimeError(
            "Responsibility contract is not LOCKED."
        )

    if (
        endpoint.get("status")
        !=
        "LOCKED"
    ):

        raise RuntimeError(
            "Endpoint contract is not LOCKED."
        )

    if (
        route.get("status")
        !=
        "LOCKED"
    ):

        raise RuntimeError(
            "Route contract is not LOCKED."
        )

    if (
        domain.get("status")
        !=
        "LOCKED"
    ):

        raise RuntimeError(
            "Domain model contract is not LOCKED."
        )

    policy = {
        "stage":
            "10.1.6",

        "version":
            "1.0.0",

        "name":
            "FRONTEND_FRESHNESS_ERROR_STATE_POLICY",

        "status":
            "LOCKED",

        "authority": {
            "prediction":
                "STAGE7",

            "context":
                "STAGE8",

            "intelligence":
                "STAGE9",

            "presentation":
                "STAGE10",

            "freshness":
                "BACKEND_RUNTIME_SERVICES",
        },

        "ui_states": [
            "READY",
            "LOADING",
            "NOT_FOUND",
            "NOT_READY",
            "CONNECTION_ERROR",
        ],

        "http_mapping": {
            str(
                HTTPStatus.OK.value
            ):
                "READY",

            str(
                HTTPStatus.NOT_FOUND.value
            ):
                "NOT_FOUND",

            str(
                HTTPStatus.SERVICE_UNAVAILABLE.value
            ):
                "NOT_READY",
        },

        "non_http_mapping": {
            "REQUEST_START":
                "LOADING",

            "NETWORK_FAILURE":
                "CONNECTION_ERROR",

            "UNEXPECTED_HTTP_STATUS":
                "CONNECTION_ERROR",

            "INVALID_RESPONSE":
                "CONNECTION_ERROR",
        },

        "state_rules": {
            "READY": {
                "backend_verified_payload_required":
                    True,

                "may_render_match_data":
                    True,

                "previous_payload_fallback":
                    False,
            },

            "LOADING": {
                "may_render_previous_match_data":
                    False,

                "may_render_loading_ui":
                    True,
            },

            "NOT_FOUND": {
                "source":
                    "HTTP_404",

                "may_render_previous_match_data":
                    False,

                "may_render_not_found_ui":
                    True,
            },

            "NOT_READY": {
                "source":
                    "HTTP_503",

                "meaning":
                    "VERIFIED_CURRENT_DATA_TEMPORARILY_UNAVAILABLE",

                "may_render_previous_match_data":
                    False,

                "may_render_not_ready_ui":
                    True,
            },

            "CONNECTION_ERROR": {
                "sources": [
                    "NETWORK_FAILURE",
                    "UNEXPECTED_HTTP_STATUS",
                    "INVALID_RESPONSE"
                ],

                "may_render_previous_match_data":
                    False,

                "may_render_connection_error_ui":
                    True,
            },
        },

        "request_transition_policy": {
            "every_new_request_enters_loading":
                True,

            "previous_payload_cleared_before_refresh":
                True,

            "200_to_ready":
                True,

            "404_to_not_found":
                True,

            "503_to_not_ready":
                True,

            "network_failure_to_connection_error":
                True,

            "unexpected_status_to_connection_error":
                True,

            "invalid_response_to_connection_error":
                True,
        },

        "retry_policy": {
            "retry_allowed":
                True,

            "allowed_from_states": [
                "NOT_READY",
                "CONNECTION_ERROR"
            ],

            "request_method":
                "GET",

            "retry_enters_loading":
                True,

            "previous_payload_may_remain_visible":
                False,

            "automatic_retry_schedule_locked_here":
                False,

            "automatic_retry_owner":
                "10.8.9",
        },

        "cache_policy": {
            "frontend_fetch_cache_mode":
                "no-store",

            "respect_backend_no_store":
                True,

            "stale_prediction_cache":
                False,

            "stale_context_cache":
                False,

            "stale_intelligence_cache":
                False,

            "local_storage_prediction_cache":
                False,

            "session_storage_prediction_cache":
                False,

            "service_worker_stale_fallback":
                False,
        },

        "freshness_policy": {
            "frontend_may_determine_fixture_freshness":
                False,

            "frontend_may_override_not_ready":
                False,

            "frontend_may_extend_backend_validity":
                False,

            "frontend_may_reuse_old_ready_payload_after_failure":
                False,

            "backend_status_is_authoritative":
                True,

            "temporal_boundary_owned_by_backend":
                True,
        },

        "display_policy": {
            "loading_must_not_show_stale_values":
                True,

            "not_found_must_not_show_stale_values":
                True,

            "not_ready_must_not_show_stale_values":
                True,

            "connection_error_must_not_show_stale_values":
                True,

            "not_ready_state_visible_to_user":
                True,

            "connection_error_state_visible_to_user":
                True,
        },

        "implementation_boundary": {
            "policy_only":
                True,

            "network_client_implemented_here":
                False,

            "runtime_validation_implemented_here":
                False,

            "ui_components_implemented_here":
                False,

            "api_client_owner":
                "10.2",

            "failure_ui_owner":
                "10.8",
        },

        "dependency_identity": {
            relative(
                RESPONSIBILITY_FILE
            ): {
                "sha256":
                    sha256_file(
                        RESPONSIBILITY_FILE
                    )
            },

            relative(
                ENDPOINT_FILE
            ): {
                "sha256":
                    sha256_file(
                        ENDPOINT_FILE
                    )
            },

            relative(
                ROUTE_FILE
            ): {
                "sha256":
                    sha256_file(
                        ROUTE_FILE
                    )
            },

            relative(
                DOMAIN_FILE
            ): {
                "sha256":
                    sha256_file(
                        DOMAIN_FILE
                    )
            },

            relative(
                TYPES_FILE
            ): {
                "sha256":
                    sha256_file(
                        TYPES_FILE
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

        "promotion": {
            "stage10_1_6_complete":
                False,

            "stage10_1_complete":
                False,

            "stage10_complete":
                False,

            "promotion_authorized":
                False,
        },

        "generated_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }

    save_json_atomic(
        OUTPUT_FILE,
        policy,
    )

    print()

    print(
        f"200 -> "
        f"{policy['http_mapping']['200']}"
    )

    print(
        f"404 -> "
        f"{policy['http_mapping']['404']}"
    )

    print(
        f"503 -> "
        f"{policy['http_mapping']['503']}"
    )

    print(
        "Network failure -> CONNECTION_ERROR"
    )

    print(
        "Stale fallback -> DISABLED"
    )

    print(
        "Frontend cache mode -> no-store"
    )

    print()

    print(
        f"Saved: {relative(OUTPUT_FILE)}"
    )

    print()

    print("=" * 72)

    print(
        "STAGE 10.1.6 RUNTIME-STATE POLICY: BUILT"
    )

    print(
        "POLICY STATUS: LOCKED"
    )

    print(
        "STAGE 10 IS NOT YET PROMOTED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
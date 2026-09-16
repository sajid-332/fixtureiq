from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from http import HTTPStatus
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


AUDIT_FILE = (
    DOCS
    / "frontend_audit.json"
)

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

RUNTIME_POLICY_FILE = (
    DOCS
    / "frontend_runtime_state_policy.json"
)

STAGE_10_1_2_FILE = (
    FRONTEND_DATA
    / "stage10_1_1_10_1_2_verification.json"
)

STAGE_10_1_3_FILE = (
    FRONTEND_DATA
    / "stage10_1_3_verification.json"
)

STAGE_10_1_4_5_FILE = (
    FRONTEND_DATA
    / "stage10_1_4_10_1_5_verification.json"
)

TYPES_FILE = (
    FRONTEND
    / "lib"
    / "domain"
    / "types.ts"
)

OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_1_final_verification.json"
)


SOURCE_EXTENSIONS = {
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
}

IGNORED_DIRECTORIES = {
    "node_modules",
    ".next",
    "out",
    "dist",
    "coverage",
}

FORBIDDEN_PATTERNS = {
    "direct_processed_data_access":
        re.compile(
            r"data[\\/]+processed",
            re.IGNORECASE,
        ),

    "direct_historical_data_access":
        re.compile(
            r"data[\\/]+historical",
            re.IGNORECASE,
        ),

    "direct_joblib_access":
        re.compile(
            r"\.joblib\b",
            re.IGNORECASE,
        ),

    "direct_provider_access":
        re.compile(
            (
                r"\b(?:api-football|"
                r"api-sports|"
                r"football-data\.org)\b"
            ),
            re.IGNORECASE,
        ),
}


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
            f"Expected object: {path}"
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

    dependencies = payload.get(
        "dependency_identity",
        {}
    )

    check(
        f"{label} dependency identity exists",
        isinstance(
            dependencies,
            dict,
        )
        and
        bool(dependencies),
        failures,
    )

    if not isinstance(
        dependencies,
        dict,
    ):

        return

    for path_text, identity in (
        dependencies.items()
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


def walk_source_files(
    directory: Path,
) -> list[Path]:

    result = []

    for path in directory.rglob("*"):

        if not path.is_file():

            continue

        if any(
            part
            in
            IGNORED_DIRECTORIES

            for part in path.parts
        ):

            continue

        if (
            path.suffix.lower()
            not in
            SOURCE_EXTENSIONS
        ):

            continue

        result.append(path)

    return result


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
        "FixtureIQ Stage 10.1.6 + 10.1.7"
    )

    print(
        "RUNTIME POLICY + STAGE 10.1 FINAL VERIFICATION"
    )

    print("=" * 72)

    failures: list[str] = []

    required_files = [
        AUDIT_FILE,
        RESPONSIBILITY_FILE,
        ENDPOINT_FILE,
        ROUTE_FILE,
        DOMAIN_FILE,
        RUNTIME_POLICY_FILE,
        STAGE_10_1_2_FILE,
        STAGE_10_1_3_FILE,
        STAGE_10_1_4_5_FILE,
        TYPES_FILE,
    ]

    print(
        "\n1. REQUIRED STAGE 10.1 ARTIFACTS"
    )

    for path in required_files:

        check(
            relative(path),
            path.exists(),
            failures,
        )

    if failures:

        sys.exit(1)

    audit = load_json(
        AUDIT_FILE
    )

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

    policy = load_json(
        RUNTIME_POLICY_FILE
    )

    evidence_12 = load_json(
        STAGE_10_1_2_FILE
    )

    evidence_13 = load_json(
        STAGE_10_1_3_FILE
    )

    evidence_145 = load_json(
        STAGE_10_1_4_5_FILE
    )

    # ========================================================
    # Previous evidence
    # ========================================================

    print(
        "\n2. PREVIOUS SUBSTAGE EVIDENCE"
    )

    check(
        "10.1.1-10.1.2 PASS",
        evidence_12.get("status")
        ==
        "PASS",
        failures,
    )

    check(
        "10.1.1 complete",
        evidence_12.get(
            "stage_10_1_1_complete"
        )
        is True,
        failures,
    )

    check(
        "10.1.2 complete",
        evidence_12.get(
            "stage_10_1_2_complete"
        )
        is True,
        failures,
    )

    check(
        "10.1.3 PASS",
        evidence_13.get("status")
        ==
        "PASS",
        failures,
    )

    check(
        "10.1.3 complete",
        evidence_13.get(
            "stage_10_1_3_complete"
        )
        is True,
        failures,
    )

    check(
        "10.1.4-10.1.5 PASS",
        evidence_145.get("status")
        ==
        "PASS",
        failures,
    )

    check(
        "10.1.4 complete",
        evidence_145.get(
            "stage_10_1_4_complete"
        )
        is True,
        failures,
    )

    check(
        "10.1.5 complete",
        evidence_145.get(
            "stage_10_1_5_complete"
        )
        is True,
        failures,
    )

    check(
        "10.1.5 authorized 10.1.6",
        evidence_145.get(
            "stage10_ready_for_10_1_6"
        )
        is True,
        failures,
    )

    # ========================================================
    # Contracts
    # ========================================================

    print(
        "\n3. STAGE 10.1 CONTRACT LOCKS"
    )

    for label, payload in [
        (
            "Responsibility contract",
            responsibility,
        ),
        (
            "Endpoint contract",
            endpoint,
        ),
        (
            "Route architecture",
            route,
        ),
        (
            "Domain models",
            domain,
        ),
        (
            "Runtime-state policy",
            policy,
        ),
    ]:

        check(
            f"{label} LOCKED",
            payload.get("status")
            ==
            "LOCKED",
            failures,
        )

    # ========================================================
    # 10.1.6 runtime policy
    # ========================================================

    print(
        "\n4. STAGE 10.1.6 RUNTIME STATE POLICY"
    )

    check(
        "Policy stage exact",
        policy.get("stage")
        ==
        "10.1.6",
        failures,
    )

    expected_states = {
        "READY",
        "LOADING",
        "NOT_FOUND",
        "NOT_READY",
        "CONNECTION_ERROR",
    }

    check(
        "UI state set exact",
        set(
            policy.get(
                "ui_states",
                [],
            )
        )
        ==
        expected_states,
        failures,
    )

    http_mapping = policy.get(
        "http_mapping",
        {}
    )

    check(
        "HTTP 200 -> READY",
        http_mapping.get(
            str(
                HTTPStatus.OK.value
            )
        )
        ==
        "READY",
        failures,
    )

    check(
        "HTTP 404 -> NOT_FOUND",
        http_mapping.get(
            str(
                HTTPStatus.NOT_FOUND.value
            )
        )
        ==
        "NOT_FOUND",
        failures,
    )

    check(
        "HTTP 503 -> NOT_READY",
        http_mapping.get(
            str(
                HTTPStatus.SERVICE_UNAVAILABLE.value
            )
        )
        ==
        "NOT_READY",
        failures,
    )

    non_http = policy.get(
        "non_http_mapping",
        {}
    )

    check(
        "Request start -> LOADING",
        non_http.get(
            "REQUEST_START"
        )
        ==
        "LOADING",
        failures,
    )

    check(
        "Network failure -> CONNECTION_ERROR",
        non_http.get(
            "NETWORK_FAILURE"
        )
        ==
        "CONNECTION_ERROR",
        failures,
    )

    check(
        "Unexpected HTTP -> CONNECTION_ERROR",
        non_http.get(
            "UNEXPECTED_HTTP_STATUS"
        )
        ==
        "CONNECTION_ERROR",
        failures,
    )

    check(
        "Invalid response -> CONNECTION_ERROR",
        non_http.get(
            "INVALID_RESPONSE"
        )
        ==
        "CONNECTION_ERROR",
        failures,
    )

    # ========================================================
    # Stale-data protection
    # ========================================================

    print(
        "\n5. STALE-DATA PROTECTION"
    )

    cache = policy.get(
        "cache_policy",
        {}
    )

    freshness = policy.get(
        "freshness_policy",
        {}
    )

    display = policy.get(
        "display_policy",
        {}
    )

    check(
        "Frontend fetch uses no-store",
        cache.get(
            "frontend_fetch_cache_mode"
        )
        ==
        "no-store",
        failures,
    )

    check(
        "Backend no-store respected",
        cache.get(
            "respect_backend_no_store"
        )
        is True,
        failures,
    )

    for key in [
        "stale_prediction_cache",
        "stale_context_cache",
        "stale_intelligence_cache",
        "local_storage_prediction_cache",
        "session_storage_prediction_cache",
        "service_worker_stale_fallback",
    ]:

        check(
            f"{key} disabled",
            cache.get(key)
            is False,
            failures,
        )

    check(
        "Frontend cannot determine freshness",
        freshness.get(
            "frontend_may_determine_fixture_freshness"
        )
        is False,
        failures,
    )

    check(
        "Frontend cannot override NOT_READY",
        freshness.get(
            "frontend_may_override_not_ready"
        )
        is False,
        failures,
    )

    check(
        "Frontend cannot extend backend validity",
        freshness.get(
            "frontend_may_extend_backend_validity"
        )
        is False,
        failures,
    )

    check(
        "Old READY payload cannot survive failure",
        freshness.get(
            "frontend_may_reuse_old_ready_payload_after_failure"
        )
        is False,
        failures,
    )

    check(
        "Backend freshness authority retained",
        freshness.get(
            "backend_status_is_authoritative"
        )
        is True,
        failures,
    )

    for key in [
        "loading_must_not_show_stale_values",
        "not_found_must_not_show_stale_values",
        "not_ready_must_not_show_stale_values",
        "connection_error_must_not_show_stale_values",
    ]:

        check(
            key,
            display.get(key)
            is True,
            failures,
        )

    # ========================================================
    # Retry boundary
    # ========================================================

    print(
        "\n6. RETRY POLICY"
    )

    retry = policy.get(
        "retry_policy",
        {}
    )

    check(
        "Retry is GET-only",
        retry.get(
            "request_method"
        )
        ==
        "GET",
        failures,
    )

    check(
        "Retry allowed only from recoverable states",
        set(
            retry.get(
                "allowed_from_states",
                [],
            )
        )
        ==
        {
            "NOT_READY",
            "CONNECTION_ERROR",
        },
        failures,
    )

    check(
        "Retry re-enters LOADING",
        retry.get(
            "retry_enters_loading"
        )
        is True,
        failures,
    )

    check(
        "Retry cannot display previous payload",
        retry.get(
            "previous_payload_may_remain_visible"
        )
        is False,
        failures,
    )

    check(
        "Automatic retry timing deferred to 10.8.9",
        (
            retry.get(
                "automatic_retry_schedule_locked_here"
            )
            is False
            and
            retry.get(
                "automatic_retry_owner"
            )
            ==
            "10.8.9"
        ),
        failures,
    )

    # ========================================================
    # TypeScript state model
    # ========================================================

    print(
        "\n7. TYPESCRIPT STATE MODEL"
    )

    types_source = TYPES_FILE.read_text(
        encoding="utf-8"
    )

    for state in sorted(
        expected_states
    ):

        check(
            f"UiDataState includes {state}",
            f'"{state}"'
            in
            types_source,
            failures,
        )

    # ========================================================
    # Route architecture
    # ========================================================

    print(
        "\n8. ROUTE ARCHITECTURE"
    )

    routes = route.get(
        "routes",
        []
    )

    check(
        "Exactly three user-facing routes",
        len(routes)
        ==
        3,
        failures,
    )

    check(
        "Primary source remains Stage 9 intelligence",
        route.get(
            "routing_principles",
            {},
        ).get(
            "primary_user_data_source"
        )
        ==
        "/api/v1/intelligence",
        failures,
    )

    check(
        "Server-first architecture retained",
        route.get(
            "routing_principles",
            {},
        ).get(
            "server_first"
        )
        is True,
        failures,
    )

    # ========================================================
    # Endpoint contract
    # ========================================================

    print(
        "\n9. API CONTRACT"
    )

    check(
        "Frontend methods remain GET-only",
        endpoint.get(
            "allowed_http_methods"
        )
        ==
        ["GET"],
        failures,
    )

    check(
        "Five intelligence endpoints remain locked",
        endpoint.get(
            "namespace_counts",
            {},
        ).get(
            "intelligence"
        )
        ==
        5,
        failures,
    )

    # ========================================================
    # Current dependency identities
    # ========================================================

    print(
        "\n10. DEPENDENCY FRESHNESS"
    )

    verify_dependencies(
        route,
        "10.1.4",
        failures,
    )

    verify_dependencies(
        domain,
        "10.1.5",
        failures,
    )

    verify_dependencies(
        policy,
        "10.1.6",
        failures,
    )

    # ========================================================
    # Frontend boundary scan
    # ========================================================

    print(
        "\n11. FRONTEND BOUNDARY SCAN"
    )

    boundary_hits = []

    for path in walk_source_files(
        FRONTEND
    ):

        # Audit/build scripts are development tooling,
        # not application runtime source.
        if (
            "scripts"
            in
            path.parts
        ):

            continue

        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        for name, pattern in (
            FORBIDDEN_PATTERNS.items()
        ):

            if pattern.search(text):

                boundary_hits.append(
                    (
                        relative(path),
                        name,
                    )
                )

    check(
        "No direct artifact/provider access in frontend runtime source",
        len(boundary_hits)
        ==
        0,
        failures,
    )

    if boundary_hits:

        for path, reason in boundary_hits:

            print(
                f"  {path}: {reason}"
            )

    # ========================================================
    # No Next.js backend proxy routes
    # ========================================================

    print(
        "\n12. NEXT.JS ROUTE-HANDLER BOUNDARY"
    )

    app_root_text = route.get(
        "app_root"
    )

    app_root = resolve_project_path(
        app_root_text
    )

    route_handlers = []

    if app_root.exists():

        for path in app_root.rglob(
            "route.*"
        ):

            if (
                path.suffix.lower()
                in
                SOURCE_EXTENSIONS
            ):

                route_handlers.append(
                    relative(path)
                )

    check(
        "No frontend API route handlers introduced",
        len(route_handlers)
        ==
        0,
        failures,
    )

    # ========================================================
    # TypeScript
    # ========================================================

    print(
        "\n13. TYPESCRIPT COMPILER"
    )

    typescript_ok, compiler_output = (
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
        compiler_output
    ):

        print(
            compiler_output
        )

    # ========================================================
    # No Stage 10 promotion
    # ========================================================

    print(
        "\n14. PROMOTION BOUNDARY"
    )

    policy_promotion = policy.get(
        "promotion",
        {}
    )

    check(
        "10.1.6 contract did not self-promote",
        policy_promotion.get(
            "stage10_1_6_complete"
        )
        is False,
        failures,
    )

    check(
        "Stage 10 not promoted",
        policy_promotion.get(
            "stage10_complete"
        )
        is False,
        failures,
    )

    # ========================================================
    # Save 10.1 final evidence
    # ========================================================

    print(
        "\n15. SAVE STAGE 10.1 FINAL EVIDENCE"
    )

    passed = (
        len(failures)
        ==
        0
    )

    if passed:

        evidence = {
            "stage":
                "10.1.7",

            "name":
                "STAGE_10_1_ARCHITECTURE_FINAL_VERIFICATION",

            "status":
                "PASS",

            "stage_10_1_1_complete":
                True,

            "stage_10_1_2_complete":
                True,

            "stage_10_1_3_complete":
                True,

            "stage_10_1_4_complete":
                True,

            "stage_10_1_5_complete":
                True,

            "stage_10_1_6_complete":
                True,

            "stage_10_1_7_complete":
                True,

            "stage_10_1_complete":
                True,

            "frontend_architecture":
                "LOCKED_AND_VERIFIED",

            "responsibility_boundary":
                "VERIFIED",

            "api_endpoint_contract":
                "VERIFIED",

            "route_architecture":
                "VERIFIED",

            "typescript_domain_models":
                "VERIFIED",

            "freshness_error_state_policy":
                "VERIFIED",

            "typescript_compiler":
                "PASS",

            "runtime_policy": {
                "200":
                    "READY",

                "404":
                    "NOT_FOUND",

                "503":
                    "NOT_READY",

                "network_failure":
                    "CONNECTION_ERROR",

                "cache":
                    "no-store",

                "stale_fallback":
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

            "safety": {
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

                "write_api_methods":
                    False,

                "frontend_api_proxy_routes":
                    False,
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
                    RUNTIME_POLICY_FILE
                ): {
                    "sha256":
                        sha256_file(
                            RUNTIME_POLICY_FILE
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
                    STAGE_10_1_2_FILE
                ): {
                    "sha256":
                        sha256_file(
                            STAGE_10_1_2_FILE
                        )
                },

                relative(
                    STAGE_10_1_3_FILE
                ): {
                    "sha256":
                        sha256_file(
                            STAGE_10_1_3_FILE
                        )
                },

                relative(
                    STAGE_10_1_4_5_FILE
                ): {
                    "sha256":
                        sha256_file(
                            STAGE_10_1_4_5_FILE
                        )
                },
            },

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "stage10_ready_for_10_2_1":
                True,

            "stage10_complete":
                False,

            "promotion": {
                "stage10_1_promoted":
                    True,

                "stage10_promoted":
                    False,
            },

            "next_stage":
                "10.2.1",

            "failures":
                [],
        }

        save_json_atomic(
            OUTPUT_FILE,
            evidence,
        )

        print(
            relative(OUTPUT_FILE)
        )

    print(
        "\n" + "=" * 72
    )

    if passed:

        print(
            "STAGE 10.1.6: PASS"
        )

        print(
            "FRESHNESS / ERROR-STATE POLICY: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.1.7: PASS"
        )

        print(
            "STAGE 10.1 ARCHITECTURE CONTRACT: VERIFIED"
        )

        print()

        print(
            "STAGE 10.1: COMPLETE"
        )

        print(
            "STAGE 10 READY FOR 10.2.1"
        )

        print()

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.1.6 / 10.1.7: FAIL"
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
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
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


# ============================================================
# Stage 10 final evidence
# ============================================================

STAGE10_FINAL_ARTIFACTS = {
    f"10.{number}":
        FRONTEND_DATA
        / f"stage10_{number}_final_verification.json"
    for number in range(
        1,
        11,
    )
}


STAGE10_10_FINAL = (
    FRONTEND_DATA
    / "stage10_10_final_verification.json"
)


# ============================================================
# Upstream authority evidence
# ============================================================

STAGE7_FINAL = (
    ROOT
    / "data"
    / "processed"
    / "production"
    / "stage7_9_final_verification.json"
)

STAGE8_FINAL = (
    ROOT
    / "data"
    / "processed"
    / "context"
    / "stage8_final_verification.json"
)

STAGE9_FINAL = (
    ROOT
    / "data"
    / "processed"
    / "intelligence"
    / "stage9_final_verification.json"
)


# ============================================================
# Architecture contracts
# ============================================================

RESPONSIBILITY_CONTRACT = (
    DOCS
    / "frontend_responsibility_contract.json"
)

API_ENDPOINT_CONTRACT = (
    DOCS
    / "frontend_api_endpoint_contract.json"
)

ROUTE_CONTRACT = (
    DOCS
    / "frontend_route_architecture.json"
)

DOMAIN_CONTRACT = (
    DOCS
    / "frontend_domain_model_contract.json"
)

RUNTIME_POLICY = (
    DOCS
    / "frontend_runtime_state_policy.json"
)

HTTP_CLIENT_CONTRACT = (
    DOCS
    / "frontend_http_client_contract.json"
)


# ============================================================
# Core frontend files
# ============================================================

PACKAGE_JSON = (
    FRONTEND
    / "package.json"
)

PACKAGE_LOCK = (
    FRONTEND
    / "package-lock.json"
)


API_CLIENT = (
    FRONTEND
    / "lib"
    / "api"
    / "client.ts"
)

API_CONFIG = (
    FRONTEND
    / "lib"
    / "api"
    / "config.ts"
)

API_MAPPED = (
    FRONTEND
    / "lib"
    / "api"
    / "mapped.ts"
)

API_RESULT = (
    FRONTEND
    / "lib"
    / "api"
    / "result.ts"
)

API_VALIDATED = (
    FRONTEND
    / "lib"
    / "api"
    / "validated.ts"
)

API_VALIDATION = (
    FRONTEND
    / "lib"
    / "api"
    / "validation.ts"
)

API_VALIDATION_TEST = (
    FRONTEND
    / "scripts"
    / "verify-stage10-api-validation.mjs"
)

API_MAPPING_TEST = (
    FRONTEND
    / "scripts"
    / "verify-stage10-api-result-mapping.mjs"
)


# ============================================================
# User-facing routes
# ============================================================

ROOT_PAGE = (
    FRONTEND
    / "app"
    / "page.tsx"
)

MATCH_PAGE = (
    FRONTEND
    / "app"
    / "matches"
    / "[fixtureId]"
    / "page.tsx"
)

TEAM_PAGE = (
    FRONTEND
    / "app"
    / "teams"
    / "[teamName]"
    / "page.tsx"
)


# ============================================================
# Runtime UX
# ============================================================

ROOT_LOADING = (
    FRONTEND
    / "app"
    / "loading.tsx"
)

MATCH_LOADING = (
    FRONTEND
    / "app"
    / "matches"
    / "[fixtureId]"
    / "loading.tsx"
)

TEAM_LOADING = (
    FRONTEND
    / "app"
    / "teams"
    / "[teamName]"
    / "loading.tsx"
)

ROOT_NOT_FOUND = (
    FRONTEND
    / "app"
    / "not-found.tsx"
)

MATCH_NOT_FOUND = (
    FRONTEND
    / "app"
    / "matches"
    / "[fixtureId]"
    / "not-found.tsx"
)

TEAM_NOT_FOUND = (
    FRONTEND
    / "app"
    / "teams"
    / "[teamName]"
    / "not-found.tsx"
)


READY_STATE = (
    FRONTEND
    / "components"
    / "runtime"
    / "ready-state.tsx"
)

SERVICE_NOT_READY = (
    FRONTEND
    / "components"
    / "runtime"
    / "service-not-ready-state.tsx"
)

CONNECTION_ERROR = (
    FRONTEND
    / "components"
    / "runtime"
    / "connection-error-state.tsx"
)

EMPTY_FIXTURES = (
    FRONTEND
    / "components"
    / "runtime"
    / "empty-fixtures-state.tsx"
)

RETRY_ACTION = (
    FRONTEND
    / "components"
    / "runtime"
    / "retry-action.tsx"
)


# ============================================================
# Reusable Stage 10.7 components
# ============================================================

REUSABLE_COMPONENTS = [
    FRONTEND
    / "components"
    / "matches"
    / "match-card.tsx",

    FRONTEND
    / "components"
    / "ui"
    / "probability-bar.tsx",

    FRONTEND
    / "components"
    / "ui"
    / "outcome-badge.tsx",

    FRONTEND
    / "components"
    / "ui"
    / "confidence-badge.tsx",

    FRONTEND
    / "components"
    / "ui"
    / "uncertainty-badge.tsx",

    FRONTEND
    / "components"
    / "ui"
    / "context-alignment-badge.tsx",

    FRONTEND
    / "components"
    / "ui"
    / "context-score.tsx",

    FRONTEND
    / "components"
    / "ui"
    / "team-comparison-row.tsx",

    FRONTEND
    / "components"
    / "ui"
    / "recent-form-display.tsx",

    FRONTEND
    / "components"
    / "ui"
    / "intelligence-explanation.tsx",

    FRONTEND
    / "components"
    / "ui"
    / "freshness-indicator.tsx",

    FRONTEND
    / "components"
    / "ui"
    / "empty-state.tsx",

    FRONTEND
    / "components"
    / "ui"
    / "error-state.tsx",

    FRONTEND
    / "components"
    / "ui"
    / "loading-state.tsx",
]


# ============================================================
# Final outputs
# ============================================================

STAGE10_11_OUTPUT = (
    FRONTEND_DATA
    / "stage10_11_final_verification.json"
)

STAGE10_FINAL_OUTPUT = (
    FRONTEND_DATA
    / "stage10_final_verification.json"
)


failures: list[str] = []


# ============================================================
# Helpers
# ============================================================

def relative(
    path: Path,
) -> str:

    return str(
        path.resolve().relative_to(
            ROOT.resolve()
        )
    ).replace(
        "\\",
        "/",
    )


def source(
    path: Path,
) -> str:

    return path.read_text(
        encoding="utf-8"
    )


def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise RuntimeError(
            f"Missing JSON: {relative(path)}"
        )


    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        value = json.load(
            file
        )


    if not isinstance(
        value,
        dict,
    ):

        raise RuntimeError(
            f"Expected JSON object: {relative(path)}"
        )


    return value


def save_json(
    path: Path,
    value: dict,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )


    temporary.write_text(
        json.dumps(
            value,
            indent=2,
        )
        +
        "\n",
        encoding="utf-8",
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

        for chunk in iter(
            lambda: file.read(
                1024 * 1024
            ),
            b"",
        ):

            digest.update(
                chunk
            )


    return digest.hexdigest()


def verify(
    label: str,
    condition: bool,
) -> None:

    print(
        f"{label}: "
        +
        (
            "PASS"
            if condition
            else "FAIL"
        )
    )


    if not condition:

        failures.append(
            label
        )


def artifact_pass(
    artifact: dict,
) -> bool:

    return (
        artifact.get(
            "status"
        )
        ==
        "PASS"
    )


def npm_path() -> str:

    executable = (
        shutil.which(
            "npm.cmd"
        )
        or
        shutil.which(
            "npm"
        )
    )


    if executable is None:

        raise RuntimeError(
            "npm executable not found."
        )


    return executable


def node_path() -> str:

    executable = (
        shutil.which(
            "node.exe"
        )
        or
        shutil.which(
            "node"
        )
    )


    if executable is None:

        raise RuntimeError(
            "node executable not found."
        )


    return executable


def run_command(
    args: list[str],
    cwd: Path,
    env: dict | None = None,
) -> tuple[bool, str]:

    result = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


    output = (
        result.stdout
        +
        result.stderr
    ).strip()


    return (
        result.returncode == 0,
        output,
    )


def flatten_strings(
    value: object,
) -> list[str]:

    result: list[str] = []


    if isinstance(
        value,
        str,
    ):

        result.append(
            value
        )


    elif isinstance(
        value,
        dict,
    ):

        for key, item in value.items():

            result.extend(
                flatten_strings(
                    key
                )
            )

            result.extend(
                flatten_strings(
                    item
                )
            )


    elif isinstance(
        value,
        list,
    ):

        for item in value:

            result.extend(
                flatten_strings(
                    item
                )
            )


    return result


def runtime_source_files() -> list[Path]:

    roots = [
        FRONTEND
        / "app",

        FRONTEND
        / "components",

        FRONTEND
        / "lib",
    ]


    extensions = {
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
    }


    files: list[Path] = []


    for root in roots:

        if not root.exists():

            continue


        for path in root.rglob(
            "*"
        ):

            if (
                path.is_file()
                and
                path.suffix
                in
                extensions
            ):

                files.append(
                    path
                )


    return sorted(
        files
    )


def runtime_sources() -> dict[Path, str]:

    return {
        path:
            source(
                path
            )
        for path in runtime_source_files()
    }


def imports_filesystem(
    text: str,
) -> bool:

    pattern = re.compile(
        r'''
        (?:
            from
            \s*
            ["']
            (?:
                node:
            )?
            fs
            (?:
                /promises
            )?
            ["']
        )
        |
        (?:
            require
            \(
            \s*
            ["']
            (?:
                node:
            )?
            fs
            (?:
                /promises
            )?
            ["']
            \s*
            \)
        )
        ''',
        re.VERBOSE,
    )


    return (
        pattern.search(
            text
        )
        is not None
    )


def page_route(
    path: Path,
) -> str:

    relative_page = (
        path
        .resolve()
        .relative_to(
            (
                FRONTEND
                / "app"
            ).resolve()
        )
    )


    parts = list(
        relative_page.parts[:-1]
    )


    if not parts:

        return "/"


    return (
        "/"
        +
        "/".join(
            parts
        )
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print(
        "=" * 76
    )

    print(
        "FixtureIQ Stage 10.11"
    )

    print(
        "FINAL STAGE 10 VERIFICATION AND PROMOTION"
    )

    print(
        "=" * 76
    )


    # ========================================================
    # Foundation
    # ========================================================

    print(
        "\n1. REQUIRED FINAL EVIDENCE"
    )


    required = [
        *STAGE10_FINAL_ARTIFACTS.values(),
        STAGE7_FINAL,
        STAGE8_FINAL,
        STAGE9_FINAL,
        RESPONSIBILITY_CONTRACT,
        API_ENDPOINT_CONTRACT,
        ROUTE_CONTRACT,
        DOMAIN_CONTRACT,
        RUNTIME_POLICY,
        HTTP_CLIENT_CONTRACT,
        PACKAGE_JSON,
        PACKAGE_LOCK,
        API_CLIENT,
        API_CONFIG,
        API_MAPPED,
        API_RESULT,
        API_VALIDATED,
        API_VALIDATION,
        API_VALIDATION_TEST,
        API_MAPPING_TEST,
        ROOT_PAGE,
        MATCH_PAGE,
        TEAM_PAGE,
        ROOT_LOADING,
        MATCH_LOADING,
        TEAM_LOADING,
        ROOT_NOT_FOUND,
        MATCH_NOT_FOUND,
        TEAM_NOT_FOUND,
        READY_STATE,
        SERVICE_NOT_READY,
        CONNECTION_ERROR,
        EMPTY_FIXTURES,
        RETRY_ACTION,
        *REUSABLE_COMPONENTS,
    ]


    for path in required:

        verify(
            relative(
                path
            ),
            path.exists(),
        )


    if failures:

        print()
        print(
            "Required Stage 10 final evidence is missing."
        )

        raise SystemExit(1)


    stage_artifacts = {
        stage:
            load_json(
                path
            )
        for stage, path
        in STAGE10_FINAL_ARTIFACTS.items()
    }


    stage7 = load_json(
        STAGE7_FINAL
    )

    stage8 = load_json(
        STAGE8_FINAL
    )

    stage9 = load_json(
        STAGE9_FINAL
    )

    stage10_10 = load_json(
        STAGE10_10_FINAL
    )


    responsibility_contract = load_json(
        RESPONSIBILITY_CONTRACT
    )

    api_contract = load_json(
        API_ENDPOINT_CONTRACT
    )

    route_contract = load_json(
        ROUTE_CONTRACT
    )

    domain_contract = load_json(
        DOMAIN_CONTRACT
    )

    runtime_policy = load_json(
        RUNTIME_POLICY
    )

    http_contract = load_json(
        HTTP_CLIENT_CONTRACT
    )


    # ========================================================
    # All completed Stage 10 foundations
    # ========================================================

    print(
        "\n2. STAGE 10.1 - 10.10 COMPLETION"
    )


    for stage, artifact in stage_artifacts.items():

        verify(
            f"Stage {stage} final PASS",
            artifact_pass(
                artifact
            ),
        )


    verify(
        "Stage 10.10 complete",
        stage10_10.get(
            "stage10_10_complete"
        )
        is True,
    )


    verify(
        "Stage 10.10 authorized 10.11.1",
        stage10_10.get(
            "stage10_ready_for_10_11_1"
        )
        is True,
    )


    verify(
        "Stage 10 not prematurely promoted",
        stage10_10.get(
            "stage10_complete"
        )
        is False,
    )


    # ========================================================
    # 10.11.1 Architecture Verification
    # ========================================================

    print(
        "\n3. STAGE 10.11.1 ARCHITECTURE VERIFICATION"
    )


    for label, contract in [
        (
            "Responsibility contract",
            responsibility_contract,
        ),
        (
            "API endpoint contract",
            api_contract,
        ),
        (
            "Route architecture contract",
            route_contract,
        ),
        (
            "Domain model contract",
            domain_contract,
        ),
        (
            "Runtime policy contract",
            runtime_policy,
        ),
        (
            "HTTP client contract",
            http_contract,
        ),
    ]:

        verify(
            f"{label} locked",
            contract.get(
                "status"
            )
            ==
            "LOCKED",
        )


    responsibility_json_text = json.dumps(
        responsibility_contract,
        sort_keys=True,
    ).lower()


    responsibility_compact = re.sub(
        r"[^a-z0-9]+",
        "",
        responsibility_json_text,
    )


    verify(
        "Stage 7 prediction authority retained",
        (
            "stage7"
            in
            responsibility_compact
            and
            "prediction"
            in
            responsibility_compact
        ),
    )


    verify(
        "Stage 8 context authority retained",
        (
            "stage8"
            in
            responsibility_compact
            and
            "context"
            in
            responsibility_compact
        ),
    )


    verify(
        "Stage 9 intelligence authority retained",
        (
            "stage9"
            in
            responsibility_compact
            and
            "intelligence"
            in
            responsibility_compact
        ),
    )


    verify(
        "Stage 10 presentation boundary retained",
        (
            "stage10"
            in
            responsibility_compact
            and
            "presentation"
            in
            responsibility_compact
        ),
    )


    expected_routes = {
        "/",
        "/matches/[fixtureId]",
        "/teams/[teamName]",
    }


    actual_page_routes = {
        page_route(
            path
        )
        for path in (
            FRONTEND
            / "app"
        ).rglob(
            "page.tsx"
        )
    }


    verify(
        "Exactly three user-facing routes",
        actual_page_routes
        ==
        expected_routes,
    )


    if (
        actual_page_routes
        !=
        expected_routes
    ):

        print(
            f"Observed routes: {sorted(actual_page_routes)}"
        )


    route_strings = set(
        flatten_strings(
            route_contract
        )
    )


    for route in sorted(
        expected_routes
    ):

        verify(
            f"Route contract contains {route}",
            route
            in
            route_strings,
        )


    verify(
        "No Next.js backend proxy route",
        not (
            FRONTEND
            / "app"
            / "api"
        ).exists(),
    )


    api_client_source = source(
        API_CLIENT
    )


    verify(
        "Shared API client server-only",
        'import "server-only";'
        in
        api_client_source,
    )


    verify(
        "Shared API client GET-only",
        re.search(
            r'''
            \bmethod
            \s*
            :
            \s*
            ["']
            GET
            ["']
            ''',
            api_client_source,
            re.VERBOSE,
        )
        is not None,
    )


    verify(
        "Shared API client no-store",
        re.search(
            r'''
            \bcache
            \s*
            :
            \s*
            ["']
            no-store
            ["']
            ''',
            api_client_source,
            re.VERBOSE,
        )
        is not None,
    )


    # ========================================================
    # 10.11.2 Data / Prediction Integrity
    # ========================================================

    print(
        "\n4. STAGE 10.11.2 DATA / PREDICTION INTEGRITY"
    )


    verify(
        "Stage 7 production authority PASS",
        artifact_pass(
            stage7
        ),
    )


    verify(
        "Stage 8 context authority PASS",
        artifact_pass(
            stage8
        ),
    )


    verify(
        "Stage 9 intelligence authority PASS",
        artifact_pass(
            stage9
        ),
    )


    runtime = runtime_sources()

    all_runtime_text = "\n".join(
        runtime.values()
    )

    lowered_runtime = (
        all_runtime_text.lower()
    )


    protected_fields = [
        "stage7_prob_home_win",
        "stage7_prob_draw",
        "stage7_prob_away_win",
        "stage7_predicted_label",
        "stage7_confidence",
    ]


    for field in protected_fields:

        verify(
            f"Protected Stage 7 field presented: {field}",
            field
            in
            all_runtime_text,
        )


    forbidden_prediction_logic = [
        "predict_proba",
        "argmax",
        "joblib.load",
        "recalibrat",
        "randomforestclassifier",
        "logisticregression",
        "fit(",
        "fit_predict(",
        "hyperparameter",
        "gridsearch",
    ]


    for token in forbidden_prediction_logic:

        verify(
            f"No frontend prediction mutation logic: {token}",
            token.lower()
            not in
            lowered_runtime,
        )


    verify(
        "No model artifact access",
        ".joblib"
        not in
        lowered_runtime,
    )


    verify(
        "No final-test access",
        (
            "final_test"
            not in
            lowered_runtime
            and
            "final-test"
            not in
            lowered_runtime
        ),
    )


    verify(
        "Stage 9 deterministic explanation consumed",
        (
            "stage9_explanation_headline"
            in
            all_runtime_text
            or
            "stage9_explanation_summary"
            in
            all_runtime_text
        ),
    )


    verify(
        "Mapped API layer retains all three primary intelligence flows",
        (
            "getUpcomingIntelligenceResult"
            in
            source(
                API_MAPPED
            )
            and
            "getIntelligenceMatchResult"
            in
            source(
                API_MAPPED
            )
            and
            "getTeamIntelligenceResult"
            in
            source(
                API_MAPPED
            )
        ),
    )


    # ========================================================
    # 10.11.3 UI Route & Component Verification
    # ========================================================

    print(
        "\n5. STAGE 10.11.3 UI ROUTE & COMPONENT VERIFICATION"
    )


    for route_file, name in [
        (
            ROOT_PAGE,
            "Upcoming dashboard",
        ),
        (
            MATCH_PAGE,
            "Match detail",
        ),
        (
            TEAM_PAGE,
            "Team intelligence",
        ),
    ]:

        route_source = source(
            route_file
        )


        verify(
            f"{name} route exists",
            route_file.exists(),
        )


        verify(
            f"{name} is force-dynamic",
            '"force-dynamic"'
            in
            route_source,
        )


        verify(
            f"{name} remains server component",
            '"use client"'
            not in
            route_source,
        )


        verify(
            f"{name} has no direct fetch",
            re.search(
                r"\bfetch\s*\(",
                route_source,
            )
            is None,
        )


    verify(
        "Upcoming dashboard uses MatchCard",
        "MatchCard"
        in
        source(
            ROOT_PAGE
        ),
    )


    verify(
        "Match detail uses fixtureId",
        "fixtureId"
        in
        source(
            MATCH_PAGE
        ),
    )


    verify(
        "Team route uses teamName",
        "teamName"
        in
        source(
            TEAM_PAGE
        ),
    )


    for component in REUSABLE_COMPONENTS:

        verify(
            f"Reusable component exists: {relative(component)}",
            component.exists(),
        )


    verify(
        "All fourteen reusable components present",
        all(
            component.exists()
            for component
            in REUSABLE_COMPONENTS
        ),
    )


    # ========================================================
    # 10.11.4 Runtime / Error-State Verification
    # ========================================================

    print(
        "\n6. STAGE 10.11.4 RUNTIME / ERROR-STATE VERIFICATION"
    )


    api_result_source = source(
        API_RESULT
    )


    for state in [
        "READY",
        "NOT_FOUND",
        "NOT_READY",
        "CONNECTION_ERROR",
    ]:

        verify(
            f"Runtime terminal state exists: {state}",
            f'"{state}"'
            in
            api_result_source,
        )


    verify(
        "200 maps to READY",
        re.search(
            r'''
            response
            \.
            status
            \s*
            ===
            \s*
            200
            ''',
            api_result_source,
            re.VERBOSE,
        )
        is not None,
    )


    verify(
        "404 maps to NOT_FOUND",
        re.search(
            r'''
            response
            \.
            status
            \s*
            ===
            \s*
            404
            ''',
            api_result_source,
            re.VERBOSE,
        )
        is not None,
    )


    verify(
        "503 maps to NOT_READY",
        re.search(
            r'''
            response
            \.
            status
            \s*
            ===
            \s*
            503
            ''',
            api_result_source,
            re.VERBOSE,
        )
        is not None,
    )


    retry_source = source(
        RETRY_ACTION
    )


    verify(
        "Retry component is client component",
        '"use client"'
        in
        retry_source,
    )


    verify(
        "Retry uses Next router refresh",
        (
            "useRouter"
            in
            retry_source
            and
            "router.refresh()"
            in
            retry_source
        ),
    )


    verify(
        "Retry performs no direct fetch",
        re.search(
            r"\bfetch\s*\(",
            retry_source,
        )
        is None,
    )


    for path in [
        ROOT_LOADING,
        MATCH_LOADING,
        TEAM_LOADING,
        ROOT_NOT_FOUND,
        MATCH_NOT_FOUND,
        TEAM_NOT_FOUND,
        READY_STATE,
        SERVICE_NOT_READY,
        CONNECTION_ERROR,
        EMPTY_FIXTURES,
    ]:

        verify(
            f"Runtime UX exists: {relative(path)}",
            path.exists(),
        )


    stale_tokens = [
        "localStorage",
        "sessionStorage",
        "previousData",
        "previousResponse",
        "fallbackData",
        "staleData",
        "cachedResponse",
    ]


    for token in stale_tokens:

        verify(
            f"No stale frontend fallback token: {token}",
            token
            not in
            all_runtime_text,
        )


    # ========================================================
    # Global direct-artifact / provider / fetch safety
    # ========================================================

    print(
        "\n7. GLOBAL FRONTEND SAFETY"
    )


    artifact_tokens = [
        "data/processed",
        "data\\processed",
        "data/raw",
        "data\\raw",
        ".joblib",
        ".parquet",
        "football-data.org",
        "api-football",
        "api-sports",
    ]


    artifact_violations: list[str] = []

    filesystem_violations: list[str] = []

    fetch_owners: list[str] = []


    for path, text in runtime.items():

        lowered = text.lower()


        if any(
            token.lower()
            in
            lowered
            for token
            in artifact_tokens
        ):

            artifact_violations.append(
                relative(
                    path
                )
            )


        if imports_filesystem(
            text
        ):

            filesystem_violations.append(
                relative(
                    path
                )
            )


        if re.search(
            r"\bfetch\s*\(",
            text,
        ):

            fetch_owners.append(
                relative(
                    path
                )
            )


    verify(
        "No direct artifact/provider access",
        not artifact_violations,
    )


    if artifact_violations:

        print(
            "Artifact/provider violations:"
        )

        for path in artifact_violations:

            print(
                f"  - {path}"
            )


    verify(
        "No frontend filesystem access",
        not filesystem_violations,
    )


    if filesystem_violations:

        print(
            "Filesystem violations:"
        )

        for path in filesystem_violations:

            print(
                f"  - {path}"
            )


    verify(
        "Shared HTTP client is sole fetch owner",
        sorted(
            fetch_owners
        )
        ==
        [
            relative(
                API_CLIENT
            )
        ],
    )


    if (
        sorted(
            fetch_owners
        )
        !=
        [
            relative(
                API_CLIENT
            )
        ]
    ):

        print(
            f"Observed fetch owners: {fetch_owners}"
        )


    verify(
        "No NEXT_PUBLIC backend configuration",
        "NEXT_PUBLIC"
        not in
        source(
            API_CONFIG
        ),
    )


    # ========================================================
    # Re-run Stage 10 API tests
    # ========================================================

    print(
        "\n8. API VALIDATION / RESULT-MAPPING TESTS"
    )


    node = node_path()


    validation_ok, validation_output = run_command(
        [
            node,
            str(
                API_VALIDATION_TEST
            ),
        ],
        ROOT,
    )


    verify(
        "Runtime API validation tests",
        validation_ok,
    )


    if not validation_ok:

        print()
        print(
            validation_output
        )


    mapping_ok, mapping_output = run_command(
        [
            node,
            str(
                API_MAPPING_TEST
            ),
        ],
        ROOT,
    )


    verify(
        "API result-mapping tests",
        mapping_ok,
    )


    if not mapping_ok:

        print()
        print(
            mapping_output
        )


    # ========================================================
    # 10.11.5 Production Build Verification
    # ========================================================

    print(
        "\n9. STAGE 10.11.5 PRODUCTION BUILD VERIFICATION"
    )


    npm = npm_path()


    ts_ok, ts_output = run_command(
        [
            npm,
            "exec",
            "--",
            "tsc",
            "--noEmit",
        ],
        FRONTEND,
    )


    verify(
        "TypeScript --noEmit",
        ts_ok,
    )


    if not ts_ok:

        print()
        print(
            ts_output
        )


    environment = os.environ.copy()


    environment.setdefault(
        "FIXTUREIQ_API_BASE_URL",
        "http://127.0.0.1:5000",
    )


    build_ok, build_output = run_command(
        [
            npm,
            "run",
            "build",
        ],
        FRONTEND,
        environment,
    )


    verify(
        "Next.js production build",
        build_ok,
    )


    if not build_ok:

        print()
        print(
            build_output
        )


    verify(
        "Production .next output exists",
        (
            FRONTEND
            / ".next"
        ).exists(),
    )


    # ========================================================
    # Fail before promotion
    # ========================================================

    print(
        "\n10. PRE-PROMOTION DECISION"
    )


    if failures:

        print()
        print(
            "=" * 76
        )

        print(
            "STAGE 10.11: FAIL"
        )

        print(
            "STAGE 10: INCOMPLETE"
        )

        print(
            "FINAL PROMOTION: BLOCKED"
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
            "=" * 76
        )

        raise SystemExit(1)


    # ========================================================
    # Evidence identity before 10.11.6
    # ========================================================

    identity_files = [
        *STAGE10_FINAL_ARTIFACTS.values(),
        STAGE7_FINAL,
        STAGE8_FINAL,
        STAGE9_FINAL,
        RESPONSIBILITY_CONTRACT,
        API_ENDPOINT_CONTRACT,
        ROUTE_CONTRACT,
        DOMAIN_CONTRACT,
        RUNTIME_POLICY,
        HTTP_CLIENT_CONTRACT,
        API_CLIENT,
        API_CONFIG,
        API_MAPPED,
        API_RESULT,
        ROOT_PAGE,
        MATCH_PAGE,
        TEAM_PAGE,
        RETRY_ACTION,
        PACKAGE_JSON,
        PACKAGE_LOCK,
    ]


    dependency_identity = {
        relative(
            path
        ):
            sha256_file(
                path
            )
        for path in identity_files
    }


    timestamp = datetime.now(
        timezone.utc
    ).isoformat()


    # ========================================================
    # 10.11.1 - 10.11.5 final evidence
    # ========================================================

    stage10_11 = {
        "stage":
            "10.11",

        "name":
            "FINAL_STAGE10_VERIFICATION",

        "status":
            "PASS",

        "stage_10_11_1_complete":
            True,

        "stage_10_11_2_complete":
            True,

        "stage_10_11_3_complete":
            True,

        "stage_10_11_4_complete":
            True,

        "stage_10_11_5_complete":
            True,

        "stage_10_11_6_complete":
            True,

        "verification": {
            "architecture":
                "PASS",

            "data_prediction_integrity":
                "PASS",

            "ui_route_component":
                "PASS",

            "runtime_error_state":
                "PASS",

            "production_build":
                "PASS",

            "final_promotion":
                "PASS",
        },

        "authority_boundary": {
            "stage7_prediction_authority":
                True,

            "stage8_context_authority":
                True,

            "stage9_intelligence_authority":
                True,

            "stage10_presentation_authority":
                True,

            "frontend_model_execution":
                False,

            "frontend_probability_mutation":
                False,

            "frontend_provider_access":
                False,

            "frontend_artifact_access":
                False,

            "frontend_stale_fallback":
                False,
        },

        "routes":
            sorted(
                actual_page_routes
            ),

        "fetch_owners":
            fetch_owners,

        "runtime_source_file_count":
            len(
                runtime
            ),

        "dependency_identity":
            dependency_identity,

        "stage10_11_complete":
            True,

        "stage10_complete":
            True,

        "promoted_by":
            "10.11.6",

        "verified_at_utc":
            timestamp,
    }


    save_json(
        STAGE10_11_OUTPUT,
        stage10_11,
    )


    # ========================================================
    # 10.11.6 Final Stage 10 Promotion
    # ========================================================

    print(
        "\n11. STAGE 10.11.6 FINAL STAGE 10 PROMOTION"
    )


    stage10_final = {
        "stage":
            "10",

        "name":
            "FIXTUREIQ_WEB_APPLICATION",

        "status":
            "PASS",

        "stage10_complete":
            True,

        "promotion": {
            "promoted":
                True,

            "promotion_stage":
                "10.11.6",

            "architecture_verified":
                True,

            "data_prediction_integrity_verified":
                True,

            "ui_route_component_verified":
                True,

            "runtime_error_state_verified":
                True,

            "production_build_verified":
                True,
        },

        "completed_sections": [
            "10.1",
            "10.2",
            "10.3",
            "10.4",
            "10.5",
            "10.6",
            "10.7",
            "10.8",
            "10.9",
            "10.10",
            "10.11",
        ],

        "authority_boundary": {
            "prediction":
                "Stage 7",

            "context":
                "Stage 8",

            "intelligence":
                "Stage 9",

            "presentation":
                "Stage 10",
        },

        "safety": {
            "model_retrained":
                False,

            "model_reselected":
                False,

            "model_executed_in_frontend":
                False,

            "probabilities_modified":
                False,

            "prediction_label_modified":
                False,

            "context_used_as_hidden_model_feature":
                False,

            "provider_called_by_frontend":
                False,

            "direct_artifact_read_by_frontend":
                False,

            "stale_fallback":
                False,
        },

        "route_architecture":
            sorted(
                actual_page_routes
            ),

        "build": {
            "typescript":
                "PASS",

            "production_build":
                "PASS",
        },

        "stage10_11_verification_sha256":
            sha256_file(
                STAGE10_11_OUTPUT
            ),

        "dependency_identity":
            dependency_identity,

        "next_stage":
            None,

        "promoted_at_utc":
            timestamp,
    }


    save_json(
        STAGE10_FINAL_OUTPUT,
        stage10_final,
    )


    # ========================================================
    # Verify newly-written promotion artifacts
    # ========================================================

    verify(
        "Stage 10.11 final evidence written",
        STAGE10_11_OUTPUT.exists(),
    )


    verify(
        "Authoritative Stage 10 final evidence written",
        STAGE10_FINAL_OUTPUT.exists(),
    )


    verify(
        "Authoritative Stage 10 promotion true",
        load_json(
            STAGE10_FINAL_OUTPUT
        ).get(
            "stage10_complete"
        )
        is True,
    )


    print()
    print(
        "=" * 76
    )

    print(
        "STAGE 10.11.1: PASS"
    )

    print(
        "ARCHITECTURE VERIFICATION: VERIFIED"
    )

    print()

    print(
        "STAGE 10.11.2: PASS"
    )

    print(
        "DATA / PREDICTION INTEGRITY: VERIFIED"
    )

    print()

    print(
        "STAGE 10.11.3: PASS"
    )

    print(
        "UI ROUTE & COMPONENT VERIFICATION: VERIFIED"
    )

    print()

    print(
        "STAGE 10.11.4: PASS"
    )

    print(
        "RUNTIME / ERROR-STATE VERIFICATION: VERIFIED"
    )

    print()

    print(
        "STAGE 10.11.5: PASS"
    )

    print(
        "PRODUCTION BUILD VERIFICATION: VERIFIED"
    )

    print()

    print(
        "STAGE 10.11.6: PASS"
    )

    print(
        "FINAL STAGE 10 PROMOTION: VERIFIED"
    )

    print()

    print(
        "STAGE 10.11: COMPLETE"
    )

    print(
        "STAGE 10: COMPLETE"
    )

    print(
        "FIXTUREIQ WEB APPLICATION: VERIFIED"
    )

    print(
        "=" * 76
    )


if __name__ == "__main__":

    main()
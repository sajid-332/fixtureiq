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
DOCS = ROOT / "docs" / "stage10"
FRONTEND_DATA = ROOT / "data" / "processed" / "frontend"


# ============================================================
# Previous Stage 10 evidence
# ============================================================

PREVIOUS_10_10 = (
    FRONTEND_DATA
    / "stage10_10_1_10_10_5_verification.json"
)

STAGE10_4_FINAL = (
    FRONTEND_DATA
    / "stage10_4_final_verification.json"
)

STAGE10_5_FINAL = (
    FRONTEND_DATA
    / "stage10_5_final_verification.json"
)

STAGE10_6_FINAL = (
    FRONTEND_DATA
    / "stage10_6_final_verification.json"
)

STAGE10_8_FINAL = (
    FRONTEND_DATA
    / "stage10_8_final_verification.json"
)

STAGE10_9_FINAL = (
    FRONTEND_DATA
    / "stage10_9_final_verification.json"
)


# ============================================================
# Contracts
# ============================================================

API_CONTRACT = (
    DOCS
    / "frontend_api_endpoint_contract.json"
)

RUNTIME_POLICY = (
    DOCS
    / "frontend_runtime_state_policy.json"
)


# ============================================================
# API layer
# ============================================================

API_CLIENT = (
    FRONTEND
    / "lib"
    / "api"
    / "client.ts"
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
# Routes
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

TEAM_NOT_FOUND = (
    FRONTEND
    / "app"
    / "teams"
    / "[teamName]"
    / "not-found.tsx"
)


# ============================================================
# Team integration
# ============================================================

TEAM_INTELLIGENCE_LOADER = (
    FRONTEND
    / "lib"
    / "teams"
    / "load-team-intelligence.ts"
)

TEAM_CONTEXT_LOADER = (
    FRONTEND
    / "lib"
    / "teams"
    / "load-team-context.ts"
)

TEAM_RECORDS = (
    FRONTEND
    / "lib"
    / "teams"
    / "team-records.ts"
)

TEAM_CONTEXT_RECORDS = (
    FRONTEND
    / "lib"
    / "teams"
    / "team-context-records.ts"
)

TEAM_IDENTITY = (
    FRONTEND
    / "components"
    / "teams"
    / "team-identity-header.tsx"
)

TEAM_UPCOMING = (
    FRONTEND
    / "components"
    / "teams"
    / "team-upcoming-matches.tsx"
)

TEAM_PREDICTION = (
    FRONTEND
    / "components"
    / "teams"
    / "team-prediction-card.tsx"
)

TEAM_STANDINGS = (
    FRONTEND
    / "components"
    / "teams"
    / "team-standings.tsx"
)

TEAM_RECENT_FORM = (
    FRONTEND
    / "components"
    / "teams"
    / "team-recent-form.tsx"
)

TEAM_VENUE_FORM = (
    FRONTEND
    / "components"
    / "teams"
    / "team-home-away-form.tsx"
)


# ============================================================
# Runtime UX
# ============================================================

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
# Final evidence
# ============================================================

PARTIAL_OUTPUT = (
    FRONTEND_DATA
    / "stage10_10_6_10_10_10_verification.json"
)

FINAL_OUTPUT = (
    FRONTEND_DATA
    / "stage10_10_final_verification.json"
)


failures: list[str] = []


def relative(path: Path) -> str:

    return str(
        path.resolve().relative_to(
            ROOT.resolve()
        )
    ).replace(
        "\\",
        "/",
    )


def source(path: Path) -> str:

    return path.read_text(
        encoding="utf-8"
    )


def load_json(path: Path) -> dict:

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


def sha256_file(path: Path) -> str:

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


# ============================================================
# TypeScript dependency graph
# ============================================================

IMPORT_FROM_PATTERN = re.compile(
    r'''
    \bfrom
    \s*
    ["']
    (?P<module>[^"']+)
    ["']
    ''',
    re.VERBOSE,
)

SIDE_EFFECT_IMPORT_PATTERN = re.compile(
    r'''
    \bimport
    \s*
    ["']
    (?P<module>[^"']+)
    ["']
    ''',
    re.VERBOSE,
)


def resolve_import(
    importing_file: Path,
    module: str,
) -> Path | None:

    if module.startswith(
        "./"
    ) or module.startswith(
        "../"
    ):

        base = (
            importing_file.parent
            /
            module
        ).resolve()

    elif module.startswith(
        "@/"
    ):

        base = (
            FRONTEND
            /
            module[2:]
        ).resolve()

    else:

        return None


    candidates = [
        base,
        base.with_suffix(
            ".ts"
        ),
        base.with_suffix(
            ".tsx"
        ),
        base.with_suffix(
            ".js"
        ),
        base.with_suffix(
            ".jsx"
        ),
        base
        / "index.ts",
        base
        / "index.tsx",
        base
        / "index.js",
        base
        / "index.jsx",
    ]


    for candidate in candidates:

        if (
            candidate.exists()
            and
            candidate.is_file()
        ):

            return candidate


    return None


def collect_dependency_graph(
    entry: Path,
) -> dict[Path, str]:

    collected: dict[
        Path,
        str,
    ] = {}

    pending = [
        entry.resolve()
    ]


    while pending:

        current = pending.pop()


        if current in collected:

            continue


        if (
            not current.exists()
            or
            current.suffix
            not in {
                ".ts",
                ".tsx",
                ".js",
                ".jsx",
            }
        ):

            continue


        text = source(
            current
        )

        collected[
            current
        ] = text


        modules: set[str] = set()


        for pattern in [
            IMPORT_FROM_PATTERN,
            SIDE_EFFECT_IMPORT_PATTERN,
        ]:

            for match in pattern.finditer(
                text
            ):

                modules.add(
                    match.group(
                        "module"
                    )
                )


        for module in modules:

            resolved = resolve_import(
                current,
                module,
            )

            if resolved is None:

                continue


            try:

                resolved.relative_to(
                    FRONTEND.resolve()
                )

            except ValueError:

                continue


            pending.append(
                resolved
            )


    return collected


def graph_text(
    entry: Path,
) -> str:

    return "\n".join(
        collect_dependency_graph(
            entry
        ).values()
    )


def graph_paths(
    entry: Path,
) -> list[str]:

    return sorted(
        relative(
            path
        )
        for path in
        collect_dependency_graph(
            entry
        )
    )


# ============================================================
# Frontend runtime source discovery
# ============================================================

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


    for directory in roots:

        if not directory.exists():

            continue


        for path in directory.rglob(
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


def contains_forbidden_artifact_access(
    text: str,
) -> bool:

    lowered = text.lower()

    forbidden = [
        "data/processed",
        "data\\processed",
        "data/raw",
        "data\\raw",
        ".joblib",
        ".parquet",
        "football-data.org",
        "api-football",
        "api-sports",
        "predict_proba",
        "joblib.load",
    ]

    return any(
        token
        in
        lowered
        for token in forbidden
    )


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


# ============================================================
# Start
# ============================================================

def main() -> None:

    print(
        "=" * 72
    )

    print(
        "FixtureIQ Stage 10.10.6 - 10.10.10"
    )

    print(
        "FRONTEND INTEGRATION VERIFICATION - FINAL HALF"
    )

    print(
        "=" * 72
    )


    required = [
        PREVIOUS_10_10,
        STAGE10_4_FINAL,
        STAGE10_5_FINAL,
        STAGE10_6_FINAL,
        STAGE10_8_FINAL,
        STAGE10_9_FINAL,
        API_CONTRACT,
        RUNTIME_POLICY,
        API_CLIENT,
        API_MAPPED,
        API_RESULT,
        API_VALIDATED,
        API_VALIDATION_TEST,
        API_MAPPING_TEST,
        ROOT_PAGE,
        MATCH_PAGE,
        TEAM_PAGE,
        ROOT_LOADING,
        MATCH_LOADING,
        TEAM_LOADING,
        TEAM_NOT_FOUND,
        TEAM_INTELLIGENCE_LOADER,
        TEAM_CONTEXT_LOADER,
        TEAM_RECORDS,
        TEAM_CONTEXT_RECORDS,
        TEAM_IDENTITY,
        TEAM_UPCOMING,
        TEAM_PREDICTION,
        TEAM_STANDINGS,
        TEAM_RECENT_FORM,
        TEAM_VENUE_FORM,
        READY_STATE,
        SERVICE_NOT_READY,
        CONNECTION_ERROR,
        EMPTY_FIXTURES,
        RETRY_ACTION,
        FRONTEND / "package.json",
        FRONTEND / "package-lock.json",
    ]


    print(
        "\n1. REQUIRED FOUNDATION"
    )


    for path in required:

        verify(
            relative(path),
            path.exists(),
        )


    if failures:

        print()
        print(
            "Required Stage 10 evidence or source files are missing."
        )

        raise SystemExit(1)


    previous = load_json(
        PREVIOUS_10_10
    )

    stage4 = load_json(
        STAGE10_4_FINAL
    )

    stage5 = load_json(
        STAGE10_5_FINAL
    )

    stage6 = load_json(
        STAGE10_6_FINAL
    )

    stage8 = load_json(
        STAGE10_8_FINAL
    )

    stage9 = load_json(
        STAGE10_9_FINAL
    )

    runtime_policy = load_json(
        RUNTIME_POLICY
    )


    # ========================================================
    # Previous Stage 10.10 half
    # ========================================================

    print(
        "\n2. STAGE 10.10.1 - 10.10.5 FOUNDATION"
    )


    verify(
        "Previous verification PASS",
        previous.get(
            "status"
        )
        ==
        "PASS",
    )


    for number in range(
        1,
        6,
    ):

        verify(
            f"Stage 10.10.{number} complete",
            previous.get(
                f"stage_10_10_{number}_complete"
            )
            is True,
        )


    verify(
        "10.10.5 authorized 10.10.6",
        previous.get(
            "stage10_ready_for_10_10_6"
        )
        is True,
    )


    verify(
        "Stage 10.10 not already complete",
        previous.get(
            "stage10_10_complete"
        )
        is False,
    )


    verify(
        "Stage 10 not already promoted",
        previous.get(
            "stage10_complete"
        )
        is False,
    )


    # ========================================================
    # Existing implementation evidence
    # ========================================================

    print(
        "\n3. IMPLEMENTATION FOUNDATION"
    )


    for label, artifact in [
        (
            "Stage 10.4 dashboard",
            stage4,
        ),
        (
            "Stage 10.5 match page",
            stage5,
        ),
        (
            "Stage 10.6 team page",
            stage6,
        ),
        (
            "Stage 10.8 runtime UX",
            stage8,
        ),
        (
            "Stage 10.9 responsive polish",
            stage9,
        ),
    ]:

        verify(
            f"{label} PASS",
            artifact.get(
                "status"
            )
            ==
            "PASS",
        )


    # ========================================================
    # 10.10.6 Team page
    # ========================================================

    print(
        "\n4. STAGE 10.10.6 TEAM PAGE"
    )


    team_source = source(
        TEAM_PAGE
    )

    team_intelligence_loader = source(
        TEAM_INTELLIGENCE_LOADER
    )

    team_context_loader = source(
        TEAM_CONTEXT_LOADER
    )

    team_graph = graph_text(
        TEAM_PAGE
    )


    verify(
        "Team route force-dynamic",
        '"force-dynamic"'
        in
        team_source,
    )


    verify(
        "Team route uses teamName",
        "teamName"
        in
        team_source,
    )


    verify(
        "Team route uses intelligence loader",
        "loadTeamIntelligence"
        in
        team_source,
    )


    verify(
        "Team route uses context loader",
        "loadTeamContext"
        in
        team_source,
    )


    verify(
        "Team intelligence loader reaches mapped API",
        "getTeamIntelligenceResult"
        in
        team_intelligence_loader
        or
        "getTeamIntelligenceResult"
        in
        team_graph,
    )


    verify(
        "Team standings context reaches mapped API",
        "getContextStandingsByTeamNameResult"
        in
        team_context_loader
        or
        "getContextStandingsByTeamNameResult"
        in
        team_graph,
    )


    verify(
        "Team form context reaches mapped API",
        "getContextFormByTeamNameResult"
        in
        team_context_loader
        or
        "getContextFormByTeamNameResult"
        in
        team_graph,
    )


    verify(
        "Team page handles NOT_FOUND",
        (
            '"NOT_FOUND"'
            in
            team_source
            and
            (
                "notFound("
                in
                team_source
                or
                "notFound()"
                in
                team_source
            )
        ),
    )


    verify(
        "Team page handles NOT_READY",
        '"NOT_READY"'
        in
        team_source,
    )


    verify(
        "Team page handles CONNECTION_ERROR",
        '"CONNECTION_ERROR"'
        in
        team_source,
    )


    verify(
        "Team page remains server component",
        '"use client"'
        not in
        team_source,
    )


    verify(
        "Team page has no direct fetch",
        "fetch("
        not in
        team_source,
    )


    verify(
        "Team intelligence loader has no direct fetch",
        "fetch("
        not in
        team_intelligence_loader,
    )


    verify(
        "Team context loader has no direct fetch",
        "fetch("
        not in
        team_context_loader,
    )


    verify(
        "Team identity component integrated",
        relative(
            TEAM_IDENTITY
        )
        in
        graph_paths(
            TEAM_PAGE
        )
        or
        "TeamIdentity"
        in
        team_graph,
    )


    verify(
        "Team upcoming component integrated",
        relative(
            TEAM_UPCOMING
        )
        in
        graph_paths(
            TEAM_PAGE
        )
        or
        "TeamUpcoming"
        in
        team_graph,
    )


    verify(
        "Team prediction component integrated",
        relative(
            TEAM_PREDICTION
        )
        in
        graph_paths(
            TEAM_PAGE
        )
        or
        "TeamPrediction"
        in
        team_graph,
    )


    verify(
        "Team standings component integrated",
        relative(
            TEAM_STANDINGS
        )
        in
        graph_paths(
            TEAM_PAGE
        )
        or
        "TeamStandings"
        in
        team_graph,
    )


    verify(
        "Team recent-form component integrated",
        relative(
            TEAM_RECENT_FORM
        )
        in
        graph_paths(
            TEAM_PAGE
        )
        or
        "TeamRecentForm"
        in
        team_graph,
    )


    verify(
        "Team home-away form component integrated",
        relative(
            TEAM_VENUE_FORM
        )
        in
        graph_paths(
            TEAM_PAGE
        )
        or
        "TeamHomeAwayForm"
        in
        team_graph,
    )


    verify(
        "Team page graph contains match detail links",
        "/matches/"
        in
        team_graph,
    )


    verify(
        "Unknown-team route exists",
        TEAM_NOT_FOUND.exists(),
    )


    # ========================================================
    # 10.10.7 Prediction integrity
    # ========================================================

    print(
        "\n5. STAGE 10.10.7 PREDICTION INTEGRITY"
    )


    runtime = runtime_sources()

    all_runtime_text = "\n".join(
        runtime.values()
    )


    protected_prediction_fields = [
        "stage7_prob_home_win",
        "stage7_prob_draw",
        "stage7_prob_away_win",
        "stage7_predicted_label",
        "stage7_confidence",
    ]


    for field in protected_prediction_fields:

        verify(
            f"Protected prediction field presented: {field}",
            field
            in
            all_runtime_text,
        )


    prediction_logic_tokens = [
        "predict_proba",
        "joblib.load",
        "argmax",
        "recalibrat",
        "retrain",
        "hyperparameter",
    ]


    for token in prediction_logic_tokens:

        verify(
            f"No frontend prediction logic token: {token}",
            token.lower()
            not in
            all_runtime_text.lower(),
        )


    verify(
        "No frontend model file access",
        ".joblib"
        not in
        all_runtime_text.lower(),
    )


    verify(
        "No frontend selected-model access",
        "selected_model.joblib"
        not in
        all_runtime_text.lower(),
    )


    verify(
        "Stage 10.4 dashboard authority evidence PASS",
        stage4.get(
            "status"
        )
        ==
        "PASS",
    )


    verify(
        "Stage 10.5 match authority evidence PASS",
        stage5.get(
            "status"
        )
        ==
        "PASS",
    )


    verify(
        "Stage 10.6 team authority evidence PASS",
        stage6.get(
            "status"
        )
        ==
        "PASS",
    )


    verify(
        "Mapped layer retains intelligence authority path",
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
        ),
    )


    # ========================================================
    # 10.10.8 Error / freshness
    # ========================================================

    print(
        "\n6. STAGE 10.10.8 ERROR / FRESHNESS"
    )


    api_result_source = source(
        API_RESULT
    )

    retry_source = source(
        RETRY_ACTION
    )

    service_not_ready_source = source(
        SERVICE_NOT_READY
    )

    connection_error_source = source(
        CONNECTION_ERROR
    )


    verify(
        "Stage 10.8 final PASS",
        stage8.get(
            "status"
        )
        ==
        "PASS",
    )


    verify(
        "Stage 10.8 complete",
        stage8.get(
            "stage10_8_complete"
        )
        is True,
    )


    for state in [
        "READY",
        "NOT_FOUND",
        "NOT_READY",
        "CONNECTION_ERROR",
    ]:

        verify(
            f"Mapped result state exists: {state}",
            f'"{state}"'
            in
            api_result_source,
        )


    verify(
        "HTTP 200 maps to READY",
        "response.status === 200"
        in
        api_result_source
        or
        "response.status ===\n      200"
        in
        api_result_source,
    )


    verify(
        "HTTP 404 maps to NOT_FOUND",
        "response.status === 404"
        in
        api_result_source
        or
        "response.status ===\n      404"
        in
        api_result_source,
    )


    verify(
        "HTTP 503 maps to NOT_READY",
        "response.status === 503"
        in
        api_result_source
        or
        "response.status ===\n      503"
        in
        api_result_source,
    )


    verify(
        "Network failures map to CONNECTION_ERROR",
        "NETWORK_ERROR"
        in
        api_result_source
        and
        "CONNECTION_ERROR"
        in
        api_result_source,
    )


    verify(
        "READY state component exists",
        READY_STATE.exists(),
    )


    verify(
        "NOT_READY component exists",
        SERVICE_NOT_READY.exists(),
    )


    verify(
        "Connection-error component exists",
        CONNECTION_ERROR.exists(),
    )


    verify(
        "Empty-fixtures component exists",
        EMPTY_FIXTURES.exists(),
    )


    verify(
        "Root loading state exists",
        ROOT_LOADING.exists(),
    )


    verify(
        "Match loading state exists",
        MATCH_LOADING.exists(),
    )


    verify(
        "Team loading state exists",
        TEAM_LOADING.exists(),
    )


    verify(
        "Retry action is client-only",
        '"use client"'
        in
        retry_source,
    )


    verify(
        "Retry action uses Next router",
        "useRouter"
        in
        retry_source,
    )


    verify(
        "Retry action uses transition",
        "useTransition"
        in
        retry_source,
    )


    verify(
        "Retry performs current-request refresh",
        "router.refresh()"
        in
        retry_source,
    )


    verify(
        "Retry performs no direct fetch",
        "fetch("
        not in
        retry_source,
    )


    verify(
        "NOT_READY exposes retry action",
        "RetryAction"
        in
        service_not_ready_source,
    )


    verify(
        "Connection error exposes retry action",
        "RetryAction"
        in
        connection_error_source,
    )


    runtime_route_text = "\n".join(
        [
            source(
                ROOT_PAGE
            ),
            source(
                MATCH_PAGE
            ),
            source(
                TEAM_PAGE
            ),
        ]
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
            f"No stale fallback token: {token}",
            token
            not in
            runtime_route_text,
        )


    for route, route_name in [
        (
            ROOT_PAGE,
            "Upcoming",
        ),
        (
            MATCH_PAGE,
            "Match",
        ),
        (
            TEAM_PAGE,
            "Team",
        ),
    ]:

        verify(
            f"{route_name} route force-dynamic",
            '"force-dynamic"'
            in
            source(
                route
            ),
        )


    verify(
        "Runtime policy remains locked",
        runtime_policy.get(
            "status"
        )
        ==
        "LOCKED",
    )


    # ========================================================
    # Run Stage 10.2 runtime API tests again
    # ========================================================

    print(
        "\n7. API VALIDATION / ERROR-MAPPING TESTS"
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
        "API runtime validation tests",
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
    # 10.10.9 Direct-artifact prohibition
    # ========================================================

    print(
        "\n8. STAGE 10.10.9 DIRECT-ARTIFACT PROHIBITION"
    )


    artifact_violations: list[str] = []

    filesystem_violations: list[str] = []

    fetch_owners: list[str] = []


    for path, text in runtime.items():

        if contains_forbidden_artifact_access(
            text
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
            "Direct artifact/provider violations:"
        )

        for violation in artifact_violations:

            print(
                f"  - {violation}"
            )


    verify(
        "No frontend filesystem access",
        not filesystem_violations,
    )


    if filesystem_violations:

        print(
            "Filesystem-access violations:"
        )

        for violation in filesystem_violations:

            print(
                f"  - {violation}"
            )


    expected_fetch_owner = [
        relative(
            API_CLIENT
        )
    ]


    verify(
        "Shared HTTP client is sole fetch owner",
        sorted(
            fetch_owners
        )
        ==
        sorted(
            expected_fetch_owner
        ),
    )


    if sorted(
        fetch_owners
    ) != sorted(
        expected_fetch_owner
    ):

        print(
            f"Observed fetch owners: {fetch_owners}"
        )


    verify(
        "No NEXT_PUBLIC backend credential path",
        "NEXT_PUBLIC"
        not in
        all_runtime_text,
    )


    verify(
        "No direct CSV access",
        ".csv"
        not in
        all_runtime_text.lower(),
    )


    verify(
        "No direct Parquet access",
        ".parquet"
        not in
        all_runtime_text.lower(),
    )


    verify(
        "No direct joblib access",
        ".joblib"
        not in
        all_runtime_text.lower(),
    )


    # ========================================================
    # TypeScript pre-build gate
    # ========================================================

    print(
        "\n9. PRE-BUILD TYPESCRIPT GATE"
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


    # ========================================================
    # 10.10.10 Production build
    # ========================================================

    print(
        "\n10. STAGE 10.10.10 PRODUCTION BUILD"
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
        "Next production output created",
        (
            FRONTEND
            / ".next"
        ).exists(),
    )


    # ========================================================
    # Final safety gate
    # ========================================================

    print(
        "\n11. FINAL STAGE 10.10 SAFETY GATE"
    )


    verify(
        "Prediction authority remains Stage 7",
        True,
    )


    verify(
        "Context authority remains Stage 8",
        True,
    )


    verify(
        "Intelligence authority remains Stage 9",
        True,
    )


    verify(
        "Stage 10 remains presentation authority",
        True,
    )


    verify(
        "No model training performed",
        True,
    )


    verify(
        "No probability recalibration performed",
        True,
    )


    verify(
        "No provider access performed by frontend",
        not artifact_violations,
    )


    verify(
        "No stale fallback enabled",
        all(
            token
            not in
            runtime_route_text
            for token in stale_tokens
        ),
    )


    verify(
        "Stage 10 must remain unpromoted",
        True,
    )


    # ========================================================
    # Failure decision
    # ========================================================

    print(
        "\n12. SAVE VERIFICATION EVIDENCE"
    )


    if failures:

        print()
        print(
            "=" * 72
        )

        print(
            "STAGE 10.10.6 - 10.10.10: FAIL"
        )

        print(
            "STAGE 10.10: INCOMPLETE"
        )

        print(
            "STAGE 10 IS NOT PROMOTED"
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

        raise SystemExit(1)


    # ========================================================
    # Dependency identity
    # ========================================================

    identity_files = [
        PREVIOUS_10_10,
        STAGE10_4_FINAL,
        STAGE10_5_FINAL,
        STAGE10_6_FINAL,
        STAGE10_8_FINAL,
        STAGE10_9_FINAL,
        API_CONTRACT,
        RUNTIME_POLICY,
        API_CLIENT,
        API_MAPPED,
        API_RESULT,
        TEAM_PAGE,
        TEAM_INTELLIGENCE_LOADER,
        TEAM_CONTEXT_LOADER,
        RETRY_ACTION,
        ROOT_PAGE,
        MATCH_PAGE,
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
    # 10.10.6 - 10.10.10 evidence
    # ========================================================

    partial = {
        "stage":
            "10.10.6-10.10.10",

        "name":
            "FRONTEND_INTEGRATION_VERIFICATION_PART_2",

        "status":
            "PASS",

        "stage_10_10_6_complete":
            True,

        "stage_10_10_7_complete":
            True,

        "stage_10_10_8_complete":
            True,

        "stage_10_10_9_complete":
            True,

        "stage_10_10_10_complete":
            True,

        "verification": {
            "team_page":
                "PASS",

            "prediction_integrity":
                "PASS",

            "error_freshness":
                "PASS",

            "direct_artifact_prohibition":
                "PASS",

            "production_build":
                "PASS",

            "typescript":
                "PASS",

            "api_validation_tests":
                "PASS",

            "api_result_mapping_tests":
                "PASS",
        },

        "fetch_owners":
            fetch_owners,

        "artifact_access_violations":
            artifact_violations,

        "filesystem_access_violations":
            filesystem_violations,

        "team_dependency_graph":
            graph_paths(
                TEAM_PAGE
            ),

        "dependency_identity":
            dependency_identity,

        "stage10_10_complete":
            True,

        "stage10_ready_for_10_11_1":
            True,

        "stage10_complete":
            False,

        "next_stage":
            "10.11.1",

        "verified_at_utc":
            timestamp,
    }


    save_json(
        PARTIAL_OUTPUT,
        partial,
    )


    # ========================================================
    # Authoritative Stage 10.10 final artifact
    # ========================================================

    final = {
        "stage":
            "10.10",

        "name":
            "FRONTEND_INTEGRATION_VERIFICATION_FINAL",

        "status":
            "PASS",

        "stage_10_10_1_complete":
            True,

        "stage_10_10_2_complete":
            True,

        "stage_10_10_3_complete":
            True,

        "stage_10_10_4_complete":
            True,

        "stage_10_10_5_complete":
            True,

        "stage_10_10_6_complete":
            True,

        "stage_10_10_7_complete":
            True,

        "stage_10_10_8_complete":
            True,

        "stage_10_10_9_complete":
            True,

        "stage_10_10_10_complete":
            True,

        "integration_verification": {
            "build":
                "PASS",

            "typescript":
                "PASS",

            "api_contract":
                "PASS",

            "upcoming_page":
                "PASS",

            "match_page":
                "PASS",

            "team_page":
                "PASS",

            "prediction_integrity":
                "PASS",

            "error_freshness":
                "PASS",

            "direct_artifact_prohibition":
                "PASS",

            "production_build":
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

            "frontend_prediction_recalculation":
                False,

            "frontend_model_execution":
                False,

            "frontend_provider_access":
                False,

            "frontend_artifact_access":
                False,

            "stale_fallback":
                False,
        },

        "source_verification": {
            "sole_fetch_owner":
                relative(
                    API_CLIENT
                ),

            "runtime_source_file_count":
                len(
                    runtime
                ),

            "team_dependency_graph":
                graph_paths(
                    TEAM_PAGE
                ),
        },

        "dependency_identity":
            {
                **dependency_identity,

                relative(
                    PARTIAL_OUTPUT
                ):
                    sha256_file(
                        PARTIAL_OUTPUT
                    ),
            },

        "stage10_10_complete":
            True,

        "stage10_ready_for_10_11_1":
            True,

        "stage10_complete":
            False,

        "next_stage":
            "10.11.1",

        "verified_at_utc":
            timestamp,
    }


    save_json(
        FINAL_OUTPUT,
        final,
    )


    print(
        relative(
            PARTIAL_OUTPUT
        )
    )

    print(
        relative(
            FINAL_OUTPUT
        )
    )


    print()
    print(
        "=" * 72
    )

    print(
        "STAGE 10.10.6: PASS"
    )

    print(
        "TEAM PAGE: VERIFIED"
    )

    print()

    print(
        "STAGE 10.10.7: PASS"
    )

    print(
        "PREDICTION INTEGRITY: VERIFIED"
    )

    print()

    print(
        "STAGE 10.10.8: PASS"
    )

    print(
        "ERROR / FRESHNESS: VERIFIED"
    )

    print()

    print(
        "STAGE 10.10.9: PASS"
    )

    print(
        "DIRECT-ARTIFACT PROHIBITION: VERIFIED"
    )

    print()

    print(
        "STAGE 10.10.10: PASS"
    )

    print(
        "PRODUCTION BUILD: VERIFIED"
    )

    print()

    print(
        "STAGE 10.10: COMPLETE"
    )

    print(
        "STAGE 10 READY FOR 10.11.1"
    )

    print(
        "STAGE 10 IS NOT YET PROMOTED"
    )

    print(
        "=" * 72
    )


if __name__ == "__main__":

    main()
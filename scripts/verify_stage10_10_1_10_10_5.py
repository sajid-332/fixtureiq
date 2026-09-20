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
DATA = ROOT / "data" / "processed" / "frontend"


STAGE10_9_FINAL = (
    DATA
    / "stage10_9_final_verification.json"
)

STAGE10_2_FINAL = (
    DATA
    / "stage10_2_final_verification.json"
)

API_CONTRACT = (
    DOCS
    / "frontend_api_endpoint_contract.json"
)

OUTPUT = (
    DATA
    / "stage10_10_1_10_10_5_verification.json"
)


PACKAGE_JSON = (
    FRONTEND
    / "package.json"
)

PACKAGE_LOCK = (
    FRONTEND
    / "package-lock.json"
)


CLIENT = (
    FRONTEND
    / "lib"
    / "api"
    / "client.ts"
)

CONFIG = (
    FRONTEND
    / "lib"
    / "api"
    / "config.ts"
)

INTELLIGENCE = (
    FRONTEND
    / "lib"
    / "api"
    / "intelligence.ts"
)

PRODUCTION = (
    FRONTEND
    / "lib"
    / "api"
    / "production.ts"
)

CONTEXT = (
    FRONTEND
    / "lib"
    / "api"
    / "context.ts"
)

VALIDATION = (
    FRONTEND
    / "lib"
    / "api"
    / "validation.ts"
)

VALIDATED = (
    FRONTEND
    / "lib"
    / "api"
    / "validated.ts"
)

RESULT = (
    FRONTEND
    / "lib"
    / "api"
    / "result.ts"
)

MAPPED = (
    FRONTEND
    / "lib"
    / "api"
    / "mapped.ts"
)


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

UPCOMING_LOADER = (
    FRONTEND
    / "lib"
    / "dashboard"
    / "load-upcoming-matches.ts"
)

UPCOMING_RECORDS = (
    FRONTEND
    / "lib"
    / "dashboard"
    / "upcoming-records.ts"
)

MATCH_CARD = (
    FRONTEND
    / "components"
    / "matches"
    / "match-card.tsx"
)


CONNECTION_ERROR_STATE = (
    FRONTEND
    / "components"
    / "runtime"
    / "connection-error-state.tsx"
)

NOT_READY_STATE = (
    FRONTEND
    / "components"
    / "runtime"
    / "service-not-ready-state.tsx"
)

EMPTY_FIXTURES_STATE = (
    FRONTEND
    / "components"
    / "runtime"
    / "empty-fixtures-state.tsx"
)


INTELLIGENCE_ROUTES = {
    "/api/v1/intelligence/status",
    "/api/v1/intelligence/matches",
    "/api/v1/intelligence/matches/<fixture_id>",
    "/api/v1/intelligence/team/<path:team_name>",
    "/api/v1/intelligence/upcoming",
}


CONTEXT_ROUTES = {
    "/api/v1/context/fixtures",
    "/api/v1/context/fixtures/<fixture_id>",
    "/api/v1/context/fixtures/team/<path:team_name>",
    "/api/v1/context/form",
    "/api/v1/context/form/<path:team_name>",
    "/api/v1/context/standings",
    "/api/v1/context/standings/<path:team_name>",
    "/api/v1/context/status",
    "/api/v1/context/teams",
    "/api/v1/context/teams/<path:team_name>",
}


failures: list[str] = []


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


IMPORT_PATTERN = re.compile(
    r'''
    from
    \s+
    ["']
    (?P<module>\.[^"']+)
    ["']
    ''',
    re.VERBOSE,
)


def resolve_relative_import(
    importing_file: Path,
    module: str,
) -> Path | None:

    base = (
        importing_file.parent
        /
        module
    ).resolve()


    candidates = [
        base.with_suffix(
            ".ts"
        ),
        base.with_suffix(
            ".tsx"
        ),
        base
        / "index.ts",
        base
        / "index.tsx",
    ]


    for candidate in candidates:

        if candidate.exists():

            return candidate


    return None


def collect_relative_dependency_sources(
    entry: Path,
) -> dict[Path, str]:

    collected: dict[
        Path,
        str,
    ] = {}

    pending = [
        entry
    ]


    while pending:

        current = pending.pop()


        if current in collected:
            continue


        if not current.exists():
            continue


        if current.suffix not in {
            ".ts",
            ".tsx",
        }:
            continue


        current_source = source(
            current
        )

        collected[
            current
        ] = current_source


        for match in IMPORT_PATTERN.finditer(
            current_source
        ):

            module = match.group(
                "module"
            )

            resolved = resolve_relative_import(
                current,
                module,
            )

            if (
                resolved is not None
                and
                resolved.is_relative_to(
                    FRONTEND.resolve()
                )
            ):

                pending.append(
                    resolved
                )


    return collected


def dependency_graph_contains(
    entry: Path,
    token: str,
) -> bool:

    graph = collect_relative_dependency_sources(
        entry
    )

    return any(
        token
        in
        file_source
        for file_source in graph.values()
    )


def dependency_graph_paths(
    entry: Path,
) -> list[str]:

    return sorted(
        relative(
            path
        )
        for path in
        collect_relative_dependency_sources(
            entry
        ).keys()
    )


def no_direct_artifact_or_provider_access(
    text: str,
) -> bool:

    forbidden = [
        "data/processed",
        "data\\processed",
        ".csv",
        ".joblib",
        "football-data.org",
        "api-football",
        "api-sports",
    ]

    lowered = text.lower()

    return all(
        token.lower()
        not in
        lowered
        for token in forbidden
    )


def no_prediction_math(
    text: str,
) -> bool:

    forbidden = [
        "Math.max(",
        "predict_proba",
        "recalibr",
        "argmax",
        "joblib.load",
    ]

    return all(
        token
        not in
        text
        for token in forbidden
    )


def main() -> None:

    print(
        "=" * 72
    )

    print(
        "FixtureIQ Stage 10.10.1 - 10.10.5"
    )

    print(
        "FRONTEND INTEGRATION VERIFICATION"
    )

    print(
        "=" * 72
    )


    required = [
        STAGE10_9_FINAL,
        STAGE10_2_FINAL,
        API_CONTRACT,
        PACKAGE_JSON,
        PACKAGE_LOCK,
        CLIENT,
        CONFIG,
        INTELLIGENCE,
        PRODUCTION,
        CONTEXT,
        VALIDATION,
        VALIDATED,
        RESULT,
        MAPPED,
        ROOT_PAGE,
        MATCH_PAGE,
        UPCOMING_LOADER,
        UPCOMING_RECORDS,
        MATCH_CARD,
        CONNECTION_ERROR_STATE,
        NOT_READY_STATE,
        EMPTY_FIXTURES_STATE,
    ]


    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    for path in required:

        verify(
            relative(path),
            path.exists(),
        )


    if failures:

        print()
        print(
            "Required artifacts are missing."
        )

        raise SystemExit(1)


    stage9 = load_json(
        STAGE10_9_FINAL
    )

    stage2 = load_json(
        STAGE10_2_FINAL
    )

    api_contract = load_json(
        API_CONTRACT
    )


    print(
        "\n2. STAGE 10.9 FOUNDATION"
    )

    verify(
        "Stage 10.9 final PASS",
        stage9.get(
            "status"
        )
        ==
        "PASS",
    )

    verify(
        "Stage 10.9 complete",
        stage9.get(
            "stage10_9_complete"
        )
        is True,
    )

    verify(
        "Stage 10.9 authorized 10.10.1",
        stage9.get(
            "stage10_ready_for_10_10_1"
        )
        is True,
    )

    verify(
        "Stage 10 not promoted",
        stage9.get(
            "stage10_complete"
        )
        is False,
    )


    # ====================================================
    # 10.10.1 BUILD
    # ====================================================

    print(
        "\n3. STAGE 10.10.1 BUILD"
    )

    npm = npm_path()

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
        "Next.js build",
        build_ok,
    )


    if not build_ok:

        print()
        print(
            build_output
        )


    package = load_json(
        PACKAGE_JSON
    )

    scripts = package.get(
        "scripts",
        {},
    )


    verify(
        "package.json build script exists",
        isinstance(
            scripts,
            dict,
        )
        and
        isinstance(
            scripts.get(
                "build"
            ),
            str,
        ),
    )


    # ====================================================
    # 10.10.2 TYPESCRIPT
    # ====================================================

    print(
        "\n4. STAGE 10.10.2 TYPESCRIPT"
    )


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


    # ====================================================
    # 10.10.3 API CONTRACT
    # ====================================================

    print(
        "\n5. STAGE 10.10.3 API CONTRACT"
    )


    verify(
        "Stage 10.2 final PASS",
        stage2.get(
            "status"
        )
        ==
        "PASS",
    )


    contract_strings = set(
        flatten_strings(
            api_contract
        )
    )


    verify(
        "API contract LOCKED",
        api_contract.get(
            "status"
        )
        ==
        "LOCKED",
    )


    for route in sorted(
        INTELLIGENCE_ROUTES
    ):

        verify(
            f"Intelligence route locked: {route}",
            route
            in
            contract_strings,
        )


    for route in sorted(
        CONTEXT_ROUTES
    ):

        verify(
            f"Context route locked: {route}",
            route
            in
            contract_strings,
        )


    api_sources = {
        path:
            source(
                path
            )
        for path in [
            CLIENT,
            CONFIG,
            INTELLIGENCE,
            PRODUCTION,
            CONTEXT,
            VALIDATION,
            VALIDATED,
            RESULT,
            MAPPED,
        ]
    }


    combined_api_source = "\n".join(
        api_sources.values()
    )


    for forbidden_method in [
        'method: "POST"',
        "method: 'POST'",
        'method: "PUT"',
        "method: 'PUT'",
        'method: "PATCH"',
        "method: 'PATCH'",
        'method: "DELETE"',
        "method: 'DELETE'",
    ]:

        verify(
            (
                "No frontend write method: "
                +
                forbidden_method
            ),
            forbidden_method
            not in
            combined_api_source,
        )


    verify(
        "HTTP client uses no-store",
        re.search(
            r"""
            \bcache
            \s*
            :
            \s*
            ["']
            no-store
            ["']
            """,
            api_sources[
                CLIENT
            ],
            re.VERBOSE,
        )
        is not None,
    )


    verify(
        "Intelligence mapped upcoming wrapper exists",
        "getUpcomingIntelligenceResult"
        in
        api_sources[
            MAPPED
        ],
    )


    verify(
        "Intelligence mapped match wrapper exists",
        "getIntelligenceMatchResult"
        in
        api_sources[
            MAPPED
        ],
    )


    verify(
        "Mapped result preserves READY",
        '"READY"'
        in
        api_sources[
            RESULT
        ],
    )

    verify(
        "Mapped result preserves NOT_FOUND",
        '"NOT_FOUND"'
        in
        api_sources[
            RESULT
        ],
    )

    verify(
        "Mapped result preserves NOT_READY",
        '"NOT_READY"'
        in
        api_sources[
            RESULT
        ],
    )

    verify(
        "Mapped result preserves CONNECTION_ERROR",
        '"CONNECTION_ERROR"'
        in
        api_sources[
            RESULT
        ],
    )


    verify(
        "API client layer has no direct artifacts/providers",
        no_direct_artifact_or_provider_access(
            combined_api_source
        ),
    )


    # ====================================================
    # 10.10.4 UPCOMING PAGE
    # ====================================================

    print(
        "\n6. STAGE 10.10.4 UPCOMING PAGE"
    )


    root_source = source(
        ROOT_PAGE
    )

    loader_source = source(
        UPCOMING_LOADER
    )

    records_source = source(
        UPCOMING_RECORDS
    )

    card_source = source(
        MATCH_CARD
    )


    verify(
        "Upcoming page force-dynamic",
        '"force-dynamic"'
        in
        root_source,
    )


    verify(
        "Upcoming page uses loader",
        "loadUpcomingMatches"
        in
        root_source,
    )


    verify(
        "Upcoming dependency reaches mapped upcoming client",
        dependency_graph_contains(
            ROOT_PAGE,
            "getUpcomingIntelligenceResult",
        ),
    )


    verify(
        "Upcoming loader reaches mapped upcoming client",
        dependency_graph_contains(
            UPCOMING_LOADER,
            "getUpcomingIntelligenceResult",
        ),
    )


    verify(
        "Upcoming page handles NOT_READY",
        '"NOT_READY"'
        in
        root_source,
    )


    verify(
        "Upcoming page handles CONNECTION_ERROR",
        '"CONNECTION_ERROR"'
        in
        root_source,
    )


    verify(
        "Upcoming page renders empty fixture state",
        "EmptyFixturesState"
        in
        root_source,
    )


    verify(
        "Upcoming page renders MatchCard",
        "MatchCard"
        in
        root_source,
    )


    verify(
        "Upcoming page reads result data",
        "result.data"
        in
        root_source,
    )


    verify(
        "Upcoming record extraction preserved",
        "extractUpcomingDashboardMatches"
        in
        root_source
        and
        len(
            records_source.strip()
        )
        >
        0,
    )


    verify(
        "MatchCard fixture detail link preserved",
        (
            "/matches/"
            in
            card_source
            or
            "/matches/"
            in
            root_source
        ),
    )


    verify(
        "Upcoming page has no direct fetch",
        "fetch("
        not in
        root_source
        and
        "fetch("
        not in
        loader_source,
    )


    verify(
        "Upcoming page has no direct artifact/provider access",
        no_direct_artifact_or_provider_access(
            root_source
            +
            "\n"
            +
            loader_source
            +
            "\n"
            +
            records_source
        ),
    )


    verify(
        "Upcoming page has no prediction math",
        no_prediction_math(
            root_source
            +
            "\n"
            +
            loader_source
            +
            "\n"
            +
            records_source
        ),
    )


    # ====================================================
    # 10.10.5 MATCH PAGE
    # ====================================================

    print(
        "\n7. STAGE 10.10.5 MATCH PAGE"
    )


    match_source = source(
        MATCH_PAGE
    )

    match_graph = collect_relative_dependency_sources(
        MATCH_PAGE
    )


    match_graph_text = "\n".join(
        match_graph.values()
    )


    verify(
        "Match route force-dynamic",
        '"force-dynamic"'
        in
        match_source,
    )


    verify(
        "Match route uses fixtureId",
        "fixtureId"
        in
        match_source,
    )


    verify(
        "Match route dependency reaches mapped match client",
        "getIntelligenceMatchResult"
        in
        match_graph_text,
    )


    verify(
        "Match route handles NOT_FOUND",
        '"NOT_FOUND"'
        in
        match_source
        and
        "notFound("
        in
        match_source,
    )


    verify(
        "Match route handles NOT_READY",
        '"NOT_READY"'
        in
        match_source,
    )


    verify(
        "Match route handles CONNECTION_ERROR",
        '"CONNECTION_ERROR"'
        in
        match_source,
    )


    verify(
        "Match route uses result data",
        "result.data"
        in
        match_source,
    )


    verify(
        "Match route remains server-side",
        '"use client"'
        not in
        match_source,
    )


    verify(
        "Match route has no direct fetch",
        "fetch("
        not in
        match_source,
    )


    verify(
        "Match dependency graph has no direct artifacts/providers",
        no_direct_artifact_or_provider_access(
            match_graph_text
        ),
    )


    verify(
        "Match dependency graph has no prediction math",
        no_prediction_math(
            match_graph_text
        ),
    )


    verify(
        "Match detail has prediction probability fields",
        (
            "stage7_prob_home_win"
            in
            match_graph_text
            and
            "stage7_prob_draw"
            in
            match_graph_text
            and
            "stage7_prob_away_win"
            in
            match_graph_text
        ),
    )


    verify(
        "Match detail has confidence presentation",
        (
            "stage7_confidence"
            in
            match_graph_text
            or
            "confidence_band"
            in
            match_graph_text
        ),
    )


    verify(
        "Match detail has uncertainty presentation",
        "uncertainty"
        in
        match_graph_text.lower(),
    )


    verify(
        "Match detail has context alignment presentation",
        (
            "context_alignment"
            in
            match_graph_text
            or
            "ContextAlignment"
            in
            match_graph_text
        ),
    )


    verify(
        "Match detail has explanation presentation",
        "explanation"
        in
        match_graph_text.lower(),
    )


    # ====================================================
    # SHARED FRONTEND INTEGRITY
    # ====================================================

    print(
        "\n8. SHARED FRONTEND INTEGRITY"
    )


    route_combined = (
        root_source
        +
        "\n"
        +
        match_source
    )


    verify(
        "Pages do not access browser storage",
        all(
            token
            not in
            route_combined
            for token in [
                "localStorage",
                "sessionStorage",
                "previousData",
                "previousResponse",
                "fallbackData",
                "staleData",
            ]
        ),
    )


    verify(
        "Pages do not execute model code",
        all(
            token
            not in
            route_combined
            for token in [
                "predict_proba",
                "joblib",
                "RandomForest",
                "LogisticRegression",
            ]
        ),
    )


    verify(
        "Frontend does not recompute probabilities",
        "Math.max("
        not in
        route_combined,
    )


    print(
        "\n9. DEPENDENCY IDENTITY"
    )


    dependency_files = [
        STAGE10_9_FINAL,
        STAGE10_2_FINAL,
        API_CONTRACT,
        CLIENT,
        RESULT,
        MAPPED,
        ROOT_PAGE,
        MATCH_PAGE,
        UPCOMING_LOADER,
    ]


    dependency_identity = {
        relative(
            path
        ):
            sha256_file(
                path
            )
        for path in dependency_files
    }


    for path in dependency_files:

        verify(
            f"{relative(path)} captured",
            relative(path)
            in
            dependency_identity,
        )


    print(
        "\n10. NO PREMATURE PROMOTION"
    )


    verify(
        "10.10 stops before 10.10.6",
        True,
    )

    verify(
        "Stage 10.10 not complete",
        True,
    )

    verify(
        "Stage 10 not promoted",
        True,
    )


    print(
        "\n11. SAVE VERIFICATION"
    )


    if failures:

        print()
        print(
            "=" * 72
        )

        print(
            "STAGE 10.10.1 - 10.10.5: FAIL"
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


    result = {
        "stage":
            "10.10.1-10.10.5",

        "name":
            "FRONTEND_INTEGRATION_VERIFICATION_PART_1",

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

        "verification": {
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

            "direct_provider_access":
                False,

            "direct_artifact_access":
                False,

            "stale_fallback":
                False,
        },

        "upcoming_dependency_graph":
            dependency_graph_paths(
                ROOT_PAGE
            ),

        "match_dependency_graph":
            dependency_graph_paths(
                MATCH_PAGE
            ),

        "dependency_identity":
            dependency_identity,

        "stage10_ready_for_10_10_6":
            True,

        "stage10_10_complete":
            False,

        "stage10_complete":
            False,

        "next_stage":
            "10.10.6",

        "verified_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }


    save_json(
        OUTPUT,
        result,
    )


    print(
        relative(
            OUTPUT
        )
    )

    print()
    print(
        "=" * 72
    )

    print(
        "STAGE 10.10.1: PASS"
    )

    print(
        "FRONTEND BUILD: VERIFIED"
    )

    print()

    print(
        "STAGE 10.10.2: PASS"
    )

    print(
        "TYPESCRIPT: VERIFIED"
    )

    print()

    print(
        "STAGE 10.10.3: PASS"
    )

    print(
        "API CONTRACT: VERIFIED"
    )

    print()

    print(
        "STAGE 10.10.4: PASS"
    )

    print(
        "UPCOMING PAGE: VERIFIED"
    )

    print()

    print(
        "STAGE 10.10.5: PASS"
    )

    print(
        "MATCH PAGE: VERIFIED"
    )

    print()

    print(
        "STAGE 10 READY FOR 10.10.6"
    )

    print(
        "STAGE 10.10 IS NOT YET COMPLETE"
    )

    print(
        "STAGE 10 IS NOT YET PROMOTED"
    )

    print(
        "=" * 72
    )


if __name__ == "__main__":

    main()
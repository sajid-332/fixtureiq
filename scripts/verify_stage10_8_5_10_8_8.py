from __future__ import annotations

import hashlib
import json
import os
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


PREVIOUS_FILE = (
    FRONTEND_DATA
    / "stage10_8_1_10_8_4_verification.json"
)

OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_8_5_10_8_8_verification.json"
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

TEAM_PAGE = (
    FRONTEND
    / "app"
    / "teams"
    / "[teamName]"
    / "page.tsx"
)


CONNECTION_ERROR_STATE_FILE = (
    FRONTEND
    / "components"
    / "runtime"
    / "connection-error-state.tsx"
)

EMPTY_FIXTURES_STATE_FILE = (
    FRONTEND
    / "components"
    / "runtime"
    / "empty-fixtures-state.tsx"
)


API_CLIENT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "client.ts"
)

RESULT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "result.ts"
)

UPCOMING_LOADER_FILE = (
    FRONTEND
    / "lib"
    / "dashboard"
    / "load-upcoming-matches.ts"
)

TEAM_LOADER_FILE = (
    FRONTEND
    / "lib"
    / "teams"
    / "load-team-intelligence.ts"
)

TEAM_CONTEXT_LOADER_FILE = (
    FRONTEND
    / "lib"
    / "teams"
    / "load-team-context.ts"
)


CONNECTION_ERROR_CONTRACT_FILE = (
    DOCS
    / "frontend_runtime_connection_error_contract.json"
)

EMPTY_FIXTURES_CONTRACT_FILE = (
    DOCS
    / "frontend_runtime_empty_fixtures_contract.json"
)

NO_STALE_FALLBACK_CONTRACT_FILE = (
    DOCS
    / "frontend_runtime_no_stale_fallback_contract.json"
)

FAILED_REFRESH_CONTRACT_FILE = (
    DOCS
    / "frontend_runtime_failed_refresh_isolation_contract.json"
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

        payload = json.load(
            file
        )

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

            digest.update(
                chunk
            )

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
        .replace(
            "\\",
            "/",
        )
    )


def resolve_project_path(
    value: str,
) -> Path:

    path = (
        ROOT
        /
        value
    ).resolve()

    path.relative_to(
        ROOT.resolve()
    )

    return path


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

        file.write(
            "\n"
        )

    temporary.replace(
        path
    )


def check(
    label: str,
    condition,
    failures: list[str],
) -> None:

    passed = bool(
        condition
    )

    print(
        f"{label}: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    if not passed:

        failures.append(
            label
        )


def verify_dependencies(
    contract: dict,
    label: str,
    failures: list[str],
) -> None:

    dependencies = contract.get(
        "dependency_identity",
        {},
    )


    check(
        f"{label} dependency identity exists",
        isinstance(
            dependencies,
            dict,
        )
        and
        bool(
            dependencies
        ),
        failures,
    )


    if not isinstance(
        dependencies,
        dict,
    ):

        return


    for path_text, declaration in (
        dependencies.items()
    ):

        try:

            expected = (
                declaration.get(
                    "sha256"
                )
                if isinstance(
                    declaration,
                    dict,
                )
                else None
            )

            path = resolve_project_path(
                path_text
            )

            current = (
                isinstance(
                    expected,
                    str,
                )
                and
                bool(
                    expected
                )
                and
                path.exists()
                and
                sha256_file(
                    path
                )
                ==
                expected
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


def npm_executable() -> str | None:

    return (
        shutil.which(
            "npm.cmd"
        )
        or
        shutil.which(
            "npm"
        )
    )


def run_typescript() -> tuple[
    bool,
    str,
]:

    npm = npm_executable()


    if npm is None:

        return (
            False,
            "npm not found.",
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


def run_production_build() -> tuple[
    bool,
    str,
]:

    npm = npm_executable()


    if npm is None:

        return (
            False,
            "npm not found.",
        )


    environment = os.environ.copy()

    environment.setdefault(
        "FIXTUREIQ_API_BASE_URL",
        "http://127.0.0.1:5000",
    )


    result = subprocess.run(
        [
            npm,
            "run",
            "build",
        ],
        cwd=FRONTEND,
        env=environment,
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


def failure_before_data(
    source: str,
) -> bool:

    result_assignment = re.search(
        r"""
        \b
        (?:const|let)
        \s+
        result
        \s*
        =
        \s*
        await
        \b
        """,
        source,
        re.VERBOSE,
    )


    if result_assignment is None:
        return False


    request_scope = source[
        result_assignment.start():
    ]


    data_position = request_scope.find(
        "result.data"
    )

    connection_position = request_scope.find(
        '"CONNECTION_ERROR"'
    )

    not_ready_position = request_scope.find(
        '"NOT_READY"'
    )


    return (
        data_position >= 0
        and
        connection_position >= 0
        and
        not_ready_position >= 0
        and
        connection_position
        <
        data_position
        and
        not_ready_position
        <
        data_position
    )


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.8.5 - 10.8.8"
    )

    print(
        "NETWORK + EMPTY + NO-STALE + FAILED-REFRESH VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        PREVIOUS_FILE,
        ROOT_PAGE,
        MATCH_PAGE,
        TEAM_PAGE,
        CONNECTION_ERROR_STATE_FILE,
        EMPTY_FIXTURES_STATE_FILE,
        API_CLIENT_FILE,
        RESULT_FILE,
        UPCOMING_LOADER_FILE,
        TEAM_LOADER_FILE,
        TEAM_CONTEXT_LOADER_FILE,
        CONNECTION_ERROR_CONTRACT_FILE,
        EMPTY_FIXTURES_CONTRACT_FILE,
        NO_STALE_FALLBACK_CONTRACT_FILE,
        FAILED_REFRESH_CONTRACT_FILE,
    ]


    print(
        "\n1. REQUIRED ARTIFACTS"
    )


    for path in required:

        check(
            relative(
                path
            ),
            path.exists(),
            failures,
        )


    if failures:

        sys.exit(
            1
        )


    previous = load_json(
        PREVIOUS_FILE
    )

    connection_contract = load_json(
        CONNECTION_ERROR_CONTRACT_FILE
    )

    empty_contract = load_json(
        EMPTY_FIXTURES_CONTRACT_FILE
    )

    stale_contract = load_json(
        NO_STALE_FALLBACK_CONTRACT_FILE
    )

    refresh_contract = load_json(
        FAILED_REFRESH_CONTRACT_FILE
    )


    root_source = (
        ROOT_PAGE.read_text(
            encoding="utf-8"
        )
    )

    match_source = (
        MATCH_PAGE.read_text(
            encoding="utf-8"
        )
    )

    team_source = (
        TEAM_PAGE.read_text(
            encoding="utf-8"
        )
    )

    connection_source = (
        CONNECTION_ERROR_STATE_FILE.read_text(
            encoding="utf-8"
        )
    )

    empty_source = (
        EMPTY_FIXTURES_STATE_FILE.read_text(
            encoding="utf-8"
        )
    )

    client_source = (
        API_CLIENT_FILE.read_text(
            encoding="utf-8"
        )
    )

    result_source = (
        RESULT_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. STAGE 10.8.1 - 10.8.4 FOUNDATION"
    )


    check(
        "Previous verification PASS",
        previous.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )


    for key in [
        "stage_10_8_1_complete",
        "stage_10_8_2_complete",
        "stage_10_8_3_complete",
        "stage_10_8_4_complete",
    ]:

        check(
            key,
            previous.get(
                key
            )
            is True,
            failures,
        )


    check(
        "10.8.4 authorized 10.8.5",
        previous.get(
            "stage10_ready_for_10_8_5"
        )
        is True,
        failures,
    )


    print(
        "\n3. STAGE 10.8.5 NETWORK UNAVAILABLE"
    )


    check(
        "10.8.5 stage exact",
        connection_contract.get(
            "stage"
        )
        ==
        "10.8.5",
        failures,
    )


    check(
        "10.8.5 LOCKED",
        connection_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Mapped state CONNECTION_ERROR",
        connection_contract.get(
            "mapped_state"
        )
        ==
        "CONNECTION_ERROR",
        failures,
    )


    check(
        "ConnectionErrorState export",
        (
            "export function ConnectionErrorState"
            in
            connection_source
        ),
        failures,
    )


    check(
        "Connection error runtime marker",
        (
            'data-fixtureiq-runtime-state="CONNECTION_ERROR"'
            in
            connection_source
        ),
        failures,
    )


    check(
        "Connection error uses ErrorState",
        "ErrorState"
        in
        connection_source,
        failures,
    )


    check(
        "Connection error uses FreshnessIndicator",
        "FreshnessIndicator"
        in
        connection_source,
        failures,
    )


    check(
        "Connection error explicitly rejects old result",
        (
            "No older result is being shown."
            in
            connection_source
        ),
        failures,
    )


    for label, source, resource in [
        (
            "Dashboard",
            root_source,
            "Upcoming match intelligence",
        ),
        (
            "Match",
            match_source,
            "Match intelligence",
        ),
        (
            "Team",
            team_source,
            "Team intelligence",
        ),
    ]:

        check(
            f"{label} handles CONNECTION_ERROR",
            (
                '"CONNECTION_ERROR"'
                in
                source
                and
                "ConnectionErrorState"
                in
                source
                and
                f'resource="{resource}"'
                in
                source
            ),
            failures,
        )


    check(
        "Team context handles CONNECTION_ERROR",
        (
            "standingsResult.state ==="
            in
            team_source
            and
            "formResult.state ==="
            in
            team_source
            and
            '"CONNECTION_ERROR"'
            in
            team_source
            and
            'resource="Team context"'
            in
            team_source
        ),
        failures,
    )


    check(
        "ConnectionErrorState SHA exact",
        connection_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            CONNECTION_ERROR_STATE_FILE
        ),
        failures,
    )


    print(
        "\n4. STAGE 10.8.6 EMPTY FIXTURES"
    )


    check(
        "10.8.6 stage exact",
        empty_contract.get(
            "stage"
        )
        ==
        "10.8.6",
        failures,
    )


    check(
        "10.8.6 LOCKED",
        empty_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Empty fixtures requires READY",
        empty_contract.get(
            "required_parent_state"
        )
        ==
        "READY",
        failures,
    )


    check(
        "EmptyFixturesState export",
        (
            "export function EmptyFixturesState"
            in
            empty_source
        ),
        failures,
    )


    check(
        "EMPTY_FIXTURES marker",
        (
            'data-fixtureiq-runtime-state="EMPTY_FIXTURES"'
            in
            empty_source
        ),
        failures,
    )


    check(
        "Empty state rejects old fixture list",
        (
            "No previous fixture list is being reused."
            in
            empty_source
        ),
        failures,
    )


    check(
        "Dashboard renders EmptyFixturesState",
        "<EmptyFixturesState"
        in
        root_source,
        failures,
    )


    check(
        "Dashboard still has zero-length condition",
        re.search(
            r'''
            [A-Za-z_$][A-Za-z0-9_$]*
            \s*
            \.
            \s*
            length
            \s*
            ===
            \s*
            0
            ''',
            root_source,
            re.VERBOSE,
        )
        is not None,
        failures,
    )


    check(
        "EmptyFixturesState SHA exact",
        empty_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            EMPTY_FIXTURES_STATE_FILE
        ),
        failures,
    )


    print(
        "\n5. STAGE 10.8.7 PREVENT STALE FALLBACK"
    )


    check(
        "10.8.7 stage exact",
        stale_contract.get(
            "stage"
        )
        ==
        "10.8.7",
        failures,
    )


    check(
        "10.8.7 LOCKED",
        stale_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Policy current-request-only",
        stale_contract.get(
            "policy"
        )
        ==
        "CURRENT_REQUEST_ONLY_FAIL_CLOSED",
        failures,
    )


    check(
        "HTTP client cache=no-store",
        re.search(
            r'''cache\s*:\s*["']no-store["']''',
            client_source,
        )
        is not None,
        failures,
    )


    for label, source in [
        (
            "Dashboard",
            root_source,
        ),
        (
            "Match",
            match_source,
        ),
        (
            "Team",
            team_source,
        ),
    ]:

        check(
            f"{label} is force-dynamic",
            '"force-dynamic"'
            in
            source,
            failures,
        )


    stale_combined = "\n".join(
        [
            root_source,
            match_source,
            team_source,
            UPCOMING_LOADER_FILE.read_text(
                encoding="utf-8"
            ),
            TEAM_LOADER_FILE.read_text(
                encoding="utf-8"
            ),
            TEAM_CONTEXT_LOADER_FILE.read_text(
                encoding="utf-8"
            ),
        ]
    )


    for forbidden in [
        "localStorage",
        "sessionStorage",
        "previousData",
        "previousResponse",
        "fallbackData",
        "staleData",
        "unstable_cache",
    ]:

        check(
            f"No stale fallback mechanism: {forbidden}",
            forbidden
            not in
            stale_combined,
            failures,
        )


    check(
        "No client state retention",
        (
            '"use client"'
            not in
            stale_combined
            and
            "'use client'"
            not in
            stale_combined
            and
            "useState("
            not in
            stale_combined
            and
            "useEffect("
            not in
            stale_combined
        ),
        failures,
    )


    check(
        "HTTP client SHA exact",
        stale_contract.get(
            "http_client",
            {},
        ).get(
            "sha256"
        )
        ==
        sha256_file(
            API_CLIENT_FILE
        ),
        failures,
    )


    print(
        "\n6. STAGE 10.8.8 FAILED REFRESH ISOLATION"
    )


    check(
        "10.8.8 stage exact",
        refresh_contract.get(
            "stage"
        )
        ==
        "10.8.8",
        failures,
    )


    check(
        "10.8.8 LOCKED",
        refresh_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Failure replaces prior READY view",
        refresh_contract.get(
            "policy"
        )
        ==
        "FAILURE_REPLACES_PRIOR_READY_VIEW",
        failures,
    )


    check(
        "Dashboard failure before data extraction",
        failure_before_data(
            root_source
        ),
        failures,
    )


    check(
        "Match failure before data extraction",
        failure_before_data(
            match_source
        ),
        failures,
    )


    check(
        "Team failure before data extraction",
        failure_before_data(
            team_source
        ),
        failures,
    )


    check(
        "Dashboard route SHA exact",
        refresh_contract.get(
            "routes",
            {},
        ).get(
            "/",
            {},
        ).get(
            "sha256"
        )
        ==
        sha256_file(
            ROOT_PAGE
        ),
        failures,
    )


    check(
        "Match route SHA exact",
        refresh_contract.get(
            "routes",
            {},
        ).get(
            "/matches/[fixtureId]",
            {},
        ).get(
            "sha256"
        )
        ==
        sha256_file(
            MATCH_PAGE
        ),
        failures,
    )


    check(
        "Team route SHA exact",
        refresh_contract.get(
            "routes",
            {},
        ).get(
            "/teams/[teamName]",
            {},
        ).get(
            "sha256"
        )
        ==
        sha256_file(
            TEAM_PAGE
        ),
        failures,
    )


    behavior = refresh_contract.get(
        "behavior",
        {},
    )


    for key in [
        "failed_refresh_keeps_old_match",
        "failed_refresh_keeps_old_fixture_list",
        "failed_refresh_keeps_old_team_data",
        "client_state_retention",
        "browser_storage_retention",
        "stale_fallback",
    ]:

        check(
            f"Failed-refresh rule false: {key}",
            behavior.get(
                key
            )
            is False,
            failures,
        )


    check(
        "Current failure rendered",
        behavior.get(
            "current_request_failure_rendered"
        )
        is True,
        failures,
    )


    print(
        "\n7. 10.8.9 RETRY NOT IMPLEMENTED EARLY"
    )


    runtime_combined = "\n".join(
        [
            root_source,
            match_source,
            team_source,
            connection_source,
            empty_source,
        ]
    )


    for term in [
        "router.refresh",
        "window.location.reload",
        "location.reload",
        "Retry",
        "Try again",
        "onClick",
    ]:

        check(
            f"Retry behavior absent: {term}",
            term.lower()
            not in
            runtime_combined.lower(),
            failures,
        )


    print(
        "\n8. DATA / MODEL SAFETY"
    )


    check(
        "Routes contain no direct fetch",
        re.search(
            r"\bfetch\s*\(",
            runtime_combined,
        )
        is None,
        failures,
    )


    for term in [
        "data/processed",
        "data\\processed",
        ".csv",
        ".joblib",
        "football-data.org",
        "api-football",
        "api-sports",
        "Math.max",
        "recalibr",
    ]:

        check(
            f"Runtime UX excludes {term}",
            term.lower()
            not in
            runtime_combined.lower(),
            failures,
        )


    print(
        "\n9. DEPENDENCY FRESHNESS"
    )


    for stage, contract in [
        (
            "10.8.5",
            connection_contract,
        ),
        (
            "10.8.6",
            empty_contract,
        ),
        (
            "10.8.7",
            stale_contract,
        ),
        (
            "10.8.8",
            refresh_contract,
        ),
    ]:

        verify_dependencies(
            contract,
            stage,
            failures,
        )


    print(
        "\n10. TYPESCRIPT"
    )


    (
        typescript_ok,
        typescript_output,
    ) = run_typescript()


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


    print(
        "\n11. PRODUCTION BUILD"
    )


    (
        build_ok,
        build_output,
    ) = run_production_build()


    check(
        "Next.js production build",
        build_ok,
        failures,
    )


    if (
        not build_ok
        and
        build_output
    ):

        print()

        print(
            build_output
        )


    print(
        "\n12. NO PREMATURE PROMOTION"
    )


    for stage, contract, key in [
        (
            "10.8.5",
            connection_contract,
            "stage10_8_5_complete",
        ),
        (
            "10.8.6",
            empty_contract,
            "stage10_8_6_complete",
        ),
        (
            "10.8.7",
            stale_contract,
            "stage10_8_7_complete",
        ),
        (
            "10.8.8",
            refresh_contract,
            "stage10_8_8_complete",
        ),
    ]:

        promotion = contract.get(
            "promotion",
            {},
        )


        check(
            f"{stage} did not self-promote",
            promotion.get(
                key
            )
            is False,
            failures,
        )


        check(
            f"{stage}: Stage 10.8 incomplete",
            promotion.get(
                "stage10_8_complete"
            )
            is False,
            failures,
        )


        check(
            f"{stage}: Stage 10 incomplete",
            promotion.get(
                "stage10_complete"
            )
            is False,
            failures,
        )


    print(
        "\n13. SAVE VERIFICATION"
    )


    passed = (
        len(
            failures
        )
        ==
        0
    )


    if passed:

        report = {
            "stage":
                "10.8.5-10.8.8",

            "name":
                "NETWORK_EMPTY_NO_STALE_FAILED_REFRESH_VERIFICATION",

            "status":
                "PASS",

            "stage_10_8_5_complete":
                True,

            "stage_10_8_6_complete":
                True,

            "stage_10_8_7_complete":
                True,

            "stage_10_8_8_complete":
                True,

            "network_unavailable":
                "LOCKED_AND_VERIFIED",

            "empty_fixtures":
                "LOCKED_AND_VERIFIED",

            "no_stale_fallback":
                "LOCKED_AND_VERIFIED",

            "failed_refresh_isolation":
                "LOCKED_AND_VERIFIED",

            "integrity": {
                "connection_error_explicit":
                    True,

                "ready_empty_explicit":
                    True,

                "http_cache_no_store":
                    True,

                "force_dynamic":
                    True,

                "stale_fallback":
                    False,

                "old_match_after_failed_refresh":
                    False,

                "old_fixture_list_after_failed_refresh":
                    False,

                "old_team_data_after_failed_refresh":
                    False,

                "browser_storage":
                    False,

                "client_state_retention":
                    False,

                "retry_logic":
                    False,

                "direct_fetch":
                    False,

                "provider_access":
                    False,

                "artifact_access":
                    False,

                "prediction_modification":
                    False,
            },

            "typescript_compiler":
                "PASS",

            "production_build":
                "PASS",

            "stage10_ready_for_10_8_9":
                True,

            "stage10_8_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.8.9",

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "failures":
                [],
        }


        save_json_atomic(
            OUTPUT_FILE,
            report,
        )


        print(
            relative(
                OUTPUT_FILE
            )
        )


    print(
        "\n"
        +
        "=" * 72
    )


    if passed:

        print(
            "STAGE 10.8.5: PASS"
        )

        print(
            "NETWORK UNAVAILABLE: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.8.6: PASS"
        )

        print(
            "EMPTY FIXTURES: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.8.7: PASS"
        )

        print(
            "NO STALE FALLBACK: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.8.8: PASS"
        )

        print(
            "FAILED REFRESH ISOLATION: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.8.9"
        )

        print(
            "STAGE 10.8 IS NOT YET COMPLETE"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.8.5 - 10.8.8: FAIL"
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
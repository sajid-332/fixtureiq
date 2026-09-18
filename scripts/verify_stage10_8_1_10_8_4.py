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
    / "stage10_7_final_verification.json"
)

OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_8_1_10_8_4_verification.json"
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


APP_LOADING_FILE = (
    FRONTEND
    / "app"
    / "loading.tsx"
)

MATCH_LOADING_FILE = (
    FRONTEND
    / "app"
    / "matches"
    / "[fixtureId]"
    / "loading.tsx"
)

TEAM_LOADING_FILE = (
    FRONTEND
    / "app"
    / "teams"
    / "[teamName]"
    / "loading.tsx"
)


GLOBAL_NOT_FOUND_FILE = (
    FRONTEND
    / "app"
    / "not-found.tsx"
)

MATCH_NOT_FOUND_FILE = (
    FRONTEND
    / "app"
    / "matches"
    / "[fixtureId]"
    / "not-found.tsx"
)

TEAM_NOT_FOUND_FILE = (
    FRONTEND
    / "app"
    / "teams"
    / "[teamName]"
    / "not-found.tsx"
)


READY_STATE_FILE = (
    FRONTEND
    / "components"
    / "runtime"
    / "ready-state.tsx"
)

NOT_READY_STATE_FILE = (
    FRONTEND
    / "components"
    / "runtime"
    / "service-not-ready-state.tsx"
)


RESULT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "result.ts"
)


READY_CONTRACT = (
    DOCS
    / "frontend_runtime_ready_state_contract.json"
)

LOADING_UX_CONTRACT = (
    DOCS
    / "frontend_runtime_loading_ux_contract.json"
)

NOT_FOUND_UX_CONTRACT = (
    DOCS
    / "frontend_runtime_not_found_ux_contract.json"
)

NOT_READY_UX_CONTRACT = (
    DOCS
    / "frontend_runtime_not_ready_ux_contract.json"
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


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.8.1 - 10.8.4"
    )

    print(
        "READY + LOADING + 404 + NOT_READY UX VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        PREVIOUS_FILE,
        ROOT_PAGE,
        MATCH_PAGE,
        TEAM_PAGE,
        APP_LOADING_FILE,
        MATCH_LOADING_FILE,
        TEAM_LOADING_FILE,
        GLOBAL_NOT_FOUND_FILE,
        MATCH_NOT_FOUND_FILE,
        TEAM_NOT_FOUND_FILE,
        READY_STATE_FILE,
        NOT_READY_STATE_FILE,
        RESULT_FILE,
        READY_CONTRACT,
        LOADING_UX_CONTRACT,
        NOT_FOUND_UX_CONTRACT,
        NOT_READY_UX_CONTRACT,
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

    ready_contract = load_json(
        READY_CONTRACT
    )

    loading_contract = load_json(
        LOADING_UX_CONTRACT
    )

    not_found_contract = load_json(
        NOT_FOUND_UX_CONTRACT
    )

    not_ready_contract = load_json(
        NOT_READY_UX_CONTRACT
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

    ready_source = (
        READY_STATE_FILE.read_text(
            encoding="utf-8"
        )
    )

    not_ready_source = (
        NOT_READY_STATE_FILE.read_text(
            encoding="utf-8"
        )
    )

    result_source = (
        RESULT_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. STAGE 10.7 FOUNDATION"
    )


    check(
        "Stage 10.7 final PASS",
        previous.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )


    check(
        "Stage 10.7 complete",
        previous.get(
            "stage10_7_complete"
        )
        is True,
        failures,
    )


    check(
        "Stage 10 ready for 10.8.1",
        previous.get(
            "stage10_ready_for_10_8_1"
        )
        is True,
        failures,
    )


    print(
        "\n3. API RESULT STATE AUTHORITY"
    )


    for token in [
        '"READY"',
        '"NOT_FOUND"',
        '"NOT_READY"',
        '"CONNECTION_ERROR"',
    ]:

        check(
            f"Mapped result preserves {token}",
            token
            in
            result_source,
            failures,
        )


    check(
        "Mapped result contains HTTP 404",
        "404"
        in
        result_source,
        failures,
    )


    check(
        "Mapped result contains HTTP 503",
        "503"
        in
        result_source,
        failures,
    )


    print(
        "\n4. STAGE 10.8.1 READY"
    )


    check(
        "10.8.1 stage exact",
        ready_contract.get(
            "stage"
        )
        ==
        "10.8.1",
        failures,
    )


    check(
        "10.8.1 LOCKED",
        ready_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "ReadyState export",
        "export function ReadyState"
        in
        ready_source,
        failures,
    )


    check(
        "READY marker exact",
        (
            'data-fixtureiq-runtime-state="READY"'
            in
            ready_source
        ),
        failures,
    )


    check(
        "READY renders children directly",
        "{children}"
        in
        ready_source,
        failures,
    )


    check(
        "READY has no data fetch",
        re.search(
            r"\bfetch\s*\(",
            ready_source,
        )
        is None,
        failures,
    )


    check(
        "ReadyState SHA exact",
        ready_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            READY_STATE_FILE
        ),
        failures,
    )


    print(
        "\n5. STAGE 10.8.2 LOADING"
    )


    check(
        "10.8.2 stage exact",
        loading_contract.get(
            "stage"
        )
        ==
        "10.8.2",
        failures,
    )


    check(
        "10.8.2 LOCKED",
        loading_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    loading_files = [
        APP_LOADING_FILE,
        MATCH_LOADING_FILE,
        TEAM_LOADING_FILE,
    ]


    declared_loading = loading_contract.get(
        "boundary_sha256",
        {},
    )


    for path in loading_files:

        source = path.read_text(
            encoding="utf-8"
        )


        check(
            f"{relative(path)} uses LoadingState",
            "LoadingState"
            in
            source,
            failures,
        )


        check(
            f"{relative(path)} default export",
            "export default function Loading"
            in
            source,
            failures,
        )


        check(
            f"{relative(path)} SHA exact",
            isinstance(
                declared_loading,
                dict,
            )
            and
            declared_loading.get(
                relative(
                    path
                )
            )
            ==
            sha256_file(
                path
            ),
            failures,
        )


    print(
        "\n6. STAGE 10.8.3 404"
    )


    check(
        "10.8.3 stage exact",
        not_found_contract.get(
            "stage"
        )
        ==
        "10.8.3",
        failures,
    )


    check(
        "10.8.3 LOCKED",
        not_found_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "404 status mapped exactly",
        not_found_contract.get(
            "mapped_http_status"
        )
        ==
        404,
        failures,
    )


    for path in [
        GLOBAL_NOT_FOUND_FILE,
        MATCH_NOT_FOUND_FILE,
        TEAM_NOT_FOUND_FILE,
    ]:

        source = path.read_text(
            encoding="utf-8"
        )


        check(
            f"{relative(path)} has visible not-found content",
            (
                "not found"
                in
                source.lower()
            ),
            failures,
        )


    check(
        "Match route maps NOT_FOUND to notFound",
        (
            '"NOT_FOUND"'
            in
            match_source
            and
            "notFound();"
            in
            match_source
        ),
        failures,
    )


    check(
        "Team route maps NOT_FOUND to notFound",
        (
            '"NOT_FOUND"'
            in
            team_source
            and
            "notFound();"
            in
            team_source
        ),
        failures,
    )


    print(
        "\n7. STAGE 10.8.4 NOT_READY / API 503"
    )


    check(
        "10.8.4 stage exact",
        not_ready_contract.get(
            "stage"
        )
        ==
        "10.8.4",
        failures,
    )


    check(
        "10.8.4 LOCKED",
        not_ready_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "NOT_READY maps to API 503",
        (
            not_ready_contract.get(
                "mapped_state"
            )
            ==
            "NOT_READY"
            and
            not_ready_contract.get(
                "mapped_http_status"
            )
            ==
            503
        ),
        failures,
    )


    check(
        "ServiceNotReadyState export",
        (
            "export function ServiceNotReadyState"
            in
            not_ready_source
        ),
        failures,
    )


    check(
        "NOT_READY runtime marker",
        (
            'data-fixtureiq-runtime-state="NOT_READY"'
            in
            not_ready_source
        ),
        failures,
    )


    check(
        "NOT_READY state compile-time fixed",
        (
            'state:\n      "NOT_READY"'
            in
            not_ready_source
        ),
        failures,
    )


    check(
        "NOT_READY uses ErrorState",
        "ErrorState"
        in
        not_ready_source,
        failures,
    )


    check(
        "NOT_READY uses FreshnessIndicator",
        "FreshnessIndicator"
        in
        not_ready_source,
        failures,
    )


    check(
        "No stale-result language",
        (
            "No older result is being shown."
            in
            not_ready_source
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
            f"{label} explicit NOT_READY branch",
            (
                'result.state ==='
                in
                source
                and
                '"NOT_READY"'
                in
                source
                and
                "ServiceNotReadyState"
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
        "Team context explicit NOT_READY branch",
        (
            'standingsResult.state ==='
            in
            team_source
            and
            'formResult.state ==='
            in
            team_source
            and
            'resource="Team context"'
            in
            team_source
        ),
        failures,
    )


    print(
        "\n8. ROUTE SOURCE IDENTITY"
    )


    check(
        "Dashboard route SHA current",
        not_ready_contract.get(
            "root_page_after_sha256"
        )
        ==
        sha256_file(
            ROOT_PAGE
        ),
        failures,
    )


    check(
        "Match route SHA current",
        not_ready_contract.get(
            "match_page_after_sha256"
        )
        ==
        sha256_file(
            MATCH_PAGE
        ),
        failures,
    )


    check(
        "Team route SHA current",
        not_ready_contract.get(
            "team_page_after_sha256"
        )
        ==
        sha256_file(
            TEAM_PAGE
        ),
        failures,
    )


    check(
        "NOT_READY component SHA exact",
        not_ready_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            NOT_READY_STATE_FILE
        ),
        failures,
    )


    print(
        "\n9. 10.8.5+ NOT IMPLEMENTED EARLY"
    )


    combined = "\n".join(
        [
            root_source,
            match_source,
            team_source,
            ready_source,
            not_ready_source,
            APP_LOADING_FILE.read_text(
                encoding="utf-8"
            ),
            MATCH_LOADING_FILE.read_text(
                encoding="utf-8"
            ),
            TEAM_LOADING_FILE.read_text(
                encoding="utf-8"
            ),
            GLOBAL_NOT_FOUND_FILE.read_text(
                encoding="utf-8"
            ),
            MATCH_NOT_FOUND_FILE.read_text(
                encoding="utf-8"
            ),
        ]
    )


    for term in [
        "retry",
        "window.location.reload",
        "router.refresh",
        "setInterval",
        "localStorage",
        "sessionStorage",
        "previousData",
        "previousResponse",
        "staleData",
        "fallbackData",
    ]:

        check(
            f"No future runtime behavior: {term}",
            term.lower()
            not in
            combined.lower(),
            failures,
        )


    check(
        "No network-specific UX added early",
        (
            "network unavailable"
            not in
            combined.lower()
            and
            "connection error"
            not in
            combined.lower()
        ),
        failures,
    )


    print(
        "\n10. DATA / MODEL SAFETY"
    )


    check(
        "No direct fetch added",
        re.search(
            r"\bfetch\s*\(",
            combined,
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
            combined.lower(),
            failures,
        )


    print(
        "\n11. DEPENDENCY FRESHNESS"
    )


    for stage, contract in [
        (
            "10.8.1",
            ready_contract,
        ),
        (
            "10.8.2",
            loading_contract,
        ),
        (
            "10.8.3",
            not_found_contract,
        ),
        (
            "10.8.4",
            not_ready_contract,
        ),
    ]:

        verify_dependencies(
            contract,
            stage,
            failures,
        )


    print(
        "\n12. TYPESCRIPT"
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
        "\n13. PRODUCTION BUILD"
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
        "\n14. NO PREMATURE PROMOTION"
    )


    for stage, contract, key in [
        (
            "10.8.1",
            ready_contract,
            "stage10_8_1_complete",
        ),
        (
            "10.8.2",
            loading_contract,
            "stage10_8_2_complete",
        ),
        (
            "10.8.3",
            not_found_contract,
            "stage10_8_3_complete",
        ),
        (
            "10.8.4",
            not_ready_contract,
            "stage10_8_4_complete",
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
        "\n15. SAVE VERIFICATION"
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
                "10.8.1-10.8.4",

            "name":
                "READY_LOADING_404_NOT_READY_UX_VERIFICATION",

            "status":
                "PASS",

            "stage_10_8_1_complete":
                True,

            "stage_10_8_2_complete":
                True,

            "stage_10_8_3_complete":
                True,

            "stage_10_8_4_complete":
                True,

            "ready_state":
                "LOCKED_AND_VERIFIED",

            "loading_state":
                "LOCKED_AND_VERIFIED",

            "not_found_404":
                "LOCKED_AND_VERIFIED",

            "not_ready_503":
                "LOCKED_AND_VERIFIED",

            "integrity": {
                "ready_data_unchanged":
                    True,

                "next_loading_boundaries":
                    True,

                "not_found_uses_next_boundary":
                    True,

                "api_503_uses_not_ready":
                    True,

                "stale_fallback":
                    False,

                "retry_logic":
                    False,

                "network_specific_logic":
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

            "stage10_ready_for_10_8_5":
                True,

            "stage10_8_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.8.5",

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
            "STAGE 10.8.1: PASS"
        )

        print(
            "READY STATE UX: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.8.2: PASS"
        )

        print(
            "LOADING UX: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.8.3: PASS"
        )

        print(
            "404 UX: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.8.4: PASS"
        )

        print(
            "503 / NOT_READY UX: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.8.5"
        )

        print(
            "STAGE 10.8 IS NOT YET COMPLETE"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.8.1 - 10.8.4: FAIL"
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
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


VERIFY_1_4_FILE = (
    FRONTEND_DATA
    / "stage10_7_1_10_7_4_verification.json"
)

VERIFY_5_8_FILE = (
    FRONTEND_DATA
    / "stage10_7_5_10_7_8_verification.json"
)

VERIFY_9_12_FILE = (
    FRONTEND_DATA
    / "stage10_7_9_10_7_12_verification.json"
)


ERROR_STATE_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "error-state.tsx"
)

LOADING_STATE_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "loading-state.tsx"
)


ERROR_STATE_CONTRACT = (
    DOCS
    / "frontend_error_state_contract.json"
)

LOADING_STATE_CONTRACT = (
    DOCS
    / "frontend_loading_state_contract.json"
)

CONSISTENCY_CONTRACT = (
    DOCS
    / "frontend_reusable_ui_consistency_contract.json"
)


OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_7_final_verification.json"
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
    failures: list[str],
) -> None:

    dependencies = contract.get(
        "dependency_identity",
        {},
    )


    check(
        "10.7.15 dependency identity exists",
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
                "Dependency current: "
                f"{Path(path_text).name}"
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
        "FixtureIQ Stage 10.7.13 - 10.7.15"
    )

    print(
        "FINAL REUSABLE FOOTBALL UI VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        VERIFY_1_4_FILE,
        VERIFY_5_8_FILE,
        VERIFY_9_12_FILE,
        ERROR_STATE_FILE,
        LOADING_STATE_FILE,
        ERROR_STATE_CONTRACT,
        LOADING_STATE_CONTRACT,
        CONSISTENCY_CONTRACT,
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


    verify_1_4 = load_json(
        VERIFY_1_4_FILE
    )

    verify_5_8 = load_json(
        VERIFY_5_8_FILE
    )

    verify_9_12 = load_json(
        VERIFY_9_12_FILE
    )

    error_contract = load_json(
        ERROR_STATE_CONTRACT
    )

    loading_contract = load_json(
        LOADING_STATE_CONTRACT
    )

    consistency_contract = load_json(
        CONSISTENCY_CONTRACT
    )


    error_source = (
        ERROR_STATE_FILE.read_text(
            encoding="utf-8"
        )
    )

    loading_source = (
        LOADING_STATE_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. COMPLETE 10.7 VERIFICATION CHAIN"
    )


    previous_blocks = [
        (
            "10.7.1-10.7.4",
            verify_1_4,
            range(
                1,
                5,
            ),
        ),
        (
            "10.7.5-10.7.8",
            verify_5_8,
            range(
                5,
                9,
            ),
        ),
        (
            "10.7.9-10.7.12",
            verify_9_12,
            range(
                9,
                13,
            ),
        ),
    ]


    for label, payload, stages in previous_blocks:

        check(
            f"{label} verification PASS",
            payload.get(
                "status"
            )
            ==
            "PASS",
            failures,
        )


        for stage in stages:

            check(
                f"10.7.{stage} complete",
                payload.get(
                    f"stage_10_7_{stage}_complete"
                )
                is True,
                failures,
            )


    check(
        "10.7.12 authorized 10.7.13",
        verify_9_12.get(
            "stage10_ready_for_10_7_13"
        )
        is True,
        failures,
    )


    print(
        "\n3. STAGE 10.7.13 ERRORSTATE"
    )


    check(
        "10.7.13 stage exact",
        error_contract.get(
            "stage"
        )
        ==
        "10.7.13",
        failures,
    )


    check(
        "10.7.13 LOCKED",
        error_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "ErrorState export",
        "export function ErrorState"
        in
        error_source,
        failures,
    )


    check(
        "ErrorState marker",
        (
            'data-fixtureiq-component="error-state"'
            in
            error_source
        ),
        failures,
    )


    check(
        "ErrorState uses alert role",
        'role="alert"'
        in
        error_source,
        failures,
    )


    check(
        "Error title direct",
        "{title}"
        in
        error_source,
        failures,
    )


    check(
        "Error message direct",
        "{message}"
        in
        error_source,
        failures,
    )


    check(
        "Optional action direct",
        (
            "action?"
            in
            error_source
            and
            "{action}"
            in
            error_source
        ),
        failures,
    )


    error_forbidden = [
        "fetch(",
        "onClick",
        "useState",
        "useEffect",
        "localStorage",
        "sessionStorage",
        "previousData",
        "fallbackData",
    ]


    for forbidden in error_forbidden:

        check(
            f"ErrorState excludes runtime logic: {forbidden}",
            forbidden.lower()
            not in
            error_source.lower(),
            failures,
        )


    check(
        "ErrorState SHA exact",
        error_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            ERROR_STATE_FILE
        ),
        failures,
    )


    print(
        "\n4. STAGE 10.7.14 LOADINGSTATE"
    )


    check(
        "10.7.14 stage exact",
        loading_contract.get(
            "stage"
        )
        ==
        "10.7.14",
        failures,
    )


    check(
        "10.7.14 LOCKED",
        loading_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "LoadingState export",
        "export function LoadingState"
        in
        loading_source,
        failures,
    )


    check(
        "LoadingState marker",
        (
            'data-fixtureiq-component="loading-state"'
            in
            loading_source
        ),
        failures,
    )


    check(
        "LoadingState role=status",
        'role="status"'
        in
        loading_source,
        failures,
    )


    check(
        "LoadingState aria-live polite",
        'aria-live="polite"'
        in
        loading_source,
        failures,
    )


    check(
        "LoadingState aria-busy",
        'aria-busy="true"'
        in
        loading_source,
        failures,
    )


    check(
        "Loading label direct",
        "{label}"
        in
        loading_source,
        failures,
    )


    loading_forbidden = [
        "fetch(",
        "setTimeout",
        "setInterval",
        "useState",
        "useEffect",
        "Date.now",
        "localStorage",
        "sessionStorage",
    ]


    for forbidden in loading_forbidden:

        check(
            f"LoadingState excludes runtime logic: {forbidden}",
            forbidden.lower()
            not in
            loading_source.lower(),
            failures,
        )


    check(
        "LoadingState SHA exact",
        loading_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            LOADING_STATE_FILE
        ),
        failures,
    )


    print(
        "\n5. STAGE 10.7.15 CONSISTENCY CONTRACT"
    )


    check(
        "10.7.15 stage exact",
        consistency_contract.get(
            "stage"
        )
        ==
        "10.7.15",
        failures,
    )


    check(
        "Consistency contract locked pending verification",
        consistency_contract.get(
            "status"
        )
        ==
        "LOCKED_PENDING_VERIFICATION",
        failures,
    )


    check(
        "Expected reusable component count = 14",
        consistency_contract.get(
            "expected_component_count"
        )
        ==
        14,
        failures,
    )


    components = consistency_contract.get(
        "components",
        {},
    )


    check(
        "Consistency component map has 14 entries",
        isinstance(
            components,
            dict,
        )
        and
        len(
            components
        )
        ==
        14,
        failures,
    )


    expected_names = {
        "MatchCard",
        "ProbabilityBar",
        "OutcomeBadge",
        "ConfidenceBadge",
        "UncertaintyBadge",
        "ContextAlignmentBadge",
        "ContextScore",
        "TeamComparisonRow",
        "RecentFormDisplay",
        "IntelligenceExplanation",
        "FreshnessIndicator",
        "EmptyState",
        "ErrorState",
        "LoadingState",
    }


    check(
        "Exact reusable component set",
        isinstance(
            components,
            dict,
        )
        and
        set(
            components.keys()
        )
        ==
        expected_names,
        failures,
    )


    print(
        "\n6. COMPONENT + CONTRACT IDENTITY"
    )


    reusable_sources: list[str] = []


    if isinstance(
        components,
        dict,
    ):

        for name in sorted(
            components.keys()
        ):

            declaration = components.get(
                name,
            )


            if not isinstance(
                declaration,
                dict,
            ):

                check(
                    f"{name} declaration valid",
                    False,
                    failures,
                )

                continue


            try:

                source = resolve_project_path(
                    declaration[
                        "source"
                    ]
                )

                contract = resolve_project_path(
                    declaration[
                        "contract"
                    ]
                )

                source_exists = (
                    source.exists()
                )

                contract_exists = (
                    contract.exists()
                )


                check(
                    f"{name} source exists",
                    source_exists,
                    failures,
                )

                check(
                    f"{name} contract exists",
                    contract_exists,
                    failures,
                )


                if (
                    source_exists
                    and
                    contract_exists
                ):

                    source_sha = sha256_file(
                        source
                    )

                    contract_sha = sha256_file(
                        contract
                    )


                    check(
                        f"{name} source SHA current",
                        declaration.get(
                            "component_sha256"
                        )
                        ==
                        source_sha,
                        failures,
                    )


                    check(
                        f"{name} contract SHA current",
                        declaration.get(
                            "contract_sha256"
                        )
                        ==
                        contract_sha,
                        failures,
                    )


                    contract_payload = load_json(
                        contract
                    )


                    check(
                        f"{name} contract component SHA agrees",
                        contract_payload.get(
                            "component_sha256"
                        )
                        ==
                        source_sha,
                        failures,
                    )


                    reusable_sources.append(
                        source.read_text(
                            encoding="utf-8"
                        )
                    )

            except Exception:

                check(
                    f"{name} identity readable",
                    False,
                    failures,
                )


    print(
        "\n7. GLOBAL REUSABLE UI SAFETY"
    )


    combined = "\n".join(
        reusable_sources
    )


    check(
        "No direct fetch",
        re.search(
            r"\bfetch\s*\(",
            combined,
        )
        is None,
        failures,
    )


    check(
        "No client component directives",
        (
            '"use client"'
            not in
            combined
            and
            "'use client'"
            not in
            combined
        ),
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
    ]:

        check(
            f"Reusable UI excludes {term}",
            term.lower()
            not in
            combined.lower(),
            failures,
        )


    check(
        "No frontend argmax",
        "Math.max"
        not in
        combined,
        failures,
    )


    check(
        "No probability recalibration",
        "recalibr"
        not in
        combined.lower(),
        failures,
    )


    check(
        "No model execution imports",
        (
            "sklearn"
            not in
            combined.lower()
            and
            "joblib"
            not in
            combined.lower()
        ),
        failures,
    )


    check(
        "No explanation generation",
        (
            "openai"
            not in
            combined.lower()
            and
            "llm"
            not in
            combined.lower()
        ),
        failures,
    )


    print(
        "\n8. COMPONENT MARKER CONSISTENCY"
    )


    expected_markers = {
        "match-card",
        "probability-bar",
        "outcome-badge",
        "confidence-badge",
        "uncertainty-badge",
        "context-alignment-badge",
        "context-score",
        "team-comparison-row",
        "recent-form-display",
        "intelligence-explanation",
        "freshness-indicator",
        "empty-state",
        "error-state",
        "loading-state",
    }


    discovered_markers = set(
        re.findall(
            (
                r'data-fixtureiq-component='
                r'"([^"]+)"'
            ),
            combined,
        )
    )


    check(
        "Exact reusable component markers",
        discovered_markers
        ==
        expected_markers,
        failures,
    )


    print(
        "\n9. CONSISTENCY RULES"
    )


    rules = consistency_contract.get(
        "consistency_rules",
        {},
    )


    expected_true = [
        "stage10_presentation_only",
        "server_safe_by_default",
    ]


    for key in expected_true:

        check(
            f"Consistency rule true: {key}",
            rules.get(
                key
            )
            is True,
            failures,
        )


    expected_false = [
        "direct_provider_access",
        "direct_artifact_access",
        "direct_fetch",
        "probability_recalculation",
        "prediction_derivation",
        "context_recalculation",
        "explanation_generation",
        "frontend_freshness_derivation",
        "built_in_retry_logic",
    ]


    for key in expected_false:

        check(
            f"Consistency rule false: {key}",
            rules.get(
                key
            )
            is False,
            failures,
        )


    print(
        "\n10. DEPENDENCY FRESHNESS"
    )


    verify_dependencies(
        consistency_contract,
        failures,
    )


    print(
        "\n11. TYPESCRIPT"
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
        "\n12. PRODUCTION BUILD"
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
        "\n13. NO PREMATURE STAGE 10 PROMOTION"
    )


    check(
        "10.7.13 did not self-promote",
        error_contract.get(
            "promotion",
            {},
        ).get(
            "stage10_7_13_complete"
        )
        is False,
        failures,
    )


    check(
        "10.7.14 did not self-promote",
        loading_contract.get(
            "promotion",
            {},
        ).get(
            "stage10_7_14_complete"
        )
        is False,
        failures,
    )


    check(
        "10.7.15 contract did not self-promote",
        consistency_contract.get(
            "promotion",
            {},
        ).get(
            "stage10_7_15_complete"
        )
        is False,
        failures,
    )


    check(
        "Stage 10 not promoted by reusable UI",
        consistency_contract.get(
            "promotion",
            {},
        ).get(
            "stage10_complete"
        )
        is False,
        failures,
    )


    print(
        "\n14. FINAL STAGE 10.7 DECISION"
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
                "10.7.15",

            "name":
                "REUSABLE_FOOTBALL_UI_FINAL_VERIFICATION",

            "status":
                "PASS",

            "stage_10_7_1_complete":
                True,

            "stage_10_7_2_complete":
                True,

            "stage_10_7_3_complete":
                True,

            "stage_10_7_4_complete":
                True,

            "stage_10_7_5_complete":
                True,

            "stage_10_7_6_complete":
                True,

            "stage_10_7_7_complete":
                True,

            "stage_10_7_8_complete":
                True,

            "stage_10_7_9_complete":
                True,

            "stage_10_7_10_complete":
                True,

            "stage_10_7_11_complete":
                True,

            "stage_10_7_12_complete":
                True,

            "stage_10_7_13_complete":
                True,

            "stage_10_7_14_complete":
                True,

            "stage_10_7_15_complete":
                True,

            "component_count":
                14,

            "consistency":
                "VERIFIED",

            "integrity": {
                "stage7_prediction_authority_preserved":
                    True,

                "stage8_context_authority_preserved":
                    True,

                "stage9_intelligence_authority_preserved":
                    True,

                "stage10_presentation_only":
                    True,

                "direct_fetch":
                    False,

                "provider_access":
                    False,

                "artifact_access":
                    False,

                "model_execution":
                    False,

                "probability_recalculation":
                    False,

                "frontend_argmax":
                    False,

                "context_recalculation":
                    False,

                "explanation_generation":
                    False,

                "frontend_freshness_derivation":
                    False,

                "built_in_retry_logic":
                    False,
            },

            "typescript_compiler":
                "PASS",

            "production_build":
                "PASS",

            "stage10_7_complete":
                True,

            "stage10_ready_for_10_8_1":
                True,

            "stage10_complete":
                False,

            "next_stage":
                "10.8.1",

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
            "STAGE 10.7.13: PASS"
        )

        print(
            "ERRORSTATE: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.7.14: PASS"
        )

        print(
            "LOADINGSTATE: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.7.15: PASS"
        )

        print(
            "REUSABLE UI CONSISTENCY: VERIFIED"
        )

        print()

        print(
            "STAGE 10.7: COMPLETE"
        )

        print(
            "STAGE 10 READY FOR 10.8.1"
        )

        print()

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.7.13 - 10.7.15: FAIL"
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
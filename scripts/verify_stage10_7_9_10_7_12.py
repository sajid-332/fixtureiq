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

DOCS = ROOT / "docs" / "stage10"

FRONTEND_DATA = (
    ROOT
    / "data"
    / "processed"
    / "frontend"
)


PREVIOUS_FILE = (
    FRONTEND_DATA
    / "stage10_7_5_10_7_8_verification.json"
)


UNCERTAINTY_BADGE_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "uncertainty-badge.tsx"
)

CONTEXT_ALIGNMENT_BADGE_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "context-alignment-badge.tsx"
)

CONTEXT_SCORE_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "context-score.tsx"
)

TEAM_COMPARISON_ROW_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "team-comparison-row.tsx"
)


RECENT_FORM_DISPLAY_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "recent-form-display.tsx"
)

INTELLIGENCE_EXPLANATION_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "intelligence-explanation.tsx"
)

FRESHNESS_INDICATOR_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "freshness-indicator.tsx"
)

EMPTY_STATE_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "empty-state.tsx"
)


RESULT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "result.ts"
)


UNCERTAINTY_CONTRACT_FILE = (
    DOCS
    / "frontend_uncertainty_badge_contract.json"
)

ALIGNMENT_CONTRACT_FILE = (
    DOCS
    / "frontend_context_alignment_badge_contract.json"
)

CONTEXT_SCORE_CONTRACT_FILE = (
    DOCS
    / "frontend_context_score_contract.json"
)

TEAM_COMPARISON_CONTRACT_FILE = (
    DOCS
    / "frontend_team_comparison_row_contract.json"
)


RECENT_FORM_CONTRACT_FILE = (
    DOCS
    / "frontend_recent_form_display_contract.json"
)

INTELLIGENCE_EXPLANATION_CONTRACT_FILE = (
    DOCS
    / "frontend_intelligence_explanation_contract.json"
)

FRESHNESS_INDICATOR_CONTRACT_FILE = (
    DOCS
    / "frontend_freshness_indicator_contract.json"
)

EMPTY_STATE_CONTRACT_FILE = (
    DOCS
    / "frontend_empty_state_contract.json"
)


OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_7_9_10_7_12_verification.json"
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


def run_typescript() -> tuple[
    bool,
    str,
]:

    npm = (
        shutil.which(
            "npm.cmd"
        )
        or
        shutil.which(
            "npm"
        )
    )


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


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.7.9 - 10.7.12"
    )

    print(
        "REUSABLE FORM + EXPLANATION + FRESHNESS + EMPTY UI VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        PREVIOUS_FILE,
        UNCERTAINTY_BADGE_FILE,
        CONTEXT_ALIGNMENT_BADGE_FILE,
        CONTEXT_SCORE_FILE,
        TEAM_COMPARISON_ROW_FILE,
        RECENT_FORM_DISPLAY_FILE,
        INTELLIGENCE_EXPLANATION_FILE,
        FRESHNESS_INDICATOR_FILE,
        EMPTY_STATE_FILE,
        RESULT_FILE,
        UNCERTAINTY_CONTRACT_FILE,
        ALIGNMENT_CONTRACT_FILE,
        CONTEXT_SCORE_CONTRACT_FILE,
        TEAM_COMPARISON_CONTRACT_FILE,
        RECENT_FORM_CONTRACT_FILE,
        INTELLIGENCE_EXPLANATION_CONTRACT_FILE,
        FRESHNESS_INDICATOR_CONTRACT_FILE,
        EMPTY_STATE_CONTRACT_FILE,
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

    uncertainty_contract = load_json(
        UNCERTAINTY_CONTRACT_FILE
    )

    alignment_contract = load_json(
        ALIGNMENT_CONTRACT_FILE
    )

    score_contract = load_json(
        CONTEXT_SCORE_CONTRACT_FILE
    )

    comparison_contract = load_json(
        TEAM_COMPARISON_CONTRACT_FILE
    )

    recent_contract = load_json(
        RECENT_FORM_CONTRACT_FILE
    )

    explanation_contract = load_json(
        INTELLIGENCE_EXPLANATION_CONTRACT_FILE
    )

    freshness_contract = load_json(
        FRESHNESS_INDICATOR_CONTRACT_FILE
    )

    empty_contract = load_json(
        EMPTY_STATE_CONTRACT_FILE
    )


    recent_source = (
        RECENT_FORM_DISPLAY_FILE.read_text(
            encoding="utf-8"
        )
    )

    explanation_source = (
        INTELLIGENCE_EXPLANATION_FILE.read_text(
            encoding="utf-8"
        )
    )

    freshness_source = (
        FRESHNESS_INDICATOR_FILE.read_text(
            encoding="utf-8"
        )
    )

    empty_source = (
        EMPTY_STATE_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. STAGE 10.7.5 - 10.7.8 FOUNDATION"
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
        "stage_10_7_5_complete",
        "stage_10_7_6_complete",
        "stage_10_7_7_complete",
        "stage_10_7_8_complete",
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
        "10.7.8 authorized 10.7.9",
        previous.get(
            "stage10_ready_for_10_7_9"
        )
        is True,
        failures,
    )


    print(
        "\n3. PREVIOUS COMPONENT PROTECTION"
    )


    check(
        "UncertaintyBadge unchanged",
        uncertainty_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            UNCERTAINTY_BADGE_FILE
        ),
        failures,
    )


    check(
        "ContextAlignmentBadge unchanged",
        alignment_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            CONTEXT_ALIGNMENT_BADGE_FILE
        ),
        failures,
    )


    check(
        "ContextScore unchanged",
        score_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            CONTEXT_SCORE_FILE
        ),
        failures,
    )


    check(
        "TeamComparisonRow unchanged",
        comparison_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            TEAM_COMPARISON_ROW_FILE
        ),
        failures,
    )


    print(
        "\n4. STAGE 10.7.9 RECENTFORMDISPLAY"
    )


    check(
        "10.7.9 stage exact",
        recent_contract.get(
            "stage"
        )
        ==
        "10.7.9",
        failures,
    )


    check(
        "10.7.9 LOCKED",
        recent_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "RecentFormDisplay export",
        "export function RecentFormDisplay"
        in
        recent_source,
        failures,
    )


    check(
        "RecentFormDisplay marker",
        (
            'data-fixtureiq-component="recent-form-display"'
            in
            recent_source
        ),
        failures,
    )


    check(
        "Results displayed directly",
        "{results || \"No results\"}"
        in
        recent_source,
        failures,
    )


    check(
        "Matches available displayed directly",
        "{matchesAvailable} matches available"
        in
        recent_source,
        failures,
    )


    for forbidden in [
        ".reduce(",
        ".filter(",
        ".sort(",
        "wins * 3",
        "draws",
        "points",
        "score",
    ]:

        check(
            f"No form derivation: {forbidden}",
            forbidden.lower()
            not in
            recent_source.lower(),
            failures,
        )


    check(
        "RecentFormDisplay SHA exact",
        recent_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            RECENT_FORM_DISPLAY_FILE
        ),
        failures,
    )


    print(
        "\n5. STAGE 10.7.10 INTELLIGENCEEXPLANATION"
    )


    check(
        "10.7.10 stage exact",
        explanation_contract.get(
            "stage"
        )
        ==
        "10.7.10",
        failures,
    )


    check(
        "10.7.10 LOCKED",
        explanation_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "IntelligenceExplanation export",
        "export function IntelligenceExplanation"
        in
        explanation_source,
        failures,
    )


    check(
        "Explanation marker",
        (
            'data-fixtureiq-component="intelligence-explanation"'
            in
            explanation_source
        ),
        failures,
    )


    check(
        "Headline direct",
        "{headline}"
        in
        explanation_source,
        failures,
    )


    check(
        "Summary direct",
        "{summary}"
        in
        explanation_source,
        failures,
    )


    for forbidden in [
        ".slice(",
        ".substring(",
        ".replace(",
        "truncate",
        "fallback",
        "generate",
        "openai",
        "llm",
    ]:

        check(
            f"No explanation mutation: {forbidden}",
            forbidden.lower()
            not in
            explanation_source.lower(),
            failures,
        )


    check(
        "Explanation SHA exact",
        explanation_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            INTELLIGENCE_EXPLANATION_FILE
        ),
        failures,
    )


    print(
        "\n6. STAGE 10.7.11 FRESHNESSINDICATOR"
    )


    check(
        "10.7.11 stage exact",
        freshness_contract.get(
            "stage"
        )
        ==
        "10.7.11",
        failures,
    )


    check(
        "10.7.11 LOCKED",
        freshness_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "ApiTerminalState used",
        "ApiTerminalState"
        in
        freshness_source,
        failures,
    )


    check(
        "FreshnessIndicator export",
        "export function FreshnessIndicator"
        in
        freshness_source,
        failures,
    )


    check(
        "FreshnessIndicator marker",
        (
            'data-fixtureiq-component="freshness-indicator"'
            in
            freshness_source
        ),
        failures,
    )


    check(
        "State direct display",
        "{state}"
        in
        freshness_source,
        failures,
    )


    check(
        "Null HTTP status supported",
        (
            "httpStatus === null"
            in
            freshness_source
            and
            "No HTTP response"
            in
            freshness_source
        ),
        failures,
    )


    freshness_forbidden = [
        "Date.now",
        "new Date",
        "setInterval",
        "setTimeout",
        "ttl",
        "expires",
        "generated_at",
        "last_updated",
        "localStorage",
        "sessionStorage",
    ]


    for forbidden in freshness_forbidden:

        check(
            f"No frontend freshness derivation: {forbidden}",
            forbidden.lower()
            not in
            freshness_source.lower(),
            failures,
        )


    check(
        "FreshnessIndicator SHA exact",
        freshness_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            FRESHNESS_INDICATOR_FILE
        ),
        failures,
    )


    print(
        "\n7. STAGE 10.7.12 EMPTYSTATE"
    )


    check(
        "10.7.12 stage exact",
        empty_contract.get(
            "stage"
        )
        ==
        "10.7.12",
        failures,
    )


    check(
        "10.7.12 LOCKED",
        empty_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "ReactNode optional action used",
        (
            "ReactNode"
            in
            empty_source
            and
            "action?"
            in
            empty_source
        ),
        failures,
    )


    check(
        "EmptyState export",
        "export function EmptyState"
        in
        empty_source,
        failures,
    )


    check(
        "EmptyState marker",
        (
            'data-fixtureiq-component="empty-state"'
            in
            empty_source
        ),
        failures,
    )


    check(
        "Title direct",
        "{title}"
        in
        empty_source,
        failures,
    )


    check(
        "Message direct",
        "{message}"
        in
        empty_source,
        failures,
    )


    check(
        "Optional action direct",
        "{action}"
        in
        empty_source,
        failures,
    )


    for forbidden in [
        "fetch(",
        "retry",
        "previousData",
        "fallbackData",
        "localStorage",
        "sessionStorage",
    ]:

        check(
            f"EmptyState excludes runtime logic: {forbidden}",
            forbidden.lower()
            not in
            empty_source.lower(),
            failures,
        )


    check(
        "EmptyState SHA exact",
        empty_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            EMPTY_STATE_FILE
        ),
        failures,
    )


    print(
        "\n8. PRESENTATION / SAFETY BOUNDARY"
    )


    combined = "\n".join(
        [
            recent_source,
            explanation_source,
            freshness_source,
            empty_source,
        ]
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


    check(
        "No direct fetch",
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
    ]:

        check(
            f"UI sources exclude {term}",
            term.lower()
            not in
            combined.lower(),
            failures,
        )


    print(
        "\n9. 10.7.13+ NOT IMPLEMENTED EARLY"
    )


    for filename in [
        "error-state.tsx",
        "loading-state.tsx",
    ]:

        path = (
            FRONTEND
            / "components"
            / "ui"
            / filename
        )


        check(
            f"Future component absent: {filename}",
            not path.exists(),
            failures,
        )


    print(
        "\n10. PROTECTED STATE"
    )


    protected = empty_contract.get(
        "protected_state",
        {},
    )


    protected_sources = [
        (
            "UncertaintyBadge",
            UNCERTAINTY_BADGE_FILE,
            "uncertainty_badge_sha256",
        ),
        (
            "ContextAlignmentBadge",
            CONTEXT_ALIGNMENT_BADGE_FILE,
            "context_alignment_badge_sha256",
        ),
        (
            "ContextScore",
            CONTEXT_SCORE_FILE,
            "context_score_sha256",
        ),
        (
            "TeamComparisonRow",
            TEAM_COMPARISON_ROW_FILE,
            "team_comparison_row_sha256",
        ),
        (
            "API result mapping",
            RESULT_FILE,
            "result_mapping_sha256",
        ),
    ]


    for label, path, key in protected_sources:

        check(
            f"{label} unchanged",
            protected.get(
                key
            )
            ==
            sha256_file(
                path
            ),
            failures,
        )


    print(
        "\n11. DEPENDENCY FRESHNESS"
    )


    for stage, contract in [
        (
            "10.7.9",
            recent_contract,
        ),
        (
            "10.7.10",
            explanation_contract,
        ),
        (
            "10.7.11",
            freshness_contract,
        ),
        (
            "10.7.12",
            empty_contract,
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
        "\n13. NO PREMATURE PROMOTION"
    )


    for stage, contract, key in [
        (
            "10.7.9",
            recent_contract,
            "stage10_7_9_complete",
        ),
        (
            "10.7.10",
            explanation_contract,
            "stage10_7_10_complete",
        ),
        (
            "10.7.11",
            freshness_contract,
            "stage10_7_11_complete",
        ),
        (
            "10.7.12",
            empty_contract,
            "stage10_7_12_complete",
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
            f"{stage}: Stage 10.7 incomplete",
            promotion.get(
                "stage10_7_complete"
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
        "\n14. SAVE VERIFICATION"
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
                "10.7.9-10.7.12",

            "name":
                "REUSABLE_FORM_EXPLANATION_FRESHNESS_EMPTY_UI_VERIFICATION",

            "status":
                "PASS",

            "stage_10_7_9_complete":
                True,

            "stage_10_7_10_complete":
                True,

            "stage_10_7_11_complete":
                True,

            "stage_10_7_12_complete":
                True,

            "recent_form_display":
                "LOCKED_AND_VERIFIED",

            "intelligence_explanation":
                "LOCKED_AND_VERIFIED",

            "freshness_indicator":
                "LOCKED_AND_VERIFIED",

            "empty_state":
                "LOCKED_AND_VERIFIED",

            "integrity": {
                "stage8_form_authority_preserved":
                    True,

                "stage9_explanation_authority_preserved":
                    True,

                "backend_freshness_authority_preserved":
                    True,

                "stage10_presentation_only":
                    True,

                "form_recalculation":
                    False,

                "explanation_generation":
                    False,

                "explanation_rewriting":
                    False,

                "frontend_freshness_calculation":
                    False,

                "empty_state_data_logic":
                    False,

                "direct_fetch":
                    False,

                "provider_access":
                    False,

                "artifact_access":
                    False,
            },

            "typescript_compiler":
                "PASS",

            "stage10_ready_for_10_7_13":
                True,

            "stage10_7_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.7.13",

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
            "STAGE 10.7.9: PASS"
        )

        print(
            "RECENTFORMDISPLAY: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.7.10: PASS"
        )

        print(
            "INTELLIGENCEEXPLANATION: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.7.11: PASS"
        )

        print(
            "FRESHNESSINDICATOR: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.7.12: PASS"
        )

        print(
            "EMPTYSTATE: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.7.13"
        )

        print(
            "STAGE 10.7 IS NOT YET COMPLETE"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.7.9 - 10.7.12: FAIL"
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
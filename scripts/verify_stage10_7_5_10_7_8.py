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
    / "stage10_7_1_10_7_4_verification.json"
)


PROBABILITY_BAR_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "probability-bar.tsx"
)

OUTCOME_BADGE_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "outcome-badge.tsx"
)

CONFIDENCE_BADGE_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "confidence-badge.tsx"
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


DOMAIN_TYPES_FILE = (
    FRONTEND
    / "lib"
    / "domain"
    / "types.ts"
)


PROBABILITY_BAR_CONTRACT_FILE = (
    DOCS
    / "frontend_probability_bar_contract.json"
)

OUTCOME_BADGE_CONTRACT_FILE = (
    DOCS
    / "frontend_outcome_badge_contract.json"
)

CONFIDENCE_BADGE_CONTRACT_FILE = (
    DOCS
    / "frontend_confidence_badge_contract.json"
)

UNCERTAINTY_BADGE_CONTRACT_FILE = (
    DOCS
    / "frontend_uncertainty_badge_contract.json"
)

CONTEXT_ALIGNMENT_BADGE_CONTRACT_FILE = (
    DOCS
    / "frontend_context_alignment_badge_contract.json"
)

CONTEXT_SCORE_CONTRACT_FILE = (
    DOCS
    / "frontend_context_score_contract.json"
)

TEAM_COMPARISON_ROW_CONTRACT_FILE = (
    DOCS
    / "frontend_team_comparison_row_contract.json"
)


OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_7_5_10_7_8_verification.json"
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
        "FixtureIQ Stage 10.7.5 - 10.7.8"
    )

    print(
        "REUSABLE INTELLIGENCE + TEAM COMPARISON UI VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        PREVIOUS_FILE,
        PROBABILITY_BAR_FILE,
        OUTCOME_BADGE_FILE,
        CONFIDENCE_BADGE_FILE,
        UNCERTAINTY_BADGE_FILE,
        CONTEXT_ALIGNMENT_BADGE_FILE,
        CONTEXT_SCORE_FILE,
        TEAM_COMPARISON_ROW_FILE,
        DOMAIN_TYPES_FILE,
        PROBABILITY_BAR_CONTRACT_FILE,
        OUTCOME_BADGE_CONTRACT_FILE,
        CONFIDENCE_BADGE_CONTRACT_FILE,
        UNCERTAINTY_BADGE_CONTRACT_FILE,
        CONTEXT_ALIGNMENT_BADGE_CONTRACT_FILE,
        CONTEXT_SCORE_CONTRACT_FILE,
        TEAM_COMPARISON_ROW_CONTRACT_FILE,
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

    probability_contract = load_json(
        PROBABILITY_BAR_CONTRACT_FILE
    )

    outcome_contract = load_json(
        OUTCOME_BADGE_CONTRACT_FILE
    )

    confidence_contract = load_json(
        CONFIDENCE_BADGE_CONTRACT_FILE
    )

    uncertainty_contract = load_json(
        UNCERTAINTY_BADGE_CONTRACT_FILE
    )

    alignment_contract = load_json(
        CONTEXT_ALIGNMENT_BADGE_CONTRACT_FILE
    )

    score_contract = load_json(
        CONTEXT_SCORE_CONTRACT_FILE
    )

    comparison_contract = load_json(
        TEAM_COMPARISON_ROW_CONTRACT_FILE
    )


    uncertainty_source = (
        UNCERTAINTY_BADGE_FILE.read_text(
            encoding="utf-8"
        )
    )

    alignment_source = (
        CONTEXT_ALIGNMENT_BADGE_FILE.read_text(
            encoding="utf-8"
        )
    )

    score_source = (
        CONTEXT_SCORE_FILE.read_text(
            encoding="utf-8"
        )
    )

    comparison_source = (
        TEAM_COMPARISON_ROW_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. STAGE 10.7.1 - 10.7.4 FOUNDATION"
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
        "stage_10_7_1_complete",
        "stage_10_7_2_complete",
        "stage_10_7_3_complete",
        "stage_10_7_4_complete",
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
        "10.7.4 authorized 10.7.5",
        previous.get(
            "stage10_ready_for_10_7_5"
        )
        is True,
        failures,
    )


    print(
        "\n3. PREVIOUS COMPONENT PROTECTION"
    )


    check(
        "ProbabilityBar unchanged",
        probability_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            PROBABILITY_BAR_FILE
        ),
        failures,
    )


    check(
        "OutcomeBadge unchanged",
        outcome_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            OUTCOME_BADGE_FILE
        ),
        failures,
    )


    check(
        "ConfidenceBadge unchanged",
        confidence_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            CONFIDENCE_BADGE_FILE
        ),
        failures,
    )


    print(
        "\n4. STAGE 10.7.5 UNCERTAINTYBADGE"
    )


    check(
        "10.7.5 stage exact",
        uncertainty_contract.get(
            "stage"
        )
        ==
        "10.7.5",
        failures,
    )


    check(
        "10.7.5 LOCKED",
        uncertainty_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "UncertaintyBand used",
        "UncertaintyBand"
        in
        uncertainty_source,
        failures,
    )


    check(
        "UncertaintyBadge export",
        "export function UncertaintyBadge"
        in
        uncertainty_source,
        failures,
    )


    check(
        "UncertaintyBadge marker",
        (
            'data-fixtureiq-component="uncertainty-badge"'
            in
            uncertainty_source
        ),
        failures,
    )


    check(
        "Uncertainty band direct display",
        "{band}"
        in
        uncertainty_source,
        failures,
    )


    threshold_patterns = [
        r"band\s*[<>]=?",
        r"value\s*[<>]=?",
        r"0\.4",
        r"0\.5",
        r"0\.6",
        r"0\.7",
        r"Math\.log",
    ]


    check(
        "No uncertainty threshold/entropy logic",
        all(
            re.search(
                pattern,
                uncertainty_source,
            )
            is None

            for pattern in threshold_patterns
        ),
        failures,
    )


    check(
        "UncertaintyBadge SHA exact",
        uncertainty_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            UNCERTAINTY_BADGE_FILE
        ),
        failures,
    )


    print(
        "\n5. STAGE 10.7.6 CONTEXTALIGNMENTBADGE"
    )


    check(
        "10.7.6 stage exact",
        alignment_contract.get(
            "stage"
        )
        ==
        "10.7.6",
        failures,
    )


    check(
        "10.7.6 LOCKED",
        alignment_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "ContextAlignment used",
        "ContextAlignment"
        in
        alignment_source,
        failures,
    )


    check(
        "ContextAlignmentBadge export",
        "export function ContextAlignmentBadge"
        in
        alignment_source,
        failures,
    )


    check(
        "Alignment component marker",
        (
            'data-fixtureiq-component="context-alignment-badge"'
            in
            alignment_source
        ),
        failures,
    )


    check(
        "Alignment direct display",
        "{alignment}"
        in
        alignment_source,
        failures,
    )


    for forbidden in [
        "stage9_context_support_score",
        "supportScore",
        "Math.abs",
        "SUPPORTIVE ?",
        "CONTRADICTORY ?",
    ]:

        check(
            f"No alignment derivation: {forbidden}",
            forbidden
            not in
            alignment_source,
            failures,
        )


    check(
        "ContextAlignmentBadge SHA exact",
        alignment_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            CONTEXT_ALIGNMENT_BADGE_FILE
        ),
        failures,
    )


    print(
        "\n6. STAGE 10.7.7 CONTEXTSCORE"
    )


    check(
        "10.7.7 stage exact",
        score_contract.get(
            "stage"
        )
        ==
        "10.7.7",
        failures,
    )


    check(
        "10.7.7 LOCKED",
        score_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "ContextSupportScore used",
        "ContextSupportScore"
        in
        score_source,
        failures,
    )


    check(
        "ContextScore export",
        "export function ContextScore"
        in
        score_source,
        failures,
    )


    check(
        "ContextScore marker",
        (
            'data-fixtureiq-component="context-score"'
            in
            score_source
        ),
        failures,
    )


    check(
        "Direct score data attribute",
        (
            "data-context-score"
            in
            score_source
            and
            "score"
            in
            score_source
        ),
        failures,
    )


    check(
        "Intl formatter used for display only",
        (
            "Intl.NumberFormat"
            in
            score_source
            and
            "signDisplay"
            in
            score_source
        ),
        failures,
    )


    for forbidden in [
        "Math.abs",
        "Math.max",
        "Math.min",
        "supportive",
        "contradictory",
        "neutral",
        "mixed",
    ]:

        check(
            f"ContextScore excludes derivation token: {forbidden}",
            forbidden.lower()
            not in
            score_source.lower(),
            failures,
        )


    check(
        "ContextScore SHA exact",
        score_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            CONTEXT_SCORE_FILE
        ),
        failures,
    )


    print(
        "\n7. STAGE 10.7.8 TEAMCOMPARISONROW"
    )


    check(
        "10.7.8 stage exact",
        comparison_contract.get(
            "stage"
        )
        ==
        "10.7.8",
        failures,
    )


    check(
        "10.7.8 LOCKED",
        comparison_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "ReactNode used",
        "ReactNode"
        in
        comparison_source,
        failures,
    )


    check(
        "TeamComparisonRow export",
        "export function TeamComparisonRow"
        in
        comparison_source,
        failures,
    )


    check(
        "TeamComparisonRow marker",
        (
            'data-fixtureiq-component="team-comparison-row"'
            in
            comparison_source
        ),
        failures,
    )


    for prop in [
        "label",
        "homeTeamName",
        "awayTeamName",
        "homeValue",
        "awayValue",
    ]:

        check(
            f"TeamComparisonRow preserves {prop}",
            prop
            in
            comparison_source,
            failures,
        )


    check(
        "Home value direct display",
        "{homeValue}"
        in
        comparison_source,
        failures,
    )


    check(
        "Away value direct display",
        "{awayValue}"
        in
        comparison_source,
        failures,
    )


    comparison_forbidden = [
        "Math.max",
        "Math.min",
        "Math.abs",
        "homeValue >",
        "homeValue <",
        "awayValue >",
        "awayValue <",
        "winner",
        "difference",
        ".sort(",
    ]


    for forbidden in comparison_forbidden:

        check(
            f"No comparison derivation: {forbidden}",
            forbidden.lower()
            not in
            comparison_source.lower(),
            failures,
        )


    check(
        "TeamComparisonRow SHA exact",
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
        "\n8. PRESENTATION / SAFETY BOUNDARY"
    )


    combined = "\n".join(
        [
            uncertainty_source,
            alignment_source,
            score_source,
            comparison_source,
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
        "\n9. 10.7.9+ NOT IMPLEMENTED EARLY"
    )


    future_files = [
        "recent-form-display.tsx",
        "intelligence-explanation.tsx",
        "freshness-indicator.tsx",
        "empty-state.tsx",
        "error-state.tsx",
        "loading-state.tsx",
    ]


    for filename in future_files:

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


    protected = comparison_contract.get(
        "protected_state",
        {},
    )


    protected_sources = [
        (
            "ProbabilityBar",
            PROBABILITY_BAR_FILE,
            "probability_bar_sha256",
        ),
        (
            "OutcomeBadge",
            OUTCOME_BADGE_FILE,
            "outcome_badge_sha256",
        ),
        (
            "ConfidenceBadge",
            CONFIDENCE_BADGE_FILE,
            "confidence_badge_sha256",
        ),
        (
            "Domain types",
            DOMAIN_TYPES_FILE,
            "domain_types_sha256",
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
            "10.7.5",
            uncertainty_contract,
        ),
        (
            "10.7.6",
            alignment_contract,
        ),
        (
            "10.7.7",
            score_contract,
        ),
        (
            "10.7.8",
            comparison_contract,
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
            "10.7.5",
            uncertainty_contract,
            "stage10_7_5_complete",
        ),
        (
            "10.7.6",
            alignment_contract,
            "stage10_7_6_complete",
        ),
        (
            "10.7.7",
            score_contract,
            "stage10_7_7_complete",
        ),
        (
            "10.7.8",
            comparison_contract,
            "stage10_7_8_complete",
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
                "10.7.5-10.7.8",

            "name":
                "REUSABLE_INTELLIGENCE_TEAM_COMPARISON_UI_VERIFICATION",

            "status":
                "PASS",

            "stage_10_7_5_complete":
                True,

            "stage_10_7_6_complete":
                True,

            "stage_10_7_7_complete":
                True,

            "stage_10_7_8_complete":
                True,

            "uncertainty_badge":
                "LOCKED_AND_VERIFIED",

            "context_alignment_badge":
                "LOCKED_AND_VERIFIED",

            "context_score":
                "LOCKED_AND_VERIFIED",

            "team_comparison_row":
                "LOCKED_AND_VERIFIED",

            "integrity": {
                "stage9_uncertainty_authority_preserved":
                    True,

                "stage9_context_alignment_authority_preserved":
                    True,

                "stage9_context_support_score_authority_preserved":
                    True,

                "stage10_presentation_only":
                    True,

                "uncertainty_threshold_logic":
                    False,

                "alignment_derivation":
                    False,

                "context_score_recalculation":
                    False,

                "team_value_comparison_logic":
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

            "stage10_ready_for_10_7_9":
                True,

            "stage10_7_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.7.9",

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
            "STAGE 10.7.5: PASS"
        )

        print(
            "UNCERTAINTYBADGE: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.7.6: PASS"
        )

        print(
            "CONTEXTALIGNMENTBADGE: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.7.7: PASS"
        )

        print(
            "CONTEXTSCORE: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.7.8: PASS"
        )

        print(
            "TEAMCOMPARISONROW: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.7.9"
        )

        print(
            "STAGE 10.7 IS NOT YET COMPLETE"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.7.5 - 10.7.8: FAIL"
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
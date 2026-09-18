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
    / "stage10_6_final_verification.json"
)


MATCH_CARD_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-card.tsx"
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


DOMAIN_TYPES_FILE = (
    FRONTEND
    / "lib"
    / "domain"
    / "types.ts"
)

PROBABILITY_FORMATTER_FILE = (
    FRONTEND
    / "lib"
    / "formatters"
    / "probability.ts"
)


MATCH_CARD_CONTRACT_FILE = (
    DOCS
    / "frontend_reusable_match_card_contract.json"
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


OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_7_1_10_7_4_verification.json"
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
        "FixtureIQ Stage 10.7.1 - 10.7.4"
    )

    print(
        "REUSABLE FOOTBALL UI FOUNDATION VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        PREVIOUS_FILE,
        MATCH_CARD_FILE,
        PROBABILITY_BAR_FILE,
        OUTCOME_BADGE_FILE,
        CONFIDENCE_BADGE_FILE,
        DOMAIN_TYPES_FILE,
        PROBABILITY_FORMATTER_FILE,
        MATCH_CARD_CONTRACT_FILE,
        PROBABILITY_BAR_CONTRACT_FILE,
        OUTCOME_BADGE_CONTRACT_FILE,
        CONFIDENCE_BADGE_CONTRACT_FILE,
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

    match_contract = load_json(
        MATCH_CARD_CONTRACT_FILE
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


    match_source = (
        MATCH_CARD_FILE.read_text(
            encoding="utf-8"
        )
    )

    probability_source = (
        PROBABILITY_BAR_FILE.read_text(
            encoding="utf-8"
        )
    )

    outcome_source = (
        OUTCOME_BADGE_FILE.read_text(
            encoding="utf-8"
        )
    )

    confidence_source = (
        CONFIDENCE_BADGE_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. STAGE 10.6 FOUNDATION"
    )


    check(
        "Stage 10.6 final PASS",
        previous.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )


    check(
        "Stage 10.6 COMPLETE",
        previous.get(
            "stage10_6_complete"
        )
        is True,
        failures,
    )


    check(
        "Stage 10 ready for 10.7.1",
        previous.get(
            "stage10_ready_for_10_7_1"
        )
        is True,
        failures,
    )


    print(
        "\n3. STAGE 10.7.1 MATCHCARD"
    )


    check(
        "10.7.1 stage exact",
        match_contract.get(
            "stage"
        )
        ==
        "10.7.1",
        failures,
    )


    check(
        "10.7.1 LOCKED",
        match_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Existing MatchCard retained",
        match_contract.get(
            "canonical_existing_component"
        )
        is True,
        failures,
    )


    check(
        "MatchCard export exists",
        "export function MatchCard"
        in
        match_source,
        failures,
    )


    check(
        "MatchCard component marker",
        (
            'data-fixtureiq-component="match-card"'
            in
            match_source
        ),
        failures,
    )


    for field in [
        "homeTeamName",
        "awayTeamName",
        "kickoffUtc",
        "stage7_prob_home_win",
        "stage7_prob_draw",
        "stage7_prob_away_win",
        "stage7_predicted_label",
        "stage7_confidence",
        "confidence_band",
        "uncertainty_band",
        "context_alignment",
        "explanation_headline",
        "explanation_summary",
    ]:

        check(
            f"MatchCard preserves {field}",
            field
            in
            match_source,
            failures,
        )


    check(
        "MatchCard SHA exact",
        match_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            MATCH_CARD_FILE
        ),
        failures,
    )


    print(
        "\n4. STAGE 10.7.2 PROBABILITYBAR"
    )


    check(
        "10.7.2 stage exact",
        probability_contract.get(
            "stage"
        )
        ==
        "10.7.2",
        failures,
    )


    check(
        "10.7.2 LOCKED",
        probability_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "ProbabilityBar export exists",
        "export function ProbabilityBar"
        in
        probability_source,
        failures,
    )


    check(
        "ProbabilityBar marker",
        (
            'data-fixtureiq-component="probability-bar"'
            in
            probability_source
        ),
        failures,
    )


    check(
        "Native progress used",
        "<progress"
        in
        probability_source,
        failures,
    )


    check(
        "Progress max is one",
        "max={1}"
        in
        probability_source,
        failures,
    )


    check(
        "Raw probability passed directly",
        re.search(
            r"value=\{\s*value\s*\}",
            probability_source,
        )
        is not None,
        failures,
    )


    check(
        "Existing probability formatter reused",
        (
            "formatProbability"
            in
            probability_source
        ),
        failures,
    )


    for forbidden in [
        "Math.max",
        "Math.min",
        "clamp",
        "normalize",
        "recalibr",
    ]:

        check(
            f"ProbabilityBar excludes {forbidden}",
            forbidden.lower()
            not in
            probability_source.lower(),
            failures,
        )


    check(
        "ProbabilityBar SHA exact",
        probability_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            PROBABILITY_BAR_FILE
        ),
        failures,
    )


    print(
        "\n5. STAGE 10.7.3 OUTCOMEBADGE"
    )


    check(
        "10.7.3 stage exact",
        outcome_contract.get(
            "stage"
        )
        ==
        "10.7.3",
        failures,
    )


    check(
        "10.7.3 LOCKED",
        outcome_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "OutcomeLabel domain type used",
        "OutcomeLabel"
        in
        outcome_source,
        failures,
    )


    check(
        "OutcomeBadge export exists",
        "export function OutcomeBadge"
        in
        outcome_source,
        failures,
    )


    check(
        "OutcomeBadge marker",
        (
            'data-fixtureiq-component="outcome-badge"'
            in
            outcome_source
        ),
        failures,
    )


    check(
        "Outcome displayed directly",
        "{outcome}"
        in
        outcome_source,
        failures,
    )


    check(
        "No frontend argmax",
        "Math.max"
        not in
        outcome_source,
        failures,
    )


    check(
        "No probability fields in OutcomeBadge",
        "stage7_prob_"
        not in
        outcome_source,
        failures,
    )


    check(
        "OutcomeBadge SHA exact",
        outcome_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            OUTCOME_BADGE_FILE
        ),
        failures,
    )


    print(
        "\n6. STAGE 10.7.4 CONFIDENCEBADGE"
    )


    check(
        "10.7.4 stage exact",
        confidence_contract.get(
            "stage"
        )
        ==
        "10.7.4",
        failures,
    )


    check(
        "10.7.4 LOCKED",
        confidence_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "ConfidenceBand domain type used",
        "ConfidenceBand"
        in
        confidence_source,
        failures,
    )


    check(
        "ConfidenceBadge export exists",
        "export function ConfidenceBadge"
        in
        confidence_source,
        failures,
    )


    check(
        "ConfidenceBadge marker",
        (
            'data-fixtureiq-component="confidence-badge"'
            in
            confidence_source
        ),
        failures,
    )


    check(
        "Confidence band displayed directly",
        "{band}"
        in
        confidence_source,
        failures,
    )


    threshold_patterns = [
        r"band\s*[<>]=?",
        r"value\s*[<>]=?",
        r"confidence\s*[<>]=?",
        r"0\.4",
        r"0\.5",
        r"0\.6",
        r"0\.7",
    ]


    check(
        "No confidence threshold logic",
        all(
            re.search(
                pattern,
                confidence_source,
            )
            is None

            for pattern in
            threshold_patterns
        ),
        failures,
    )


    check(
        "ConfidenceBadge SHA exact",
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
        "\n7. SERVER / PRESENTATION SAFETY"
    )


    combined = "\n".join(
        [
            match_source,
            probability_source,
            outcome_source,
            confidence_source,
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
        "\n8. 10.7.5+ NOT IMPLEMENTED EARLY"
    )


    for future_component in [
        "uncertainty-badge.tsx",
        "context-alignment-badge.tsx",
        "context-score.tsx",
        "team-comparison-row.tsx",
        "recent-form-display.tsx",
        "intelligence-explanation.tsx",
        "freshness-indicator.tsx",
        "empty-state.tsx",
        "error-state.tsx",
        "loading-state.tsx",
    ]:

        path = (
            FRONTEND
            / "components"
            / "ui"
            / future_component
        )


        check(
            f"Future component absent: {future_component}",
            not path.exists(),
            failures,
        )


    print(
        "\n9. DEPENDENCY FRESHNESS"
    )


    for stage, contract in [
        (
            "10.7.1",
            match_contract,
        ),
        (
            "10.7.2",
            probability_contract,
        ),
        (
            "10.7.3",
            outcome_contract,
        ),
        (
            "10.7.4",
            confidence_contract,
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
        "\n11. NO PREMATURE PROMOTION"
    )


    for stage, contract, key in [
        (
            "10.7.1",
            match_contract,
            "stage10_7_1_complete",
        ),
        (
            "10.7.2",
            probability_contract,
            "stage10_7_2_complete",
        ),
        (
            "10.7.3",
            outcome_contract,
            "stage10_7_3_complete",
        ),
        (
            "10.7.4",
            confidence_contract,
            "stage10_7_4_complete",
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
        "\n12. SAVE VERIFICATION"
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
                "10.7.1-10.7.4",

            "name":
                "REUSABLE_FOOTBALL_UI_FOUNDATION_VERIFICATION",

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

            "match_card":
                "LOCKED_AND_VERIFIED",

            "probability_bar":
                "LOCKED_AND_VERIFIED",

            "outcome_badge":
                "LOCKED_AND_VERIFIED",

            "confidence_badge":
                "LOCKED_AND_VERIFIED",

            "integrity": {
                "stage7_prediction_authority_preserved":
                    True,

                "stage9_intelligence_authority_preserved":
                    True,

                "stage10_presentation_only":
                    True,

                "probability_recalculation":
                    False,

                "probability_normalization":
                    False,

                "frontend_argmax":
                    False,

                "confidence_threshold_logic":
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

            "stage10_ready_for_10_7_5":
                True,

            "stage10_7_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.7.5",

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
            "STAGE 10.7.1: PASS"
        )

        print(
            "MATCHCARD: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.7.2: PASS"
        )

        print(
            "PROBABILITYBAR: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.7.3: PASS"
        )

        print(
            "OUTCOMEBADGE: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.7.4: PASS"
        )

        print(
            "CONFIDENCEBADGE: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.7.5"
        )

        print(
            "STAGE 10.7 IS NOT YET COMPLETE"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.7.1 - 10.7.4: FAIL"
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
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
APP_ROOT = FRONTEND / "app"

DOCS = ROOT / "docs" / "stage10"

FRONTEND_DATA = (
    ROOT
    / "data"
    / "processed"
    / "frontend"
)


PREVIOUS_FILE = (
    FRONTEND_DATA
    / "stage10_4_3_10_4_4_verification.json"
)

KICKOFF_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_kickoff_contract.json"
)

LOADER_CONTRACT_FILE = (
    DOCS
    / "frontend_upcoming_dashboard_loader_contract.json"
)

PROBABILITY_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_probabilities_contract.json"
)

OUTCOME_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_predicted_outcome_contract.json"
)

MATCH_CARD_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-card.tsx"
)

LOADER_FILE = (
    FRONTEND
    / "lib"
    / "dashboard"
    / "load-upcoming-matches.ts"
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


OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_4_5_10_4_6_verification.json"
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

        payload = json.load(file)

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

    with path.open("rb") as file:

        for chunk in iter(
            lambda:
                file.read(
                    1024 * 1024
                ),
            b"",
        ):

            digest.update(chunk)

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
        .replace("\\", "/")
    )


def resolve_project_path(
    value: str,
) -> Path:

    raw = Path(value)

    resolved = (
        raw.resolve()
        if raw.is_absolute()
        else
        (
            ROOT
            /
            raw
        ).resolve()
    )

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

    return passed


def current_route_pages() -> dict:

    output = {}

    for path in sorted(
        APP_ROOT.rglob(
            "page.tsx"
        )
    ):

        output[
            relative(path)
        ] = {
            "sha256":
                sha256_file(path)
        }

    return output


def verify_dependencies(
    payload: dict,
    label: str,
    failures: list[str],
) -> None:

    dependencies = payload.get(
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


    for path_text, declared in (
        dependencies.items()
    ):

        try:

            expected = (
                declared.get(
                    "sha256",
                    "",
                )
                if isinstance(
                    declared,
                    dict,
                )
                else ""
            )

            path = resolve_project_path(
                path_text
            )

            current = (
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


def run_typescript_check() -> tuple[
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
        "FixtureIQ Stage 10.4.5 + 10.4.6"
    )

    print(
        "H/D/A PROBABILITIES + PREDICTED OUTCOME VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        PREVIOUS_FILE,
        KICKOFF_CONTRACT_FILE,
        LOADER_CONTRACT_FILE,
        PROBABILITY_CONTRACT_FILE,
        OUTCOME_CONTRACT_FILE,
        MATCH_CARD_FILE,
        LOADER_FILE,
        DOMAIN_TYPES_FILE,
        PROBABILITY_FORMATTER_FILE,
    ]


    print(
        "\n1. REQUIRED ARTIFACTS"
    )


    for path in required:

        check(
            relative(path),
            path.exists(),
            failures,
        )


    if failures:

        sys.exit(1)


    previous = load_json(
        PREVIOUS_FILE
    )

    kickoff_contract = load_json(
        KICKOFF_CONTRACT_FILE
    )

    loader_contract = load_json(
        LOADER_CONTRACT_FILE
    )

    probability_contract = load_json(
        PROBABILITY_CONTRACT_FILE
    )

    outcome_contract = load_json(
        OUTCOME_CONTRACT_FILE
    )


    card_source = (
        MATCH_CARD_FILE.read_text(
            encoding="utf-8"
        )
    )

    formatter_source = (
        PROBABILITY_FORMATTER_FILE.read_text(
            encoding="utf-8"
        )
    )

    domain_source = (
        DOMAIN_TYPES_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. STAGE 10.4.3 / 10.4.4 FOUNDATION"
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


    check(
        "10.4.3 complete",
        previous.get(
            "stage_10_4_3_complete"
        )
        is True,
        failures,
    )


    check(
        "10.4.4 complete",
        previous.get(
            "stage_10_4_4_complete"
        )
        is True,
        failures,
    )


    check(
        "10.4.4 authorized 10.4.5",
        previous.get(
            "stage10_ready_for_10_4_5"
        )
        is True,
        failures,
    )


    print(
        "\n3. STAGE 10.4.5 CONTRACT"
    )


    check(
        "Probability contract stage exact",
        probability_contract.get(
            "stage"
        )
        ==
        "10.4.5",
        failures,
    )


    check(
        "Probability contract LOCKED",
        probability_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Stage 7 probability authority exact",
        probability_contract.get(
            "authority"
        )
        ==
        "STAGE_7_PREDICTION",
        failures,
    )


    expected_probability_fields = [
        "stage7_prob_home_win",
        "stage7_prob_draw",
        "stage7_prob_away_win",
    ]


    check(
        "Probability source fields exact",
        probability_contract.get(
            "source_fields"
        )
        ==
        expected_probability_fields,
        failures,
    )


    probability_transition = (
        probability_contract.get(
            "transition",
            {},
        )
    )


    check(
        "10.4.5 starts from 10.4.4 output",
        probability_transition.get(
            "match_card_before_probabilities_sha256"
        )
        ==
        kickoff_contract.get(
            "match_card_after_kickoff_sha256"
        ),
        failures,
    )


    print(
        "\n4. H/D/A PROBABILITY SOURCE"
    )


    for field in expected_probability_fields:

        check(
            f"Probability prop present: {field}",
            f"{field}: number"
            in
            card_source,
            failures,
        )

        check(
            f"Stage 7 field marker present: {field}",
            (
                f'data-stage7-field="{field}"'
                in
                card_source
            ),
            failures,
        )

        check(
            f"Probability formatter receives: {field}",
            re.search(
                (
                    r"formatProbability\s*\(\s*"
                    +
                    re.escape(field)
                    +
                    r"\s*,?\s*\)"
                ),
                card_source,
            )
            is not None,
            failures,
        )


    compact_card = re.sub(
        r"\s+",
        "",
        card_source,
    )


    check(
        "Home probability label present",
        ">Home<"
        in
        compact_card,
        failures,
    )


    check(
        "Draw probability label present",
        ">Draw<"
        in
        compact_card,
        failures,
    )


    check(
        "Away probability label present",
        ">Away<"
        in
        compact_card,
        failures,
    )


    check(
        "Probability section accessible",
        (
            'aria-label="Three-way outcome probabilities"'
            in
            card_source
        ),
        failures,
    )


    print(
        "\n5. PROBABILITY FORMATTER"
    )


    check(
        "Intl.NumberFormat used",
        "new Intl.NumberFormat"
        in
        formatter_source,
        failures,
    )


    check(
        "Percent style exact",
        'style: "percent"'
        in
        formatter_source,
        failures,
    )


    check(
        "One decimal minimum",
        "minimumFractionDigits: 1"
        in
        formatter_source,
        failures,
    )


    check(
        "One decimal maximum",
        "maximumFractionDigits: 1"
        in
        formatter_source,
        failures,
    )


    check(
        "Probability finite validation",
        "Number.isFinite(value)"
        in
        formatter_source,
        failures,
    )


    check(
        "Probability lower bound validation",
        "value < 0"
        in
        formatter_source,
        failures,
    )


    check(
        "Probability upper bound validation",
        "value > 1"
        in
        formatter_source,
        failures,
    )


    check(
        "Invalid probability fails closed",
        "throw new RangeError"
        in
        formatter_source,
        failures,
    )


    check(
        "Formatter SHA current",
        probability_contract.get(
            "probability_formatter_sha256"
        )
        ==
        sha256_file(
            PROBABILITY_FORMATTER_FILE
        ),
        failures,
    )


    print(
        "\n6. PROBABILITY INTEGRITY"
    )


    probability_arithmetic = re.search(
        (
            r"stage7_prob_(?:home_win|draw|away_win)"
            r"\s*[\+\-\*/]"
            r"|"
            r"[\+\-\*/]\s*"
            r"stage7_prob_(?:home_win|draw|away_win)"
        ),
        card_source,
    )


    check(
        "No probability arithmetic",
        probability_arithmetic
        is None,
        failures,
    )


    check(
        "No frontend probability normalization",
        (
            "normalize"
            not in
            card_source.lower()
            and
            "renormal"
            not in
            card_source.lower()
        ),
        failures,
    )


    check(
        "No probability argmax",
        "Math.max"
        not in
        card_source,
        failures,
    )


    check(
        "No probability sorting",
        ".sort("
        not in
        card_source,
        failures,
    )


    check(
        "10.4.5 output preserved into 10.4.6 transition",
        probability_contract.get(
            "match_card_after_probabilities_sha256"
        )
        ==
        outcome_contract
        .get(
            "transition",
            {},
        )
        .get(
            "match_card_before_outcome_sha256"
        ),
        failures,
    )


    print(
        "\n7. STAGE 10.4.6 CONTRACT"
    )


    check(
        "Outcome contract stage exact",
        outcome_contract.get(
            "stage"
        )
        ==
        "10.4.6",
        failures,
    )


    check(
        "Outcome contract LOCKED",
        outcome_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Stage 7 outcome authority exact",
        outcome_contract.get(
            "authority"
        )
        ==
        "STAGE_7_PREDICTION",
        failures,
    )


    check(
        "Predicted label source exact",
        outcome_contract.get(
            "source_field"
        )
        ==
        "stage7_predicted_label",
        failures,
    )


    check(
        "Outcome labels exact",
        outcome_contract.get(
            "allowed_labels"
        )
        ==
        [
            "Home Win",
            "Draw",
            "Away Win",
        ],
        failures,
    )


    print(
        "\n8. PREDICTED OUTCOME SOURCE"
    )


    check(
        "OutcomeLabel domain type exists",
        "OutcomeLabel"
        in
        domain_source,
        failures,
    )


    check(
        "OutcomeLabel imported",
        (
            "OutcomeLabel"
            in
            card_source
            and
            "../../lib/domain/types"
            in
            card_source
        ),
        failures,
    )


    check(
        "stage7_predicted_label prop typed",
        re.search(
            (
                r"stage7_predicted_label\s*:\s*"
                r"OutcomeLabel"
            ),
            card_source,
        )
        is not None,
        failures,
    )


    check(
        "Predicted outcome heading present",
        ">Predictedoutcome<"
        in
        compact_card,
        failures,
    )


    check(
        "Predicted label field marker present",
        (
            'data-stage7-field="stage7_predicted_label"'
            in
            card_source
        ),
        failures,
    )


    check(
        "Stage 7 label rendered directly",
        "{stage7_predicted_label}"
        in
        card_source,
        failures,
    )


    check(
        "No frontend-derived predicted outcome",
        (
            "Math.max"
            not in
            card_source
            and
            ".sort("
            not in
            card_source
        ),
        failures,
    )


    comparison_pattern = re.compile(
        (
            r"stage7_prob_(?:home_win|draw|away_win)"
            r"\s*(?:>|<|>=|<=|===|==)"
            r"|"
            r"(?:>|<|>=|<=|===|==)\s*"
            r"stage7_prob_(?:home_win|draw|away_win)"
        )
    )


    check(
        "No probability comparison for outcome",
        comparison_pattern.search(
            card_source
        )
        is None,
        failures,
    )


    check(
        "Current MatchCard equals 10.4.6 output",
        outcome_contract.get(
            "match_card_after_outcome_sha256"
        )
        ==
        sha256_file(
            MATCH_CARD_FILE
        ),
        failures,
    )


    print(
        "\n9. ROUTE / LOADER / TYPES PRESERVATION"
    )


    protected = (
        outcome_contract.get(
            "protected_state",
            {},
        )
    )


    check(
        "Route pages unchanged",
        protected.get(
            "route_page_identity"
        )
        ==
        current_route_pages(),
        failures,
    )


    check(
        "Dashboard loader unchanged",
        (
            protected.get(
                "loader_sha256"
            )
            ==
            sha256_file(
                LOADER_FILE
            )
            ==
            loader_contract.get(
                "source_sha256"
            )
        ),
        failures,
    )


    check(
        "Domain types unchanged",
        protected.get(
            "domain_types_sha256"
        )
        ==
        sha256_file(
            DOMAIN_TYPES_FILE
        ),
        failures,
    )


    print(
        "\n10. LATER FEATURES NOT IMPLEMENTED EARLY"
    )


    forbidden_later_terms = [
        "confidence_band",
        "uncertainty_band",
        "context_alignment",
        "context_support_score",
        "explanation_headline",
        "explanation_summary",
        "/matches/",
    ]


    for term in forbidden_later_terms:

        check(
            f"MatchCard excludes: {term}",
            term
            not in
            card_source,
            failures,
        )


    print(
        "\n11. PRESENTATION-ONLY SAFETY"
    )


    combined_source = (
        card_source
        +
        "\n"
        +
        formatter_source
    )


    check(
        "No fetch",
        re.search(
            r"\bfetch\s*\(",
            combined_source,
        )
        is None,
        failures,
    )


    check(
        "No API client import",
        "lib/api"
        not in
        combined_source,
        failures,
    )


    check(
        "No client component directive",
        (
            '"use client"'
            not in
            combined_source
            and
            "'use client'"
            not in
            combined_source
        ),
        failures,
    )


    for term in [
        "data/processed",
        "data\\processed",
        "data/historical",
        "data\\historical",
        ".joblib",
        "football-data.org",
        "api-football",
        "api-sports",
    ]:

        check(
            f"Sources exclude: {term}",
            term.lower()
            not in
            combined_source.lower(),
            failures,
        )


    print(
        "\n12. DEPENDENCY FRESHNESS"
    )


    verify_dependencies(
        probability_contract,
        "10.4.5",
        failures,
    )


    verify_dependencies(
        outcome_contract,
        "10.4.6",
        failures,
    )


    print(
        "\n13. TYPESCRIPT COMPILER"
    )


    compiler_ok, compiler_output = (
        run_typescript_check()
    )


    check(
        "TypeScript --noEmit",
        compiler_ok,
        failures,
    )


    if (
        not compiler_ok
        and
        compiler_output
    ):

        print()

        print(
            compiler_output
        )


    print(
        "\n14. NO PREMATURE PROMOTION"
    )


    probability_promotion = (
        probability_contract.get(
            "promotion",
            {},
        )
    )

    outcome_promotion = (
        outcome_contract.get(
            "promotion",
            {},
        )
    )


    check(
        "10.4.5 did not self-promote",
        probability_promotion.get(
            "stage10_4_5_complete"
        )
        is False,
        failures,
    )


    check(
        "10.4.6 did not self-promote",
        outcome_promotion.get(
            "stage10_4_6_complete"
        )
        is False,
        failures,
    )


    check(
        "Stage 10.4 remains incomplete",
        (
            probability_promotion.get(
                "stage10_4_complete"
            )
            is False
            and
            outcome_promotion.get(
                "stage10_4_complete"
            )
            is False
        ),
        failures,
    )


    check(
        "Stage 10 remains incomplete",
        (
            probability_promotion.get(
                "stage10_complete"
            )
            is False
            and
            outcome_promotion.get(
                "stage10_complete"
            )
            is False
        ),
        failures,
    )


    print(
        "\n15. SAVE VERIFICATION EVIDENCE"
    )


    passed = (
        len(
            failures
        )
        ==
        0
    )


    if passed:

        evidence = {
            "stage":
                "10.4.5-10.4.6",

            "name":
                (
                    "HDA_PROBABILITIES_AND_"
                    "PREDICTED_OUTCOME_VERIFICATION"
                ),

            "status":
                "PASS",

            "stage_10_4_5_complete":
                True,

            "stage_10_4_6_complete":
                True,

            "hda_probabilities":
                "LOCKED_AND_VERIFIED",

            "predicted_outcome":
                "LOCKED_AND_VERIFIED",

            "stage7_authority": {
                "probabilities": [
                    "stage7_prob_home_win",
                    "stage7_prob_draw",
                    "stage7_prob_away_win",
                ],

                "predicted_label":
                    "stage7_predicted_label",

                "frontend_argmax":
                    False,

                "frontend_recalculation":
                    False,

                "frontend_normalization":
                    False,

                "probability_mutation":
                    False,
            },

            "probability_display": {
                "formatter":
                    "Intl.NumberFormat",

                "style":
                    "percent",

                "decimal_places":
                    1,

                "source_values_unchanged":
                    True,
            },

            "safety": {
                "route_pages_modified":
                    False,

                "dashboard_loader_modified":
                    False,

                "api_access":
                    False,

                "provider_access":
                    False,

                "artifact_access":
                    False,

                "frontend_prediction_logic":
                    False,

                "probability_recalibration":
                    False,

                "predicted_label_recalculation":
                    False,
            },

            "typescript_compiler":
                "PASS",

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "stage10_ready_for_10_4_7":
                True,

            "stage10_4_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.4.7",

            "failures":
                [],
        }


        save_json_atomic(
            OUTPUT_FILE,
            evidence,
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
            "STAGE 10.4.5: PASS"
        )

        print(
            "H/D/A PROBABILITIES: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.4.6: PASS"
        )

        print(
            "PREDICTED OUTCOME: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.4.7"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.4.5 / 10.4.6: FAIL"
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
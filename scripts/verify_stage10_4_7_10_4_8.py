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
    / "stage10_4_5_10_4_6_verification.json"
)

OUTCOME_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_predicted_outcome_contract.json"
)

PROBABILITY_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_probabilities_contract.json"
)

LOADER_CONTRACT_FILE = (
    DOCS
    / "frontend_upcoming_dashboard_loader_contract.json"
)

CONFIDENCE_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_confidence_contract.json"
)

UNCERTAINTY_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_uncertainty_contract.json"
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
    / "stage10_4_7_10_4_8_verification.json"
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
        "FixtureIQ Stage 10.4.7 + 10.4.8"
    )

    print(
        "CONFIDENCE + UNCERTAINTY VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        PREVIOUS_FILE,
        OUTCOME_CONTRACT_FILE,
        PROBABILITY_CONTRACT_FILE,
        LOADER_CONTRACT_FILE,
        CONFIDENCE_CONTRACT_FILE,
        UNCERTAINTY_CONTRACT_FILE,
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

    outcome_contract = load_json(
        OUTCOME_CONTRACT_FILE
    )

    probability_contract = load_json(
        PROBABILITY_CONTRACT_FILE
    )

    loader_contract = load_json(
        LOADER_CONTRACT_FILE
    )

    confidence_contract = load_json(
        CONFIDENCE_CONTRACT_FILE
    )

    uncertainty_contract = load_json(
        UNCERTAINTY_CONTRACT_FILE
    )


    card_source = (
        MATCH_CARD_FILE.read_text(
            encoding="utf-8"
        )
    )

    domain_source = (
        DOMAIN_TYPES_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. STAGE 10.4.5 / 10.4.6 FOUNDATION"
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
        "10.4.5 complete",
        previous.get(
            "stage_10_4_5_complete"
        )
        is True,
        failures,
    )


    check(
        "10.4.6 complete",
        previous.get(
            "stage_10_4_6_complete"
        )
        is True,
        failures,
    )


    check(
        "10.4.6 authorized 10.4.7",
        previous.get(
            "stage10_ready_for_10_4_7"
        )
        is True,
        failures,
    )


    print(
        "\n3. STAGE 10.4.7 CONTRACT"
    )


    check(
        "Confidence stage exact",
        confidence_contract.get(
            "stage"
        )
        ==
        "10.4.7",
        failures,
    )


    check(
        "Confidence contract LOCKED",
        confidence_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    authority = confidence_contract.get(
        "authority",
        {},
    )


    check(
        "Stage 7 confidence authority exact",
        authority.get(
            "stage7_confidence"
        )
        ==
        "STAGE_7_PREDICTION",
        failures,
    )


    check(
        "Stage 9 confidence-band authority exact",
        authority.get(
            "confidence_band"
        )
        ==
        "STAGE_9_INTELLIGENCE",
        failures,
    )


    confidence_type = (
        confidence_contract.get(
            "domain_type"
        )
    )


    check(
        "Confidence domain type recorded",
        isinstance(
            confidence_type,
            str,
        )
        and
        bool(
            confidence_type
        ),
        failures,
    )


    check(
        "Confidence domain type still exported",
        isinstance(
            confidence_type,
            str,
        )
        and
        re.search(
            (
                r"export\s+type\s+"
                +
                re.escape(
                    confidence_type
                )
                +
                r"\b"
            ),
            domain_source,
        )
        is not None,
        failures,
    )


    confidence_transition = (
        confidence_contract.get(
            "transition",
            {},
        )
    )


    check(
        "10.4.7 starts from 10.4.6 output",
        confidence_transition.get(
            "match_card_before_confidence_sha256"
        )
        ==
        outcome_contract.get(
            "match_card_after_outcome_sha256"
        ),
        failures,
    )


    print(
        "\n4. CONFIDENCE SOURCE"
    )


    check(
        "stage7_confidence prop present",
        "stage7_confidence: number"
        in
        card_source,
        failures,
    )


    check(
        "confidence_band prop present",
        isinstance(
            confidence_type,
            str,
        )
        and
        re.search(
            (
                r"confidence_band\s*:\s*"
                +
                re.escape(
                    confidence_type
                )
            ),
            card_source,
        )
        is not None,
        failures,
    )


    check(
        "Stage 7 confidence marker present",
        (
            'data-stage7-field="stage7_confidence"'
            in
            card_source
        ),
        failures,
    )


    check(
        "Stage 9 confidence band marker present",
        (
            'data-stage9-field="confidence_band"'
            in
            card_source
        ),
        failures,
    )


    check(
        "Confidence formatted by existing probability formatter",
        re.search(
            (
                r"formatProbability\s*\(\s*"
                r"stage7_confidence"
                r"\s*,?\s*\)"
            ),
            card_source,
        )
        is not None,
        failures,
    )


    check(
        "Confidence band displayed directly",
        "{confidence_band}"
        in
        card_source,
        failures,
    )


    check(
        "Confidence section accessible",
        (
            'aria-label="Prediction confidence"'
            in
            card_source
        ),
        failures,
    )


    print(
        "\n5. CONFIDENCE DERIVATION PROHIBITED"
    )


    check(
        "No confidence threshold comparison",
        re.search(
            (
                r"stage7_confidence\s*"
                r"(?:>=|<=|>|<)"
                r"|"
                r"(?:>=|<=|>|<)\s*"
                r"stage7_confidence"
            ),
            card_source,
        )
        is None,
        failures,
    )


    check(
        "No frontend confidence max calculation",
        "Math.max"
        not in
        card_source,
        failures,
    )


    check(
        "No confidence-band switch",
        re.search(
            r"switch\s*\(\s*stage7_confidence",
            card_source,
        )
        is None,
        failures,
    )


    print(
        "\n6. STAGE 10.4.8 CONTRACT"
    )


    check(
        "Uncertainty stage exact",
        uncertainty_contract.get(
            "stage"
        )
        ==
        "10.4.8",
        failures,
    )


    check(
        "Uncertainty contract LOCKED",
        uncertainty_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Stage 9 uncertainty authority exact",
        uncertainty_contract.get(
            "authority"
        )
        ==
        "STAGE_9_INTELLIGENCE",
        failures,
    )


    check(
        "Uncertainty source field exact",
        uncertainty_contract.get(
            "source_field"
        )
        ==
        "uncertainty_band",
        failures,
    )


    uncertainty_type = (
        uncertainty_contract.get(
            "domain_type"
        )
    )


    check(
        "Uncertainty domain type recorded",
        isinstance(
            uncertainty_type,
            str,
        )
        and
        bool(
            uncertainty_type
        ),
        failures,
    )


    check(
        "Uncertainty domain type still exported",
        isinstance(
            uncertainty_type,
            str,
        )
        and
        re.search(
            (
                r"export\s+type\s+"
                +
                re.escape(
                    uncertainty_type
                )
                +
                r"\b"
            ),
            domain_source,
        )
        is not None,
        failures,
    )


    uncertainty_transition = (
        uncertainty_contract.get(
            "transition",
            {},
        )
    )


    check(
        "10.4.8 starts from 10.4.7 output",
        uncertainty_transition.get(
            "match_card_before_uncertainty_sha256"
        )
        ==
        confidence_contract.get(
            "match_card_after_confidence_sha256"
        ),
        failures,
    )


    check(
        "Current MatchCard equals 10.4.8 output",
        uncertainty_contract.get(
            "match_card_after_uncertainty_sha256"
        )
        ==
        sha256_file(
            MATCH_CARD_FILE
        ),
        failures,
    )


    print(
        "\n7. UNCERTAINTY SOURCE"
    )


    check(
        "uncertainty_band prop present",
        isinstance(
            uncertainty_type,
            str,
        )
        and
        re.search(
            (
                r"uncertainty_band\s*:\s*"
                +
                re.escape(
                    uncertainty_type
                )
            ),
            card_source,
        )
        is not None,
        failures,
    )


    check(
        "Stage 9 uncertainty marker present",
        (
            'data-stage9-field="uncertainty_band"'
            in
            card_source
        ),
        failures,
    )


    check(
        "Uncertainty displayed directly",
        "{uncertainty_band}"
        in
        card_source,
        failures,
    )


    check(
        "Uncertainty section accessible",
        (
            'aria-label="Prediction uncertainty"'
            in
            card_source
        ),
        failures,
    )


    print(
        "\n8. UNCERTAINTY DERIVATION PROHIBITED"
    )


    check(
        "No entropy calculation",
        (
            "Math.log"
            not in
            card_source
            and
            "normalized_entropy"
            not in
            card_source
        ),
        failures,
    )


    check(
        "No uncertainty threshold comparison",
        re.search(
            (
                r"uncertainty_band\s*"
                r"(?:>=|<=|>|<)"
                r"|"
                r"(?:>=|<=|>|<)\s*"
                r"uncertainty_band"
            ),
            card_source,
        )
        is None,
        failures,
    )


    print(
        "\n9. PREVIOUS AUTHORITIES PRESERVED"
    )


    check(
        "Stage 7 H/D/A probability fields remain",
        all(
            field
            in
            card_source

            for field in [
                "stage7_prob_home_win",
                "stage7_prob_draw",
                "stage7_prob_away_win",
            ]
        ),
        failures,
    )


    check(
        "Stage 7 predicted label remains",
        "stage7_predicted_label"
        in
        card_source,
        failures,
    )


    check(
        "No H/D/A probability arithmetic",
        re.search(
            (
                r"stage7_prob_"
                r"(?:home_win|draw|away_win)"
                r"\s*[\+\-\*/]"
                r"|"
                r"[\+\-\*/]\s*"
                r"stage7_prob_"
                r"(?:home_win|draw|away_win)"
            ),
            card_source,
        )
        is None,
        failures,
    )


    print(
        "\n10. ROUTE / LOADER / DOMAIN PRESERVATION"
    )


    protected = uncertainty_contract.get(
        "protected_state",
        {},
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


    check(
        "Probability formatter unchanged",
        (
            protected.get(
                "probability_formatter_sha256"
            )
            ==
            sha256_file(
                PROBABILITY_FORMATTER_FILE
            )
            ==
            probability_contract.get(
                "probability_formatter_sha256"
            )
        ),
        failures,
    )


    print(
        "\n11. LATER FEATURES NOT IMPLEMENTED EARLY"
    )


    later_fields = [
        "context_alignment",
        "context_support_score",
        "explanation_headline",
        "explanation_summary",
        "/matches/",
    ]


    for field in later_fields:

        check(
            f"MatchCard excludes: {field}",
            field
            not in
            card_source,
            failures,
        )


    print(
        "\n12. PRESENTATION-ONLY SAFETY"
    )


    check(
        "No fetch",
        re.search(
            r"\bfetch\s*\(",
            card_source,
        )
        is None,
        failures,
    )


    check(
        "No API client import",
        "lib/api"
        not in
        card_source,
        failures,
    )


    check(
        "No client component directive",
        (
            '"use client"'
            not in
            card_source
            and
            "'use client'"
            not in
            card_source
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
            f"MatchCard excludes: {term}",
            term.lower()
            not in
            card_source.lower(),
            failures,
        )


    print(
        "\n13. DEPENDENCY FRESHNESS"
    )


    verify_dependencies(
        confidence_contract,
        "10.4.7",
        failures,
    )


    verify_dependencies(
        uncertainty_contract,
        "10.4.8",
        failures,
    )


    print(
        "\n14. TYPESCRIPT COMPILER"
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
        "\n15. NO PREMATURE PROMOTION"
    )


    confidence_promotion = (
        confidence_contract.get(
            "promotion",
            {},
        )
    )

    uncertainty_promotion = (
        uncertainty_contract.get(
            "promotion",
            {},
        )
    )


    check(
        "10.4.7 did not self-promote",
        confidence_promotion.get(
            "stage10_4_7_complete"
        )
        is False,
        failures,
    )


    check(
        "10.4.8 did not self-promote",
        uncertainty_promotion.get(
            "stage10_4_8_complete"
        )
        is False,
        failures,
    )


    check(
        "Stage 10.4 remains incomplete",
        (
            confidence_promotion.get(
                "stage10_4_complete"
            )
            is False
            and
            uncertainty_promotion.get(
                "stage10_4_complete"
            )
            is False
        ),
        failures,
    )


    check(
        "Stage 10 remains incomplete",
        (
            confidence_promotion.get(
                "stage10_complete"
            )
            is False
            and
            uncertainty_promotion.get(
                "stage10_complete"
            )
            is False
        ),
        failures,
    )


    print(
        "\n16. SAVE VERIFICATION EVIDENCE"
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
                "10.4.7-10.4.8",

            "name":
                (
                    "CONFIDENCE_AND_"
                    "UNCERTAINTY_VERIFICATION"
                ),

            "status":
                "PASS",

            "stage_10_4_7_complete":
                True,

            "stage_10_4_8_complete":
                True,

            "confidence":
                "LOCKED_AND_VERIFIED",

            "uncertainty":
                "LOCKED_AND_VERIFIED",

            "authority": {
                "stage7_confidence":
                    "STAGE_7_PREDICTION",

                "confidence_band":
                    "STAGE_9_INTELLIGENCE",

                "uncertainty_band":
                    "STAGE_9_INTELLIGENCE",
            },

            "derivation": {
                "frontend_confidence_calculation":
                    False,

                "frontend_confidence_band_derivation":
                    False,

                "frontend_uncertainty_calculation":
                    False,

                "frontend_entropy_calculation":
                    False,

                "frontend_uncertainty_band_derivation":
                    False,
            },

            "safety": {
                "route_pages_modified":
                    False,

                "dashboard_loader_modified":
                    False,

                "domain_types_modified":
                    False,

                "probability_formatter_modified":
                    False,

                "api_access":
                    False,

                "provider_access":
                    False,

                "artifact_access":
                    False,

                "prediction_logic":
                    False,
            },

            "typescript_compiler":
                "PASS",

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "stage10_ready_for_10_4_9":
                True,

            "stage10_4_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.4.9",

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
            "STAGE 10.4.7: PASS"
        )

        print(
            "CONFIDENCE: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.4.8: PASS"
        )

        print(
            "UNCERTAINTY: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.4.9"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.4.7 / 10.4.8: FAIL"
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
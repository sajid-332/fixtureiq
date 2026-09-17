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
    / "stage10_4_7_10_4_8_verification.json"
)

UNCERTAINTY_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_uncertainty_contract.json"
)

LOADER_CONTRACT_FILE = (
    DOCS
    / "frontend_upcoming_dashboard_loader_contract.json"
)

ALIGNMENT_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_context_alignment_contract.json"
)

EXPLANATION_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_explanation_preview_contract.json"
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
    / "stage10_4_9_10_4_10_verification.json"
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
            lambda: file.read(
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
        bool(dependencies),
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
                bool(expected)
                and
                path.exists()
                and
                sha256_file(path)
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
        "FixtureIQ Stage 10.4.9 + 10.4.10"
    )

    print(
        "CONTEXT ALIGNMENT + EXPLANATION PREVIEW VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        PREVIOUS_FILE,
        UNCERTAINTY_CONTRACT_FILE,
        LOADER_CONTRACT_FILE,
        ALIGNMENT_CONTRACT_FILE,
        EXPLANATION_CONTRACT_FILE,
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

    uncertainty_contract = load_json(
        UNCERTAINTY_CONTRACT_FILE
    )

    loader_contract = load_json(
        LOADER_CONTRACT_FILE
    )

    alignment_contract = load_json(
        ALIGNMENT_CONTRACT_FILE
    )

    explanation_contract = load_json(
        EXPLANATION_CONTRACT_FILE
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
        "\n2. STAGE 10.4.7 / 10.4.8 FOUNDATION"
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
        "10.4.7 complete",
        previous.get(
            "stage_10_4_7_complete"
        )
        is True,
        failures,
    )


    check(
        "10.4.8 complete",
        previous.get(
            "stage_10_4_8_complete"
        )
        is True,
        failures,
    )


    check(
        "10.4.8 authorized 10.4.9",
        previous.get(
            "stage10_ready_for_10_4_9"
        )
        is True,
        failures,
    )


    print(
        "\n3. STAGE 10.4.9 CONTRACT"
    )


    check(
        "Alignment stage exact",
        alignment_contract.get(
            "stage"
        )
        ==
        "10.4.9",
        failures,
    )


    check(
        "Alignment contract LOCKED",
        alignment_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Stage 9 alignment authority exact",
        alignment_contract.get(
            "authority"
        )
        ==
        "STAGE_9_INTELLIGENCE",
        failures,
    )


    check(
        "Alignment source field exact",
        alignment_contract.get(
            "source_field"
        )
        ==
        "context_alignment",
        failures,
    )


    check(
        "Alignment values exact",
        alignment_contract.get(
            "allowed_values"
        )
        ==
        [
            "SUPPORTIVE",
            "MIXED",
            "CONTRADICTORY",
            "NEUTRAL",
        ],
        failures,
    )


    alignment_type = (
        alignment_contract.get(
            "domain_type"
        )
    )


    check(
        "Alignment domain type recorded",
        isinstance(
            alignment_type,
            str,
        )
        and
        bool(alignment_type),
        failures,
    )


    check(
        "Alignment type still exported",
        isinstance(
            alignment_type,
            str,
        )
        and
        re.search(
            (
                r"export\s+type\s+"
                +
                re.escape(
                    alignment_type
                )
                +
                r"\b"
            ),
            domain_source,
        )
        is not None,
        failures,
    )


    alignment_transition = (
        alignment_contract.get(
            "transition",
            {},
        )
    )


    check(
        "10.4.9 starts from 10.4.8 output",
        alignment_transition.get(
            "match_card_before_alignment_sha256"
        )
        ==
        uncertainty_contract.get(
            "match_card_after_uncertainty_sha256"
        ),
        failures,
    )


    print(
        "\n4. CONTEXT ALIGNMENT SOURCE"
    )


    check(
        "context_alignment prop typed",
        isinstance(
            alignment_type,
            str,
        )
        and
        re.search(
            (
                r"context_alignment\s*:\s*"
                +
                re.escape(
                    alignment_type
                )
            ),
            card_source,
        )
        is not None,
        failures,
    )


    check(
        "Context alignment marker present",
        (
            'data-stage9-field="context_alignment"'
            in
            card_source
        ),
        failures,
    )


    check(
        "Context alignment displayed directly",
        "{context_alignment}"
        in
        card_source,
        failures,
    )


    check(
        "Context alignment section accessible",
        (
            'aria-label="Context alignment"'
            in
            card_source
        ),
        failures,
    )


    check(
        "Context support score not used",
        "context_support_score"
        not in
        card_source,
        failures,
    )


    check(
        "No frontend alignment switch",
        re.search(
            r"switch\s*\(\s*context_alignment",
            card_source,
        )
        is None,
        failures,
    )


    print(
        "\n5. STAGE 10.4.10 CONTRACT"
    )


    check(
        "Explanation stage exact",
        explanation_contract.get(
            "stage"
        )
        ==
        "10.4.10",
        failures,
    )


    check(
        "Explanation contract LOCKED",
        explanation_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Stage 9 explanation authority exact",
        explanation_contract.get(
            "authority"
        )
        ==
        "STAGE_9_INTELLIGENCE",
        failures,
    )


    check(
        "Explanation fields exact",
        explanation_contract.get(
            "source_fields"
        )
        ==
        [
            "explanation_headline",
            "explanation_summary",
        ],
        failures,
    )


    explanation_transition = (
        explanation_contract.get(
            "transition",
            {},
        )
    )


    check(
        "10.4.10 starts from 10.4.9 output",
        explanation_transition.get(
            "match_card_before_explanation_sha256"
        )
        ==
        alignment_contract.get(
            "match_card_after_alignment_sha256"
        ),
        failures,
    )


    check(
        "Current MatchCard equals 10.4.10 output",
        explanation_contract.get(
            "match_card_after_explanation_sha256"
        )
        ==
        sha256_file(
            MATCH_CARD_FILE
        ),
        failures,
    )


    print(
        "\n6. EXPLANATION PREVIEW SOURCE"
    )


    check(
        "explanation_headline prop present",
        "explanation_headline: string"
        in
        card_source,
        failures,
    )


    check(
        "explanation_summary prop present",
        "explanation_summary: string"
        in
        card_source,
        failures,
    )


    check(
        "Explanation headline marker present",
        (
            'data-stage9-field="explanation_headline"'
            in
            card_source
        ),
        failures,
    )


    check(
        "Explanation summary marker present",
        (
            'data-stage9-field="explanation_summary"'
            in
            card_source
        ),
        failures,
    )


    check(
        "Explanation headline rendered directly",
        "{explanation_headline}"
        in
        card_source,
        failures,
    )


    check(
        "Explanation summary rendered directly",
        "{explanation_summary}"
        in
        card_source,
        failures,
    )


    check(
        "Explanation preview accessible",
        (
            'aria-label="Explanation preview"'
            in
            card_source
        ),
        failures,
    )


    print(
        "\n7. EXPLANATION MUTATION PROHIBITED"
    )


    forbidden_explanation_operations = [
        ".slice(",
        ".substring(",
        ".substr(",
        "line-clamp",
        "text-overflow",
        "truncate",
    ]


    for term in forbidden_explanation_operations:

        check(
            f"Explanation excludes mutation/truncation: {term}",
            term
            not in
            card_source,
            failures,
        )


    check(
        "No frontend explanation fallback",
        re.search(
            (
                r"explanation_(?:headline|summary)"
                r"\s*(?:\?\?|\|\|)"
            ),
            card_source,
        )
        is None,
        failures,
    )


    print(
        "\n8. PREVIOUS AUTHORITIES PRESERVED"
    )


    for field in [
        "stage7_prob_home_win",
        "stage7_prob_draw",
        "stage7_prob_away_win",
        "stage7_predicted_label",
        "stage7_confidence",
        "confidence_band",
        "uncertainty_band",
    ]:

        check(
            f"Existing field remains: {field}",
            field
            in
            card_source,
            failures,
        )


    print(
        "\n9. ROUTE / LOADER / DOMAIN PRESERVATION"
    )


    protected = explanation_contract.get(
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
        protected.get(
            "probability_formatter_sha256"
        )
        ==
        sha256_file(
            PROBABILITY_FORMATTER_FILE
        ),
        failures,
    )


    print(
        "\n10. DETAIL LINKS NOT IMPLEMENTED EARLY"
    )


    check(
        "No /matches/ detail link yet",
        "/matches/"
        not in
        card_source,
        failures,
    )


    check(
        "No Next Link import yet",
        'from "next/link"'
        not in
        card_source
        and
        "from 'next/link'"
        not in
        card_source,
        failures,
    )


    print(
        "\n11. PRESENTATION-ONLY SAFETY"
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
        "\n12. DEPENDENCY FRESHNESS"
    )


    verify_dependencies(
        alignment_contract,
        "10.4.9",
        failures,
    )


    verify_dependencies(
        explanation_contract,
        "10.4.10",
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


    alignment_promotion = (
        alignment_contract.get(
            "promotion",
            {},
        )
    )

    explanation_promotion = (
        explanation_contract.get(
            "promotion",
            {},
        )
    )


    check(
        "10.4.9 did not self-promote",
        alignment_promotion.get(
            "stage10_4_9_complete"
        )
        is False,
        failures,
    )


    check(
        "10.4.10 did not self-promote",
        explanation_promotion.get(
            "stage10_4_10_complete"
        )
        is False,
        failures,
    )


    check(
        "Stage 10.4 remains incomplete",
        (
            alignment_promotion.get(
                "stage10_4_complete"
            )
            is False
            and
            explanation_promotion.get(
                "stage10_4_complete"
            )
            is False
        ),
        failures,
    )


    check(
        "Stage 10 remains incomplete",
        (
            alignment_promotion.get(
                "stage10_complete"
            )
            is False
            and
            explanation_promotion.get(
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
        len(failures)
        ==
        0
    )


    if passed:

        evidence = {
            "stage":
                "10.4.9-10.4.10",

            "name":
                (
                    "CONTEXT_ALIGNMENT_AND_"
                    "EXPLANATION_PREVIEW_VERIFICATION"
                ),

            "status":
                "PASS",

            "stage_10_4_9_complete":
                True,

            "stage_10_4_10_complete":
                True,

            "context_alignment":
                "LOCKED_AND_VERIFIED",

            "explanation_preview":
                "LOCKED_AND_VERIFIED",

            "stage9_authority": {
                "context_alignment":
                    True,

                "explanation_headline":
                    True,

                "explanation_summary":
                    True,

                "frontend_alignment_derivation":
                    False,

                "frontend_explanation_generation":
                    False,

                "frontend_explanation_rewrite":
                    False,
            },

            "safety": {
                "route_pages_modified":
                    False,

                "dashboard_loader_modified":
                    False,

                "domain_types_modified":
                    False,

                "provider_access":
                    False,

                "artifact_access":
                    False,

                "prediction_logic":
                    False,

                "detail_links_implemented_early":
                    False,
            },

            "typescript_compiler":
                "PASS",

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "stage10_ready_for_10_4_11":
                True,

            "stage10_4_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.4.11",

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
            "STAGE 10.4.9: PASS"
        )

        print(
            "CONTEXT ALIGNMENT: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.4.10: PASS"
        )

        print(
            "EXPLANATION PREVIEW: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.4.11"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.4.9 / 10.4.10: FAIL"
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
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


STAGE10_3_FINAL = (
    FRONTEND_DATA
    / "stage10_3_final_verification.json"
)

MAPPED_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "mapped.ts"
)

RESULT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "result.ts"
)

VALIDATED_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "validated.ts"
)

LOADER_FILE = (
    FRONTEND
    / "lib"
    / "dashboard"
    / "load-upcoming-matches.ts"
)

MATCH_CARD_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-card.tsx"
)

LOADER_CONTRACT_FILE = (
    DOCS
    / "frontend_upcoming_dashboard_loader_contract.json"
)

MATCH_CARD_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_base_contract.json"
)


OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_4_1_10_4_2_verification.json"
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
        {}
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
        "FixtureIQ Stage 10.4.1 + 10.4.2"
    )

    print(
        "UPCOMING DASHBOARD LOADER + MATCHCARD BASE VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        STAGE10_3_FINAL,
        MAPPED_FILE,
        RESULT_FILE,
        VALIDATED_FILE,
        LOADER_FILE,
        MATCH_CARD_FILE,
        LOADER_CONTRACT_FILE,
        MATCH_CARD_CONTRACT_FILE,
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


    stage10_3 = load_json(
        STAGE10_3_FINAL
    )

    loader_contract = load_json(
        LOADER_CONTRACT_FILE
    )

    card_contract = load_json(
        MATCH_CARD_CONTRACT_FILE
    )


    loader_source = (
        LOADER_FILE.read_text(
            encoding="utf-8"
        )
    )

    card_source = (
        MATCH_CARD_FILE.read_text(
            encoding="utf-8"
        )
    )

    mapped_source = (
        MAPPED_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. STAGE 10.3 FOUNDATION"
    )


    check(
        "Stage 10.3 final PASS",
        stage10_3.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )


    check(
        "Stage 10.3 complete",
        stage10_3.get(
            "stage_10_3_complete"
        )
        is True,
        failures,
    )


    check(
        "Stage 10.3 authorized 10.4.1",
        stage10_3.get(
            "stage10_ready_for_10_4_1"
        )
        is True,
        failures,
    )


    print(
        "\n3. STAGE 10.4.1 CONTRACT"
    )


    check(
        "Loader contract stage exact",
        loader_contract.get(
            "stage"
        )
        ==
        "10.4.1",
        failures,
    )


    check(
        "Loader contract LOCKED",
        loader_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Loader export exact",
        loader_contract.get(
            "export"
        )
        ==
        "loadUpcomingMatches",
        failures,
    )


    upstream = loader_contract.get(
        "upstream",
        {}
    )


    mapped_export = upstream.get(
        "mapped_export"
    )


    check(
        "Mapped upcoming export recorded",
        isinstance(
            mapped_export,
            str,
        )
        and
        bool(
            mapped_export
        ),
        failures,
    )


    check(
        "Mapped export still exists",
        isinstance(
            mapped_export,
            str,
        )
        and
        mapped_export
        in
        mapped_source,
        failures,
    )


    check(
        "Stage 9 intelligence authority locked",
        upstream.get(
            "backend_authority"
        )
        ==
        "STAGE_9_INTELLIGENCE",
        failures,
    )


    check(
        "Upcoming endpoint authority exact",
        upstream.get(
            "endpoint_authority"
        )
        ==
        "/api/v1/intelligence/upcoming",
        failures,
    )


    print(
        "\n4. DASHBOARD LOADER SOURCE"
    )


    check(
        "server-only imported",
        (
            'import "server-only"'
            in
            loader_source
        ),
        failures,
    )


    check(
        "Loader function exported",
        (
            "export async function "
            "loadUpcomingMatches"
            in
            loader_source
        ),
        failures,
    )


    check(
        "Mapped wrapper imported",
        isinstance(
            mapped_export,
            str,
        )
        and
        mapped_export
        in
        loader_source,
        failures,
    )


    check(
        "Mapped wrapper called directly",
        isinstance(
            mapped_export,
            str,
        )
        and
        re.search(
            (
                r"return\s+"
                +
                re.escape(
                    mapped_export
                )
                +
                r"\s*\(\s*\)\s*;"
            ),
            loader_source,
        )
        is not None,
        failures,
    )


    implementation = loader_contract.get(
        "implementation",
        {}
    )


    check(
        "No loader response transformation",
        implementation.get(
            "response_transformation"
        )
        is False,
        failures,
    )


    check(
        "No probability transformation",
        implementation.get(
            "probability_transformation"
        )
        is False,
        failures,
    )


    check(
        "No loader retry",
        implementation.get(
            "retry"
        )
        is False,
        failures,
    )


    check(
        "No stale fallback",
        implementation.get(
            "stale_fallback"
        )
        is False,
        failures,
    )


    check(
        "No direct fetch",
        re.search(
            r"\bfetch\s*\(",
            loader_source,
        )
        is None,
        failures,
    )


    check(
        "No cache API",
        (
            "localStorage"
            not in
            loader_source
            and
            "sessionStorage"
            not in
            loader_source
            and
            "unstable_cache"
            not in
            loader_source
        ),
        failures,
    )


    print(
        "\n5. STAGE 10.4.2 CONTRACT"
    )


    check(
        "MatchCard contract stage exact",
        card_contract.get(
            "stage"
        )
        ==
        "10.4.2",
        failures,
    )


    check(
        "MatchCard contract LOCKED",
        card_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "MatchCard component exact",
        card_contract.get(
            "component"
        )
        ==
        "MatchCard",
        failures,
    )


    check(
        "MatchCard semantic article exact",
        card_contract.get(
            "semantic_element"
        )
        ==
        "article",
        failures,
    )


    print(
        "\n6. MATCHCARD BASE SOURCE"
    )


    check(
        "ReactNode imported",
        "ReactNode"
        in
        card_source,
        failures,
    )


    check(
        "MatchCard exported",
        "export function MatchCard"
        in
        card_source,
        failures,
    )


    check(
        "Article semantic element present",
        (
            "<article"
            in
            card_source
            and
            "</article>"
            in
            card_source
        ),
        failures,
    )


    check(
        "Children rendered",
        "{children}"
        in
        card_source,
        failures,
    )


    check(
        "MatchCard identity marker present",
        (
            'data-fixtureiq-component="match-card"'
            in
            card_source
        ),
        failures,
    )


    check(
        "Base border present",
        "border"
        in
        card_source,
        failures,
    )


    check(
        "Base rounded structure present",
        "rounded-xl"
        in
        card_source,
        failures,
    )


    check(
        "Base background present",
        "bg-white"
        in
        card_source,
        failures,
    )


    check(
        "MatchCard remains server component",
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


    print(
        "\n7. LATER DASHBOARD FEATURES NOT IMPLEMENTED EARLY"
    )


    forbidden_early_terms = [
        "home_team_name",
        "away_team_name",
        "kickoff",
        "stage7_prob_home_win",
        "stage7_prob_draw",
        "stage7_prob_away_win",
        "stage7_predicted_label",
        "confidence_band",
        "uncertainty_band",
        "context_alignment",
        "explanation_summary",
        "/matches/",
    ]


    for term in forbidden_early_terms:

        check(
            f"MatchCard base excludes: {term}",
            term
            not in
            card_source,
            failures,
        )


    print(
        "\n8. SOURCE IDENTITY"
    )


    check(
        "Loader SHA current",
        loader_contract.get(
            "source_sha256"
        )
        ==
        sha256_file(
            LOADER_FILE
        ),
        failures,
    )


    check(
        "MatchCard SHA current",
        card_contract.get(
            "source_sha256"
        )
        ==
        sha256_file(
            MATCH_CARD_FILE
        ),
        failures,
    )


    print(
        "\n9. ROUTE PAGE PRESERVATION"
    )


    protected_pages = (
        loader_contract
        .get(
            "protected_state",
            {}
        )
        .get(
            "route_page_identity",
            {},
        )
    )


    check(
        "Protected route identity exists",
        isinstance(
            protected_pages,
            dict,
        )
        and
        bool(
            protected_pages
        ),
        failures,
    )


    check(
        "Route pages unchanged",
        protected_pages
        ==
        current_route_pages(),
        failures,
    )


    print(
        "\n10. STAGE 10.2 API LAYER PRESERVATION"
    )


    loader_protected = loader_contract.get(
        "protected_state",
        {}
    )


    check(
        "mapped.ts unchanged",
        loader_protected.get(
            "mapped_api_sha256"
        )
        ==
        sha256_file(
            MAPPED_FILE
        ),
        failures,
    )


    check(
        "result.ts unchanged",
        loader_protected.get(
            "result_api_sha256"
        )
        ==
        sha256_file(
            RESULT_FILE
        ),
        failures,
    )


    check(
        "validated.ts unchanged",
        loader_protected.get(
            "validated_api_sha256"
        )
        ==
        sha256_file(
            VALIDATED_FILE
        ),
        failures,
    )


    print(
        "\n11. PRESENTATION / AUTHORITY SAFETY"
    )


    combined_source = (
        loader_source
        +
        "\n"
        +
        card_source
    )


    forbidden_terms = [
        "data/processed",
        "data\\processed",
        "data/historical",
        "data\\historical",
        ".joblib",
        "football-data.org",
        "api-football",
        "api-sports",
    ]


    for term in forbidden_terms:

        check(
            f"10.4.1/10.4.2 excludes: {term}",
            term.lower()
            not in
            combined_source.lower(),
            failures,
        )


    check(
        "No probability arithmetic",
        re.search(
            (
                r"(?:probability|prob_|confidence)"
                r"[\w.]*\s*[\+\-\*/]"
            ),
            combined_source,
            re.IGNORECASE,
        )
        is None,
        failures,
    )


    print(
        "\n12. DEPENDENCY FRESHNESS"
    )


    verify_dependencies(
        loader_contract,
        "10.4.1",
        failures,
    )


    verify_dependencies(
        card_contract,
        "10.4.2",
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


    loader_promotion = (
        loader_contract.get(
            "promotion",
            {}
        )
    )

    card_promotion = (
        card_contract.get(
            "promotion",
            {}
        )
    )


    check(
        "10.4.1 did not self-promote",
        loader_promotion.get(
            "stage10_4_1_complete"
        )
        is False,
        failures,
    )


    check(
        "10.4.2 did not self-promote",
        card_promotion.get(
            "stage10_4_2_complete"
        )
        is False,
        failures,
    )


    check(
        "Stage 10.4 remains incomplete",
        (
            loader_promotion.get(
                "stage10_4_complete"
            )
            is False
            and
            card_promotion.get(
                "stage10_4_complete"
            )
            is False
        ),
        failures,
    )


    check(
        "Stage 10 remains incomplete",
        (
            loader_promotion.get(
                "stage10_complete"
            )
            is False
            and
            card_promotion.get(
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
                "10.4.1-10.4.2",

            "name":
                (
                    "UPCOMING_DASHBOARD_LOADER_"
                    "AND_MATCHCARD_BASE_VERIFICATION"
                ),

            "status":
                "PASS",

            "stage_10_4_1_complete":
                True,

            "stage_10_4_2_complete":
                True,

            "upcoming_dashboard_loader":
                "LOCKED_AND_VERIFIED",

            "match_card_base":
                "LOCKED_AND_VERIFIED",

            "mapped_upcoming_export":
                mapped_export,

            "authority": {
                "prediction":
                    "STAGE_7",

                "context":
                    "STAGE_8",

                "intelligence":
                    "STAGE_9",

                "presentation":
                    "STAGE_10",
            },

            "safety": {
                "direct_fetch":
                    False,

                "direct_artifact_access":
                    False,

                "provider_access":
                    False,

                "probability_mutation":
                    False,

                "response_transformation":
                    False,

                "stale_fallback":
                    False,

                "route_pages_modified":
                    False,
            },

            "later_features_implemented_early":
                False,

            "typescript_compiler":
                "PASS",

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "stage10_ready_for_10_4_3":
                True,

            "stage10_4_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.4.3",

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
            "STAGE 10.4.1: PASS"
        )

        print(
            "UPCOMING MATCHES DASHBOARD LOADER: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.4.2: PASS"
        )

        print(
            "MATCHCARD BASE: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.4.3"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.4.1 / 10.4.2: FAIL"
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


    sys.exit(
        0
        if passed
        else 1
    )


if __name__ == "__main__":

    main()
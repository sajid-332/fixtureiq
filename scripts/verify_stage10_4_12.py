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


EVIDENCE_FILES = [
    FRONTEND_DATA
    / "stage10_4_1_10_4_2_verification.json",

    FRONTEND_DATA
    / "stage10_4_3_10_4_4_verification.json",

    FRONTEND_DATA
    / "stage10_4_5_10_4_6_verification.json",

    FRONTEND_DATA
    / "stage10_4_7_10_4_8_verification.json",

    FRONTEND_DATA
    / "stage10_4_9_10_4_10_verification.json",
]


PREVIOUS_FILE = (
    EVIDENCE_FILES[-1]
)

DETAIL_LINK_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_detail_link_contract.json"
)

DASHBOARD_CONTRACT_FILE = (
    DOCS
    / "frontend_upcoming_dashboard_contract.json"
)

LOADER_CONTRACT_FILE = (
    DOCS
    / "frontend_upcoming_dashboard_loader_contract.json"
)


MATCH_CARD_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-card.tsx"
)

PAGE_FILE = (
    FRONTEND
    / "app"
    / "page.tsx"
)

EXTRACTOR_FILE = (
    FRONTEND
    / "lib"
    / "dashboard"
    / "upcoming-records.ts"
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

VALIDATION_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "validation.ts"
)

MAPPED_API_FILE = (
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

KICKOFF_FORMATTER_FILE = (
    FRONTEND
    / "lib"
    / "formatters"
    / "kickoff.ts"
)

PROBABILITY_FORMATTER_FILE = (
    FRONTEND
    / "lib"
    / "formatters"
    / "probability.ts"
)


OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_4_final_verification.json"
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

    with path.open("rb") as file:

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

    raw = Path(
        value
    )

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


def non_root_pages(
    pages: dict,
) -> dict:

    return {
        key:
            value

        for key, value
        in pages.items()

        if key
        !=
        "frontend/app/page.tsx"
    }


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


def npm_path() -> str | None:

    return (
        shutil.which(
            "npm.cmd"
        )
        or
        shutil.which(
            "npm"
        )
    )


def run_typescript_check() -> tuple[
    bool,
    str,
]:

    npm = npm_path()

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


def run_production_build() -> tuple[
    bool,
    str,
]:

    npm = npm_path()

    if npm is None:

        return (
            False,
            "npm executable not found.",
        )


    result = subprocess.run(
        [
            npm,
            "run",
            "build",
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
        "FixtureIQ Stage 10.4.12"
    )

    print(
        "FINAL UPCOMING MATCHES DASHBOARD VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        *EVIDENCE_FILES,
        DETAIL_LINK_CONTRACT_FILE,
        DASHBOARD_CONTRACT_FILE,
        LOADER_CONTRACT_FILE,
        MATCH_CARD_FILE,
        PAGE_FILE,
        EXTRACTOR_FILE,
        LOADER_FILE,
        DOMAIN_TYPES_FILE,
        VALIDATION_FILE,
        MAPPED_API_FILE,
        RESULT_FILE,
        KICKOFF_FORMATTER_FILE,
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

        sys.exit(
            1
        )


    evidence = [
        load_json(
            path
        )
        for path
        in EVIDENCE_FILES
    ]

    detail_contract = load_json(
        DETAIL_LINK_CONTRACT_FILE
    )

    dashboard_contract = load_json(
        DASHBOARD_CONTRACT_FILE
    )

    loader_contract = load_json(
        LOADER_CONTRACT_FILE
    )


    card_source = (
        MATCH_CARD_FILE.read_text(
            encoding="utf-8"
        )
    )

    page_source = (
        PAGE_FILE.read_text(
            encoding="utf-8"
        )
    )

    extractor_source = (
        EXTRACTOR_FILE.read_text(
            encoding="utf-8"
        )
    )

    loader_source = (
        LOADER_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. STAGE 10.4.1 - 10.4.10 FOUNDATION"
    )


    for index, item in enumerate(
        evidence,
        start=1,
    ):

        check(
            f"Prior dashboard evidence {index} PASS",
            item.get(
                "status"
            )
            ==
            "PASS",
            failures,
        )


    required_flags = [
        (
            evidence[0],
            "stage_10_4_1_complete",
        ),
        (
            evidence[0],
            "stage_10_4_2_complete",
        ),
        (
            evidence[1],
            "stage_10_4_3_complete",
        ),
        (
            evidence[1],
            "stage_10_4_4_complete",
        ),
        (
            evidence[2],
            "stage_10_4_5_complete",
        ),
        (
            evidence[2],
            "stage_10_4_6_complete",
        ),
        (
            evidence[3],
            "stage_10_4_7_complete",
        ),
        (
            evidence[3],
            "stage_10_4_8_complete",
        ),
        (
            evidence[4],
            "stage_10_4_9_complete",
        ),
        (
            evidence[4],
            "stage_10_4_10_complete",
        ),
    ]


    for item, key in required_flags:

        check(
            key,
            item.get(
                key
            )
            is True,
            failures,
        )


    check(
        "10.4.10 authorized 10.4.11",
        evidence[-1].get(
            "stage10_ready_for_10_4_11"
        )
        is True,
        failures,
    )


    print(
        "\n3. STAGE 10.4.11 DETAIL LINK CONTRACT"
    )


    check(
        "Detail-link stage exact",
        detail_contract.get(
            "stage"
        )
        ==
        "10.4.11",
        failures,
    )


    check(
        "Detail-link contract LOCKED",
        detail_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Detail route exact",
        detail_contract.get(
            "route_contract"
        )
        ==
        "/matches/[fixtureId]",
        failures,
    )


    check(
        "Detail-link domain type FixtureId",
        detail_contract.get(
            "domain_type"
        )
        ==
        "FixtureId",
        failures,
    )


    print(
        "\n4. MATCHCARD DETAIL LINK"
    )


    check(
        "Next Link imported",
        (
            'from "next/link"'
            in
            card_source
            or
            "from 'next/link'"
            in
            card_source
        ),
        failures,
    )


    check(
        "fixtureId prop present",
        re.search(
            (
                r"fixtureId\s*:\s*"
                r"FixtureId"
            ),
            card_source,
        )
        is not None,
        failures,
    )


    check(
        "fixtureId destructured",
        re.search(
            (
                r"MatchCard\s*\(\s*\{"
                r"[\s\S]*?\bfixtureId\b"
            ),
            card_source,
        )
        is not None,
        failures,
    )


    check(
        "Detail route uses /matches/",
        "/matches/"
        in
        card_source,
        failures,
    )


    check(
        "Fixture ID URL encoded",
        "encodeURIComponent"
        in
        card_source,
        failures,
    )


    check(
        "Fixture ID stringified",
        "String(fixtureId)"
        in
        re.sub(
            r"\s+",
            "",
            card_source,
        ),
        failures,
    )


    check(
        "Detail-link text present",
        "View match intelligence"
        in
        card_source,
        failures,
    )


    check(
        "Current MatchCard SHA exact",
        detail_contract.get(
            "match_card_after_detail_link_sha256"
        )
        ==
        sha256_file(
            MATCH_CARD_FILE
        ),
        failures,
    )


    print(
        "\n5. STAGE 10.4.12 ASSEMBLY CONTRACT"
    )


    check(
        "Dashboard stage exact",
        dashboard_contract.get(
            "stage"
        )
        ==
        "10.4.12",
        failures,
    )


    check(
        "Dashboard assembly LOCKED",
        dashboard_contract.get(
            "status"
        )
        ==
        "LOCKED_ASSEMBLY",
        failures,
    )


    check(
        "Upcoming intelligence API authority exact",
        dashboard_contract.get(
            "api_authority"
        )
        ==
        "/api/v1/intelligence/upcoming",
        failures,
    )


    check(
        "Loader authority exact",
        dashboard_contract.get(
            "loader_authority"
        )
        ==
        "loadUpcomingMatches",
        failures,
    )


    print(
        "\n6. DASHBOARD PAGE INTEGRATION"
    )


    check(
        "Dashboard loader imported",
        "loadUpcomingMatches"
        in
        page_source,
        failures,
    )


    check(
        "Dashboard loader awaited",
        re.search(
            (
                r"await\s+"
                r"loadUpcomingMatches\s*\(\s*\)"
            ),
            page_source,
        )
        is not None,
        failures,
    )


    check(
        "Dashboard extractor imported",
        "extractUpcomingDashboardMatches"
        in
        page_source,
        failures,
    )


    check(
        "READY data passed into extractor",
        re.search(
            (
                r"extractUpcomingDashboardMatches"
                r"\s*\(\s*"
                r"result\.data"
            ),
            page_source,
        )
        is not None,
        failures,
    )


    check(
        "Non-READY fails closed before data use",
        (
            'result.state !=='
            in
            page_source
            and
            '"READY"'
            in
            page_source
        ),
        failures,
    )


    check(
        "No stale payload variable",
        "previousData"
        not in
        page_source
        and
        "staleData"
        not in
        page_source,
        failures,
    )


    check(
        "Force-dynamic server rendering",
        (
            'export const dynamic'
            in
            page_source
            and
            '"force-dynamic"'
            in
            page_source
        ),
        failures,
    )


    check(
        "MatchCard rendered",
        "<MatchCard"
        in
        page_source,
        failures,
    )


    print(
        "\n7. AUTHORITATIVE FIELD MAPPING"
    )


    expected_mappings = [
        (
            "fixtureId",
            "match.fixture_id",
        ),
        (
            "homeTeamName",
            "match.home_team_name",
        ),
        (
            "awayTeamName",
            "match.away_team_name",
        ),
        (
            "kickoffUtc",
            "match.kickoffUtc",
        ),
        (
            "stage7_prob_home_win",
            "match.stage7_prob_home_win",
        ),
        (
            "stage7_prob_draw",
            "match.stage7_prob_draw",
        ),
        (
            "stage7_prob_away_win",
            "match.stage7_prob_away_win",
        ),
        (
            "stage7_predicted_label",
            "match.stage7_predicted_label",
        ),
        (
            "stage7_confidence",
            "match.stage7_confidence",
        ),
        (
            "confidence_band",
            "match.stage9_confidence_band",
        ),
        (
            "uncertainty_band",
            "match.stage9_uncertainty_band",
        ),
        (
            "context_alignment",
            "match.stage9_context_alignment",
        ),
        (
            "explanation_headline",
            "match.stage9_explanation_headline",
        ),
        (
            "explanation_summary",
            "match.stage9_explanation_summary",
        ),
    ]


    compact_page = re.sub(
        r"\s+",
        "",
        page_source,
    )


    for prop, source_field in expected_mappings:

        expected = (
            f"{prop}={{"
            f"{source_field}"
            f"}}"
        )


        check(
            f"Exact mapping: {prop}",
            expected
            in
            compact_page,
            failures,
        )


    print(
        "\n8. EXTRACTOR INTEGRITY"
    )


    kickoff = (
        dashboard_contract
        .get(
            "kickoff",
            {}
        )
    )


    kickoff_field = (
        kickoff.get(
            "source_field"
        )
    )


    check(
        "Kickoff source field recorded",
        isinstance(
            kickoff_field,
            str,
        )
        and
        bool(
            kickoff_field
        ),
        failures,
    )


    check(
        "Kickoff source constant exact",
        isinstance(
            kickoff_field,
            str,
        )
        and
        (
            f'"{kickoff_field}" as const'
            in
            extractor_source
        ),
        failures,
    )


    check(
        "Kickoff fallback prohibited",
        kickoff.get(
            "frontend_fallback"
        )
        is False,
        failures,
    )


    for field in [
        "fixture_id",
        "home_team_name",
        "away_team_name",
        "stage7_prob_home_win",
        "stage7_prob_draw",
        "stage7_prob_away_win",
        "stage7_predicted_label",
        "stage7_confidence",
        "stage9_top_probability",
        "stage9_probability_margin",
        "stage9_confidence_band",
        "stage9_uncertainty_band",
        "stage9_context_support_score",
        "stage9_context_alignment",
        "stage9_explanation_headline",
        "stage9_explanation_summary",
    ]:

        check(
            f"Extractor preserves: {field}",
            field
            in
            extractor_source,
            failures,
        )


    check(
        "Duplicate fixture protection",
        (
            "seen.has"
            in
            extractor_source
            and
            "seen.add"
            in
            extractor_source
        ),
        failures,
    )


    check(
        "Transport numeric fields normalized",
        (
            "NUMERIC_TRANSPORT_FIELDS"
            in
            extractor_source
            and
            "normalizeTransportRecord"
            in
            extractor_source
            and
            "Number("
            in
            re.sub(
                r"\s+",
                "",
                extractor_source,
            )
        ),
        failures,
    )


    check(
        "Transport normalization copies source record",
        (
            "...value"
            in
            re.sub(
                r"\s+",
                "",
                extractor_source,
            )
        ),
        failures,
    )


    check(
        "No probability renormalization",
        (
            "normalizeProbability"
            not in
            extractor_source
            and
            "renormal"
            not in
            extractor_source.lower()
        ),
        failures,
    )


    check(
        "No extractor sorting",
        ".sort("
        not in
        extractor_source,
        failures,
    )


    check(
        "No frontend argmax",
        "Math.max"
        not in
        extractor_source
        and
        "Math.max"
        not in
        page_source,
        failures,
    )


    print(
        "\n9. LOADER / API CLIENT PRESERVATION"
    )


    protected = dashboard_contract.get(
        "protected_state",
        {},
    )


    protected_checks = [
        (
            "Dashboard loader",
            LOADER_FILE,
            "loader_sha256",
        ),
        (
            "Domain types",
            DOMAIN_TYPES_FILE,
            "domain_types_sha256",
        ),
        (
            "Runtime validation",
            VALIDATION_FILE,
            "validation_sha256",
        ),
        (
            "Mapped API",
            MAPPED_API_FILE,
            "mapped_api_sha256",
        ),
        (
            "Result mapping",
            RESULT_FILE,
            "result_sha256",
        ),
        (
            "Kickoff formatter",
            KICKOFF_FORMATTER_FILE,
            "kickoff_formatter_sha256",
        ),
        (
            "Probability formatter",
            PROBABILITY_FORMATTER_FILE,
            "probability_formatter_sha256",
        ),
    ]


    for label, path, key in protected_checks:

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


    check(
        "Loader still uses mapped API layer",
        (
            "api/mapped"
            in
            loader_source
            or
            "../api/mapped"
            in
            loader_source
        ),
        failures,
    )


    check(
        "Loader has no direct fetch",
        re.search(
            r"\bfetch\s*\(",
            loader_source,
        )
        is None,
        failures,
    )


    print(
        "\n10. ROUTE TRANSITION SAFETY"
    )


    check(
        "Root page transition SHA exact",
        dashboard_contract
        .get(
            "page_after_dashboard_sha256"
        )
        ==
        sha256_file(
            PAGE_FILE
        ),
        failures,
    )


    check(
        "Non-root route pages unchanged",
        protected.get(
            "non_root_route_page_identity"
        )
        ==
        non_root_pages(
            current_route_pages()
        ),
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
        page_source
        +
        "\n"
        +
        extractor_source
    )


    check(
        "No direct fetch",
        re.search(
            r"\bfetch\s*\(",
            combined_source,
        )
        is None,
        failures,
    )


    check(
        "No provider calls",
        all(
            term
            not in
            combined_source.lower()

            for term in [
                "football-data.org",
                "api-football",
                "api-sports",
            ]
        ),
        failures,
    )


    check(
        "No artifact reads",
        all(
            term
            not in
            combined_source.lower()

            for term in [
                "data/processed",
                "data\\processed",
                "data/historical",
                "data\\historical",
                ".joblib",
                ".csv",
            ]
        ),
        failures,
    )


    probability_arithmetic = re.search(
        (
            r"stage7_prob_"
            r"(?:home_win|draw|away_win)"
            r"\s*[\+\-\*/]"
            r"|"
            r"[\+\-\*/]\s*"
            r"stage7_prob_"
            r"(?:home_win|draw|away_win)"
        ),
        combined_source,
    )


    check(
        "No probability arithmetic",
        probability_arithmetic
        is None,
        failures,
    )


    check(
        "No prediction recalculation",
        (
            "argmax"
            not in
            combined_source.lower()
            and
            "recalibr"
            not in
            combined_source.lower()
        ),
        failures,
    )


    print(
        "\n12. DEPENDENCY FRESHNESS"
    )


    verify_dependencies(
        detail_contract,
        "10.4.11",
        failures,
    )


    verify_dependencies(
        dashboard_contract,
        "10.4.12",
        failures,
    )


    print(
        "\n13. TYPESCRIPT"
    )


    typescript_ok, typescript_output = (
        run_typescript_check()
    )


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
        "\n14. PRODUCTION BUILD"
    )


    build_ok = False
    build_output = ""


    if typescript_ok:

        (
            build_ok,
            build_output,
        ) = run_production_build()


    check(
        "Next production build",
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
        "\n15. NO PREVIOUS PREMATURE PROMOTION"
    )


    check(
        "10.4.11 did not self-promote",
        detail_contract
        .get(
            "promotion",
            {},
        )
        .get(
            "stage10_4_11_complete"
        )
        is False,
        failures,
    )


    check(
        "10.4.12 assembly did not self-promote",
        dashboard_contract
        .get(
            "promotion",
            {},
        )
        .get(
            "stage10_4_12_complete"
        )
        is False,
        failures,
    )


    check(
        "Stage 10 not previously promoted",
        dashboard_contract
        .get(
            "promotion",
            {},
        )
        .get(
            "stage10_complete"
        )
        is False,
        failures,
    )


    print(
        "\n16. FINAL STAGE 10.4 PROMOTION"
    )


    passed = (
        len(
            failures
        )
        ==
        0
    )


    if passed:

        final_report = {
            "stage":
                "10.4.12",

            "name":
                (
                    "FINAL_UPCOMING_MATCHES_"
                    "DASHBOARD_VERIFICATION"
                ),

            "status":
                "PASS",

            "stage_10_4_1_complete":
                True,

            "stage_10_4_2_complete":
                True,

            "stage_10_4_3_complete":
                True,

            "stage_10_4_4_complete":
                True,

            "stage_10_4_5_complete":
                True,

            "stage_10_4_6_complete":
                True,

            "stage_10_4_7_complete":
                True,

            "stage_10_4_8_complete":
                True,

            "stage_10_4_9_complete":
                True,

            "stage_10_4_10_complete":
                True,

            "stage_10_4_11_complete":
                True,

            "stage_10_4_12_complete":
                True,

            "upcoming_matches_dashboard":
                "VERIFIED",

            "detail_links":
                "VERIFIED",

            "dashboard_loader":
                "VERIFIED",

            "backend_authority": {
                "prediction":
                    "STAGE_7",

                "context":
                    "STAGE_8",

                "intelligence":
                    "STAGE_9",

                "presentation":
                    "STAGE_10",
            },

            "integrity": {
                "probabilities_modified":
                    False,

                "prediction_label_modified":
                    False,

                "confidence_modified":
                    False,

                "confidence_band_derived_frontend":
                    False,

                "uncertainty_derived_frontend":
                    False,

                "context_alignment_derived_frontend":
                    False,

                "explanation_generated_frontend":
                    False,

                "stale_fallback":
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

            "production_build":
                "PASS",

            "stage10_4_complete":
                True,

            "stage10_ready_for_10_5_1":
                True,

            "stage10_complete":
                False,

            "next_stage":
                "10.5.1",

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "failures":
                [],
        }


        save_json_atomic(
            OUTPUT_FILE,
            final_report,
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
            "STAGE 10.4.11: PASS"
        )

        print(
            "DETAIL LINKS: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.4.12: PASS"
        )

        print(
            "UPCOMING MATCHES DASHBOARD: VERIFIED"
        )

        print()

        print(
            "STAGE 10.4: COMPLETE"
        )

        print(
            "STAGE 10 READY FOR 10.5.1"
        )

        print()

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.4.12: FAIL"
        )

        print(
            "STAGE 10.4: INCOMPLETE"
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
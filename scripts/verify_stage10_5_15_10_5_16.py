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


VERIFY_1_2_FILE = (
    FRONTEND_DATA
    / "stage10_5_1_10_5_2_verification.json"
)

VERIFY_3_6_FILE = (
    FRONTEND_DATA
    / "stage10_5_3_10_5_6_verification.json"
)

VERIFY_7_10_FILE = (
    FRONTEND_DATA
    / "stage10_5_7_10_5_10_verification.json"
)

VERIFY_11_14_FILE = (
    FRONTEND_DATA
    / "stage10_5_11_10_5_14_verification.json"
)


STATUS_CONTRACT_FILE = (
    DOCS
    / "frontend_match_freshness_status_contract.json"
)

EXPLANATION_CONTRACT_FILE = (
    DOCS
    / "frontend_match_deterministic_explanation_contract.json"
)


ROUTE_PAGE_FILE = (
    FRONTEND
    / "app"
    / "matches"
    / "[fixtureId]"
    / "page.tsx"
)

MATCH_LOADER_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "load-match-intelligence.ts"
)

STATUS_LOADER_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "load-intelligence-status.ts"
)


HEADER_RECORD_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "match-header-record.ts"
)

PREDICTION_RECORD_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "match-prediction-record.ts"
)

CONTEXT_RECORD_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "match-context-record.ts"
)

INTELLIGENCE_RECORD_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "match-intelligence-detail-record.ts"
)


HEADER_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-fixture-header.tsx"
)

OVERVIEW_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-prediction-overview.tsx"
)

PROBABILITY_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-probability-visualization.tsx"
)

CONFIDENCE_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-confidence.tsx"
)

UNCERTAINTY_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-uncertainty.tsx"
)

LEAGUE_POSITION_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-league-position-comparison.tsx"
)

POINTS_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-points-comparison.tsx"
)

GOAL_DIFFERENCE_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-goal-difference-comparison.tsx"
)

RECENT_FORM_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-recent-form.tsx"
)

VENUE_FORM_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-venue-form.tsx"
)

CONTEXT_SUPPORT_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-context-support.tsx"
)

ALIGNMENT_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-context-alignment.tsx"
)

EXPLANATION_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-intelligence-explanation.tsx"
)

STATUS_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-freshness-status.tsx"
)


DOMAIN_TYPES_FILE = (
    FRONTEND
    / "lib"
    / "domain"
    / "types.ts"
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

CLIENT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "client.ts"
)


OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_5_final_verification.json"
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

    # Stage 10.2.2 requires an explicit server-side API
    # base URL in production mode. This value exists only
    # for the build verification subprocess.
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
        "FixtureIQ Stage 10.5.15 + 10.5.16"
    )

    print(
        "FRESHNESS / STATUS + FINAL MATCH DETAIL VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        VERIFY_1_2_FILE,
        VERIFY_3_6_FILE,
        VERIFY_7_10_FILE,
        VERIFY_11_14_FILE,
        STATUS_CONTRACT_FILE,
        EXPLANATION_CONTRACT_FILE,
        ROUTE_PAGE_FILE,
        MATCH_LOADER_FILE,
        STATUS_LOADER_FILE,
        HEADER_RECORD_FILE,
        PREDICTION_RECORD_FILE,
        CONTEXT_RECORD_FILE,
        INTELLIGENCE_RECORD_FILE,
        HEADER_COMPONENT_FILE,
        OVERVIEW_COMPONENT_FILE,
        PROBABILITY_COMPONENT_FILE,
        CONFIDENCE_COMPONENT_FILE,
        UNCERTAINTY_COMPONENT_FILE,
        LEAGUE_POSITION_COMPONENT_FILE,
        POINTS_COMPONENT_FILE,
        GOAL_DIFFERENCE_COMPONENT_FILE,
        RECENT_FORM_COMPONENT_FILE,
        VENUE_FORM_COMPONENT_FILE,
        CONTEXT_SUPPORT_COMPONENT_FILE,
        ALIGNMENT_COMPONENT_FILE,
        EXPLANATION_COMPONENT_FILE,
        STATUS_COMPONENT_FILE,
        DOMAIN_TYPES_FILE,
        MAPPED_API_FILE,
        RESULT_FILE,
        CLIENT_FILE,
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


    verify_1_2 = load_json(
        VERIFY_1_2_FILE
    )

    verify_3_6 = load_json(
        VERIFY_3_6_FILE
    )

    verify_7_10 = load_json(
        VERIFY_7_10_FILE
    )

    verify_11_14 = load_json(
        VERIFY_11_14_FILE
    )

    status_contract = load_json(
        STATUS_CONTRACT_FILE
    )

    explanation_contract = load_json(
        EXPLANATION_CONTRACT_FILE
    )


    route_source = (
        ROUTE_PAGE_FILE.read_text(
            encoding="utf-8"
        )
    )

    status_loader_source = (
        STATUS_LOADER_FILE.read_text(
            encoding="utf-8"
        )
    )

    status_component_source = (
        STATUS_COMPONENT_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. PREVIOUS STAGE 10.5 VERIFICATION CHAIN"
    )


    prior_groups = [
        (
            "10.5.1-10.5.2",
            verify_1_2,
            [
                "stage_10_5_1_complete",
                "stage_10_5_2_complete",
            ],
        ),
        (
            "10.5.3-10.5.6",
            verify_3_6,
            [
                "stage_10_5_3_complete",
                "stage_10_5_4_complete",
                "stage_10_5_5_complete",
                "stage_10_5_6_complete",
            ],
        ),
        (
            "10.5.7-10.5.10",
            verify_7_10,
            [
                "stage_10_5_7_complete",
                "stage_10_5_8_complete",
                "stage_10_5_9_complete",
                "stage_10_5_10_complete",
            ],
        ),
        (
            "10.5.11-10.5.14",
            verify_11_14,
            [
                "stage_10_5_11_complete",
                "stage_10_5_12_complete",
                "stage_10_5_13_complete",
                "stage_10_5_14_complete",
            ],
        ),
    ]


    for label, report, flags in prior_groups:

        check(
            f"{label} verification PASS",
            report.get(
                "status"
            )
            ==
            "PASS",
            failures,
        )


        for flag in flags:

            check(
                f"{label}: {flag}",
                report.get(
                    flag
                )
                is True,
                failures,
            )


    check(
        "10.5.14 authorized 10.5.15",
        verify_11_14.get(
            "stage10_ready_for_10_5_15"
        )
        is True,
        failures,
    )


    print(
        "\n3. STAGE 10.5.15 CONTRACT"
    )


    check(
        "10.5.15 stage exact",
        status_contract.get(
            "stage"
        )
        ==
        "10.5.15",
        failures,
    )


    check(
        "10.5.15 contract LOCKED",
        status_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Freshness authority Stage 9 runtime",
        status_contract.get(
            "backend_authority"
        )
        ==
        "STAGE_9_RUNTIME_FRESHNESS",
        failures,
    )


    check(
        "Status endpoint exact",
        status_contract.get(
            "backend_endpoint"
        )
        ==
        "/api/v1/intelligence/status",
        failures,
    )


    check(
        "Mapped status client exact",
        status_contract.get(
            "mapped_client"
        )
        ==
        "getIntelligenceStatusResult",
        failures,
    )


    print(
        "\n4. STATUS LOADER"
    )


    check(
        "Status loader server-only",
        'import "server-only"'
        in
        status_loader_source,
        failures,
    )


    check(
        "Mapped intelligence status used",
        "getIntelligenceStatusResult"
        in
        status_loader_source,
        failures,
    )


    check(
        "No direct fetch in status loader",
        re.search(
            r"\bfetch\s*\(",
            status_loader_source,
        )
        is None,
        failures,
    )


    print(
        "\n5. STATUS COMPONENT"
    )


    check(
        "ApiTerminalState used",
        "ApiTerminalState"
        in
        status_component_source,
        failures,
    )


    check(
        "Null HTTP status handled",
        (
            "httpStatus === null"
            in
            status_component_source
            and
            "No HTTP response"
            in
            status_component_source
        ),
        failures,
    )


    check(
        "Runtime state displayed directly",
        "{state}"
        in
        status_component_source,
        failures,
    )


    check(
        "Freshness component marker",
        (
            'data-fixtureiq-component="match-freshness-status"'
            in
            status_component_source
        ),
        failures,
    )


    check(
        "No frontend freshness timestamp",
        all(
            term
            not in
            status_component_source

            for term in [
                "Date.now",
                "new Date",
                "updated_at",
                "last_updated",
                "generated_at",
                "expires_at",
            ]
        ),
        failures,
    )


    check(
        "No frontend TTL",
        "ttl"
        not in
        status_component_source.lower(),
        failures,
    )


    print(
        "\n6. ROUTE FRESHNESS INTEGRATION"
    )


    check(
        "Status loader imported",
        "loadIntelligenceStatus"
        in
        route_source,
        failures,
    )


    check(
        "Status request awaited",
        re.search(
            (
                r"await\s+"
                r"loadIntelligenceStatus"
                r"\s*\("
            ),
            route_source,
        )
        is not None,
        failures,
    )


    check(
        "Freshness component rendered",
        "<MatchFreshnessStatus"
        in
        route_source,
        failures,
    )


    check(
        "Runtime state direct mapping",
        "statusResult.state"
        in
        route_source,
        failures,
    )


    check(
        "HTTP status direct mapping",
        "statusResult.status"
        in
        route_source,
        failures,
    )


    print(
        "\n7. FINAL MATCH DETAIL PAGE COMPONENT COVERAGE"
    )


    required_components = [
        "MatchFixtureHeader",
        "MatchPredictionOverview",
        "MatchProbabilityVisualization",
        "MatchConfidence",
        "MatchUncertainty",
        "MatchLeaguePositionComparison",
        "MatchPointsComparison",
        "MatchGoalDifferenceComparison",
        "MatchRecentForm",
        "MatchVenueForm",
        "MatchContextSupport",
        "MatchContextAlignment",
        "MatchIntelligenceExplanation",
        "MatchFreshnessStatus",
    ]


    for component in required_components:

        check(
            f"Detail page renders {component}",
            f"<{component}"
            in
            route_source,
            failures,
        )


    print(
        "\n8. DETAIL ROUTE RUNTIME SAFETY"
    )


    check(
        "Route force-dynamic",
        (
            'export const dynamic'
            in
            route_source
            and
            '"force-dynamic"'
            in
            route_source
        ),
        failures,
    )


    check(
        "Match endpoint result awaited",
        re.search(
            (
                r"await\s+"
                r"loadMatchIntelligence"
                r"\s*\("
            ),
            route_source,
        )
        is not None,
        failures,
    )


    check(
        "404 uses notFound()",
        (
            "NOT_FOUND"
            in
            route_source
            and
            "notFound();"
            in
            route_source
        ),
        failures,
    )


    check(
        "Non-READY match response fails closed",
        (
            'result.state !=='
            in
            route_source
            and
            '"READY"'
            in
            route_source
        ),
        failures,
    )


    check(
        "No direct fetch in route",
        re.search(
            r"\bfetch\s*\(",
            route_source,
        )
        is None,
        failures,
    )


    print(
        "\n9. NO STALE FALLBACK"
    )


    combined_sources = "\n".join(
        path.read_text(
            encoding="utf-8"
        )

        for path in [
            ROUTE_PAGE_FILE,
            MATCH_LOADER_FILE,
            STATUS_LOADER_FILE,
            HEADER_RECORD_FILE,
            PREDICTION_RECORD_FILE,
            CONTEXT_RECORD_FILE,
            INTELLIGENCE_RECORD_FILE,
            STATUS_COMPONENT_FILE,
        ]
    )


    for forbidden in [
        "localStorage",
        "sessionStorage",
        "cachedPrevious",
        "previousResponse",
        "previousData",
        "staleData",
        "fallbackData",
    ]:

        check(
            f"No stale fallback mechanism: {forbidden}",
            forbidden
            not in
            combined_sources,
            failures,
        )


    print(
        "\n10. AUTHORITY BOUNDARY"
    )


    check(
        "No client component directives",
        (
            '"use client"'
            not in
            combined_sources
            and
            "'use client'"
            not in
            combined_sources
        ),
        failures,
    )


    check(
        "No provider access",
        all(
            term
            not in
            combined_sources.lower()

            for term in [
                "football-data.org",
                "api-football",
                "api-sports",
            ]
        ),
        failures,
    )


    check(
        "No direct artifact access",
        all(
            term
            not in
            combined_sources.lower()

            for term in [
                "data/processed",
                "data\\processed",
                ".csv",
                ".joblib",
            ]
        ),
        failures,
    )


    check(
        "No prediction argmax",
        "Math.max"
        not in
        combined_sources,
        failures,
    )


    check(
        "No probability recalibration",
        "recalibr"
        not in
        combined_sources.lower(),
        failures,
    )


    print(
        "\n11. 10.5.15 SOURCE IDENTITY"
    )


    check(
        "Status component SHA exact",
        status_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            STATUS_COMPONENT_FILE
        ),
        failures,
    )


    check(
        "Status loader SHA exact",
        status_contract.get(
            "loader_sha256"
        )
        ==
        sha256_file(
            STATUS_LOADER_FILE
        ),
        failures,
    )


    check(
        "Detail route SHA exact",
        status_contract.get(
            "route_page_after_10_5_15_sha256"
        )
        ==
        sha256_file(
            ROUTE_PAGE_FILE
        ),
        failures,
    )


    check(
        "10.5.15 started from verified 10.5.14",
        status_contract.get(
            "route_page_before_10_5_15_sha256"
        )
        ==
        explanation_contract.get(
            "route_page_after_10_5_14_sha256"
        ),
        failures,
    )


    print(
        "\n12. PREVIOUS SOURCE PROTECTION"
    )


    protected = status_contract.get(
        "protected_state",
        {},
    )


    protected_sources = [
        (
            "Match loader",
            MATCH_LOADER_FILE,
            "match_loader_sha256",
        ),
        (
            "Header component",
            HEADER_COMPONENT_FILE,
            "header_component_sha256",
        ),
        (
            "Header record",
            HEADER_RECORD_FILE,
            "header_record_sha256",
        ),
        (
            "Prediction record",
            PREDICTION_RECORD_FILE,
            "prediction_record_sha256",
        ),
        (
            "Context record",
            CONTEXT_RECORD_FILE,
            "context_record_sha256",
        ),
        (
            "Intelligence record",
            INTELLIGENCE_RECORD_FILE,
            "intelligence_record_sha256",
        ),
        (
            "Prediction overview",
            OVERVIEW_COMPONENT_FILE,
            "prediction_overview_sha256",
        ),
        (
            "Probability visualization",
            PROBABILITY_COMPONENT_FILE,
            "probability_visualization_sha256",
        ),
        (
            "Confidence",
            CONFIDENCE_COMPONENT_FILE,
            "confidence_sha256",
        ),
        (
            "Uncertainty",
            UNCERTAINTY_COMPONENT_FILE,
            "uncertainty_sha256",
        ),
        (
            "League position",
            LEAGUE_POSITION_COMPONENT_FILE,
            "league_position_sha256",
        ),
        (
            "Points",
            POINTS_COMPONENT_FILE,
            "points_sha256",
        ),
        (
            "Goal difference",
            GOAL_DIFFERENCE_COMPONENT_FILE,
            "goal_difference_sha256",
        ),
        (
            "Recent form",
            RECENT_FORM_COMPONENT_FILE,
            "recent_form_sha256",
        ),
        (
            "Venue form",
            VENUE_FORM_COMPONENT_FILE,
            "venue_form_sha256",
        ),
        (
            "Context support",
            CONTEXT_SUPPORT_COMPONENT_FILE,
            "context_support_sha256",
        ),
        (
            "Alignment",
            ALIGNMENT_COMPONENT_FILE,
            "alignment_sha256",
        ),
        (
            "Explanation",
            EXPLANATION_COMPONENT_FILE,
            "explanation_sha256",
        ),
        (
            "Domain types",
            DOMAIN_TYPES_FILE,
            "domain_types_sha256",
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
        "\n13. DEPENDENCY FRESHNESS"
    )


    verify_dependencies(
        status_contract,
        "10.5.15",
        failures,
    )


    print(
        "\n14. TYPESCRIPT"
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
        "\n15. PRODUCTION BUILD"
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
        "\n16. NO PREMATURE PROMOTION"
    )


    promotion = status_contract.get(
        "promotion",
        {},
    )


    check(
        "10.5.15 did not self-promote",
        promotion.get(
            "stage10_5_15_complete"
        )
        is False,
        failures,
    )


    check(
        "Stage 10.5 not already promoted",
        promotion.get(
            "stage10_5_complete"
        )
        is False,
        failures,
    )


    check(
        "Stage 10 not already promoted",
        promotion.get(
            "stage10_complete"
        )
        is False,
        failures,
    )


    print(
        "\n17. FINAL STAGE 10.5 DECISION"
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
                "10.5.16",

            "name":
                "MATCH_INTELLIGENCE_DETAIL_PAGE_FINAL_VERIFICATION",

            "status":
                "PASS",

            "stage_10_5_1_complete":
                True,

            "stage_10_5_2_complete":
                True,

            "stage_10_5_3_complete":
                True,

            "stage_10_5_4_complete":
                True,

            "stage_10_5_5_complete":
                True,

            "stage_10_5_6_complete":
                True,

            "stage_10_5_7_complete":
                True,

            "stage_10_5_8_complete":
                True,

            "stage_10_5_9_complete":
                True,

            "stage_10_5_10_complete":
                True,

            "stage_10_5_11_complete":
                True,

            "stage_10_5_12_complete":
                True,

            "stage_10_5_13_complete":
                True,

            "stage_10_5_14_complete":
                True,

            "stage_10_5_15_complete":
                True,

            "stage_10_5_16_complete":
                True,

            "dynamic_match_route":
                "VERIFIED",

            "fixture_header":
                "VERIFIED",

            "prediction_overview":
                "VERIFIED",

            "three_way_visualization":
                "VERIFIED",

            "confidence":
                "VERIFIED",

            "uncertainty":
                "VERIFIED",

            "league_position_comparison":
                "VERIFIED",

            "points_comparison":
                "VERIFIED",

            "goal_difference_comparison":
                "VERIFIED",

            "recent_form":
                "VERIFIED",

            "venue_form":
                "VERIFIED",

            "context_support":
                "VERIFIED",

            "context_alignment":
                "VERIFIED",

            "deterministic_explanation":
                "VERIFIED",

            "freshness_status":
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

                "stale_fallback":
                    False,

                "frontend_prediction_derivation":
                    False,

                "frontend_probability_modification":
                    False,

                "frontend_context_recalculation":
                    False,

                "frontend_explanation_generation":
                    False,
            },

            "typescript_compiler":
                "PASS",

            "production_build":
                "PASS",

            "stage10_5_complete":
                True,

            "stage10_ready_for_10_6_1":
                True,

            "stage10_complete":
                False,

            "next_stage":
                "10.6.1",

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
            "STAGE 10.5.15: PASS"
        )

        print(
            "FRESHNESS / STATUS: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.5.16: PASS"
        )

        print(
            "MATCH INTELLIGENCE DETAIL PAGE: VERIFIED"
        )

        print()

        print(
            "STAGE 10.5: COMPLETE"
        )

        print(
            "STAGE 10 READY FOR 10.6.1"
        )

        print()

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.5.15 / 10.5.16: FAIL"
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
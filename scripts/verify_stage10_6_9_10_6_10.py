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
    / "stage10_6_1_10_6_4_verification.json"
)

VERIFY_5_8_FILE = (
    FRONTEND_DATA
    / "stage10_6_5_10_6_8_verification.json"
)

UNKNOWN_TEAM_CONTRACT_FILE = (
    DOCS
    / "frontend_team_unknown_team_contract.json"
)

FIXTURE_LINKS_CONTRACT_FILE = (
    DOCS
    / "frontend_team_fixture_links_contract.json"
)

IDENTITY_CONTRACT_FILE = (
    DOCS
    / "frontend_team_identity_header_contract.json"
)

UPCOMING_CONTRACT_FILE = (
    DOCS
    / "frontend_team_upcoming_matches_contract.json"
)

STANDINGS_CONTRACT_FILE = (
    DOCS
    / "frontend_team_standings_contract.json"
)

RECENT_FORM_CONTRACT_FILE = (
    DOCS
    / "frontend_team_recent_form_contract.json"
)

VENUE_FORM_CONTRACT_FILE = (
    DOCS
    / "frontend_team_home_away_form_contract.json"
)


TEAM_ROUTE_FILE = (
    FRONTEND
    / "app"
    / "teams"
    / "[teamName]"
    / "page.tsx"
)

TEAM_NOT_FOUND_FILE = (
    FRONTEND
    / "app"
    / "teams"
    / "[teamName]"
    / "not-found.tsx"
)


TEAM_LOADER_FILE = (
    FRONTEND
    / "lib"
    / "teams"
    / "load-team-intelligence.ts"
)

TEAM_CONTEXT_LOADER_FILE = (
    FRONTEND
    / "lib"
    / "teams"
    / "load-team-context.ts"
)

TEAM_RECORDS_FILE = (
    FRONTEND
    / "lib"
    / "teams"
    / "team-records.ts"
)

TEAM_CONTEXT_RECORDS_FILE = (
    FRONTEND
    / "lib"
    / "teams"
    / "team-context-records.ts"
)


TEAM_HEADER_FILE = (
    FRONTEND
    / "components"
    / "teams"
    / "team-identity-header.tsx"
)

TEAM_UPCOMING_FILE = (
    FRONTEND
    / "components"
    / "teams"
    / "team-upcoming-matches.tsx"
)

TEAM_PREDICTION_CARD_FILE = (
    FRONTEND
    / "components"
    / "teams"
    / "team-prediction-card.tsx"
)

TEAM_STANDINGS_FILE = (
    FRONTEND
    / "components"
    / "teams"
    / "team-standings.tsx"
)

TEAM_RECENT_FORM_FILE = (
    FRONTEND
    / "components"
    / "teams"
    / "team-recent-form.tsx"
)

TEAM_VENUE_FORM_FILE = (
    FRONTEND
    / "components"
    / "teams"
    / "team-home-away-form.tsx"
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

DOMAIN_TYPES_FILE = (
    FRONTEND
    / "lib"
    / "domain"
    / "types.ts"
)


OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_6_final_verification.json"
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
        "FixtureIQ Stage 10.6.9 + 10.6.10"
    )

    print(
        "UNKNOWN TEAM + FINAL TEAM INTELLIGENCE VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        VERIFY_1_4_FILE,
        VERIFY_5_8_FILE,
        UNKNOWN_TEAM_CONTRACT_FILE,
        FIXTURE_LINKS_CONTRACT_FILE,
        IDENTITY_CONTRACT_FILE,
        UPCOMING_CONTRACT_FILE,
        STANDINGS_CONTRACT_FILE,
        RECENT_FORM_CONTRACT_FILE,
        VENUE_FORM_CONTRACT_FILE,
        TEAM_ROUTE_FILE,
        TEAM_NOT_FOUND_FILE,
        TEAM_LOADER_FILE,
        TEAM_CONTEXT_LOADER_FILE,
        TEAM_RECORDS_FILE,
        TEAM_CONTEXT_RECORDS_FILE,
        TEAM_HEADER_FILE,
        TEAM_UPCOMING_FILE,
        TEAM_PREDICTION_CARD_FILE,
        TEAM_STANDINGS_FILE,
        TEAM_RECENT_FORM_FILE,
        TEAM_VENUE_FORM_FILE,
        MAPPED_API_FILE,
        RESULT_FILE,
        DOMAIN_TYPES_FILE,
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

    unknown_contract = load_json(
        UNKNOWN_TEAM_CONTRACT_FILE
    )

    links_contract = load_json(
        FIXTURE_LINKS_CONTRACT_FILE
    )

    identity_contract = load_json(
        IDENTITY_CONTRACT_FILE
    )

    upcoming_contract = load_json(
        UPCOMING_CONTRACT_FILE
    )

    standings_contract = load_json(
        STANDINGS_CONTRACT_FILE
    )

    recent_form_contract = load_json(
        RECENT_FORM_CONTRACT_FILE
    )

    venue_form_contract = load_json(
        VENUE_FORM_CONTRACT_FILE
    )


    route_source = (
        TEAM_ROUTE_FILE.read_text(
            encoding="utf-8"
        )
    )

    not_found_source = (
        TEAM_NOT_FOUND_FILE.read_text(
            encoding="utf-8"
        )
    )

    loader_source = (
        TEAM_LOADER_FILE.read_text(
            encoding="utf-8"
        )
    )

    context_loader_source = (
        TEAM_CONTEXT_LOADER_FILE.read_text(
            encoding="utf-8"
        )
    )

    records_source = (
        TEAM_RECORDS_FILE.read_text(
            encoding="utf-8"
        )
    )

    context_records_source = (
        TEAM_CONTEXT_RECORDS_FILE.read_text(
            encoding="utf-8"
        )
    )

    card_source = (
        TEAM_PREDICTION_CARD_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. PREVIOUS STAGE 10.6 VERIFICATION CHAIN"
    )


    check(
        "10.6.1-10.6.4 PASS",
        verify_1_4.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )


    for key in [
        "stage_10_6_1_complete",
        "stage_10_6_2_complete",
        "stage_10_6_3_complete",
        "stage_10_6_4_complete",
    ]:

        check(
            key,
            verify_1_4.get(
                key
            )
            is True,
            failures,
        )


    check(
        "10.6.5-10.6.8 PASS",
        verify_5_8.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )


    for key in [
        "stage_10_6_5_complete",
        "stage_10_6_6_complete",
        "stage_10_6_7_complete",
        "stage_10_6_8_complete",
    ]:

        check(
            key,
            verify_5_8.get(
                key
            )
            is True,
            failures,
        )


    check(
        "10.6.8 authorized 10.6.9",
        verify_5_8.get(
            "stage10_ready_for_10_6_9"
        )
        is True,
        failures,
    )


    print(
        "\n3. STAGE 10.6.9 UNKNOWN TEAM CONTRACT"
    )


    check(
        "10.6.9 stage exact",
        unknown_contract.get(
            "stage"
        )
        ==
        "10.6.9",
        failures,
    )


    check(
        "10.6.9 contract LOCKED",
        unknown_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Unknown-team route exact",
        unknown_contract.get(
            "route"
        )
        ==
        "/teams/[teamName]",
        failures,
    )


    behavior = unknown_contract.get(
        "behavior",
        {},
    )


    check(
        "NOT_FOUND maps to 404",
        behavior.get(
            "not_found_maps_to_404"
        )
        is True,
        failures,
    )


    check(
        "No fuzzy matching",
        behavior.get(
            "fuzzy_matching"
        )
        is False,
        failures,
    )


    check(
        "No team guessing",
        behavior.get(
            "team_name_guessing"
        )
        is False,
        failures,
    )


    check(
        "No automatic redirect",
        behavior.get(
            "automatic_redirect"
        )
        is False,
        failures,
    )


    check(
        "No suggested substitution",
        behavior.get(
            "suggested_team_substitution"
        )
        is False,
        failures,
    )


    print(
        "\n4. UNKNOWN TEAM ROUTE BEHAVIOR"
    )


    check(
        "Team intelligence NOT_FOUND handled",
        (
            "result.state ==="
            in
            route_source
            and
            '"NOT_FOUND"'
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
        "Stage 8 context NOT_FOUND handled",
        (
            "standingsResult.state ==="
            in
            route_source
            and
            "formResult.state ==="
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
        "Route-scoped not-found component marker",
        (
            'data-fixtureiq-component="team-not-found"'
            in
            not_found_source
        ),
        failures,
    )


    check(
        "Unknown-team heading",
        "Team not found"
        in
        not_found_source,
        failures,
    )


    check(
        "Back to upcoming matches",
        (
            'href="/"'
            in
            not_found_source
            and
            "Back to upcoming matches"
            in
            not_found_source
        ),
        failures,
    )


    combined_unknown = (
        route_source
        +
        "\n"
        +
        not_found_source
    )


    for forbidden in [
        "levenshtein",
        "fuzzy",
        "closest team",
        "suggested team",
        "did you mean",
    ]:

        check(
            f"Unknown team avoids {forbidden}",
            forbidden.lower()
            not in
            combined_unknown.lower(),
            failures,
        )


    print(
        "\n5. FINAL TEAM VIEW COMPONENT COVERAGE"
    )


    required_components = [
        "TeamIdentityHeader",
        "TeamUpcomingMatches",
        "TeamPredictionCard",
        "TeamStandings",
        "TeamRecentForm",
        "TeamHomeAwayForm",
    ]


    for component in required_components:

        check(
            f"Team page renders {component}",
            f"<{component}"
            in
            route_source,
            failures,
        )


    check(
        "Fixture detail Link retained",
        (
            'import Link from "next/link"'
            in
            card_source
            and
            "/matches/${encodeURIComponent("
            in
            card_source
            and
            "View match intelligence"
            in
            card_source
        ),
        failures,
    )


    print(
        "\n6. TEAM VIEW API AUTHORITY"
    )


    check(
        "Stage 9 team intelligence loader retained",
        "getTeamIntelligenceResult"
        in
        loader_source,
        failures,
    )


    check(
        "Stage 8 standings loader retained",
        "getContextStandingsByTeamNameResult"
        in
        context_loader_source,
        failures,
    )


    check(
        "Stage 8 form loader retained",
        "getContextFormByTeamNameResult"
        in
        context_loader_source,
        failures,
    )


    check(
        "Context requests use Promise.all",
        "Promise.all"
        in
        context_loader_source,
        failures,
    )


    print(
        "\n7. RUNTIME SAFETY"
    )


    check(
        "Team route force-dynamic",
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
        "Team intelligence non-READY fails closed",
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
        "Context non-READY fails closed",
        (
            'standingsResult.state !=='
            in
            route_source
            and
            'formResult.state !=='
            in
            route_source
        ),
        failures,
    )


    combined_runtime = "\n".join(
        [
            route_source,
            not_found_source,
            loader_source,
            context_loader_source,
            records_source,
            context_records_source,
            card_source,
        ]
    )


    check(
        "No direct fetch",
        re.search(
            r"\bfetch\s*\(",
            combined_runtime,
        )
        is None,
        failures,
    )


    check(
        "No client directive",
        (
            '"use client"'
            not in
            combined_runtime
            and
            "'use client'"
            not in
            combined_runtime
        ),
        failures,
    )


    for forbidden in [
        "localStorage",
        "sessionStorage",
        "previousData",
        "previousResponse",
        "staleData",
        "fallbackData",
    ]:

        check(
            f"No stale fallback: {forbidden}",
            forbidden
            not in
            combined_runtime,
            failures,
        )


    print(
        "\n8. DIRECT ARTIFACT / PROVIDER PROHIBITION"
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
            f"Team sources exclude {term}",
            term.lower()
            not in
            combined_runtime.lower(),
            failures,
        )


    print(
        "\n9. PREDICTION / CONTEXT INTEGRITY"
    )


    check(
        "No frontend argmax",
        "Math.max"
        not in
        combined_runtime,
        failures,
    )


    check(
        "No recalibration",
        "recalibr"
        not in
        combined_runtime.lower(),
        failures,
    )


    check(
        "No standings points calculation",
        (
            "won * 3"
            not in
            combined_runtime
            and
            "wins * 3"
            not in
            combined_runtime
        ),
        failures,
    )


    check(
        "No form aggregation",
        (
            ".reduce("
            not in
            context_records_source
            and
            ".sort("
            not in
            context_records_source
        ),
        failures,
    )


    print(
        "\n10. SOURCE IDENTITY"
    )


    check(
        "Team route SHA exact",
        unknown_contract.get(
            "team_route_sha256"
        )
        ==
        sha256_file(
            TEAM_ROUTE_FILE
        ),
        failures,
    )


    check(
        "Unknown-team page SHA exact",
        unknown_contract.get(
            "not_found_page_sha256"
        )
        ==
        sha256_file(
            TEAM_NOT_FOUND_FILE
        ),
        failures,
    )


    check(
        "Final route remains 10.6.8 route",
        links_contract.get(
            "route_page_after_10_6_8_sha256"
        )
        ==
        sha256_file(
            TEAM_ROUTE_FILE
        ),
        failures,
    )


    check(
        "Prediction card remains verified 10.6.8",
        links_contract.get(
            "prediction_card_after_10_6_8_sha256"
        )
        ==
        sha256_file(
            TEAM_PREDICTION_CARD_FILE
        ),
        failures,
    )


    check(
        "Identity header current",
        identity_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            TEAM_HEADER_FILE
        ),
        failures,
    )


    check(
        "Upcoming component current",
        upcoming_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            TEAM_UPCOMING_FILE
        ),
        failures,
    )


    check(
        "Standings component current",
        standings_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            TEAM_STANDINGS_FILE
        ),
        failures,
    )


    check(
        "Recent form component current",
        recent_form_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            TEAM_RECENT_FORM_FILE
        ),
        failures,
    )


    check(
        "Home/away form component current",
        venue_form_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            TEAM_VENUE_FORM_FILE
        ),
        failures,
    )


    print(
        "\n11. PROTECTED SOURCE STATE"
    )


    protected = unknown_contract.get(
        "protected_state",
        {},
    )


    protected_sources = [
        (
            "Team route",
            TEAM_ROUTE_FILE,
            "team_route_sha256",
        ),
        (
            "Team loader",
            TEAM_LOADER_FILE,
            "team_loader_sha256",
        ),
        (
            "Team context loader",
            TEAM_CONTEXT_LOADER_FILE,
            "team_context_loader_sha256",
        ),
        (
            "Team records",
            TEAM_RECORDS_FILE,
            "team_records_sha256",
        ),
        (
            "Team context records",
            TEAM_CONTEXT_RECORDS_FILE,
            "team_context_records_sha256",
        ),
        (
            "Team header",
            TEAM_HEADER_FILE,
            "team_header_sha256",
        ),
        (
            "Team upcoming",
            TEAM_UPCOMING_FILE,
            "team_upcoming_sha256",
        ),
        (
            "Prediction card",
            TEAM_PREDICTION_CARD_FILE,
            "team_prediction_card_sha256",
        ),
        (
            "Standings",
            TEAM_STANDINGS_FILE,
            "team_standings_sha256",
        ),
        (
            "Recent form",
            TEAM_RECENT_FORM_FILE,
            "team_recent_form_sha256",
        ),
        (
            "Home/away form",
            TEAM_VENUE_FORM_FILE,
            "team_home_away_form_sha256",
        ),
        (
            "Mapped API",
            MAPPED_API_FILE,
            "mapped_api_sha256",
        ),
        (
            "Result mapping",
            RESULT_FILE,
            "result_mapping_sha256",
        ),
        (
            "Domain types",
            DOMAIN_TYPES_FILE,
            "domain_types_sha256",
        ),
    ]


    for label, path, key in protected_sources:

        check(
            f"{label} unchanged by 10.6.9",
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
        "\n12. DEPENDENCY FRESHNESS"
    )


    verify_dependencies(
        unknown_contract,
        "10.6.9",
        failures,
    )


    print(
        "\n13. TYPESCRIPT"
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
        "\n14. PRODUCTION BUILD"
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
        "\n15. NO PREMATURE STAGE 10 PROMOTION"
    )


    promotion = unknown_contract.get(
        "promotion",
        {},
    )


    check(
        "10.6.9 did not self-promote",
        promotion.get(
            "stage10_6_9_complete"
        )
        is False,
        failures,
    )


    check(
        "Stage 10.6 not already promoted",
        promotion.get(
            "stage10_6_complete"
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
        "\n16. FINAL STAGE 10.6 DECISION"
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
                "10.6.10",

            "name":
                "TEAM_INTELLIGENCE_VIEW_FINAL_VERIFICATION",

            "status":
                "PASS",

            "stage_10_6_1_complete":
                True,

            "stage_10_6_2_complete":
                True,

            "stage_10_6_3_complete":
                True,

            "stage_10_6_4_complete":
                True,

            "stage_10_6_5_complete":
                True,

            "stage_10_6_6_complete":
                True,

            "stage_10_6_7_complete":
                True,

            "stage_10_6_8_complete":
                True,

            "stage_10_6_9_complete":
                True,

            "stage_10_6_10_complete":
                True,

            "dynamic_team_route":
                "VERIFIED",

            "team_identity_header":
                "VERIFIED",

            "upcoming_team_matches":
                "VERIFIED",

            "prediction_cards":
                "VERIFIED",

            "standings":
                "VERIFIED",

            "recent_form":
                "VERIFIED",

            "home_away_form":
                "VERIFIED",

            "fixture_links":
                "VERIFIED",

            "unknown_team":
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

                "fuzzy_team_matching":
                    False,

                "frontend_probability_modification":
                    False,

                "frontend_context_recalculation":
                    False,
            },

            "typescript_compiler":
                "PASS",

            "production_build":
                "PASS",

            "stage10_6_complete":
                True,

            "stage10_ready_for_10_7_1":
                True,

            "stage10_complete":
                False,

            "next_stage":
                "10.7.1",

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
            "STAGE 10.6.9: PASS"
        )

        print(
            "UNKNOWN TEAM: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.6.10: PASS"
        )

        print(
            "TEAM INTELLIGENCE VIEW: VERIFIED"
        )

        print()

        print(
            "STAGE 10.6: COMPLETE"
        )

        print(
            "STAGE 10 READY FOR 10.7.1"
        )

        print()

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.6.9 / 10.6.10: FAIL"
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
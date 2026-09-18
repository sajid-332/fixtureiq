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
    / "stage10_6_1_10_6_4_verification.json"
)

PREVIOUS_CARD_CONTRACT_FILE = (
    DOCS
    / "frontend_team_prediction_cards_contract.json"
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

FIXTURE_LINKS_CONTRACT_FILE = (
    DOCS
    / "frontend_team_fixture_links_contract.json"
)


TEAM_ROUTE_FILE = (
    FRONTEND
    / "app"
    / "teams"
    / "[teamName]"
    / "page.tsx"
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
    / "stage10_6_5_10_6_8_verification.json"
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
        "FixtureIQ Stage 10.6.5 - 10.6.8"
    )

    print(
        "TEAM CONTEXT + FIXTURE LINKS VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        PREVIOUS_FILE,
        PREVIOUS_CARD_CONTRACT_FILE,
        STANDINGS_CONTRACT_FILE,
        RECENT_FORM_CONTRACT_FILE,
        VENUE_FORM_CONTRACT_FILE,
        FIXTURE_LINKS_CONTRACT_FILE,
        TEAM_ROUTE_FILE,
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


    previous = load_json(
        PREVIOUS_FILE
    )

    previous_card_contract = load_json(
        PREVIOUS_CARD_CONTRACT_FILE
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

    links_contract = load_json(
        FIXTURE_LINKS_CONTRACT_FILE
    )


    route_source = (
        TEAM_ROUTE_FILE.read_text(
            encoding="utf-8"
        )
    )

    context_loader_source = (
        TEAM_CONTEXT_LOADER_FILE.read_text(
            encoding="utf-8"
        )
    )

    context_records_source = (
        TEAM_CONTEXT_RECORDS_FILE.read_text(
            encoding="utf-8"
        )
    )

    standings_source = (
        TEAM_STANDINGS_FILE.read_text(
            encoding="utf-8"
        )
    )

    recent_form_source = (
        TEAM_RECENT_FORM_FILE.read_text(
            encoding="utf-8"
        )
    )

    venue_form_source = (
        TEAM_VENUE_FORM_FILE.read_text(
            encoding="utf-8"
        )
    )

    card_source = (
        TEAM_PREDICTION_CARD_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. STAGE 10.6.1 - 10.6.4 FOUNDATION"
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
        "stage_10_6_1_complete",
        "stage_10_6_2_complete",
        "stage_10_6_3_complete",
        "stage_10_6_4_complete",
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
        "10.6.4 authorized 10.6.5",
        previous.get(
            "stage10_ready_for_10_6_5"
        )
        is True,
        failures,
    )


    print(
        "\n3. STAGE 8 CONTEXT LOADER"
    )


    check(
        "Context loader server-only",
        'import "server-only"'
        in
        context_loader_source,
        failures,
    )


    check(
        "Standings mapped client used",
        "getContextStandingsByTeamNameResult"
        in
        context_loader_source,
        failures,
    )


    check(
        "Form mapped client used",
        "getContextFormByTeamNameResult"
        in
        context_loader_source,
        failures,
    )


    check(
        "Promise.all library API used",
        "Promise.all"
        in
        context_loader_source,
        failures,
    )


    check(
        "No direct fetch",
        re.search(
            r"\bfetch\s*\(",
            context_loader_source,
        )
        is None,
        failures,
    )


    print(
        "\n4. CONTEXT RECORD VALIDATION"
    )


    standings_fields = [
        "team_name",
        "position",
        "played",
        "won",
        "drawn",
        "lost",
        "goals_for",
        "goals_against",
        "goal_difference",
        "points",
    ]


    for field in standings_fields:

        check(
            f"Standings field preserved: {field}",
            field
            in
            context_records_source,
            failures,
        )


    form_fields = [
        "form_matches_available",
        "recent_results",
        "recent_points",
        "recent_wins",
        "recent_draws",
        "recent_losses",
        "recent_goals_for",
        "recent_goals_against",
        "recent_goal_difference",
        "home_form_matches_available",
        "home_recent_results",
        "home_recent_points",
        "home_recent_wins",
        "home_recent_draws",
        "home_recent_losses",
        "home_recent_goals_for",
        "home_recent_goals_against",
        "home_recent_goal_difference",
        "away_form_matches_available",
        "away_recent_results",
        "away_recent_points",
        "away_recent_wins",
        "away_recent_draws",
        "away_recent_losses",
        "away_recent_goals_for",
        "away_recent_goals_against",
        "away_recent_goal_difference",
    ]


    for field in form_fields:

        check(
            f"Form field preserved: {field}",
            field
            in
            context_records_source,
            failures,
        )


    check(
        "Transport integer conversion",
        (
            "Number("
            in
            context_records_source
            and
            "Number.isInteger"
            in
            context_records_source
        ),
        failures,
    )


    check(
        "W/D/L strings validated",
        "^[WDL]*$"
        in
        context_records_source,
        failures,
    )


    check(
        "Exact team identity matching",
        (
            "record.team_name"
            in
            context_records_source
            and
            "requestedTeamName"
            in
            context_records_source
        ),
        failures,
    )


    check(
        "Exactly one standings row required",
        (
            "Expected exactly one Stage 8 standings record"
            in
            context_records_source
        ),
        failures,
    )


    check(
        "Exactly one form row required",
        (
            "Expected exactly one Stage 8 form record"
            in
            context_records_source
        ),
        failures,
    )


    print(
        "\n5. STAGE 10.6.5 STANDINGS"
    )


    check(
        "10.6.5 stage exact",
        standings_contract.get(
            "stage"
        )
        ==
        "10.6.5",
        failures,
    )


    check(
        "10.6.5 LOCKED",
        standings_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Standings authority Stage 8",
        standings_contract.get(
            "source_authority"
        )
        ==
        "STAGE_8_CONTEXT",
        failures,
    )


    check(
        "Standings endpoint exact",
        standings_contract.get(
            "backend_endpoint"
        )
        ==
        "/api/v1/context/standings/<path:team_name>",
        failures,
    )


    check(
        "Standings component marker",
        (
            'data-fixtureiq-component="team-standings"'
            in
            standings_source
        ),
        failures,
    )


    for field in [
        "position",
        "points",
        "played",
        "won",
        "drawn",
        "lost",
        "goals_for",
        "goals_against",
        "goal_difference",
    ]:

        check(
            f"Standings presentation marker: {field}",
            field
            in
            standings_source,
            failures,
        )


    print(
        "\n6. STAGE 10.6.6 RECENT FORM"
    )


    check(
        "10.6.6 stage exact",
        recent_form_contract.get(
            "stage"
        )
        ==
        "10.6.6",
        failures,
    )


    check(
        "10.6.6 LOCKED",
        recent_form_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Recent form authority Stage 8",
        recent_form_contract.get(
            "source_authority"
        )
        ==
        "STAGE_8_CONTEXT",
        failures,
    )


    check(
        "Form endpoint exact",
        recent_form_contract.get(
            "backend_endpoint"
        )
        ==
        "/api/v1/context/form/<path:team_name>",
        failures,
    )


    check(
        "Recent form component marker",
        (
            'data-fixtureiq-component="team-recent-form"'
            in
            recent_form_source
        ),
        failures,
    )


    for field in [
        "recent_results",
        "form_matches_available",
        "recent_points",
        "recent_wins",
        "recent_draws",
        "recent_losses",
        "recent_goals_for",
        "recent_goals_against",
        "recent_goal_difference",
    ]:

        check(
            f"Recent form marker: {field}",
            field
            in
            recent_form_source,
            failures,
        )


    check(
        "No frontend result aggregation",
        (
            ".reduce("
            not in
            recent_form_source
            and
            ".filter("
            not in
            recent_form_source
        ),
        failures,
    )


    print(
        "\n7. STAGE 10.6.7 HOME / AWAY FORM"
    )


    check(
        "10.6.7 stage exact",
        venue_form_contract.get(
            "stage"
        )
        ==
        "10.6.7",
        failures,
    )


    check(
        "10.6.7 LOCKED",
        venue_form_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Venue form authority Stage 8",
        venue_form_contract.get(
            "source_authority"
        )
        ==
        "STAGE_8_CONTEXT",
        failures,
    )


    check(
        "Venue form component marker",
        (
            'data-fixtureiq-component="team-home-away-form"'
            in
            venue_form_source
        ),
        failures,
    )


    check(
        "Home venue context present",
        (
            'fieldPrefix="home"'
            in
            venue_form_source
            and
            "homePoints"
            in
            venue_form_source
        ),
        failures,
    )


    check(
        "Away venue context present",
        (
            'fieldPrefix="away"'
            in
            venue_form_source
            and
            "awayPoints"
            in
            venue_form_source
        ),
        failures,
    )


    check(
        "No venue score derivation",
        (
            "homePoints - awayPoints"
            not in
            venue_form_source
            and
            "awayPoints - homePoints"
            not in
            venue_form_source
        ),
        failures,
    )


    print(
        "\n8. ROUTE CONTEXT INTEGRATION"
    )


    check(
        "loadTeamContext imported",
        "loadTeamContext"
        in
        route_source,
        failures,
    )


    check(
        "Context request awaited",
        re.search(
            (
                r"await\s+"
                r"loadTeamContext"
                r"\s*\("
            ),
            route_source,
        )
        is not None,
        failures,
    )


    check(
        "Standings extracted from READY response",
        (
            "extractTeamStandingsRecord"
            in
            route_source
            and
            "standingsResult.data"
            in
            route_source
        ),
        failures,
    )


    check(
        "Form extracted from READY response",
        (
            "extractTeamFormRecord"
            in
            route_source
            and
            "formResult.data"
            in
            route_source
        ),
        failures,
    )


    check(
        "Context 404 maps to notFound",
        (
            'standingsResult.state ==='
            in
            route_source
            and
            'formResult.state ==='
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
        "Context non-READY fails closed",
        (
            'standingsResult.state !=='
            in
            route_source
            and
            'formResult.state !=='
            in
            route_source
            and
            '"READY"'
            in
            route_source
        ),
        failures,
    )


    for component in [
        "TeamStandings",
        "TeamRecentForm",
        "TeamHomeAwayForm",
    ]:

        check(
            f"Route renders {component}",
            f"<{component}"
            in
            route_source,
            failures,
        )


    print(
        "\n9. STAGE 10.6.8 FIXTURE LINKS"
    )


    check(
        "10.6.8 stage exact",
        links_contract.get(
            "stage"
        )
        ==
        "10.6.8",
        failures,
    )


    check(
        "10.6.8 LOCKED",
        links_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Next Link imported",
        'import Link from "next/link"'
        in
        card_source,
        failures,
    )


    check(
        "Match detail path exact",
        "/matches/${encodeURIComponent("
        in
        card_source,
        failures,
    )


    check(
        "Fixture ID used for link",
        (
            "fixtureId"
            in
            card_source
            and
            "String("
            in
            card_source
        ),
        failures,
    )


    check(
        "Link text exact",
        "View match intelligence"
        in
        card_source,
        failures,
    )


    print(
        "\n10. 10.6.9+ NOT IMPLEMENTED EARLY"
    )


    combined = "\n".join(
        [
            route_source,
            context_loader_source,
            context_records_source,
            standings_source,
            recent_form_source,
            venue_form_source,
            card_source,
        ]
    )


    for forbidden in [
        "Unknown team",
        "unknown-team",
        "closest team",
        "suggested team",
        "fuzzy",
        "levenshtein",
    ]:

        check(
            f"10.6.9 not implemented early: {forbidden}",
            forbidden.lower()
            not in
            combined.lower(),
            failures,
        )


    print(
        "\n11. PRESENTATION / AUTHORITY SAFETY"
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


    check(
        "No client component directive",
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
            f"Sources exclude {term}",
            term.lower()
            not in
            combined.lower(),
            failures,
        )


    check(
        "No frontend standings calculation",
        (
            "won * 3"
            not in
            combined
            and
            "wins * 3"
            not in
            combined
        ),
        failures,
    )


    check(
        "No probability logic added",
        (
            "Math.max"
            not in
            combined
            and
            "recalibr"
            not in
            combined.lower()
        ),
        failures,
    )


    print(
        "\n12. PREVIOUS 10.6 SOURCE PROTECTION"
    )


    protected = links_contract.get(
        "protected_state",
        {},
    )


    protected_sources = [
        (
            "Team intelligence loader",
            TEAM_LOADER_FILE,
            "team_loader_sha256",
        ),
        (
            "Team records",
            TEAM_RECORDS_FILE,
            "team_records_sha256",
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
        "Prediction card started from verified 10.6.4",
        links_contract.get(
            "prediction_card_before_10_6_8_sha256"
        )
        ==
        previous_card_contract.get(
            "component_sha256"
        ),
        failures,
    )


    check(
        "Route started from verified 10.6.4",
        standings_contract.get(
            "route_page_before_10_6_5_sha256"
        )
        ==
        previous_card_contract.get(
            "route_page_after_10_6_4_sha256"
        ),
        failures,
    )


    print(
        "\n13. CURRENT SOURCE IDENTITY"
    )


    check(
        "Standings component SHA exact",
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
        "Recent form component SHA exact",
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
        "Home/away form component SHA exact",
        venue_form_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            TEAM_VENUE_FORM_FILE
        ),
        failures,
    )


    check(
        "Context loader SHA exact",
        standings_contract.get(
            "context_loader_sha256"
        )
        ==
        sha256_file(
            TEAM_CONTEXT_LOADER_FILE
        ),
        failures,
    )


    check(
        "Context record SHA exact",
        standings_contract.get(
            "context_records_sha256"
        )
        ==
        sha256_file(
            TEAM_CONTEXT_RECORDS_FILE
        ),
        failures,
    )


    check(
        "Prediction card after links SHA exact",
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
        "Team route after 10.6.8 SHA exact",
        links_contract.get(
            "route_page_after_10_6_8_sha256"
        )
        ==
        sha256_file(
            TEAM_ROUTE_FILE
        ),
        failures,
    )


    print(
        "\n14. DEPENDENCY FRESHNESS"
    )


    for stage, contract in [
        (
            "10.6.5",
            standings_contract,
        ),
        (
            "10.6.6",
            recent_form_contract,
        ),
        (
            "10.6.7",
            venue_form_contract,
        ),
        (
            "10.6.8",
            links_contract,
        ),
    ]:

        verify_dependencies(
            contract,
            stage,
            failures,
        )


    print(
        "\n15. TYPESCRIPT"
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
        "\n16. NO PREMATURE PROMOTION"
    )


    for stage, contract, key in [
        (
            "10.6.5",
            standings_contract,
            "stage10_6_5_complete",
        ),
        (
            "10.6.6",
            recent_form_contract,
            "stage10_6_6_complete",
        ),
        (
            "10.6.7",
            venue_form_contract,
            "stage10_6_7_complete",
        ),
        (
            "10.6.8",
            links_contract,
            "stage10_6_8_complete",
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
            f"{stage}: Stage 10.6 incomplete",
            promotion.get(
                "stage10_6_complete"
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
        "\n17. SAVE VERIFICATION"
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
                "10.6.5-10.6.8",

            "name":
                "TEAM_CONTEXT_AND_FIXTURE_LINKS_VERIFICATION",

            "status":
                "PASS",

            "stage_10_6_5_complete":
                True,

            "stage_10_6_6_complete":
                True,

            "stage_10_6_7_complete":
                True,

            "stage_10_6_8_complete":
                True,

            "standings":
                "LOCKED_AND_VERIFIED",

            "recent_form":
                "LOCKED_AND_VERIFIED",

            "home_away_form":
                "LOCKED_AND_VERIFIED",

            "fixture_links":
                "LOCKED_AND_VERIFIED",

            "authority": {
                "standings":
                    "STAGE_8",

                "recent_form":
                    "STAGE_8",

                "home_away_form":
                    "STAGE_8",

                "fixture_identity":
                    "STAGE_9",
            },

            "integrity": {
                "standings_recalculated":
                    False,

                "form_recalculated":
                    False,

                "venue_form_recalculated":
                    False,

                "probabilities_modified":
                    False,

                "direct_fetch":
                    False,

                "provider_access":
                    False,

                "artifact_access":
                    False,

                "stale_fallback":
                    False,

                "fixture_links":
                    True,
            },

            "typescript_compiler":
                "PASS",

            "stage10_ready_for_10_6_9":
                True,

            "stage10_6_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.6.9",

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
            "STAGE 10.6.5: PASS"
        )

        print(
            "STANDINGS: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.6.6: PASS"
        )

        print(
            "RECENT FORM: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.6.7: PASS"
        )

        print(
            "HOME / AWAY FORM: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.6.8: PASS"
        )

        print(
            "FIXTURE LINKS: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.6.9"
        )

        print(
            "STAGE 10.6 IS NOT YET COMPLETE"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.6.5 - 10.6.8: FAIL"
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
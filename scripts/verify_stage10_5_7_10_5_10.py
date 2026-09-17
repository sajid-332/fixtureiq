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
    / "stage10_5_3_10_5_6_verification.json"
)

UNCERTAINTY_CONTRACT_FILE = (
    DOCS
    / "frontend_match_uncertainty_contract.json"
)

LEAGUE_POSITION_CONTRACT_FILE = (
    DOCS
    / "frontend_match_league_position_comparison_contract.json"
)

POINTS_CONTRACT_FILE = (
    DOCS
    / "frontend_match_points_comparison_contract.json"
)

GOAL_DIFFERENCE_CONTRACT_FILE = (
    DOCS
    / "frontend_match_goal_difference_comparison_contract.json"
)

RECENT_FORM_CONTRACT_FILE = (
    DOCS
    / "frontend_match_recent_form_contract.json"
)


ROUTE_PAGE_FILE = (
    FRONTEND
    / "app"
    / "matches"
    / "[fixtureId]"
    / "page.tsx"
)

CONTEXT_RECORD_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "match-context-record.ts"
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


HEADER_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-fixture-header.tsx"
)

HEADER_RECORD_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "match-header-record.ts"
)

MATCH_LOADER_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "load-match-intelligence.ts"
)

PREDICTION_RECORD_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "match-prediction-record.ts"
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
    / "stage10_5_7_10_5_10_verification.json"
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
        "FixtureIQ Stage 10.5.7 - 10.5.10"
    )

    print(
        "MATCH CONTEXT COMPARISON VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        PREVIOUS_FILE,
        UNCERTAINTY_CONTRACT_FILE,
        LEAGUE_POSITION_CONTRACT_FILE,
        POINTS_CONTRACT_FILE,
        GOAL_DIFFERENCE_CONTRACT_FILE,
        RECENT_FORM_CONTRACT_FILE,
        ROUTE_PAGE_FILE,
        CONTEXT_RECORD_FILE,
        LEAGUE_POSITION_COMPONENT_FILE,
        POINTS_COMPONENT_FILE,
        GOAL_DIFFERENCE_COMPONENT_FILE,
        RECENT_FORM_COMPONENT_FILE,
        HEADER_COMPONENT_FILE,
        HEADER_RECORD_FILE,
        MATCH_LOADER_FILE,
        PREDICTION_RECORD_FILE,
        OVERVIEW_COMPONENT_FILE,
        PROBABILITY_COMPONENT_FILE,
        CONFIDENCE_COMPONENT_FILE,
        UNCERTAINTY_COMPONENT_FILE,
        DOMAIN_TYPES_FILE,
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

    uncertainty_contract = load_json(
        UNCERTAINTY_CONTRACT_FILE
    )

    league_contract = load_json(
        LEAGUE_POSITION_CONTRACT_FILE
    )

    points_contract = load_json(
        POINTS_CONTRACT_FILE
    )

    goal_difference_contract = load_json(
        GOAL_DIFFERENCE_CONTRACT_FILE
    )

    recent_form_contract = load_json(
        RECENT_FORM_CONTRACT_FILE
    )


    route_source = (
        ROUTE_PAGE_FILE.read_text(
            encoding="utf-8"
        )
    )

    context_source = (
        CONTEXT_RECORD_FILE.read_text(
            encoding="utf-8"
        )
    )

    league_source = (
        LEAGUE_POSITION_COMPONENT_FILE.read_text(
            encoding="utf-8"
        )
    )

    points_source = (
        POINTS_COMPONENT_FILE.read_text(
            encoding="utf-8"
        )
    )

    goal_difference_source = (
        GOAL_DIFFERENCE_COMPONENT_FILE.read_text(
            encoding="utf-8"
        )
    )

    recent_form_source = (
        RECENT_FORM_COMPONENT_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. STAGE 10.5.3 - 10.5.6 FOUNDATION"
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
        "stage_10_5_3_complete",
        "stage_10_5_4_complete",
        "stage_10_5_5_complete",
        "stage_10_5_6_complete",
    ]:

        check(
            f"{key}",
            previous.get(
                key
            )
            is True,
            failures,
        )


    check(
        "10.5.6 authorized 10.5.7",
        previous.get(
            "stage10_ready_for_10_5_7"
        )
        is True,
        failures,
    )


    print(
        "\n3. CONTEXT TRANSPORT RECORD"
    )


    required_context_fields = [
        "fixture_id",
        "home_team_position",
        "away_team_position",
        "home_team_points",
        "away_team_points",
        "home_team_goal_difference",
        "away_team_goal_difference",
        "home_team_form_matches_available",
        "away_team_form_matches_available",
        "home_team_recent_results",
        "away_team_recent_results",
    ]


    for field in required_context_fields:

        check(
            f"Context record preserves {field}",
            field
            in
            context_source,
            failures,
        )


    check(
        "Transport integer conversion uses Number",
        "Number("
        in
        context_source,
        failures,
    )


    check(
        "Transport integer validation uses Number.isInteger",
        "Number.isInteger"
        in
        context_source,
        failures,
    )


    check(
        "Recent results restricted to W/D/L",
        "^[WDL]*$"
        in
        context_source,
        failures,
    )


    check(
        "Exact fixture identity preserved",
        (
            "String("
            in
            context_source
            and
            "expectedFixtureId"
            in
            context_source
        ),
        failures,
    )


    check(
        "Duplicate context record rejected",
        "records.length !== 1"
        in
        context_source,
        failures,
    )


    print(
        "\n4. STAGE 10.5.7 LEAGUE POSITION"
    )


    check(
        "10.5.7 stage exact",
        league_contract.get(
            "stage"
        )
        ==
        "10.5.7",
        failures,
    )


    check(
        "10.5.7 contract LOCKED",
        league_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "League position authority Stage 8",
        league_contract.get(
            "source_authority"
        )
        ==
        "STAGE_8_CONTEXT",
        failures,
    )


    check(
        "Home league position marker",
        (
            'data-stage8-field="home_team_position"'
            in
            league_source
        ),
        failures,
    )


    check(
        "Away league position marker",
        (
            'data-stage8-field="away_team_position"'
            in
            league_source
        ),
        failures,
    )


    check(
        "Home position direct",
        "{homePosition}"
        in
        league_source,
        failures,
    )


    check(
        "Away position direct",
        "{awayPosition}"
        in
        league_source,
        failures,
    )


    print(
        "\n5. STAGE 10.5.8 POINTS"
    )


    check(
        "10.5.8 stage exact",
        points_contract.get(
            "stage"
        )
        ==
        "10.5.8",
        failures,
    )


    check(
        "10.5.8 contract LOCKED",
        points_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Points authority Stage 8",
        points_contract.get(
            "source_authority"
        )
        ==
        "STAGE_8_CONTEXT",
        failures,
    )


    check(
        "Home points marker",
        (
            'data-stage8-field="home_team_points"'
            in
            points_source
        ),
        failures,
    )


    check(
        "Away points marker",
        (
            'data-stage8-field="away_team_points"'
            in
            points_source
        ),
        failures,
    )


    check(
        "Home points direct",
        "{homePoints}"
        in
        points_source,
        failures,
    )


    check(
        "Away points direct",
        "{awayPoints}"
        in
        points_source,
        failures,
    )


    print(
        "\n6. STAGE 10.5.9 GOAL DIFFERENCE"
    )


    check(
        "10.5.9 stage exact",
        goal_difference_contract.get(
            "stage"
        )
        ==
        "10.5.9",
        failures,
    )


    check(
        "10.5.9 contract LOCKED",
        goal_difference_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Goal difference authority Stage 8",
        goal_difference_contract.get(
            "source_authority"
        )
        ==
        "STAGE_8_CONTEXT",
        failures,
    )


    check(
        "Home goal difference marker",
        (
            'data-stage8-field="home_team_goal_difference"'
            in
            goal_difference_source
        ),
        failures,
    )


    check(
        "Away goal difference marker",
        (
            'data-stage8-field="away_team_goal_difference"'
            in
            goal_difference_source
        ),
        failures,
    )


    check(
        "Intl.NumberFormat used for sign display",
        (
            "Intl.NumberFormat"
            in
            goal_difference_source
            and
            'signDisplay: "always"'
            in
            goal_difference_source
        ),
        failures,
    )


    check(
        "No home-away goal-difference calculation",
        re.search(
            (
                r"homeGoalDifference"
                r"\s*-\s*"
                r"awayGoalDifference"
            ),
            goal_difference_source,
        )
        is None,
        failures,
    )


    print(
        "\n7. STAGE 10.5.10 RECENT FORM"
    )


    check(
        "10.5.10 stage exact",
        recent_form_contract.get(
            "stage"
        )
        ==
        "10.5.10",
        failures,
    )


    check(
        "10.5.10 contract LOCKED",
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


    for field in [
        "home_team_recent_results",
        "away_team_recent_results",
        "home_team_form_matches_available",
        "away_team_form_matches_available",
    ]:

        check(
            f"Recent-form marker: {field}",
            field
            in
            recent_form_source,
            failures,
        )


    check(
        "Home recent results direct",
        "homeResults"
        in
        recent_form_source,
        failures,
    )


    check(
        "Away recent results direct",
        "awayResults"
        in
        recent_form_source,
        failures,
    )


    check(
        "No result-derived point calculation",
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
        "\n8. DETAIL ROUTE INTEGRATION"
    )


    check(
        "Context extractor imported",
        "extractMatchContextRecord"
        in
        route_source,
        failures,
    )


    check(
        "Context extracted from same READY response",
        (
            "extractMatchContextRecord"
            in
            route_source
            and
            "result.data"
            in
            route_source
            and
            "fixtureId"
            in
            route_source
        ),
        failures,
    )


    for component in [
        "MatchLeaguePositionComparison",
        "MatchPointsComparison",
        "MatchGoalDifferenceComparison",
        "MatchRecentForm",
    ]:

        check(
            f"Route renders {component}",
            f"<{component}"
            in
            route_source,
            failures,
        )


    direct_mappings = [
        "context.home_team_position",
        "context.away_team_position",
        "context.home_team_points",
        "context.away_team_points",
        "context.home_team_goal_difference",
        "context.away_team_goal_difference",
        "context.home_team_recent_results",
        "context.away_team_recent_results",
        "context.home_team_form_matches_available",
        "context.away_team_form_matches_available",
    ]


    for mapping in direct_mappings:

        check(
            f"Route direct mapping: {mapping}",
            mapping
            in
            route_source,
            failures,
        )


    print(
        "\n9. NO GAP RECALCULATION"
    )


    combined = (
        route_source
        +
        "\n"
        +
        context_source
        +
        "\n"
        +
        league_source
        +
        "\n"
        +
        points_source
        +
        "\n"
        +
        goal_difference_source
        +
        "\n"
        +
        recent_form_source
    )


    for forbidden_gap in [
        "stage9_league_position_gap",
        "stage9_points_gap",
        "stage9_goal_difference_gap",
        "stage9_recent_points_gap",
        "stage9_recent_goal_difference_gap",
    ]:

        check(
            f"Gap field not consumed: {forbidden_gap}",
            forbidden_gap
            not in
            combined,
            failures,
        )


    check(
        "No position subtraction",
        re.search(
            (
                r"home_team_position"
                r"\s*-\s*"
                r"away_team_position"
            ),
            combined,
        )
        is None,
        failures,
    )


    check(
        "No points subtraction",
        re.search(
            (
                r"home_team_points"
                r"\s*-\s*"
                r"away_team_points"
            ),
            combined,
        )
        is None,
        failures,
    )


    print(
        "\n10. 10.5.11+ NOT IMPLEMENTED EARLY"
    )


    forbidden_future = [
        "home_team_home_recent_results",
        "away_team_away_recent_results",
        "home_team_home_recent_points",
        "away_team_away_recent_points",
        "stage9_venue_form_points_gap",
        "stage9_context_support_score",
        "stage9_context_alignment",
        "stage9_explanation_headline",
        "stage9_explanation_summary",
    ]


    for field in forbidden_future:

        check(
            f"Not implemented early: {field}",
            field
            not in
            combined,
            failures,
        )


    print(
        "\n11. PRESENTATION-ONLY SAFETY"
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
            f"Sources exclude {term}",
            term.lower()
            not in
            combined.lower(),
            failures,
        )


    print(
        "\n12. PREVIOUS SOURCE PROTECTION"
    )


    protected = recent_form_contract.get(
        "protected_state",
        {},
    )


    protected_sources = [
        (
            "10.5.2 header component",
            HEADER_COMPONENT_FILE,
            "header_component_sha256",
        ),
        (
            "10.5.2 header record",
            HEADER_RECORD_FILE,
            "header_record_sha256",
        ),
        (
            "Match loader",
            MATCH_LOADER_FILE,
            "match_loader_sha256",
        ),
        (
            "Prediction record",
            PREDICTION_RECORD_FILE,
            "prediction_record_sha256",
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
        "\n13. CURRENT SOURCE IDENTITY"
    )


    check(
        "League-position component SHA exact",
        league_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            LEAGUE_POSITION_COMPONENT_FILE
        ),
        failures,
    )


    check(
        "Points component SHA exact",
        points_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            POINTS_COMPONENT_FILE
        ),
        failures,
    )


    check(
        "Goal-difference component SHA exact",
        goal_difference_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            GOAL_DIFFERENCE_COMPONENT_FILE
        ),
        failures,
    )


    check(
        "Recent-form component SHA exact",
        recent_form_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            RECENT_FORM_COMPONENT_FILE
        ),
        failures,
    )


    check(
        "Context record SHA exact",
        recent_form_contract.get(
            "context_record_sha256"
        )
        ==
        sha256_file(
            CONTEXT_RECORD_FILE
        ),
        failures,
    )


    check(
        "Route page SHA exact",
        recent_form_contract.get(
            "route_page_after_10_5_10_sha256"
        )
        ==
        sha256_file(
            ROUTE_PAGE_FILE
        ),
        failures,
    )


    check(
        "Route started from verified 10.5.6",
        league_contract.get(
            "route_page_before_10_5_7_sha256"
        )
        ==
        uncertainty_contract.get(
            "route_page_after_10_5_6_sha256"
        ),
        failures,
    )


    print(
        "\n14. DEPENDENCY FRESHNESS"
    )


    for stage, contract in [
        (
            "10.5.7",
            league_contract,
        ),
        (
            "10.5.8",
            points_contract,
        ),
        (
            "10.5.9",
            goal_difference_contract,
        ),
        (
            "10.5.10",
            recent_form_contract,
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
            "10.5.7",
            league_contract,
            "stage10_5_7_complete",
        ),
        (
            "10.5.8",
            points_contract,
            "stage10_5_8_complete",
        ),
        (
            "10.5.9",
            goal_difference_contract,
            "stage10_5_9_complete",
        ),
        (
            "10.5.10",
            recent_form_contract,
            "stage10_5_10_complete",
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
            f"{stage}: Stage 10.5 still incomplete",
            promotion.get(
                "stage10_5_complete"
            )
            is False,
            failures,
        )


        check(
            f"{stage}: Stage 10 still incomplete",
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
                "10.5.7-10.5.10",

            "name":
                "MATCH_CONTEXT_COMPARISON_VERIFICATION",

            "status":
                "PASS",

            "stage_10_5_7_complete":
                True,

            "stage_10_5_8_complete":
                True,

            "stage_10_5_9_complete":
                True,

            "stage_10_5_10_complete":
                True,

            "league_position_comparison":
                "LOCKED_AND_VERIFIED",

            "points_comparison":
                "LOCKED_AND_VERIFIED",

            "goal_difference_comparison":
                "LOCKED_AND_VERIFIED",

            "recent_form":
                "LOCKED_AND_VERIFIED",

            "authority": {
                "league_position":
                    "STAGE_8",

                "points":
                    "STAGE_8",

                "goal_difference":
                    "STAGE_8",

                "recent_form":
                    "STAGE_8",

                "transport":
                    "STAGE_9_JOINED_INTELLIGENCE_API",
            },

            "integrity": {
                "transport_string_to_integer_only":
                    True,

                "league_position_gap_recalculated":
                    False,

                "points_gap_recalculated":
                    False,

                "goal_difference_gap_recalculated":
                    False,

                "recent_points_calculated":
                    False,

                "venue_form_used":
                    False,

                "context_support_used":
                    False,

                "context_alignment_used":
                    False,

                "explanation_used":
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

            "stage10_ready_for_10_5_11":
                True,

            "stage10_5_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.5.11",

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
            "STAGE 10.5.7: PASS"
        )

        print(
            "LEAGUE POSITION COMPARISON: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.5.8: PASS"
        )

        print(
            "POINTS COMPARISON: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.5.9: PASS"
        )

        print(
            "GOAL DIFFERENCE COMPARISON: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.5.10: PASS"
        )

        print(
            "RECENT FORM: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.5.11"
        )

        print(
            "STAGE 10.5 IS NOT YET COMPLETE"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.5.7 - 10.5.10: FAIL"
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
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
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
    / "stage10_5_final_verification.json"
)

MATCH_STATUS_CONTRACT_FILE = (
    DOCS
    / "frontend_match_freshness_status_contract.json"
)

ROUTE_CONTRACT_FILE = (
    DOCS
    / "frontend_team_dynamic_route_contract.json"
)

IDENTITY_CONTRACT_FILE = (
    DOCS
    / "frontend_team_identity_header_contract.json"
)

UPCOMING_CONTRACT_FILE = (
    DOCS
    / "frontend_team_upcoming_matches_contract.json"
)

PREDICTION_CARDS_CONTRACT_FILE = (
    DOCS
    / "frontend_team_prediction_cards_contract.json"
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

TEAM_RECORDS_FILE = (
    FRONTEND
    / "lib"
    / "teams"
    / "team-records.ts"
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


MATCH_DETAIL_ROUTE_FILE = (
    FRONTEND
    / "app"
    / "matches"
    / "[fixtureId]"
    / "page.tsx"
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
    / "stage10_6_1_10_6_4_verification.json"
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
        "FixtureIQ Stage 10.6.1 - 10.6.4"
    )

    print(
        "TEAM INTELLIGENCE FOUNDATION VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        PREVIOUS_FILE,
        MATCH_STATUS_CONTRACT_FILE,
        ROUTE_CONTRACT_FILE,
        IDENTITY_CONTRACT_FILE,
        UPCOMING_CONTRACT_FILE,
        PREDICTION_CARDS_CONTRACT_FILE,
        TEAM_ROUTE_FILE,
        TEAM_LOADER_FILE,
        TEAM_RECORDS_FILE,
        TEAM_HEADER_FILE,
        TEAM_UPCOMING_FILE,
        TEAM_PREDICTION_CARD_FILE,
        MATCH_DETAIL_ROUTE_FILE,
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

    match_status_contract = load_json(
        MATCH_STATUS_CONTRACT_FILE
    )

    route_contract = load_json(
        ROUTE_CONTRACT_FILE
    )

    identity_contract = load_json(
        IDENTITY_CONTRACT_FILE
    )

    upcoming_contract = load_json(
        UPCOMING_CONTRACT_FILE
    )

    prediction_contract = load_json(
        PREDICTION_CARDS_CONTRACT_FILE
    )


    route_source = (
        TEAM_ROUTE_FILE.read_text(
            encoding="utf-8"
        )
    )

    loader_source = (
        TEAM_LOADER_FILE.read_text(
            encoding="utf-8"
        )
    )

    records_source = (
        TEAM_RECORDS_FILE.read_text(
            encoding="utf-8"
        )
    )

    header_source = (
        TEAM_HEADER_FILE.read_text(
            encoding="utf-8"
        )
    )

    upcoming_source = (
        TEAM_UPCOMING_FILE.read_text(
            encoding="utf-8"
        )
    )

    card_source = (
        TEAM_PREDICTION_CARD_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. STAGE 10.5 FOUNDATION"
    )


    check(
        "Stage 10.5 final PASS",
        previous.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )


    check(
        "Stage 10.5 COMPLETE",
        previous.get(
            "stage10_5_complete"
        )
        is True,
        failures,
    )


    check(
        "Stage 10 ready for 10.6.1",
        previous.get(
            "stage10_ready_for_10_6_1"
        )
        is True,
        failures,
    )


    print(
        "\n3. STAGE 10.6.1 DYNAMIC TEAM ROUTE"
    )


    check(
        "10.6.1 stage exact",
        route_contract.get(
            "stage"
        )
        ==
        "10.6.1",
        failures,
    )


    check(
        "10.6.1 contract LOCKED",
        route_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Team route exact",
        route_contract.get(
            "route"
        )
        ==
        "/teams/[teamName]",
        failures,
    )


    check(
        "Team endpoint exact",
        route_contract.get(
            "backend_endpoint"
        )
        ==
        "/api/v1/intelligence/team/<path:team_name>",
        failures,
    )


    check(
        "Mapped client exact",
        route_contract.get(
            "mapped_client"
        )
        ==
        "getTeamIntelligenceResult",
        failures,
    )


    check(
        "TeamRouteParams used",
        "TeamRouteParams"
        in
        route_source,
        failures,
    )


    check(
        "teamName route parameter used",
        "teamName"
        in
        route_source,
        failures,
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
        "Team loader awaited",
        re.search(
            (
                r"await\s+"
                r"loadTeamIntelligence"
                r"\s*\("
            ),
            route_source,
        )
        is not None,
        failures,
    )


    check(
        "NOT_FOUND uses notFound()",
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
        "Non-READY fails closed",
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


    print(
        "\n4. TEAM API LOADER"
    )


    check(
        "Loader server-only",
        'import "server-only"'
        in
        loader_source,
        failures,
    )


    check(
        "getTeamIntelligenceResult used",
        "getTeamIntelligenceResult"
        in
        loader_source,
        failures,
    )


    check(
        "No direct fetch in loader",
        re.search(
            r"\bfetch\s*\(",
            loader_source,
        )
        is None,
        failures,
    )


    print(
        "\n5. TEAM RESPONSE EXTRACTION"
    )


    required_record_fields = [
        "fixture_id",
        "date",
        "home_team_name",
        "away_team_name",
        "stage7_prob_home_win",
        "stage7_prob_draw",
        "stage7_prob_away_win",
        "stage7_predicted_label",
        "stage7_confidence",
        "stage9_confidence_band",
        "stage9_uncertainty_band",
        "stage9_context_alignment",
    ]


    for field in required_record_fields:

        check(
            f"Record preserves {field}",
            field
            in
            records_source,
            failures,
        )


    check(
        "Transport string-number conversion uses Number",
        "Number("
        in
        records_source,
        failures,
    )


    check(
        "Probability range validated",
        (
            "parsed < 0"
            in
            records_source
            and
            "parsed > 1"
            in
            records_source
        ),
        failures,
    )


    check(
        "Kickoff validated",
        "Date.parse"
        in
        records_source,
        failures,
    )


    check(
        "Team identity membership enforced",
        (
            "belongsToRequestedTeam"
            in
            records_source
            and
            "record.home_team_name"
            in
            records_source
            and
            "record.away_team_name"
            in
            records_source
        ),
        failures,
    )


    check(
        "Duplicate fixture identities rejected",
        (
            "fixtureIds.has"
            in
            records_source
            and
            "duplicate fixture identity"
            in
            records_source
        ),
        failures,
    )


    check(
        "No fixture sorting",
        ".sort("
        not in
        records_source,
        failures,
    )


    check(
        "No frontend temporal filtering",
        ".filter("
        not in
        records_source,
        failures,
    )


    print(
        "\n6. STAGE 10.6.2 TEAM IDENTITY HEADER"
    )


    check(
        "10.6.2 stage exact",
        identity_contract.get(
            "stage"
        )
        ==
        "10.6.2",
        failures,
    )


    check(
        "10.6.2 contract LOCKED",
        identity_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Identity header marker",
        (
            'data-fixtureiq-component="team-identity-header"'
            in
            header_source
        ),
        failures,
    )


    check(
        "Team name rendered",
        "{teamName}"
        in
        header_source,
        failures,
    )


    check(
        "Route passes verified team identity",
        "team.teamName"
        in
        route_source,
        failures,
    )


    print(
        "\n7. STAGE 10.6.3 UPCOMING TEAM MATCHES"
    )


    check(
        "10.6.3 stage exact",
        upcoming_contract.get(
            "stage"
        )
        ==
        "10.6.3",
        failures,
    )


    check(
        "10.6.3 contract LOCKED",
        upcoming_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Upcoming matches component marker",
        (
            'data-fixtureiq-component="team-upcoming-matches"'
            in
            upcoming_source
        ),
        failures,
    )


    check(
        "Upcoming matches heading",
        "Upcoming matches"
        in
        upcoming_source,
        failures,
    )


    check(
        "Backend match count displayed",
        "{matchCount}"
        in
        upcoming_source,
        failures,
    )


    check(
        "Backend order mapped directly",
        "team.matches.map"
        in
        route_source,
        failures,
    )


    check(
        "No route sorting",
        ".sort("
        not in
        route_source,
        failures,
    )


    check(
        "No route temporal filtering",
        ".filter("
        not in
        route_source,
        failures,
    )


    print(
        "\n8. STAGE 10.6.4 PREDICTION CARDS"
    )


    check(
        "10.6.4 stage exact",
        prediction_contract.get(
            "stage"
        )
        ==
        "10.6.4",
        failures,
    )


    check(
        "10.6.4 contract LOCKED",
        prediction_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Prediction card marker",
        (
            'data-fixtureiq-component="team-prediction-card"'
            in
            card_source
        ),
        failures,
    )


    for field in [
        "stage7_prob_home_win",
        "stage7_prob_draw",
        "stage7_prob_away_win",
        "stage7_predicted_label",
        "stage7_confidence",
        "stage9_confidence_band",
        "stage9_uncertainty_band",
        "stage9_context_alignment",
    ]:

        check(
            f"Prediction card source marker: {field}",
            field
            in
            card_source,
            failures,
        )


    check(
        "Kickoff formatter reused",
        "formatKickoffUtc"
        in
        card_source,
        failures,
    )


    check(
        "Probability formatter reused",
        "formatProbability"
        in
        card_source,
        failures,
    )


    check(
        "No frontend argmax",
        "Math.max"
        not in
        card_source,
        failures,
    )


    check(
        "No probability normalization",
        "normalize"
        not in
        card_source.lower(),
        failures,
    )


    check(
        "No probability recalibration",
        "recalibr"
        not in
        card_source.lower(),
        failures,
    )


    route_mappings = [
        "match.fixture_id",
        "match.date",
        "match.home_team_name",
        "match.away_team_name",
        "match.stage7_prob_home_win",
        "match.stage7_prob_draw",
        "match.stage7_prob_away_win",
        "match.stage7_predicted_label",
        "match.stage7_confidence",
        "match.stage9_confidence_band",
        "match.stage9_uncertainty_band",
        "match.stage9_context_alignment",
    ]


    for mapping in route_mappings:

        check(
            f"Route direct mapping: {mapping}",
            mapping
            in
            route_source,
            failures,
        )


    print(
        "\n9. 10.6.5+ FEATURES NOT IMPLEMENTED EARLY"
    )


    combined = "\n".join(
        [
            route_source,
            loader_source,
            records_source,
            header_source,
            upcoming_source,
            card_source,
        ]
    )


    forbidden_future = [
        "getContextStandingsByTeamName",
        "getContextFormByTeamName",
        "home_team_position",
        "away_team_position",
        "home_team_recent_results",
        "away_team_recent_results",
        "home_team_home_recent_results",
        "away_team_away_recent_results",
        "next/link",
        "<Link",
        "href=",
    ]


    for term in forbidden_future:

        check(
            f"Not implemented early: {term}",
            term
            not in
            combined,
            failures,
        )


    print(
        "\n10. PRESENTATION AUTHORITY / SAFETY"
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
        "\n11. STAGE 10.5 PROTECTION"
    )


    locked_match_route_sha = (
        match_status_contract.get(
            "route_page_after_10_5_15_sha256"
        )
    )


    check(
        "Stage 10.5 match route unchanged",
        locked_match_route_sha
        ==
        sha256_file(
            MATCH_DETAIL_ROUTE_FILE
        ),
        failures,
    )


    protected = (
        prediction_contract.get(
            "protected_state",
            {},
        )
    )


    protected_sources = [
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
            "result_mapping_sha256",
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
        "\n12. CURRENT SOURCE IDENTITY"
    )


    check(
        "Team route SHA exact",
        prediction_contract.get(
            "route_page_after_10_6_4_sha256"
        )
        ==
        sha256_file(
            TEAM_ROUTE_FILE
        ),
        failures,
    )


    check(
        "Team header SHA exact",
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
        "Upcoming component SHA exact",
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
        "Prediction card SHA exact",
        prediction_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            TEAM_PREDICTION_CARD_FILE
        ),
        failures,
    )


    check(
        "Team record extractor SHA exact",
        prediction_contract.get(
            "record_source_sha256"
        )
        ==
        sha256_file(
            TEAM_RECORDS_FILE
        ),
        failures,
    )


    print(
        "\n13. DEPENDENCY FRESHNESS"
    )


    for stage, contract in [
        (
            "10.6.1",
            route_contract,
        ),
        (
            "10.6.2",
            identity_contract,
        ),
        (
            "10.6.3",
            upcoming_contract,
        ),
        (
            "10.6.4",
            prediction_contract,
        ),
    ]:

        verify_dependencies(
            contract,
            stage,
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
        "\n15. NO PREMATURE PROMOTION"
    )


    for stage, contract, key in [
        (
            "10.6.1",
            route_contract,
            "stage10_6_1_complete",
        ),
        (
            "10.6.2",
            identity_contract,
            "stage10_6_2_complete",
        ),
        (
            "10.6.3",
            upcoming_contract,
            "stage10_6_3_complete",
        ),
        (
            "10.6.4",
            prediction_contract,
            "stage10_6_4_complete",
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
        "\n16. SAVE VERIFICATION"
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
                "10.6.1-10.6.4",

            "name":
                "TEAM_INTELLIGENCE_FOUNDATION_VERIFICATION",

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

            "dynamic_team_route":
                "LOCKED_AND_VERIFIED",

            "team_identity_header":
                "LOCKED_AND_VERIFIED",

            "upcoming_team_matches":
                "LOCKED_AND_VERIFIED",

            "prediction_cards":
                "LOCKED_AND_VERIFIED",

            "integrity": {
                "team_intelligence_authority":
                    "STAGE_9",

                "probability_authority":
                    "STAGE_7",

                "frontend_temporal_filtering":
                    False,

                "frontend_sorting":
                    False,

                "probability_recalculation":
                    False,

                "probability_normalization":
                    False,

                "frontend_argmax":
                    False,

                "fixture_links_implemented":
                    False,

                "standings_implemented":
                    False,

                "recent_form_implemented":
                    False,

                "venue_form_implemented":
                    False,

                "direct_fetch":
                    False,

                "provider_access":
                    False,

                "artifact_access":
                    False,

                "stale_fallback":
                    False,
            },

            "typescript_compiler":
                "PASS",

            "stage10_ready_for_10_6_5":
                True,

            "stage10_6_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.6.5",

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
            "STAGE 10.6.1: PASS"
        )

        print(
            "DYNAMIC TEAM ROUTE: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.6.2: PASS"
        )

        print(
            "TEAM IDENTITY HEADER: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.6.3: PASS"
        )

        print(
            "UPCOMING TEAM MATCHES: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.6.4: PASS"
        )

        print(
            "PREDICTION CARDS: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.6.5"
        )

        print(
            "STAGE 10.6 IS NOT YET COMPLETE"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.6.1 - 10.6.4: FAIL"
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
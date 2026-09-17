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


STAGE10_4_FINAL_FILE = (
    FRONTEND_DATA
    / "stage10_4_final_verification.json"
)

ROUTE_CONTRACT_FILE = (
    DOCS
    / "frontend_match_detail_route_contract.json"
)

HEADER_CONTRACT_FILE = (
    DOCS
    / "frontend_match_fixture_header_contract.json"
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

HEADER_RECORD_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "match-header-record.ts"
)

HEADER_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-fixture-header.tsx"
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


OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_5_1_10_5_2_verification.json"
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

    temp = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temp.open(
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

    temp.replace(
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


def current_route_pages() -> dict:

    output = {}

    for path in sorted(
        APP_ROOT.rglob(
            "page.tsx"
        )
    ):

        output[
            relative(
                path
            )
        ] = {
            "sha256":
                sha256_file(
                    path
                )
        }

    return output


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
        "FixtureIQ Stage 10.5.1 + 10.5.2"
    )

    print(
        "DYNAMIC MATCH ROUTE + FIXTURE HEADER VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        STAGE10_4_FINAL_FILE,
        ROUTE_CONTRACT_FILE,
        HEADER_CONTRACT_FILE,
        ROUTE_PAGE_FILE,
        MATCH_LOADER_FILE,
        HEADER_RECORD_FILE,
        HEADER_COMPONENT_FILE,
        DOMAIN_TYPES_FILE,
        MAPPED_API_FILE,
        RESULT_FILE,
        KICKOFF_FORMATTER_FILE,
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


    stage10_4 = load_json(
        STAGE10_4_FINAL_FILE
    )

    route_contract = load_json(
        ROUTE_CONTRACT_FILE
    )

    header_contract = load_json(
        HEADER_CONTRACT_FILE
    )


    route_source = (
        ROUTE_PAGE_FILE.read_text(
            encoding="utf-8"
        )
    )

    loader_source = (
        MATCH_LOADER_FILE.read_text(
            encoding="utf-8"
        )
    )

    record_source = (
        HEADER_RECORD_FILE.read_text(
            encoding="utf-8"
        )
    )

    header_source = (
        HEADER_COMPONENT_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. STAGE 10.4 FOUNDATION"
    )


    check(
        "Stage 10.4 final PASS",
        stage10_4.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )


    check(
        "Stage 10.4 COMPLETE",
        stage10_4.get(
            "stage10_4_complete"
        )
        is True,
        failures,
    )


    check(
        "Stage 10 ready for 10.5.1",
        stage10_4.get(
            "stage10_ready_for_10_5_1"
        )
        is True,
        failures,
    )


    print(
        "\n3. STAGE 10.5.1 ROUTE CONTRACT"
    )


    check(
        "10.5.1 stage exact",
        route_contract.get(
            "stage"
        )
        ==
        "10.5.1",
        failures,
    )


    check(
        "Route contract LOCKED",
        route_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Dynamic route exact",
        route_contract.get(
            "route"
        )
        ==
        "/matches/[fixtureId]",
        failures,
    )


    check(
        "Backend endpoint exact",
        route_contract.get(
            "backend_endpoint"
        )
        ==
        "/api/v1/intelligence/matches/<fixture_id>",
        failures,
    )


    check(
        "Mapped client exact",
        route_contract.get(
            "mapped_client"
        )
        ==
        "getIntelligenceMatchResult",
        failures,
    )


    print(
        "\n4. DYNAMIC ROUTE SOURCE"
    )


    check(
        "FixtureRouteParams used",
        "FixtureRouteParams"
        in
        route_source,
        failures,
    )


    check(
        "fixtureId route param used",
        "fixtureId"
        in
        route_source,
        failures,
    )


    check(
        "Match loader awaited",
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
        "NOT_FOUND uses Next notFound()",
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


    print(
        "\n5. SINGLE MATCH LOADER"
    )


    check(
        "Loader server-only",
        'import "server-only"'
        in
        loader_source,
        failures,
    )


    check(
        "Mapped detail client used",
        "getIntelligenceMatchResult"
        in
        loader_source,
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


    print(
        "\n6. DETAIL RECORD EXTRACTION"
    )


    for field in [
        "fixture_id",
        "home_team_name",
        "away_team_name",
        "date",
    ]:

        check(
            f"Header record preserves {field}",
            field
            in
            record_source,
            failures,
        )


    check(
        "Exact fixture identity comparison",
        (
            "String("
            in
            record_source
            and
            "expectedFixtureId"
            in
            record_source
        ),
        failures,
    )


    check(
        "Kickoff date validated",
        "Date.parse"
        in
        record_source,
        failures,
    )


    check(
        "Duplicate detail record rejected",
        "records.length !== 1"
        in
        record_source,
        failures,
    )


    print(
        "\n7. STAGE 10.5.2 HEADER CONTRACT"
    )


    check(
        "10.5.2 stage exact",
        header_contract.get(
            "stage"
        )
        ==
        "10.5.2",
        failures,
    )


    check(
        "Header contract LOCKED",
        header_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Canonical kickoff source = date",
        header_contract
        .get(
            "kickoff",
            {},
        )
        .get(
            "backend_field"
        )
        ==
        "date",
        failures,
    )


    check(
        "UTC formatter exact",
        header_contract
        .get(
            "kickoff",
            {},
        )
        .get(
            "formatter"
        )
        ==
        "formatKickoffUtc",
        failures,
    )


    print(
        "\n8. FIXTURE HEADER SOURCE"
    )


    check(
        "Header component marker",
        (
            'data-fixtureiq-component="match-fixture-header"'
            in
            header_source
        ),
        failures,
    )


    check(
        "Fixture ID preserved",
        (
            "fixtureId"
            in
            header_source
            and
            "FixtureId"
            in
            header_source
        ),
        failures,
    )


    check(
        "Home team displayed",
        "{homeTeamName}"
        in
        header_source,
        failures,
    )


    check(
        "Away team displayed",
        "{awayTeamName}"
        in
        header_source,
        failures,
    )


    check(
        "Kickoff formatted",
        re.search(
            (
                r"formatKickoffUtc"
                r"\s*\(\s*"
                r"kickoffUtc"
            ),
            header_source,
        )
        is not None,
        failures,
    )


    check(
        "Semantic time element",
        "<time"
        in
        header_source
        and
        "dateTime="
        in
        header_source,
        failures,
    )


    print(
        "\n9. 10.5.3+ FEATURES NOT IMPLEMENTED EARLY"
    )


    combined = (
        route_source
        +
        "\n"
        +
        header_source
        +
        "\n"
        +
        record_source
    )


    forbidden = [
        "stage7_prob_home_win",
        "stage7_prob_draw",
        "stage7_prob_away_win",
        "stage7_predicted_label",
        "stage7_confidence",
        "stage9_confidence_band",
        "stage9_uncertainty_band",
        "stage9_context_support_score",
        "stage9_context_alignment",
        "stage9_explanation_headline",
        "stage9_explanation_summary",
        "league_position",
        "recent_points",
        "venue_form",
    ]


    for field in forbidden:

        check(
            f"Not implemented early: {field}",
            field
            not in
            combined,
            failures,
        )


    print(
        "\n10. AUTHORITY / SAFETY"
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
        "No direct fetch anywhere",
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
        "\n11. SOURCE IDENTITY"
    )


    check(
        "Route page SHA exact",
        header_contract.get(
            "route_page_after_header_sha256"
        )
        ==
        sha256_file(
            ROUTE_PAGE_FILE
        ),
        failures,
    )


    check(
        "Header component SHA exact",
        header_contract.get(
            "header_component_sha256"
        )
        ==
        sha256_file(
            HEADER_COMPONENT_FILE
        ),
        failures,
    )


    check(
        "Header record SHA exact",
        header_contract.get(
            "header_record_sha256"
        )
        ==
        sha256_file(
            HEADER_RECORD_FILE
        ),
        failures,
    )


    check(
        "Match loader SHA exact",
        header_contract.get(
            "match_loader_sha256"
        )
        ==
        sha256_file(
            MATCH_LOADER_FILE
        ),
        failures,
    )


    protected = (
        header_contract.get(
            "protected_state",
            {},
        )
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
        "Mapped API unchanged",
        protected.get(
            "mapped_api_sha256"
        )
        ==
        sha256_file(
            MAPPED_API_FILE
        ),
        failures,
    )


    check(
        "Result mapping unchanged",
        protected.get(
            "result_sha256"
        )
        ==
        sha256_file(
            RESULT_FILE
        ),
        failures,
    )


    check(
        "Kickoff formatter unchanged",
        protected.get(
            "kickoff_formatter_sha256"
        )
        ==
        sha256_file(
            KICKOFF_FORMATTER_FILE
        ),
        failures,
    )


    print(
        "\n12. DEPENDENCY FRESHNESS"
    )


    verify_dependencies(
        route_contract,
        "10.5.1",
        failures,
    )


    verify_dependencies(
        header_contract,
        "10.5.2",
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
        "\n14. NO PREMATURE PROMOTION"
    )


    check(
        "10.5.1 did not self-promote",
        route_contract
        .get(
            "promotion",
            {},
        )
        .get(
            "stage10_5_1_complete"
        )
        is False,
        failures,
    )


    check(
        "10.5.2 did not self-promote",
        header_contract
        .get(
            "promotion",
            {},
        )
        .get(
            "stage10_5_2_complete"
        )
        is False,
        failures,
    )


    check(
        "Stage 10.5 still incomplete",
        header_contract
        .get(
            "promotion",
            {},
        )
        .get(
            "stage10_5_complete"
        )
        is False,
        failures,
    )


    check(
        "Stage 10 still incomplete",
        header_contract
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
        "\n15. SAVE VERIFICATION"
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
                "10.5.1-10.5.2",

            "name":
                (
                    "DYNAMIC_MATCH_ROUTE_AND_"
                    "FIXTURE_HEADER_VERIFICATION"
                ),

            "status":
                "PASS",

            "stage_10_5_1_complete":
                True,

            "stage_10_5_2_complete":
                True,

            "dynamic_match_route":
                "LOCKED_AND_VERIFIED",

            "fixture_header":
                "LOCKED_AND_VERIFIED",

            "route":
                "/matches/[fixtureId]",

            "source_fields": [
                "fixture_id",
                "home_team_name",
                "away_team_name",
                "date",
            ],

            "safety": {
                "direct_fetch":
                    False,

                "provider_access":
                    False,

                "artifact_access":
                    False,

                "stale_fallback":
                    False,

                "prediction_logic":
                    False,

                "future_detail_features_implemented":
                    False,
            },

            "typescript_compiler":
                "PASS",

            "stage10_ready_for_10_5_3":
                True,

            "stage10_5_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.5.3",

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
            "STAGE 10.5.1: PASS"
        )

        print(
            "DYNAMIC MATCH ROUTE: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.5.2: PASS"
        )

        print(
            "FIXTURE HEADER: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.5.3"
        )

        print(
            "STAGE 10.5 IS NOT YET COMPLETE"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.5.1 / 10.5.2: FAIL"
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
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
    / "stage10_5_7_10_5_10_verification.json"
)

RECENT_FORM_CONTRACT_FILE = (
    DOCS
    / "frontend_match_recent_form_contract.json"
)

VENUE_FORM_CONTRACT_FILE = (
    DOCS
    / "frontend_match_venue_form_contract.json"
)

CONTEXT_SUPPORT_CONTRACT_FILE = (
    DOCS
    / "frontend_match_context_support_contract.json"
)

ALIGNMENT_CONTRACT_FILE = (
    DOCS
    / "frontend_match_context_alignment_contract.json"
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

INTELLIGENCE_RECORD_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "match-intelligence-detail-record.ts"
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

CONTEXT_RECORD_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "match-context-record.ts"
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


OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_5_11_10_5_14_verification.json"
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
        "FixtureIQ Stage 10.5.11 - 10.5.14"
    )
    print(
        "VENUE FORM + CONTEXT INTELLIGENCE VERIFICATION"
    )
    print("=" * 72)


    failures: list[str] = []


    required = [
        PREVIOUS_FILE,
        RECENT_FORM_CONTRACT_FILE,
        VENUE_FORM_CONTRACT_FILE,
        CONTEXT_SUPPORT_CONTRACT_FILE,
        ALIGNMENT_CONTRACT_FILE,
        EXPLANATION_CONTRACT_FILE,
        ROUTE_PAGE_FILE,
        INTELLIGENCE_RECORD_FILE,
        VENUE_FORM_COMPONENT_FILE,
        CONTEXT_SUPPORT_COMPONENT_FILE,
        ALIGNMENT_COMPONENT_FILE,
        EXPLANATION_COMPONENT_FILE,
        HEADER_COMPONENT_FILE,
        HEADER_RECORD_FILE,
        MATCH_LOADER_FILE,
        PREDICTION_RECORD_FILE,
        CONTEXT_RECORD_FILE,
        OVERVIEW_COMPONENT_FILE,
        PROBABILITY_COMPONENT_FILE,
        CONFIDENCE_COMPONENT_FILE,
        UNCERTAINTY_COMPONENT_FILE,
        LEAGUE_POSITION_COMPONENT_FILE,
        POINTS_COMPONENT_FILE,
        GOAL_DIFFERENCE_COMPONENT_FILE,
        RECENT_FORM_COMPONENT_FILE,
        DOMAIN_TYPES_FILE,
        MAPPED_API_FILE,
        RESULT_FILE,
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

    recent_form_contract = load_json(
        RECENT_FORM_CONTRACT_FILE
    )

    venue_contract = load_json(
        VENUE_FORM_CONTRACT_FILE
    )

    support_contract = load_json(
        CONTEXT_SUPPORT_CONTRACT_FILE
    )

    alignment_contract = load_json(
        ALIGNMENT_CONTRACT_FILE
    )

    explanation_contract = load_json(
        EXPLANATION_CONTRACT_FILE
    )


    route_source = (
        ROUTE_PAGE_FILE.read_text(
            encoding="utf-8"
        )
    )

    record_source = (
        INTELLIGENCE_RECORD_FILE.read_text(
            encoding="utf-8"
        )
    )

    venue_source = (
        VENUE_FORM_COMPONENT_FILE.read_text(
            encoding="utf-8"
        )
    )

    support_source = (
        CONTEXT_SUPPORT_COMPONENT_FILE.read_text(
            encoding="utf-8"
        )
    )

    alignment_source = (
        ALIGNMENT_COMPONENT_FILE.read_text(
            encoding="utf-8"
        )
    )

    explanation_source = (
        EXPLANATION_COMPONENT_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. STAGE 10.5.7 - 10.5.10 FOUNDATION"
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
        "stage_10_5_7_complete",
        "stage_10_5_8_complete",
        "stage_10_5_9_complete",
        "stage_10_5_10_complete",
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
        "10.5.10 authorized 10.5.11",
        previous.get(
            "stage10_ready_for_10_5_11"
        )
        is True,
        failures,
    )


    print(
        "\n3. STAGE 9 DETAIL TRANSPORT RECORD"
    )


    required_fields = [
        "fixture_id",
        "home_team_home_form_matches_available",
        "home_team_home_recent_points",
        "away_team_away_form_matches_available",
        "away_team_away_recent_points",
        "stage9_context_support_score",
        "stage9_context_alignment",
        "stage9_explanation_headline",
        "stage9_explanation_summary",
    ]


    for field in required_fields:

        check(
            f"Record preserves {field}",
            field
            in
            record_source,
            failures,
        )


    check(
        "Transport integer conversion uses Number",
        "Number("
        in
        record_source,
        failures,
    )


    check(
        "Transport integer validation uses Number.isInteger",
        "Number.isInteger"
        in
        record_source,
        failures,
    )


    check(
        "Support score range -5..5 enforced",
        (
            "parsed < -5"
            in
            record_source
            and
            "parsed > 5"
            in
            record_source
        ),
        failures,
    )


    check(
        "Context alignment uses locked domain constant",
        (
            "CONTEXT_ALIGNMENTS"
            in
            record_source
            and
            "contextAlignments.has"
            in
            record_source
        ),
        failures,
    )


    check(
        "Explanation requires source text",
        "requiredText"
        in
        record_source,
        failures,
    )


    check(
        "Exact fixture identity preserved",
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
        "Duplicate detail record rejected",
        "records.length !== 1"
        in
        record_source,
        failures,
    )


    print(
        "\n4. STAGE 10.5.11 VENUE FORM"
    )


    check(
        "10.5.11 stage exact",
        venue_contract.get(
            "stage"
        )
        ==
        "10.5.11",
        failures,
    )


    check(
        "10.5.11 contract LOCKED",
        venue_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Venue form authority Stage 8",
        venue_contract.get(
            "source_authority"
        )
        ==
        "STAGE_8_CONTEXT",
        failures,
    )


    for field in [
        "home_team_home_recent_points",
        "home_team_home_form_matches_available",
        "away_team_away_recent_points",
        "away_team_away_form_matches_available",
    ]:

        check(
            f"Venue marker/source: {field}",
            field
            in
            venue_source,
            failures,
        )


    check(
        "No Stage 9 venue-gap field consumed",
        "stage9_venue_form_points_gap"
        not in
        venue_source
        and
        "stage9_venue_form_points_gap"
        not in
        record_source,
        failures,
    )


    check(
        "No venue points subtraction",
        re.search(
            (
                r"homeRecentPoints"
                r"\s*-\s*"
                r"awayRecentPoints"
            ),
            venue_source,
        )
        is None,
        failures,
    )


    print(
        "\n5. STAGE 10.5.12 CONTEXT SUPPORT"
    )


    check(
        "10.5.12 stage exact",
        support_contract.get(
            "stage"
        )
        ==
        "10.5.12",
        failures,
    )


    check(
        "10.5.12 contract LOCKED",
        support_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Context support authority Stage 9",
        support_contract.get(
            "source_authority"
        )
        ==
        "STAGE_9_INTELLIGENCE",
        failures,
    )


    check(
        "Support score source marker",
        (
            'data-stage9-field="stage9_context_support_score"'
            in
            support_source
        ),
        failures,
    )


    check(
        "Support score displayed directly",
        "supportScore"
        in
        support_source,
        failures,
    )


    check(
        "No frontend signal counting",
        (
            ".filter("
            not in
            support_source
            and
            ".reduce("
            not in
            support_source
        ),
        failures,
    )


    print(
        "\n6. STAGE 10.5.13 ALIGNMENT"
    )


    check(
        "10.5.13 stage exact",
        alignment_contract.get(
            "stage"
        )
        ==
        "10.5.13",
        failures,
    )


    check(
        "10.5.13 contract LOCKED",
        alignment_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Alignment authority Stage 9",
        alignment_contract.get(
            "source_authority"
        )
        ==
        "STAGE_9_INTELLIGENCE",
        failures,
    )


    check(
        "Alignment source marker",
        (
            'data-stage9-field="stage9_context_alignment"'
            in
            alignment_source
        ),
        failures,
    )


    check(
        "Alignment rendered directly",
        "{alignment}"
        in
        alignment_source,
        failures,
    )


    check(
        "No frontend alignment thresholds",
        all(
            term
            not in
            alignment_source

            for term in [
                "supportScore >",
                "supportScore <",
                "Math.abs",
            ]
        ),
        failures,
    )


    print(
        "\n7. STAGE 10.5.14 DETERMINISTIC EXPLANATION"
    )


    check(
        "10.5.14 stage exact",
        explanation_contract.get(
            "stage"
        )
        ==
        "10.5.14",
        failures,
    )


    check(
        "10.5.14 contract LOCKED",
        explanation_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Explanation authority Stage 9",
        explanation_contract.get(
            "source_authority"
        )
        ==
        "STAGE_9_INTELLIGENCE",
        failures,
    )


    check(
        "Deterministic rule authority exact",
        explanation_contract.get(
            "rule_authority"
        )
        ==
        "STAGE9_5_DETERMINISTIC_EXPLANATION_V1",
        failures,
    )


    check(
        "Headline source marker",
        (
            'data-stage9-field="stage9_explanation_headline"'
            in
            explanation_source
        ),
        failures,
    )


    check(
        "Summary source marker",
        (
            'data-stage9-field="stage9_explanation_summary"'
            in
            explanation_source
        ),
        failures,
    )


    check(
        "Headline rendered verbatim",
        "{headline}"
        in
        explanation_source,
        failures,
    )


    check(
        "Summary rendered verbatim",
        "{summary}"
        in
        explanation_source,
        failures,
    )


    check(
        "No truncation",
        (
            ".slice("
            not in
            explanation_source
            and
            ".substring("
            not in
            explanation_source
            and
            ".substr("
            not in
            explanation_source
        ),
        failures,
    )


    check(
        "No explanation generation logic",
        (
            "Math."
            not in
            explanation_source
            and
            ".split("
            not in
            explanation_source
            and
            ".replace("
            not in
            explanation_source
        ),
        failures,
    )


    print(
        "\n8. DETAIL ROUTE INTEGRATION"
    )


    check(
        "Stage 9 detail extractor imported",
        "extractMatchIntelligenceDetailRecord"
        in
        route_source,
        failures,
    )


    check(
        "Stage 9 detail extracted from same READY payload",
        (
            "extractMatchIntelligenceDetailRecord"
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
        "MatchVenueForm",
        "MatchContextSupport",
        "MatchContextAlignment",
        "MatchIntelligenceExplanation",
    ]:

        check(
            f"Route renders {component}",
            f"<{component}"
            in
            route_source,
            failures,
        )


    mappings = [
        "intelligence.home_team_home_recent_points",
        "intelligence.away_team_away_recent_points",
        "intelligence.home_team_home_form_matches_available",
        "intelligence.away_team_away_form_matches_available",
        "intelligence.stage9_context_support_score",
        "intelligence.stage9_context_alignment",
        "intelligence.stage9_explanation_headline",
        "intelligence.stage9_explanation_summary",
    ]


    for mapping in mappings:

        check(
            f"Route direct mapping: {mapping}",
            mapping
            in
            route_source,
            failures,
        )


    print(
        "\n9. STAGE 10.5.15 NOT IMPLEMENTED EARLY"
    )


    combined = (
        route_source
        +
        "\n"
        +
        record_source
        +
        "\n"
        +
        venue_source
        +
        "\n"
        +
        support_source
        +
        "\n"
        +
        alignment_source
        +
        "\n"
        +
        explanation_source
    )


    for forbidden in [
        "getIntelligenceStatusResult",
        "getProductionStatusResult",
        "FreshnessIndicator",
        "data-updated-at",
        "last_updated",
        "updated_at",
        "generated_at",
    ]:

        check(
            f"10.5.15 not implemented early: {forbidden}",
            forbidden
            not in
            combined,
            failures,
        )


    print(
        "\n10. PRESENTATION-ONLY SAFETY"
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
        "\n11. PREVIOUS SOURCE PROTECTION"
    )


    protected = explanation_contract.get(
        "protected_state",
        {},
    )


    protected_sources = [
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
            "Context record",
            CONTEXT_RECORD_FILE,
            "context_record_sha256",
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
        "\n12. CURRENT SOURCE IDENTITY"
    )


    check(
        "Venue component SHA exact",
        venue_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            VENUE_FORM_COMPONENT_FILE
        ),
        failures,
    )


    check(
        "Context support component SHA exact",
        support_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            CONTEXT_SUPPORT_COMPONENT_FILE
        ),
        failures,
    )


    check(
        "Alignment component SHA exact",
        alignment_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            ALIGNMENT_COMPONENT_FILE
        ),
        failures,
    )


    check(
        "Explanation component SHA exact",
        explanation_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            EXPLANATION_COMPONENT_FILE
        ),
        failures,
    )


    check(
        "Stage 9 detail record SHA exact",
        explanation_contract.get(
            "record_source_sha256"
        )
        ==
        sha256_file(
            INTELLIGENCE_RECORD_FILE
        ),
        failures,
    )


    check(
        "Route page SHA exact",
        explanation_contract.get(
            "route_page_after_10_5_14_sha256"
        )
        ==
        sha256_file(
            ROUTE_PAGE_FILE
        ),
        failures,
    )


    check(
        "Route started from verified 10.5.10",
        venue_contract.get(
            "route_page_before_10_5_11_sha256"
        )
        ==
        recent_form_contract.get(
            "route_page_after_10_5_10_sha256"
        ),
        failures,
    )


    print(
        "\n13. DEPENDENCY FRESHNESS"
    )


    for stage, contract in [
        (
            "10.5.11",
            venue_contract,
        ),
        (
            "10.5.12",
            support_contract,
        ),
        (
            "10.5.13",
            alignment_contract,
        ),
        (
            "10.5.14",
            explanation_contract,
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
            "10.5.11",
            venue_contract,
            "stage10_5_11_complete",
        ),
        (
            "10.5.12",
            support_contract,
            "stage10_5_12_complete",
        ),
        (
            "10.5.13",
            alignment_contract,
            "stage10_5_13_complete",
        ),
        (
            "10.5.14",
            explanation_contract,
            "stage10_5_14_complete",
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
                "10.5.11-10.5.14",

            "name":
                "MATCH_CONTEXT_INTELLIGENCE_DETAIL_VERIFICATION",

            "status":
                "PASS",

            "stage_10_5_11_complete":
                True,

            "stage_10_5_12_complete":
                True,

            "stage_10_5_13_complete":
                True,

            "stage_10_5_14_complete":
                True,

            "venue_form":
                "LOCKED_AND_VERIFIED",

            "context_support":
                "LOCKED_AND_VERIFIED",

            "context_alignment":
                "LOCKED_AND_VERIFIED",

            "deterministic_explanation":
                "LOCKED_AND_VERIFIED",

            "authority": {
                "venue_form":
                    "STAGE_8",

                "context_support":
                    "STAGE_9",

                "context_alignment":
                    "STAGE_9",

                "explanation":
                    "STAGE_9",
            },

            "integrity": {
                "venue_gap_recalculated":
                    False,

                "support_score_recalculated":
                    False,

                "alignment_derived_frontend":
                    False,

                "explanation_generated_frontend":
                    False,

                "explanation_rewritten":
                    False,

                "explanation_truncated":
                    False,

                "llm_used":
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

            "stage10_ready_for_10_5_15":
                True,

            "stage10_5_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.5.15",

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
            "STAGE 10.5.11: PASS"
        )
        print(
            "VENUE FORM: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.5.12: PASS"
        )
        print(
            "CONTEXT SUPPORT: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.5.13: PASS"
        )
        print(
            "ALIGNMENT: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.5.14: PASS"
        )
        print(
            "DETERMINISTIC EXPLANATION: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.5.15"
        )
        print(
            "STAGE 10.5 IS NOT YET COMPLETE"
        )
        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.5.11 - 10.5.14: FAIL"
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
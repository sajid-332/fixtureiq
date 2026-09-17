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
    / "stage10_5_1_10_5_2_verification.json"
)

HEADER_CONTRACT_FILE = (
    DOCS
    / "frontend_match_fixture_header_contract.json"
)

DASHBOARD_CONTRACT_FILE = (
    DOCS
    / "frontend_upcoming_dashboard_contract.json"
)

OVERVIEW_CONTRACT_FILE = (
    DOCS
    / "frontend_match_prediction_overview_contract.json"
)

PROBABILITY_CONTRACT_FILE = (
    DOCS
    / "frontend_match_probability_visualization_contract.json"
)

CONFIDENCE_CONTRACT_FILE = (
    DOCS
    / "frontend_match_confidence_contract.json"
)

UNCERTAINTY_CONTRACT_FILE = (
    DOCS
    / "frontend_match_uncertainty_contract.json"
)


ROUTE_PAGE_FILE = (
    FRONTEND
    / "app"
    / "matches"
    / "[fixtureId]"
    / "page.tsx"
)

ROOT_PAGE_FILE = (
    FRONTEND
    / "app"
    / "page.tsx"
)

MATCH_CARD_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-card.tsx"
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
    / "stage10_5_3_10_5_6_verification.json"
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
        "FixtureIQ Stage 10.5.3 - 10.5.6"
    )

    print(
        "PREDICTION DETAIL VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        PREVIOUS_FILE,
        HEADER_CONTRACT_FILE,
        DASHBOARD_CONTRACT_FILE,
        OVERVIEW_CONTRACT_FILE,
        PROBABILITY_CONTRACT_FILE,
        CONFIDENCE_CONTRACT_FILE,
        UNCERTAINTY_CONTRACT_FILE,
        ROUTE_PAGE_FILE,
        ROOT_PAGE_FILE,
        MATCH_CARD_FILE,
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

    header_contract = load_json(
        HEADER_CONTRACT_FILE
    )

    dashboard_contract = load_json(
        DASHBOARD_CONTRACT_FILE
    )

    overview_contract = load_json(
        OVERVIEW_CONTRACT_FILE
    )

    probability_contract = load_json(
        PROBABILITY_CONTRACT_FILE
    )

    confidence_contract = load_json(
        CONFIDENCE_CONTRACT_FILE
    )

    uncertainty_contract = load_json(
        UNCERTAINTY_CONTRACT_FILE
    )


    route_source = (
        ROUTE_PAGE_FILE.read_text(
            encoding="utf-8"
        )
    )

    record_source = (
        PREDICTION_RECORD_FILE.read_text(
            encoding="utf-8"
        )
    )

    overview_source = (
        OVERVIEW_COMPONENT_FILE.read_text(
            encoding="utf-8"
        )
    )

    probability_source = (
        PROBABILITY_COMPONENT_FILE.read_text(
            encoding="utf-8"
        )
    )

    confidence_source = (
        CONFIDENCE_COMPONENT_FILE.read_text(
            encoding="utf-8"
        )
    )

    uncertainty_source = (
        UNCERTAINTY_COMPONENT_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. STAGE 10.5.1 / 10.5.2 FOUNDATION"
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
        "10.5.1 complete",
        previous.get(
            "stage_10_5_1_complete"
        )
        is True,
        failures,
    )


    check(
        "10.5.2 complete",
        previous.get(
            "stage_10_5_2_complete"
        )
        is True,
        failures,
    )


    check(
        "10.5.2 authorized 10.5.3",
        previous.get(
            "stage10_ready_for_10_5_3"
        )
        is True,
        failures,
    )


    print(
        "\n3. TRANSPORT RECORD"
    )


    for field in [
        "fixture_id",
        "stage7_prob_home_win",
        "stage7_prob_draw",
        "stage7_prob_away_win",
        "stage7_predicted_label",
        "stage7_confidence",
        "stage9_confidence_band",
        "stage9_uncertainty_band",
    ]:

        check(
            f"Record preserves {field}",
            field
            in
            record_source,
            failures,
        )


    check(
        "Transport string conversion uses Number",
        "Number("
        in
        record_source,
        failures,
    )


    check(
        "Transport conversion uses Number.isFinite",
        "Number.isFinite"
        in
        record_source,
        failures,
    )


    check(
        "Probability range validated",
        (
            "parsed < 0"
            in
            record_source
            and
            "parsed > 1"
            in
            record_source
        ),
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
        "Duplicate prediction record rejected",
        "records.length !== 1"
        in
        record_source,
        failures,
    )


    print(
        "\n4. STAGE 10.5.3 PREDICTION OVERVIEW"
    )


    check(
        "10.5.3 contract stage exact",
        overview_contract.get(
            "stage"
        )
        ==
        "10.5.3",
        failures,
    )


    check(
        "10.5.3 contract LOCKED",
        overview_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Predicted label authority Stage 7",
        overview_contract.get(
            "authority"
        )
        ==
        "STAGE_7_PREDICTION",
        failures,
    )


    check(
        "Overview source marker",
        (
            'data-stage7-field="stage7_predicted_label"'
            in
            overview_source
        ),
        failures,
    )


    check(
        "Predicted label rendered directly",
        "{predictedLabel}"
        in
        overview_source,
        failures,
    )


    check(
        "No frontend argmax",
        "Math.max"
        not in
        overview_source
        and
        "argmax"
        not in
        overview_source.lower(),
        failures,
    )


    print(
        "\n5. STAGE 10.5.4 3-WAY VISUALIZATION"
    )


    check(
        "10.5.4 stage exact",
        probability_contract.get(
            "stage"
        )
        ==
        "10.5.4",
        failures,
    )


    check(
        "10.5.4 contract LOCKED",
        probability_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    for field in [
        "stage7_prob_home_win",
        "stage7_prob_draw",
        "stage7_prob_away_win",
    ]:

        check(
            f"Probability source marker: {field}",
            field
            in
            probability_source,
            failures,
        )


    check(
        "Native progress element used",
        "<progress"
        in
        probability_source,
        failures,
    )


    check(
        "Progress maximum is raw probability scale 1",
        "max={1}"
        in
        probability_source,
        failures,
    )


    check(
        "Raw probability supplied to progress value",
        "value={"
        in
        probability_source
        and
        "probability"
        in
        probability_source,
        failures,
    )


    check(
        "Display formatter used",
        "formatProbability"
        in
        probability_source,
        failures,
    )


    check(
        "No percent multiplication",
        "* 100"
        not in
        probability_source
        and
        "*100"
        not in
        probability_source,
        failures,
    )


    check(
        "No probability normalization",
        "normalize"
        not in
        probability_source.lower(),
        failures,
    )


    check(
        "No probability sorting",
        ".sort("
        not in
        probability_source,
        failures,
    )


    print(
        "\n6. STAGE 10.5.5 CONFIDENCE"
    )


    check(
        "10.5.5 stage exact",
        confidence_contract.get(
            "stage"
        )
        ==
        "10.5.5",
        failures,
    )


    check(
        "10.5.5 contract LOCKED",
        confidence_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Stage 7 confidence marker",
        (
            'data-stage7-field="stage7_confidence"'
            in
            confidence_source
        ),
        failures,
    )


    check(
        "Stage 7 confidence formatted",
        "formatProbability"
        in
        confidence_source
        and
        "confidence"
        in
        confidence_source,
        failures,
    )


    check(
        "Stage 9 confidence band marker",
        (
            'data-stage9-field="stage9_confidence_band"'
            in
            confidence_source
        ),
        failures,
    )


    check(
        "Confidence band displayed directly",
        "{confidenceBand}"
        in
        confidence_source,
        failures,
    )


    check(
        "No confidence thresholds",
        all(
            token
            not in
            confidence_source

            for token in [
                "0.4",
                "0.5",
                "0.6",
                "0.7",
            ]
        ),
        failures,
    )


    print(
        "\n7. STAGE 10.5.6 UNCERTAINTY"
    )


    check(
        "10.5.6 stage exact",
        uncertainty_contract.get(
            "stage"
        )
        ==
        "10.5.6",
        failures,
    )


    check(
        "10.5.6 contract LOCKED",
        uncertainty_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Uncertainty Stage 9 authority",
        uncertainty_contract.get(
            "authority"
        )
        ==
        "STAGE_9_INTELLIGENCE",
        failures,
    )


    check(
        "Stage 9 uncertainty marker",
        (
            'data-stage9-field="stage9_uncertainty_band"'
            in
            uncertainty_source
        ),
        failures,
    )


    check(
        "Uncertainty band rendered directly",
        "{uncertaintyBand}"
        in
        uncertainty_source,
        failures,
    )


    check(
        "No entropy calculation",
        (
            "Math.log"
            not in
            uncertainty_source
            and
            "entropy"
            not in
            uncertainty_source.lower()
        ),
        failures,
    )


    print(
        "\n8. ROUTE INTEGRATION"
    )


    check(
        "Prediction record extractor imported",
        "extractMatchPredictionRecord"
        in
        route_source,
        failures,
    )


    check(
        "Prediction record extracted from READY data",
        (
            "extractMatchPredictionRecord"
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
        "MatchPredictionOverview",
        "MatchProbabilityVisualization",
        "MatchConfidence",
        "MatchUncertainty",
    ]:

        check(
            f"Route renders {component}",
            f"<{component}"
            in
            route_source,
            failures,
        )


    route_mapping_checks = [
        "prediction.stage7_predicted_label",
        "prediction.stage7_prob_home_win",
        "prediction.stage7_prob_draw",
        "prediction.stage7_prob_away_win",
        "prediction.stage7_confidence",
        "prediction.stage9_confidence_band",
        "prediction.stage9_uncertainty_band",
    ]


    for expression in route_mapping_checks:

        check(
            f"Route direct mapping: {expression}",
            expression
            in
            route_source,
            failures,
        )


    print(
        "\n9. 10.5.7+ NOT IMPLEMENTED EARLY"
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
        overview_source
        +
        "\n"
        +
        probability_source
        +
        "\n"
        +
        confidence_source
        +
        "\n"
        +
        uncertainty_source
    )


    forbidden_future = [
        "stage9_context_support_score",
        "stage9_context_alignment",
        "stage9_explanation_headline",
        "stage9_explanation_summary",
        "home_team_position",
        "away_team_position",
        "home_team_points",
        "away_team_points",
        "home_team_goal_difference",
        "away_team_goal_difference",
        "recent_results",
        "recent_points",
        "venue_form",
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


    check(
        "No probability argmax",
        "Math.max"
        not in
        combined,
        failures,
    )


    check(
        "No probability recalibration",
        "recalibr"
        not in
        combined.lower(),
        failures,
    )


    print(
        "\n11. PREVIOUS SOURCE PROTECTION"
    )


    protected = (
        uncertainty_contract.get(
            "protected_state",
            {},
        )
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
        (
            "Stage 10.4 dashboard page",
            ROOT_PAGE_FILE,
            "dashboard_page_sha256",
        ),
        (
            "Stage 10.4 MatchCard",
            MATCH_CARD_FILE,
            "dashboard_match_card_sha256",
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
        "Dashboard contract page identity still exact",
        dashboard_contract.get(
            "page_after_dashboard_sha256"
        )
        ==
        sha256_file(
            ROOT_PAGE_FILE
        ),
        failures,
    )


    check(
        "Dashboard MatchCard identity still exact",
        dashboard_contract.get(
            "match_card_sha256"
        )
        ==
        sha256_file(
            MATCH_CARD_FILE
        ),
        failures,
    )


    print(
        "\n12. CURRENT SOURCE IDENTITY"
    )


    check(
        "Prediction overview SHA exact",
        overview_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            OVERVIEW_COMPONENT_FILE
        ),
        failures,
    )


    check(
        "Probability visualization SHA exact",
        probability_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            PROBABILITY_COMPONENT_FILE
        ),
        failures,
    )


    check(
        "Confidence SHA exact",
        confidence_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            CONFIDENCE_COMPONENT_FILE
        ),
        failures,
    )


    check(
        "Uncertainty SHA exact",
        uncertainty_contract.get(
            "component_sha256"
        )
        ==
        sha256_file(
            UNCERTAINTY_COMPONENT_FILE
        ),
        failures,
    )


    check(
        "Prediction record SHA exact",
        uncertainty_contract.get(
            "record_source_sha256"
        )
        ==
        sha256_file(
            PREDICTION_RECORD_FILE
        ),
        failures,
    )


    check(
        "Route page SHA exact",
        uncertainty_contract.get(
            "route_page_after_10_5_6_sha256"
        )
        ==
        sha256_file(
            ROUTE_PAGE_FILE
        ),
        failures,
    )


    check(
        "Route started from verified 10.5.2",
        overview_contract.get(
            "route_page_before_10_5_3_sha256"
        )
        ==
        header_contract.get(
            "route_page_after_header_sha256"
        ),
        failures,
    )


    print(
        "\n13. DEPENDENCY FRESHNESS"
    )


    for stage, contract in [
        (
            "10.5.3",
            overview_contract,
        ),
        (
            "10.5.4",
            probability_contract,
        ),
        (
            "10.5.5",
            confidence_contract,
        ),
        (
            "10.5.6",
            uncertainty_contract,
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
            "10.5.3",
            overview_contract,
            "stage10_5_3_complete",
        ),
        (
            "10.5.4",
            probability_contract,
            "stage10_5_4_complete",
        ),
        (
            "10.5.5",
            confidence_contract,
            "stage10_5_5_complete",
        ),
        (
            "10.5.6",
            uncertainty_contract,
            "stage10_5_6_complete",
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
                "10.5.3-10.5.6",

            "name":
                (
                    "MATCH_PREDICTION_DETAIL_"
                    "VERIFICATION"
                ),

            "status":
                "PASS",

            "stage_10_5_3_complete":
                True,

            "stage_10_5_4_complete":
                True,

            "stage_10_5_5_complete":
                True,

            "stage_10_5_6_complete":
                True,

            "prediction_overview":
                "LOCKED_AND_VERIFIED",

            "three_way_probability_visualization":
                "LOCKED_AND_VERIFIED",

            "confidence":
                "LOCKED_AND_VERIFIED",

            "uncertainty":
                "LOCKED_AND_VERIFIED",

            "authority": {
                "probabilities":
                    "STAGE_7",

                "predicted_label":
                    "STAGE_7",

                "confidence":
                    "STAGE_7",

                "confidence_band":
                    "STAGE_9",

                "uncertainty_band":
                    "STAGE_9",
            },

            "integrity": {
                "transport_string_to_number_only":
                    True,

                "probabilities_modified":
                    False,

                "probabilities_normalized":
                    False,

                "probabilities_recalibrated":
                    False,

                "prediction_rederived":
                    False,

                "confidence_band_derived_frontend":
                    False,

                "uncertainty_band_derived_frontend":
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

            "stage10_ready_for_10_5_7":
                True,

            "stage10_5_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.5.7",

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
            "STAGE 10.5.3: PASS"
        )

        print(
            "PREDICTION OVERVIEW: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.5.4: PASS"
        )

        print(
            "3-WAY VISUALIZATION: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.5.5: PASS"
        )

        print(
            "CONFIDENCE: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.5.6: PASS"
        )

        print(
            "UNCERTAINTY: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.5.7"
        )

        print(
            "STAGE 10.5 IS NOT YET COMPLETE"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.5.3 - 10.5.6: FAIL"
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
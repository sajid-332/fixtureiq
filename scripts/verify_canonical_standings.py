"""
FixtureIQ Stage 8.2.3
Independent Canonical Standings Verification.

Verifies the generated artifacts only.

No provider fetch.
No model loading.
No model execution.
No prediction execution.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path


# ============================================================
# Paths
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

CONTEXT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "context"
)

PRODUCTION_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "production"
)

CONTRACT_FILE = (
    CONTEXT_DIR
    / "stage8_context_contract.json"
)

CONTRACT_VERIFICATION_FILE = (
    CONTEXT_DIR
    / "stage8_context_contract_verification.json"
)

STANDINGS_FILE = (
    CONTEXT_DIR
    / "current_standings.csv"
)

REPORT_FILE = (
    CONTEXT_DIR
    / "standings_report.json"
)

UPCOMING_FIXTURES_FILE = (
    PRODUCTION_DIR
    / "upcoming_fixtures.csv"
)


EXPECTED_FIELDS = [

    "team_id",
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


# ============================================================
# Helpers
# ============================================================

def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise FileNotFoundError(
            f"Required artifact missing: {path}"
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

        while True:

            chunk = file.read(
                1024 * 1024
            )

            if not chunk:

                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


def relative_path(
    path: Path,
) -> str:

    return (
        str(
            path.relative_to(
                BASE_DIR
            )
        )
        .replace(
            "\\",
            "/",
        )
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


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.2.3"
    )

    print(
        "Canonical EPL Standings Verification"
    )

    print("=" * 72)

    failures = []

    # ========================================================
    # 1. Required artifacts
    # ========================================================

    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    required = [

        CONTRACT_FILE,
        CONTRACT_VERIFICATION_FILE,

        STANDINGS_FILE,
        REPORT_FILE,

        UPCOMING_FIXTURES_FILE,
    ]

    for path in required:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        sys.exit(1)

    contract = load_json(
        CONTRACT_FILE
    )

    contract_verification = load_json(
        CONTRACT_VERIFICATION_FILE
    )

    report = load_json(
        REPORT_FILE
    )

    # ========================================================
    # 2. Stage 8 foundation
    # ========================================================

    print(
        "\n2. STAGE 8 FOUNDATION"
    )

    check(
        "Stage 8.1 COMPLETE",
        contract.get(
            "stage_8_1_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 8 contract LOCKED",
        contract.get(
            "contract_status"
        )
        == "LOCKED_CONTEXT_CONTRACT",
        failures,
    )

    check(
        "Stage 8.1 verification PASS",
        contract_verification.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "8.2.1 previously PASS",
        report.get(
            "sub_stages",
            {}
        ).get(
            "8.2.1"
        )
        == "PASS",
        failures,
    )

    check(
        "8.2.2 previously PASS",
        report.get(
            "sub_stages",
            {}
        ).get(
            "8.2.2"
        )
        == "PASS",
        failures,
    )

    check(
        "8.2.3 builder PASS",
        report.get(
            "sub_stages",
            {}
        ).get(
            "8.2.3"
        )
        == "PASS",
        failures,
    )

    # ========================================================
    # 3. Locked output contract
    # ========================================================

    print(
        "\n3. OUTPUT CONTRACT"
    )

    output_contract = contract.get(
        "output_artifact_contract",
        {}
    )

    outputs = output_contract.get(
        "outputs",
        {}
    )

    check(
        "current_standings path locked",
        outputs.get(
            "current_standings",
            {}
        ).get(
            "path"
        )
        ==
        relative_path(
            STANDINGS_FILE
        ),
        failures,
    )

    check(
        "standings_report path locked",
        outputs.get(
            "standings_report",
            {}
        ).get(
            "path"
        )
        ==
        relative_path(
            REPORT_FILE
        ),
        failures,
    )

    check(
        "Stage 7 writes prohibited",
        output_contract.get(
            "stage7_output_write_allowed"
        )
        is False,
        failures,
    )

    # ========================================================
    # 4. Read canonical CSV
    # ========================================================

    print(
        "\n4. CANONICAL CSV SCHEMA"
    )

    with STANDINGS_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        actual_fields = (
            reader.fieldnames
            or []
        )

        rows = list(
            reader
        )

    check(
        "Schema exact",
        actual_fields
        == EXPECTED_FIELDS,
        failures,
    )

    check(
        "Column count = 11",
        len(
            actual_fields
        )
        == 11,
        failures,
    )

    check(
        "Row count = 20",
        len(
            rows
        )
        == 20,
        failures,
    )

    check(
        "Provider ID excluded from CSV",
        "provider_team_id"
        not in actual_fields,
        failures,
    )

    check(
        "Provider name excluded from CSV",
        "provider_team_name"
        not in actual_fields,
        failures,
    )

    # ========================================================
    # 5. Canonical identity
    # ========================================================

    print(
        "\n5. CANONICAL TEAM IDENTITY"
    )

    team_ids = [

        row[
            "team_id"
        ].strip()

        for row in rows
    ]

    team_names = [

        row[
            "team_name"
        ].strip()

        for row in rows
    ]

    check(
        "No blank team IDs",
        all(
            team_ids
        ),
        failures,
    )

    check(
        "No blank team names",
        all(
            team_names
        ),
        failures,
    )

    check(
        "20 unique team IDs",
        len(
            set(
                team_ids
            )
        )
        == 20,
        failures,
    )

    check(
        "20 unique team names",
        len(
            {
                name.casefold()
                for name in team_names
            }
        )
        == 20,
        failures,
    )

    # ========================================================
    # 6. Standings integrity
    # ========================================================

    print(
        "\n6. STANDINGS INTEGRITY"
    )

    try:

        positions = [

            int(
                row[
                    "position"
                ]
            )

            for row in rows
        ]

        numeric_rows_valid = True

    except (
        TypeError,
        ValueError,
    ):

        positions = []

        numeric_rows_valid = False

    check(
        "Numeric position values valid",
        numeric_rows_valid,
        failures,
    )

    check(
        "Sorted position ASC",
        positions
        == list(
            range(
                1,
                21,
            )
        ),
        failures,
    )

    played_equation = True
    goal_difference_equation = True
    points_equation = True
    non_negative = True

    try:

        for row in rows:

            played = int(
                row[
                    "played"
                ]
            )

            won = int(
                row[
                    "won"
                ]
            )

            drawn = int(
                row[
                    "drawn"
                ]
            )

            lost = int(
                row[
                    "lost"
                ]
            )

            goals_for = int(
                row[
                    "goals_for"
                ]
            )

            goals_against = int(
                row[
                    "goals_against"
                ]
            )

            goal_difference = int(
                row[
                    "goal_difference"
                ]
            )

            points = int(
                row[
                    "points"
                ]
            )

            if (
                played
                !=
                won + drawn + lost
            ):

                played_equation = False

            if (
                goal_difference
                !=
                goals_for - goals_against
            ):

                goal_difference_equation = False

            if (
                points
                !=
                (3 * won) + drawn
            ):

                points_equation = False

            if min(
                played,
                won,
                drawn,
                lost,
                goals_for,
                goals_against,
                points,
            ) < 0:

                non_negative = False

    except (
        TypeError,
        ValueError,
        KeyError,
    ):

        played_equation = False
        goal_difference_equation = False
        points_equation = False
        non_negative = False

    check(
        "played = W + D + L",
        played_equation,
        failures,
    )

    check(
        "GD = GF - GA",
        goal_difference_equation,
        failures,
    )

    check(
        "points = 3W + D",
        points_equation,
        failures,
    )

    check(
        "Non-negative counts",
        non_negative,
        failures,
    )

    # ========================================================
    # 7. Artifact hash
    # ========================================================

    print(
        "\n7. ARTIFACT INTEGRITY"
    )

    actual_standings_sha = (
        sha256_file(
            STANDINGS_FILE
        )
    )

    report_standings = report.get(
        "current_standings",
        {}
    )

    check(
        "CSV hash matches report",
        report_standings.get(
            "sha256"
        )
        == actual_standings_sha,
        failures,
    )

    check(
        "Report row count = 20",
        report_standings.get(
            "row_count"
        )
        == 20,
        failures,
    )

    check(
        "Report columns exact",
        report_standings.get(
            "columns"
        )
        == EXPECTED_FIELDS,
        failures,
    )

    check(
        "Team namespace fixtureiq-team",
        report_standings.get(
            "team_namespace"
        )
        == "fixtureiq-team",
        failures,
    )

    check(
        "Provider IDs excluded",
        report_standings.get(
            "provider_ids_in_public_csv"
        )
        is False,
        failures,
    )

    # ========================================================
    # 8. Provenance
    # ========================================================

    print(
        "\n8. PROVENANCE"
    )

    check(
        "generated_at_utc present",
        bool(
            report.get(
                "generated_at_utc"
            )
        ),
        failures,
    )

    check(
        "source_as_of_utc present",
        bool(
            report.get(
                "source_as_of_utc"
            )
        ),
        failures,
    )

    check(
        "Provider football-data.org",
        report.get(
            "provider"
        )
        == "football-data.org",
        failures,
    )

    check(
        "Competition code PL",
        report.get(
            "competition_code"
        )
        == "PL",
        failures,
    )

    check(
        "Season 2026",
        report.get(
            "season"
        )
        == 2026,
        failures,
    )

    dependencies = report.get(
        "dependency_identity",
        {}
    )

    expected_dependencies = {

        "stage8_context_contract":
            CONTRACT_FILE,

        "stage8_context_contract_verification":
            CONTRACT_VERIFICATION_FILE,

        "upcoming_fixtures_team_registry":
            UPCOMING_FIXTURES_FILE,
    }

    for (
        name,
        path,
    ) in expected_dependencies.items():

        dependency = (
            dependencies.get(
                name,
                {}
            )
        )

        check(
            f"{name} dependency declared",
            bool(
                dependency
            ),
            failures,
        )

        check(
            f"{name} hash valid",
            dependency.get(
                "sha256"
            )
            ==
            sha256_file(
                path
            ),
            failures,
        )

    # ========================================================
    # 9. Safety boundary
    # ========================================================

    print(
        "\n9. SAFETY BOUNDARY"
    )

    safety = report.get(
        "safety",
        {}
    )

    check(
        "Context only",
        safety.get(
            "context_only"
        )
        is True,
        failures,
    )

    check(
        "Stage 7 artifacts untouched",
        safety.get(
            "stage7_artifacts_modified"
        )
        is False,
        failures,
    )

    check(
        "Model not loaded",
        safety.get(
            "model_loaded"
        )
        is False,
        failures,
    )

    check(
        "Model not executed",
        safety.get(
            "model_executed"
        )
        is False,
        failures,
    )

    check(
        "Model not modified",
        safety.get(
            "model_modified"
        )
        is False,
        failures,
    )

    check(
        "Predictions not modified",
        safety.get(
            "production_predictions_modified"
        )
        is False,
        failures,
    )

    check(
        "Feature schema not modified",
        safety.get(
            "feature_schema_modified"
        )
        is False,
        failures,
    )

    check(
        "Standings not model features",
        safety.get(
            "standings_used_as_model_features"
        )
        is False,
        failures,
    )

    check(
        "Final test not accessed",
        safety.get(
            "final_test_accessed"
        )
        is False,
        failures,
    )

    # ========================================================
    # 10. Final decision
    # ========================================================

    print(
        "\n10. FINAL 8.2.3 DECISION"
    )

    overall_pass = (
        len(
            failures
        )
        == 0
    )

    if overall_pass:

        print(
            "\n" + "=" * 72
        )

        print(
            "STAGE 8.2.1: PASS"
        )

        print(
            "STAGE 8.2.2: PASS"
        )

        print(
            "STAGE 8.2.3: PASS"
        )

        print(
            "CANONICAL EPL STANDINGS: VERIFIED"
        )

        print(
            "STAGE 8.2: IN PROGRESS"
        )

        print("=" * 72)

    else:

        print(
            "\n" + "=" * 72
        )

        print(
            "STAGE 8.2.3: FAIL"
        )

        print(
            "STAGE 8.2: INCOMPLETE"
        )

        print(
            "\nFailures:"
        )

        for failure in failures:

            print(
                f"  - {failure}"
            )

        print("=" * 72)

    sys.exit(
        0
        if overall_pass
        else 1
    )


if __name__ == "__main__":

    main()
"""
FixtureIQ Stage 8.2.3
Canonical EPL Standings Builder.

Pipeline:

football-data.org
        ->
provider standings
        ->
FixtureIQ deterministic normalization
        ->
canonical current_standings.csv
        ->
standings_report.json

This stage does NOT:
- modify Stage 7 artifacts
- modify production predictions
- load or execute the ML model
- change the 86-feature schema
- use standings as model features
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# Project root
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(BASE_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(BASE_DIR),
    )


# ============================================================
# FixtureIQ imports
# ============================================================

from backend.providers.football_data_standings import (
    FootballDataStandingsClient,
)

from backend.services.standings_normalization_service import (
    StandingsNormalizationService,
)


# ============================================================
# Paths
# ============================================================

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

UPCOMING_FIXTURES_FILE = (
    PRODUCTION_DIR
    / "upcoming_fixtures.csv"
)

OUTPUT_FILE = (
    CONTEXT_DIR
    / "current_standings.csv"
)

REPORT_FILE = (
    CONTEXT_DIR
    / "standings_report.json"
)


# ============================================================
# Locked canonical CSV schema
# ============================================================

CSV_FIELDS = [

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

    if not path.exists():

        raise FileNotFoundError(
            f"Required artifact missing: {path}"
        )

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


def validate_rows(
    rows: list[dict],
) -> None:

    if len(rows) != 20:

        raise RuntimeError(
            (
                "Canonical standings must contain "
                f"exactly 20 teams, received {len(rows)}."
            )
        )

    team_ids = [
        str(
            row[
                "team_id"
            ]
        ).strip()
        for row in rows
    ]

    team_names = [
        str(
            row[
                "team_name"
            ]
        ).strip()
        for row in rows
    ]

    positions = [
        int(
            row[
                "position"
            ]
        )
        for row in rows
    ]

    if any(
        not value
        for value in team_ids
    ):

        raise RuntimeError(
            "Blank FixtureIQ team ID found."
        )

    if any(
        not value
        for value in team_names
    ):

        raise RuntimeError(
            "Blank FixtureIQ team name found."
        )

    if len(
        set(
            team_ids
        )
    ) != 20:

        raise RuntimeError(
            "FixtureIQ team IDs are not unique."
        )

    if len(
        {
            name.casefold()
            for name in team_names
        }
    ) != 20:

        raise RuntimeError(
            "FixtureIQ team names are not unique."
        )

    if positions != list(
        range(
            1,
            21,
        )
    ):

        raise RuntimeError(
            (
                "Canonical standings must be sorted "
                "exactly by positions 1 through 20."
            )
        )

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

        if min(
            played,
            won,
            drawn,
            lost,
            goals_for,
            goals_against,
            points,
        ) < 0:

            raise RuntimeError(
                (
                    "Negative standings value found for "
                    f"{row['team_name']}."
                )
            )

        if (
            played
            !=
            won + drawn + lost
        ):

            raise RuntimeError(
                (
                    "played != won + drawn + lost for "
                    f"{row['team_name']}."
                )
            )

        if (
            goal_difference
            !=
            goals_for - goals_against
        ):

            raise RuntimeError(
                (
                    "Invalid goal difference for "
                    f"{row['team_name']}."
                )
            )

        if (
            points
            !=
            (3 * won) + drawn
        ):

            raise RuntimeError(
                (
                    "Invalid points arithmetic for "
                    f"{row['team_name']}."
                )
            )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.2.3"
    )

    print(
        "Canonical EPL Standings Builder"
    )

    print("=" * 72)

    CONTEXT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # 1. Stage 8.1 foundation
    # ========================================================

    print(
        "\n1. STAGE 8.1 FOUNDATION"
    )

    contract = load_json(
        CONTRACT_FILE
    )

    contract_verification = load_json(
        CONTRACT_VERIFICATION_FILE
    )

    if (
        contract.get(
            "stage_8_1_complete"
        )
        is not True
    ):

        raise RuntimeError(
            "Stage 8.1 contract is not complete."
        )

    if (
        contract.get(
            "contract_status"
        )
        != "LOCKED_CONTEXT_CONTRACT"
    ):

        raise RuntimeError(
            "Stage 8 context contract is not locked."
        )

    if (
        contract_verification.get(
            "status"
        )
        != "PASS"
    ):

        raise RuntimeError(
            (
                "Stage 8.1 verification "
                "is not PASS."
            )
        )

    print(
        "Stage 8.1 contract: PASS"
    )

    print(
        "Context contract lock: PASS"
    )

    # ========================================================
    # 2. Verify declared output paths
    # ========================================================

    print(
        "\n2. OUTPUT CONTRACT"
    )

    output_contract = contract.get(
        "output_artifact_contract",
        {}
    )

    outputs = output_contract.get(
        "outputs",
        {}
    )

    standings_output = outputs.get(
        "current_standings",
        {}
    )

    report_output = outputs.get(
        "standings_report",
        {}
    )

    expected_csv_path = (
        relative_path(
            OUTPUT_FILE
        )
    )

    expected_report_path = (
        relative_path(
            REPORT_FILE
        )
    )

    if (
        standings_output.get(
            "path"
        )
        != expected_csv_path
    ):

        raise RuntimeError(
            (
                "current_standings.csv path does not "
                "match locked Stage 8 contract."
            )
        )

    if (
        report_output.get(
            "path"
        )
        != expected_report_path
    ):

        raise RuntimeError(
            (
                "standings_report.json path does not "
                "match locked Stage 8 contract."
            )
        )

    if (
        output_contract.get(
            "stage7_output_write_allowed"
        )
        is not False
    ):

        raise RuntimeError(
            (
                "Stage 7 write protection "
                "is not active."
            )
        )

    print(
        "current_standings.csv path: PASS"
    )

    print(
        "standings_report.json path: PASS"
    )

    print(
        "Stage 7 write protection: PASS"
    )

    # ========================================================
    # 3. Fetch live provider standings
    # ========================================================

    print(
        "\n3. FETCH LIVE EPL STANDINGS"
    )

    client = (
        FootballDataStandingsClient(
            competition_code="PL",
            season=2026,
        )
    )

    snapshot = (
        client.fetch_standings()
    )

    provider_rows = snapshot[
        "rows"
    ]

    print(
        f"Provider: {snapshot['provider']}"
    )

    print(
        f"Competition: {snapshot['competition_code']}"
    )

    print(
        f"Season: {snapshot['configured_season']}"
    )

    print(
        f"Provider teams: {len(provider_rows)}"
    )

    # ========================================================
    # 4. Normalize to FixtureIQ identity
    # ========================================================

    print(
        "\n4. FIXTUREIQ TEAM NORMALIZATION"
    )

    normalizer = (
        StandingsNormalizationService()
    )

    normalized_rows = (
        normalizer.normalize_standings(
            provider_rows
        )
    )

    print(
        "Canonical registry teams: "
        f"{normalizer.canonical_team_count}"
    )

    print(
        "Normalized teams: "
        f"{len(normalized_rows)}"
    )

    # ========================================================
    # 5. Canonicalize public rows
    # ========================================================

    print(
        "\n5. BUILD CANONICAL TABLE"
    )

    canonical_rows = []

    for row in normalized_rows:

        canonical_rows.append(
            {

                "team_id":
                    str(
                        row[
                            "team_id"
                        ]
                    ),

                "team_name":
                    str(
                        row[
                            "team_name"
                        ]
                    ),

                "position":
                    int(
                        row[
                            "position"
                        ]
                    ),

                "played":
                    int(
                        row[
                            "played"
                        ]
                    ),

                "won":
                    int(
                        row[
                            "won"
                        ]
                    ),

                "drawn":
                    int(
                        row[
                            "drawn"
                        ]
                    ),

                "lost":
                    int(
                        row[
                            "lost"
                        ]
                    ),

                "goals_for":
                    int(
                        row[
                            "goals_for"
                        ]
                    ),

                "goals_against":
                    int(
                        row[
                            "goals_against"
                        ]
                    ),

                "goal_difference":
                    int(
                        row[
                            "goal_difference"
                        ]
                    ),

                "points":
                    int(
                        row[
                            "points"
                        ]
                    ),
            }
        )

    canonical_rows.sort(
        key=lambda row:
            row[
                "position"
            ]
    )

    validate_rows(
        canonical_rows
    )

    print(
        "Canonical row count: PASS"
    )

    print(
        "Identity uniqueness: PASS"
    )

    print(
        "Positions 1..20: PASS"
    )

    print(
        "Standings arithmetic: PASS"
    )

    # ========================================================
    # 6. Write canonical CSV
    # ========================================================

    print(
        "\n6. WRITE CURRENT STANDINGS"
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=CSV_FIELDS,
        )

        writer.writeheader()

        writer.writerows(
            canonical_rows
        )

    standings_sha256 = (
        sha256_file(
            OUTPUT_FILE
        )
    )

    print(
        OUTPUT_FILE
    )

    print(
        f"SHA256: {standings_sha256}"
    )

    # ========================================================
    # 7. Dependency identity
    # ========================================================

    print(
        "\n7. PROVENANCE & DEPENDENCIES"
    )

    dependency_identity = {

        "stage8_context_contract": {

            "path":
                relative_path(
                    CONTRACT_FILE
                ),

            "sha256":
                sha256_file(
                    CONTRACT_FILE
                ),
        },

        "stage8_context_contract_verification": {

            "path":
                relative_path(
                    CONTRACT_VERIFICATION_FILE
                ),

            "sha256":
                sha256_file(
                    CONTRACT_VERIFICATION_FILE
                ),
        },

        "upcoming_fixtures_team_registry": {

            "path":
                relative_path(
                    UPCOMING_FIXTURES_FILE
                ),

            "sha256":
                sha256_file(
                    UPCOMING_FIXTURES_FILE
                ),

            "usage":
                "FIXTUREIQ_CANONICAL_TEAM_IDENTITY",
        },
    }

    for name, dependency in (
        dependency_identity.items()
    ):

        print(
            f"{name}: {dependency['sha256']}"
        )

    # ========================================================
    # 8. Provider mapping evidence
    # ========================================================

    mappings = [

        {

            "provider_team_id":
                row[
                    "provider_team_id"
                ],

            "provider_team_name":
                row[
                    "provider_team_name"
                ],

            "team_id":
                row[
                    "team_id"
                ],

            "team_name":
                row[
                    "team_name"
                ],
        }

        for row in normalized_rows
    ]

    # ========================================================
    # 9. Write report
    # ========================================================

    print(
        "\n8. WRITE STANDINGS REPORT"
    )

    generated_at_utc = (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )

    report = {

        "stage":
            "8.2",

        "status":
            "PARTIAL_PASS",

        "stage_8_2_complete":
            False,

        "sub_stages": {

            "8.2.1":
                "PASS",

            "8.2.2":
                "PASS",

            "8.2.3":
                "PASS",

            "8.2.4":
                "PENDING",

            "8.2.5":
                "PENDING",
        },

        "provider_fetch":
            "VERIFIED",

        "team_normalization":
            "VERIFIED",

        "canonical_standings":
            "VERIFIED",

        # ----------------------------------------------------
        # Required Stage 8 provenance
        # ----------------------------------------------------

        "generated_at_utc":
            generated_at_utc,

        "source_as_of_utc":
            snapshot.get(
                "source_as_of_utc"
            ),

        "provider":
            snapshot.get(
                "provider"
            ),

        "competition":
            snapshot.get(
                "competition"
            ),

        "competition_code":
            snapshot.get(
                "competition_code"
            ),

        "season":
            snapshot.get(
                "configured_season"
            ),

        "provider_season_id":
            snapshot.get(
                "provider_season_id"
            ),

        "current_matchday":
            snapshot.get(
                "current_matchday"
            ),

        "season_start_date":
            snapshot.get(
                "season_start_date"
            ),

        "season_end_date":
            snapshot.get(
                "season_end_date"
            ),

        "provider_fetch_timestamp_utc":
            snapshot.get(
                "fetched_at_utc"
            ),

        # ----------------------------------------------------
        # Canonical artifact
        # ----------------------------------------------------

        "current_standings": {

            "path":
                relative_path(
                    OUTPUT_FILE
                ),

            "sha256":
                standings_sha256,

            "row_count":
                len(
                    canonical_rows
                ),

            "column_count":
                len(
                    CSV_FIELDS
                ),

            "columns":
                CSV_FIELDS,

            "sort_order":
                "position ASC",

            "team_namespace":
                "fixtureiq-team",

            "provider_ids_in_public_csv":
                False,
        },

        # ----------------------------------------------------
        # Data quality
        # ----------------------------------------------------

        "integrity": {

            "expected_team_count":
                20,

            "actual_team_count":
                len(
                    canonical_rows
                ),

            "unique_team_ids":
                len(
                    {
                        row[
                            "team_id"
                        ]
                        for row in canonical_rows
                    }
                ),

            "unique_team_names":
                len(
                    {
                        row[
                            "team_name"
                        ].casefold()
                        for row in canonical_rows
                    }
                ),

            "positions_1_to_20":
                True,

            "played_equation_valid":
                True,

            "goal_difference_equation_valid":
                True,

            "points_equation_valid":
                True,

            "unknown_team_count":
                0,

            "duplicate_team_count":
                0,
        },

        # ----------------------------------------------------
        # Dependencies / freshness
        # ----------------------------------------------------

        "dependency_identity":
            dependency_identity,

        "freshness": {

            "mode":
                "DEPENDENCY_BASED",

            "snapshot_generated_at_utc":
                generated_at_utc,

            "source_as_of_utc":
                snapshot.get(
                    "source_as_of_utc"
                ),

            "provider_snapshot_valid":
                True,

            "dependency_identity_recorded":
                True,
        },

        # ----------------------------------------------------
        # Safety
        # ----------------------------------------------------

        "safety": {

            "context_only":
                True,

            "stage7_artifacts_modified":
                False,

            "model_loaded":
                False,

            "model_executed":
                False,

            "model_modified":
                False,

            "production_predictions_modified":
                False,

            "feature_schema_modified":
                False,

            "standings_used_as_model_features":
                False,

            "final_test_accessed":
                False,
        },

        "team_mappings":
            mappings,

        "failures":
            [],
    }

    with REPORT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
        )

    print(
        REPORT_FILE
    )

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
        "STAGE 8.2.3: BUILT"
    )

    print(
        "CANONICAL EPL STANDINGS: CREATED"
    )

    print(
        "STAGE 8.2: IN PROGRESS"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
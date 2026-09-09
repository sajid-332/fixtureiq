"""
FixtureIQ Stage 8.2.1 + 8.2.2 Verification

8.2.1:
- fetch live EPL standings from football-data.org
- verify PL / season 2026 / TOTAL table
- verify 20 provider teams

8.2.2:
- map provider teams to FixtureIQ canonical identity
- verify 20/20 mappings
- reject unknown/duplicate teams
- ensure provider IDs remain metadata only

No current_standings.csv is written yet.
That belongs to Stage 8.2.3.

This verifier writes only:
data/processed/context/standings_report.json
"""

from __future__ import annotations

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

if str(
    BASE_DIR
) not in sys.path:

    sys.path.insert(
        0,
        str(
            BASE_DIR
        ),
    )


# ============================================================
# Imports
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

REPORT_FILE = (
    CONTEXT_DIR
    / "standings_report.json"
)


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
        "FixtureIQ Stage 8.2.1 + 8.2.2"
    )

    print(
        "Live EPL Standings Source + Team Normalization Verification"
    )

    print("=" * 72)

    failures = []

    CONTEXT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # 1. Required Stage 8.1 contract
    # ========================================================

    print(
        "\n1. STAGE 8.1 FOUNDATION"
    )

    required = [
        CONTRACT_FILE,
        CONTRACT_VERIFICATION_FILE,
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

    verification = load_json(
        CONTRACT_VERIFICATION_FILE
    )

    check(
        "Stage 8.1 contract COMPLETE",
        contract.get(
            "stage_8_1_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 8.1 contract status COMPLETE",
        contract.get(
            "stage_8_1_status"
        )
        == "COMPLETE",
        failures,
    )

    check(
        "Stage 8 context contract LOCKED",
        contract.get(
            "contract_status"
        )
        == "LOCKED_CONTEXT_CONTRACT",
        failures,
    )

    check(
        "Stage 8.1 verification PASS",
        verification.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 8.1 verification complete",
        verification.get(
            "stage_8_1_complete"
        )
        is True,
        failures,
    )

    if failures:

        print(
            "\nStage 8.1 foundation invalid."
        )

        sys.exit(1)

    # ========================================================
    # 2. Contract provider identity
    # ========================================================

    print(
        "\n2. PROVIDER CONTRACT"
    )

    trusted = contract.get(
        "trusted_inputs",
        {}
    )

    provider_contract = trusted.get(
        "live_context_provider",
        {}
    )

    check(
        "Provider = football-data.org",
        provider_contract.get(
            "provider"
        )
        == "football-data.org",
        failures,
    )

    check(
        "Provider role live context",
        provider_contract.get(
            "role"
        )
        == "PRIMARY_LIVE_CONTEXT_PROVIDER",
        failures,
    )

    check(
        "Competition = Premier League",
        provider_contract.get(
            "competition"
        )
        == "Premier League",
        failures,
    )

    check(
        "Competition code = PL",
        provider_contract.get(
            "competition_code"
        )
        == "PL",
        failures,
    )

    check(
        "Configured season = 2026",
        provider_contract.get(
            "configured_season"
        )
        == 2026,
        failures,
    )

    # ========================================================
    # 3. Stage 8.2.1 provider fetch
    # ========================================================

    print(
        "\n3. STAGE 8.2.1 - LIVE STANDINGS FETCH"
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

    provider_rows = snapshot.get(
        "rows",
        []
    )

    check(
        "Live request succeeded",
        isinstance(
            snapshot,
            dict,
        ),
        failures,
    )

    check(
        "Response provider football-data.org",
        snapshot.get(
            "provider"
        )
        == "football-data.org",
        failures,
    )

    check(
        "Response competition code PL",
        snapshot.get(
            "competition_code"
        )
        == "PL",
        failures,
    )

    check(
        "Response configured season 2026",
        snapshot.get(
            "configured_season"
        )
        == 2026,
        failures,
    )

    check(
        "Standings type TOTAL",
        str(
            snapshot.get(
                "standings_type",
                ""
            )
        )
        .upper()
        == "TOTAL",
        failures,
    )

    check(
        "Provider row count = 20",
        len(
            provider_rows
        )
        == 20,
        failures,
    )

    provider_ids = [
        row[
            "provider_team_id"
        ]
        for row in provider_rows
    ]

    provider_names = [
        row[
            "provider_team_name"
        ]
        for row in provider_rows
    ]

    positions = [
        int(
            row[
                "position"
            ]
        )
        for row in provider_rows
    ]

    check(
        "20 unique provider IDs",
        len(
            set(
                provider_ids
            )
        )
        == 20,
        failures,
    )

    check(
        "20 unique provider names",
        len(
            {
                name.casefold()
                for name in provider_names
            }
        )
        == 20,
        failures,
    )

    check(
        "Positions exactly 1..20",
        sorted(
            positions
        )
        == list(
            range(
                1,
                21,
            )
        ),
        failures,
    )

    check(
        "Provider source timestamp present",
        bool(
            snapshot.get(
                "source_as_of_utc"
            )
        ),
        failures,
    )

    check(
        "Fetch timestamp present",
        bool(
            snapshot.get(
                "fetched_at_utc"
            )
        ),
        failures,
    )

    # ========================================================
    # 4. Stage 8.2.2 canonical normalization
    # ========================================================

    print(
        "\n4. STAGE 8.2.2 - TEAM NORMALIZATION"
    )

    normalization_service = (
        StandingsNormalizationService()
    )

    check(
        "FixtureIQ canonical registry = 20",
        normalization_service
        .canonical_team_count
        == 20,
        failures,
    )

    normalized = (
        normalization_service
        .normalize_standings(
            provider_rows
        )
    )

    check(
        "Normalized standings = 20",
        len(
            normalized
        )
        == 20,
        failures,
    )

    fixtureiq_ids = [
        row[
            "team_id"
        ]
        for row in normalized
    ]

    fixtureiq_names = [
        row[
            "team_name"
        ]
        for row in normalized
    ]

    normalized_positions = [
        int(
            row[
                "position"
            ]
        )
        for row in normalized
    ]

    check(
        "20 unique FixtureIQ IDs",
        len(
            set(
                fixtureiq_ids
            )
        )
        == 20,
        failures,
    )

    check(
        "20 unique canonical names",
        len(
            {
                name.casefold()
                for name in fixtureiq_names
            }
        )
        == 20,
        failures,
    )

    check(
        "Normalized positions 1..20",
        normalized_positions
        == list(
            range(
                1,
                21,
            )
        ),
        failures,
    )

    check(
        "Zero unknown teams",
        len(
            normalized
        )
        == len(
            provider_rows
        ),
        failures,
    )

    check(
        "Provider IDs remain separate metadata",
        all(
            (
                "provider_team_id"
                in row

                and

                "team_id"
                in row
            )
            for row in normalized
        ),
        failures,
    )

    # FixtureIQ IDs must come from the Stage 7 registry,
    # never blindly from provider IDs.
    check(
        "Provider IDs not reused as FixtureIQ IDs",
        all(
            str(
                row[
                    "provider_team_id"
                ]
            )
            !=
            str(
                row[
                    "team_id"
                ]
            )
            for row in normalized
        ),
        failures,
    )

    # ========================================================
    # 5. Basic standings integrity
    # ========================================================

    print(
        "\n5. SOURCE DATA INTEGRITY"
    )

    check(
        "played = won + drawn + lost",
        all(
            int(
                row[
                    "played"
                ]
            )
            ==
            (
                int(
                    row[
                        "won"
                    ]
                )
                +
                int(
                    row[
                        "drawn"
                    ]
                )
                +
                int(
                    row[
                        "lost"
                    ]
                )
            )
            for row in normalized
        ),
        failures,
    )

    check(
        "goal difference arithmetic valid",
        all(
            int(
                row[
                    "goal_difference"
                ]
            )
            ==
            (
                int(
                    row[
                        "goals_for"
                    ]
                )
                -
                int(
                    row[
                        "goals_against"
                    ]
                )
            )
            for row in normalized
        ),
        failures,
    )

    check(
        "points arithmetic valid",
        all(
            int(
                row[
                    "points"
                ]
            )
            ==
            (
                3
                *
                int(
                    row[
                        "won"
                    ]
                )
                +
                int(
                    row[
                        "drawn"
                    ]
                )
            )
            for row in normalized
        ),
        failures,
    )

    # ========================================================
    # 6. Stage 8 output boundary
    # ========================================================

    print(
        "\n6. OUTPUT CONTRACT"
    )

    output_contract = contract.get(
        "output_artifact_contract",
        {}
    )

    outputs = output_contract.get(
        "outputs",
        {}
    )

    current_standings_contract = (
        outputs.get(
            "current_standings",
            {}
        )
    )

    standings_report_contract = (
        outputs.get(
            "standings_report",
            {}
        )
    )

    check(
        "current_standings output declared",
        current_standings_contract.get(
            "path"
        )
        ==
        (
            "data/processed/context/"
            "current_standings.csv"
        ),
        failures,
    )

    check(
        "standings_report output declared",
        standings_report_contract.get(
            "path"
        )
        ==
        (
            "data/processed/context/"
            "standings_report.json"
        ),
        failures,
    )

    check(
        "Stage 7 write prohibited",
        output_contract.get(
            "stage7_output_write_allowed"
        )
        is False,
        failures,
    )

    # ========================================================
    # 7. Decision
    # ========================================================

    overall_pass = (
        len(
            failures
        )
        == 0
    )

    # ========================================================
    # 8. Save partial Stage 8.2 report
    # ========================================================

    print(
        "\n7. SAVE STANDINGS REPORT"
    )

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

        for row in normalized
    ]

    report = {

        "stage":
            "8.2",

        "status":
            (
                "PARTIAL_PASS"
                if overall_pass
                else "FAIL"
            ),

        "stage_8_2_complete":
            False,

        "sub_stages": {

            "8.2.1":
                (
                    "PASS"
                    if overall_pass
                    else "FAIL"
                ),

            "8.2.2":
                (
                    "PASS"
                    if overall_pass
                    else "FAIL"
                ),

            "8.2.3":
                "PENDING",

            "8.2.4":
                "PENDING",

            "8.2.5":
                "PENDING",
        },

        "provider_fetch":
            (
                "VERIFIED"
                if overall_pass
                else "NOT_VERIFIED"
            ),

        "team_normalization":
            (
                "VERIFIED"
                if overall_pass
                else "NOT_VERIFIED"
            ),

        "generated_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),

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

        "provider_team_count":
            len(
                provider_rows
            ),

        "canonical_team_count":
            len(
                normalized
            ),

        "unknown_team_count":
            (
                0
                if overall_pass
                else None
            ),

        "duplicate_team_count":
            (
                0
                if overall_pass
                else None
            ),

        "current_standings_csv_written":
            False,

        "current_standings_csv_owner":
            "8.2.3",

        "team_mappings":
            mappings,

        "failures":
            list(
                failures
            ),
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

    # ========================================================
    # Final
    # ========================================================

    print(
        "\n" + "=" * 72
    )

    if overall_pass:

        print(
            "STAGE 8.2.1: PASS"
        )

        print(
            "LIVE EPL STANDINGS SOURCE: VERIFIED"
        )

        print(
            "STAGE 8.2.2: PASS"
        )

        print(
            "FIXTUREIQ TEAM NORMALIZATION: VERIFIED"
        )

        print(
            "STAGE 8.2: IN PROGRESS"
        )

    else:

        print(
            "STAGE 8.2.1 / 8.2.2: FAIL"
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
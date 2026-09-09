"""
FixtureIQ Stage 8.2.5
Final Live EPL Standings Layer Gate.

Independently verifies:

8.2.1 - Live football-data.org standings source
8.2.2 - FixtureIQ team normalization
8.2.3 - Canonical standings artifact
8.2.4 - Standings service + dependency freshness
8.2.5 - Final Stage 8.2 integrity gate

On PASS:
- standings_report.json is promoted from PARTIAL_PASS -> PASS
- stage_8_2_complete = true
- stage_8_2_status = COMPLETE
- live_epl_standings_layer = VERIFIED

No model execution.
No provider fetch.
No Stage 7 writes.
No final-test access.
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

from backend.services.standings_service import (
    StandingsService,
)


# ============================================================
# Paths
# ============================================================

MODEL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
)

PRODUCTION_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "production"
)

CONTEXT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "context"
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

STANDINGS_REPORT_FILE = (
    CONTEXT_DIR
    / "standings_report.json"
)

UPCOMING_FIXTURES_FILE = (
    PRODUCTION_DIR
    / "upcoming_fixtures.csv"
)

STAGE7_8_FILE = (
    PRODUCTION_DIR
    / "stage7_8_final_verification.json"
)

STAGE7_9_FILE = (
    PRODUCTION_DIR
    / "stage7_9_final_verification.json"
)

SELECTED_MODEL_FILE = (
    MODEL_DIR
    / "selected"
    / "selected_model.joblib"
)


# ============================================================
# Locked canonical schema
# ============================================================

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


def save_json(
    path: Path,
    payload: dict,
) -> None:

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=2,
        )


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


def parse_aware_timestamp(
    value,
) -> bool:

    if not isinstance(
        value,
        str,
    ):

        return False

    text = value.strip()

    if not text:

        return False

    if text.endswith(
        "Z"
    ):

        text = (
            text[:-1]
            + "+00:00"
        )

    try:

        parsed = datetime.fromisoformat(
            text
        )

    except ValueError:

        return False

    return (
        parsed.tzinfo
        is not None
    )


def read_standings() -> tuple[
    list[str],
    list[dict],
]:

    with STANDINGS_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        fields = (
            reader.fieldnames
            or []
        )

        raw_rows = list(
            reader
        )

    rows = []

    for raw in raw_rows:

        rows.append(
            {

                "team_id":
                    str(
                        raw.get(
                            "team_id",
                            ""
                        )
                    ).strip(),

                "team_name":
                    str(
                        raw.get(
                            "team_name",
                            ""
                        )
                    ).strip(),

                "position":
                    int(
                        raw[
                            "position"
                        ]
                    ),

                "played":
                    int(
                        raw[
                            "played"
                        ]
                    ),

                "won":
                    int(
                        raw[
                            "won"
                        ]
                    ),

                "drawn":
                    int(
                        raw[
                            "drawn"
                        ]
                    ),

                "lost":
                    int(
                        raw[
                            "lost"
                        ]
                    ),

                "goals_for":
                    int(
                        raw[
                            "goals_for"
                        ]
                    ),

                "goals_against":
                    int(
                        raw[
                            "goals_against"
                        ]
                    ),

                "goal_difference":
                    int(
                        raw[
                            "goal_difference"
                        ]
                    ),

                "points":
                    int(
                        raw[
                            "points"
                        ]
                    ),
            }
        )

    return (
        fields,
        rows,
    )


def load_fixture_registry() -> set[
    tuple[str, str]
]:

    with UPCOMING_FIXTURES_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        fields = set(
            reader.fieldnames
            or []
        )

        required = {

            "home_team_id",
            "home_team_name",
            "away_team_id",
            "away_team_name",
        }

        if not required.issubset(
            fields
        ):

            raise RuntimeError(
                (
                    "upcoming_fixtures.csv canonical "
                    "team schema is invalid."
                )
            )

        registry = set()

        id_to_name = {}
        name_to_id = {}

        for row in reader:

            pairs = [

                (
                    row.get(
                        "home_team_id"
                    ),
                    row.get(
                        "home_team_name"
                    ),
                ),

                (
                    row.get(
                        "away_team_id"
                    ),
                    row.get(
                        "away_team_name"
                    ),
                ),
            ]

            for team_id, team_name in pairs:

                team_id = str(
                    team_id
                ).strip()

                team_name = str(
                    team_name
                ).strip()

                if (
                    not team_id
                    or
                    not team_name
                ):

                    raise RuntimeError(
                        (
                            "Blank canonical team identity "
                            "in upcoming fixtures."
                        )
                    )

                if (
                    team_id in id_to_name
                    and
                    id_to_name[
                        team_id
                    ]
                    != team_name
                ):

                    raise RuntimeError(
                        (
                            "FixtureIQ team ID maps to "
                            "multiple names."
                        )
                    )

                if (
                    team_name in name_to_id
                    and
                    name_to_id[
                        team_name
                    ]
                    != team_id
                ):

                    raise RuntimeError(
                        (
                            "FixtureIQ team name maps to "
                            "multiple IDs."
                        )
                    )

                id_to_name[
                    team_id
                ] = team_name

                name_to_id[
                    team_name
                ] = team_id

                registry.add(
                    (
                        team_id,
                        team_name,
                    )
                )

    return registry


def load_report_registry(
    report: dict,
) -> set[
    tuple[str, str]
]:

    mappings = report.get(
        "team_mappings",
        []
    )

    registry = set()

    for mapping in mappings:

        if not isinstance(
            mapping,
            dict,
        ):

            raise RuntimeError(
                "Invalid team mapping in standings report."
            )

        team_id = str(
            mapping.get(
                "team_id",
                ""
            )
        ).strip()

        team_name = str(
            mapping.get(
                "team_name",
                ""
            )
        ).strip()

        if (
            not team_id
            or
            not team_name
        ):

            raise RuntimeError(
                (
                    "Blank canonical identity "
                    "in standings report."
                )
            )

        registry.add(
            (
                team_id,
                team_name,
            )
        )

    return registry


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.2.5"
    )

    print(
        "Final Live EPL Standings Layer Gate"
    )

    print("=" * 72)

    failures = []

    # ========================================================
    # 1. Required artifacts
    # ========================================================

    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    required_files = [

        CONTRACT_FILE,
        CONTRACT_VERIFICATION_FILE,

        STANDINGS_FILE,
        STANDINGS_REPORT_FILE,

        UPCOMING_FIXTURES_FILE,

        STAGE7_8_FILE,
        STAGE7_9_FILE,

        SELECTED_MODEL_FILE,
    ]

    for path in required_files:

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
        STANDINGS_REPORT_FILE
    )

    stage7_8 = load_json(
        STAGE7_8_FILE
    )

    stage7_9 = load_json(
        STAGE7_9_FILE
    )

    # ========================================================
    # 2. Upstream foundation
    # ========================================================

    print(
        "\n2. UPSTREAM FOUNDATION"
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
        "Stage 8.1 status COMPLETE",
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
        contract_verification.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 7.8 PASS",
        stage7_8.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 7.9 PASS",
        stage7_9.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 7.9 COMPLETE",
        stage7_9.get(
            "stage_7_9_complete"
        )
        is True,
        failures,
    )

    check(
        "Production serving VERIFIED",
        stage7_9.get(
            "production_serving_stack"
        )
        == "VERIFIED",
        failures,
    )

    # ========================================================
    # 3. Stage 8.2 prior evidence
    # ========================================================

    print(
        "\n3. STAGE 8.2 PRIOR EVIDENCE"
    )

    sub_stages = report.get(
        "sub_stages",
        {}
    )

    check(
        "Report stage = 8.2",
        report.get(
            "stage"
        )
        == "8.2",
        failures,
    )

    for stage in (
        "8.2.1",
        "8.2.2",
        "8.2.3",
        "8.2.4",
    ):

        check(
            f"{stage} PASS",
            sub_stages.get(
                stage
            )
            == "PASS",
            failures,
        )

    check(
        "8.2.5 state valid",
        sub_stages.get(
            "8.2.5"
        )
        in {
            "PENDING",
            "PASS",
        },
        failures,
    )

    check(
        "Provider fetch VERIFIED",
        report.get(
            "provider_fetch"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Team normalization VERIFIED",
        report.get(
            "team_normalization"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Canonical standings VERIFIED",
        report.get(
            "canonical_standings"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Standings service VERIFIED",
        report.get(
            "standings_service"
        )
        == "VERIFIED",
        failures,
    )

    # ========================================================
    # 4. Canonical standings artifact
    # ========================================================

    print(
        "\n4. CANONICAL STANDINGS ARTIFACT"
    )

    try:

        fields, rows = (
            read_standings()
        )

        csv_read_ok = True

    except Exception:

        fields = []
        rows = []
        csv_read_ok = False

    check(
        "Canonical CSV readable",
        csv_read_ok,
        failures,
    )

    check(
        "Schema exact",
        fields
        == EXPECTED_FIELDS,
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
        "Provider IDs excluded",
        (
            "provider_team_id"
            not in fields
            and
            "provider_team_name"
            not in fields
        ),
        failures,
    )

    if rows:

        team_ids = [

            row[
                "team_id"
            ]

            for row in rows
        ]

        team_names = [

            row[
                "team_name"
            ]

            for row in rows
        ]

        positions = [

            row[
                "position"
            ]

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
            "20 unique FixtureIQ IDs",
            len(
                set(
                    team_ids
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
                    for name in team_names
                }
            )
            == 20,
            failures,
        )

        check(
            "Positions exactly 1..20",
            positions
            ==
            list(
                range(
                    1,
                    21,
                )
            ),
            failures,
        )

        check(
            "played = won + drawn + lost",
            all(
                row[
                    "played"
                ]
                ==
                (
                    row[
                        "won"
                    ]
                    +
                    row[
                        "drawn"
                    ]
                    +
                    row[
                        "lost"
                    ]
                )
                for row in rows
            ),
            failures,
        )

        check(
            "GD = GF - GA",
            all(
                row[
                    "goal_difference"
                ]
                ==
                (
                    row[
                        "goals_for"
                    ]
                    -
                    row[
                        "goals_against"
                    ]
                )
                for row in rows
            ),
            failures,
        )

        check(
            "points = 3W + D",
            all(
                row[
                    "points"
                ]
                ==
                (
                    3
                    *
                    row[
                        "won"
                    ]
                    +
                    row[
                        "drawn"
                    ]
                )
                for row in rows
            ),
            failures,
        )

    # ========================================================
    # 5. Artifact contract + hash
    # ========================================================

    print(
        "\n5. ARTIFACT CONTRACT & HASH"
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
            STANDINGS_REPORT_FILE
        ),
        failures,
    )

    check(
        "Stage 7 output writes prohibited",
        output_contract.get(
            "stage7_output_write_allowed"
        )
        is False,
        failures,
    )

    actual_standings_sha = (
        sha256_file(
            STANDINGS_FILE
        )
    )

    artifact_info = report.get(
        "current_standings",
        {}
    )

    check(
        "Standings hash matches report",
        artifact_info.get(
            "sha256"
        )
        == actual_standings_sha,
        failures,
    )

    check(
        "Report row count = 20",
        artifact_info.get(
            "row_count"
        )
        == 20,
        failures,
    )

    check(
        "Report schema exact",
        artifact_info.get(
            "columns"
        )
        == EXPECTED_FIELDS,
        failures,
    )

    check(
        "Namespace fixtureiq-team",
        artifact_info.get(
            "team_namespace"
        )
        == "fixtureiq-team",
        failures,
    )

    check(
        "Provider IDs absent from public CSV",
        artifact_info.get(
            "provider_ids_in_public_csv"
        )
        is False,
        failures,
    )

    # ========================================================
    # 6. Provider + provenance
    # ========================================================

    print(
        "\n6. PROVIDER & PROVENANCE"
    )

    provider_contract = (
        contract
        .get(
            "trusted_inputs",
            {}
        )
        .get(
            "live_context_provider",
            {}
        )
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
        "Provider matches locked contract",
        report.get(
            "provider"
        )
        ==
        provider_contract.get(
            "provider"
        ),
        failures,
    )

    check(
        "Competition Premier League",
        report.get(
            "competition"
        )
        == "Premier League",
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
        "Competition matches contract",
        report.get(
            "competition_code"
        )
        ==
        provider_contract.get(
            "competition_code"
        ),
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

    check(
        "Season matches contract",
        report.get(
            "season"
        )
        ==
        provider_contract.get(
            "configured_season"
        ),
        failures,
    )

    check(
        "generated_at_utc valid",
        parse_aware_timestamp(
            report.get(
                "generated_at_utc"
            )
        ),
        failures,
    )

    check(
        "source_as_of_utc valid",
        parse_aware_timestamp(
            report.get(
                "source_as_of_utc"
            )
        ),
        failures,
    )

    check(
        "Provider fetch timestamp valid",
        parse_aware_timestamp(
            report.get(
                "provider_fetch_timestamp_utc"
            )
        ),
        failures,
    )

    freshness = report.get(
        "freshness",
        {}
    )

    check(
        "Freshness DEPENDENCY_BASED",
        freshness.get(
            "mode"
        )
        == "DEPENDENCY_BASED",
        failures,
    )

    check(
        "Provider snapshot valid",
        freshness.get(
            "provider_snapshot_valid"
        )
        is True,
        failures,
    )

    check(
        "Dependency identity recorded",
        freshness.get(
            "dependency_identity_recorded"
        )
        is True,
        failures,
    )

    # ========================================================
    # 7. Team mapping + semantic registry
    # ========================================================

    print(
        "\n7. TEAM REGISTRY & NORMALIZATION"
    )

    try:

        fixture_registry = (
            load_fixture_registry()
        )

        report_registry = (
            load_report_registry(
                report
            )
        )

        registry_read_ok = True

    except Exception:

        fixture_registry = set()
        report_registry = set()
        registry_read_ok = False

    check(
        "Team registries readable",
        registry_read_ok,
        failures,
    )

    check(
        "FixtureIQ registry = 20",
        len(
            fixture_registry
        )
        == 20,
        failures,
    )

    check(
        "Report registry = 20",
        len(
            report_registry
        )
        == 20,
        failures,
    )

    check(
        "Registry identities match",
        fixture_registry
        == report_registry,
        failures,
    )

    if rows:

        csv_registry = {

            (
                row[
                    "team_id"
                ],
                row[
                    "team_name"
                ],
            )

            for row in rows
        }

        check(
            "CSV registry = report registry",
            csv_registry
            == report_registry,
            failures,
        )

    mappings = report.get(
        "team_mappings",
        []
    )

    provider_ids = [

        mapping.get(
            "provider_team_id"
        )

        for mapping in mappings

        if isinstance(
            mapping,
            dict,
        )
    ]

    check(
        "20 provider mappings",
        len(
            mappings
        )
        == 20,
        failures,
    )

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
        "Provider IDs not reused internally",
        all(
            str(
                mapping.get(
                    "provider_team_id"
                )
            )
            !=
            str(
                mapping.get(
                    "team_id"
                )
            )
            for mapping in mappings
            if isinstance(
                mapping,
                dict,
            )
        ),
        failures,
    )

    # ========================================================
    # 8. Dependency identity
    # ========================================================

    print(
        "\n8. DEPENDENCY IDENTITY"
    )

    dependencies = report.get(
        "dependency_identity",
        {}
    )

    contract_dependency = dependencies.get(
        "stage8_context_contract",
        {}
    )

    verification_dependency = dependencies.get(
        "stage8_context_contract_verification",
        {}
    )

    team_dependency = dependencies.get(
        "upcoming_fixtures_team_registry",
        {}
    )

    check(
        "Contract dependency hash valid",
        contract_dependency.get(
            "sha256"
        )
        ==
        sha256_file(
            CONTRACT_FILE
        ),
        failures,
    )

    check(
        "Contract verification hash valid",
        verification_dependency.get(
            "sha256"
        )
        ==
        sha256_file(
            CONTRACT_VERIFICATION_FILE
        ),
        failures,
    )

    check(
        "Team registry dependency usage valid",
        team_dependency.get(
            "usage"
        )
        ==
        "FIXTUREIQ_CANONICAL_TEAM_IDENTITY",
        failures,
    )

    # Raw upcoming-fixtures hash is intentionally NOT used
    # as the standings readiness decision.
    #
    # Stage 8.2.4 already verifies semantic team identity
    # so fixture scheduling refreshes do not falsely stale
    # the standings artifact.

    # ========================================================
    # 9. Real standings service
    # ========================================================

    print(
        "\n9. REAL STANDINGS SERVICE"
    )

    service = (
        StandingsService()
    )

    service_status = (
        service.get_status()
    )

    check(
        "Standings service READY",
        service_status.get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "Service stage 8.2.4",
        service_status.get(
            "stage"
        )
        == "8.2.4",
        failures,
    )

    check(
        "Service team count = 20",
        service_status.get(
            "team_count"
        )
        == 20,
        failures,
    )

    check(
        "Service dependencies valid",
        service_status.get(
            "dependencies_valid"
        )
        is True,
        failures,
    )

    check(
        "Service team registry valid",
        service_status.get(
            "team_registry_valid"
        )
        is True,
        failures,
    )

    check(
        "Service freshness DEPENDENCY_BASED",
        service_status.get(
            "freshness_mode"
        )
        == "DEPENDENCY_BASED",
        failures,
    )

    try:

        served_rows = (
            service.get_standings()
        )

        read_service_ok = True

    except Exception:

        served_rows = []
        read_service_ok = False

    check(
        "Standings read succeeds",
        read_service_ok,
        failures,
    )

    check(
        "Service returns 20 rows",
        len(
            served_rows
        )
        == 20,
        failures,
    )

    if rows and served_rows:

        check(
            "Service data matches canonical CSV",
            served_rows
            == rows,
            failures,
        )

        first_team = rows[
            0
        ][
            "team_name"
        ]

        exact_lookup = (
            service.get_team_standing(
                first_team
            )
        )

        case_lookup = (
            service.get_team_standing(
                first_team.upper()
            )
        )

        check(
            "Exact team lookup works",
            (
                exact_lookup
                is not None
                and
                exact_lookup.get(
                    "team_name"
                )
                == first_team
            ),
            failures,
        )

        check(
            "Case-insensitive exact lookup works",
            (
                case_lookup
                is not None
                and
                case_lookup.get(
                    "team_name"
                )
                == first_team
            ),
            failures,
        )

    check(
        "Unknown team returns None",
        service.get_team_standing(
            "Definitely Not An EPL Team"
        )
        is None,
        failures,
    )

    # ========================================================
    # 10. 8.2.4 freshness evidence
    # ========================================================

    print(
        "\n10. SERVICE FRESHNESS EVIDENCE"
    )

    service_freshness = report.get(
        "service_freshness",
        {}
    )

    check(
        "Service freshness VERIFIED",
        service_freshness.get(
            "status"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Service fail-closed",
        service_freshness.get(
            "fail_closed"
        )
        is True,
        failures,
    )

    check(
        "Artifact hash validation enabled",
        service_freshness.get(
            "artifact_hash_validation"
        )
        is True,
        failures,
    )

    check(
        "Contract hash validation enabled",
        service_freshness.get(
            "contract_hash_validation"
        )
        is True,
        failures,
    )

    check(
        "Semantic registry validation enabled",
        service_freshness.get(
            "semantic_team_registry_validation"
        )
        is True,
        failures,
    )

    check(
        "Fixture-only refresh does not invalidate",
        service_freshness.get(
            "fixture_only_refresh_invalidates_standings"
        )
        is False,
        failures,
    )

    check(
        "Team registry change invalidates",
        service_freshness.get(
            "team_registry_change_invalidates_standings"
        )
        is True,
        failures,
    )

    check(
        "Invalid provenance -> NOT_READY",
        service_freshness.get(
            "invalid_provenance_not_ready"
        )
        is True,
        failures,
    )

    check(
        "Missing artifact -> NOT_READY",
        service_freshness.get(
            "missing_artifact_not_ready"
        )
        is True,
        failures,
    )

    # ========================================================
    # 11. Locked model + safety boundary
    # ========================================================

    print(
        "\n11. MODEL & STAGE 7 SAFETY"
    )

    check(
        "Stage 8 context-only",
        contract.get(
            "context_only"
        )
        is True,
        failures,
    )

    locked_model = contract.get(
        "locked_model",
        {}
    )

    actual_model_sha = (
        sha256_file(
            SELECTED_MODEL_FILE
        )
    )

    check(
        "Locked model random_forest",
        locked_model.get(
            "model_id"
        )
        == "random_forest",
        failures,
    )

    check(
        "Locked feature count = 86",
        locked_model.get(
            "feature_count"
        )
        == 86,
        failures,
    )

    check(
        "Locked model SHA unchanged",
        locked_model.get(
            "sha256"
        )
        == actual_model_sha,
        failures,
    )

    model_protection = contract.get(
        "model_protection",
        {}
    )

    prohibited_flags = [

        "model_mutation_allowed",
        "retraining_allowed",
        "model_selection_allowed",
        "hyperparameter_tuning_allowed",
        "feature_schema_mutation_allowed",
        "prediction_mutation_allowed",
        "final_test_reuse_allowed",
        "standings_as_model_features_allowed",
        "form_as_model_features_allowed",
    ]

    for flag in prohibited_flags:

        check(
            f"{flag} = false",
            model_protection.get(
                flag
            )
            is False,
            failures,
        )

    safety = report.get(
        "safety",
        {}
    )

    check(
        "Report context-only",
        safety.get(
            "context_only"
        )
        is True,
        failures,
    )

    safety_false_flags = [

        "stage7_artifacts_modified",
        "model_loaded",
        "model_executed",
        "model_modified",
        "production_predictions_modified",
        "feature_schema_modified",
        "standings_used_as_model_features",
        "final_test_accessed",
    ]

    for flag in safety_false_flags:

        check(
            f"{flag} = false",
            safety.get(
                flag
            )
            is False,
            failures,
        )

    # ========================================================
    # 12. Final Stage 8.2 decision
    # ========================================================

    print(
        "\n12. STAGE 8.2.5 FINAL DECISION"
    )

    final_pass = (
        len(
            failures
        )
        == 0
    )

    if final_pass:

        # ----------------------------------------------------
        # Evidence hashes
        # ----------------------------------------------------

        evidence_sha256 = {

            "stage8_context_contract":
                sha256_file(
                    CONTRACT_FILE
                ),

            "stage8_context_contract_verification":
                sha256_file(
                    CONTRACT_VERIFICATION_FILE
                ),

            "current_standings":
                actual_standings_sha,

            "selected_model":
                actual_model_sha,

            "stage7_8_final_verification":
                sha256_file(
                    STAGE7_8_FILE
                ),

            "stage7_9_final_verification":
                sha256_file(
                    STAGE7_9_FILE
                ),

            # Snapshot observation only.
            # Not a standings freshness dependency.
            "upcoming_fixtures_snapshot":
                sha256_file(
                    UPCOMING_FIXTURES_FILE
                ),
        }

        # ----------------------------------------------------
        # Promote standings report to final PASS
        # ----------------------------------------------------

        final_report = load_json(
            STANDINGS_REPORT_FILE
        )

        final_sub_stages = dict(
            final_report.get(
                "sub_stages",
                {}
            )
        )

        final_sub_stages[
            "8.2.1"
        ] = "PASS"

        final_sub_stages[
            "8.2.2"
        ] = "PASS"

        final_sub_stages[
            "8.2.3"
        ] = "PASS"

        final_sub_stages[
            "8.2.4"
        ] = "PASS"

        final_sub_stages[
            "8.2.5"
        ] = "PASS"

        final_report[
            "sub_stages"
        ] = final_sub_stages

        final_report[
            "status"
        ] = "PASS"

        final_report[
            "stage_8_2_complete"
        ] = True

        final_report[
            "stage_8_2_status"
        ] = "COMPLETE"

        final_report[
            "live_epl_standings_layer"
        ] = "VERIFIED"

        final_report[
            "stage_8_2_5_verified_at_utc"
        ] = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        final_report[
            "final_gate"
        ] = {

            "status":
                "PASS",

            "stage":
                "8.2.5",

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                )
                .isoformat(),

            "canonical_team_count":
                20,

            "canonical_schema_verified":
                True,

            "provider_verified":
                True,

            "normalization_verified":
                True,

            "standings_service_ready":
                True,

            "dependency_freshness_verified":
                True,

            "fail_closed_verified":
                True,

            "locked_model_unchanged":
                True,

            "feature_count":
                86,

            "stage7_write_protection":
                True,

            "standings_context_only":
                True,
        }

        final_report[
            "evidence_sha256"
        ] = evidence_sha256

        save_json(
            STANDINGS_REPORT_FILE,
            final_report,
        )

        # ----------------------------------------------------
        # Persisted final state
        # ----------------------------------------------------

        persisted = load_json(
            STANDINGS_REPORT_FILE
        )

        check(
            "Final report status PASS persisted",
            persisted.get(
                "status"
            )
            == "PASS",
            failures,
        )

        check(
            "stage_8_2_complete persisted",
            persisted.get(
                "stage_8_2_complete"
            )
            is True,
            failures,
        )

        check(
            "Stage 8.2 COMPLETE persisted",
            persisted.get(
                "stage_8_2_status"
            )
            == "COMPLETE",
            failures,
        )

        check(
            "Live standings layer VERIFIED persisted",
            persisted.get(
                "live_epl_standings_layer"
            )
            == "VERIFIED",
            failures,
        )

        check(
            "8.2.5 PASS persisted",
            persisted.get(
                "sub_stages",
                {}
            ).get(
                "8.2.5"
            )
            == "PASS",
            failures,
        )

        # ----------------------------------------------------
        # Real service must still be READY after report update
        # ----------------------------------------------------

        final_service_status = (
            StandingsService()
            .get_status()
        )

        check(
            "Standings service remains READY",
            final_service_status.get(
                "status"
            )
            == "READY",
            failures,
        )

        final_pass = (
            len(
                failures
            )
            == 0
        )

    # ========================================================
    # Final output
    # ========================================================

    print(
        "\n" + "=" * 72
    )

    if final_pass:

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
            "STAGE 8.2.4: PASS"
        )

        print(
            "STAGE 8.2.5: PASS"
        )

        print()

        print(
            "STAGE 8.2: COMPLETE"
        )

        print(
            "LIVE EPL STANDINGS LAYER: VERIFIED"
        )

    else:

        print(
            "STAGE 8.2.5: FAIL"
        )

        print(
            "STAGE 8.2: INCOMPLETE"
        )

        print(
            "LIVE EPL STANDINGS LAYER: NOT VERIFIED"
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
        if final_pass
        else 1
    )


if __name__ == "__main__":

    main()
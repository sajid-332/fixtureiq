"""
FixtureIQ Stage 8.5.1 + 8.5.2

8.5.1
Upcoming Fixture Source & Temporal Gate

8.5.2
Home/Away Context Join + Initial Canonical Enriched Fixture Artifact

Creates:
- data/processed/context/enriched_upcoming_fixtures.csv
- data/processed/context/fixture_context_report.json

Important provenance rule:
The legacy Stage 7.8.2 production fixture-fetch report may not contain
a provider timestamp. In that case Stage 8 records the UTC time at which
the exact hashed upcoming_fixtures.csv artifact is observed and verified.

We do NOT:
- modify the locked Stage 7 report
- fabricate a historical provider timestamp
- use filesystem mtime as provenance
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

from backend.services.fixture_context_builder import (
    build_enriched_fixture_context,
)

from backend.services.team_context_service import (
    TeamContextService,
)


# ============================================================
# Paths
# ============================================================

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

UPCOMING_FIXTURES_FILE = (
    PRODUCTION_DIR
    / "upcoming_fixtures.csv"
)

FIXTURE_FETCH_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_fixture_fetch_report.json"
)

TEAM_CONTEXT_FILE = (
    CONTEXT_DIR
    / "team_context.csv"
)

TEAM_CONTEXT_REPORT_FILE = (
    CONTEXT_DIR
    / "team_context_report.json"
)

ENRICHED_FIXTURES_FILE = (
    CONTEXT_DIR
    / "enriched_upcoming_fixtures.csv"
)

FIXTURE_CONTEXT_REPORT_FILE = (
    CONTEXT_DIR
    / "fixture_context_report.json"
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


def parse_aware_timestamp(
    value,
    field_name: str,
) -> datetime:

    if not isinstance(
        value,
        str,
    ):

        raise RuntimeError(
            f"{field_name} missing."
        )

    text = value.strip()

    if not text:

        raise RuntimeError(
            f"{field_name} blank."
        )

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

    except ValueError as exc:

        raise RuntimeError(
            f"{field_name} invalid."
        ) from exc

    if parsed.tzinfo is None:

        raise RuntimeError(
            (
                f"{field_name} must be "
                "timezone-aware."
            )
        )

    return parsed.astimezone(
        timezone.utc
    )


# ============================================================
# Fixture snapshot provenance resolver
# ============================================================

def resolve_fixture_snapshot_timestamp(
    report: dict,
    *,
    observed_at_utc: datetime,
) -> tuple[
    str,
    datetime,
    bool,
]:
    """
    Resolve fixture snapshot provenance.

    Preferred:
    - use an explicit offset-aware timestamp from the
      existing production fixture-fetch report.

    Legacy fallback:
    - Stage 7.8.2 reports created before timestamp provenance
      may contain no timestamp at all.
    - In that case Stage 8 records the UTC time at which the
      exact hashed upcoming_fixtures.csv artifact is observed
      and validated.

    Returns:
        (
            provenance_field_or_mode,
            timestamp,
            provider_timestamp_available,
        )

    We do NOT:
    - modify the locked Stage 7 report
    - invent a historical provider-fetch timestamp
    - use filesystem mtime as provenance
    """

    if not isinstance(
        report,
        dict,
    ):

        raise RuntimeError(
            (
                "Fixture fetch report must "
                "be a JSON object."
            )
        )

    if (
        observed_at_utc.tzinfo
        is None
    ):

        raise RuntimeError(
            (
                "observed_at_utc must be "
                "timezone-aware."
            )
        )

    observed_at_utc = (
        observed_at_utc.astimezone(
            timezone.utc
        )
    )

    candidate_keys = [

        "fixture_snapshot_as_of_utc",
        "source_as_of_utc",
        "snapshot_as_of_utc",

        "fetched_at_utc",
        "fetch_completed_at_utc",
        "retrieved_at_utc",

        "generated_at_utc",
        "updated_at_utc",
        "last_updated_utc",
    ]

    discovered = []

    def walk(
        value,
        path: str,
    ) -> None:

        if isinstance(
            value,
            dict,
        ):

            for key, child in value.items():

                child_path = (
                    f"{path}.{key}"
                    if path
                    else key
                )

                if (
                    key in candidate_keys
                    and
                    isinstance(
                        child,
                        str,
                    )
                    and
                    child.strip()
                ):

                    try:

                        parsed = (
                            parse_aware_timestamp(
                                child,
                                child_path,
                            )
                        )

                        discovered.append(
                            {
                                "key":
                                    key,

                                "path":
                                    child_path,

                                "timestamp":
                                    parsed,
                            }
                        )

                    except RuntimeError:

                        # Malformed timestamp candidate:
                        # ignore it and continue searching.
                        pass

                walk(
                    child,
                    child_path,
                )

        elif isinstance(
            value,
            list,
        ):

            for index, child in enumerate(
                value
            ):

                walk(
                    child,
                    f"{path}[{index}]",
                )

    walk(
        report,
        "",
    )

    # ========================================================
    # Explicit provider/report timestamp available
    # ========================================================

    if discovered:

        priority = {

            key:
                index

            for index, key in enumerate(
                candidate_keys
            )
        }

        discovered.sort(
            key=lambda item: (
                priority[
                    item[
                        "key"
                    ]
                ],
                item[
                    "path"
                ].count(
                    "."
                ),
                item[
                    "path"
                ],
            )
        )

        selected = discovered[
            0
        ]

        return (
            selected[
                "path"
            ],
            selected[
                "timestamp"
            ],
            True,
        )

    # ========================================================
    # Legacy Stage 7.8.2 compatibility
    # ========================================================

    if (
        report.get(
            "stage"
        )
        == "7.8.2"
        and
        report.get(
            "component"
        )
        == "production_fixture_fetch"
        and
        report.get(
            "status"
        )
        == "PASS"
        and
        report.get(
            "provider"
        )
        == "football-data.org"
    ):

        return (
            (
                "STAGE8_VERIFIED_ARTIFACT_"
                "OBSERVED_AT_UTC"
            ),
            observed_at_utc,
            False,
        )

    raise RuntimeError(
        (
            "Could not resolve fixture snapshot provenance. "
            "No explicit timestamp exists and the source "
            "report is not a recognized verified legacy "
            "Stage 7.8.2 fixture-fetch report."
        )
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.5.1 + 8.5.2"
    )

    print(
        (
            "Upcoming Fixture Gate + "
            "Home/Away Context Enrichment"
        )
    )

    print("=" * 72)

    CONTEXT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # 1. Foundation
    # ========================================================

    print(
        "\n1. STAGE FOUNDATION"
    )

    contract = load_json(
        CONTRACT_FILE
    )

    contract_verification = load_json(
        CONTRACT_VERIFICATION_FILE
    )

    team_context_report = load_json(
        TEAM_CONTEXT_REPORT_FILE
    )

    fixture_fetch_report = load_json(
        FIXTURE_FETCH_REPORT_FILE
    )

    if (
        contract.get(
            "stage_8_1_complete"
        )
        is not True
    ):

        raise RuntimeError(
            "Stage 8.1 is not complete."
        )

    if (
        contract.get(
            "stage_8_1_status"
        )
        != "COMPLETE"
    ):

        raise RuntimeError(
            "Stage 8.1 status is not COMPLETE."
        )

    if (
        contract.get(
            "contract_status"
        )
        != "LOCKED_CONTEXT_CONTRACT"
    ):

        raise RuntimeError(
            (
                "Stage 8 context contract "
                "is not locked."
            )
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

    if (
        team_context_report.get(
            "stage_8_4_complete"
        )
        is not True
    ):

        raise RuntimeError(
            "Stage 8.4 is not complete."
        )

    if (
        team_context_report.get(
            "stage_8_4_status"
        )
        != "COMPLETE"
    ):

        raise RuntimeError(
            (
                "Stage 8.4 status is "
                "not COMPLETE."
            )
        )

    if (
        team_context_report.get(
            "unified_team_context_layer"
        )
        != "VERIFIED"
    ):

        raise RuntimeError(
            (
                "Unified Team Context Layer "
                "not VERIFIED."
            )
        )

    print(
        "Stage 8.1: COMPLETE"
    )

    print(
        "Stage 8.4: COMPLETE"
    )

    print(
        "Unified Team Context Layer: VERIFIED"
    )

    # ========================================================
    # 2. Locked output contract
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

    if (
        outputs.get(
            "enriched_upcoming_fixtures",
            {}
        ).get(
            "path"
        )
        !=
        relative_path(
            ENRICHED_FIXTURES_FILE
        )
    ):

        raise RuntimeError(
            (
                "enriched_upcoming_fixtures.csv "
                "path does not match locked "
                "Stage 8.1 contract."
            )
        )

    if (
        outputs.get(
            "fixture_context_report",
            {}
        ).get(
            "path"
        )
        !=
        relative_path(
            FIXTURE_CONTEXT_REPORT_FILE
        )
    ):

        raise RuntimeError(
            (
                "fixture_context_report.json "
                "path does not match locked "
                "Stage 8.1 contract."
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
        "Enriched fixture path: PASS"
    )

    print(
        "Fixture context report path: PASS"
    )

    print(
        "Stage 7 write protection: PASS"
    )

    # ========================================================
    # 3. Verified TeamContextService
    # ========================================================

    print(
        "\n3. VERIFIED TEAM CONTEXT SOURCE"
    )

    team_context_service = (
        TeamContextService()
    )

    context_status = (
        team_context_service.get_status()
    )

    if (
        context_status.get(
            "status"
        )
        != "READY"
    ):

        raise RuntimeError(
            (
                "TeamContextService NOT_READY: "
                f"{context_status.get('reason')}"
            )
        )

    if (
        context_status.get(
            "team_count"
        )
        != 20
    ):

        raise RuntimeError(
            (
                "TeamContextService did not "
                "return 20 canonical teams."
            )
        )

    print(
        "TeamContextService: READY"
    )

    print(
        "Canonical context teams:",
        context_status.get(
            "team_count"
        ),
    )

    # ========================================================
    # 4. Resolve source provenance
    # ========================================================

    print(
        "\n4. SOURCE PROVENANCE"
    )

    fixture_artifact_observed_at = (
        datetime.now(
            timezone.utc
        )
    )

    (
        fixture_snapshot_field,
        fixture_snapshot_as_of,
        fixture_provider_timestamp_available,
    ) = resolve_fixture_snapshot_timestamp(
        fixture_fetch_report,
        observed_at_utc=
            fixture_artifact_observed_at,
    )

    context_generated_at = (
        parse_aware_timestamp(
            team_context_report.get(
                "generated_at_utc"
            ),
            "team_context.generated_at_utc",
        )
    )

    context_source_as_of = (
        parse_aware_timestamp(
            team_context_report.get(
                "source_as_of_utc"
            ),
            "team_context.source_as_of_utc",
        )
    )

    form_history_cutoff = (
        parse_aware_timestamp(
            team_context_report.get(
                "form_history_cutoff_utc"
            ),
            (
                "team_context."
                "form_history_cutoff_utc"
            ),
        )
    )

    print(
        "Fixture snapshot timestamp field:",
        fixture_snapshot_field,
    )

    print(
        "Fixture snapshot as-of:",
        fixture_snapshot_as_of.isoformat(),
    )

    print(
        "Provider snapshot timestamp available:",
        fixture_provider_timestamp_available,
    )

    if not fixture_provider_timestamp_available:

        print(
            (
                "Legacy Stage 7.8.2 report has no "
                "provider timestamp; using Stage 8 "
                "verified-artifact observation time."
            )
        )

    print(
        "Team context source as-of:",
        context_source_as_of.isoformat(),
    )

    print(
        "Form history cutoff:",
        form_history_cutoff.isoformat(),
    )

    # ========================================================
    # 5. Stage 8.5.1 + 8.5.2
    # ========================================================

    print(
        "\n5. BUILD ENRICHED FIXTURE CONTEXT"
    )

    build_now = datetime.now(
        timezone.utc
    )

    snapshot = (
        build_enriched_fixture_context(

            upcoming_fixtures_file=
                UPCOMING_FIXTURES_FILE,

            team_context_service=
                team_context_service,

            form_history_cutoff_utc=
                form_history_cutoff.isoformat(),

            context_generated_at_utc=
                context_generated_at.isoformat(),

            now_utc=
                build_now,
        )
    )

    print(
        "Fixture source rows:",
        snapshot[
            "source_row_count"
        ],
    )

    print(
        "Fixture source columns:",
        snapshot[
            "source_column_count"
        ],
    )

    print(
        "Date field:",
        snapshot[
            "date_field"
        ],
    )

    print(
        "Context fields / team:",
        snapshot[
            "context_fields_per_team"
        ],
    )

    print(
        "Context fields appended:",
        snapshot[
            "context_fields_appended"
        ],
    )

    print(
        "Enriched columns:",
        snapshot[
            "enriched_column_count"
        ],
    )

    print(
        "Fixture teams represented:",
        snapshot[
            "fixture_team_count"
        ],
    )

    print(
        "Earliest kickoff:",
        snapshot[
            "earliest_fixture_kickoff_utc"
        ],
    )

    print(
        "Latest kickoff:",
        snapshot[
            "latest_fixture_kickoff_utc"
        ],
    )

    # ========================================================
    # 6. Write enriched fixture CSV
    # ========================================================

    print(
        "\n6. WRITE ENRICHED UPCOMING FIXTURES"
    )

    with ENRICHED_FIXTURES_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=snapshot[
                "enriched_fields"
            ],
        )

        writer.writeheader()

        writer.writerows(
            snapshot[
                "enriched_rows"
            ]
        )

    enriched_sha = (
        sha256_file(
            ENRICHED_FIXTURES_FILE
        )
    )

    print(
        ENRICHED_FIXTURES_FILE
    )

    print(
        "Rows:",
        snapshot[
            "enriched_row_count"
        ],
    )

    print(
        "Columns:",
        snapshot[
            "enriched_column_count"
        ],
    )

    print(
        "SHA256:",
        enriched_sha,
    )

    # ========================================================
    # 7. Initial Stage 8.5 report
    # ========================================================

    print(
        "\n7. BUILD FIXTURE CONTEXT REPORT"
    )

    generated_at = datetime.now(
        timezone.utc
    )

    fixture_source_sha = (
        sha256_file(
            UPCOMING_FIXTURES_FILE
        )
    )

    fixture_fetch_report_sha = (
        sha256_file(
            FIXTURE_FETCH_REPORT_FILE
        )
    )

    team_context_sha = (
        sha256_file(
            TEAM_CONTEXT_FILE
        )
    )

    team_context_report_sha = (
        sha256_file(
            TEAM_CONTEXT_REPORT_FILE
        )
    )

    report = {

        "stage":
            "8.5",

        "status":
            "PARTIAL_PASS",

        "stage_8_5_complete":
            False,

        "sub_stages": {

            "8.5.1":
                "PASS",

            "8.5.2":
                "PASS",

            "8.5.3":
                "PENDING",

            "8.5.4":
                "PENDING",

            "8.5.5":
                "PENDING",
        },

        "upcoming_fixture_source_gate":
            "VERIFIED",

        "home_away_context_join":
            "VERIFIED",

        "generated_at_utc":
            generated_at.isoformat(),

        # ----------------------------------------------------
        # Fixture provenance
        # ----------------------------------------------------

        "fixture_snapshot_as_of_utc":
            fixture_snapshot_as_of.isoformat(),

        "fixture_snapshot_source_field":
            fixture_snapshot_field,

        "fixture_provider_timestamp_available":
            fixture_provider_timestamp_available,

        "fixture_snapshot_provenance_mode":
            (
                "PROVIDER_REPORTED_TIMESTAMP"
                if fixture_provider_timestamp_available
                else
                "STAGE8_VERIFIED_ARTIFACT_OBSERVATION"
            ),

        "legacy_fixture_report_timestamp_missing":
            not fixture_provider_timestamp_available,

        "fixture_artifact_observed_at_utc":
            fixture_artifact_observed_at.isoformat(),

        # ----------------------------------------------------
        # Team-context provenance
        # ----------------------------------------------------

        "team_context_source_as_of_utc":
            context_source_as_of.isoformat(),

        "team_context_generated_at_utc":
            context_generated_at.isoformat(),

        "form_history_cutoff_utc":
            form_history_cutoff.isoformat(),

        # ----------------------------------------------------
        # Fixture range
        # ----------------------------------------------------

        "earliest_fixture_kickoff_utc":
            snapshot[
                "earliest_fixture_kickoff_utc"
            ],

        "latest_fixture_kickoff_utc":
            snapshot[
                "latest_fixture_kickoff_utc"
            ],

        "competition":
            "Premier League",

        "competition_code":
            "PL",

        "season":
            2026,

        "team_namespace":
            "fixtureiq-team",

        "fixture_count":
            snapshot[
                "enriched_row_count"
            ],

        "context_team_count":
            context_status.get(
                "team_count"
            ),

        # ====================================================
        # Source fixture description
        # ====================================================

        "fixture_source": {

            "path":
                relative_path(
                    UPCOMING_FIXTURES_FILE
                ),

            "sha256":
                fixture_source_sha,

            "row_count":
                snapshot[
                    "source_row_count"
                ],

            "column_count":
                snapshot[
                    "source_column_count"
                ],

            "columns":
                snapshot[
                    "source_fields"
                ],

            "date_field":
                snapshot[
                    "date_field"
                ],

            "fixture_ids_unique":
                True,

            "provider_fixture_ids_unique_when_present":
                True,

            "provider":
                fixture_fetch_report.get(
                    "provider"
                ),

            "source_report_stage":
                fixture_fetch_report.get(
                    "stage"
                ),

            "source_report_status":
                fixture_fetch_report.get(
                    "status"
                ),

            "source_report_has_provider_timestamp":
                fixture_provider_timestamp_available,
        },

        # ====================================================
        # Temporal gate
        # ====================================================

        "temporal_gate": {

            "all_fixtures_future":
                True,

            "form_history_cutoff_before_all_fixtures":
                True,

            "team_context_generated_before_all_fixtures":
                True,

            "earliest_fixture_kickoff_utc":
                snapshot[
                    "earliest_fixture_kickoff_utc"
                ],

            "latest_fixture_kickoff_utc":
                snapshot[
                    "latest_fixture_kickoff_utc"
                ],

            "build_now_utc":
                snapshot[
                    "build_now_utc"
                ],

            "fixture_snapshot_as_of_utc":
                fixture_snapshot_as_of.isoformat(),

            "fixture_snapshot_provenance_mode":
                (
                    "PROVIDER_REPORTED_TIMESTAMP"
                    if fixture_provider_timestamp_available
                    else
                    "STAGE8_VERIFIED_ARTIFACT_OBSERVATION"
                ),
        },

        # ====================================================
        # Context join contract
        # ====================================================

        "context_join": {

            "type":
                "STRICT_CANONICAL_IDENTITY_JOIN",

            "team_id_match_required":
                True,

            "team_name_match_required":
                True,

            "fuzzy_matching_allowed":
                False,

            "missing_context_fallback_allowed":
                False,

            "home_context_match":
                True,

            "away_context_match":
                True,

            "context_fields_per_team":
                snapshot[
                    "context_fields_per_team"
                ],

            "home_context_fields_appended":
                36,

            "away_context_fields_appended":
                36,

            "total_context_fields_appended":
                snapshot[
                    "context_fields_appended"
                ],

            "source_rows":
                snapshot[
                    "source_row_count"
                ],

            "output_rows":
                snapshot[
                    "enriched_row_count"
                ],

            "row_count_preserved":
                True,
        },

        # ====================================================
        # Shared snapshot / leakage policy
        # ====================================================

        "snapshot_policy": {

            "shared_context_snapshot":
                True,

            "future_fixture_state_propagation":
                False,

            "future_fixtures_update_each_other":
                False,

            "pre_kickoff_context_only":
                True,
        },

        # ====================================================
        # Canonical output artifact
        # ====================================================

        "enriched_upcoming_fixtures": {

            "path":
                relative_path(
                    ENRICHED_FIXTURES_FILE
                ),

            "sha256":
                enriched_sha,

            "row_count":
                snapshot[
                    "enriched_row_count"
                ],

            "column_count":
                snapshot[
                    "enriched_column_count"
                ],

            "source_column_count":
                snapshot[
                    "source_column_count"
                ],

            "context_column_count":
                snapshot[
                    "context_fields_appended"
                ],

            "columns":
                snapshot[
                    "enriched_fields"
                ],

            "sort_order":
                snapshot[
                    "sort_order"
                ],

            "team_namespace":
                "fixtureiq-team",
        },

        # ====================================================
        # Full dependency identity
        # ====================================================

        "dependency_identity": {

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

            "upcoming_fixtures": {

                "path":
                    relative_path(
                        UPCOMING_FIXTURES_FILE
                    ),

                "sha256":
                    fixture_source_sha,

                "usage":
                    "UPCOMING_FIXTURE_SOURCE",
            },

            "production_fixture_fetch_report": {

                "path":
                    relative_path(
                        FIXTURE_FETCH_REPORT_FILE
                    ),

                "sha256":
                    fixture_fetch_report_sha,

                "usage":
                    "FIXTURE_SOURCE_PROVENANCE",

                "legacy_timestamp_missing":
                    not fixture_provider_timestamp_available,
            },

            "team_context": {

                "path":
                    relative_path(
                        TEAM_CONTEXT_FILE
                    ),

                "sha256":
                    team_context_sha,

                "usage":
                    "FULL_HOME_AWAY_CONTEXT",
            },

            "team_context_report": {

                "path":
                    relative_path(
                        TEAM_CONTEXT_REPORT_FILE
                    ),

                "sha256":
                    team_context_report_sha,

                "usage":
                    "VERIFIED_TEAM_CONTEXT_PROVENANCE",
            },
        },

        # ====================================================
        # Freshness policy
        # ====================================================

        "freshness": {

            "mode":
                "DEPENDENCY_BASED_PLUS_TEMPORAL_BOUNDARY",

            "upcoming_fixture_change_invalidates_context":
                True,

            "fixture_fetch_report_change_invalidates_context":
                True,

            "team_context_change_invalidates_context":
                True,

            "team_context_report_change_invalidates_context":
                True,

            "fixture_kickoff_reached_invalidates_context":
                True,

            "legacy_fixture_timestamp_absence_tolerated":
                True,

            "legacy_fixture_timestamp_fallback_mode":
                (
                    "STAGE8_VERIFIED_ARTIFACT_OBSERVATION"
                ),

            "stale_fallback_allowed":
                False,

            "partial_unverified_output_allowed":
                False,

            "fail_closed":
                True,
        },

        # ====================================================
        # Safety
        # ====================================================

        "safety": {

            "context_only":
                True,

            "stage7_artifacts_modified":
                False,

            "legacy_stage7_report_modified":
                False,

            "provider_timestamp_fabricated":
                False,

            "filesystem_mtime_used_as_provenance":
                False,

            "provider_fetch_performed":
                False,

            "fixture_source_modified":
                False,

            "team_context_modified":
                False,

            "future_results_used":
                False,

            "future_fixture_state_propagation":
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

            "fixture_context_used_as_model_features":
                False,

            "final_test_accessed":
                False,
        },

        "failures":
            [],
    }

    save_json(
        FIXTURE_CONTEXT_REPORT_FILE,
        report,
    )

    print(
        FIXTURE_CONTEXT_REPORT_FILE
    )

    print(
        (
            "Fixture provenance mode:"
        ),
        report[
            "fixture_snapshot_provenance_mode"
        ],
    )

    # ========================================================
    # Final
    # ========================================================

    print(
        "\n" + "=" * 72
    )

    print(
        "STAGE 8.5.1: PASS"
    )

    print(
        (
            "UPCOMING FIXTURE SOURCE & "
            "TEMPORAL GATE: VERIFIED"
        )
    )

    print(
        "STAGE 8.5.2: BUILT"
    )

    print(
        "HOME/AWAY FIXTURE CONTEXT: CREATED"
    )

    print(
        "STAGE 8.5: IN PROGRESS"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
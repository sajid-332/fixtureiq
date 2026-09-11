"""
FixtureIQ Stage 8.4.1 + 8.4.2

8.4.1 - Upstream Context Readiness Gate
8.4.2 - Unified Team Context Builder

Creates:
data/processed/context/team_context.csv
data/processed/context/team_context_report.json
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
# FixtureIQ imports
# ============================================================

from backend.services.team_context_builder import (
    TEAM_CONTEXT_FIELDS,
    build_team_context,
)

from backend.services.standings_service import (
    StandingsService,
)

from backend.services.team_form_service import (
    TeamFormService,
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

STANDINGS_FILE = (
    CONTEXT_DIR
    / "current_standings.csv"
)

STANDINGS_REPORT_FILE = (
    CONTEXT_DIR
    / "standings_report.json"
)

TEAM_FORM_FILE = (
    CONTEXT_DIR
    / "current_team_form.csv"
)

TEAM_FORM_REPORT_FILE = (
    CONTEXT_DIR
    / "team_form_report.json"
)

TEAM_CONTEXT_FILE = (
    CONTEXT_DIR
    / "team_context.csv"
)

TEAM_CONTEXT_REPORT_FILE = (
    CONTEXT_DIR
    / "team_context_report.json"
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
            f"{field_name} missing or invalid."
        )

    text = value.strip()

    if not text:

        raise RuntimeError(
            f"{field_name} missing or blank."
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
            f"{field_name} is not valid ISO datetime."
        ) from exc

    if parsed.tzinfo is None:

        raise RuntimeError(
            f"{field_name} must be timezone-aware."
        )

    return parsed


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.4.1 + 8.4.2"
    )

    print(
        "Upstream Readiness + Unified Team Context Builder"
    )

    print("=" * 72)

    CONTEXT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # 1. Required foundation
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

    standings_report = load_json(
        STANDINGS_REPORT_FILE
    )

    form_report = load_json(
        TEAM_FORM_REPORT_FILE
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
            "Stage 8 context contract is not locked."
        )

    if (
        contract_verification.get(
            "status"
        )
        != "PASS"
    ):

        raise RuntimeError(
            "Stage 8.1 verification is not PASS."
        )

    if (
        standings_report.get(
            "stage_8_2_complete"
        )
        is not True
    ):

        raise RuntimeError(
            "Stage 8.2 is not complete."
        )

    if (
        standings_report.get(
            "stage_8_2_status"
        )
        != "COMPLETE"
    ):

        raise RuntimeError(
            "Stage 8.2 status is not COMPLETE."
        )

    if (
        standings_report.get(
            "live_epl_standings_layer"
        )
        != "VERIFIED"
    ):

        raise RuntimeError(
            "Stage 8.2 standings layer not VERIFIED."
        )

    if (
        form_report.get(
            "stage_8_3_complete"
        )
        is not True
    ):

        raise RuntimeError(
            "Stage 8.3 is not complete."
        )

    if (
        form_report.get(
            "stage_8_3_status"
        )
        != "COMPLETE"
    ):

        raise RuntimeError(
            "Stage 8.3 status is not COMPLETE."
        )

    if (
        form_report.get(
            "current_team_form_layer"
        )
        != "VERIFIED"
    ):

        raise RuntimeError(
            "Stage 8.3 form layer not VERIFIED."
        )

    print(
        "Stage 8.1: COMPLETE"
    )

    print(
        "Stage 8.2: COMPLETE"
    )

    print(
        "Stage 8.3: COMPLETE"
    )

    # ========================================================
    # 2. Locked output contract
    # ========================================================

    print(
        "\n2. OUTPUT CONTRACT"
    )

    output_contract = (
        contract.get(
            "output_artifact_contract",
            {}
        )
    )

    outputs = output_contract.get(
        "outputs",
        {}
    )

    expected_context_path = (
        relative_path(
            TEAM_CONTEXT_FILE
        )
    )

    expected_report_path = (
        relative_path(
            TEAM_CONTEXT_REPORT_FILE
        )
    )

    if (
        outputs.get(
            "team_context",
            {}
        ).get(
            "path"
        )
        != expected_context_path
    ):

        raise RuntimeError(
            (
                "team_context.csv path does not match "
                "locked Stage 8.1 output contract."
            )
        )

    if (
        outputs.get(
            "team_context_report",
            {}
        ).get(
            "path"
        )
        != expected_report_path
    ):

        raise RuntimeError(
            (
                "team_context_report.json path does not "
                "match locked Stage 8.1 output contract."
            )
        )

    if (
        output_contract.get(
            "stage7_output_write_allowed"
        )
        is not False
    ):

        raise RuntimeError(
            "Stage 7 write protection is not active."
        )

    print(
        "team_context.csv path: PASS"
    )

    print(
        "team_context_report.json path: PASS"
    )

    print(
        "Stage 7 write protection: PASS"
    )

    # ========================================================
    # 3. Stage 8.4.1 service readiness
    # ========================================================

    print(
        "\n3. STAGE 8.4.1 - UPSTREAM READINESS"
    )

    standings_service = (
        StandingsService()
    )

    form_service = (
        TeamFormService()
    )

    standings_status = (
        standings_service.get_status()
    )

    form_status = (
        form_service.get_status()
    )

    if (
        standings_status.get(
            "status"
        )
        != "READY"
    ):

        raise RuntimeError(
            (
                "StandingsService NOT_READY: "
                f"{standings_status.get('reason')}"
            )
        )

    if (
        form_status.get(
            "status"
        )
        != "READY"
    ):

        raise RuntimeError(
            (
                "TeamFormService NOT_READY: "
                f"{form_status.get('reason')}"
            )
        )

    print(
        "StandingsService: READY"
    )

    print(
        "TeamFormService: READY"
    )

    # ========================================================
    # 4. Build strict unified snapshot
    # ========================================================

    print(
        "\n4. STAGE 8.4.2 - BUILD UNIFIED CONTEXT"
    )

    snapshot = build_team_context(

        standings_service=
            standings_service,

        team_form_service=
            form_service,
    )

    rows = snapshot[
        "rows"
    ]

    if (
        snapshot.get(
            "identity_match"
        )
        is not True
    ):

        raise RuntimeError(
            "Standings/form identities do not match."
        )

    if (
        snapshot.get(
            "join_cardinality"
        )
        != "ONE_TO_ONE"
    ):

        raise RuntimeError(
            "Unified join is not one-to-one."
        )

    if len(
        rows
    ) != 20:

        raise RuntimeError(
            (
                "Unified context must contain exactly "
                f"20 teams, found {len(rows)}."
            )
        )

    print(
        "Standings/form identity match: PASS"
    )

    print(
        "Join cardinality ONE_TO_ONE: PASS"
    )

    print(
        f"Unified teams: {len(rows)}"
    )

    # ========================================================
    # 5. Write canonical CSV
    # ========================================================

    print(
        "\n5. WRITE TEAM CONTEXT"
    )

    with TEAM_CONTEXT_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=TEAM_CONTEXT_FIELDS,
        )

        writer.writeheader()

        writer.writerows(
            rows
        )

    context_sha = (
        sha256_file(
            TEAM_CONTEXT_FILE
        )
    )

    print(
        TEAM_CONTEXT_FILE
    )

    print(
        f"Rows: {len(rows)}"
    )

    print(
        f"Columns: {len(TEAM_CONTEXT_FIELDS)}"
    )

    print(
        f"SHA256: {context_sha}"
    )

    # ========================================================
    # 6. Provenance
    # ========================================================

    print(
        "\n6. PROVENANCE"
    )

    standings_source = (
        parse_aware_timestamp(
            standings_report.get(
                "source_as_of_utc"
            ),
            "standings_source_as_of_utc",
        )
    )

    form_source = (
        parse_aware_timestamp(
            form_report.get(
                "source_as_of_utc"
            ),
            "form_source_as_of_utc",
        )
    )

    form_history_cutoff = (
        parse_aware_timestamp(
            form_report.get(
                "history_cutoff_utc"
            ),
            "form_history_cutoff_utc",
        )
    )

    unified_source_as_of = max(
        standings_source,
        form_source,
    )

    generated_at = (
        datetime.now(
            timezone.utc
        )
    )

    print(
        "Standings source as-of:",
        standings_source.isoformat(),
    )

    print(
        "Form source as-of:",
        form_source.isoformat(),
    )

    print(
        "Form history cutoff:",
        form_history_cutoff.isoformat(),
    )

    # ========================================================
    # 7. Build report
    # ========================================================

    print(
        "\n7. BUILD TEAM CONTEXT REPORT"
    )

    report = {

        "stage":
            "8.4",

        "status":
            "PARTIAL_PASS",

        "stage_8_4_complete":
            False,

        "sub_stages": {

            "8.4.1":
                "PASS",

            "8.4.2":
                "PASS",

            "8.4.3":
                "PENDING",

            "8.4.4":
                "PENDING",

            "8.4.5":
                "PENDING",
        },

        "upstream_context_readiness":
            "VERIFIED",

        "unified_team_context_builder":
            "VERIFIED",

        "generated_at_utc":
            generated_at.isoformat(),

        "source_as_of_utc":
            unified_source_as_of.isoformat(),

        "standings_source_as_of_utc":
            standings_source.isoformat(),

        "form_source_as_of_utc":
            form_source.isoformat(),

        "form_history_cutoff_utc":
            form_history_cutoff.isoformat(),

        "competition":
            "Premier League",

        "competition_code":
            "PL",

        "season":
            2026,

        "team_namespace":
            "fixtureiq-team",

        "team_count":
            20,

        "join": {

            "type":
                "ONE_TO_ONE",

            "key":
                [
                    "team_id",
                    "team_name",
                ],

            "standings_rows":
                20,

            "form_rows":
                20,

            "output_rows":
                20,

            "identity_match":
                True,

            "missing_standings_teams":
                0,

            "missing_form_teams":
                0,

            "duplicate_output_teams":
                0,
        },

        "team_context": {

            "path":
                relative_path(
                    TEAM_CONTEXT_FILE
                ),

            "sha256":
                context_sha,

            "row_count":
                20,

            "column_count":
                len(
                    TEAM_CONTEXT_FIELDS
                ),

            "columns":
                TEAM_CONTEXT_FIELDS,

            "sort_order":
                "team_name ASC",

            "team_namespace":
                "fixtureiq-team",
        },

        # Full artifact dependencies are deliberate.
        # Any upstream standings/form content change must
        # invalidate the unified team context.
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

            "current_standings": {

                "path":
                    relative_path(
                        STANDINGS_FILE
                    ),

                "sha256":
                    sha256_file(
                        STANDINGS_FILE
                    ),

                "usage":
                    "FULL_STANDINGS_CONTEXT",
            },

            "standings_report": {

                "path":
                    relative_path(
                        STANDINGS_REPORT_FILE
                    ),

                "sha256":
                    sha256_file(
                        STANDINGS_REPORT_FILE
                    ),

                "usage":
                    "VERIFIED_STANDINGS_PROVENANCE",
            },

            "current_team_form": {

                "path":
                    relative_path(
                        TEAM_FORM_FILE
                    ),

                "sha256":
                    sha256_file(
                        TEAM_FORM_FILE
                    ),

                "usage":
                    "FULL_CURRENT_FORM_CONTEXT",
            },

            "team_form_report": {

                "path":
                    relative_path(
                        TEAM_FORM_REPORT_FILE
                    ),

                "sha256":
                    sha256_file(
                        TEAM_FORM_REPORT_FILE
                    ),

                "usage":
                    "VERIFIED_FORM_PROVENANCE",
            },
        },

        "freshness": {

            "mode":
                "DEPENDENCY_BASED",

            "current_standings_change_invalidates_context":
                True,

            "standings_report_change_invalidates_context":
                True,

            "current_team_form_change_invalidates_context":
                True,

            "team_form_report_change_invalidates_context":
                True,

            "stale_fallback_allowed":
                False,

            "partial_unverified_output_allowed":
                False,

            "fail_closed":
                True,
        },

        "safety": {

            "context_only":
                True,

            "stage7_artifacts_modified":
                False,

            "provider_fetch_performed":
                False,

            "standings_rebuilt":
                False,

            "team_form_rebuilt":
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

            "team_context_used_as_model_features":
                False,

            "final_test_accessed":
                False,
        },

        "failures":
            [],
    }

    save_json(
        TEAM_CONTEXT_REPORT_FILE,
        report,
    )

    print(
        TEAM_CONTEXT_REPORT_FILE
    )

    # ========================================================
    # Final
    # ========================================================

    print(
        "\n" + "=" * 72
    )

    print(
        "STAGE 8.4.1: PASS"
    )

    print(
        "UPSTREAM CONTEXT READINESS: VERIFIED"
    )

    print(
        "STAGE 8.4.2: BUILT"
    )

    print(
        "UNIFIED TEAM CONTEXT: CREATED"
    )

    print(
        "STAGE 8.4: IN PROGRESS"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
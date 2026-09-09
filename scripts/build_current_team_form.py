"""
FixtureIQ Stage 8.3.3
Build canonical current_team_form.csv.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


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


from backend.services.team_form_canonical_builder import (
    FORM_FIELDS,
    build_current_team_form,
)

from backend.services.team_form_engine import (
    TeamFormEngine,
    sha256_file,
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

HISTORY_FILE = (
    PRODUCTION_DIR
    / "production_history.csv"
)

HISTORY_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_history_report.json"
)

TEAM_FORM_REPORT_FILE = (
    CONTEXT_DIR
    / "team_form_report.json"
)

OUTPUT_FILE = (
    CONTEXT_DIR
    / "current_team_form.csv"
)


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


def registry_sha256(
    rows: list[dict],
) -> str:

    lines = sorted(

        (
            f"{row['team_id']}|"
            f"{row['team_name']}"
        )

        for row in rows
    )

    payload = (
        "\n".join(
            lines
        )
        + "\n"
    ).encode(
        "utf-8"
    )

    return hashlib.sha256(
        payload
    ).hexdigest()


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.3.3"
    )

    print(
        "Home/Away Form + Canonical Team Form Builder"
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
            "live_epl_standings_layer"
        )
        != "VERIFIED"
    ):

        raise RuntimeError(
            "Stage 8.2 standings layer is not VERIFIED."
        )

    sub_stages = form_report.get(
        "sub_stages",
        {}
    )

    if (
        sub_stages.get(
            "8.3.1"
        )
        != "PASS"
    ):

        raise RuntimeError(
            "Stage 8.3.1 is not PASS."
        )

    if (
        sub_stages.get(
            "8.3.2"
        )
        != "PASS"
    ):

        raise RuntimeError(
            "Stage 8.3.2 is not PASS."
        )

    print(
        "Stage 8.1: PASS"
    )

    print(
        "Stage 8.2: PASS"
    )

    print(
        "Stage 8.3.1: PASS"
    )

    print(
        "Stage 8.3.2: PASS"
    )

    # ========================================================
    # 2. Ensure 8.3.1/8.3.2 source did not change
    # ========================================================

    print(
        "\n2. SOURCE DEPENDENCY CHECK"
    )

    dependencies = (
        form_report.get(
            "dependency_identity",
            {}
        )
    )

    history_dependency = (
        dependencies.get(
            "production_history",
            {}
        )
    )

    history_report_dependency = (
        dependencies.get(
            "production_history_report",
            {}
        )
    )

    current_history_sha = (
        sha256_file(
            HISTORY_FILE
        )
    )

    current_history_report_sha = (
        sha256_file(
            HISTORY_REPORT_FILE
        )
    )

    if (
        history_dependency.get(
            "sha256"
        )
        != current_history_sha
    ):

        raise RuntimeError(
            (
                "production_history.csv changed after "
                "8.3.1/8.3.2 verification. "
                "Rerun Stage 8.3.1 + 8.3.2."
            )
        )

    if (
        history_report_dependency.get(
            "sha256"
        )
        != current_history_report_sha
    ):

        raise RuntimeError(
            (
                "production_history_report.json changed "
                "after 8.3.1/8.3.2 verification. "
                "Rerun Stage 8.3.1 + 8.3.2."
            )
        )

    print(
        "Production history unchanged: PASS"
    )

    print(
        "History report unchanged: PASS"
    )

    # ========================================================
    # 3. Locked output contract
    # ========================================================

    print(
        "\n3. OUTPUT CONTRACT"
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

    if (
        outputs.get(
            "current_team_form",
            {}
        ).get(
            "path"
        )
        !=
        relative_path(
            OUTPUT_FILE
        )
    ):

        raise RuntimeError(
            "current_team_form.csv path contract mismatch."
        )

    if (
        outputs.get(
            "team_form_report",
            {}
        ).get(
            "path"
        )
        !=
        relative_path(
            TEAM_FORM_REPORT_FILE
        )
    ):

        raise RuntimeError(
            "team_form_report.json path contract mismatch."
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
        "current_team_form.csv path: PASS"
    )

    print(
        "team_form_report.json path: PASS"
    )

    print(
        "Stage 7 write protection: PASS"
    )

    # ========================================================
    # 4. Build canonical snapshot
    # ========================================================

    print(
        "\n4. BUILD CURRENT TEAM FORM"
    )

    engine = TeamFormEngine(
        season=2026,
        window=5,
    )

    snapshot = (
        build_current_team_form(
            engine
        )
    )

    rows = snapshot[
        "rows"
    ]

    gated = snapshot[
        "gated_source"
    ]

    evidence = snapshot[
        "evidence"
    ]

    print(
        f"Canonical teams: {len(rows)}"
    )

    print(
        "Completed current-season matches: "
        f"{gated['completed_current_season_matches']}"
    )

    print(
        f"History cutoff: {gated['history_cutoff_utc']}"
    )

    # ========================================================
    # 5. Write canonical CSV
    # ========================================================

    print(
        "\n5. WRITE CURRENT TEAM FORM"
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FORM_FIELDS,
        )

        writer.writeheader()

        writer.writerows(
            rows
        )

    form_sha = (
        sha256_file(
            OUTPUT_FILE
        )
    )

    print(
        OUTPUT_FILE
    )

    print(
        f"Rows: {len(rows)}"
    )

    print(
        f"Columns: {len(FORM_FIELDS)}"
    )

    print(
        f"SHA256: {form_sha}"
    )

    # ========================================================
    # 6. Update report
    # ========================================================

    print(
        "\n6. UPDATE TEAM FORM REPORT"
    )

    generated_at_utc = (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )

    sub_stages = dict(
        form_report.get(
            "sub_stages",
            {}
        )
    )

    sub_stages[
        "8.3.3"
    ] = "PASS"

    form_report[
        "sub_stages"
    ] = sub_stages

    form_report[
        "status"
    ] = "PARTIAL_PASS"

    form_report[
        "stage_8_3_complete"
    ] = False

    form_report[
        "canonical_team_form"
    ] = "VERIFIED"

    form_report[
        "venue_form_engine"
    ] = "VERIFIED"

    form_report[
        "generated_at_utc"
    ] = generated_at_utc

    form_report[
        "source_as_of_utc"
    ] = gated[
        "history_cutoff_utc"
    ]

    form_report[
        "history_cutoff_utc"
    ] = gated[
        "history_cutoff_utc"
    ]

    form_report[
        "current_team_form"
    ] = {

        "path":
            relative_path(
                OUTPUT_FILE
            ),

        "sha256":
            form_sha,

        "row_count":
            len(
                rows
            ),

        "column_count":
            len(
                FORM_FIELDS
            ),

        "columns":
            FORM_FIELDS,

        "sort_order":
            "team_name ASC",

        "team_namespace":
            "fixtureiq-team",
    }

    form_report[
        "venue_form"
    ] = {

        "enabled":
            True,

        "window":
            5,

        "allow_short_window":
            True,

        "season_scope":
            "CURRENT_PRODUCTION_SEASON_ONLY",

        "result_order":
            "OLDEST_TO_NEWEST",

        "most_recent_result_position":
            "RIGHTMOST",

        "home_min_matches_available":
            min(
                row[
                    "home_form_matches_available"
                ]
                for row in rows
            ),

        "home_max_matches_available":
            max(
                row[
                    "home_form_matches_available"
                ]
                for row in rows
            ),

        "away_min_matches_available":
            min(
                row[
                    "away_form_matches_available"
                ]
                for row in rows
            ),

        "away_max_matches_available":
            max(
                row[
                    "away_form_matches_available"
                ]
                for row in rows
            ),
    }

    form_report[
        "venue_form_evidence"
    ] = evidence

    # Semantic team identity dependency:
    # standings position/points changes must NOT invalidate form.
    form_report[
        "dependency_identity"
    ][
        "current_epl_team_registry"
    ] = {

        "path":
            relative_path(
                STANDINGS_FILE
            ),

        "usage":
            "CANONICAL_TEAM_IDENTITY_ONLY",

        "team_count":
            20,

        "semantic_sha256":
            registry_sha256(
                rows
            ),
    }

    form_report[
        "current_team_form_csv_written"
    ] = True

    form_report[
        "current_team_form_csv_owner"
    ] = "8.3.3"

    safety = dict(
        form_report.get(
            "safety",
            {}
        )
    )

    safety.update(
        {
            "context_only":
                True,

            "stage7_artifacts_modified":
                False,

            "provider_fetch_performed":
                False,

            "future_matches_used":
                False,

            "previous_season_padding_used":
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

            "form_used_as_model_features":
                False,

            "final_test_accessed":
                False,
        }
    )

    form_report[
        "safety"
    ] = safety

    form_report[
        "stage_8_3_3_verified_at_utc"
    ] = generated_at_utc

    save_json(
        TEAM_FORM_REPORT_FILE,
        form_report,
    )

    print(
        TEAM_FORM_REPORT_FILE
    )

    print(
        "\n" + "=" * 72
    )

    print(
        "STAGE 8.3.1: PASS"
    )

    print(
        "STAGE 8.3.2: PASS"
    )

    print(
        "STAGE 8.3.3: BUILT"
    )

    print(
        "HOME/AWAY FORM: CREATED"
    )

    print(
        "CANONICAL CURRENT TEAM FORM: CREATED"
    )

    print(
        "STAGE 8.3: IN PROGRESS"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
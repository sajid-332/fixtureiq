"""
FixtureIQ Stage 8.4.1 + 8.4.2 Verification.

Independently verifies:
- Stage 8.2 and Stage 8.3 complete
- StandingsService READY
- TeamFormService READY
- exact 20-team identity match
- canonical team_context.csv
- exact 38-column schema
- strict one-to-one join
- exact preservation of standings and form values
- upstream dependency hashes
- provenance
- Stage 8 safety boundary
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime
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

from backend.services.standings_service import (
    StandingsService,
)

from backend.services.team_form_service import (
    TeamFormService,
)

from backend.services.team_context_builder import (
    FORM_VALUE_FIELDS,
    STANDINGS_VALUE_FIELDS,
    TEAM_CONTEXT_FIELDS,
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
# CSV integer fields
# ============================================================

INTEGER_FIELDS = [

    field

    for field in TEAM_CONTEXT_FIELDS

    if field not in {

        "team_id",
        "team_name",

        "recent_results",
        "home_recent_results",
        "away_recent_results",
    }
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


def valid_timestamp(
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


def read_context_csv() -> tuple[
    list[str],
    list[dict],
]:

    with TEAM_CONTEXT_FILE.open(
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

        row = dict(
            raw
        )

        row[
            "team_id"
        ] = str(
            raw.get(
                "team_id",
                ""
            )
        ).strip()

        row[
            "team_name"
        ] = str(
            raw.get(
                "team_name",
                ""
            )
        ).strip()

        for field in INTEGER_FIELDS:

            row[
                field
            ] = int(
                raw[
                    field
                ]
            )

        rows.append(
            row
        )

    return (
        fields,
        rows,
    )


def independently_join(
    standings: list[dict],
    forms: list[dict],
) -> list[dict]:

    standings_by_id = {

        str(
            row[
                "team_id"
            ]
        ):
            row

        for row in standings
    }

    forms_by_id = {

        str(
            row[
                "team_id"
            ]
        ):
            row

        for row in forms
    }

    if (
        set(
            standings_by_id
        )
        !=
        set(
            forms_by_id
        )
    ):

        raise RuntimeError(
            "Independent join identity sets differ."
        )

    expected = []

    for team_id in standings_by_id:

        standings_row = (
            standings_by_id[
                team_id
            ]
        )

        form_row = (
            forms_by_id[
                team_id
            ]
        )

        if (
            standings_row[
                "team_name"
            ]
            !=
            form_row[
                "team_name"
            ]
        ):

            raise RuntimeError(
                (
                    "Independent join name mismatch: "
                    f"{team_id}"
                )
            )

        row = {

            "team_id":
                team_id,

            "team_name":
                standings_row[
                    "team_name"
                ],
        }

        for field in STANDINGS_VALUE_FIELDS:

            row[
                field
            ] = standings_row[
                field
            ]

        for field in FORM_VALUE_FIELDS:

            row[
                field
            ] = form_row[
                field
            ]

        expected.append(
            row
        )

    expected.sort(
        key=lambda row:
            row[
                "team_name"
            ].casefold()
    )

    return expected


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.4.1 + 8.4.2"
    )

    print(
        "Unified Team Context Build Verification"
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
        STANDINGS_REPORT_FILE,

        TEAM_FORM_FILE,
        TEAM_FORM_REPORT_FILE,

        TEAM_CONTEXT_FILE,
        TEAM_CONTEXT_REPORT_FILE,
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

    standings_report = load_json(
        STANDINGS_REPORT_FILE
    )

    form_report = load_json(
        TEAM_FORM_REPORT_FILE
    )

    report = load_json(
        TEAM_CONTEXT_REPORT_FILE
    )

    # ========================================================
    # 2. Foundation
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
        "Stage 8.2 COMPLETE",
        standings_report.get(
            "stage_8_2_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 8.2 VERIFIED",
        standings_report.get(
            "live_epl_standings_layer"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Stage 8.3 COMPLETE",
        form_report.get(
            "stage_8_3_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 8.3 VERIFIED",
        form_report.get(
            "current_team_form_layer"
        )
        == "VERIFIED",
        failures,
    )

    # ========================================================
    # 3. Stage 8.4 evidence
    # ========================================================

    print(
        "\n3. STAGE 8.4 EVIDENCE"
    )

    sub_stages = report.get(
        "sub_stages",
        {}
    )

    check(
        "Report stage = 8.4",
        report.get(
            "stage"
        )
        == "8.4",
        failures,
    )

    check(
        "8.4.1 PASS",
        sub_stages.get(
            "8.4.1"
        )
        == "PASS",
        failures,
    )

    check(
        "8.4.2 PASS",
        sub_stages.get(
            "8.4.2"
        )
        == "PASS",
        failures,
    )

    check(
        "Upstream readiness VERIFIED",
        report.get(
            "upstream_context_readiness"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Unified builder VERIFIED",
        report.get(
            "unified_team_context_builder"
        )
        == "VERIFIED",
        failures,
    )

    # ========================================================
    # 4. Real upstream services
    # ========================================================

    print(
        "\n4. REAL UPSTREAM SERVICES"
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

    check(
        "StandingsService READY",
        standings_status.get(
            "status"
        )
        == "READY",
        failures,
    )

    check(
        "TeamFormService READY",
        form_status.get(
            "status"
        )
        == "READY",
        failures,
    )

    standings = (
        standings_service
        .get_standings()
    )

    forms = (
        form_service
        .get_all_team_form()
    )

    check(
        "Standings rows = 20",
        len(
            standings
        )
        == 20,
        failures,
    )

    check(
        "Form rows = 20",
        len(
            forms
        )
        == 20,
        failures,
    )

    standings_identity = {

        (
            row[
                "team_id"
            ],
            row[
                "team_name"
            ],
        )

        for row in standings
    }

    form_identity = {

        (
            row[
                "team_id"
            ],
            row[
                "team_name"
            ],
        )

        for row in forms
    }

    check(
        "Exact 20-team identities match",
        (
            len(
                standings_identity
            )
            == 20
            and
            standings_identity
            == form_identity
        ),
        failures,
    )

    # ========================================================
    # 5. Canonical CSV
    # ========================================================

    print(
        "\n5. CANONICAL TEAM CONTEXT"
    )

    try:

        fields, rows = (
            read_context_csv()
        )

        read_ok = True

    except Exception as exc:

        print(
            "CSV read error:",
            exc,
        )

        fields = []
        rows = []
        read_ok = False

    check(
        "Canonical CSV readable",
        read_ok,
        failures,
    )

    check(
        "Schema exact",
        fields
        == TEAM_CONTEXT_FIELDS,
        failures,
    )

    check(
        "Column count = 38",
        len(
            fields
        )
        == 38,
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

    if rows:

        check(
            "20 unique team IDs",
            len(
                {
                    row[
                        "team_id"
                    ]
                    for row in rows
                }
            )
            == 20,
            failures,
        )

        check(
            "20 unique team names",
            len(
                {
                    row[
                        "team_name"
                    ].casefold()
                    for row in rows
                }
            )
            == 20,
            failures,
        )

        check(
            "Sorted team_name ASC",
            [
                row[
                    "team_name"
                ].casefold()
                for row in rows
            ]
            ==
            sorted(
                row[
                    "team_name"
                ].casefold()
                for row in rows
            ),
            failures,
        )

    # ========================================================
    # 6. Independent strict join
    # ========================================================

    print(
        "\n6. INDEPENDENT JOIN RECONSTRUCTION"
    )

    try:

        expected = independently_join(
            standings,
            forms,
        )

        join_ok = True

    except Exception as exc:

        print(
            "Join reconstruction error:",
            exc,
        )

        expected = []
        join_ok = False

    check(
        "Independent join succeeds",
        join_ok,
        failures,
    )

    check(
        "Independent join rows = 20",
        len(
            expected
        )
        == 20,
        failures,
    )

    check(
        "CSV exactly matches independent join",
        rows
        == expected,
        failures,
    )

    # ========================================================
    # 7. Standings/form preservation
    # ========================================================

    print(
        "\n7. UPSTREAM VALUE PRESERVATION"
    )

    context_by_id = {

        row[
            "team_id"
        ]:
            row

        for row in rows
    }

    standings_preserved = True

    for standing in standings:

        context = context_by_id.get(
            standing[
                "team_id"
            ]
        )

        if context is None:

            standings_preserved = False
            break

        for field in STANDINGS_VALUE_FIELDS:

            if (
                context.get(
                    field
                )
                !=
                standing.get(
                    field
                )
            ):

                standings_preserved = False
                break

    check(
        "Standings values exactly preserved",
        standings_preserved,
        failures,
    )

    form_preserved = True

    for form in forms:

        context = context_by_id.get(
            form[
                "team_id"
            ]
        )

        if context is None:

            form_preserved = False
            break

        for field in FORM_VALUE_FIELDS:

            if (
                context.get(
                    field
                )
                !=
                form.get(
                    field
                )
            ):

                form_preserved = False
                break

    check(
        "Form values exactly preserved",
        form_preserved,
        failures,
    )

    # ========================================================
    # 8. Artifact identity
    # ========================================================

    print(
        "\n8. ARTIFACT IDENTITY"
    )

    artifact = report.get(
        "team_context",
        {}
    )

    check(
        "Context SHA matches report",
        artifact.get(
            "sha256"
        )
        ==
        sha256_file(
            TEAM_CONTEXT_FILE
        ),
        failures,
    )

    check(
        "Reported row count = 20",
        artifact.get(
            "row_count"
        )
        == 20,
        failures,
    )

    check(
        "Reported column count = 38",
        artifact.get(
            "column_count"
        )
        == 38,
        failures,
    )

    check(
        "Reported schema exact",
        artifact.get(
            "columns"
        )
        == TEAM_CONTEXT_FIELDS,
        failures,
    )

    check(
        "Namespace fixtureiq-team",
        artifact.get(
            "team_namespace"
        )
        == "fixtureiq-team",
        failures,
    )

    # ========================================================
    # 9. Dependency identities
    # ========================================================

    print(
        "\n9. DEPENDENCY IDENTITY"
    )

    dependencies = report.get(
        "dependency_identity",
        {}
    )

    dependency_checks = [

        (
            "Stage 8 contract hash valid",
            "stage8_context_contract",
            CONTRACT_FILE,
        ),

        (
            "Stage 8 verification hash valid",
            "stage8_context_contract_verification",
            CONTRACT_VERIFICATION_FILE,
        ),

        (
            "Current standings hash valid",
            "current_standings",
            STANDINGS_FILE,
        ),

        (
            "Standings report hash valid",
            "standings_report",
            STANDINGS_REPORT_FILE,
        ),

        (
            "Current team form hash valid",
            "current_team_form",
            TEAM_FORM_FILE,
        ),

        (
            "Team form report hash valid",
            "team_form_report",
            TEAM_FORM_REPORT_FILE,
        ),
    ]

    for (
        label,
        dependency_name,
        dependency_file,
    ) in dependency_checks:

        check(
            label,
            dependencies.get(
                dependency_name,
                {}
            ).get(
                "sha256"
            )
            ==
            sha256_file(
                dependency_file
            ),
            failures,
        )

    # ========================================================
    # 10. Provenance / freshness
    # ========================================================

    print(
        "\n10. PROVENANCE & FRESHNESS"
    )

    for field in (

        "generated_at_utc",
        "source_as_of_utc",
        "standings_source_as_of_utc",
        "form_source_as_of_utc",
        "form_history_cutoff_utc",
    ):

        check(
            f"{field} valid",
            valid_timestamp(
                report.get(
                    field
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
        "Standings change invalidates context",
        freshness.get(
            "current_standings_change_invalidates_context"
        )
        is True,
        failures,
    )

    check(
        "Form change invalidates context",
        freshness.get(
            "current_team_form_change_invalidates_context"
        )
        is True,
        failures,
    )

    check(
        "Stale fallback prohibited",
        freshness.get(
            "stale_fallback_allowed"
        )
        is False,
        failures,
    )

    check(
        "Fail closed",
        freshness.get(
            "fail_closed"
        )
        is True,
        failures,
    )

    # ========================================================
    # 11. Safety boundary
    # ========================================================

    print(
        "\n11. SAFETY BOUNDARY"
    )

    safety = report.get(
        "safety",
        {}
    )

    check(
        "Context-only",
        safety.get(
            "context_only"
        )
        is True,
        failures,
    )

    false_flags = [

        "stage7_artifacts_modified",
        "provider_fetch_performed",
        "standings_rebuilt",
        "team_form_rebuilt",
        "model_loaded",
        "model_executed",
        "model_modified",
        "production_predictions_modified",
        "feature_schema_modified",
        "team_context_used_as_model_features",
        "final_test_accessed",
    ]

    for flag in false_flags:

        check(
            f"{flag} = false",
            safety.get(
                flag
            )
            is False,
            failures,
        )

    # ========================================================
    # Final
    # ========================================================

    overall_pass = (
        len(
            failures
        )
        == 0
    )

    print(
        "\n" + "=" * 72
    )

    if overall_pass:

        print(
            "STAGE 8.4.1: PASS"
        )

        print(
            "UPSTREAM CONTEXT READINESS: VERIFIED"
        )

        print(
            "STAGE 8.4.2: PASS"
        )

        print(
            "UNIFIED TEAM CONTEXT: VERIFIED"
        )

        print(
            "STAGE 8.4: IN PROGRESS"
        )

    else:

        print(
            "STAGE 8.4.1 / 8.4.2: FAIL"
        )

        print(
            "STAGE 8.4: INCOMPLETE"
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
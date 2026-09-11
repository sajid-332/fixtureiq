"""
FixtureIQ Stage 8.5.3
Independent Fixture Context Validation.

Runs the reusable independent validator and records verification
evidence inside the existing declared fixture_context_report.json.

No new persistent Stage 8 artifact is created.
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

from backend.services.fixture_context_validator import (
    FixtureContextValidationError,
    FixtureContextValidator,
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

REPORT_FILE = (
    CONTEXT_DIR
    / "fixture_context_report.json"
)


# ============================================================
# Helpers
# ============================================================

def load_json(
    path: Path,
) -> dict:

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


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

        failures.append(label)

    return passed


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.5.3"
    )

    print(
        "Independent Fixture Context Validation"
    )

    print("=" * 72)

    failures = []

    # ========================================================
    # 1. Run independent validator
    # ========================================================

    print(
        "\n1. INDEPENDENT VALIDATOR"
    )

    validator = (
        FixtureContextValidator()
    )

    try:

        result = (
            validator.validate()
        )

        validator_pass = (
            result.get(
                "status"
            )
            == "PASS"
        )

    except FixtureContextValidationError as exc:

        print(
            "Validation reason:",
            exc,
        )

        result = {}
        validator_pass = False

    except Exception as exc:

        print(
            "Unexpected validation error:",
            exc,
        )

        result = {}
        validator_pass = False

    check(
        "Independent validator PASS",
        validator_pass,
        failures,
    )

    if not validator_pass:

        print(
            "\n" + "=" * 72
        )

        print(
            "STAGE 8.5.3: FAIL"
        )

        print(
            "STAGE 8.5: INCOMPLETE"
        )

        print("=" * 72)

        sys.exit(1)

    # ========================================================
    # 2. Canonical shape
    # ========================================================

    print(
        "\n2. CANONICAL FIXTURE SHAPE"
    )

    check(
        "Fixture count > 0",
        result.get(
            "fixture_count",
            0
        )
        > 0,
        failures,
    )

    check(
        "36 context fields per team",
        result.get(
            "context_fields_per_team"
        )
        == 36,
        failures,
    )

    check(
        "72 context fields appended",
        result.get(
            "context_fields_appended"
        )
        == 72,
        failures,
    )

    check(
        "Fixture IDs unique",
        result.get(
            "fixture_ids_unique"
        )
        is True,
        failures,
    )

    check(
        "Provider fixture IDs unique when present",
        result.get(
            "provider_fixture_ids_unique_when_present"
        )
        is True,
        failures,
    )

    check(
        "Row count preserved",
        result.get(
            "row_count_preserved"
        )
        is True,
        failures,
    )

    check(
        "Deterministic sort verified",
        result.get(
            "deterministic_sort_verified"
        )
        is True,
        failures,
    )

    # ========================================================
    # 3. Source fixture preservation
    # ========================================================

    print(
        "\n3. SOURCE FIXTURE PRESERVATION"
    )

    check(
        "Source fields preserved",
        result.get(
            "source_fields_preserved"
        )
        is True,
        failures,
    )

    check(
        "Strict home identity verified",
        result.get(
            "strict_home_identity_verified"
        )
        is True,
        failures,
    )

    check(
        "Strict away identity verified",
        result.get(
            "strict_away_identity_verified"
        )
        is True,
        failures,
    )

    # ========================================================
    # 4. Context preservation
    # ========================================================

    print(
        "\n4. HOME/AWAY CONTEXT PRESERVATION"
    )

    check(
        "Home context preservation verified",
        result.get(
            "home_context_preservation_verified"
        )
        is True,
        failures,
    )

    check(
        "Away context preservation verified",
        result.get(
            "away_context_preservation_verified"
        )
        is True,
        failures,
    )

    check(
        "Exact independent reconstruction verified",
        result.get(
            "exact_independent_reconstruction_verified"
        )
        is True,
        failures,
    )

    # ========================================================
    # 5. Temporal safety
    # ========================================================

    print(
        "\n5. TEMPORAL SAFETY"
    )

    check(
        "All fixtures future",
        result.get(
            "all_fixtures_future"
        )
        is True,
        failures,
    )

    check(
        "Form cutoff verified",
        result.get(
            "form_cutoff_verified"
        )
        is True,
        failures,
    )

    check(
        "Team context temporal boundary verified",
        result.get(
            "team_context_temporal_boundary_verified"
        )
        is True,
        failures,
    )

    check(
        "Fixture snapshot provenance verified",
        result.get(
            "fixture_snapshot_provenance_verified"
        )
        is True,
        failures,
    )

    # ========================================================
    # 6. Snapshot policy
    # ========================================================

    print(
        "\n6. SHARED SNAPSHOT POLICY"
    )

    check(
        "Shared context snapshot verified",
        result.get(
            "shared_context_snapshot_verified"
        )
        is True,
        failures,
    )

    check(
        "Future-fixture state propagation disabled",
        result.get(
            "future_fixture_state_propagation"
        )
        is False,
        failures,
    )

    # ========================================================
    # 7. Dependencies / safety
    # ========================================================

    print(
        "\n7. DEPENDENCY & SAFETY VALIDATION"
    )

    check(
        "Dependency identity verified",
        result.get(
            "dependency_identity_verified"
        )
        is True,
        failures,
    )

    check(
        "Freshness contract verified",
        result.get(
            "freshness_contract_verified"
        )
        is True,
        failures,
    )

    check(
        "Safety verified",
        result.get(
            "safety_verified"
        )
        is True,
        failures,
    )

    # ========================================================
    # 8. Persist Stage 8.5.3 evidence
    # ========================================================

    print(
        "\n8. SAVE STAGE 8.5.3 EVIDENCE"
    )

    if failures:

        print(
            "Validation checks failed; report not promoted."
        )

    else:

        report = load_json(
            REPORT_FILE
        )

        sub_stages = dict(
            report.get(
                "sub_stages",
                {}
            )
        )

        sub_stages[
            "8.5.3"
        ] = "PASS"

        report[
            "sub_stages"
        ] = sub_stages

        report[
            "status"
        ] = "PARTIAL_PASS"

        report[
            "stage_8_5_complete"
        ] = False

        report[
            "independent_fixture_context_validation"
        ] = "VERIFIED"

        report[
            "independent_validation"
        ] = {

            "status":
                "VERIFIED",

            "fixture_count":
                result[
                    "fixture_count"
                ],

            "source_column_count":
                result[
                    "source_column_count"
                ],

            "context_fields_per_team":
                36,

            "context_fields_appended":
                72,

            "enriched_column_count":
                result[
                    "enriched_column_count"
                ],

            "fixture_ids_unique":
                True,

            "provider_fixture_ids_unique_when_present":
                True,

            "source_fields_preserved":
                True,

            "strict_home_identity_verified":
                True,

            "strict_away_identity_verified":
                True,

            "home_context_preservation_verified":
                True,

            "away_context_preservation_verified":
                True,

            "exact_independent_reconstruction_verified":
                True,

            "row_count_preserved":
                True,

            "deterministic_sort_verified":
                True,

            "all_fixtures_future":
                True,

            "form_cutoff_verified":
                True,

            "team_context_temporal_boundary_verified":
                True,

            "fixture_snapshot_provenance_verified":
                True,

            "shared_context_snapshot_verified":
                True,

            "future_fixture_state_propagation":
                False,

            "dependency_identity_verified":
                True,

            "freshness_contract_verified":
                True,

            "safety_verified":
                True,

            "earliest_fixture_kickoff_utc":
                result[
                    "earliest_fixture_kickoff_utc"
                ],

            "latest_fixture_kickoff_utc":
                result[
                    "latest_fixture_kickoff_utc"
                ],

            "enriched_artifact_sha256":
                result[
                    "enriched_artifact_sha256"
                ],
        }

        report[
            "stage_8_5_3_verified_at_utc"
        ] = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        save_json(
            REPORT_FILE,
            report,
        )

        print(
            REPORT_FILE
        )

        # ====================================================
        # Revalidate after report mutation
        # ====================================================

        try:

            post_result = (
                FixtureContextValidator()
                .validate()
            )

            post_ok = (
                post_result.get(
                    "status"
                )
                == "PASS"
            )

        except Exception as exc:

            print(
                "Post-update validation reason:",
                exc,
            )

            post_ok = False

        check(
            "Validator remains PASS after report update",
            post_ok,
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
            "STAGE 8.5.1: PASS"
        )

        print(
            "STAGE 8.5.2: PASS"
        )

        print(
            "STAGE 8.5.3: PASS"
        )

        print(
            "INDEPENDENT FIXTURE CONTEXT VALIDATION: VERIFIED"
        )

        print(
            "STAGE 8.5: IN PROGRESS"
        )

    else:

        print(
            "STAGE 8.5.3: FAIL"
        )

        print(
            "STAGE 8.5: INCOMPLETE"
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
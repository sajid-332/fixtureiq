"""
FixtureIQ Stage 8.4.3
Independent Unified Team Context Validation.
"""

from __future__ import annotations

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


from backend.services.team_context_validator import (
    TeamContextValidationError,
    TeamContextValidator,
)


CONTEXT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "context"
)

REPORT_FILE = (
    CONTEXT_DIR
    / "team_context_report.json"
)


def load_json(
    path: Path,
) -> dict:

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(
            file
        )


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


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.4.3"
    )

    print(
        "Independent Unified Team Context Validation"
    )

    print("=" * 72)

    failures = []

    validator = (
        TeamContextValidator()
    )

    try:

        result = (
            validator.validate()
        )

        validation_passed = True

    except TeamContextValidationError as exc:

        print(
            "Validation error:",
            exc,
        )

        result = {}
        validation_passed = False

    except Exception as exc:

        print(
            "Unexpected validation error:",
            exc,
        )

        result = {}
        validation_passed = False

    print(
        "\n1. INDEPENDENT VALIDATION"
    )

    check(
        "Independent validator PASS",
        validation_passed,
        failures,
    )

    if validation_passed:

        check(
            "20 canonical teams",
            result.get(
                "team_count"
            )
            == 20,
            failures,
        )

        check(
            "38 canonical columns",
            result.get(
                "column_count"
            )
            == 38,
            failures,
        )

        check(
            "Independent join verified",
            result.get(
                "independent_join_verified"
            )
            is True,
            failures,
        )

        check(
            "Standings arithmetic verified",
            result.get(
                "standings_arithmetic_verified"
            )
            is True,
            failures,
        )

        check(
            "Overall form verified",
            result.get(
                "overall_form_verified"
            )
            is True,
            failures,
        )

        check(
            "Home form verified",
            result.get(
                "home_form_verified"
            )
            is True,
            failures,
        )

        check(
            "Away form verified",
            result.get(
                "away_form_verified"
            )
            is True,
            failures,
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
            "Provenance verified",
            result.get(
                "provenance_verified"
            )
            is True,
            failures,
        )

        check(
            "Safety boundary verified",
            result.get(
                "safety_verified"
            )
            is True,
            failures,
        )

    overall_pass = (
        len(
            failures
        )
        == 0
    )

    # ========================================================
    # Persist Stage 8.4.3 evidence
    # ========================================================

    print(
        "\n2. SAVE STAGE 8.4.3 EVIDENCE"
    )

    if overall_pass:

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
            "8.4.3"
        ] = "PASS"

        report[
            "sub_stages"
        ] = sub_stages

        report[
            "status"
        ] = "PARTIAL_PASS"

        report[
            "stage_8_4_complete"
        ] = False

        report[
            "independent_context_validation"
        ] = "VERIFIED"

        report[
            "independent_validation"
        ] = {

            "status":
                "VERIFIED",

            "team_count":
                20,

            "column_count":
                38,

            "independent_join_verified":
                True,

            "standings_arithmetic_verified":
                True,

            "overall_form_verified":
                True,

            "home_form_verified":
                True,

            "away_form_verified":
                True,

            "dependency_identity_verified":
                True,

            "provenance_verified":
                True,

            "safety_verified":
                True,
        }

        report[
            "stage_8_4_3_verified_at_utc"
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

        # Re-run after report mutation.
        #
        # The validator does not self-hash team_context_report,
        # therefore promoting the verification state must not
        # invalidate the underlying snapshot.
        try:

            post_update = (
                TeamContextValidator()
                .validate()
            )

            post_update_ok = (
                post_update.get(
                    "status"
                )
                == "PASS"
            )

        except Exception as exc:

            print(
                "Post-update validation error:",
                exc,
            )

            post_update_ok = False

        check(
            "Context remains valid after report update",
            post_update_ok,
            failures,
        )

        overall_pass = (
            len(
                failures
            )
            == 0
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
            "STAGE 8.4.1: PASS"
        )

        print(
            "STAGE 8.4.2: PASS"
        )

        print(
            "STAGE 8.4.3: PASS"
        )

        print(
            "INDEPENDENT TEAM CONTEXT VALIDATION: VERIFIED"
        )

        print(
            "STAGE 8.4: IN PROGRESS"
        )

    else:

        print(
            "STAGE 8.4.3: FAIL"
        )

        print(
            "STAGE 8.4: INCOMPLETE"
        )

        if failures:

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
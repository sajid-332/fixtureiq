"""
FixtureIQ Stage 8.1.5
Output Artifact Contract Builder.

Extends the already verified Stage 8.1 contract.

Requires:
- 8.1.1 LOCKED
- 8.1.2 LOCKED
- 8.1.3 LOCKED
- 8.1.4 LOCKED

Adds:
- Stage 8 output ownership
- canonical output paths
- artifact types
- data/report pairing
- Stage 7 write protection
- final Stage 8 evidence policy

This script does not create standings, form, team context,
fixture context, or API data.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
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

CONTRACT_FILE = (
    CONTEXT_DIR
    / "stage8_context_contract.json"
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


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.1.5"
    )

    print(
        "Output Artifact Contract Builder"
    )

    print("=" * 72)

    contract = load_json(
        CONTRACT_FILE
    )

    sub_stages = dict(
        contract.get(
            "sub_stages",
            {}
        )
    )

    # ========================================================
    # 1. Require previous Stage 8.1 sections
    # ========================================================

    print(
        "\n1. PREVIOUS CONTRACT SECTIONS"
    )

    for stage in (
        "8.1.1",
        "8.1.2",
        "8.1.3",
        "8.1.4",
    ):

        locked = (
            sub_stages.get(
                stage
            )
            == "LOCKED"
        )

        print(
            f"{stage} LOCKED: "
            f"{'PASS' if locked else 'FAIL'}"
        )

        if not locked:

            raise RuntimeError(
                (
                    "Cannot build Stage 8.1.5 because "
                    f"{stage} is not LOCKED."
                )
            )

    # ========================================================
    # 2. Canonical Stage 8 outputs
    # ========================================================

    print(
        "\n2. OUTPUT ARTIFACT CONTRACT"
    )

    outputs = {

        # ----------------------------------------------------
        # Stage 8.1
        # ----------------------------------------------------

        "stage8_context_contract": {

            "path":
                (
                    "data/processed/context/"
                    "stage8_context_contract.json"
                ),

            "owner_stage":
                "8.1",

            "artifact_type":
                "CONTRACT",

            "dynamic":
                False,

            "required_for_stage8_final":
                True,
        },

        "stage8_context_contract_verification": {

            "path":
                (
                    "data/processed/context/"
                    "stage8_context_contract_verification.json"
                ),

            "owner_stage":
                "8.1",

            "artifact_type":
                "VERIFICATION",

            "dynamic":
                False,

            "required_for_stage8_final":
                True,
        },

        # ----------------------------------------------------
        # Stage 8.2
        # ----------------------------------------------------

        "current_standings": {

            "path":
                (
                    "data/processed/context/"
                    "current_standings.csv"
                ),

            "owner_stage":
                "8.2",

            "artifact_type":
                "DATA",

            "dynamic":
                True,

            "required_for_stage8_final":
                True,
        },

        "standings_report": {

            "path":
                (
                    "data/processed/context/"
                    "standings_report.json"
                ),

            "owner_stage":
                "8.2",

            "artifact_type":
                "REPORT",

            "dynamic":
                True,

            "required_for_stage8_final":
                True,
        },

        # ----------------------------------------------------
        # Stage 8.3
        # ----------------------------------------------------

        "current_team_form": {

            "path":
                (
                    "data/processed/context/"
                    "current_team_form.csv"
                ),

            "owner_stage":
                "8.3",

            "artifact_type":
                "DATA",

            "dynamic":
                True,

            "required_for_stage8_final":
                True,
        },

        "team_form_report": {

            "path":
                (
                    "data/processed/context/"
                    "team_form_report.json"
                ),

            "owner_stage":
                "8.3",

            "artifact_type":
                "REPORT",

            "dynamic":
                True,

            "required_for_stage8_final":
                True,
        },

        # ----------------------------------------------------
        # Stage 8.4
        # ----------------------------------------------------

        "team_context": {

            "path":
                (
                    "data/processed/context/"
                    "team_context.csv"
                ),

            "owner_stage":
                "8.4",

            "artifact_type":
                "DATA",

            "dynamic":
                True,

            "required_for_stage8_final":
                True,
        },

        "team_context_report": {

            "path":
                (
                    "data/processed/context/"
                    "team_context_report.json"
                ),

            "owner_stage":
                "8.4",

            "artifact_type":
                "REPORT",

            "dynamic":
                True,

            "required_for_stage8_final":
                True,
        },

        # ----------------------------------------------------
        # Stage 8.5
        # ----------------------------------------------------

        "enriched_upcoming_fixtures": {

            "path":
                (
                    "data/processed/context/"
                    "enriched_upcoming_fixtures.csv"
                ),

            "owner_stage":
                "8.5",

            "artifact_type":
                "DATA",

            "dynamic":
                True,

            "required_for_stage8_final":
                True,
        },

        "fixture_context_report": {

            "path":
                (
                    "data/processed/context/"
                    "fixture_context_report.json"
                ),

            "owner_stage":
                "8.5",

            "artifact_type":
                "REPORT",

            "dynamic":
                True,

            "required_for_stage8_final":
                True,
        },

        # ----------------------------------------------------
        # Stage 8.6
        # ----------------------------------------------------

        "context_api_verification": {

            "path":
                (
                    "data/processed/context/"
                    "context_api_verification.json"
                ),

            "owner_stage":
                "8.6",

            "artifact_type":
                "VERIFICATION",

            "dynamic":
                True,

            "required_for_stage8_final":
                True,
        },

        # ----------------------------------------------------
        # Stage 8.7
        # ----------------------------------------------------

        "context_runtime_verification": {

            "path":
                (
                    "data/processed/context/"
                    "context_runtime_verification.json"
                ),

            "owner_stage":
                "8.7",

            "artifact_type":
                "VERIFICATION",

            "dynamic":
                True,

            "required_for_stage8_final":
                True,
        },

        # ----------------------------------------------------
        # Stage 8.8
        # ----------------------------------------------------

        "stage8_final_verification": {

            "path":
                (
                    "data/processed/context/"
                    "stage8_final_verification.json"
                ),

            "owner_stage":
                "8.8",

            "artifact_type":
                "FINAL_VERIFICATION",

            "dynamic":
                True,

            "required_for_stage8_final":
                True,
        },
    }

    contract[
        "output_artifact_contract"
    ] = {

        "contract_version":
            "1.0.0",

        "output_root":
            "data/processed/context",

        "owner":
            "STAGE_8",

        "stage7_output_write_allowed":
            False,

        "all_stage8_outputs_must_remain_under_output_root":
            True,

        "outputs":
            outputs,

        "rules": {

            "stage7_artifacts_may_be_overwritten":
                False,

            "dynamic_context_artifacts_may_refresh":
                True,

            "data_artifacts_require_companion_reports":
                True,

            "derived_artifacts_require_provenance":
                True,

            "derived_artifacts_require_dependency_identity":
                True,

            "public_context_must_come_from_verified_artifacts":
                True,

            "partial_unverified_output_serving_allowed":
                False,

            "stage8_final_gate_must_hash_evidence":
                True,

            # Important:
            # 8.1 defines future artifacts.
            # They are not expected to exist yet.
            "future_stage_artifacts_need_not_exist_during_stage8_1":
                True,
        },

        "data_report_pairs": [

            [
                "current_standings",
                "standings_report",
            ],

            [
                "current_team_form",
                "team_form_report",
            ],

            [
                "team_context",
                "team_context_report",
            ],

            [
                "enriched_upcoming_fixtures",
                "fixture_context_report",
            ],
        ],
    }

    print(
        "Output root: "
        "data/processed/context"
    )

    print(
        f"Declared artifacts: {len(outputs)}"
    )

    print(
        "Stage 7 write access: PROHIBITED"
    )

    print(
        "Data/report pairing: DECLARED"
    )

    # ========================================================
    # 3. Stage markers
    # ========================================================

    sub_stages[
        "8.1.5"
    ] = "LOCKED"

    # Preserve final lock when this builder is rerun
    # after Stage 8.1.6 has already passed.
    if (
        sub_stages.get(
            "8.1.6"
        )
        != "LOCKED"
    ):

        sub_stages[
            "8.1.6"
        ] = "PENDING"

    contract[
        "sub_stages"
    ] = sub_stages

    if (
        sub_stages.get(
            "8.1.6"
        )
        == "LOCKED"
    ):

        contract[
            "stage_8_1_complete"
        ] = True

        contract[
            "stage_8_1_status"
        ] = "COMPLETE"

        contract[
            "contract_status"
        ] = "LOCKED_CONTEXT_CONTRACT"

    else:

        contract[
            "stage_8_1_complete"
        ] = False

        contract[
            "stage_8_1_status"
        ] = "IN_PROGRESS"

        contract[
            "contract_status"
        ] = "READY_FOR_FINAL_VERIFICATION"

    contract[
        "updated_at_utc"
    ] = datetime.now(
        timezone.utc
    ).isoformat()

    # ========================================================
    # 4. Save
    # ========================================================

    with CONTRACT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            contract,
            file,
            indent=2,
        )

    print(
        "\n3. CONTRACT OUTPUT"
    )

    print(
        CONTRACT_FILE
    )

    print(
        "\n" + "=" * 72
    )

    print(
        "STAGE 8.1.5: BUILT"
    )

    print(
        "OUTPUT ARTIFACT CONTRACT: LOCKED"
    )

    print(
        "STAGE 8.1.6: READY FOR FINAL VERIFICATION"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
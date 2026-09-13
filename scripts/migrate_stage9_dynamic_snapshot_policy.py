"""
FixtureIQ Stage 9.1 Contract Maintenance Patch
Version 1.2.1

Purpose:
Separate immutable Stage 9 policy from mutable production snapshots.

Before:
Stage 9.1 permanently pinned hashes of Stage 7 / Stage 8
production artifacts.

Problem:
Every legitimate production refresh changed those hashes,
making the locked policy contract reject valid new snapshots.

After:
- allowed paths / permissions / authorities remain locked
- Stage 9.1 policy remains locked
- dynamic dependency hashes are captured by downstream
  Stage 9 build reports
- Stage 9.2 report becomes the snapshot freshness anchor
- changed upstream data => Stage 9.2 stale => rebuild
- no need to rewrite Stage 9.1 on every production refresh

Also patches Stage 9.2 code to use the corrected policy.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

INTELLIGENCE_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "intelligence"
)

CONTRACT_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract.json"
)

VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract_verification.json"
)

JOIN_SERVICE_FILE = (
    BASE_DIR
    / "backend"
    / "services"
    / "prediction_context_join_service.py"
)

BASE_BUILDER_FILE = (
    BASE_DIR
    / "backend"
    / "services"
    / "match_intelligence_base_builder.py"
)

BASE_VALIDATOR_FILE = (
    BASE_DIR
    / "backend"
    / "services"
    / "match_intelligence_base_validator.py"
)

STAGE9_2_FINAL_FILE = (
    BASE_DIR
    / "scripts"
    / "verify_stage9_2.py"
)


POLICY = (
    "CAPTURE_AT_DOWNSTREAM_BUILD"
)


def load_json(
    path: Path,
) -> dict:

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


def save_json_atomic(
    path: Path,
    payload: dict,
) -> None:

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temporary.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=2,
        )

    temporary.replace(
        path
    )


def save_text_atomic(
    path: Path,
    text: str,
) -> None:

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        text,
        encoding="utf-8",
    )

    temporary.replace(
        path
    )


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


def patch_once_or_already(
    *,
    path: Path,
    old: str,
    new: str,
    already_marker: str,
) -> str:

    text = path.read_text(
        encoding="utf-8"
    )

    if old in text:

        count = text.count(
            old
        )

        if count != 1:

            raise RuntimeError(
                (
                    f"Expected exactly one patch target "
                    f"in {path}, found {count}."
                )
            )

        return text.replace(
            old,
            new,
            1,
        )

    if already_marker in text:

        print(
            f"{path.name}: already migrated"
        )

        return text

    raise RuntimeError(
        (
            "Migration patch target not found in "
            f"{path}. Stop rather than guessing."
        )
    )


# ============================================================
# Source patch blocks
# ============================================================

OLD_JOIN_HASH_BLOCK = '''            if (
                item.get(
                    "sha256"
                )
                !=
                _sha256_file(
                    path
                )
            ):

                raise PredictionContextJoinError(
                    (
                        f"Allowed input {name!r} "
                        "no longer matches the locked "
                        "Stage 9.1 dependency hash."
                    )
                )
'''

NEW_JOIN_HASH_BLOCK = '''            if (
                item.get(
                    "dependency_hash_policy"
                )
                != "CAPTURE_AT_DOWNSTREAM_BUILD"
            ):

                raise PredictionContextJoinError(
                    (
                        f"Allowed input {name!r} has "
                        "invalid dynamic snapshot policy."
                    )
                )

            if (
                item.get(
                    "contract_runtime_hash_pin"
                )
                is not False
            ):

                raise PredictionContextJoinError(
                    (
                        f"Allowed input {name!r} incorrectly "
                        "uses a permanent runtime hash pin."
                    )
                )

            if (
                item.get(
                    "downstream_snapshot_hash_required"
                )
                is not True
            ):

                raise PredictionContextJoinError(
                    (
                        f"Allowed input {name!r} does not "
                        "require downstream snapshot hashing."
                    )
                )
'''


OLD_STAGE7_STATUS_TO_STAGE8 = '''        for name, payload in stage7_evidence.items():

            if (
                payload.get(
                    "status"
                )
                != "PASS"
            ):

                raise PredictionSourceNotReadyError(
                    (
                        f"{name} does not have "
                        "status PASS."
                    )
                )

        if (
            stage8_final.get(
'''

NEW_STAGE7_STATUS_TO_STAGE8 = '''        for name, payload in stage7_evidence.items():

            if (
                payload.get(
                    "status"
                )
                != "PASS"
            ):

                raise PredictionSourceNotReadyError(
                    (
                        f"{name} does not have "
                        "status PASS."
                    )
                )

        # ----------------------------------------------------
        # Dynamic Stage 7 snapshot integrity
        #
        # The Stage 9.1 policy contract no longer permanently
        # pins production snapshot hashes. The current
        # production prediction artifact must instead be
        # cryptographically anchored by the current Stage 7
        # prediction metadata and prediction report.
        # ----------------------------------------------------

        prediction_sha = _sha256_file(
            self.predictions_file
        )

        def contains_exact_value(
            value,
            target: str,
        ) -> bool:

            if isinstance(
                value,
                dict,
            ):

                return any(
                    contains_exact_value(
                        child,
                        target,
                    )

                    for child in value.values()
                )

            if isinstance(
                value,
                list,
            ):

                return any(
                    contains_exact_value(
                        child,
                        target,
                    )

                    for child in value
                )

            return (
                isinstance(
                    value,
                    str,
                )
                and
                value
                == target
            )

        hash_evidence = {

            "production_prediction_metadata":
                metadata,

            "production_prediction_report":
                report,
        }

        for name, payload in hash_evidence.items():

            if not contains_exact_value(
                payload,
                prediction_sha,
            ):

                raise PredictionSourceNotReadyError(
                    (
                        f"{name} does not anchor the current "
                        "production_predictions.csv SHA256."
                    )
                )

        if (
            stage8_final.get(
'''


OLD_BUILDER_HASH_BLOCK = '''            current_sha = (
                _sha256_file(
                    source_path
                )
            )

            if (
                current_sha
                != item.get(
                    "sha256"
                )
            ):

                raise MatchIntelligenceBaseBuildError(
                    (
                        f"Locked dependency {name!r} "
                        "changed before Stage 9.2.3 build."
                    )
                )

            dependency_identity[
'''

NEW_BUILDER_HASH_BLOCK = '''            current_sha = (
                _sha256_file(
                    source_path
                )
            )

            if (
                item.get(
                    "dependency_hash_policy"
                )
                != "CAPTURE_AT_DOWNSTREAM_BUILD"
            ):

                raise MatchIntelligenceBaseBuildError(
                    (
                        f"Dependency {name!r} does not use "
                        "the locked downstream snapshot policy."
                    )
                )

            if (
                item.get(
                    "contract_runtime_hash_pin"
                )
                is not False
            ):

                raise MatchIntelligenceBaseBuildError(
                    (
                        f"Dependency {name!r} incorrectly "
                        "uses a permanent contract hash pin."
                    )
                )

            dependency_identity[
'''


OLD_VALIDATOR_HASH_BLOCK = '''            if (
                item.get(
                    "sha256"
                )
                != current_sha
            ):

                raise MatchIntelligenceBaseValidationError(
                    (
                        f"Locked dependency changed: "
                        f"{name}"
                    )
                )

            report_item = (
'''

NEW_VALIDATOR_HASH_BLOCK = '''            if (
                item.get(
                    "dependency_hash_policy"
                )
                != "CAPTURE_AT_DOWNSTREAM_BUILD"
            ):

                raise MatchIntelligenceBaseValidationError(
                    (
                        f"Dependency {name!r} has invalid "
                        "snapshot hash policy."
                    )
                )

            if (
                item.get(
                    "contract_runtime_hash_pin"
                )
                is not False
            ):

                raise MatchIntelligenceBaseValidationError(
                    (
                        f"Dependency {name!r} incorrectly "
                        "uses a permanent contract hash pin."
                    )
                )

            report_item = (
'''


OLD_FINAL_GATE_HASH_CHECK = '''        check(
            f"{name} SHA current",
            item.get(
                "sha256"
            )
            ==
            sha256_file(
                expected_path
            ),
            failures,
        )
'''

NEW_FINAL_GATE_HASH_CHECK = '''        check(
            f"{name} snapshot hash policy",
            item.get(
                "dependency_hash_policy"
            )
            ==
            "CAPTURE_AT_DOWNSTREAM_BUILD",
            failures,
        )

        check(
            f"{name} permanent runtime hash pin disabled",
            item.get(
                "contract_runtime_hash_pin"
            )
            is False,
            failures,
        )

        check(
            f"{name} downstream snapshot hash required",
            item.get(
                "downstream_snapshot_hash_required"
            )
            is True,
            failures,
        )
'''


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 9.1 Contract Maintenance"
    )

    print(
        "DYNAMIC SNAPSHOT POLICY MIGRATION"
    )

    print("=" * 72)

    required = [

        CONTRACT_FILE,
        VERIFICATION_FILE,
        JOIN_SERVICE_FILE,
        BASE_BUILDER_FILE,
        BASE_VALIDATOR_FILE,
        STAGE9_2_FINAL_FILE,
    ]

    for path in required:

        if not path.exists():

            raise FileNotFoundError(
                f"Required file missing: {path}"
            )

    contract = load_json(
        CONTRACT_FILE
    )

    verification = load_json(
        VERIFICATION_FILE
    )

    if (
        contract.get(
            "status"
        )
        !=
        "LOCKED_MATCH_INTELLIGENCE_CONTRACT"
    ):

        raise RuntimeError(
            "Stage 9.1 contract is not locked."
        )

    if (
        contract.get(
            "stage_9_1_complete"
        )
        is not True
    ):

        raise RuntimeError(
            "Stage 9.1 is not complete."
        )

    for substage in (

        "9.1.1",
        "9.1.2",
        "9.1.3",
        "9.1.4",
        "9.1.5",
    ):

        if (
            contract.get(
                "sub_stages",
                {}
            ).get(
                substage
            )
            != "PASS"
        ):

            raise RuntimeError(
                f"{substage} is not PASS."
            )

    if (
        verification.get(
            "status"
        )
        != "PASS"
    ):

        raise RuntimeError(
            "Stage 9.1 verification is not PASS."
        )

    # ========================================================
    # Preflight source patches
    # ========================================================

    staged_sources = {}

    staged_sources[
        JOIN_SERVICE_FILE
    ] = patch_once_or_already(

        path=
            JOIN_SERVICE_FILE,

        old=
            OLD_JOIN_HASH_BLOCK,

        new=
            NEW_JOIN_HASH_BLOCK,

        already_marker=
            "invalid dynamic snapshot policy",
    )

    staged_sources[
        JOIN_SERVICE_FILE
    ] = (
        staged_sources[
            JOIN_SERVICE_FILE
        ].replace(
            OLD_STAGE7_STATUS_TO_STAGE8,
            NEW_STAGE7_STATUS_TO_STAGE8,
            1,
        )
        if OLD_STAGE7_STATUS_TO_STAGE8
        in staged_sources[
            JOIN_SERVICE_FILE
        ]
        else staged_sources[
            JOIN_SERVICE_FILE
        ]
    )

    if (
        "production_predictions.csv SHA256"
        not in staged_sources[
            JOIN_SERVICE_FILE
        ]
    ):

        raise RuntimeError(
            (
                "Could not install dynamic Stage 7 "
                "prediction SHA validation."
            )
        )

    staged_sources[
        BASE_BUILDER_FILE
    ] = patch_once_or_already(

        path=
            BASE_BUILDER_FILE,

        old=
            OLD_BUILDER_HASH_BLOCK,

        new=
            NEW_BUILDER_HASH_BLOCK,

        already_marker=
            "the locked downstream snapshot policy",
    )

    staged_sources[
        BASE_VALIDATOR_FILE
    ] = patch_once_or_already(

        path=
            BASE_VALIDATOR_FILE,

        old=
            OLD_VALIDATOR_HASH_BLOCK,

        new=
            NEW_VALIDATOR_HASH_BLOCK,

        already_marker=
            "snapshot hash policy",
    )

    staged_sources[
        STAGE9_2_FINAL_FILE
    ] = patch_once_or_already(

        path=
            STAGE9_2_FINAL_FILE,

        old=
            OLD_FINAL_GATE_HASH_CHECK,

        new=
            NEW_FINAL_GATE_HASH_CHECK,

        already_marker=
            "permanent runtime hash pin disabled",
    )

    # ========================================================
    # Migrate contract policy
    # ========================================================

    allowed_inputs = (
        contract.get(
            "stage_9_1_1",
            {}
        ).get(
            "allowed_inputs",
            {}
        )
    )

    if not allowed_inputs:

        raise RuntimeError(
            "Stage 9.1 allowed-input contract missing."
        )

    for name, item in allowed_inputs.items():

        old_sha = item.pop(
            "sha256",
            None,
        )

        if (
            old_sha
            and
            "observed_sha256_at_contract_creation"
            not in item
        ):

            item[
                "observed_sha256_at_contract_creation"
            ] = old_sha

        item[
            "dependency_hash_policy"
        ] = POLICY

        item[
            "contract_runtime_hash_pin"
        ] = False

        item[
            "downstream_snapshot_hash_required"
        ] = True

        item[
            "runtime_content_may_change"
        ] = True

    freshness = (
        contract.get(
            "stage_9_1_4",
            {}
        ).get(
            "freshness_contract",
            {}
        )
    )

    freshness[
        "dependency_hash_anchor"
    ] = "DOWNSTREAM_STAGE_BUILD_REPORT"

    freshness[
        "contract_creation_hash_is_runtime_freshness_anchor"
    ] = False

    freshness[
        "current_dependency_hash_must_match_downstream_build_report"
    ] = True

    freshness[
        "dependency_change_requires_downstream_rebuild"
    ] = True

    provenance = (
        contract.get(
            "stage_9_1_4",
            {}
        ).get(
            "provenance_contract",
            {}
        )
    )

    provenance[
        "downstream_build_report_captures_dependency_hashes"
    ] = True

    provenance[
        "contract_pins_dynamic_snapshot_hashes"
    ] = False

    migrated_at = (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )

    contract[
        "contract_version"
    ] = "1.2.1"

    contract[
        "dependency_snapshot_policy"
    ] = {

        "mode":
            POLICY,

        "policy_contract_is_immutable":
            True,

        "dynamic_source_content_may_refresh":
            True,

        "contract_permanently_pins_dynamic_hashes":
            False,

        "downstream_build_report_pins_snapshot_hashes":
            True,

        "changed_dependency_invalidates_existing_downstream_artifact":
            True,

        "changed_dependency_requires_downstream_rebuild":
            True,
    }

    maintenance = list(
        contract.get(
            "maintenance_history",
            []
        )
    )

    if not any(
        item.get(
            "version"
        )
        == "1.2.1"

        for item in maintenance

        if isinstance(
            item,
            dict,
        )
    ):

        maintenance.append(
            {
                "version":
                    "1.2.1",

                "applied_at_utc":
                    migrated_at,

                "type":
                    "DYNAMIC_SNAPSHOT_POLICY_FIX",

                "policy_semantics_changed":
                    False,

                "snapshot_hash_anchor_corrected":
                    True,

                "reason":
                    (
                        "Separate immutable Stage 9 policy "
                        "from refreshable Stage 7/8 snapshots."
                    ),
            }
        )

    contract[
        "maintenance_history"
    ] = maintenance

    # ========================================================
    # Write source patches first
    # ========================================================

    for path, text in (
        staged_sources.items()
    ):

        save_text_atomic(
            path,
            text,
        )

        print(
            f"Patched: {path}"
        )

    # ========================================================
    # Write migrated contract
    # ========================================================

    save_json_atomic(
        CONTRACT_FILE,
        contract,
    )

    contract_sha = sha256_file(
        CONTRACT_FILE
    )

    verification[
        "contract_version"
    ] = "1.2.1"

    verification[
        "contract_sha256"
    ] = contract_sha

    verification[
        "dependency_snapshot_policy"
    ] = "VERIFIED"

    verification[
        "dependency_snapshot_policy_mode"
    ] = POLICY

    verification[
        "permanent_dynamic_hash_pinning"
    ] = False

    verification[
        "downstream_snapshot_hashing_required"
    ] = True

    verification[
        "policy_migrated_at_utc"
    ] = migrated_at

    verification[
        "status"
    ] = "PASS"

    verification[
        "stage_9_1_complete"
    ] = True

    verification[
        "stage_9_1_status"
    ] = "COMPLETE"

    save_json_atomic(
        VERIFICATION_FILE,
        verification,
    )

    # ========================================================
    # Final migration checks
    # ========================================================

    persisted_contract = load_json(
        CONTRACT_FILE
    )

    persisted_verification = load_json(
        VERIFICATION_FILE
    )

    assert (
        persisted_contract[
            "contract_version"
        ]
        == "1.2.1"
    )

    assert (
        persisted_contract[
            "status"
        ]
        ==
        "LOCKED_MATCH_INTELLIGENCE_CONTRACT"
    )

    assert (
        persisted_contract[
            "stage_9_1_complete"
        ]
        is True
    )

    assert all(
        item.get(
            "dependency_hash_policy"
        )
        == POLICY

        for item in (
            persisted_contract[
                "stage_9_1_1"
            ][
                "allowed_inputs"
            ].values()
        )
    )

    assert all(
        item.get(
            "contract_runtime_hash_pin"
        )
        is False

        for item in (
            persisted_contract[
                "stage_9_1_1"
            ][
                "allowed_inputs"
            ].values()
        )
    )

    assert (
        persisted_verification[
            "contract_sha256"
        ]
        ==
        sha256_file(
            CONTRACT_FILE
        )
    )

    print()
    print("=" * 72)

    print(
        "STAGE 9.1 CONTRACT PATCH: PASS"
    )

    print(
        "CONTRACT VERSION: 1.2.1"
    )

    print(
        "DYNAMIC SNAPSHOT POLICY: VERIFIED"
    )

    print(
        "STAGE 9.1 REMAINS COMPLETE AND LOCKED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
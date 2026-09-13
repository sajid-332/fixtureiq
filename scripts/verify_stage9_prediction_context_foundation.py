"""
FixtureIQ Stage 9.2.1 + 9.2.2

9.2.1 Prediction Source Gate
9.2.2 Fixture Identity Reconciliation

Creates / updates:
data/processed/intelligence/
    match_intelligence_base_report.json

Does NOT create:
match_intelligence_base.csv

9.2.3 Strict Join remains pending.

Safety:
- no model loading
- no model execution
- no prediction mutation
- no Stage 7 writes
- no Stage 8 writes
- no provider fetch
- no fuzzy identity matching
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
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

from backend.services.prediction_context_join_service import (
    FixtureIdentityError,
    PredictionContextJoinService,
    PredictionSourceNotReadyError,
)


# ============================================================
# Directories
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

INTELLIGENCE_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "intelligence"
)


# ============================================================
# Stage 9 contract
# ============================================================

CONTRACT_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract.json"
)

CONTRACT_VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract_verification.json"
)


# ============================================================
# Stage 7
# ============================================================

PREDICTIONS_FILE = (
    PRODUCTION_DIR
    / "production_predictions.csv"
)

PREDICTION_METADATA_FILE = (
    PRODUCTION_DIR
    / "production_prediction_metadata.json"
)

PREDICTION_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_prediction_report.json"
)

PREDICTION_VERIFICATION_FILE = (
    PRODUCTION_DIR
    / "production_prediction_verification.json"
)

STAGE7_8_FILE = (
    PRODUCTION_DIR
    / "stage7_8_final_verification.json"
)

STAGE7_9_FILE = (
    PRODUCTION_DIR
    / "stage7_9_final_verification.json"
)


# ============================================================
# Stage 8
# ============================================================

CONTEXT_FILE = (
    CONTEXT_DIR
    / "enriched_upcoming_fixtures.csv"
)

FIXTURE_CONTEXT_REPORT_FILE = (
    CONTEXT_DIR
    / "fixture_context_report.json"
)

CONTEXT_API_VERIFICATION_FILE = (
    CONTEXT_DIR
    / "context_api_verification.json"
)

CONTEXT_RUNTIME_VERIFICATION_FILE = (
    CONTEXT_DIR
    / "context_runtime_verification.json"
)

STAGE8_FINAL_FILE = (
    CONTEXT_DIR
    / "stage8_final_verification.json"
)


# ============================================================
# Stage 9.2 output
# ============================================================

BASE_REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_base_report.json"
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


def save_json_atomic(
    path: Path,
    payload: dict,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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


def build_temp_service(
    temp_root: Path,
) -> tuple[
    PredictionContextJoinService,
    dict[str, Path],
]:

    paths = {

        "contract":
            temp_root
            / "stage9_intelligence_contract.json",

        "contract_verification":
            temp_root
            / "stage9_intelligence_contract_verification.json",

        "predictions":
            temp_root
            / "production_predictions.csv",

        "metadata":
            temp_root
            / "production_prediction_metadata.json",

        "prediction_report":
            temp_root
            / "production_prediction_report.json",

        "prediction_verification":
            temp_root
            / "production_prediction_verification.json",

        "stage7_8":
            temp_root
            / "stage7_8_final_verification.json",

        "stage7_9":
            temp_root
            / "stage7_9_final_verification.json",

        "context":
            temp_root
            / "enriched_upcoming_fixtures.csv",

        "fixture_context_report":
            temp_root
            / "fixture_context_report.json",

        "context_api_verification":
            temp_root
            / "context_api_verification.json",

        "context_runtime_verification":
            temp_root
            / "context_runtime_verification.json",

        "stage8_final":
            temp_root
            / "stage8_final_verification.json",
    }

    sources = {

        "contract":
            CONTRACT_FILE,

        "contract_verification":
            CONTRACT_VERIFICATION_FILE,

        "predictions":
            PREDICTIONS_FILE,

        "metadata":
            PREDICTION_METADATA_FILE,

        "prediction_report":
            PREDICTION_REPORT_FILE,

        "prediction_verification":
            PREDICTION_VERIFICATION_FILE,

        "stage7_8":
            STAGE7_8_FILE,

        "stage7_9":
            STAGE7_9_FILE,

        "context":
            CONTEXT_FILE,

        "fixture_context_report":
            FIXTURE_CONTEXT_REPORT_FILE,

        "context_api_verification":
            CONTEXT_API_VERIFICATION_FILE,

        "context_runtime_verification":
            CONTEXT_RUNTIME_VERIFICATION_FILE,

        "stage8_final":
            STAGE8_FINAL_FILE,
    }

    for name, source in sources.items():

        shutil.copy2(
            source,
            paths[
                name
            ],
        )

    # --------------------------------------------------------
    # The locked contract stores original hashes.
    # For negative tests we first point the copied contract
    # at the copied source hashes so the temp environment
    # begins internally valid.
    # --------------------------------------------------------

    contract = load_json(
        paths[
            "contract"
        ]
    )

    allowed_inputs = (
        contract.get(
            "stage_9_1_1",
            {}
        ).get(
            "allowed_inputs",
            {}
        )
    )

    contract_path_map = {

        "production_predictions":
            paths[
                "predictions"
            ],

        "production_prediction_metadata":
            paths[
                "metadata"
            ],

        "production_prediction_report":
            paths[
                "prediction_report"
            ],

        "production_prediction_verification":
            paths[
                "prediction_verification"
            ],

        "stage7_8_final_verification":
            paths[
                "stage7_8"
            ],

        "stage7_9_final_verification":
            paths[
                "stage7_9"
            ],

        "enriched_upcoming_fixtures":
            paths[
                "context"
            ],

        "fixture_context_report":
            paths[
                "fixture_context_report"
            ],

        "context_api_verification":
            paths[
                "context_api_verification"
            ],

        "context_runtime_verification":
            paths[
                "context_runtime_verification"
            ],

        "stage8_final_verification":
            paths[
                "stage8_final"
            ],
    }

    for name, path in contract_path_map.items():

        allowed_inputs[
            name
        ][
            "sha256"
        ] = sha256_file(
            path
        )

    save_json_atomic(
        paths[
            "contract"
        ],
        contract,
    )

    verification = load_json(
        paths[
            "contract_verification"
        ]
    )

    verification[
        "contract_sha256"
    ] = sha256_file(
        paths[
            "contract"
        ]
    )

    save_json_atomic(
        paths[
            "contract_verification"
        ],
        verification,
    )

    service = PredictionContextJoinService(

        contract_file=
            paths[
                "contract"
            ],

        contract_verification_file=
            paths[
                "contract_verification"
            ],

        predictions_file=
            paths[
                "predictions"
            ],

        prediction_metadata_file=
            paths[
                "metadata"
            ],

        prediction_report_file=
            paths[
                "prediction_report"
            ],

        prediction_verification_file=
            paths[
                "prediction_verification"
            ],

        stage7_8_file=
            paths[
                "stage7_8"
            ],

        stage7_9_file=
            paths[
                "stage7_9"
            ],

        context_file=
            paths[
                "context"
            ],

        fixture_context_report_file=
            paths[
                "fixture_context_report"
            ],

        context_api_verification_file=
            paths[
                "context_api_verification"
            ],

        context_runtime_verification_file=
            paths[
                "context_runtime_verification"
            ],

        stage8_final_file=
            paths[
                "stage8_final"
            ],
    )

    return (
        service,
        paths,
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 9.2.1 + 9.2.2"
    )

    print(
        "Prediction Source Gate + Fixture Identity Reconciliation"
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

        PREDICTIONS_FILE,
        PREDICTION_METADATA_FILE,
        PREDICTION_REPORT_FILE,
        PREDICTION_VERIFICATION_FILE,

        STAGE7_8_FILE,
        STAGE7_9_FILE,

        CONTEXT_FILE,
        FIXTURE_CONTEXT_REPORT_FILE,
        CONTEXT_API_VERIFICATION_FILE,
        CONTEXT_RUNTIME_VERIFICATION_FILE,
        STAGE8_FINAL_FILE,
    ]

    for path in required:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        sys.exit(1)

    # ========================================================
    # Protect upstream artifacts
    # ========================================================

    protected_before = {

        relative_path(
            path
        ):
            sha256_file(
                path
            )

        for path in required
    }

    # ========================================================
    # 2. Locked Stage 9.1 foundation
    # ========================================================

    print(
        "\n2. LOCKED STAGE 9.1 FOUNDATION"
    )

    contract = load_json(
        CONTRACT_FILE
    )

    contract_verification = load_json(
        CONTRACT_VERIFICATION_FILE
    )

    check(
        "Stage 9.1 contract LOCKED",
        contract.get(
            "status"
        )
        ==
        "LOCKED_MATCH_INTELLIGENCE_CONTRACT",
        failures,
    )

    check(
        "Stage 9.1 COMPLETE",
        contract.get(
            "stage_9_1_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 9.1 verification PASS",
        contract_verification.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 9 ready for 9.2",
        contract_verification.get(
            "final_gate",
            {}
        ).get(
            "stage9_ready_for_9_2"
        )
        is True,
        failures,
    )

    # ========================================================
    # 3. Stage 9.2.1 Prediction Source Gate
    # ========================================================

    print(
        "\n3. STAGE 9.2.1 PREDICTION SOURCE GATE"
    )

    service = (
        PredictionContextJoinService()
    )

    try:

        source_gate = (
            service
            .validate_prediction_source()
        )

        source_gate_ok = (
            source_gate.get(
                "status"
            )
            == "PASS"
        )

    except Exception as exc:

        print(
            "Prediction source gate error:",
            exc,
        )

        source_gate = {}
        source_gate_ok = False

    check(
        "Prediction source gate PASS",
        source_gate_ok,
        failures,
    )

    if source_gate_ok:

        source_gate_true_flags = [

            "fixture_id_unique",
            "required_schema_present",
            "identity_complete",
            "probabilities_valid",
            "probabilities_sum_to_one",
            "prediction_labels_present",
            "confidence_valid",
            "stage7_8_verified",
            "stage7_9_verified",
            "stage8_final_verified",
            "locked_dependency_hashes_current",
        ]

        for flag in source_gate_true_flags:

            check(
                f"{flag} = true",
                source_gate.get(
                    flag
                )
                is True,
                failures,
            )

        check(
            "Prediction count > 0",
            source_gate.get(
                "prediction_count",
                0,
            )
            > 0,
            failures,
        )

    # ========================================================
    # 4. Stage 9.2.2 Fixture Identity Reconciliation
    # ========================================================

    print(
        "\n4. STAGE 9.2.2 FIXTURE IDENTITY RECONCILIATION"
    )

    try:

        identity = (
            service
            .reconcile_fixture_identity()
        )

        identity_ok = (
            identity.get(
                "status"
            )
            == "PASS"
        )

    except Exception as exc:

        print(
            "Fixture identity reconciliation error:",
            exc,
        )

        identity = {}
        identity_ok = False

    check(
        "Fixture identity reconciliation PASS",
        identity_ok,
        failures,
    )

    if identity_ok:

        identity_true_flags = [

            "fixture_sets_exact",
            "fixture_id_unique_prediction",
            "fixture_id_unique_context",
            "fixture_id_exact_match",
            "home_team_id_exact_match",
            "home_team_name_exact_match",
            "away_team_id_exact_match",
            "away_team_name_exact_match",
            "season_exact_match_if_shared",
        ]

        for flag in identity_true_flags:

            check(
                f"{flag} = true",
                identity.get(
                    flag
                )
                is True,
                failures,
            )

        check(
            "Prediction/context fixture counts equal",
            identity.get(
                "prediction_fixture_count"
            )
            ==
            identity.get(
                "context_fixture_count"
            ),
            failures,
        )

        check(
            "Unmatched prediction count = 0",
            identity.get(
                "unmatched_prediction_count"
            )
            == 0,
            failures,
        )

        check(
            "Unmatched context count = 0",
            identity.get(
                "unmatched_context_count"
            )
            == 0,
            failures,
        )

        check(
            "Identity mismatch count = 0",
            identity.get(
                "identity_mismatch_count"
            )
            == 0,
            failures,
        )

        check(
            "Fuzzy matching not used",
            identity.get(
                "fuzzy_matching_used"
            )
            is False,
            failures,
        )

        check(
            "Best-effort fallback not used",
            identity.get(
                "best_effort_fallback_used"
            )
            is False,
            failures,
        )

    # ========================================================
    # 5. Negative test: prediction dependency mutation
    # ========================================================

    print(
        "\n5. NEGATIVE TEST - PREDICTION DEPENDENCY MUTATION"
    )

    with tempfile.TemporaryDirectory() as temp_dir:

        temp_root = Path(
            temp_dir
        )

        (
            temp_service,
            temp_paths,
        ) = build_temp_service(
            temp_root
        )

        baseline_temp_gate = (
            temp_service
            .validate_prediction_source()
        )

        check(
            "Temporary baseline prediction gate PASS",
            baseline_temp_gate.get(
                "status"
            )
            == "PASS",
            failures,
        )

        with temp_paths[
            "predictions"
        ].open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                "\n"
            )

        prediction_mutation_rejected = False

        try:

            temp_service.validate_prediction_source()

        except PredictionSourceNotReadyError:

            prediction_mutation_rejected = True

        except Exception:

            # Locked hash invalidation may fail even earlier,
            # which is also valid fail-closed behavior.
            prediction_mutation_rejected = True

        check(
            "Prediction dependency mutation rejected",
            prediction_mutation_rejected,
            failures,
        )

    # ========================================================
    # 6. Negative test: identity mismatch
    # ========================================================

    print(
        "\n6. NEGATIVE TEST - FIXTURE IDENTITY MISMATCH"
    )

    with tempfile.TemporaryDirectory() as temp_dir:

        temp_root = Path(
            temp_dir
        )

        (
            temp_service,
            temp_paths,
        ) = build_temp_service(
            temp_root
        )

        # Modify only one canonical team-name value.
        # Then update the copied contract context hash so the
        # test reaches identity reconciliation rather than
        # stopping at dependency-hash validation.

        context_path = temp_paths[
            "context"
        ]

        text = context_path.read_text(
            encoding="utf-8-sig"
        )

        lines = text.splitlines()

        check(
            "Temporary context has data rows",
            len(
                lines
            )
            > 1,
            failures,
        )

        if (
            len(
                lines
            )
            > 1
        ):

            import csv
            import io

            reader = csv.DictReader(
                io.StringIO(
                    text
                )
            )

            fieldnames = list(
                reader.fieldnames
                or []
            )

            rows = list(
                reader
            )

            rows[
                0
            ][
                "home_team_name"
            ] = (
                rows[
                    0
                ][
                    "home_team_name"
                ]
                + "__MISMATCH"
            )

            with context_path.open(
                "w",
                encoding="utf-8",
                newline="",
            ) as file:

                writer = csv.DictWriter(
                    file,
                    fieldnames=
                        fieldnames,
                )

                writer.writeheader()

                writer.writerows(
                    rows
                )

            temp_contract = load_json(
                temp_paths[
                    "contract"
                ]
            )

            temp_contract[
                "stage_9_1_1"
            ][
                "allowed_inputs"
            ][
                "enriched_upcoming_fixtures"
            ][
                "sha256"
            ] = sha256_file(
                context_path
            )

            save_json_atomic(
                temp_paths[
                    "contract"
                ],
                temp_contract,
            )

            temp_verification = load_json(
                temp_paths[
                    "contract_verification"
                ]
            )

            temp_verification[
                "contract_sha256"
            ] = sha256_file(
                temp_paths[
                    "contract"
                ]
            )

            save_json_atomic(
                temp_paths[
                    "contract_verification"
                ],
                temp_verification,
            )

            identity_mismatch_rejected = False

            try:

                temp_service.reconcile_fixture_identity()

            except FixtureIdentityError:

                identity_mismatch_rejected = True

            check(
                "Canonical identity mismatch rejected",
                identity_mismatch_rejected,
                failures,
            )

    # ========================================================
    # 7. Negative test: unmatched fixture
    # ========================================================

    print(
        "\n7. NEGATIVE TEST - UNMATCHED FIXTURE"
    )

    with tempfile.TemporaryDirectory() as temp_dir:

        temp_root = Path(
            temp_dir
        )

        (
            temp_service,
            temp_paths,
        ) = build_temp_service(
            temp_root
        )

        import csv

        context_path = temp_paths[
            "context"
        ]

        with context_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:

            reader = csv.DictReader(
                file
            )

            fieldnames = list(
                reader.fieldnames
                or []
            )

            rows = list(
                reader
            )

        check(
            "Temporary context has multiple rows",
            len(
                rows
            )
            > 1,
            failures,
        )

        if (
            len(
                rows
            )
            > 1
        ):

            rows = rows[
                1:
            ]

            with context_path.open(
                "w",
                encoding="utf-8",
                newline="",
            ) as file:

                writer = csv.DictWriter(
                    file,
                    fieldnames=
                        fieldnames,
                )

                writer.writeheader()

                writer.writerows(
                    rows
                )

            temp_contract = load_json(
                temp_paths[
                    "contract"
                ]
            )

            temp_contract[
                "stage_9_1_1"
            ][
                "allowed_inputs"
            ][
                "enriched_upcoming_fixtures"
            ][
                "sha256"
            ] = sha256_file(
                context_path
            )

            save_json_atomic(
                temp_paths[
                    "contract"
                ],
                temp_contract,
            )

            temp_verification = load_json(
                temp_paths[
                    "contract_verification"
                ]
            )

            temp_verification[
                "contract_sha256"
            ] = sha256_file(
                temp_paths[
                    "contract"
                ]
            )

            save_json_atomic(
                temp_paths[
                    "contract_verification"
                ],
                temp_verification,
            )

            unmatched_rejected = False

            try:

                temp_service.reconcile_fixture_identity()

            except FixtureIdentityError:

                unmatched_rejected = True

            check(
                "Unmatched fixture rejected",
                unmatched_rejected,
                failures,
            )

    # ========================================================
    # 8. Upstream write protection
    # ========================================================

    print(
        "\n8. UPSTREAM WRITE PROTECTION"
    )

    for path in required:

        path_key = relative_path(
            path
        )

        check(
            f"{path.name} unchanged",
            sha256_file(
                path
            )
            ==
            protected_before[
                path_key
            ],
            failures,
        )

    # ========================================================
    # 9. Persist partial Stage 9.2 report
    # ========================================================

    print(
        "\n9. SAVE STAGE 9.2 PARTIAL REPORT"
    )

    overall_pass = (
        len(
            failures
        )
        == 0
    )

    if overall_pass:

        verified_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        output_contract = (
            contract.get(
                "stage_9_1_3",
                {}
            ).get(
                "output_artifact_contract",
                {}
            ).get(
                "outputs",
                {}
            )
        )

        expected_report_path = (
            output_contract.get(
                "match_intelligence_base_report",
                {}
            ).get(
                "path"
            )
        )

        check(
            "Stage 9.2 report path locked",
            expected_report_path
            ==
            relative_path(
                BASE_REPORT_FILE
            ),
            failures,
        )

        if not failures:

            report = {

                "stage":
                    "9.2",

                "status":
                    "PARTIAL_PASS",

                "stage_9_2_complete":
                    False,

                "stage_9_2_status":
                    "IN_PROGRESS",

                "verified_at_utc":
                    verified_at,

                "sub_stages": {

                    "9.2.1":
                        "PASS",

                    "9.2.2":
                        "PASS",

                    "9.2.3":
                        "PENDING",

                    "9.2.4":
                        "PENDING",

                    "9.2.5":
                        "PENDING",
                },

                "prediction_source_gate":
                    "VERIFIED",

                "fixture_identity_reconciliation":
                    "VERIFIED",

                "prediction_source": {

                    "path":
                        relative_path(
                            PREDICTIONS_FILE
                        ),

                    "sha256":
                        sha256_file(
                            PREDICTIONS_FILE
                        ),

                    "fixture_count":
                        source_gate.get(
                            "prediction_count"
                        ),

                    "fixture_id_unique":
                        True,

                    "probabilities_valid":
                        True,

                    "probabilities_sum_to_one":
                        True,

                    "prediction_labels_present":
                        True,

                    "confidence_valid":
                        True,
                },

                "context_source": {

                    "path":
                        relative_path(
                            CONTEXT_FILE
                        ),

                    "sha256":
                        sha256_file(
                            CONTEXT_FILE
                        ),

                    "fixture_count":
                        identity.get(
                            "context_fixture_count"
                        ),
                },

                "identity_reconciliation": {

                    "status":
                        "VERIFIED",

                    "fixture_sets_exact":
                        True,

                    "fixture_count":
                        identity.get(
                            "prediction_fixture_count"
                        ),

                    "fixture_id_exact_match":
                        True,

                    "home_team_id_exact_match":
                        True,

                    "home_team_name_exact_match":
                        True,

                    "away_team_id_exact_match":
                        True,

                    "away_team_name_exact_match":
                        True,

                    "season_exact_match_if_shared":
                        True,

                    "shared_date_field":
                        identity.get(
                            "shared_date_field"
                        ),

                    "shared_date_field_exact_match":
                        identity.get(
                            "shared_date_field_exact_match"
                        ),

                    "unmatched_prediction_count":
                        0,

                    "unmatched_context_count":
                        0,

                    "identity_mismatch_count":
                        0,

                    "fuzzy_matching_used":
                        False,

                    "best_effort_fallback_used":
                        False,
                },

                "negative_tests": {

                    "prediction_dependency_mutation_rejected":
                        True,

                    "identity_mismatch_rejected":
                        True,

                    "unmatched_fixture_rejected":
                        True,
                },

                "dependency_identity": {

                    "stage9_intelligence_contract": {

                        "path":
                            relative_path(
                                CONTRACT_FILE
                            ),

                        "sha256":
                            sha256_file(
                                CONTRACT_FILE
                            ),
                    },

                    "stage9_intelligence_contract_verification": {

                        "path":
                            relative_path(
                                CONTRACT_VERIFICATION_FILE
                            ),

                        "sha256":
                            sha256_file(
                                CONTRACT_VERIFICATION_FILE
                            ),
                    },

                    "production_predictions": {

                        "path":
                            relative_path(
                                PREDICTIONS_FILE
                            ),

                        "sha256":
                            sha256_file(
                                PREDICTIONS_FILE
                            ),
                    },

                    "enriched_upcoming_fixtures": {

                        "path":
                            relative_path(
                                CONTEXT_FILE
                            ),

                        "sha256":
                            sha256_file(
                                CONTEXT_FILE
                            ),
                    },

                    "stage7_8_final_verification": {

                        "path":
                            relative_path(
                                STAGE7_8_FILE
                            ),

                        "sha256":
                            sha256_file(
                                STAGE7_8_FILE
                            ),
                    },

                    "stage7_9_final_verification": {

                        "path":
                            relative_path(
                                STAGE7_9_FILE
                            ),

                        "sha256":
                            sha256_file(
                                STAGE7_9_FILE
                            ),
                    },

                    "stage8_final_verification": {

                        "path":
                            relative_path(
                                STAGE8_FINAL_FILE
                            ),

                        "sha256":
                            sha256_file(
                                STAGE8_FINAL_FILE
                            ),
                    },
                },

                "safety": {

                    "read_only_upstream":
                        True,

                    "interpretation_only":
                        True,

                    "provider_fetch_performed":
                        False,

                    "model_loaded":
                        False,

                    "model_executed":
                        False,

                    "model_modified":
                        False,

                    "probabilities_modified":
                        False,

                    "probabilities_recalibrated":
                        False,

                    "prediction_labels_modified":
                        False,

                    "stage7_artifacts_modified":
                        False,

                    "stage8_artifacts_modified":
                        False,

                    "fuzzy_matching_used":
                        False,

                    "best_effort_identity_fallback_used":
                        False,

                    "final_test_accessed":
                        False,
                },

                "failures":
                    [],
            }

            save_json_atomic(
                BASE_REPORT_FILE,
                report,
            )

            print(
                BASE_REPORT_FILE
            )

            persisted = load_json(
                BASE_REPORT_FILE
            )

            check(
                "Stage 9.2 report PARTIAL_PASS persisted",
                persisted.get(
                    "status"
                )
                == "PARTIAL_PASS",
                failures,
            )

            check(
                "9.2.1 PASS persisted",
                persisted.get(
                    "sub_stages",
                    {}
                ).get(
                    "9.2.1"
                )
                == "PASS",
                failures,
            )

            check(
                "9.2.2 PASS persisted",
                persisted.get(
                    "sub_stages",
                    {}
                ).get(
                    "9.2.2"
                )
                == "PASS",
                failures,
            )

            check(
                "9.2.3 remains PENDING",
                persisted.get(
                    "sub_stages",
                    {}
                ).get(
                    "9.2.3"
                )
                == "PENDING",
                failures,
            )

            check(
                "Prediction source gate VERIFIED persisted",
                persisted.get(
                    "prediction_source_gate"
                )
                == "VERIFIED",
                failures,
            )

            check(
                "Fixture identity reconciliation VERIFIED persisted",
                persisted.get(
                    "fixture_identity_reconciliation"
                )
                == "VERIFIED",
                failures,
            )

            overall_pass = (
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

    if overall_pass:

        print(
            "STAGE 9.2.1: PASS"
        )

        print(
            "PREDICTION SOURCE GATE: VERIFIED"
        )

        print(
            "STAGE 9.2.2: PASS"
        )

        print(
            "FIXTURE IDENTITY RECONCILIATION: VERIFIED"
        )

        print(
            "STAGE 9.2: IN PROGRESS"
        )

    else:

        print(
            "STAGE 9.2.1 / 9.2.2: FAIL"
        )

        print(
            "STAGE 9.2: INCOMPLETE"
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
"""
FixtureIQ Stage 9.7
Runtime-Safe Match Intelligence Service.

Runtime policy:
DUAL_UPSTREAM_DEPENDENCY_PLUS_TEMPORAL_BOUNDARY

Every public read revalidates:
- locked Stage 9.1 policy
- Stage 9.2 dynamic dependency identity
- Stage 7 final verification artifacts
- Stage 8 final/runtime verification artifacts
- current FixtureContextService readiness
- Stage 9.3/9.4/9.5 artifact integrity
- Stage 9.6 API verification

No stale fallback.
No artifact rebuilding.
No provider fetch.
No model loading/execution.
No in-memory stale cache.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Callable

from backend.services.fixture_context_service import (
    FixtureContextService,
)


# ============================================================
# Paths
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
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

CONTRACT_VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract_verification.json"
)

BASE_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_base.csv"
)

BASE_REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_base_report.json"
)

INTELLIGENCE_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence.csv"
)

REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_report.json"
)

API_VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "intelligence_api_verification.json"
)


# ============================================================
# Errors
# ============================================================

class MatchIntelligenceNotReadyError(
    RuntimeError
):
    pass


class MatchIntelligenceNotFoundError(
    LookupError
):
    pass


# ============================================================
# Public fields
# ============================================================

PUBLIC_CORE_FIELDS = [

    "fixture_id",

    "home_team_id",
    "home_team_name",

    "away_team_id",
    "away_team_name",
]


DATE_FIELD_CANDIDATES = [

    "date",
    "kickoff_utc",
    "utc_date",
    "kickoff",
    "match_date",
]


PUBLIC_OPTIONAL_CONTEXT_FIELDS = [

    "season",

    "home_team_position",
    "away_team_position",

    "home_team_points",
    "away_team_points",

    "home_team_goal_difference",
    "away_team_goal_difference",

    "home_team_recent_points",
    "away_team_recent_points",

    "home_team_recent_goal_difference",
    "away_team_recent_goal_difference",

    "home_team_home_recent_points",
    "away_team_away_recent_points",

    "home_team_home_form_matches_available",
    "away_team_away_form_matches_available",
]


PUBLIC_STAGE7_FIELDS = [

    "stage7_prob_home_win",
    "stage7_prob_draw",
    "stage7_prob_away_win",

    "stage7_predicted_label",
    "stage7_confidence",
]


PUBLIC_STAGE9_FIELDS = [

    "stage9_top_probability",
    "stage9_second_probability",
    "stage9_probability_margin",

    "stage9_entropy",
    "stage9_normalized_entropy",

    "stage9_confidence_band",
    "stage9_uncertainty_band",

    "stage9_league_position_gap",
    "stage9_points_gap",
    "stage9_goal_difference_gap",

    "stage9_recent_points_gap",
    "stage9_recent_goal_difference_gap",

    "stage9_venue_form_points_gap",

    "stage9_context_support_score",
    "stage9_context_alignment",

    "stage9_explanation_headline",
    "stage9_explanation_summary",
]


# ============================================================
# Helpers
# ============================================================

def _load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise MatchIntelligenceNotReadyError(
            f"Required artifact missing: {path}"
        )

    try:

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            payload = json.load(
                file
            )

    except Exception as exc:

        raise MatchIntelligenceNotReadyError(
            f"Could not read JSON artifact: {path}"
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):

        raise MatchIntelligenceNotReadyError(
            f"Expected JSON object: {path}"
        )

    return payload


def _load_csv(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:

    if not path.exists():

        raise MatchIntelligenceNotReadyError(
            f"Required artifact missing: {path}"
        )

    try:

        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:

            reader = csv.DictReader(
                file
            )

            fields = list(
                reader.fieldnames
                or []
            )

            rows = [
                dict(row)
                for row in reader
            ]

    except Exception as exc:

        raise MatchIntelligenceNotReadyError(
            f"Could not read CSV artifact: {path}"
        ) from exc

    if not fields:

        raise MatchIntelligenceNotReadyError(
            "Match intelligence CSV has no columns."
        )

    if not rows:

        raise MatchIntelligenceNotReadyError(
            "Match intelligence CSV has no rows."
        )

    return (
        fields,
        rows,
    )


def _sha256_file(
    path: Path,
) -> str:

    if not path.exists():

        raise MatchIntelligenceNotReadyError(
            f"Required artifact missing: {path}"
        )

    digest = hashlib.sha256()

    try:

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

    except Exception as exc:

        raise MatchIntelligenceNotReadyError(
            f"Could not hash artifact: {path}"
        ) from exc

    return digest.hexdigest()


def _normalize_lookup(
    value: str,
) -> str:

    return (
        str(
            value
        )
        .strip()
        .casefold()
    )


def _normalize_contract_path(
    value: str,
) -> str:

    return (
        str(
            value
        )
        .replace(
            "\\",
            "/",
        )
        .lstrip(
            "./"
        )
    )


def _resolve_project_path(
    value: str,
) -> Path:

    raw = Path(
        str(
            value
        )
    )

    if raw.is_absolute():

        candidate = raw.resolve()

    else:

        candidate = (
            BASE_DIR
            / raw
        ).resolve()

    project_root = BASE_DIR.resolve()

    try:

        candidate.relative_to(
            project_root
        )

    except ValueError as exc:

        raise MatchIntelligenceNotReadyError(
            (
                "Dependency path escapes "
                "FixtureIQ project root."
            )
        ) from exc

    return candidate


# ============================================================
# Runtime-safe service
# ============================================================

class MatchIntelligenceService:

    def __init__(
        self,
        *,
        contract_file: Path = CONTRACT_FILE,
        contract_verification_file: Path = CONTRACT_VERIFICATION_FILE,
        base_file: Path = BASE_FILE,
        base_report_file: Path = BASE_REPORT_FILE,
        intelligence_file: Path = INTELLIGENCE_FILE,
        report_file: Path = REPORT_FILE,
        api_verification_file: Path = API_VERIFICATION_FILE,
        fixture_context_service_factory: Callable | None = None,
    ) -> None:

        self.contract_file = Path(
            contract_file
        )

        self.contract_verification_file = Path(
            contract_verification_file
        )

        self.base_file = Path(
            base_file
        )

        self.base_report_file = Path(
            base_report_file
        )

        self.intelligence_file = Path(
            intelligence_file
        )

        self.report_file = Path(
            report_file
        )

        self.api_verification_file = Path(
            api_verification_file
        )

        self.fixture_context_service_factory = (
            fixture_context_service_factory
            or
            FixtureContextService
        )

    # ========================================================
    # Stage 9.2 dynamic source freshness
    # ========================================================

    def _validate_stage9_2_dependencies(
        self,
        contract: dict,
        base_report: dict,
    ) -> dict[str, Path]:

        allowed_inputs = (
            contract.get(
                "stage_9_1_1",
                {}
            ).get(
                "allowed_inputs",
                {}
            )
        )

        if not isinstance(
            allowed_inputs,
            dict,
        ) or not allowed_inputs:

            raise MatchIntelligenceNotReadyError(
                "Stage 9.1 allowed-input contract missing."
            )

        dependency_identity = (
            base_report.get(
                "dependency_identity",
                {}
            )
        )

        if not isinstance(
            dependency_identity,
            dict,
        ):

            raise MatchIntelligenceNotReadyError(
                (
                    "Stage 9.2 dependency identity "
                    "is missing."
                )
            )

        # Stage 9.2 records the 11 dynamic Stage 7/8
        # inputs declared by Stage 9.1, plus its two immutable
        # Stage 9.1 foundation artifacts.
        #
        # The dynamic source set must remain exact. The two
        # Stage 9.1 artifacts are legitimate internal
        # dependencies, not additional production inputs.

        expected_dependency_names = (
            set(
                allowed_inputs
            )
            |
            {
                "stage9_intelligence_contract",
                "stage9_intelligence_contract_verification",
            }
        )

        if (
            set(
                dependency_identity
            )
            !=
            expected_dependency_names
        ):

            raise MatchIntelligenceNotReadyError(
                (
                    "Stage 9.2 dependency set no longer "
                    "matches the locked Stage 9 foundation."
                )
            )

        resolved = {}

        for name, contract_item in (
            allowed_inputs.items()
        ):

            report_item = dependency_identity.get(
                name
            )

            if not isinstance(
                report_item,
                dict,
            ):

                raise MatchIntelligenceNotReadyError(
                    (
                        "Missing Stage 9.2 dependency "
                        f"identity for {name}."
                    )
                )

            contract_path = str(
                contract_item.get(
                    "path",
                    "",
                )
            ).strip()

            report_path = str(
                report_item.get(
                    "path",
                    "",
                )
            ).strip()

            if not contract_path:

                raise MatchIntelligenceNotReadyError(
                    (
                        "Missing locked dependency path "
                        f"for {name}."
                    )
                )

            if (
                _normalize_contract_path(
                    contract_path
                )
                !=
                _normalize_contract_path(
                    report_path
                )
            ):

                raise MatchIntelligenceNotReadyError(
                    (
                        "Stage 9.2 dependency path changed: "
                        f"{name}"
                    )
                )

            if (
                contract_item.get(
                    "dependency_hash_policy"
                )
                !=
                "CAPTURE_AT_DOWNSTREAM_BUILD"
            ):

                raise MatchIntelligenceNotReadyError(
                    (
                        "Invalid Stage 9 dependency "
                        f"hash policy for {name}."
                    )
                )

            if (
                contract_item.get(
                    "contract_runtime_hash_pin"
                )
                is not False
            ):

                raise MatchIntelligenceNotReadyError(
                    (
                        "Permanent runtime hash pin "
                        f"incorrectly enabled for {name}."
                    )
                )

            source_path = (
                _resolve_project_path(
                    contract_path
                )
            )

            expected_sha = str(
                report_item.get(
                    "sha256",
                    "",
                )
            ).strip()

            if not expected_sha:

                raise MatchIntelligenceNotReadyError(
                    (
                        "Stage 9.2 snapshot SHA missing "
                        f"for {name}."
                    )
                )

            current_sha = _sha256_file(
                source_path
            )

            if (
                current_sha
                !=
                expected_sha
            ):

                raise MatchIntelligenceNotReadyError(
                    (
                        "Stage 9.2 dependency changed "
                        f"after intelligence build: {name}"
                    )
                )

            resolved[
                name
            ] = source_path

        return resolved

    # ========================================================
    # Stage 7 / Stage 8 evidence
    # ========================================================

    @staticmethod
    def _validate_upstream_verification_evidence(
        dependency_paths: dict[str, Path],
    ) -> None:

        required_pass_artifacts = [

            "production_prediction_verification",
            "stage7_8_final_verification",
            "stage7_9_final_verification",

            "context_runtime_verification",
            "stage8_final_verification",
        ]

        for name in required_pass_artifacts:

            path = dependency_paths.get(
                name
            )

            if path is None:

                raise MatchIntelligenceNotReadyError(
                    (
                        "Required upstream verification "
                        f"dependency missing: {name}"
                    )
                )

            payload = _load_json(
                path
            )

            if (
                payload.get(
                    "status"
                )
                != "PASS"
            ):

                raise MatchIntelligenceNotReadyError(
                    (
                        "Upstream verification is not PASS: "
                        f"{name}"
                    )
                )

    # ========================================================
    # Current Stage 8 temporal readiness
    # ========================================================

    def _validate_fixture_context_runtime(
        self,
    ) -> dict:

        try:

            context_service = (
                self.fixture_context_service_factory()
            )

            status = (
                context_service.get_status()
            )

        except Exception as exc:

            raise MatchIntelligenceNotReadyError(
                (
                    "Could not determine current "
                    "FixtureContextService readiness."
                )
            ) from exc

        if not isinstance(
            status,
            dict,
        ):

            raise MatchIntelligenceNotReadyError(
                (
                    "FixtureContextService returned "
                    "invalid readiness state."
                )
            )

        if (
            status.get(
                "status"
            )
            != "READY"
        ):

            reason = str(
                status.get(
                    "reason",
                    "unknown reason",
                )
            )

            raise MatchIntelligenceNotReadyError(
                (
                    "Upstream FixtureContextService "
                    f"NOT_READY: {reason}"
                )
            )

        return status

    # ========================================================
    # Stage 9 downstream dependency identity
    # ========================================================

    def _validate_stage9_dependency_chain(
        self,
        report: dict,
    ) -> None:

        dependency_identity = (
            report.get(
                "dependency_identity",
                {}
            )
        )

        if not isinstance(
            dependency_identity,
            dict,
        ):

            raise MatchIntelligenceNotReadyError(
                (
                    "Match intelligence dependency "
                    "identity missing."
                )
            )

        expected_dependencies = {

            "stage9_intelligence_contract":
                self.contract_file,

            "stage9_intelligence_contract_verification":
                self.contract_verification_file,

            "match_intelligence_base":
                self.base_file,

            "match_intelligence_base_report":
                self.base_report_file,
        }

        for name, path in (
            expected_dependencies.items()
        ):

            item = dependency_identity.get(
                name
            )

            if not isinstance(
                item,
                dict,
            ):

                raise MatchIntelligenceNotReadyError(
                    (
                        "Stage 9 dependency identity "
                        f"missing: {name}"
                    )
                )

            expected_sha = str(
                item.get(
                    "sha256",
                    "",
                )
            ).strip()

            if not expected_sha:

                raise MatchIntelligenceNotReadyError(
                    (
                        "Stage 9 dependency SHA "
                        f"missing: {name}"
                    )
                )

            if (
                _sha256_file(
                    path
                )
                !=
                expected_sha
            ):

                raise MatchIntelligenceNotReadyError(
                    (
                        "Stage 9 dependency changed: "
                        f"{name}"
                    )
                )

    # ========================================================
    # Complete runtime validation
    # ========================================================

    def _validate(
        self,
    ) -> dict:

        # Every call starts from disk.
        # There is intentionally no stale in-memory fallback.

        contract = _load_json(
            self.contract_file
        )

        contract_verification = _load_json(
            self.contract_verification_file
        )

        base_report = _load_json(
            self.base_report_file
        )

        report = _load_json(
            self.report_file
        )

        api_verification = _load_json(
            self.api_verification_file
        )

        # ----------------------------------------------------
        # Stage 9.1
        # ----------------------------------------------------

        if (
            contract.get(
                "status"
            )
            !=
            "LOCKED_MATCH_INTELLIGENCE_CONTRACT"
        ):

            raise MatchIntelligenceNotReadyError(
                "Stage 9.1 contract is not locked."
            )

        if (
            contract.get(
                "stage_9_1_complete"
            )
            is not True
        ):

            raise MatchIntelligenceNotReadyError(
                "Stage 9.1 is incomplete."
            )

        if (
            contract_verification.get(
                "status"
            )
            != "PASS"
        ):

            raise MatchIntelligenceNotReadyError(
                "Stage 9.1 verification is not PASS."
            )

        if (
            contract_verification.get(
                "contract_sha256"
            )
            !=
            _sha256_file(
                self.contract_file
            )
        ):

            raise MatchIntelligenceNotReadyError(
                "Stage 9.1 contract SHA mismatch."
            )

        # ----------------------------------------------------
        # Stage 9.2
        # ----------------------------------------------------

        if (
            base_report.get(
                "status"
            )
            != "PASS"
            or
            base_report.get(
                "stage_9_2_complete"
            )
            is not True
        ):

            raise MatchIntelligenceNotReadyError(
                "Stage 9.2 is not complete."
            )

        if (
            base_report.get(
                "prediction_context_join_layer"
            )
            != "VERIFIED"
        ):

            raise MatchIntelligenceNotReadyError(
                (
                    "Prediction-context join layer "
                    "is not VERIFIED."
                )
            )

        if (
            base_report.get(
                "base_artifact",
                {}
            ).get(
                "sha256"
            )
            !=
            _sha256_file(
                self.base_file
            )
        ):

            raise MatchIntelligenceNotReadyError(
                "Stage 9.2 base artifact changed."
            )

        dependency_paths = (
            self._validate_stage9_2_dependencies(
                contract,
                base_report,
            )
        )

        self._validate_upstream_verification_evidence(
            dependency_paths
        )

        # ----------------------------------------------------
        # Dynamic Stage 8 / temporal boundary
        # ----------------------------------------------------

        context_status = (
            self._validate_fixture_context_runtime()
        )

        # ----------------------------------------------------
        # Stage 9.3 / 9.4 / 9.5
        # ----------------------------------------------------

        if (
            report.get(
                "status"
            )
            != "PASS"
        ):

            raise MatchIntelligenceNotReadyError(
                "Match intelligence report is not PASS."
            )

        if (
            report.get(
                "stage_9_3_complete"
            )
            is not True
        ):

            raise MatchIntelligenceNotReadyError(
                "Stage 9.3 is incomplete."
            )

        if (
            report.get(
                "derived_match_intelligence"
            )
            != "VERIFIED"
        ):

            raise MatchIntelligenceNotReadyError(
                "Stage 9.3 is not VERIFIED."
            )

        if (
            report.get(
                "stage_9_4_complete"
            )
            is not True
        ):

            raise MatchIntelligenceNotReadyError(
                "Stage 9.4 is incomplete."
            )

        if (
            report.get(
                "confidence_uncertainty_layer"
            )
            != "VERIFIED"
        ):

            raise MatchIntelligenceNotReadyError(
                "Stage 9.4 is not VERIFIED."
            )

        if (
            report.get(
                "stage_9_5_complete"
            )
            is not True
        ):

            raise MatchIntelligenceNotReadyError(
                "Stage 9.5 is incomplete."
            )

        if (
            report.get(
                "match_explanation_engine"
            )
            != "VERIFIED"
        ):

            raise MatchIntelligenceNotReadyError(
                "Stage 9.5 is not VERIFIED."
            )

        if (
            report.get(
                "stage9_ready_for_9_6"
            )
            is not True
        ):

            raise MatchIntelligenceNotReadyError(
                "Stage 9.5 did not authorize Stage 9.6."
            )

        self._validate_stage9_dependency_chain(
            report
        )

        # ----------------------------------------------------
        # Stage 9.6
        # ----------------------------------------------------

        if (
            api_verification.get(
                "status"
            )
            != "PASS"
        ):

            raise MatchIntelligenceNotReadyError(
                "Stage 9.6 API verification is not PASS."
            )

        if (
            api_verification.get(
                "stage_9_6_complete"
            )
            is not True
        ):

            raise MatchIntelligenceNotReadyError(
                "Stage 9.6 is incomplete."
            )

        if (
            api_verification.get(
                "match_intelligence_rest_api"
            )
            != "VERIFIED"
        ):

            raise MatchIntelligenceNotReadyError(
                "Stage 9.6 REST API is not VERIFIED."
            )

        # ----------------------------------------------------
        # Current final artifact identity
        # ----------------------------------------------------

        if (
            report.get(
                "output_artifact",
                {}
            ).get(
                "sha256"
            )
            !=
            _sha256_file(
                self.intelligence_file
            )
        ):

            raise MatchIntelligenceNotReadyError(
                (
                    "Match intelligence artifact changed "
                    "after verification."
                )
            )

        # ----------------------------------------------------
        # Canonical final schema
        # ----------------------------------------------------

        (
            fields,
            rows,
        ) = _load_csv(
            self.intelligence_file
        )

        canonical_schema = (
            contract.get(
                "stage_9_1_3",
                {}
            ).get(
                "canonical_schema",
                {}
            )
        )

        locked_final_fields = (
            canonical_schema.get(
                "final_intelligence_schema",
                {}
            ).get(
                "fields",
                [],
            )
        )

        if (
            fields
            != locked_final_fields
        ):

            raise MatchIntelligenceNotReadyError(
                "Match intelligence schema mismatch."
            )

        required_public_fields = (
            PUBLIC_CORE_FIELDS
            +
            PUBLIC_STAGE7_FIELDS
            +
            PUBLIC_STAGE9_FIELDS
        )

        for field in required_public_fields:

            if field not in fields:

                raise MatchIntelligenceNotReadyError(
                    (
                        "Required intelligence field "
                        f"missing: {field}"
                    )
                )

        # ----------------------------------------------------
        # Fixture integrity
        # ----------------------------------------------------

        fixture_ids = []

        for row in rows:

            fixture_id = str(
                row.get(
                    "fixture_id",
                    "",
                )
            ).strip()

            if not fixture_id:

                raise MatchIntelligenceNotReadyError(
                    "Empty fixture_id."
                )

            fixture_ids.append(
                fixture_id
            )

            if not str(
                row.get(
                    "stage9_explanation_headline",
                    "",
                )
            ).strip():

                raise MatchIntelligenceNotReadyError(
                    "Empty explanation headline."
                )

            if not str(
                row.get(
                    "stage9_explanation_summary",
                    "",
                )
            ).strip():

                raise MatchIntelligenceNotReadyError(
                    "Empty explanation summary."
                )

        if (
            len(
                fixture_ids
            )
            !=
            len(
                set(
                    fixture_ids
                )
            )
        ):

            raise MatchIntelligenceNotReadyError(
                "Duplicate fixture_id."
            )

        return {

            "contract":
                contract,

            "report":
                report,

            "api_verification":
                api_verification,

            "context_status":
                context_status,

            "fields":
                fields,

            "rows":
                rows,
        }

    # ========================================================
    # Projection
    # ========================================================

    @staticmethod
    def _public_fields(
        fields: list[str],
    ) -> list[str]:

        public_fields = []

        for field in PUBLIC_CORE_FIELDS:

            if field in fields:

                public_fields.append(
                    field
                )

        for candidate in DATE_FIELD_CANDIDATES:

            if candidate in fields:

                public_fields.append(
                    candidate
                )

                break

        for field in PUBLIC_OPTIONAL_CONTEXT_FIELDS:

            if (
                field in fields
                and
                field not in public_fields
            ):

                public_fields.append(
                    field
                )

        for field in PUBLIC_STAGE7_FIELDS:

            if field in fields:

                public_fields.append(
                    field
                )

        for field in PUBLIC_STAGE9_FIELDS:

            if field in fields:

                public_fields.append(
                    field
                )

        return public_fields

    @classmethod
    def _project_row(
        cls,
        row: dict[str, str],
        fields: list[str],
    ) -> dict:

        return {

            field:
                row.get(
                    field,
                    ""
                )

            for field in cls._public_fields(
                fields
            )
        }

    # ========================================================
    # Status
    # ========================================================

    def get_status(
        self,
    ) -> dict:

        try:

            state = self._validate()

        except MatchIntelligenceNotReadyError as exc:

            return {

                "status":
                    "NOT_READY",

                "stage":
                    "9.7",

                "service":
                    "match_intelligence",

                "reason":
                    str(
                        exc
                    ),
            }

        return {

            "status":
                "READY",

            "stage":
                "9.7",

            "service":
                "match_intelligence",

            "runtime_policy":
                (
                    "DUAL_UPSTREAM_DEPENDENCY_"
                    "PLUS_TEMPORAL_BOUNDARY"
                ),

            "fixture_count":
                len(
                    state[
                        "rows"
                    ]
                ),

            "stage_9_3_complete":
                True,

            "stage_9_4_complete":
                True,

            "stage_9_5_complete":
                True,

            "stage_9_6_complete":
                True,

            "upstream_context_status":
                "READY",

            "stale_fallback":
                False,
        }

    # ========================================================
    # All matches
    # ========================================================

    def get_all_matches(
        self,
    ) -> list[dict]:

        state = self._validate()

        return [

            self._project_row(
                row,
                state[
                    "fields"
                ],
            )

            for row in state[
                "rows"
            ]
        ]

    # ========================================================
    # Fixture
    # ========================================================

    def get_match(
        self,
        fixture_id: str,
    ) -> dict:

        state = self._validate()

        requested = str(
            fixture_id
        ).strip()

        if not requested:

            raise MatchIntelligenceNotFoundError(
                "Fixture not found."
            )

        for row in state[
            "rows"
        ]:

            if (
                str(
                    row.get(
                        "fixture_id",
                        "",
                    )
                ).strip()
                ==
                requested
            ):

                return self._project_row(
                    row,
                    state[
                        "fields"
                    ],
                )

        raise MatchIntelligenceNotFoundError(
            "Fixture not found."
        )

    # ========================================================
    # Team
    # ========================================================

    def get_team_matches(
        self,
        team_name: str,
    ) -> list[dict]:

        state = self._validate()

        requested = _normalize_lookup(
            team_name
        )

        if not requested:

            raise MatchIntelligenceNotFoundError(
                "Team not found."
            )

        matches = []

        for row in state[
            "rows"
        ]:

            home_name = _normalize_lookup(
                row.get(
                    "home_team_name",
                    "",
                )
            )

            away_name = _normalize_lookup(
                row.get(
                    "away_team_name",
                    "",
                )
            )

            if (
                requested == home_name
                or
                requested == away_name
            ):

                matches.append(
                    self._project_row(
                        row,
                        state[
                            "fields"
                        ],
                    )
                )

        if not matches:

            raise MatchIntelligenceNotFoundError(
                "Team not found."
            )

        return matches

    # ========================================================
    # Upcoming
    # ========================================================

    def get_upcoming(
        self,
    ) -> list[dict]:

        # _validate() has already checked the current
        # FixtureContextService temporal boundary.
        return self.get_all_matches()
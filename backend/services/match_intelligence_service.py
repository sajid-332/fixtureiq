"""
FixtureIQ Stage 9.6
Artifact-Only Match Intelligence Service.

Reads only verified Stage 9 artifacts.

This service does NOT:
- call providers
- rebuild artifacts
- load or execute the prediction model
- alter probabilities
- alter predictions
- alter context
- generate explanations dynamically
- use final-test data

Stage 9.7 will strengthen runtime freshness / temporal validation.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


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


# ============================================================
# Public response fields
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
# Service
# ============================================================

class MatchIntelligenceService:

    def __init__(
        self,
        *,
        contract_file: Path = CONTRACT_FILE,
        contract_verification_file: Path = CONTRACT_VERIFICATION_FILE,
        base_report_file: Path = BASE_REPORT_FILE,
        intelligence_file: Path = INTELLIGENCE_FILE,
        report_file: Path = REPORT_FILE,
    ) -> None:

        self.contract_file = Path(
            contract_file
        )

        self.contract_verification_file = Path(
            contract_verification_file
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

    # ========================================================
    # Readiness
    # ========================================================

    def _validate(
        self,
    ) -> dict:

        contract = _load_json(
            self.contract_file
        )

        verification = _load_json(
            self.contract_verification_file
        )

        base_report = _load_json(
            self.base_report_file
        )

        report = _load_json(
            self.report_file
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
            verification.get(
                "status"
            )
            != "PASS"
        ):

            raise MatchIntelligenceNotReadyError(
                "Stage 9.1 verification is not PASS."
            )

        if (
            verification.get(
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
                "Stage 9.2 join layer is not VERIFIED."
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
                "Stage 9.5 explanation engine is not VERIFIED."
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

        # ----------------------------------------------------
        # Artifact SHA
        # ----------------------------------------------------

        declared_output = report.get(
            "output_artifact",
            {}
        )

        if (
            declared_output.get(
                "sha256"
            )
            !=
            _sha256_file(
                self.intelligence_file
            )
        ):

            raise MatchIntelligenceNotReadyError(
                "Match intelligence artifact SHA mismatch."
            )

        # ----------------------------------------------------
        # Canonical schema
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

        # ----------------------------------------------------
        # Required public fields
        # ----------------------------------------------------

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
                        "Required public intelligence field "
                        f"missing: {field}"
                    )
                )

        # ----------------------------------------------------
        # Fixture uniqueness
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
                    "Empty fixture_id in intelligence artifact."
                )

            fixture_ids.append(
                fixture_id
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
                "Duplicate fixture_id in intelligence artifact."
            )

        # ----------------------------------------------------
        # Complete explanation fields
        # ----------------------------------------------------

        for row in rows:

            if not str(
                row.get(
                    "stage9_explanation_headline",
                    "",
                )
            ).strip():

                raise MatchIntelligenceNotReadyError(
                    "Empty Stage 9 explanation headline."
                )

            if not str(
                row.get(
                    "stage9_explanation_summary",
                    "",
                )
            ).strip():

                raise MatchIntelligenceNotReadyError(
                    "Empty Stage 9 explanation summary."
                )

        return {

            "contract":
                contract,

            "report":
                report,

            "fields":
                fields,

            "rows":
                rows,
        }

    # ========================================================
    # Public projection
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

        public_fields = cls._public_fields(
            fields
        )

        return {

            field:
                row.get(
                    field,
                    "",
                )

            for field in public_fields
        }

    # ========================================================
    # Status
    # ========================================================

    def get_status(
        self,
    ) -> dict:

        try:

            state = self._validate()

        except MatchIntelligenceNotReadyError:

            return {

                "status":
                    "NOT_READY",

                "stage":
                    "9.6",

                "service":
                    "match_intelligence",
            }

        report = state[
            "report"
        ]

        rows = state[
            "rows"
        ]

        return {

            "status":
                "READY",

            "stage":
                "9.6",

            "service":
                "match_intelligence",

            "fixture_count":
                len(
                    rows
                ),

            "intelligence_stage":
                report.get(
                    "stage"
                ),

            "stage_9_3_complete":
                report.get(
                    "stage_9_3_complete"
                )
                is True,

            "stage_9_4_complete":
                report.get(
                    "stage_9_4_complete"
                )
                is True,

            "stage_9_5_complete":
                report.get(
                    "stage_9_5_complete"
                )
                is True,

            "derived_match_intelligence":
                report.get(
                    "derived_match_intelligence"
                ),

            "confidence_uncertainty_layer":
                report.get(
                    "confidence_uncertainty_layer"
                ),

            "match_explanation_engine":
                report.get(
                    "match_explanation_engine"
                ),
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
    # One fixture
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
    # Team fixtures
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

        known_team = False

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
                requested
                == home_name
                or
                requested
                == away_name
            ):

                known_team = True

                matches.append(
                    self._project_row(
                        row,
                        state[
                            "fields"
                        ],
                    )
                )

        if not known_team:

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

        # The Stage 9 artifact is constructed exclusively from
        # Stage 9.2's verified upcoming-fixture snapshot.
        #
        # Stage 9.7 will independently revalidate temporal
        # freshness at request time.
        return self.get_all_matches()
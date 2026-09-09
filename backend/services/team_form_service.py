"""
FixtureIQ Stage 8.3.4
Current Team Form Read Service + Dependency Freshness.

Responsibilities:
- read canonical current_team_form.csv
- validate team_form_report.json
- validate Stage 8.1 / Stage 8.2 foundation
- validate canonical 29-column form schema
- validate artifact SHA
- validate production-history dependencies
- validate semantic current-EPL team registry
- fail closed when stale or invalid
- provide read-only team-form access

Important:
- production_history changes invalidate form
- production_history_report changes invalidate form
- team registry changes invalidate form
- standings numerical changes alone do NOT invalidate form

This module does NOT:
- fetch provider data
- rebuild form
- load or execute the model
- modify Stage 7
- mutate predictions
"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path


# ============================================================
# Paths
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
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

DEFAULT_CONTRACT_FILE = (
    CONTEXT_DIR
    / "stage8_context_contract.json"
)

DEFAULT_CONTRACT_VERIFICATION_FILE = (
    CONTEXT_DIR
    / "stage8_context_contract_verification.json"
)

DEFAULT_STANDINGS_FILE = (
    CONTEXT_DIR
    / "current_standings.csv"
)

DEFAULT_STANDINGS_REPORT_FILE = (
    CONTEXT_DIR
    / "standings_report.json"
)

DEFAULT_TEAM_FORM_FILE = (
    CONTEXT_DIR
    / "current_team_form.csv"
)

DEFAULT_TEAM_FORM_REPORT_FILE = (
    CONTEXT_DIR
    / "team_form_report.json"
)

DEFAULT_HISTORY_FILE = (
    PRODUCTION_DIR
    / "production_history.csv"
)

DEFAULT_HISTORY_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_history_report.json"
)


# ============================================================
# Locked canonical schema
# ============================================================

EXPECTED_FIELDS = [

    "team_id",
    "team_name",

    "form_matches_available",
    "recent_results",
    "recent_points",
    "recent_wins",
    "recent_draws",
    "recent_losses",
    "recent_goals_for",
    "recent_goals_against",
    "recent_goal_difference",

    "home_form_matches_available",
    "home_recent_results",
    "home_recent_points",
    "home_recent_wins",
    "home_recent_draws",
    "home_recent_losses",
    "home_recent_goals_for",
    "home_recent_goals_against",
    "home_recent_goal_difference",

    "away_form_matches_available",
    "away_recent_results",
    "away_recent_points",
    "away_recent_wins",
    "away_recent_draws",
    "away_recent_losses",
    "away_recent_goals_for",
    "away_recent_goals_against",
    "away_recent_goal_difference",
]


INTEGER_FIELDS = [

    field

    for field in EXPECTED_FIELDS

    if field not in {
        "team_id",
        "team_name",
        "recent_results",
        "home_recent_results",
        "away_recent_results",
    }
]


# ============================================================
# Error
# ============================================================

class TeamFormNotReadyError(
    RuntimeError
):
    """Raised when current team form cannot be safely served."""


# ============================================================
# Helpers
# ============================================================

def _load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise TeamFormNotReadyError(
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

    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:

        raise TeamFormNotReadyError(
            f"Invalid JSON artifact: {path}"
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):

        raise TeamFormNotReadyError(
            f"Expected JSON object: {path}"
        )

    return payload


def _sha256_file(
    path: Path,
) -> str:

    if not path.exists():

        raise TeamFormNotReadyError(
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

    except OSError as exc:

        raise TeamFormNotReadyError(
            f"Could not hash artifact: {path}"
        ) from exc

    return digest.hexdigest()


def _parse_timestamp(
    value,
    field_name: str,
) -> datetime:

    if not isinstance(
        value,
        str,
    ):

        raise TeamFormNotReadyError(
            f"{field_name} missing or invalid."
        )

    text = value.strip()

    if not text:

        raise TeamFormNotReadyError(
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

        raise TeamFormNotReadyError(
            f"{field_name} is not valid ISO datetime."
        ) from exc

    if parsed.tzinfo is None:

        raise TeamFormNotReadyError(
            f"{field_name} must be timezone-aware."
        )

    return parsed


def _registry_sha256(
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


def _read_team_form(
    path: Path,
) -> list[dict]:

    if not path.exists():

        raise TeamFormNotReadyError(
            f"Team form artifact missing: {path}"
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

            fields = (
                reader.fieldnames
                or []
            )

            if (
                fields
                != EXPECTED_FIELDS
            ):

                raise TeamFormNotReadyError(
                    (
                        "Canonical team-form schema mismatch. "
                        f"Expected={EXPECTED_FIELDS}, "
                        f"actual={fields}"
                    )
                )

            raw_rows = list(
                reader
            )

    except OSError as exc:

        raise TeamFormNotReadyError(
            f"Could not read team-form artifact: {path}"
        ) from exc

    if len(
        raw_rows
    ) != 20:

        raise TeamFormNotReadyError(
            (
                "Canonical team form must contain exactly "
                f"20 teams, found {len(raw_rows)}."
            )
        )

    rows = []

    for raw in raw_rows:

        team_id = str(
            raw.get(
                "team_id",
                ""
            )
        ).strip()

        team_name = str(
            raw.get(
                "team_name",
                ""
            )
        ).strip()

        if (
            not team_id
            or
            not team_name
        ):

            raise TeamFormNotReadyError(
                "Blank canonical team identity."
            )

        row = dict(
            raw
        )

        row[
            "team_id"
        ] = team_id

        row[
            "team_name"
        ] = team_name

        try:

            for field in INTEGER_FIELDS:

                row[
                    field
                ] = int(
                    raw[
                        field
                    ]
                )

        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:

            raise TeamFormNotReadyError(
                (
                    "Invalid numerical team-form data for "
                    f"{team_name!r}."
                )
            ) from exc

        rows.append(
            row
        )

    return rows


def _validate_form_block(
    row: dict,
    *,
    matches_field: str,
    results_field: str,
    points_field: str,
    wins_field: str,
    draws_field: str,
    losses_field: str,
    gf_field: str,
    ga_field: str,
    gd_field: str,
    label: str,
) -> None:

    matches = row[
        matches_field
    ]

    results = row[
        results_field
    ]

    wins = row[
        wins_field
    ]

    draws = row[
        draws_field
    ]

    losses = row[
        losses_field
    ]

    points = row[
        points_field
    ]

    goals_for = row[
        gf_field
    ]

    goals_against = row[
        ga_field
    ]

    goal_difference = row[
        gd_field
    ]

    if not (
        0
        <= matches
        <= 5
    ):

        raise TeamFormNotReadyError(
            (
                f"{label} form window invalid for "
                f"{row['team_name']}."
            )
        )

    if len(
        results
    ) != matches:

        raise TeamFormNotReadyError(
            (
                f"{label} result length mismatch for "
                f"{row['team_name']}."
            )
        )

    if not set(
        results
    ).issubset(
        {
            "W",
            "D",
            "L",
        }
    ):

        raise TeamFormNotReadyError(
            (
                f"{label} contains invalid result symbols for "
                f"{row['team_name']}."
            )
        )

    if min(
        matches,
        wins,
        draws,
        losses,
        points,
        goals_for,
        goals_against,
    ) < 0:

        raise TeamFormNotReadyError(
            (
                f"{label} contains negative values for "
                f"{row['team_name']}."
            )
        )

    if (
        matches
        !=
        wins
        +
        draws
        +
        losses
    ):

        raise TeamFormNotReadyError(
            (
                f"{label} matches != W+D+L for "
                f"{row['team_name']}."
            )
        )

    if (
        points
        !=
        3 * wins
        +
        draws
    ):

        raise TeamFormNotReadyError(
            (
                f"{label} points arithmetic invalid for "
                f"{row['team_name']}."
            )
        )

    if (
        goal_difference
        !=
        goals_for
        -
        goals_against
    ):

        raise TeamFormNotReadyError(
            (
                f"{label} goal difference invalid for "
                f"{row['team_name']}."
            )
        )


def _validate_rows(
    rows: list[dict],
) -> None:

    team_ids = [
        row[
            "team_id"
        ]
        for row in rows
    ]

    team_names = [
        row[
            "team_name"
        ]
        for row in rows
    ]

    if len(
        set(
            team_ids
        )
    ) != 20:

        raise TeamFormNotReadyError(
            "FixtureIQ team IDs are not unique."
        )

    if len(
        {
            name.casefold()
            for name in team_names
        }
    ) != 20:

        raise TeamFormNotReadyError(
            "FixtureIQ team names are not unique."
        )

    if [
        name.casefold()
        for name in team_names
    ] != sorted(
        name.casefold()
        for name in team_names
    ):

        raise TeamFormNotReadyError(
            "Team form must be sorted by team_name ASC."
        )

    for row in rows:

        _validate_form_block(
            row,
            matches_field=
                "form_matches_available",
            results_field=
                "recent_results",
            points_field=
                "recent_points",
            wins_field=
                "recent_wins",
            draws_field=
                "recent_draws",
            losses_field=
                "recent_losses",
            gf_field=
                "recent_goals_for",
            ga_field=
                "recent_goals_against",
            gd_field=
                "recent_goal_difference",
            label="OVERALL",
        )

        _validate_form_block(
            row,
            matches_field=
                "home_form_matches_available",
            results_field=
                "home_recent_results",
            points_field=
                "home_recent_points",
            wins_field=
                "home_recent_wins",
            draws_field=
                "home_recent_draws",
            losses_field=
                "home_recent_losses",
            gf_field=
                "home_recent_goals_for",
            ga_field=
                "home_recent_goals_against",
            gd_field=
                "home_recent_goal_difference",
            label="HOME",
        )

        _validate_form_block(
            row,
            matches_field=
                "away_form_matches_available",
            results_field=
                "away_recent_results",
            points_field=
                "away_recent_points",
            wins_field=
                "away_recent_wins",
            draws_field=
                "away_recent_draws",
            losses_field=
                "away_recent_losses",
            gf_field=
                "away_recent_goals_for",
            ga_field=
                "away_recent_goals_against",
            gd_field=
                "away_recent_goal_difference",
            label="AWAY",
        )


def _read_current_standings_registry(
    path: Path,
) -> list[dict]:

    if not path.exists():

        raise TeamFormNotReadyError(
            f"Current standings artifact missing: {path}"
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

            fields = set(
                reader.fieldnames
                or []
            )

            required = {
                "team_id",
                "team_name",
            }

            if not required.issubset(
                fields
            ):

                raise TeamFormNotReadyError(
                    "Standings identity schema invalid."
                )

            rows = list(
                reader
            )

    except OSError as exc:

        raise TeamFormNotReadyError(
            "Could not read current standings registry."
        ) from exc

    if len(
        rows
    ) != 20:

        raise TeamFormNotReadyError(
            (
                "Current EPL registry must contain "
                f"20 rows, found {len(rows)}."
            )
        )

    registry = []

    seen_ids = set()
    seen_names = set()

    for row in rows:

        team_id = str(
            row.get(
                "team_id",
                ""
            )
        ).strip()

        team_name = str(
            row.get(
                "team_name",
                ""
            )
        ).strip()

        if (
            not team_id
            or
            not team_name
        ):

            raise TeamFormNotReadyError(
                "Blank standings team identity."
            )

        if team_id in seen_ids:

            raise TeamFormNotReadyError(
                "Duplicate standings team ID."
            )

        if team_name.casefold() in seen_names:

            raise TeamFormNotReadyError(
                "Duplicate standings team name."
            )

        seen_ids.add(
            team_id
        )

        seen_names.add(
            team_name.casefold()
        )

        registry.append(
            {
                "team_id":
                    team_id,

                "team_name":
                    team_name,
            }
        )

    return registry


# ============================================================
# Service
# ============================================================

class TeamFormService:

    def __init__(
        self,
        *,
        contract_file: Path | None = None,
        contract_verification_file: Path | None = None,
        standings_file: Path | None = None,
        standings_report_file: Path | None = None,
        team_form_file: Path | None = None,
        team_form_report_file: Path | None = None,
        history_file: Path | None = None,
        history_report_file: Path | None = None,
    ):

        self.contract_file = (
            Path(
                contract_file
            )
            if contract_file is not None
            else DEFAULT_CONTRACT_FILE
        )

        self.contract_verification_file = (
            Path(
                contract_verification_file
            )
            if contract_verification_file is not None
            else DEFAULT_CONTRACT_VERIFICATION_FILE
        )

        self.standings_file = (
            Path(
                standings_file
            )
            if standings_file is not None
            else DEFAULT_STANDINGS_FILE
        )

        self.standings_report_file = (
            Path(
                standings_report_file
            )
            if standings_report_file is not None
            else DEFAULT_STANDINGS_REPORT_FILE
        )

        self.team_form_file = (
            Path(
                team_form_file
            )
            if team_form_file is not None
            else DEFAULT_TEAM_FORM_FILE
        )

        self.team_form_report_file = (
            Path(
                team_form_report_file
            )
            if team_form_report_file is not None
            else DEFAULT_TEAM_FORM_REPORT_FILE
        )

        self.history_file = (
            Path(
                history_file
            )
            if history_file is not None
            else DEFAULT_HISTORY_FILE
        )

        self.history_report_file = (
            Path(
                history_report_file
            )
            if history_report_file is not None
            else DEFAULT_HISTORY_REPORT_FILE
        )

    # ========================================================
    # Validation
    # ========================================================

    def _validate(
        self,
    ) -> dict:

        contract = _load_json(
            self.contract_file
        )

        contract_verification = _load_json(
            self.contract_verification_file
        )

        standings_report = _load_json(
            self.standings_report_file
        )

        report = _load_json(
            self.team_form_report_file
        )

        # ----------------------------------------------------
        # Stage 8.1
        # ----------------------------------------------------

        if (
            contract.get(
                "stage_8_1_complete"
            )
            is not True
        ):

            raise TeamFormNotReadyError(
                "Stage 8.1 is not complete."
            )

        if (
            contract.get(
                "contract_status"
            )
            != "LOCKED_CONTEXT_CONTRACT"
        ):

            raise TeamFormNotReadyError(
                "Stage 8 context contract is not locked."
            )

        if (
            contract_verification.get(
                "status"
            )
            != "PASS"
        ):

            raise TeamFormNotReadyError(
                "Stage 8.1 verification is not PASS."
            )

        # ----------------------------------------------------
        # Stage 8.2 identity foundation
        # ----------------------------------------------------

        if (
            standings_report.get(
                "stage_8_2_complete"
            )
            is not True
        ):

            raise TeamFormNotReadyError(
                "Stage 8.2 is not complete."
            )

        if (
            standings_report.get(
                "stage_8_2_status"
            )
            != "COMPLETE"
        ):

            raise TeamFormNotReadyError(
                "Stage 8.2 status is not COMPLETE."
            )

        if (
            standings_report.get(
                "live_epl_standings_layer"
            )
            != "VERIFIED"
        ):

            raise TeamFormNotReadyError(
                "Stage 8.2 standings layer is not VERIFIED."
            )

        # ----------------------------------------------------
        # Stage 8.3 state
        # ----------------------------------------------------

        if (
            report.get(
                "stage"
            )
            != "8.3"
        ):

            raise TeamFormNotReadyError(
                "team_form_report stage mismatch."
            )

        sub_stages = report.get(
            "sub_stages",
            {}
        )

        for stage in (
            "8.3.1",
            "8.3.2",
            "8.3.3",
        ):

            if (
                sub_stages.get(
                    stage
                )
                != "PASS"
            ):

                raise TeamFormNotReadyError(
                    f"{stage} is not PASS."
                )

        if (
            report.get(
                "current_season_source_gate"
            )
            != "VERIFIED"
        ):

            raise TeamFormNotReadyError(
                "Current-season source gate not VERIFIED."
            )

        if (
            report.get(
                "overall_form_engine"
            )
            != "VERIFIED"
        ):

            raise TeamFormNotReadyError(
                "Overall form engine not VERIFIED."
            )

        if (
            report.get(
                "venue_form_engine"
            )
            != "VERIFIED"
        ):

            raise TeamFormNotReadyError(
                "Venue form engine not VERIFIED."
            )

        if (
            report.get(
                "canonical_team_form"
            )
            != "VERIFIED"
        ):

            raise TeamFormNotReadyError(
                "Canonical team form not VERIFIED."
            )

        # ----------------------------------------------------
        # Locked form policy
        # ----------------------------------------------------

        if (
            report.get(
                "season"
            )
            != 2026
        ):

            raise TeamFormNotReadyError(
                "Team-form season must be 2026."
            )

        if (
            report.get(
                "form_window"
            )
            != 5
        ):

            raise TeamFormNotReadyError(
                "Team-form window must be 5."
            )

        if (
            report.get(
                "season_scope"
            )
            != "CURRENT_PRODUCTION_SEASON_ONLY"
        ):

            raise TeamFormNotReadyError(
                "Invalid team-form season scope."
            )

        if (
            report.get(
                "allow_short_window"
            )
            is not True
        ):

            raise TeamFormNotReadyError(
                "Short form windows must be allowed."
            )

        if (
            report.get(
                "result_order"
            )
            != "OLDEST_TO_NEWEST"
        ):

            raise TeamFormNotReadyError(
                "Invalid team-form result order."
            )

        if (
            report.get(
                "most_recent_result_position"
            )
            != "RIGHTMOST"
        ):

            raise TeamFormNotReadyError(
                "Most recent result must be RIGHTMOST."
            )

        # ----------------------------------------------------
        # Provenance
        # ----------------------------------------------------

        generated_at = _parse_timestamp(
            report.get(
                "generated_at_utc"
            ),
            "generated_at_utc",
        )

        source_as_of = _parse_timestamp(
            report.get(
                "source_as_of_utc"
            ),
            "source_as_of_utc",
        )

        history_cutoff = _parse_timestamp(
            report.get(
                "history_cutoff_utc"
            ),
            "history_cutoff_utc",
        )

        if (
            source_as_of
            != history_cutoff
        ):

            raise TeamFormNotReadyError(
                (
                    "source_as_of_utc must match "
                    "history_cutoff_utc."
                )
            )

        # ----------------------------------------------------
        # Canonical artifact
        # ----------------------------------------------------

        rows = _read_team_form(
            self.team_form_file
        )

        _validate_rows(
            rows
        )

        artifact = report.get(
            "current_team_form",
            {}
        )

        actual_form_sha = _sha256_file(
            self.team_form_file
        )

        if (
            artifact.get(
                "sha256"
            )
            != actual_form_sha
        ):

            raise TeamFormNotReadyError(
                (
                    "current_team_form.csv hash does not "
                    "match team_form_report."
                )
            )

        if (
            artifact.get(
                "row_count"
            )
            != 20
        ):

            raise TeamFormNotReadyError(
                "Reported team-form row count invalid."
            )

        if (
            artifact.get(
                "column_count"
            )
            != 29
        ):

            raise TeamFormNotReadyError(
                "Reported team-form column count invalid."
            )

        if (
            artifact.get(
                "columns"
            )
            != EXPECTED_FIELDS
        ):

            raise TeamFormNotReadyError(
                "Reported team-form schema invalid."
            )

        if (
            artifact.get(
                "team_namespace"
            )
            != "fixtureiq-team"
        ):

            raise TeamFormNotReadyError(
                "Invalid FixtureIQ team namespace."
            )

        # ----------------------------------------------------
        # Dependency identity
        # ----------------------------------------------------

        dependencies = report.get(
            "dependency_identity",
            {}
        )

        contract_dependency = dependencies.get(
            "stage8_context_contract",
            {}
        )

        verification_dependency = dependencies.get(
            "stage8_context_contract_verification",
            {}
        )

        history_dependency = dependencies.get(
            "production_history",
            {}
        )

        history_report_dependency = dependencies.get(
            "production_history_report",
            {}
        )

        team_registry_dependency = dependencies.get(
            "current_epl_team_registry",
            {}
        )

        if (
            contract_dependency.get(
                "sha256"
            )
            != _sha256_file(
                self.contract_file
            )
        ):

            raise TeamFormNotReadyError(
                "Stage 8 context contract dependency changed."
            )

        if (
            verification_dependency.get(
                "sha256"
            )
            != _sha256_file(
                self.contract_verification_file
            )
        ):

            raise TeamFormNotReadyError(
                "Stage 8.1 verification dependency changed."
            )

        if (
            history_dependency.get(
                "usage"
            )
            != "CURRENT_SEASON_COMPLETED_MATCH_FORM"
        ):

            raise TeamFormNotReadyError(
                "Production-history dependency usage invalid."
            )

        if (
            history_dependency.get(
                "sha256"
            )
            != _sha256_file(
                self.history_file
            )
        ):

            raise TeamFormNotReadyError(
                (
                    "production_history.csv changed after "
                    "team-form snapshot creation."
                )
            )

        if (
            history_report_dependency.get(
                "sha256"
            )
            != _sha256_file(
                self.history_report_file
            )
        ):

            raise TeamFormNotReadyError(
                (
                    "production_history_report.json changed "
                    "after team-form snapshot creation."
                )
            )

        if (
            team_registry_dependency.get(
                "usage"
            )
            != "CANONICAL_TEAM_IDENTITY_ONLY"
        ):

            raise TeamFormNotReadyError(
                "Current EPL registry dependency usage invalid."
            )

        if (
            team_registry_dependency.get(
                "team_count"
            )
            != 20
        ):

            raise TeamFormNotReadyError(
                "Current EPL registry dependency count invalid."
            )

        # ----------------------------------------------------
        # Semantic current-team identity freshness
        #
        # We intentionally do NOT hash all standings values.
        # Points/position/GD can change without changing
        # current-team-form identity.
        # ----------------------------------------------------

        standings_registry = (
            _read_current_standings_registry(
                self.standings_file
            )
        )

        current_registry_sha = (
            _registry_sha256(
                standings_registry
            )
        )

        form_registry_sha = (
            _registry_sha256(
                rows
            )
        )

        expected_registry_sha = (
            team_registry_dependency.get(
                "semantic_sha256"
            )
        )

        if (
            expected_registry_sha
            != current_registry_sha
        ):

            raise TeamFormNotReadyError(
                (
                    "Current EPL team registry changed after "
                    "team-form snapshot creation."
                )
            )

        if (
            expected_registry_sha
            != form_registry_sha
        ):

            raise TeamFormNotReadyError(
                "Team-form registry identity mismatch."
            )

        # ----------------------------------------------------
        # Safety
        # ----------------------------------------------------

        safety = report.get(
            "safety",
            {}
        )

        if (
            safety.get(
                "context_only"
            )
            is not True
        ):

            raise TeamFormNotReadyError(
                "Team form is not marked context-only."
            )

        required_false_flags = [

            "stage7_artifacts_modified",
            "provider_fetch_performed",
            "future_matches_used",
            "previous_season_padding_used",
            "model_loaded",
            "model_executed",
            "model_modified",
            "production_predictions_modified",
            "feature_schema_modified",
            "form_used_as_model_features",
            "final_test_accessed",
        ]

        for flag in required_false_flags:

            if (
                safety.get(
                    flag
                )
                is not False
            ):

                raise TeamFormNotReadyError(
                    (
                        "Team-form safety boundary invalid: "
                        f"{flag}"
                    )
                )

        # Optional 8.3.4 persisted freshness evidence.
        freshness = report.get(
            "freshness"
        )

        if freshness is not None:

            if not isinstance(
                freshness,
                dict,
            ):

                raise TeamFormNotReadyError(
                    "Invalid freshness metadata."
                )

            if (
                freshness.get(
                    "mode"
                )
                != "DEPENDENCY_BASED"
            ):

                raise TeamFormNotReadyError(
                    "Freshness mode must be DEPENDENCY_BASED."
                )

        return {

            "rows":
                rows,

            "generated_at_utc":
                generated_at.isoformat(),

            "source_as_of_utc":
                source_as_of.isoformat(),

            "history_cutoff_utc":
                history_cutoff.isoformat(),

            "season":
                report.get(
                    "season"
                ),

            "form_window":
                report.get(
                    "form_window"
                ),

            "artifact_sha256":
                actual_form_sha,

            "team_registry_sha256":
                current_registry_sha,

            "freshness_mode":
                "DEPENDENCY_BASED",

            "dependencies_valid":
                True,

            "team_registry_valid":
                True,
        }

    # ========================================================
    # Public interface
    # ========================================================

    def get_status(
        self,
    ) -> dict:

        try:

            snapshot = self._validate()

            return {

                "status":
                    "READY",

                "stage":
                    "8.3.4",

                "service":
                    "team_form",

                "season":
                    snapshot[
                        "season"
                    ],

                "form_window":
                    snapshot[
                        "form_window"
                    ],

                "team_count":
                    len(
                        snapshot[
                            "rows"
                        ]
                    ),

                "generated_at_utc":
                    snapshot[
                        "generated_at_utc"
                    ],

                "source_as_of_utc":
                    snapshot[
                        "source_as_of_utc"
                    ],

                "history_cutoff_utc":
                    snapshot[
                        "history_cutoff_utc"
                    ],

                "freshness_mode":
                    snapshot[
                        "freshness_mode"
                    ],

                "dependencies_valid":
                    True,

                "team_registry_valid":
                    True,
            }

        except TeamFormNotReadyError as exc:

            return {

                "status":
                    "NOT_READY",

                "stage":
                    "8.3.4",

                "service":
                    "team_form",

                "reason":
                    str(
                        exc
                    ),
            }

    def get_all_team_form(
        self,
    ) -> list[dict]:

        snapshot = self._validate()

        return copy.deepcopy(
            snapshot[
                "rows"
            ]
        )

    def get_team_form(
        self,
        team_name: str,
    ) -> dict | None:

        query = str(
            team_name
        ).strip()

        if not query:

            return None

        query_key = (
            query.casefold()
        )

        rows = (
            self.get_all_team_form()
        )

        for row in rows:

            if (
                row[
                    "team_name"
                ].casefold()
                == query_key
            ):

                return copy.deepcopy(
                    row
                )

        return None
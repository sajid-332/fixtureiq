"""
FixtureIQ Stage 8.4.4
Unified Team Context Read Service + Dependency Freshness.

Responsibilities:
- read canonical team_context.csv
- validate team_context_report.json
- validate Stage 8.1 / 8.2 / 8.3 foundation
- validate exact 38-column schema
- validate standings + overall/home/away form arithmetic
- validate artifact SHA
- validate direct upstream dependency hashes
- require StandingsService READY
- require TeamFormService READY
- independently reconstruct unified context
- fail closed when stale or invalid
- provide read-only unified context access

Freshness:
- standings/form artifact change -> NOT_READY
- standings/form report change -> NOT_READY
- production-history change -> upstream TeamFormService NOT_READY
- canonical team-registry change -> upstream StandingsService NOT_READY

No provider fetch.
No model execution.
No Stage 7 writes.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

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

DEFAULT_TEAM_CONTEXT_FILE = (
    CONTEXT_DIR
    / "team_context.csv"
)

DEFAULT_TEAM_CONTEXT_REPORT_FILE = (
    CONTEXT_DIR
    / "team_context_report.json"
)

DEFAULT_UPCOMING_FIXTURES_FILE = (
    PRODUCTION_DIR
    / "upcoming_fixtures.csv"
)

DEFAULT_HISTORY_FILE = (
    PRODUCTION_DIR
    / "production_history.csv"
)

DEFAULT_HISTORY_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_history_report.json"
)


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
# Error
# ============================================================

class TeamContextNotReadyError(
    RuntimeError
):
    """Raised when unified team context cannot be safely served."""


# ============================================================
# Helpers
# ============================================================

def _load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise TeamContextNotReadyError(
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

        raise TeamContextNotReadyError(
            f"Invalid JSON artifact: {path}"
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):

        raise TeamContextNotReadyError(
            f"Expected JSON object: {path}"
        )

    return payload


def _sha256_file(
    path: Path,
) -> str:

    if not path.exists():

        raise TeamContextNotReadyError(
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

        raise TeamContextNotReadyError(
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

        raise TeamContextNotReadyError(
            f"{field_name} missing or invalid."
        )

    text = value.strip()

    if not text:

        raise TeamContextNotReadyError(
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

        raise TeamContextNotReadyError(
            f"{field_name} is not valid ISO datetime."
        ) from exc

    if parsed.tzinfo is None:

        raise TeamContextNotReadyError(
            f"{field_name} must be timezone-aware."
        )

    return parsed


def _read_context(
    path: Path,
) -> list[dict]:

    if not path.exists():

        raise TeamContextNotReadyError(
            f"team_context.csv missing: {path}"
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
                != TEAM_CONTEXT_FIELDS
            ):

                raise TeamContextNotReadyError(
                    (
                        "Canonical team-context schema mismatch. "
                        f"Expected={TEAM_CONTEXT_FIELDS}, "
                        f"actual={fields}"
                    )
                )

            raw_rows = list(
                reader
            )

    except OSError as exc:

        raise TeamContextNotReadyError(
            "Could not read team_context.csv."
        ) from exc

    if len(
        raw_rows
    ) != 20:

        raise TeamContextNotReadyError(
            (
                "Canonical team context must contain "
                f"20 teams, found {len(raw_rows)}."
            )
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

        if (
            not row[
                "team_id"
            ]
            or
            not row[
                "team_name"
            ]
        ):

            raise TeamContextNotReadyError(
                "Blank canonical team identity."
            )

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

            raise TeamContextNotReadyError(
                (
                    "Invalid numerical context data for "
                    f"{row['team_name']}."
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

        raise TeamContextNotReadyError(
            (
                f"{label} form window invalid for "
                f"{row['team_name']}."
            )
        )

    if len(
        results
    ) != matches:

        raise TeamContextNotReadyError(
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

        raise TeamContextNotReadyError(
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

        raise TeamContextNotReadyError(
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

        raise TeamContextNotReadyError(
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

        raise TeamContextNotReadyError(
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

        raise TeamContextNotReadyError(
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

        raise TeamContextNotReadyError(
            "Context team IDs are not unique."
        )

    if len(
        {
            name.casefold()
            for name in team_names
        }
    ) != 20:

        raise TeamContextNotReadyError(
            "Context team names are not unique."
        )

    if [
        name.casefold()
        for name in team_names
    ] != sorted(
        name.casefold()
        for name in team_names
    ):

        raise TeamContextNotReadyError(
            "team_context.csv is not sorted team_name ASC."
        )

    positions = [
        row[
            "position"
        ]
        for row in rows
    ]

    if sorted(
        positions
    ) != list(
        range(
            1,
            21,
        )
    ):

        raise TeamContextNotReadyError(
            "Standings positions must be unique 1..20."
        )

    for row in rows:

        # ----------------------------------------------------
        # Standings arithmetic
        # ----------------------------------------------------

        if min(
            row[
                "played"
            ],
            row[
                "won"
            ],
            row[
                "drawn"
            ],
            row[
                "lost"
            ],
            row[
                "goals_for"
            ],
            row[
                "goals_against"
            ],
            row[
                "points"
            ],
        ) < 0:

            raise TeamContextNotReadyError(
                (
                    "Negative standings value for "
                    f"{row['team_name']}."
                )
            )

        if (
            row[
                "played"
            ]
            !=
            row[
                "won"
            ]
            +
            row[
                "drawn"
            ]
            +
            row[
                "lost"
            ]
        ):

            raise TeamContextNotReadyError(
                (
                    "Standings played != W+D+L for "
                    f"{row['team_name']}."
                )
            )

        if (
            row[
                "goal_difference"
            ]
            !=
            row[
                "goals_for"
            ]
            -
            row[
                "goals_against"
            ]
        ):

            raise TeamContextNotReadyError(
                (
                    "Standings GD invalid for "
                    f"{row['team_name']}."
                )
            )

        if (
            row[
                "points"
            ]
            !=
            3
            *
            row[
                "won"
            ]
            +
            row[
                "drawn"
            ]
        ):

            raise TeamContextNotReadyError(
                (
                    "Standings points invalid for "
                    f"{row['team_name']}."
                )
            )

        # ----------------------------------------------------
        # Overall / home / away form
        # ----------------------------------------------------

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


def _reconstruct(
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

        raise TeamContextNotReadyError(
            "Upstream standings/form identities differ."
        )

    expected = []

    for team_id in standings_by_id:

        standing = (
            standings_by_id[
                team_id
            ]
        )

        form = (
            forms_by_id[
                team_id
            ]
        )

        if (
            standing[
                "team_name"
            ]
            !=
            form[
                "team_name"
            ]
        ):

            raise TeamContextNotReadyError(
                (
                    "Upstream canonical name mismatch "
                    f"for {team_id}."
                )
            )

        row = {

            "team_id":
                team_id,

            "team_name":
                standing[
                    "team_name"
                ],
        }

        for field in STANDINGS_VALUE_FIELDS:

            row[
                field
            ] = standing[
                field
            ]

        for field in FORM_VALUE_FIELDS:

            row[
                field
            ] = form[
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
# Service
# ============================================================

class TeamContextService:

    def __init__(
        self,
        *,
        contract_file: Path | None = None,
        contract_verification_file: Path | None = None,
        standings_file: Path | None = None,
        standings_report_file: Path | None = None,
        team_form_file: Path | None = None,
        team_form_report_file: Path | None = None,
        team_context_file: Path | None = None,
        team_context_report_file: Path | None = None,
        upcoming_fixtures_file: Path | None = None,
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

        self.team_context_file = (
            Path(
                team_context_file
            )
            if team_context_file is not None
            else DEFAULT_TEAM_CONTEXT_FILE
        )

        self.team_context_report_file = (
            Path(
                team_context_report_file
            )
            if team_context_report_file is not None
            else DEFAULT_TEAM_CONTEXT_REPORT_FILE
        )

        self.upcoming_fixtures_file = (
            Path(
                upcoming_fixtures_file
            )
            if upcoming_fixtures_file is not None
            else DEFAULT_UPCOMING_FIXTURES_FILE
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

        form_report = _load_json(
            self.team_form_report_file
        )

        report = _load_json(
            self.team_context_report_file
        )

        # ----------------------------------------------------
        # Stage 8.1 foundation
        # ----------------------------------------------------

        if (
            contract.get(
                "stage_8_1_complete"
            )
            is not True
        ):

            raise TeamContextNotReadyError(
                "Stage 8.1 is not complete."
            )

        if (
            contract.get(
                "contract_status"
            )
            != "LOCKED_CONTEXT_CONTRACT"
        ):

            raise TeamContextNotReadyError(
                "Stage 8 context contract is not locked."
            )

        if (
            contract_verification.get(
                "status"
            )
            != "PASS"
        ):

            raise TeamContextNotReadyError(
                "Stage 8.1 verification is not PASS."
            )

        # ----------------------------------------------------
        # Stage 8.2 / 8.3 upstream completion
        # ----------------------------------------------------

        if (
            standings_report.get(
                "stage_8_2_complete"
            )
            is not True
            or
            standings_report.get(
                "stage_8_2_status"
            )
            != "COMPLETE"
        ):

            raise TeamContextNotReadyError(
                "Stage 8.2 standings layer is not complete."
            )

        if (
            standings_report.get(
                "live_epl_standings_layer"
            )
            != "VERIFIED"
        ):

            raise TeamContextNotReadyError(
                "Stage 8.2 standings layer not VERIFIED."
            )

        if (
            form_report.get(
                "stage_8_3_complete"
            )
            is not True
            or
            form_report.get(
                "stage_8_3_status"
            )
            != "COMPLETE"
        ):

            raise TeamContextNotReadyError(
                "Stage 8.3 form layer is not complete."
            )

        if (
            form_report.get(
                "current_team_form_layer"
            )
            != "VERIFIED"
        ):

            raise TeamContextNotReadyError(
                "Stage 8.3 form layer not VERIFIED."
            )

        # ----------------------------------------------------
        # Stage 8.4 evidence
        # ----------------------------------------------------

        if (
            report.get(
                "stage"
            )
            != "8.4"
        ):

            raise TeamContextNotReadyError(
                "team_context_report stage mismatch."
            )

        sub_stages = report.get(
            "sub_stages",
            {}
        )

        for stage in (
            "8.4.1",
            "8.4.2",
            "8.4.3",
        ):

            if (
                sub_stages.get(
                    stage
                )
                != "PASS"
            ):

                raise TeamContextNotReadyError(
                    f"{stage} is not PASS."
                )

        if (
            report.get(
                "upstream_context_readiness"
            )
            != "VERIFIED"
        ):

            raise TeamContextNotReadyError(
                "Upstream readiness not VERIFIED."
            )

        if (
            report.get(
                "unified_team_context_builder"
            )
            != "VERIFIED"
        ):

            raise TeamContextNotReadyError(
                "Unified builder not VERIFIED."
            )

        if (
            report.get(
                "independent_context_validation"
            )
            != "VERIFIED"
        ):

            raise TeamContextNotReadyError(
                "Independent context validation not VERIFIED."
            )

        # ----------------------------------------------------
        # Direct artifact dependencies
        # ----------------------------------------------------

        dependencies = report.get(
            "dependency_identity",
            {}
        )

        dependency_checks = {

            "stage8_context_contract":
                self.contract_file,

            "stage8_context_contract_verification":
                self.contract_verification_file,

            "current_standings":
                self.standings_file,

            "standings_report":
                self.standings_report_file,

            "current_team_form":
                self.team_form_file,

            "team_form_report":
                self.team_form_report_file,
        }

        for (
            name,
            path,
        ) in dependency_checks.items():

            expected_sha = (
                dependencies.get(
                    name,
                    {}
                ).get(
                    "sha256"
                )
            )

            actual_sha = _sha256_file(
                path
            )

            if (
                expected_sha
                != actual_sha
            ):

                raise TeamContextNotReadyError(
                    (
                        "Unified context dependency changed: "
                        f"{name}"
                    )
                )

        # ----------------------------------------------------
        # Real upstream services
        # ----------------------------------------------------

        standings_service = StandingsService(

            contract_file=
                self.contract_file,

            contract_verification_file=
                self.contract_verification_file,

            standings_file=
                self.standings_file,

            report_file=
                self.standings_report_file,

            upcoming_fixtures_file=
                self.upcoming_fixtures_file,
        )

        form_service = TeamFormService(

            contract_file=
                self.contract_file,

            contract_verification_file=
                self.contract_verification_file,

            standings_file=
                self.standings_file,

            standings_report_file=
                self.standings_report_file,

            team_form_file=
                self.team_form_file,

            team_form_report_file=
                self.team_form_report_file,

            history_file=
                self.history_file,

            history_report_file=
                self.history_report_file,
        )

        standings_status = (
            standings_service.get_status()
        )

        form_status = (
            form_service.get_status()
        )

        if (
            standings_status.get(
                "status"
            )
            != "READY"
        ):

            raise TeamContextNotReadyError(
                (
                    "Upstream StandingsService NOT_READY: "
                    f"{standings_status.get('reason')}"
                )
            )

        if (
            form_status.get(
                "status"
            )
            != "READY"
        ):

            raise TeamContextNotReadyError(
                (
                    "Upstream TeamFormService NOT_READY: "
                    f"{form_status.get('reason')}"
                )
            )

        standings = (
            standings_service.get_standings()
        )

        forms = (
            form_service.get_all_team_form()
        )

        # ----------------------------------------------------
        # Canonical context artifact
        # ----------------------------------------------------

        rows = _read_context(
            self.team_context_file
        )

        _validate_rows(
            rows
        )

        artifact = report.get(
            "team_context",
            {}
        )

        actual_context_sha = (
            _sha256_file(
                self.team_context_file
            )
        )

        if (
            artifact.get(
                "sha256"
            )
            != actual_context_sha
        ):

            raise TeamContextNotReadyError(
                "team_context.csv hash mismatch."
            )

        if (
            artifact.get(
                "row_count"
            )
            != 20
            or
            artifact.get(
                "column_count"
            )
            != 38
        ):

            raise TeamContextNotReadyError(
                "Reported team-context dimensions invalid."
            )

        if (
            artifact.get(
                "columns"
            )
            != TEAM_CONTEXT_FIELDS
        ):

            raise TeamContextNotReadyError(
                "Reported team-context schema invalid."
            )

        if (
            artifact.get(
                "team_namespace"
            )
            != "fixtureiq-team"
        ):

            raise TeamContextNotReadyError(
                "Invalid FixtureIQ team namespace."
            )

        # ----------------------------------------------------
        # Independent reconstruction
        # ----------------------------------------------------

        expected = _reconstruct(
            standings,
            forms,
        )

        if (
            rows
            != expected
        ):

            raise TeamContextNotReadyError(
                (
                    "Canonical team context does not match "
                    "current verified upstream services."
                )
            )

        # ----------------------------------------------------
        # Join contract
        # ----------------------------------------------------

        join = report.get(
            "join",
            {}
        )

        if (
            join.get(
                "type"
            )
            != "ONE_TO_ONE"
            or
            join.get(
                "identity_match"
            )
            is not True
        ):

            raise TeamContextNotReadyError(
                "Unified team-context join contract invalid."
            )

        if any(
            join.get(
                field
            )
            != 20
            for field in (
                "standings_rows",
                "form_rows",
                "output_rows",
            )
        ):

            raise TeamContextNotReadyError(
                "Unified join cardinality evidence invalid."
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

        standings_source = _parse_timestamp(
            report.get(
                "standings_source_as_of_utc"
            ),
            "standings_source_as_of_utc",
        )

        form_source = _parse_timestamp(
            report.get(
                "form_source_as_of_utc"
            ),
            "form_source_as_of_utc",
        )

        form_cutoff = _parse_timestamp(
            report.get(
                "form_history_cutoff_utc"
            ),
            "form_history_cutoff_utc",
        )

        if (
            source_as_of
            !=
            max(
                standings_source,
                form_source,
            )
        ):

            raise TeamContextNotReadyError(
                "Unified source_as_of provenance invalid."
            )

        if (
            generated_at
            <
            source_as_of
        ):

            raise TeamContextNotReadyError(
                "generated_at predates source_as_of."
            )

        if (
            standings_source
            !=
            _parse_timestamp(
                standings_report.get(
                    "source_as_of_utc"
                ),
                "upstream standings source_as_of",
            )
        ):

            raise TeamContextNotReadyError(
                "Standings provenance mismatch."
            )

        if (
            form_source
            !=
            _parse_timestamp(
                form_report.get(
                    "source_as_of_utc"
                ),
                "upstream form source_as_of",
            )
        ):

            raise TeamContextNotReadyError(
                "Form provenance mismatch."
            )

        if (
            form_cutoff
            !=
            _parse_timestamp(
                form_report.get(
                    "history_cutoff_utc"
                ),
                "upstream form history cutoff",
            )
        ):

            raise TeamContextNotReadyError(
                "Form history-cutoff provenance mismatch."
            )

        if (
            report.get(
                "competition_code"
            )
            != "PL"
            or
            report.get(
                "season"
            )
            != 2026
        ):

            raise TeamContextNotReadyError(
                "Competition/season provenance invalid."
            )

        # ----------------------------------------------------
        # Freshness policy
        # ----------------------------------------------------

        freshness = report.get(
            "freshness",
            {}
        )

        if (
            freshness.get(
                "mode"
            )
            != "DEPENDENCY_BASED"
        ):

            raise TeamContextNotReadyError(
                "Freshness mode must be DEPENDENCY_BASED."
            )

        true_flags = [

            "current_standings_change_invalidates_context",
            "standings_report_change_invalidates_context",
            "current_team_form_change_invalidates_context",
            "team_form_report_change_invalidates_context",
            "fail_closed",
        ]

        for flag in true_flags:

            if (
                freshness.get(
                    flag
                )
                is not True
            ):

                raise TeamContextNotReadyError(
                    f"Invalid freshness flag: {flag}"
                )

        if (
            freshness.get(
                "stale_fallback_allowed"
            )
            is not False
        ):

            raise TeamContextNotReadyError(
                "Stale fallback must be prohibited."
            )

        if (
            freshness.get(
                "partial_unverified_output_allowed"
            )
            is not False
        ):

            raise TeamContextNotReadyError(
                "Partial unverified output must be prohibited."
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

            raise TeamContextNotReadyError(
                "Team context is not marked context-only."
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

            if (
                safety.get(
                    flag
                )
                is not False
            ):

                raise TeamContextNotReadyError(
                    f"Safety boundary invalid: {flag}"
                )

        return {

            "rows":
                rows,

            "season":
                2026,

            "team_count":
                20,

            "column_count":
                38,

            "generated_at_utc":
                generated_at.isoformat(),

            "source_as_of_utc":
                source_as_of.isoformat(),

            "standings_source_as_of_utc":
                standings_source.isoformat(),

            "form_source_as_of_utc":
                form_source.isoformat(),

            "form_history_cutoff_utc":
                form_cutoff.isoformat(),

            "artifact_sha256":
                actual_context_sha,

            "freshness_mode":
                "DEPENDENCY_BASED",

            "dependencies_valid":
                True,

            "upstream_services_ready":
                True,

            "independent_reconstruction_valid":
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
                    "8.4.4",

                "service":
                    "team_context",

                "season":
                    snapshot[
                        "season"
                    ],

                "team_count":
                    snapshot[
                        "team_count"
                    ],

                "column_count":
                    snapshot[
                        "column_count"
                    ],

                "generated_at_utc":
                    snapshot[
                        "generated_at_utc"
                    ],

                "source_as_of_utc":
                    snapshot[
                        "source_as_of_utc"
                    ],

                "freshness_mode":
                    snapshot[
                        "freshness_mode"
                    ],

                "dependencies_valid":
                    True,

                "upstream_services_ready":
                    True,

                "independent_reconstruction_valid":
                    True,
            }

        except TeamContextNotReadyError as exc:

            return {

                "status":
                    "NOT_READY",

                "stage":
                    "8.4.4",

                "service":
                    "team_context",

                "reason":
                    str(
                        exc
                    ),
            }

    def get_all_team_context(
        self,
    ) -> list[dict]:

        snapshot = self._validate()

        return copy.deepcopy(
            snapshot[
                "rows"
            ]
        )

    def get_team_context(
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
            self.get_all_team_context()
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
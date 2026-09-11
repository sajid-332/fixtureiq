"""
FixtureIQ Stage 8.4.3
Independent Unified Team Context Validator.

Validates:
- locked Stage 8.1 contract
- Stage 8.2 COMPLETE
- Stage 8.3 COMPLETE
- StandingsService READY
- TeamFormService READY
- exact 20-team identity match
- canonical 38-column team_context.csv
- strict one-to-one reconstruction
- exact standings preservation
- exact overall/home/away form preservation
- standings arithmetic
- form arithmetic
- provenance
- dependency hashes
- Stage 8 safety boundary

No provider fetch.
No model execution.
No Stage 7 writes.
"""

from __future__ import annotations

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

class TeamContextValidationError(
    RuntimeError
):
    """Raised when unified context fails independent validation."""


# ============================================================
# Helpers
# ============================================================

def _load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise TeamContextValidationError(
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

        raise TeamContextValidationError(
            f"Invalid JSON artifact: {path}"
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):

        raise TeamContextValidationError(
            f"Expected JSON object: {path}"
        )

    return payload


def _sha256_file(
    path: Path,
) -> str:

    if not path.exists():

        raise TeamContextValidationError(
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

        raise TeamContextValidationError(
            f"Could not hash artifact: {path}"
        ) from exc

    return digest.hexdigest()


def _relative_path(
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


def _parse_timestamp(
    value,
    field_name: str,
) -> datetime:

    if not isinstance(
        value,
        str,
    ):

        raise TeamContextValidationError(
            f"{field_name} is missing."
        )

    text = value.strip()

    if not text:

        raise TeamContextValidationError(
            f"{field_name} is blank."
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

        raise TeamContextValidationError(
            f"{field_name} is not valid ISO datetime."
        ) from exc

    if parsed.tzinfo is None:

        raise TeamContextValidationError(
            f"{field_name} must be timezone-aware."
        )

    return parsed


def _read_context_csv(
    path: Path,
) -> list[dict]:

    if not path.exists():

        raise TeamContextValidationError(
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

                raise TeamContextValidationError(
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

        raise TeamContextValidationError(
            "Could not read team_context.csv."
        ) from exc

    if len(
        raw_rows
    ) != 20:

        raise TeamContextValidationError(
            (
                "Canonical team context must contain "
                f"20 rows, found {len(raw_rows)}."
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

            raise TeamContextValidationError(
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

            raise TeamContextValidationError(
                (
                    "Invalid numeric team-context value "
                    f"for {row['team_name']}."
                )
            ) from exc

        rows.append(
            row
        )

    return rows


def _validate_standings_block(
    row: dict,
) -> None:

    if not (
        1
        <= row[
            "position"
        ]
        <= 20
    ):

        raise TeamContextValidationError(
            (
                "Invalid position for "
                f"{row['team_name']}."
            )
        )

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

        raise TeamContextValidationError(
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
        (
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
        )
    ):

        raise TeamContextValidationError(
            (
                "played != W+D+L for "
                f"{row['team_name']}."
            )
        )

    if (
        row[
            "goal_difference"
        ]
        !=
        (
            row[
                "goals_for"
            ]
            -
            row[
                "goals_against"
            ]
        )
    ):

        raise TeamContextValidationError(
            (
                "Invalid standings GD for "
                f"{row['team_name']}."
            )
        )

    if (
        row[
            "points"
        ]
        !=
        (
            3
            *
            row[
                "won"
            ]
            +
            row[
                "drawn"
            ]
        )
    ):

        raise TeamContextValidationError(
            (
                "Invalid standings points for "
                f"{row['team_name']}."
            )
        )


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

        raise TeamContextValidationError(
            (
                f"{label} form window invalid for "
                f"{row['team_name']}."
            )
        )

    if len(
        results
    ) != matches:

        raise TeamContextValidationError(
            (
                f"{label} result length invalid for "
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

        raise TeamContextValidationError(
            (
                f"{label} contains invalid result symbols "
                f"for {row['team_name']}."
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

        raise TeamContextValidationError(
            (
                f"{label} contains negative values "
                f"for {row['team_name']}."
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

        raise TeamContextValidationError(
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

        raise TeamContextValidationError(
            (
                f"{label} points invalid for "
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

        raise TeamContextValidationError(
            (
                f"{label} GD invalid for "
                f"{row['team_name']}."
            )
        )


def _reconstruct_context(
    standings: list[dict],
    forms: list[dict],
) -> list[dict]:

    standings_by_id = {}

    for row in standings:

        team_id = str(
            row[
                "team_id"
            ]
        )

        if team_id in standings_by_id:

            raise TeamContextValidationError(
                "Duplicate standings team ID."
            )

        standings_by_id[
            team_id
        ] = row

    forms_by_id = {}

    for row in forms:

        team_id = str(
            row[
                "team_id"
            ]
        )

        if team_id in forms_by_id:

            raise TeamContextValidationError(
                "Duplicate form team ID."
            )

        forms_by_id[
            team_id
        ] = row

    if (
        set(
            standings_by_id
        )
        !=
        set(
            forms_by_id
        )
    ):

        raise TeamContextValidationError(
            "Standings and form identity sets differ."
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

            raise TeamContextValidationError(
                (
                    "Canonical name mismatch for "
                    f"{team_id}."
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
# Validator
# ============================================================

class TeamContextValidator:

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

    def validate(
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

        # ====================================================
        # Foundation
        # ====================================================

        if (
            contract.get(
                "stage_8_1_complete"
            )
            is not True
        ):

            raise TeamContextValidationError(
                "Stage 8.1 is not complete."
            )

        if (
            contract.get(
                "contract_status"
            )
            != "LOCKED_CONTEXT_CONTRACT"
        ):

            raise TeamContextValidationError(
                "Stage 8 contract is not locked."
            )

        if (
            contract_verification.get(
                "status"
            )
            != "PASS"
        ):

            raise TeamContextValidationError(
                "Stage 8.1 verification is not PASS."
            )

        if (
            standings_report.get(
                "stage_8_2_complete"
            )
            is not True
        ):

            raise TeamContextValidationError(
                "Stage 8.2 is not complete."
            )

        if (
            form_report.get(
                "stage_8_3_complete"
            )
            is not True
        ):

            raise TeamContextValidationError(
                "Stage 8.3 is not complete."
            )

        # ====================================================
        # Stage 8.4 report state
        # ====================================================

        if (
            report.get(
                "stage"
            )
            != "8.4"
        ):

            raise TeamContextValidationError(
                "team_context_report stage mismatch."
            )

        sub_stages = report.get(
            "sub_stages",
            {}
        )

        for stage in (
            "8.4.1",
            "8.4.2",
        ):

            if (
                sub_stages.get(
                    stage
                )
                != "PASS"
            ):

                raise TeamContextValidationError(
                    f"{stage} is not PASS."
                )

        if (
            report.get(
                "upstream_context_readiness"
            )
            != "VERIFIED"
        ):

            raise TeamContextValidationError(
                "Upstream context readiness not VERIFIED."
            )

        if (
            report.get(
                "unified_team_context_builder"
            )
            != "VERIFIED"
        ):

            raise TeamContextValidationError(
                "Unified team-context builder not VERIFIED."
            )

        # ====================================================
        # Real upstream services
        # ====================================================

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

        if (
            standings_status.get(
                "status"
            )
            != "READY"
        ):

            raise TeamContextValidationError(
                (
                    "StandingsService is not READY: "
                    f"{standings_status.get('reason')}"
                )
            )

        if (
            form_status.get(
                "status"
            )
            != "READY"
        ):

            raise TeamContextValidationError(
                (
                    "TeamFormService is not READY: "
                    f"{form_status.get('reason')}"
                )
            )

        standings = (
            standings_service.get_standings()
        )

        forms = (
            form_service.get_all_team_form()
        )

        if (
            len(
                standings
            )
            != 20
            or
            len(
                forms
            )
            != 20
        ):

            raise TeamContextValidationError(
                "Upstream services must each return 20 teams."
            )

        # ====================================================
        # Canonical artifact
        # ====================================================

        rows = _read_context_csv(
            self.team_context_file
        )

        if len(
            {
                row[
                    "team_id"
                ]
                for row in rows
            }
        ) != 20:

            raise TeamContextValidationError(
                "Context team IDs are not unique."
            )

        if len(
            {
                row[
                    "team_name"
                ].casefold()
                for row in rows
            }
        ) != 20:

            raise TeamContextValidationError(
                "Context team names are not unique."
            )

        names = [
            row[
                "team_name"
            ].casefold()
            for row in rows
        ]

        if names != sorted(
            names
        ):

            raise TeamContextValidationError(
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

            raise TeamContextValidationError(
                "Standings positions are not unique 1..20."
            )

        for row in rows:

            _validate_standings_block(
                row
            )

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

        # ====================================================
        # Independent reconstruction
        # ====================================================

        expected = _reconstruct_context(
            standings,
            forms,
        )

        if rows != expected:

            raise TeamContextValidationError(
                (
                    "team_context.csv does not exactly match "
                    "independently reconstructed upstream join."
                )
            )

        # ====================================================
        # Artifact identity
        # ====================================================

        artifact = report.get(
            "team_context",
            {}
        )

        actual_context_sha = _sha256_file(
            self.team_context_file
        )

        if (
            artifact.get(
                "sha256"
            )
            != actual_context_sha
        ):

            raise TeamContextValidationError(
                "team_context.csv SHA mismatch."
            )

        if (
            artifact.get(
                "row_count"
            )
            != 20
        ):

            raise TeamContextValidationError(
                "Reported team-context row count invalid."
            )

        if (
            artifact.get(
                "column_count"
            )
            != 38
        ):

            raise TeamContextValidationError(
                "Reported team-context column count invalid."
            )

        if (
            artifact.get(
                "columns"
            )
            != TEAM_CONTEXT_FIELDS
        ):

            raise TeamContextValidationError(
                "Reported team-context schema invalid."
            )

        if (
            artifact.get(
                "team_namespace"
            )
            != "fixtureiq-team"
        ):

            raise TeamContextValidationError(
                "Invalid team namespace."
            )

        # ====================================================
        # Join evidence
        # ====================================================

        join = report.get(
            "join",
            {}
        )

        if (
            join.get(
                "type"
            )
            != "ONE_TO_ONE"
        ):

            raise TeamContextValidationError(
                "Join type is not ONE_TO_ONE."
            )

        if (
            join.get(
                "identity_match"
            )
            is not True
        ):

            raise TeamContextValidationError(
                "Join identity_match is not true."
            )

        for field in (
            "standings_rows",
            "form_rows",
            "output_rows",
        ):

            if (
                join.get(
                    field
                )
                != 20
            ):

                raise TeamContextValidationError(
                    f"Invalid join evidence: {field}"
                )

        # ====================================================
        # Provenance
        # ====================================================

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

            raise TeamContextValidationError(
                (
                    "Unified source_as_of_utc does not equal "
                    "max(standings, form source timestamps)."
                )
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

            raise TeamContextValidationError(
                "Form history-cutoff provenance mismatch."
            )

        if generated_at < source_as_of:

            raise TeamContextValidationError(
                "Context generated_at predates source_as_of."
            )

        if (
            report.get(
                "competition_code"
            )
            != "PL"
        ):

            raise TeamContextValidationError(
                "Competition code must be PL."
            )

        if (
            report.get(
                "season"
            )
            != 2026
        ):

            raise TeamContextValidationError(
                "Context season must be 2026."
            )

        # ====================================================
        # Locked output contract
        # ====================================================

        output_contract = contract.get(
            "output_artifact_contract",
            {}
        )

        outputs = output_contract.get(
            "outputs",
            {}
        )

        if (
            outputs.get(
                "team_context",
                {}
            ).get(
                "path"
            )
            !=
            _relative_path(
                self.team_context_file
            )
        ):

            raise TeamContextValidationError(
                "Locked team_context path mismatch."
            )

        if (
            outputs.get(
                "team_context_report",
                {}
            ).get(
                "path"
            )
            !=
            _relative_path(
                self.team_context_report_file
            )
        ):

            raise TeamContextValidationError(
                "Locked team_context_report path mismatch."
            )

        if (
            output_contract.get(
                "stage7_output_write_allowed"
            )
            is not False
        ):

            raise TeamContextValidationError(
                "Stage 7 write protection invalid."
            )

        # ====================================================
        # Full upstream dependency identity
        # ====================================================

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

                raise TeamContextValidationError(
                    (
                        f"Dependency changed or mismatched: "
                        f"{name}"
                    )
                )

        # ====================================================
        # Freshness declaration
        # ====================================================

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

            raise TeamContextValidationError(
                "Freshness mode must be DEPENDENCY_BASED."
            )

        required_true = [

            "current_standings_change_invalidates_context",
            "standings_report_change_invalidates_context",
            "current_team_form_change_invalidates_context",
            "team_form_report_change_invalidates_context",
            "fail_closed",
        ]

        for flag in required_true:

            if (
                freshness.get(
                    flag
                )
                is not True
            ):

                raise TeamContextValidationError(
                    f"Freshness flag invalid: {flag}"
                )

        if (
            freshness.get(
                "stale_fallback_allowed"
            )
            is not False
        ):

            raise TeamContextValidationError(
                "Stale fallback must be prohibited."
            )

        if (
            freshness.get(
                "partial_unverified_output_allowed"
            )
            is not False
        ):

            raise TeamContextValidationError(
                "Partial unverified output must be prohibited."
            )

        # ====================================================
        # Safety
        # ====================================================

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

            raise TeamContextValidationError(
                "Unified context is not context-only."
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

                raise TeamContextValidationError(
                    (
                        "Safety boundary invalid: "
                        f"{flag}"
                    )
                )

        return {

            "status":
                "PASS",

            "rows":
                rows,

            "team_count":
                20,

            "column_count":
                38,

            "artifact_sha256":
                actual_context_sha,

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
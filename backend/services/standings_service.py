"""
FixtureIQ Stage 8.2.4
Canonical Standings Read Service + Dependency Freshness.

Responsibilities:
- read current_standings.csv
- validate standings_report.json
- enforce the locked Stage 8.1 contract
- enforce canonical schema and arithmetic
- validate dependency identity
- detect stale/invalid artifacts
- provide read-only standings access

Important freshness rule:
upcoming_fixtures.csv is used only as the source of the canonical
FixtureIQ EPL team registry.

A normal fixture refresh does NOT make standings stale if the actual
20-team FixtureIQ identity registry is unchanged.

This module does NOT:
- call football-data.org
- run the model
- load joblib
- modify Stage 7
- change predictions
- train/retrain/tune/select models
"""

from __future__ import annotations

import csv
import copy
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

CONTEXT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "context"
)

PRODUCTION_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "production"
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

DEFAULT_REPORT_FILE = (
    CONTEXT_DIR
    / "standings_report.json"
)

DEFAULT_UPCOMING_FIXTURES_FILE = (
    PRODUCTION_DIR
    / "upcoming_fixtures.csv"
)


EXPECTED_FIELDS = [

    "team_id",
    "team_name",

    "position",
    "played",
    "won",
    "drawn",
    "lost",

    "goals_for",
    "goals_against",
    "goal_difference",

    "points",
]


# ============================================================
# Exception
# ============================================================

class StandingsNotReadyError(
    RuntimeError
):
    """Raised when canonical standings cannot be safely served."""


# ============================================================
# Helpers
# ============================================================

def _load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise StandingsNotReadyError(
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

        raise StandingsNotReadyError(
            f"Invalid JSON artifact: {path}"
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):

        raise StandingsNotReadyError(
            f"Expected JSON object: {path}"
        )

    return payload


def _sha256_file(
    path: Path,
) -> str:

    if not path.exists():

        raise StandingsNotReadyError(
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

        raise StandingsNotReadyError(
            f"Could not hash artifact: {path}"
        ) from exc

    return digest.hexdigest()


def _parse_aware_timestamp(
    value,
    field_name: str,
) -> datetime:

    if not isinstance(
        value,
        str,
    ):

        raise StandingsNotReadyError(
            f"{field_name} is missing or invalid."
        )

    text = value.strip()

    if not text:

        raise StandingsNotReadyError(
            f"{field_name} is missing or blank."
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

        raise StandingsNotReadyError(
            f"{field_name} is not a valid ISO timestamp."
        ) from exc

    if (
        parsed.tzinfo
        is None
    ):

        raise StandingsNotReadyError(
            f"{field_name} must be timezone-aware."
        )

    return parsed


def _read_canonical_standings(
    path: Path,
) -> list[dict]:

    if not path.exists():

        raise StandingsNotReadyError(
            f"Standings artifact missing: {path}"
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

                raise StandingsNotReadyError(
                    (
                        "Canonical standings schema mismatch. "
                        f"Expected={EXPECTED_FIELDS}, "
                        f"actual={fields}"
                    )
                )

            raw_rows = list(
                reader
            )

    except OSError as exc:

        raise StandingsNotReadyError(
            f"Could not read standings artifact: {path}"
        ) from exc

    if len(
        raw_rows
    ) != 20:

        raise StandingsNotReadyError(
            (
                "Canonical standings must contain exactly "
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

            raise StandingsNotReadyError(
                "Blank canonical team identity found."
            )

        try:

            row = {

                "team_id":
                    team_id,

                "team_name":
                    team_name,

                "position":
                    int(
                        raw[
                            "position"
                        ]
                    ),

                "played":
                    int(
                        raw[
                            "played"
                        ]
                    ),

                "won":
                    int(
                        raw[
                            "won"
                        ]
                    ),

                "drawn":
                    int(
                        raw[
                            "drawn"
                        ]
                    ),

                "lost":
                    int(
                        raw[
                            "lost"
                        ]
                    ),

                "goals_for":
                    int(
                        raw[
                            "goals_for"
                        ]
                    ),

                "goals_against":
                    int(
                        raw[
                            "goals_against"
                        ]
                    ),

                "goal_difference":
                    int(
                        raw[
                            "goal_difference"
                        ]
                    ),

                "points":
                    int(
                        raw[
                            "points"
                        ]
                    ),
            }

        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:

            raise StandingsNotReadyError(
                (
                    "Invalid numeric standings data for "
                    f"{team_name!r}."
                )
            ) from exc

        rows.append(
            row
        )

    return rows


def _validate_standings_rows(
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

    positions = [
        row[
            "position"
        ]
        for row in rows
    ]

    if (
        len(
            set(
                team_ids
            )
        )
        != 20
    ):

        raise StandingsNotReadyError(
            "FixtureIQ team IDs are not unique."
        )

    if (
        len(
            {
                name.casefold()
                for name in team_names
            }
        )
        != 20
    ):

        raise StandingsNotReadyError(
            "FixtureIQ team names are not unique."
        )

    if (
        positions
        != list(
            range(
                1,
                21,
            )
        )
    ):

        raise StandingsNotReadyError(
            (
                "Canonical standings must be sorted "
                "by positions 1 through 20."
            )
        )

    for row in rows:

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

            raise StandingsNotReadyError(
                (
                    "Negative standings value found for "
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

            raise StandingsNotReadyError(
                (
                    "played != won + drawn + lost for "
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

            raise StandingsNotReadyError(
                (
                    "Invalid goal difference for "
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

            raise StandingsNotReadyError(
                (
                    "Invalid points arithmetic for "
                    f"{row['team_name']}."
                )
            )


def _load_current_team_registry(
    path: Path,
) -> set[tuple[str, str]]:

    if not path.exists():

        raise StandingsNotReadyError(
            (
                "Canonical team registry source missing: "
                f"{path}"
            )
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

                "home_team_id",
                "home_team_name",
                "away_team_id",
                "away_team_name",
            }

            if not required.issubset(
                fields
            ):

                raise StandingsNotReadyError(
                    (
                        "Upcoming fixture team registry "
                        "schema is invalid."
                    )
                )

            id_to_name = {}
            name_to_id = {}

            for row in reader:

                pairs = [

                    (
                        row.get(
                            "home_team_id"
                        ),
                        row.get(
                            "home_team_name"
                        ),
                    ),

                    (
                        row.get(
                            "away_team_id"
                        ),
                        row.get(
                            "away_team_name"
                        ),
                    ),
                ]

                for team_id, team_name in pairs:

                    team_id = str(
                        team_id
                    ).strip()

                    team_name = str(
                        team_name
                    ).strip()

                    if (
                        not team_id
                        or
                        not team_name
                    ):

                        raise StandingsNotReadyError(
                            (
                                "Blank team identity in "
                                "upcoming fixture registry."
                            )
                        )

                    existing_name = (
                        id_to_name.get(
                            team_id
                        )
                    )

                    if (
                        existing_name is not None
                        and
                        existing_name
                        != team_name
                    ):

                        raise StandingsNotReadyError(
                            (
                                "FixtureIQ team ID maps to "
                                "multiple names."
                            )
                        )

                    existing_id = (
                        name_to_id.get(
                            team_name
                        )
                    )

                    if (
                        existing_id is not None
                        and
                        existing_id
                        != team_id
                    ):

                        raise StandingsNotReadyError(
                            (
                                "FixtureIQ team name maps to "
                                "multiple IDs."
                            )
                        )

                    id_to_name[
                        team_id
                    ] = team_name

                    name_to_id[
                        team_name
                    ] = team_id

    except OSError as exc:

        raise StandingsNotReadyError(
            (
                "Could not read current FixtureIQ "
                "team registry."
            )
        ) from exc

    if len(
        id_to_name
    ) != 20:

        raise StandingsNotReadyError(
            (
                "Expected 20 FixtureIQ teams in current "
                f"registry, found {len(id_to_name)}."
            )
        )

    return {

        (
            team_id,
            team_name,
        )

        for (
            team_id,
            team_name,
        ) in id_to_name.items()
    }


def _load_report_team_registry(
    report: dict,
) -> set[tuple[str, str]]:

    mappings = report.get(
        "team_mappings"
    )

    if not isinstance(
        mappings,
        list,
    ):

        raise StandingsNotReadyError(
            "standings_report team_mappings is missing."
        )

    registry = set()

    for mapping in mappings:

        if not isinstance(
            mapping,
            dict,
        ):

            raise StandingsNotReadyError(
                "Invalid team mapping in standings_report."
            )

        team_id = str(
            mapping.get(
                "team_id",
                ""
            )
        ).strip()

        team_name = str(
            mapping.get(
                "team_name",
                ""
            )
        ).strip()

        if (
            not team_id
            or
            not team_name
        ):

            raise StandingsNotReadyError(
                (
                    "Blank canonical team identity "
                    "in standings_report mappings."
                )
            )

        registry.add(
            (
                team_id,
                team_name,
            )
        )

    if len(
        registry
    ) != 20:

        raise StandingsNotReadyError(
            (
                "standings_report must contain "
                "20 unique canonical team mappings."
            )
        )

    return registry


# ============================================================
# Service
# ============================================================

class StandingsService:

    def __init__(
        self,
        *,
        contract_file: Path | None = None,
        contract_verification_file: Path | None = None,
        standings_file: Path | None = None,
        report_file: Path | None = None,
        upcoming_fixtures_file: Path | None = None,
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

        self.report_file = (
            Path(
                report_file
            )
            if report_file is not None
            else DEFAULT_REPORT_FILE
        )

        self.upcoming_fixtures_file = (
            Path(
                upcoming_fixtures_file
            )
            if upcoming_fixtures_file is not None
            else DEFAULT_UPCOMING_FIXTURES_FILE
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

        report = _load_json(
            self.report_file
        )

        # ----------------------------------------------------
        # Stage 8.1 contract lock
        # ----------------------------------------------------

        if (
            contract.get(
                "stage_8_1_complete"
            )
            is not True
        ):

            raise StandingsNotReadyError(
                "Stage 8.1 contract is not complete."
            )

        if (
            contract.get(
                "stage_8_1_status"
            )
            != "COMPLETE"
        ):

            raise StandingsNotReadyError(
                "Stage 8.1 contract status is not COMPLETE."
            )

        if (
            contract.get(
                "contract_status"
            )
            != "LOCKED_CONTEXT_CONTRACT"
        ):

            raise StandingsNotReadyError(
                "Stage 8 context contract is not locked."
            )

        if (
            contract_verification.get(
                "status"
            )
            != "PASS"
        ):

            raise StandingsNotReadyError(
                "Stage 8.1 verification is not PASS."
            )

        # ----------------------------------------------------
        # Report stage state
        # ----------------------------------------------------

        if (
            report.get(
                "stage"
            )
            != "8.2"
        ):

            raise StandingsNotReadyError(
                "standings_report stage mismatch."
            )

        sub_stages = report.get(
            "sub_stages",
            {}
        )

        for stage in (
            "8.2.1",
            "8.2.2",
            "8.2.3",
        ):

            if (
                sub_stages.get(
                    stage
                )
                != "PASS"
            ):

                raise StandingsNotReadyError(
                    f"{stage} is not PASS."
                )

        # ----------------------------------------------------
        # Locked provider identity
        # ----------------------------------------------------

        trusted = contract.get(
            "trusted_inputs",
            {}
        )

        provider_contract = trusted.get(
            "live_context_provider",
            {}
        )

        if (
            report.get(
                "provider"
            )
            !=
            provider_contract.get(
                "provider"
            )
        ):

            raise StandingsNotReadyError(
                "Standings provider does not match contract."
            )

        if (
            report.get(
                "competition_code"
            )
            !=
            provider_contract.get(
                "competition_code"
            )
        ):

            raise StandingsNotReadyError(
                "Competition code does not match contract."
            )

        if (
            report.get(
                "season"
            )
            !=
            provider_contract.get(
                "configured_season"
            )
        ):

            raise StandingsNotReadyError(
                "Standings season does not match contract."
            )

        # ----------------------------------------------------
        # Output contract
        # ----------------------------------------------------

        output_contract = contract.get(
            "output_artifact_contract",
            {}
        )

        outputs = output_contract.get(
            "outputs",
            {}
        )

        standings_contract = outputs.get(
            "current_standings",
            {}
        )

        report_contract = outputs.get(
            "standings_report",
            {}
        )

        expected_standings_suffix = (
            "data/processed/context/"
            "current_standings.csv"
        )

        expected_report_suffix = (
            "data/processed/context/"
            "standings_report.json"
        )

        if (
            standings_contract.get(
                "path"
            )
            != expected_standings_suffix
        ):

            raise StandingsNotReadyError(
                "Locked current_standings path is invalid."
            )

        if (
            report_contract.get(
                "path"
            )
            != expected_report_suffix
        ):

            raise StandingsNotReadyError(
                "Locked standings_report path is invalid."
            )

        if (
            output_contract.get(
                "stage7_output_write_allowed"
            )
            is not False
        ):

            raise StandingsNotReadyError(
                "Stage 7 write protection is invalid."
            )

        # ----------------------------------------------------
        # Canonical standings
        # ----------------------------------------------------

        rows = _read_canonical_standings(
            self.standings_file
        )

        _validate_standings_rows(
            rows
        )

        report_artifact = report.get(
            "current_standings",
            {}
        )

        actual_standings_hash = _sha256_file(
            self.standings_file
        )

        if (
            report_artifact.get(
                "sha256"
            )
            != actual_standings_hash
        ):

            raise StandingsNotReadyError(
                (
                    "current_standings.csv hash does not "
                    "match standings_report."
                )
            )

        if (
            report_artifact.get(
                "row_count"
            )
            != 20
        ):

            raise StandingsNotReadyError(
                "Reported standings row count is invalid."
            )

        if (
            report_artifact.get(
                "columns"
            )
            != EXPECTED_FIELDS
        ):

            raise StandingsNotReadyError(
                "Reported standings schema is invalid."
            )

        if (
            report_artifact.get(
                "team_namespace"
            )
            != "fixtureiq-team"
        ):

            raise StandingsNotReadyError(
                "FixtureIQ team namespace is invalid."
            )

        if (
            report_artifact.get(
                "provider_ids_in_public_csv"
            )
            is not False
        ):

            raise StandingsNotReadyError(
                "Provider IDs leaked into public standings."
            )

        # ----------------------------------------------------
        # Provenance timestamps
        # ----------------------------------------------------

        generated_at = _parse_aware_timestamp(
            report.get(
                "generated_at_utc"
            ),
            "generated_at_utc",
        )

        source_as_of = _parse_aware_timestamp(
            report.get(
                "source_as_of_utc"
            ),
            "source_as_of_utc",
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

            raise StandingsNotReadyError(
                (
                    "Standings freshness mode must be "
                    "DEPENDENCY_BASED."
                )
            )

        if (
            freshness.get(
                "provider_snapshot_valid"
            )
            is not True
        ):

            raise StandingsNotReadyError(
                "Provider snapshot is not verified."
            )

        if (
            freshness.get(
                "dependency_identity_recorded"
            )
            is not True
        ):

            raise StandingsNotReadyError(
                "Dependency identity was not recorded."
            )

        # ----------------------------------------------------
        # Immutable Stage 8.1 dependencies
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

        if (
            contract_dependency.get(
                "sha256"
            )
            != _sha256_file(
                self.contract_file
            )
        ):

            raise StandingsNotReadyError(
                (
                    "Stage 8 context contract changed "
                    "after standings snapshot creation."
                )
            )

        if (
            verification_dependency.get(
                "sha256"
            )
            != _sha256_file(
                self.contract_verification_file
            )
        ):

            raise StandingsNotReadyError(
                (
                    "Stage 8.1 verification changed "
                    "after standings snapshot creation."
                )
            )

        # ----------------------------------------------------
        # Semantic canonical-team dependency
        #
        # Do NOT use the whole upcoming fixtures file hash
        # as the freshness decision.
        #
        # Fixture schedules may change while the EPL team
        # identity registry remains identical.
        # ----------------------------------------------------

        team_dependency = dependencies.get(
            "upcoming_fixtures_team_registry",
            {}
        )

        if (
            team_dependency.get(
                "usage"
            )
            != "FIXTUREIQ_CANONICAL_TEAM_IDENTITY"
        ):

            raise StandingsNotReadyError(
                (
                    "Canonical team registry dependency "
                    "is missing or invalid."
                )
            )

        current_registry = (
            _load_current_team_registry(
                self.upcoming_fixtures_file
            )
        )

        report_registry = (
            _load_report_team_registry(
                report
            )
        )

        if (
            current_registry
            != report_registry
        ):

            raise StandingsNotReadyError(
                (
                    "FixtureIQ canonical EPL team registry "
                    "changed after standings creation."
                )
            )

        # ----------------------------------------------------
        # Safety evidence
        # ----------------------------------------------------

        safety = report.get(
            "safety",
            {}
        )

        required_false_flags = [

            "stage7_artifacts_modified",
            "model_loaded",
            "model_executed",
            "model_modified",
            "production_predictions_modified",
            "feature_schema_modified",
            "standings_used_as_model_features",
            "final_test_accessed",
        ]

        if (
            safety.get(
                "context_only"
            )
            is not True
        ):

            raise StandingsNotReadyError(
                "Standings snapshot is not marked context-only."
            )

        for flag in required_false_flags:

            if (
                safety.get(
                    flag
                )
                is not False
            ):

                raise StandingsNotReadyError(
                    (
                        "Standings safety boundary invalid: "
                        f"{flag}"
                    )
                )

        return {

            "rows":
                rows,

            "generated_at_utc":
                generated_at.isoformat(),

            "source_as_of_utc":
                source_as_of.isoformat(),

            "provider":
                report.get(
                    "provider"
                ),

            "competition":
                report.get(
                    "competition"
                ),

            "competition_code":
                report.get(
                    "competition_code"
                ),

            "season":
                report.get(
                    "season"
                ),

            "current_matchday":
                report.get(
                    "current_matchday"
                ),

            "artifact_sha256":
                actual_standings_hash,

            "freshness_mode":
                "DEPENDENCY_BASED",

            "team_registry_valid":
                True,

            "dependencies_valid":
                True,
        }

    # ========================================================
    # Public methods
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
                    "8.2.4",

                "service":
                    "standings",

                "provider":
                    snapshot[
                        "provider"
                    ],

                "competition":
                    snapshot[
                        "competition"
                    ],

                "competition_code":
                    snapshot[
                        "competition_code"
                    ],

                "season":
                    snapshot[
                        "season"
                    ],

                "current_matchday":
                    snapshot[
                        "current_matchday"
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

                "freshness_mode":
                    snapshot[
                        "freshness_mode"
                    ],

                "dependencies_valid":
                    True,

                "team_registry_valid":
                    True,
            }

        except StandingsNotReadyError as exc:

            return {

                "status":
                    "NOT_READY",

                "stage":
                    "8.2.4",

                "service":
                    "standings",

                "reason":
                    str(
                        exc
                    ),
            }

    def get_standings(
        self,
    ) -> list[dict]:

        snapshot = self._validate()

        return copy.deepcopy(
            snapshot[
                "rows"
            ]
        )

    def get_team_standing(
        self,
        team_name: str,
    ) -> dict | None:

        query = str(
            team_name
        ).strip()

        if not query:

            return None

        rows = self.get_standings()

        query_key = (
            query.casefold()
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
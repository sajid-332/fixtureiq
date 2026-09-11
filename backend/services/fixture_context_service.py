"""
FixtureIQ Stage 8.5.4
Fixture Context Read Service + Freshness Enforcement.

Responsibilities:
- serve verified enriched_upcoming_fixtures.csv
- require Stage 8.5.1 / 8.5.2 / 8.5.3 verification
- reuse independent Stage 8.5 validator
- require TeamContextService READY
- enforce direct dependency freshness
- enforce transitive TeamContextService freshness
- enforce live fixture kickoff temporal boundary
- fail closed
- return defensive copies

No provider fetch.
No model execution.
No prediction mutation.
No Stage 7 writes.
"""

from __future__ import annotations

import copy
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from backend.services.fixture_context_validator import (
    APPENDED_CONTEXT_FIELDS,
    STRING_CONTEXT_FIELDS,
    TEAM_CONTEXT_VALUE_FIELDS,
    FixtureContextValidationError,
    FixtureContextValidator,
)

from backend.services.team_context_service import (
    TeamContextService,
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

DEFAULT_UPCOMING_FIXTURES_FILE = (
    PRODUCTION_DIR
    / "upcoming_fixtures.csv"
)

DEFAULT_FIXTURE_FETCH_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_fixture_fetch_report.json"
)

DEFAULT_TEAM_CONTEXT_FILE = (
    CONTEXT_DIR
    / "team_context.csv"
)

DEFAULT_TEAM_CONTEXT_REPORT_FILE = (
    CONTEXT_DIR
    / "team_context_report.json"
)

DEFAULT_ENRICHED_FIXTURES_FILE = (
    CONTEXT_DIR
    / "enriched_upcoming_fixtures.csv"
)

DEFAULT_FIXTURE_CONTEXT_REPORT_FILE = (
    CONTEXT_DIR
    / "fixture_context_report.json"
)


# ============================================================
# Error
# ============================================================

class FixtureContextNotReadyError(
    RuntimeError
):
    """Raised when fixture context cannot be safely served."""


# ============================================================
# Helpers
# ============================================================

def _load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise FixtureContextNotReadyError(
            f"Required artifact missing: {path}"
        )

    try:

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            payload = json.load(file)

    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:

        raise FixtureContextNotReadyError(
            f"Invalid JSON artifact: {path}"
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):

        raise FixtureContextNotReadyError(
            f"Expected JSON object: {path}"
        )

    return payload


def _parse_aware_timestamp(
    value,
    field_name: str,
) -> datetime:

    if not isinstance(
        value,
        str,
    ):

        raise FixtureContextNotReadyError(
            f"{field_name} missing or invalid."
        )

    text = value.strip()

    if not text:

        raise FixtureContextNotReadyError(
            f"{field_name} missing or blank."
        )

    if text.endswith("Z"):

        text = (
            text[:-1]
            + "+00:00"
        )

    try:

        parsed = datetime.fromisoformat(
            text
        )

    except ValueError as exc:

        raise FixtureContextNotReadyError(
            f"{field_name} invalid ISO datetime."
        ) from exc

    if parsed.tzinfo is None:

        raise FixtureContextNotReadyError(
            f"{field_name} must be timezone-aware."
        )

    return parsed.astimezone(
        timezone.utc
    )


def _read_enriched_rows(
    path: Path,
    expected_fields: list[str],
) -> list[dict]:

    if not path.exists():

        raise FixtureContextNotReadyError(
            f"Enriched fixture artifact missing: {path}"
        )

    try:

        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:

            reader = csv.DictReader(file)

            fields = (
                reader.fieldnames
                or []
            )

            raw_rows = list(reader)

    except OSError as exc:

        raise FixtureContextNotReadyError(
            "Could not read enriched fixture artifact."
        ) from exc

    if (
        fields
        != expected_fields
    ):

        raise FixtureContextNotReadyError(
            "Enriched fixture schema mismatch."
        )

    rows = []

    for raw in raw_rows:

        if None in raw:

            raise FixtureContextNotReadyError(
                "Malformed enriched fixture row."
            )

        row = dict(raw)

        for prefix in (
            "home_team_",
            "away_team_",
        ):

            for source_field in TEAM_CONTEXT_VALUE_FIELDS:

                output_field = (
                    prefix
                    +
                    source_field
                )

                if (
                    source_field
                    not in STRING_CONTEXT_FIELDS
                ):

                    try:

                        row[
                            output_field
                        ] = int(
                            raw[
                                output_field
                            ]
                        )

                    except (
                        KeyError,
                        TypeError,
                        ValueError,
                    ) as exc:

                        raise FixtureContextNotReadyError(
                            (
                                "Invalid enriched context field: "
                                f"{output_field}"
                            )
                        ) from exc

        rows.append(row)

    return rows


# ============================================================
# Service
# ============================================================

class FixtureContextService:

    def __init__(
        self,
        *,
        contract_file: Path | None = None,
        contract_verification_file: Path | None = None,
        upcoming_fixtures_file: Path | None = None,
        fixture_fetch_report_file: Path | None = None,
        team_context_file: Path | None = None,
        team_context_report_file: Path | None = None,
        enriched_fixtures_file: Path | None = None,
        fixture_context_report_file: Path | None = None,
        team_context_service=None,
        clock: Callable[[], datetime] | None = None,
    ):

        self.contract_file = (
            Path(contract_file)
            if contract_file is not None
            else DEFAULT_CONTRACT_FILE
        )

        self.contract_verification_file = (
            Path(contract_verification_file)
            if contract_verification_file is not None
            else DEFAULT_CONTRACT_VERIFICATION_FILE
        )

        self.upcoming_fixtures_file = (
            Path(upcoming_fixtures_file)
            if upcoming_fixtures_file is not None
            else DEFAULT_UPCOMING_FIXTURES_FILE
        )

        self.fixture_fetch_report_file = (
            Path(fixture_fetch_report_file)
            if fixture_fetch_report_file is not None
            else DEFAULT_FIXTURE_FETCH_REPORT_FILE
        )

        self.team_context_file = (
            Path(team_context_file)
            if team_context_file is not None
            else DEFAULT_TEAM_CONTEXT_FILE
        )

        self.team_context_report_file = (
            Path(team_context_report_file)
            if team_context_report_file is not None
            else DEFAULT_TEAM_CONTEXT_REPORT_FILE
        )

        self.enriched_fixtures_file = (
            Path(enriched_fixtures_file)
            if enriched_fixtures_file is not None
            else DEFAULT_ENRICHED_FIXTURES_FILE
        )

        self.fixture_context_report_file = (
            Path(fixture_context_report_file)
            if fixture_context_report_file is not None
            else DEFAULT_FIXTURE_CONTEXT_REPORT_FILE
        )

        self.team_context_service = (
            team_context_service
            if team_context_service is not None
            else TeamContextService()
        )

        self.clock = (
            clock
            if clock is not None
            else lambda: datetime.now(
                timezone.utc
            )
        )

    # ========================================================
    # Current time
    # ========================================================

    def _now(
        self,
    ) -> datetime:

        now = self.clock()

        if not isinstance(
            now,
            datetime,
        ):

            raise FixtureContextNotReadyError(
                "Fixture-context clock returned invalid value."
            )

        if now.tzinfo is None:

            raise FixtureContextNotReadyError(
                "Fixture-context clock must be timezone-aware."
            )

        return now.astimezone(
            timezone.utc
        )

    # ========================================================
    # Validation
    # ========================================================

    def _validate(
        self,
    ) -> dict:

        now_utc = self._now()

        report = _load_json(
            self.fixture_context_report_file
        )

        # ----------------------------------------------------
        # Stage 8.5 evidence
        # ----------------------------------------------------

        if (
            report.get(
                "stage"
            )
            != "8.5"
        ):

            raise FixtureContextNotReadyError(
                "Fixture context report stage mismatch."
            )

        sub_stages = report.get(
            "sub_stages",
            {}
        )

        for stage in (
            "8.5.1",
            "8.5.2",
            "8.5.3",
        ):

            if (
                sub_stages.get(stage)
                != "PASS"
            ):

                raise FixtureContextNotReadyError(
                    f"{stage} is not PASS."
                )

        if (
            sub_stages.get(
                "8.5.4"
            )
            not in {
                "PENDING",
                "PASS",
            }
        ):

            raise FixtureContextNotReadyError(
                "Stage 8.5.4 report state invalid."
            )

        if (
            report.get(
                "upcoming_fixture_source_gate"
            )
            != "VERIFIED"
        ):

            raise FixtureContextNotReadyError(
                "Fixture source gate not VERIFIED."
            )

        if (
            report.get(
                "home_away_context_join"
            )
            != "VERIFIED"
        ):

            raise FixtureContextNotReadyError(
                "Home/Away context join not VERIFIED."
            )

        if (
            report.get(
                "independent_fixture_context_validation"
            )
            != "VERIFIED"
        ):

            raise FixtureContextNotReadyError(
                "Independent fixture validation not VERIFIED."
            )

        independent = report.get(
            "independent_validation",
            {}
        )

        if (
            independent.get(
                "status"
            )
            != "VERIFIED"
        ):

            raise FixtureContextNotReadyError(
                "Independent validation evidence invalid."
            )

        # ----------------------------------------------------
        # Upstream TeamContextService
        # ----------------------------------------------------

        upstream_status = (
            self.team_context_service
            .get_status()
        )

        if (
            upstream_status.get(
                "status"
            )
            != "READY"
        ):

            raise FixtureContextNotReadyError(
                (
                    "Upstream TeamContextService NOT_READY: "
                    f"{upstream_status.get('reason')}"
                )
            )

        # ----------------------------------------------------
        # Independent Stage 8.5 validator
        # ----------------------------------------------------

        validator = FixtureContextValidator(

            contract_file=
                self.contract_file,

            contract_verification_file=
                self.contract_verification_file,

            upcoming_fixtures_file=
                self.upcoming_fixtures_file,

            fixture_fetch_report_file=
                self.fixture_fetch_report_file,

            team_context_file=
                self.team_context_file,

            team_context_report_file=
                self.team_context_report_file,

            enriched_fixtures_file=
                self.enriched_fixtures_file,

            fixture_context_report_file=
                self.fixture_context_report_file,
        )

        try:

            validation = (
                validator.validate(
                    now_utc=now_utc
                )
            )

        except FixtureContextValidationError as exc:

            raise FixtureContextNotReadyError(
                (
                    "Independent fixture-context "
                    f"validation failed: {exc}"
                )
            ) from exc

        if (
            validation.get(
                "status"
            )
            != "PASS"
        ):

            raise FixtureContextNotReadyError(
                "Independent fixture validation is not PASS."
            )

        # ----------------------------------------------------
        # Read canonical artifact
        # ----------------------------------------------------

        artifact = report.get(
            "enriched_upcoming_fixtures",
            {}
        )

        expected_fields = artifact.get(
            "columns",
            []
        )

        if not isinstance(
            expected_fields,
            list,
        ):

            raise FixtureContextNotReadyError(
                "Invalid enriched fixture schema evidence."
            )

        rows = _read_enriched_rows(
            self.enriched_fixtures_file,
            expected_fields,
        )

        if (
            len(rows)
            != validation.get(
                "fixture_count"
            )
        ):

            raise FixtureContextNotReadyError(
                "Fixture row count differs from validation."
            )

        if (
            len(rows)
            != report.get(
                "fixture_count"
            )
        ):

            raise FixtureContextNotReadyError(
                "Fixture row count differs from report."
            )

        if (
            len(expected_fields)
            != validation.get(
                "enriched_column_count"
            )
        ):

            raise FixtureContextNotReadyError(
                "Fixture column count differs from validation."
            )

        if (
            len(
                APPENDED_CONTEXT_FIELDS
            )
            != 72
        ):

            raise FixtureContextNotReadyError(
                "Fixture-context schema no longer appends 72 fields."
            )

        # ----------------------------------------------------
        # Live temporal boundary
        # ----------------------------------------------------

        earliest_kickoff = (
            _parse_aware_timestamp(
                report.get(
                    "earliest_fixture_kickoff_utc"
                ),
                "earliest_fixture_kickoff_utc",
            )
        )

        latest_kickoff = (
            _parse_aware_timestamp(
                report.get(
                    "latest_fixture_kickoff_utc"
                ),
                "latest_fixture_kickoff_utc",
            )
        )

        if (
            earliest_kickoff
            <= now_utc
        ):

            raise FixtureContextNotReadyError(
                (
                    "Fixture context is temporally stale: "
                    "earliest fixture kickoff has been reached."
                )
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
            !=
            "DEPENDENCY_BASED_PLUS_TEMPORAL_BOUNDARY"
        ):

            raise FixtureContextNotReadyError(
                "Fixture freshness mode invalid."
            )

        required_true_flags = [

            "upcoming_fixture_change_invalidates_context",
            "fixture_fetch_report_change_invalidates_context",
            "team_context_change_invalidates_context",
            "team_context_report_change_invalidates_context",
            "fixture_kickoff_reached_invalidates_context",
            "fail_closed",
        ]

        for flag in required_true_flags:

            if (
                freshness.get(flag)
                is not True
            ):

                raise FixtureContextNotReadyError(
                    f"Invalid freshness flag: {flag}"
                )

        if (
            freshness.get(
                "stale_fallback_allowed"
            )
            is not False
        ):

            raise FixtureContextNotReadyError(
                "Stale fallback must remain prohibited."
            )

        if (
            freshness.get(
                "partial_unverified_output_allowed"
            )
            is not False
        ):

            raise FixtureContextNotReadyError(
                "Partial unverified output must remain prohibited."
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

            raise FixtureContextNotReadyError(
                "Fixture context is not marked context-only."
            )

        safety_false_flags = [

            "stage7_artifacts_modified",
            "legacy_stage7_report_modified",
            "provider_timestamp_fabricated",
            "filesystem_mtime_used_as_provenance",
            "provider_fetch_performed",
            "fixture_source_modified",
            "team_context_modified",
            "future_results_used",
            "future_fixture_state_propagation",
            "model_loaded",
            "model_executed",
            "model_modified",
            "production_predictions_modified",
            "feature_schema_modified",
            "fixture_context_used_as_model_features",
            "final_test_accessed",
        ]

        for flag in safety_false_flags:

            if (
                safety.get(flag)
                is not False
            ):

                raise FixtureContextNotReadyError(
                    f"Safety boundary invalid: {flag}"
                )

        return {

            "rows":
                rows,

            "columns":
                expected_fields,

            "season":
                2026,

            "fixture_count":
                len(rows),

            "column_count":
                len(expected_fields),

            "source_column_count":
                artifact.get(
                    "source_column_count"
                ),

            "context_column_count":
                artifact.get(
                    "context_column_count"
                ),

            "earliest_fixture_kickoff_utc":
                earliest_kickoff.isoformat(),

            "latest_fixture_kickoff_utc":
                latest_kickoff.isoformat(),

            "fixture_snapshot_as_of_utc":
                report.get(
                    "fixture_snapshot_as_of_utc"
                ),

            "team_context_source_as_of_utc":
                report.get(
                    "team_context_source_as_of_utc"
                ),

            "freshness_mode":
                "DEPENDENCY_BASED_PLUS_TEMPORAL_BOUNDARY",

            "dependency_validation":
                True,

            "temporal_boundary_valid":
                True,

            "upstream_team_context_ready":
                True,

            "independent_validation":
                True,
        }

    # ========================================================
    # Public status
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
                    "8.5.4",

                "service":
                    "fixture_context",

                "season":
                    snapshot[
                        "season"
                    ],

                "fixture_count":
                    snapshot[
                        "fixture_count"
                    ],

                "column_count":
                    snapshot[
                        "column_count"
                    ],

                "source_column_count":
                    snapshot[
                        "source_column_count"
                    ],

                "context_column_count":
                    snapshot[
                        "context_column_count"
                    ],

                "earliest_fixture_kickoff_utc":
                    snapshot[
                        "earliest_fixture_kickoff_utc"
                    ],

                "latest_fixture_kickoff_utc":
                    snapshot[
                        "latest_fixture_kickoff_utc"
                    ],

                "fixture_snapshot_as_of_utc":
                    snapshot[
                        "fixture_snapshot_as_of_utc"
                    ],

                "team_context_source_as_of_utc":
                    snapshot[
                        "team_context_source_as_of_utc"
                    ],

                "freshness_mode":
                    snapshot[
                        "freshness_mode"
                    ],

                "dependency_validation":
                    True,

                "temporal_boundary_valid":
                    True,

                "upstream_team_context_ready":
                    True,

                "independent_validation":
                    True,
            }

        except FixtureContextNotReadyError as exc:

            return {

                "status":
                    "NOT_READY",

                "stage":
                    "8.5.4",

                "service":
                    "fixture_context",

                "reason":
                    str(exc),
            }

    # ========================================================
    # Public reads
    # ========================================================

    def get_all_fixture_context(
        self,
    ) -> list[dict]:

        snapshot = self._validate()

        return copy.deepcopy(
            snapshot[
                "rows"
            ]
        )

    def get_fixture_context(
        self,
        fixture_id,
    ) -> dict | None:

        query = str(
            fixture_id
        ).strip()

        if not query:

            return None

        rows = self.get_all_fixture_context()

        for row in rows:

            if (
                str(
                    row.get(
                        "fixture_id",
                        ""
                    )
                ).strip()
                == query
            ):

                return copy.deepcopy(row)

        return None

    def get_team_fixtures(
        self,
        team_name: str,
    ) -> list[dict]:

        query = str(
            team_name
        ).strip()

        if not query:

            return []

        query_key = query.casefold()

        rows = self.get_all_fixture_context()

        matched = []

        for row in rows:

            home_name = str(
                row.get(
                    "home_team_name",
                    ""
                )
            ).strip()

            away_name = str(
                row.get(
                    "away_team_name",
                    ""
                )
            ).strip()

            if (
                home_name.casefold()
                == query_key
                or
                away_name.casefold()
                == query_key
            ):

                matched.append(
                    copy.deepcopy(row)
                )

        return matched
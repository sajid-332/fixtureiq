"""
FixtureIQ Stage 8.5.3
Independent Fixture Context Validator.

Purpose:
- independently validate Stage 8.5.1 / 8.5.2
- independently reconstruct every enriched upcoming fixture
- verify exact source-fixture preservation
- verify exact home/away team-context preservation
- verify temporal safety
- verify dependency identity
- verify provenance
- verify context-only safety boundary

Important:
This validator DOES NOT use the Stage 8.5 enrichment builder.

No provider fetch.
No model execution.
No Stage 7 write.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from backend.services.team_context_builder import (
    TEAM_CONTEXT_FIELDS,
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
# Canonical schema
# ============================================================

REQUIRED_FIXTURE_FIELDS = [

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


TEAM_CONTEXT_VALUE_FIELDS = [

    field

    for field in TEAM_CONTEXT_FIELDS

    if field not in {
        "team_id",
        "team_name",
    }
]


HOME_CONTEXT_FIELDS = [

    f"home_team_{field}"

    for field in TEAM_CONTEXT_VALUE_FIELDS
]


AWAY_CONTEXT_FIELDS = [

    f"away_team_{field}"

    for field in TEAM_CONTEXT_VALUE_FIELDS
]


APPENDED_CONTEXT_FIELDS = (
    HOME_CONTEXT_FIELDS
    +
    AWAY_CONTEXT_FIELDS
)


STRING_CONTEXT_FIELDS = {

    "recent_results",
    "home_recent_results",
    "away_recent_results",
}


# ============================================================
# Error
# ============================================================

class FixtureContextValidationError(
    RuntimeError
):
    """Raised when Stage 8.5 fixture context is invalid."""


# ============================================================
# Helpers
# ============================================================

def _load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise FixtureContextValidationError(
            f"Required JSON artifact missing: {path}"
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

        raise FixtureContextValidationError(
            f"Invalid JSON artifact: {path}"
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):

        raise FixtureContextValidationError(
            f"Expected JSON object: {path}"
        )

    return payload


def _sha256_file(
    path: Path,
) -> str:

    if not path.exists():

        raise FixtureContextValidationError(
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

                digest.update(chunk)

    except OSError as exc:

        raise FixtureContextValidationError(
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

        raise FixtureContextValidationError(
            f"{field_name} missing or invalid."
        )

    text = value.strip()

    if not text:

        raise FixtureContextValidationError(
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

        raise FixtureContextValidationError(
            f"{field_name} is not valid ISO datetime."
        ) from exc

    if parsed.tzinfo is None:

        raise FixtureContextValidationError(
            f"{field_name} must be timezone-aware."
        )

    return parsed.astimezone(
        timezone.utc
    )


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


def _read_csv_raw(
    path: Path,
) -> tuple[
    list[str],
    list[dict],
]:

    if not path.exists():

        raise FixtureContextValidationError(
            f"CSV artifact missing: {path}"
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

            rows = list(reader)

    except OSError as exc:

        raise FixtureContextValidationError(
            f"Could not read CSV: {path}"
        ) from exc

    if not fields:

        raise FixtureContextValidationError(
            f"CSV schema empty: {path}"
        )

    for row_number, row in enumerate(
        rows,
        start=2,
    ):

        if None in row:

            raise FixtureContextValidationError(
                (
                    "Malformed CSV row with extra columns "
                    f"at row {row_number}: {path}"
                )
            )

    return (
        fields,
        rows,
    )


def _identify_date_field(
    fields: list[str],
) -> str:

    for candidate in DATE_FIELD_CANDIDATES:

        if candidate in fields:

            return candidate

    raise FixtureContextValidationError(
        (
            "Could not identify fixture kickoff field. "
            f"Candidates={DATE_FIELD_CANDIDATES}"
        )
    )


def _typed_enriched_rows(
    raw_rows: list[dict],
) -> list[dict]:

    rows = []

    for raw in raw_rows:

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

                        raise FixtureContextValidationError(
                            (
                                "Invalid enriched numerical field: "
                                f"{output_field}"
                            )
                        ) from exc

        rows.append(row)

    return rows


# ============================================================
# Validator
# ============================================================

class FixtureContextValidator:

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

    # ========================================================
    # Validate
    # ========================================================

    def validate(
        self,
        *,
        now_utc: datetime | None = None,
    ) -> dict:

        if now_utc is None:

            now_utc = datetime.now(
                timezone.utc
            )

        if now_utc.tzinfo is None:

            raise FixtureContextValidationError(
                "now_utc must be timezone-aware."
            )

        now_utc = now_utc.astimezone(
            timezone.utc
        )

        # ----------------------------------------------------
        # Load metadata
        # ----------------------------------------------------

        contract = _load_json(
            self.contract_file
        )

        contract_verification = _load_json(
            self.contract_verification_file
        )

        fixture_fetch_report = _load_json(
            self.fixture_fetch_report_file
        )

        team_context_report = _load_json(
            self.team_context_report_file
        )

        report = _load_json(
            self.fixture_context_report_file
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

            raise FixtureContextValidationError(
                "Stage 8.1 is not complete."
            )

        if (
            contract.get(
                "stage_8_1_status"
            )
            != "COMPLETE"
        ):

            raise FixtureContextValidationError(
                "Stage 8.1 status is not COMPLETE."
            )

        if (
            contract.get(
                "contract_status"
            )
            != "LOCKED_CONTEXT_CONTRACT"
        ):

            raise FixtureContextValidationError(
                "Stage 8 context contract is not locked."
            )

        if (
            contract_verification.get(
                "status"
            )
            != "PASS"
        ):

            raise FixtureContextValidationError(
                "Stage 8.1 verification is not PASS."
            )

        # ----------------------------------------------------
        # Stage 8.4 foundation
        # ----------------------------------------------------

        if (
            team_context_report.get(
                "stage_8_4_complete"
            )
            is not True
        ):

            raise FixtureContextValidationError(
                "Stage 8.4 is not complete."
            )

        if (
            team_context_report.get(
                "stage_8_4_status"
            )
            != "COMPLETE"
        ):

            raise FixtureContextValidationError(
                "Stage 8.4 status is not COMPLETE."
            )

        if (
            team_context_report.get(
                "unified_team_context_layer"
            )
            != "VERIFIED"
        ):

            raise FixtureContextValidationError(
                "Unified Team Context Layer not VERIFIED."
            )

        # ----------------------------------------------------
        # Stage 8.5 prior evidence
        # ----------------------------------------------------

        if (
            report.get(
                "stage"
            )
            != "8.5"
        ):

            raise FixtureContextValidationError(
                "fixture_context_report stage mismatch."
            )

        sub_stages = report.get(
            "sub_stages",
            {}
        )

        if (
            sub_stages.get(
                "8.5.1"
            )
            != "PASS"
        ):

            raise FixtureContextValidationError(
                "Stage 8.5.1 is not PASS."
            )

        if (
            sub_stages.get(
                "8.5.2"
            )
            != "PASS"
        ):

            raise FixtureContextValidationError(
                "Stage 8.5.2 is not PASS."
            )

        if (
            report.get(
                "upcoming_fixture_source_gate"
            )
            != "VERIFIED"
        ):

            raise FixtureContextValidationError(
                "Upcoming fixture source gate not VERIFIED."
            )

        if (
            report.get(
                "home_away_context_join"
            )
            != "VERIFIED"
        ):

            raise FixtureContextValidationError(
                "Home/Away context join not VERIFIED."
            )

        # ----------------------------------------------------
        # Existing fixture-fetch evidence
        # ----------------------------------------------------

        if (
            fixture_fetch_report.get(
                "stage"
            )
            != "7.8.2"
        ):

            raise FixtureContextValidationError(
                "Unexpected production fixture report stage."
            )

        if (
            fixture_fetch_report.get(
                "component"
            )
            != "production_fixture_fetch"
        ):

            raise FixtureContextValidationError(
                "Unexpected production fixture component."
            )

        if (
            fixture_fetch_report.get(
                "status"
            )
            != "PASS"
        ):

            raise FixtureContextValidationError(
                "Production fixture fetch report is not PASS."
            )

        if (
            fixture_fetch_report.get(
                "provider"
            )
            != "football-data.org"
        ):

            raise FixtureContextValidationError(
                "Unexpected production fixture provider."
            )

        if (
            fixture_fetch_report.get(
                "configured_season"
            )
            != 2026
        ):

            raise FixtureContextValidationError(
                "Production fixture season is not 2026."
            )

        # ----------------------------------------------------
        # TeamContextService
        # ----------------------------------------------------

        team_context_service = (
            TeamContextService()
        )

        context_status = (
            team_context_service.get_status()
        )

        if (
            context_status.get(
                "status"
            )
            != "READY"
        ):

            raise FixtureContextValidationError(
                (
                    "TeamContextService NOT_READY: "
                    f"{context_status.get('reason')}"
                )
            )

        contexts = (
            team_context_service
            .get_all_team_context()
        )

        if len(contexts) != 20:

            raise FixtureContextValidationError(
                (
                    "Expected 20 canonical team contexts, "
                    f"found {len(contexts)}."
                )
            )

        context_by_id = {}

        for context in contexts:

            if (
                list(
                    context.keys()
                )
                != TEAM_CONTEXT_FIELDS
            ):

                raise FixtureContextValidationError(
                    "Team context schema mismatch."
                )

            team_id = str(
                context[
                    "team_id"
                ]
            ).strip()

            team_name = str(
                context[
                    "team_name"
                ]
            ).strip()

            if not team_id or not team_name:

                raise FixtureContextValidationError(
                    "Blank canonical team identity."
                )

            if team_id in context_by_id:

                raise FixtureContextValidationError(
                    f"Duplicate team context ID: {team_id}"
                )

            context_by_id[
                team_id
            ] = context

        # ----------------------------------------------------
        # Source fixtures
        # ----------------------------------------------------

        (
            source_fields,
            source_rows,
        ) = _read_csv_raw(
            self.upcoming_fixtures_file
        )

        for field in REQUIRED_FIXTURE_FIELDS:

            if field not in source_fields:

                raise FixtureContextValidationError(
                    (
                        "Source fixture missing required field: "
                        f"{field}"
                    )
                )

        date_field = _identify_date_field(
            source_fields
        )

        if not source_rows:

            raise FixtureContextValidationError(
                "Upcoming fixture source is empty."
            )

        # ----------------------------------------------------
        # Enriched fixture artifact
        # ----------------------------------------------------

        (
            enriched_fields,
            enriched_raw_rows,
        ) = _read_csv_raw(
            self.enriched_fixtures_file
        )

        expected_fields = (
            source_fields
            +
            APPENDED_CONTEXT_FIELDS
        )

        if (
            enriched_fields
            != expected_fields
        ):

            raise FixtureContextValidationError(
                "Enriched fixture schema mismatch."
            )

        if len(
            enriched_fields
        ) != len(
            set(
                enriched_fields
            )
        ):

            raise FixtureContextValidationError(
                "Duplicate enriched fixture columns."
            )

        enriched_rows = _typed_enriched_rows(
            enriched_raw_rows
        )

        if (
            len(
                enriched_rows
            )
            != len(
                source_rows
            )
        ):

            raise FixtureContextValidationError(
                (
                    "Enrichment changed fixture row count: "
                    f"source={len(source_rows)}, "
                    f"enriched={len(enriched_rows)}"
                )
            )

        # ----------------------------------------------------
        # Temporal provenance
        # ----------------------------------------------------

        form_cutoff = _parse_aware_timestamp(
            report.get(
                "form_history_cutoff_utc"
            ),
            "form_history_cutoff_utc",
        )

        context_generated_at = (
            _parse_aware_timestamp(
                report.get(
                    "team_context_generated_at_utc"
                ),
                "team_context_generated_at_utc",
            )
        )

        context_source_as_of = (
            _parse_aware_timestamp(
                report.get(
                    "team_context_source_as_of_utc"
                ),
                "team_context_source_as_of_utc",
            )
        )

        fixture_snapshot_as_of = (
            _parse_aware_timestamp(
                report.get(
                    "fixture_snapshot_as_of_utc"
                ),
                "fixture_snapshot_as_of_utc",
            )
        )

        report_generated_at = (
            _parse_aware_timestamp(
                report.get(
                    "generated_at_utc"
                ),
                "generated_at_utc",
            )
        )

        if (
            context_generated_at
            !=
            _parse_aware_timestamp(
                team_context_report.get(
                    "generated_at_utc"
                ),
                "upstream team_context generated_at_utc",
            )
        ):

            raise FixtureContextValidationError(
                "Team-context generated-at provenance mismatch."
            )

        if (
            context_source_as_of
            !=
            _parse_aware_timestamp(
                team_context_report.get(
                    "source_as_of_utc"
                ),
                "upstream team_context source_as_of_utc",
            )
        ):

            raise FixtureContextValidationError(
                "Team-context source provenance mismatch."
            )

        if (
            form_cutoff
            !=
            _parse_aware_timestamp(
                team_context_report.get(
                    "form_history_cutoff_utc"
                ),
                "upstream form history cutoff",
            )
        ):

            raise FixtureContextValidationError(
                "Form-history-cutoff provenance mismatch."
            )

        # ----------------------------------------------------
        # Fixture snapshot provenance mode
        # ----------------------------------------------------

        provider_timestamp_available = (
            report.get(
                "fixture_provider_timestamp_available"
            )
        )

        provenance_mode = (
            report.get(
                "fixture_snapshot_provenance_mode"
            )
        )

        legacy_missing = (
            report.get(
                "legacy_fixture_report_timestamp_missing"
            )
        )

        source_field = (
            report.get(
                "fixture_snapshot_source_field"
            )
        )

        if (
            provider_timestamp_available
            is False
        ):

            if (
                provenance_mode
                !=
                "STAGE8_VERIFIED_ARTIFACT_OBSERVATION"
            ):

                raise FixtureContextValidationError(
                    "Legacy fixture provenance mode invalid."
                )

            if (
                legacy_missing
                is not True
            ):

                raise FixtureContextValidationError(
                    "Legacy missing-timestamp evidence invalid."
                )

            if (
                source_field
                !=
                "STAGE8_VERIFIED_ARTIFACT_OBSERVED_AT_UTC"
            ):

                raise FixtureContextValidationError(
                    "Legacy fixture timestamp source marker invalid."
                )

            observed_at = (
                _parse_aware_timestamp(
                    report.get(
                        "fixture_artifact_observed_at_utc"
                    ),
                    "fixture_artifact_observed_at_utc",
                )
            )

            if (
                observed_at
                != fixture_snapshot_as_of
            ):

                raise FixtureContextValidationError(
                    (
                        "Legacy fixture observation time does "
                        "not equal fixture snapshot as-of."
                    )
                )

        elif (
            provider_timestamp_available
            is True
        ):

            if (
                provenance_mode
                != "PROVIDER_REPORTED_TIMESTAMP"
            ):

                raise FixtureContextValidationError(
                    "Provider timestamp provenance mode invalid."
                )

            if legacy_missing is not False:

                raise FixtureContextValidationError(
                    "Provider timestamp marked legacy-missing."
                )

        else:

            raise FixtureContextValidationError(
                "fixture_provider_timestamp_available invalid."
            )

        if (
            report_generated_at
            <
            fixture_snapshot_as_of
        ):

            raise FixtureContextValidationError(
                (
                    "Fixture-context report generated before "
                    "fixture snapshot provenance time."
                )
            )

        # ----------------------------------------------------
        # Independently reconstruct every enriched fixture
        # ----------------------------------------------------

        fixture_ids = set()
        provider_fixture_ids = set()

        expected_rows_with_time = []
        source_by_fixture_id = {}

        all_fixture_team_ids = set()

        for source_row in source_rows:

            fixture_id = str(
                source_row.get(
                    "fixture_id",
                    ""
                )
            ).strip()

            if not fixture_id:

                raise FixtureContextValidationError(
                    "Blank fixture_id."
                )

            if fixture_id in fixture_ids:

                raise FixtureContextValidationError(
                    f"Duplicate fixture_id: {fixture_id}"
                )

            fixture_ids.add(
                fixture_id
            )

            source_by_fixture_id[
                fixture_id
            ] = dict(
                source_row
            )

            if (
                "provider_fixture_id"
                in source_fields
            ):

                provider_fixture_id = str(
                    source_row.get(
                        "provider_fixture_id",
                        ""
                    )
                ).strip()

                if provider_fixture_id:

                    if (
                        provider_fixture_id
                        in provider_fixture_ids
                    ):

                        raise FixtureContextValidationError(
                            (
                                "Duplicate provider_fixture_id: "
                                f"{provider_fixture_id}"
                            )
                        )

                    provider_fixture_ids.add(
                        provider_fixture_id
                    )

            home_team_id = str(
                source_row.get(
                    "home_team_id",
                    ""
                )
            ).strip()

            home_team_name = str(
                source_row.get(
                    "home_team_name",
                    ""
                )
            ).strip()

            away_team_id = str(
                source_row.get(
                    "away_team_id",
                    ""
                )
            ).strip()

            away_team_name = str(
                source_row.get(
                    "away_team_name",
                    ""
                )
            ).strip()

            if (
                not home_team_id
                or
                not home_team_name
                or
                not away_team_id
                or
                not away_team_name
            ):

                raise FixtureContextValidationError(
                    (
                        "Blank team identity for fixture "
                        f"{fixture_id}."
                    )
                )

            if (
                home_team_id
                == away_team_id
            ):

                raise FixtureContextValidationError(
                    (
                        "Same home/away team ID for fixture "
                        f"{fixture_id}."
                    )
                )

            if (
                home_team_name.casefold()
                == away_team_name.casefold()
            ):

                raise FixtureContextValidationError(
                    (
                        "Same home/away team name for fixture "
                        f"{fixture_id}."
                    )
                )

            home_context = (
                context_by_id.get(
                    home_team_id
                )
            )

            away_context = (
                context_by_id.get(
                    away_team_id
                )
            )

            if home_context is None:

                raise FixtureContextValidationError(
                    (
                        "Home team missing from canonical "
                        f"context: {home_team_id}"
                    )
                )

            if away_context is None:

                raise FixtureContextValidationError(
                    (
                        "Away team missing from canonical "
                        f"context: {away_team_id}"
                    )
                )

            if (
                home_context[
                    "team_name"
                ]
                != home_team_name
            ):

                raise FixtureContextValidationError(
                    (
                        "Home canonical-name mismatch for "
                        f"{fixture_id}."
                    )
                )

            if (
                away_context[
                    "team_name"
                ]
                != away_team_name
            ):

                raise FixtureContextValidationError(
                    (
                        "Away canonical-name mismatch for "
                        f"{fixture_id}."
                    )
                )

            all_fixture_team_ids.add(
                home_team_id
            )

            all_fixture_team_ids.add(
                away_team_id
            )

            kickoff = (
                _parse_aware_timestamp(
                    source_row.get(
                        date_field
                    ),
                    (
                        f"{date_field} for "
                        f"{fixture_id}"
                    ),
                )
            )

            if (
                kickoff
                <= now_utc
            ):

                raise FixtureContextValidationError(
                    (
                        "Fixture no longer future: "
                        f"{fixture_id}"
                    )
                )

            if (
                form_cutoff
                >= kickoff
            ):

                raise FixtureContextValidationError(
                    (
                        "Form cutoff not strictly before "
                        f"fixture {fixture_id}."
                    )
                )

            if (
                context_generated_at
                >= kickoff
            ):

                raise FixtureContextValidationError(
                    (
                        "Team context not generated strictly "
                        f"before fixture {fixture_id}."
                    )
                )

            expected_row = dict(
                source_row
            )

            for field in TEAM_CONTEXT_VALUE_FIELDS:

                expected_row[
                    f"home_team_{field}"
                ] = home_context[
                    field
                ]

            for field in TEAM_CONTEXT_VALUE_FIELDS:

                expected_row[
                    f"away_team_{field}"
                ] = away_context[
                    field
                ]

            if (
                list(
                    expected_row.keys()
                )
                != expected_fields
            ):

                raise FixtureContextValidationError(
                    (
                        "Expected enriched schema ordering "
                        f"invalid for {fixture_id}."
                    )
                )

            expected_rows_with_time.append(
                (
                    kickoff,
                    fixture_id,
                    expected_row,
                )
            )

        expected_rows_with_time.sort(
            key=lambda item: (
                item[0],
                item[1],
            )
        )

        expected_rows = [

            item[2]

            for item in expected_rows_with_time
        ]

        kickoffs = [

            item[0]

            for item in expected_rows_with_time
        ]

        if (
            enriched_rows
            != expected_rows
        ):

            raise FixtureContextValidationError(
                (
                    "Persisted enriched fixture artifact does "
                    "not equal independent reconstruction."
                )
            )

        # ----------------------------------------------------
        # Source field preservation
        # ----------------------------------------------------

        for enriched_row in enriched_rows:

            fixture_id = str(
                enriched_row[
                    "fixture_id"
                ]
            )

            source_row = source_by_fixture_id.get(
                fixture_id
            )

            if source_row is None:

                raise FixtureContextValidationError(
                    (
                        "Enriched fixture absent from source: "
                        f"{fixture_id}"
                    )
                )

            for field in source_fields:

                if (
                    enriched_row[
                        field
                    ]
                    != source_row[
                        field
                    ]
                ):

                    raise FixtureContextValidationError(
                        (
                            "Source fixture field changed during "
                            f"enrichment: fixture={fixture_id}, "
                            f"field={field}"
                        )
                    )

        # ----------------------------------------------------
        # Artifact report
        # ----------------------------------------------------

        artifact = report.get(
            "enriched_upcoming_fixtures",
            {}
        )

        actual_enriched_sha = (
            _sha256_file(
                self.enriched_fixtures_file
            )
        )

        if (
            artifact.get(
                "sha256"
            )
            != actual_enriched_sha
        ):

            raise FixtureContextValidationError(
                "Enriched fixture SHA mismatch."
            )

        if (
            artifact.get(
                "row_count"
            )
            != len(
                enriched_rows
            )
        ):

            raise FixtureContextValidationError(
                "Reported enriched row count mismatch."
            )

        if (
            artifact.get(
                "column_count"
            )
            != len(
                expected_fields
            )
        ):

            raise FixtureContextValidationError(
                "Reported enriched column count mismatch."
            )

        if (
            artifact.get(
                "source_column_count"
            )
            != len(
                source_fields
            )
        ):

            raise FixtureContextValidationError(
                "Reported source column count mismatch."
            )

        if (
            artifact.get(
                "context_column_count"
            )
            != 72
        ):

            raise FixtureContextValidationError(
                "Reported context column count must be 72."
            )

        if (
            artifact.get(
                "columns"
            )
            != expected_fields
        ):

            raise FixtureContextValidationError(
                "Reported enriched schema mismatch."
            )

        if (
            artifact.get(
                "team_namespace"
            )
            != "fixtureiq-team"
        ):

            raise FixtureContextValidationError(
                "Invalid enriched team namespace."
            )

        expected_sort_order = (
            f"{date_field} ASC, fixture_id ASC"
        )

        if (
            artifact.get(
                "sort_order"
            )
            != expected_sort_order
        ):

            raise FixtureContextValidationError(
                "Enriched fixture sort-order contract mismatch."
            )

        # ----------------------------------------------------
        # Source fixture report
        # ----------------------------------------------------

        fixture_source = report.get(
            "fixture_source",
            {}
        )

        if (
            fixture_source.get(
                "sha256"
            )
            !=
            _sha256_file(
                self.upcoming_fixtures_file
            )
        ):

            raise FixtureContextValidationError(
                "Fixture source SHA mismatch."
            )

        if (
            fixture_source.get(
                "row_count"
            )
            != len(
                source_rows
            )
        ):

            raise FixtureContextValidationError(
                "Fixture source row-count mismatch."
            )

        if (
            fixture_source.get(
                "column_count"
            )
            != len(
                source_fields
            )
        ):

            raise FixtureContextValidationError(
                "Fixture source column-count mismatch."
            )

        if (
            fixture_source.get(
                "columns"
            )
            != source_fields
        ):

            raise FixtureContextValidationError(
                "Fixture source schema mismatch."
            )

        if (
            fixture_source.get(
                "date_field"
            )
            != date_field
        ):

            raise FixtureContextValidationError(
                "Fixture source date-field mismatch."
            )

        # ----------------------------------------------------
        # Join contract
        # ----------------------------------------------------

        join = report.get(
            "context_join",
            {}
        )

        if (
            join.get(
                "type"
            )
            != "STRICT_CANONICAL_IDENTITY_JOIN"
        ):

            raise FixtureContextValidationError(
                "Context join type invalid."
            )

        required_true_join_flags = [

            "team_id_match_required",
            "team_name_match_required",
            "home_context_match",
            "away_context_match",
            "row_count_preserved",
        ]

        for flag in required_true_join_flags:

            if (
                join.get(flag)
                is not True
            ):

                raise FixtureContextValidationError(
                    f"Invalid context join flag: {flag}"
                )

        if (
            join.get(
                "fuzzy_matching_allowed"
            )
            is not False
        ):

            raise FixtureContextValidationError(
                "Fuzzy matching must be prohibited."
            )

        if (
            join.get(
                "missing_context_fallback_allowed"
            )
            is not False
        ):

            raise FixtureContextValidationError(
                "Missing-context fallback must be prohibited."
            )

        if (
            join.get(
                "context_fields_per_team"
            )
            != 36
        ):

            raise FixtureContextValidationError(
                "Expected 36 context fields per team."
            )

        if (
            join.get(
                "home_context_fields_appended"
            )
            != 36
            or
            join.get(
                "away_context_fields_appended"
            )
            != 36
            or
            join.get(
                "total_context_fields_appended"
            )
            != 72
        ):

            raise FixtureContextValidationError(
                "Home/Away context field counts invalid."
            )

        if (
            join.get(
                "source_rows"
            )
            != len(
                source_rows
            )
            or
            join.get(
                "output_rows"
            )
            != len(
                enriched_rows
            )
        ):

            raise FixtureContextValidationError(
                "Join row-count evidence invalid."
            )

        # ----------------------------------------------------
        # Temporal report
        # ----------------------------------------------------

        temporal = report.get(
            "temporal_gate",
            {}
        )

        temporal_true_flags = [

            "all_fixtures_future",
            "form_history_cutoff_before_all_fixtures",
            "team_context_generated_before_all_fixtures",
        ]

        for flag in temporal_true_flags:

            if (
                temporal.get(flag)
                is not True
            ):

                raise FixtureContextValidationError(
                    f"Invalid temporal flag: {flag}"
                )

        earliest_kickoff = min(
            kickoffs
        )

        latest_kickoff = max(
            kickoffs
        )

        if (
            _parse_aware_timestamp(
                report.get(
                    "earliest_fixture_kickoff_utc"
                ),
                "earliest_fixture_kickoff_utc",
            )
            != earliest_kickoff
        ):

            raise FixtureContextValidationError(
                "Earliest fixture kickoff mismatch."
            )

        if (
            _parse_aware_timestamp(
                report.get(
                    "latest_fixture_kickoff_utc"
                ),
                "latest_fixture_kickoff_utc",
            )
            != latest_kickoff
        ):

            raise FixtureContextValidationError(
                "Latest fixture kickoff mismatch."
            )

        # ----------------------------------------------------
        # Shared snapshot policy
        # ----------------------------------------------------

        snapshot_policy = report.get(
            "snapshot_policy",
            {}
        )

        if (
            snapshot_policy.get(
                "shared_context_snapshot"
            )
            is not True
        ):

            raise FixtureContextValidationError(
                "Shared context snapshot not enforced."
            )

        if (
            snapshot_policy.get(
                "future_fixture_state_propagation"
            )
            is not False
        ):

            raise FixtureContextValidationError(
                "Future fixture state propagation must be false."
            )

        if (
            snapshot_policy.get(
                "future_fixtures_update_each_other"
            )
            is not False
        ):

            raise FixtureContextValidationError(
                "Future fixtures must not update each other."
            )

        if (
            snapshot_policy.get(
                "pre_kickoff_context_only"
            )
            is not True
        ):

            raise FixtureContextValidationError(
                "Pre-kickoff context-only policy invalid."
            )

        # ----------------------------------------------------
        # Dependency identity
        # ----------------------------------------------------

        dependencies = report.get(
            "dependency_identity",
            {}
        )

        dependency_files = {

            "stage8_context_contract":
                self.contract_file,

            "stage8_context_contract_verification":
                self.contract_verification_file,

            "upcoming_fixtures":
                self.upcoming_fixtures_file,

            "production_fixture_fetch_report":
                self.fixture_fetch_report_file,

            "team_context":
                self.team_context_file,

            "team_context_report":
                self.team_context_report_file,
        }

        for (
            name,
            path,
        ) in dependency_files.items():

            expected_sha = (
                dependencies.get(
                    name,
                    {}
                ).get(
                    "sha256"
                )
            )

            actual_sha = (
                _sha256_file(
                    path
                )
            )

            if (
                expected_sha
                != actual_sha
            ):

                raise FixtureContextValidationError(
                    (
                        "Dependency identity mismatch: "
                        f"{name}"
                    )
                )

        expected_usage = {

            "upcoming_fixtures":
                "UPCOMING_FIXTURE_SOURCE",

            "production_fixture_fetch_report":
                "FIXTURE_SOURCE_PROVENANCE",

            "team_context":
                "FULL_HOME_AWAY_CONTEXT",

            "team_context_report":
                "VERIFIED_TEAM_CONTEXT_PROVENANCE",
        }

        for (
            name,
            usage,
        ) in expected_usage.items():

            if (
                dependencies.get(
                    name,
                    {}
                ).get(
                    "usage"
                )
                != usage
            ):

                raise FixtureContextValidationError(
                    (
                        "Dependency usage mismatch: "
                        f"{name}"
                    )
                )

        # ----------------------------------------------------
        # Locked output paths
        # ----------------------------------------------------

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
                "enriched_upcoming_fixtures",
                {}
            ).get(
                "path"
            )
            !=
            "data/processed/context/enriched_upcoming_fixtures.csv"
        ):

            raise FixtureContextValidationError(
                "Locked enriched-fixture output path invalid."
            )

        if (
            outputs.get(
                "fixture_context_report",
                {}
            ).get(
                "path"
            )
            !=
            "data/processed/context/fixture_context_report.json"
        ):

            raise FixtureContextValidationError(
                "Locked fixture-context report path invalid."
            )

        if (
            output_contract.get(
                "stage7_output_write_allowed"
            )
            is not False
        ):

            raise FixtureContextValidationError(
                "Stage 7 output write protection invalid."
            )

        # ----------------------------------------------------
        # Competition identity
        # ----------------------------------------------------

        if (
            report.get(
                "competition_code"
            )
            != "PL"
        ):

            raise FixtureContextValidationError(
                "Competition code must be PL."
            )

        if (
            report.get(
                "season"
            )
            != 2026
        ):

            raise FixtureContextValidationError(
                "Season must be 2026."
            )

        if (
            report.get(
                "team_namespace"
            )
            != "fixtureiq-team"
        ):

            raise FixtureContextValidationError(
                "Team namespace invalid."
            )

        if (
            report.get(
                "fixture_count"
            )
            != len(
                source_rows
            )
        ):

            raise FixtureContextValidationError(
                "Reported fixture count mismatch."
            )

        if (
            report.get(
                "context_team_count"
            )
            != 20
        ):

            raise FixtureContextValidationError(
                "Reported context team count mismatch."
            )

        # ----------------------------------------------------
        # Freshness
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

            raise FixtureContextValidationError(
                "Fixture freshness mode invalid."
            )

        freshness_true_flags = [

            "upcoming_fixture_change_invalidates_context",
            "fixture_fetch_report_change_invalidates_context",
            "team_context_change_invalidates_context",
            "team_context_report_change_invalidates_context",
            "fixture_kickoff_reached_invalidates_context",
            "legacy_fixture_timestamp_absence_tolerated",
            "fail_closed",
        ]

        for flag in freshness_true_flags:

            if (
                freshness.get(flag)
                is not True
            ):

                raise FixtureContextValidationError(
                    f"Invalid freshness flag: {flag}"
                )

        if (
            freshness.get(
                "stale_fallback_allowed"
            )
            is not False
        ):

            raise FixtureContextValidationError(
                "Stale fallback must be prohibited."
            )

        if (
            freshness.get(
                "partial_unverified_output_allowed"
            )
            is not False
        ):

            raise FixtureContextValidationError(
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

            raise FixtureContextValidationError(
                "Fixture enrichment not marked context-only."
            )

        false_safety_flags = [

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

        for flag in false_safety_flags:

            if (
                safety.get(flag)
                is not False
            ):

                raise FixtureContextValidationError(
                    f"Safety boundary invalid: {flag}"
                )

        # ----------------------------------------------------
        # Final independent result
        # ----------------------------------------------------

        return {

            "status":
                "PASS",

            "stage":
                "8.5.3",

            "fixture_count":
                len(
                    enriched_rows
                ),

            "source_column_count":
                len(
                    source_fields
                ),

            "context_fields_per_team":
                36,

            "context_fields_appended":
                72,

            "enriched_column_count":
                len(
                    expected_fields
                ),

            "fixture_ids_unique":
                True,

            "provider_fixture_ids_unique_when_present":
                True,

            "source_fields_preserved":
                True,

            "strict_home_identity_verified":
                True,

            "strict_away_identity_verified":
                True,

            "home_context_preservation_verified":
                True,

            "away_context_preservation_verified":
                True,

            "exact_independent_reconstruction_verified":
                True,

            "row_count_preserved":
                True,

            "deterministic_sort_verified":
                True,

            "all_fixtures_future":
                True,

            "form_cutoff_verified":
                True,

            "team_context_temporal_boundary_verified":
                True,

            "fixture_snapshot_provenance_verified":
                True,

            "shared_context_snapshot_verified":
                True,

            "future_fixture_state_propagation":
                False,

            "dependency_identity_verified":
                True,

            "freshness_contract_verified":
                True,

            "safety_verified":
                True,

            "earliest_fixture_kickoff_utc":
                earliest_kickoff.isoformat(),

            "latest_fixture_kickoff_utc":
                latest_kickoff.isoformat(),

            "enriched_artifact_sha256":
                actual_enriched_sha,

            "fixture_team_count":
                len(
                    all_fixture_team_ids
                ),
        }
"""
FixtureIQ Stage 8.5.1 + 8.5.2

8.5.1
Upcoming Fixture Source & Temporal Gate

8.5.2
Strict Home/Away Team Context Join

Rules:
- upcoming_fixtures.csv is READ_ONLY
- fixture IDs must be unique
- home/away identities must be canonical FixtureIQ identities
- all fixtures must still be future fixtures
- form-history cutoff must predate every fixture
- team-context snapshot must predate every fixture
- every fixture must match verified TeamContextService identities
- no fuzzy matching
- no missing-context fallback
- future fixtures never update one another's state
- exact source fixture columns are preserved
- 36 home context + 36 away context fields are appended

No provider fetch.
No model execution.
No prediction mutation.
"""

from __future__ import annotations

import csv
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

DEFAULT_UPCOMING_FIXTURES_FILE = (
    PRODUCTION_DIR
    / "upcoming_fixtures.csv"
)


# ============================================================
# Fixture contract
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


CONTEXT_FIELDS_APPENDED = (
    HOME_CONTEXT_FIELDS
    +
    AWAY_CONTEXT_FIELDS
)


# ============================================================
# Error
# ============================================================

class FixtureContextBuildError(
    RuntimeError
):
    """Raised when fixture context cannot be built safely."""


# ============================================================
# Time helpers
# ============================================================

def parse_aware_timestamp(
    value,
    field_name: str,
) -> datetime:

    if not isinstance(
        value,
        str,
    ):

        raise FixtureContextBuildError(
            f"{field_name} missing or invalid."
        )

    text = value.strip()

    if not text:

        raise FixtureContextBuildError(
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

        raise FixtureContextBuildError(
            (
                f"{field_name} must be a valid "
                "ISO datetime."
            )
        ) from exc

    if parsed.tzinfo is None:

        raise FixtureContextBuildError(
            (
                f"{field_name} must be "
                "timezone-aware."
            )
        )

    return parsed.astimezone(
        timezone.utc
    )


# ============================================================
# Source reader
# ============================================================

def read_upcoming_fixture_source(
    path: Path,
) -> dict:

    path = Path(
        path
    )

    if not path.exists():

        raise FixtureContextBuildError(
            f"Upcoming fixture source missing: {path}"
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

            rows = list(
                reader
            )

    except OSError as exc:

        raise FixtureContextBuildError(
            "Could not read upcoming fixtures."
        ) from exc

    if not fields:

        raise FixtureContextBuildError(
            "Upcoming fixture schema is empty."
        )

    missing_required = [

        field

        for field in REQUIRED_FIXTURE_FIELDS

        if field not in fields
    ]

    if missing_required:

        raise FixtureContextBuildError(
            (
                "Upcoming fixture source missing "
                f"required fields: {missing_required}"
            )
        )

    date_field = next(
        (
            candidate

            for candidate in DATE_FIELD_CANDIDATES

            if candidate in fields
        ),
        None,
    )

    if date_field is None:

        raise FixtureContextBuildError(
            (
                "Could not identify fixture kickoff field. "
                f"Candidates={DATE_FIELD_CANDIDATES}"
            )
        )

    if not rows:

        raise FixtureContextBuildError(
            "Upcoming fixture source contains zero fixtures."
        )

    # DictReader may create a None key if a malformed row
    # contains extra columns.
    for row_number, row in enumerate(
        rows,
        start=2,
    ):

        if None in row:

            raise FixtureContextBuildError(
                (
                    "Malformed fixture CSV row with extra "
                    f"columns at source row {row_number}."
                )
            )

    return {

        "path":
            path,

        "fields":
            fields,

        "rows":
            rows,

        "date_field":
            date_field,
    }


# ============================================================
# Main builder
# ============================================================

def build_enriched_fixture_context(
    *,
    upcoming_fixtures_file: Path | None = None,
    team_context_service: TeamContextService | None = None,
    form_history_cutoff_utc,
    context_generated_at_utc,
    now_utc: datetime | None = None,
) -> dict:

    upcoming_fixtures_file = (
        Path(
            upcoming_fixtures_file
        )
        if upcoming_fixtures_file is not None
        else DEFAULT_UPCOMING_FIXTURES_FILE
    )

    if team_context_service is None:

        team_context_service = (
            TeamContextService()
        )

    if now_utc is None:

        now_utc = datetime.now(
            timezone.utc
        )

    if now_utc.tzinfo is None:

        raise FixtureContextBuildError(
            "now_utc must be timezone-aware."
        )

    now_utc = now_utc.astimezone(
        timezone.utc
    )

    form_cutoff = parse_aware_timestamp(
        form_history_cutoff_utc,
        "form_history_cutoff_utc",
    )

    context_generated_at = (
        parse_aware_timestamp(
            context_generated_at_utc,
            "context_generated_at_utc",
        )
    )

    # ========================================================
    # Verified team-context layer
    # ========================================================

    context_status = (
        team_context_service.get_status()
    )

    if (
        context_status.get(
            "status"
        )
        != "READY"
    ):

        raise FixtureContextBuildError(
            (
                "TeamContextService is not READY: "
                f"{context_status.get('reason')}"
            )
        )

    contexts = (
        team_context_service
        .get_all_team_context()
    )

    if len(
        contexts
    ) != 20:

        raise FixtureContextBuildError(
            (
                "Expected 20 canonical context teams, "
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

            raise FixtureContextBuildError(
                "TeamContextService schema mismatch."
            )

        team_id = str(
            context.get(
                "team_id",
                ""
            )
        ).strip()

        team_name = str(
            context.get(
                "team_name",
                ""
            )
        ).strip()

        if (
            not team_id
            or
            not team_name
        ):

            raise FixtureContextBuildError(
                "Blank team identity in context service."
            )

        if team_id in context_by_id:

            raise FixtureContextBuildError(
                (
                    "Duplicate context team ID: "
                    f"{team_id}"
                )
            )

        context_by_id[
            team_id
        ] = context

    # ========================================================
    # Fixture source gate
    # ========================================================

    source = (
        read_upcoming_fixture_source(
            upcoming_fixtures_file
        )
    )

    source_fields = source[
        "fields"
    ]

    source_rows = source[
        "rows"
    ]

    date_field = source[
        "date_field"
    ]

    # New context fields must never overwrite source fields.
    collisions = sorted(
        set(
            source_fields
        )
        &
        set(
            CONTEXT_FIELDS_APPENDED
        )
    )

    if collisions:

        raise FixtureContextBuildError(
            (
                "Fixture/context column collision: "
                f"{collisions}"
            )
        )

    enriched_fields = (
        source_fields
        +
        CONTEXT_FIELDS_APPENDED
    )

    if len(
        enriched_fields
    ) != len(
        set(
            enriched_fields
        )
    ):

        raise FixtureContextBuildError(
            "Duplicate enriched fixture columns detected."
        )

    # ========================================================
    # Validate source identities / temporal boundary
    # ========================================================

    fixture_ids = set()
    provider_fixture_ids = set()

    enriched_with_time = []

    all_fixture_team_ids = set()

    for source_index, source_row in enumerate(
        source_rows
    ):

        fixture_id = str(
            source_row.get(
                "fixture_id",
                ""
            )
        ).strip()

        if not fixture_id:

            raise FixtureContextBuildError(
                (
                    "Blank fixture_id at source index "
                    f"{source_index}."
                )
            )

        if fixture_id in fixture_ids:

            raise FixtureContextBuildError(
                (
                    "Duplicate fixture_id: "
                    f"{fixture_id}"
                )
            )

        fixture_ids.add(
            fixture_id
        )

        # -----------------------------------------------
        # Optional provider fixture ID
        # -----------------------------------------------

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

                    raise FixtureContextBuildError(
                        (
                            "Duplicate provider_fixture_id: "
                            f"{provider_fixture_id}"
                        )
                    )

                provider_fixture_ids.add(
                    provider_fixture_id
                )

        # -----------------------------------------------
        # Team identities
        # -----------------------------------------------

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

            raise FixtureContextBuildError(
                (
                    "Blank fixture team identity for "
                    f"{fixture_id}."
                )
            )

        if (
            home_team_id
            == away_team_id
        ):

            raise FixtureContextBuildError(
                (
                    "Home and away team IDs are equal for "
                    f"{fixture_id}."
                )
            )

        if (
            home_team_name.casefold()
            == away_team_name.casefold()
        ):

            raise FixtureContextBuildError(
                (
                    "Home and away team names are equal for "
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

            raise FixtureContextBuildError(
                (
                    "Home team missing from verified "
                    f"context: {home_team_id}"
                )
            )

        if away_context is None:

            raise FixtureContextBuildError(
                (
                    "Away team missing from verified "
                    f"context: {away_team_id}"
                )
            )

        if (
            home_context[
                "team_name"
            ]
            != home_team_name
        ):

            raise FixtureContextBuildError(
                (
                    "Home canonical-name mismatch for "
                    f"{fixture_id}: "
                    f"fixture={home_team_name!r}, "
                    "context="
                    f"{home_context['team_name']!r}"
                )
            )

        if (
            away_context[
                "team_name"
            ]
            != away_team_name
        ):

            raise FixtureContextBuildError(
                (
                    "Away canonical-name mismatch for "
                    f"{fixture_id}: "
                    f"fixture={away_team_name!r}, "
                    "context="
                    f"{away_context['team_name']!r}"
                )
            )

        all_fixture_team_ids.add(
            home_team_id
        )

        all_fixture_team_ids.add(
            away_team_id
        )

        # -----------------------------------------------
        # Kickoff temporal gate
        # -----------------------------------------------

        kickoff = parse_aware_timestamp(
            source_row.get(
                date_field
            ),
            (
                f"{date_field} for fixture "
                f"{fixture_id}"
            ),
        )

        if (
            kickoff
            <= now_utc
        ):

            raise FixtureContextBuildError(
                (
                    "Upcoming fixture is not in the future: "
                    f"{fixture_id} @ {kickoff.isoformat()}"
                )
            )

        if (
            form_cutoff
            >= kickoff
        ):

            raise FixtureContextBuildError(
                (
                    "Form history cutoff is not strictly "
                    "before fixture kickoff: "
                    f"{fixture_id}"
                )
            )

        if (
            context_generated_at
            >= kickoff
        ):

            raise FixtureContextBuildError(
                (
                    "Team-context snapshot was not created "
                    "strictly before fixture kickoff: "
                    f"{fixture_id}"
                )
            )

        # ====================================================
        # Strict home / away context enrichment
        # ====================================================

        enriched = dict(
            source_row
        )

        for field in TEAM_CONTEXT_VALUE_FIELDS:

            enriched[
                f"home_team_{field}"
            ] = home_context[
                field
            ]

        for field in TEAM_CONTEXT_VALUE_FIELDS:

            enriched[
                f"away_team_{field}"
            ] = away_context[
                field
            ]

        if (
            list(
                enriched.keys()
            )
            != enriched_fields
        ):

            raise FixtureContextBuildError(
                (
                    "Enriched field ordering mismatch for "
                    f"{fixture_id}."
                )
            )

        enriched_with_time.append(
            (
                kickoff,
                fixture_id,
                enriched,
            )
        )

    # ========================================================
    # Deterministic fixture ordering
    # ========================================================

    enriched_with_time.sort(
        key=lambda item: (
            item[
                0
            ],
            item[
                1
            ],
        )
    )

    enriched_rows = [

        item[
            2
        ]

        for item in enriched_with_time
    ]

    kickoffs = [

        item[
            0
        ]

        for item in enriched_with_time
    ]

    if len(
        enriched_rows
    ) != len(
        source_rows
    ):

        raise FixtureContextBuildError(
            "Fixture enrichment changed row count."
        )

    if not enriched_rows:

        raise FixtureContextBuildError(
            "Fixture enrichment produced zero rows."
        )

    # Every current EPL team should be represented somewhere
    # in the upcoming season fixture set.
    unknown_fixture_teams = (
        all_fixture_team_ids
        -
        set(
            context_by_id
        )
    )

    if unknown_fixture_teams:

        raise FixtureContextBuildError(
            (
                "Unknown fixture teams remain after join: "
                f"{sorted(unknown_fixture_teams)}"
            )
        )

    return {

        "team_context_status":
            context_status,

        "source_fields":
            source_fields,

        "date_field":
            date_field,

        "source_rows":
            source_rows,

        "source_row_count":
            len(
                source_rows
            ),

        "enriched_fields":
            enriched_fields,

        "enriched_rows":
            enriched_rows,

        "enriched_row_count":
            len(
                enriched_rows
            ),

        "source_column_count":
            len(
                source_fields
            ),

        "context_fields_per_team":
            len(
                TEAM_CONTEXT_VALUE_FIELDS
            ),

        "context_fields_appended":
            len(
                CONTEXT_FIELDS_APPENDED
            ),

        "enriched_column_count":
            len(
                enriched_fields
            ),

        "fixture_id_count":
            len(
                fixture_ids
            ),

        "provider_fixture_id_count":
            len(
                provider_fixture_ids
            ),

        "fixture_team_count":
            len(
                all_fixture_team_ids
            ),

        "all_fixtures_future":
            True,

        "form_cutoff_before_all_fixtures":
            True,

        "context_generated_before_all_fixtures":
            True,

        "earliest_fixture_kickoff_utc":
            min(
                kickoffs
            ).isoformat(),

        "latest_fixture_kickoff_utc":
            max(
                kickoffs
            ).isoformat(),

        "form_history_cutoff_utc":
            form_cutoff.isoformat(),

        "context_generated_at_utc":
            context_generated_at.isoformat(),

        "build_now_utc":
            now_utc.isoformat(),

        "home_context_match":
            True,

        "away_context_match":
            True,

        "shared_context_snapshot":
            True,

        "future_fixture_state_propagation":
            False,

        "sort_order":
            f"{date_field} ASC, fixture_id ASC",
    }
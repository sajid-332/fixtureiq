"""
FixtureIQ Stage 8.4.1 + 8.4.2

Unified Team Context Builder.

8.4.1
- require verified StandingsService READY
- require verified TeamFormService READY
- require exact one-to-one FixtureIQ team identity match

8.4.2
- join standings + current form
- create canonical 20-team / 38-column context snapshot

This module does NOT:
- fetch provider data
- rebuild standings
- rebuild form
- run/load/modify the prediction model
- modify predictions
- modify Stage 7 artifacts
"""

from __future__ import annotations

from backend.services.standings_service import (
    StandingsService,
)

from backend.services.team_form_service import (
    TeamFormService,
)


# ============================================================
# Canonical schema
# ============================================================

TEAM_CONTEXT_FIELDS = [

    "team_id",
    "team_name",

    # Standings
    "position",
    "played",
    "won",
    "drawn",
    "lost",
    "goals_for",
    "goals_against",
    "goal_difference",
    "points",

    # Overall form
    "form_matches_available",
    "recent_results",
    "recent_points",
    "recent_wins",
    "recent_draws",
    "recent_losses",
    "recent_goals_for",
    "recent_goals_against",
    "recent_goal_difference",

    # Home form
    "home_form_matches_available",
    "home_recent_results",
    "home_recent_points",
    "home_recent_wins",
    "home_recent_draws",
    "home_recent_losses",
    "home_recent_goals_for",
    "home_recent_goals_against",
    "home_recent_goal_difference",

    # Away form
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


STANDINGS_VALUE_FIELDS = [

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


FORM_VALUE_FIELDS = [

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


class TeamContextBuildError(
    RuntimeError
):
    """Raised when unified team context cannot be built safely."""


def build_team_context(
    *,
    standings_service: StandingsService | None = None,
    team_form_service: TeamFormService | None = None,
) -> dict:

    if standings_service is None:

        standings_service = (
            StandingsService()
        )

    if team_form_service is None:

        team_form_service = (
            TeamFormService()
        )

    # ========================================================
    # Stage 8.4.1 readiness gate
    # ========================================================

    standings_status = (
        standings_service.get_status()
    )

    form_status = (
        team_form_service.get_status()
    )

    if (
        standings_status.get(
            "status"
        )
        != "READY"
    ):

        raise TeamContextBuildError(
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

        raise TeamContextBuildError(
            (
                "TeamFormService is not READY: "
                f"{form_status.get('reason')}"
            )
        )

    standings = (
        standings_service
        .get_standings()
    )

    forms = (
        team_form_service
        .get_all_team_form()
    )

    if len(
        standings
    ) != 20:

        raise TeamContextBuildError(
            (
                "Expected 20 standings teams, "
                f"found {len(standings)}."
            )
        )

    if len(
        forms
    ) != 20:

        raise TeamContextBuildError(
            (
                "Expected 20 team-form rows, "
                f"found {len(forms)}."
            )
        )

    standings_by_id = {}

    for row in standings:

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

            raise TeamContextBuildError(
                "Blank identity in standings service."
            )

        if team_id in standings_by_id:

            raise TeamContextBuildError(
                (
                    "Duplicate standings FixtureIQ "
                    f"team ID: {team_id}"
                )
            )

        standings_by_id[
            team_id
        ] = row

    forms_by_id = {}

    for row in forms:

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

            raise TeamContextBuildError(
                "Blank identity in team-form service."
            )

        if team_id in forms_by_id:

            raise TeamContextBuildError(
                (
                    "Duplicate team-form FixtureIQ "
                    f"team ID: {team_id}"
                )
            )

        forms_by_id[
            team_id
        ] = row

    standings_ids = set(
        standings_by_id
    )

    form_ids = set(
        forms_by_id
    )

    if (
        standings_ids
        != form_ids
    ):

        missing_from_form = sorted(
            standings_ids
            - form_ids
        )

        missing_from_standings = sorted(
            form_ids
            - standings_ids
        )

        raise TeamContextBuildError(
            (
                "Standings/form team identity sets differ. "
                f"Missing from form={missing_from_form}; "
                "missing from standings="
                f"{missing_from_standings}"
            )
        )

    # Exact ID + canonical name match.
    for team_id in sorted(
        standings_ids
    ):

        standings_name = str(
            standings_by_id[
                team_id
            ][
                "team_name"
            ]
        ).strip()

        form_name = str(
            forms_by_id[
                team_id
            ][
                "team_name"
            ]
        ).strip()

        if (
            standings_name
            != form_name
        ):

            raise TeamContextBuildError(
                (
                    "Canonical team-name mismatch for "
                    f"{team_id}: "
                    f"standings={standings_name!r}, "
                    f"form={form_name!r}"
                )
            )

    # ========================================================
    # Stage 8.4.2 strict one-to-one join
    # ========================================================

    joined_rows = []

    for team_id in standings_ids:

        standings_row = (
            standings_by_id[
                team_id
            ]
        )

        form_row = (
            forms_by_id[
                team_id
            ]
        )

        context_row = {

            "team_id":
                team_id,

            "team_name":
                standings_row[
                    "team_name"
                ],
        }

        for field in STANDINGS_VALUE_FIELDS:

            if field not in standings_row:

                raise TeamContextBuildError(
                    (
                        "Missing standings field "
                        f"{field!r} for "
                        f"{context_row['team_name']}."
                    )
                )

            context_row[
                field
            ] = standings_row[
                field
            ]

        for field in FORM_VALUE_FIELDS:

            if field not in form_row:

                raise TeamContextBuildError(
                    (
                        "Missing form field "
                        f"{field!r} for "
                        f"{context_row['team_name']}."
                    )
                )

            context_row[
                field
            ] = form_row[
                field
            ]

        if (
            list(
                context_row.keys()
            )
            != TEAM_CONTEXT_FIELDS
        ):

            raise TeamContextBuildError(
                (
                    "Canonical team-context field ordering "
                    f"failed for {context_row['team_name']}."
                )
            )

        joined_rows.append(
            context_row
        )

    joined_rows.sort(
        key=lambda row:
            row[
                "team_name"
            ].casefold()
    )

    if len(
        joined_rows
    ) != 20:

        raise TeamContextBuildError(
            (
                "Unified context must contain exactly "
                f"20 teams, found {len(joined_rows)}."
            )
        )

    if len(
        {
            row[
                "team_id"
            ]
            for row in joined_rows
        }
    ) != 20:

        raise TeamContextBuildError(
            "Unified context team IDs are not unique."
        )

    if len(
        {
            row[
                "team_name"
            ].casefold()
            for row in joined_rows
        }
    ) != 20:

        raise TeamContextBuildError(
            "Unified context team names are not unique."
        )

    return {

        "standings_status":
            standings_status,

        "team_form_status":
            form_status,

        "standings_rows":
            standings,

        "form_rows":
            forms,

        "rows":
            joined_rows,

        "identity_match":
            True,

        "join_cardinality":
            "ONE_TO_ONE",

        "team_count":
            20,
    }
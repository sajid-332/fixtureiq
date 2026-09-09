"""
FixtureIQ Stage 8.3.3
Canonical Current Team Form Builder.

Builds:
- overall latest up-to-5 current-season form
- home latest up-to-5 current-season form
- away latest up-to-5 current-season form

Rules:
- production season 2026 only
- completed matches only
- no previous-season padding
- short windows allowed
- OLDEST_TO_NEWEST
- most recent result RIGHTMOST
- FixtureIQ canonical team identity
"""

from __future__ import annotations

from backend.services.team_form_engine import (
    FORM_WINDOW,
    TeamFormEngine,
    TeamFormSourceError,
)


FORM_FIELDS = [

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


class TeamFormBuildError(
    RuntimeError
):
    """Raised when canonical team form cannot be built safely."""


def _build_form_block(
    matches: list[dict],
    team_id: str,
    *,
    mode: str,
    window: int = FORM_WINDOW,
) -> dict:

    mode = str(
        mode
    ).strip().upper()

    if mode not in {
        "OVERALL",
        "HOME",
        "AWAY",
    }:

        raise TeamFormBuildError(
            f"Unsupported form mode: {mode}"
        )

    relevant = []

    for match in matches:

        is_home = (
            match[
                "home_team_id"
            ]
            == team_id
        )

        is_away = (
            match[
                "away_team_id"
            ]
            == team_id
        )

        if mode == "OVERALL":

            include = (
                is_home
                or
                is_away
            )

        elif mode == "HOME":

            include = is_home

        else:

            include = is_away

        if include:

            relevant.append(
                match
            )

    # Source matches are already chronological.
    selected = relevant[
        -window:
    ]

    results = []

    wins = 0
    draws = 0
    losses = 0

    goals_for = 0
    goals_against = 0

    evidence = []

    for match in selected:

        is_home = (
            match[
                "home_team_id"
            ]
            == team_id
        )

        if is_home:

            team_goals = (
                match[
                    "home_goals"
                ]
            )

            opponent_goals = (
                match[
                    "away_goals"
                ]
            )

            opponent_id = (
                match[
                    "away_team_id"
                ]
            )

            opponent_name = (
                match[
                    "away_team_name"
                ]
            )

            venue = "HOME"

        else:

            team_goals = (
                match[
                    "away_goals"
                ]
            )

            opponent_goals = (
                match[
                    "home_goals"
                ]
            )

            opponent_id = (
                match[
                    "home_team_id"
                ]
            )

            opponent_name = (
                match[
                    "home_team_name"
                ]
            )

            venue = "AWAY"

        if (
            team_goals
            >
            opponent_goals
        ):

            result = "W"
            wins += 1

        elif (
            team_goals
            ==
            opponent_goals
        ):

            result = "D"
            draws += 1

        else:

            result = "L"
            losses += 1

        results.append(
            result
        )

        goals_for += (
            team_goals
        )

        goals_against += (
            opponent_goals
        )

        evidence.append(
            {
                "date_utc":
                    match[
                        "date_utc"
                    ].isoformat(),

                "venue":
                    venue,

                "opponent_team_id":
                    opponent_id,

                "opponent_team_name":
                    opponent_name,

                "goals_for":
                    team_goals,

                "goals_against":
                    opponent_goals,

                "result":
                    result,
            }
        )

    matches_available = len(
        selected
    )

    recent_results = "".join(
        results
    )

    recent_points = (
        3 * wins
        + draws
    )

    goal_difference = (
        goals_for
        - goals_against
    )

    # ========================================================
    # Invariants
    # ========================================================

    if matches_available > window:

        raise TeamFormBuildError(
            (
                f"{mode} form exceeded "
                f"window={window}."
            )
        )

    if (
        matches_available
        !=
        wins + draws + losses
    ):

        raise TeamFormBuildError(
            f"{mode} form count invariant failed."
        )

    if (
        len(
            recent_results
        )
        != matches_available
    ):

        raise TeamFormBuildError(
            (
                f"{mode} result-string "
                "length invariant failed."
            )
        )

    if not set(
        recent_results
    ).issubset(
        {
            "W",
            "D",
            "L",
        }
    ):

        raise TeamFormBuildError(
            f"{mode} contains invalid result symbols."
        )

    if (
        recent_points
        !=
        3 * wins + draws
    ):

        raise TeamFormBuildError(
            f"{mode} points invariant failed."
        )

    if (
        goal_difference
        !=
        goals_for - goals_against
    ):

        raise TeamFormBuildError(
            f"{mode} goal-difference invariant failed."
        )

    return {

        "matches_available":
            matches_available,

        "recent_results":
            recent_results,

        "recent_points":
            recent_points,

        "recent_wins":
            wins,

        "recent_draws":
            draws,

        "recent_losses":
            losses,

        "recent_goals_for":
            goals_for,

        "recent_goals_against":
            goals_against,

        "recent_goal_difference":
            goal_difference,

        "selected_matches":
            evidence,
    }


def build_current_team_form(
    engine: TeamFormEngine | None = None,
) -> dict:

    if engine is None:

        engine = TeamFormEngine(
            season=2026,
            window=5,
        )

    gated = (
        engine.load_current_season_matches()
    )

    matches = gated[
        "matches"
    ]

    # Existing verified 8.3.2 implementation acts as a
    # cross-check for our independently calculated overall block.
    verified_overall = (
        engine.build_overall_form(
            gated
        )
    )

    verified_overall_by_id = {

        row[
            "team_id"
        ]:
            row

        for row in verified_overall
    }

    teams = sorted(
        engine.team_by_id.values(),
        key=lambda team:
            team[
                "team_name"
            ].casefold(),
    )

    rows = []

    evidence = []

    for team in teams:

        team_id = (
            team[
                "team_id"
            ]
        )

        team_name = (
            team[
                "team_name"
            ]
        )

        overall = (
            _build_form_block(
                matches,
                team_id,
                mode="OVERALL",
                window=5,
            )
        )

        home = (
            _build_form_block(
                matches,
                team_id,
                mode="HOME",
                window=5,
            )
        )

        away = (
            _build_form_block(
                matches,
                team_id,
                mode="AWAY",
                window=5,
            )
        )

        # ====================================================
        # Cross-check 8.3.2 overall engine
        # ====================================================

        reference = (
            verified_overall_by_id.get(
                team_id
            )
        )

        if reference is None:

            raise TeamFormBuildError(
                (
                    "Missing verified overall form for "
                    f"{team_name}."
                )
            )

        comparison_pairs = {

            "form_matches_available":
                overall[
                    "matches_available"
                ],

            "recent_results":
                overall[
                    "recent_results"
                ],

            "recent_points":
                overall[
                    "recent_points"
                ],

            "recent_wins":
                overall[
                    "recent_wins"
                ],

            "recent_draws":
                overall[
                    "recent_draws"
                ],

            "recent_losses":
                overall[
                    "recent_losses"
                ],

            "recent_goals_for":
                overall[
                    "recent_goals_for"
                ],

            "recent_goals_against":
                overall[
                    "recent_goals_against"
                ],

            "recent_goal_difference":
                overall[
                    "recent_goal_difference"
                ],
        }

        for (
            field,
            calculated_value,
        ) in comparison_pairs.items():

            if (
                reference.get(
                    field
                )
                != calculated_value
            ):

                raise TeamFormBuildError(
                    (
                        "8.3.2 overall-form cross-check "
                        f"failed for {team_name}: {field}"
                    )
                )

        # ====================================================
        # Public canonical row
        # ====================================================

        row = {

            "team_id":
                team_id,

            "team_name":
                team_name,

            # Overall
            "form_matches_available":
                overall[
                    "matches_available"
                ],

            "recent_results":
                overall[
                    "recent_results"
                ],

            "recent_points":
                overall[
                    "recent_points"
                ],

            "recent_wins":
                overall[
                    "recent_wins"
                ],

            "recent_draws":
                overall[
                    "recent_draws"
                ],

            "recent_losses":
                overall[
                    "recent_losses"
                ],

            "recent_goals_for":
                overall[
                    "recent_goals_for"
                ],

            "recent_goals_against":
                overall[
                    "recent_goals_against"
                ],

            "recent_goal_difference":
                overall[
                    "recent_goal_difference"
                ],

            # Home
            "home_form_matches_available":
                home[
                    "matches_available"
                ],

            "home_recent_results":
                home[
                    "recent_results"
                ],

            "home_recent_points":
                home[
                    "recent_points"
                ],

            "home_recent_wins":
                home[
                    "recent_wins"
                ],

            "home_recent_draws":
                home[
                    "recent_draws"
                ],

            "home_recent_losses":
                home[
                    "recent_losses"
                ],

            "home_recent_goals_for":
                home[
                    "recent_goals_for"
                ],

            "home_recent_goals_against":
                home[
                    "recent_goals_against"
                ],

            "home_recent_goal_difference":
                home[
                    "recent_goal_difference"
                ],

            # Away
            "away_form_matches_available":
                away[
                    "matches_available"
                ],

            "away_recent_results":
                away[
                    "recent_results"
                ],

            "away_recent_points":
                away[
                    "recent_points"
                ],

            "away_recent_wins":
                away[
                    "recent_wins"
                ],

            "away_recent_draws":
                away[
                    "recent_draws"
                ],

            "away_recent_losses":
                away[
                    "recent_losses"
                ],

            "away_recent_goals_for":
                away[
                    "recent_goals_for"
                ],

            "away_recent_goals_against":
                away[
                    "recent_goals_against"
                ],

            "away_recent_goal_difference":
                away[
                    "recent_goal_difference"
                ],
        }

        if (
            list(
                row.keys()
            )
            != FORM_FIELDS
        ):

            raise TeamFormBuildError(
                (
                    "Canonical form field ordering "
                    f"failed for {team_name}."
                )
            )

        rows.append(
            row
        )

        evidence.append(
            {

                "team_id":
                    team_id,

                "team_name":
                    team_name,

                "overall_selected_matches":
                    overall[
                        "selected_matches"
                    ],

                "home_selected_matches":
                    home[
                        "selected_matches"
                    ],

                "away_selected_matches":
                    away[
                        "selected_matches"
                    ],
            }
        )

    if len(
        rows
    ) != 20:

        raise TeamFormBuildError(
            (
                "Canonical form snapshot must contain "
                f"20 teams, found {len(rows)}."
            )
        )

    if len(
        {
            row[
                "team_id"
            ]
            for row in rows
        }
    ) != 20:

        raise TeamFormBuildError(
            "Canonical team IDs are not unique."
        )

    return {

        "gated_source":
            gated,

        "rows":
            rows,

        "evidence":
            evidence,
    }
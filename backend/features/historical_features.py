"""
FixtureIQ Stage 7.4.2
Time-Based Historical Feature Construction.

All features for a fixture are calculated exclusively from
matches occurring before that fixture.

No current-match goals or outcome are used as input features.
"""

from collections import defaultdict, deque
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

FEATURE_DATASET_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "model_features.csv"
)

FEATURE_METADATA_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "feature_metadata.json"
)


# ============================================================
# Team state
# ============================================================

def empty_team_state():
    return {
        "matches": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "points": 0,
        "goals_for": 0,
        "goals_against": 0,
        "home_matches": 0,
        "home_wins": 0,
        "home_draws": 0,
        "home_losses": 0,
        "home_goals_for": 0,
        "home_goals_against": 0,
        "away_matches": 0,
        "away_wins": 0,
        "away_draws": 0,
        "away_losses": 0,
        "away_goals_for": 0,
        "away_goals_against": 0,
        "recent": deque(maxlen=10),
    }


def copy_state(
    state,
):
    return {
        key: (
            deque(
                value,
                maxlen=10,
            )
            if isinstance(
                value,
                deque,
            )
            else value
        )
        for key, value in state.items()
    }


# ============================================================
# Statistics
# ============================================================

def safe_average(
    value,
    matches,
):
    if matches == 0:
        return 0.0

    return value / matches


def recent_statistics(
    recent_matches,
):
    if not recent_matches:

        return {
            "matches": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "points": 0,
            "goals_for": 0,
            "goals_against": 0,
        }

    wins = sum(
        item["result"] == "W"
        for item in recent_matches
    )

    draws = sum(
        item["result"] == "D"
        for item in recent_matches
    )

    losses = sum(
        item["result"] == "L"
        for item in recent_matches
    )

    goals_for = sum(
        item["goals_for"]
        for item in recent_matches
    )

    goals_against = sum(
        item["goals_against"]
        for item in recent_matches
    )

    points = (
        wins * 3
        +
        draws
    )

    return {
        "matches": len(
            recent_matches
        ),
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "points": points,
        "goals_for": goals_for,
        "goals_against": goals_against,
    }


# ============================================================
# Pre-match feature extraction
# ============================================================

def team_features(
    state,
    prefix,
):
    recent = recent_statistics(
        state["recent"]
    )

    matches = state["matches"]

    features = {
        f"{prefix}_matches": matches,

        f"{prefix}_wins":
            state["wins"],

        f"{prefix}_draws":
            state["draws"],

        f"{prefix}_losses":
            state["losses"],

        f"{prefix}_points":
            state["points"],

        f"{prefix}_points_per_match":
            safe_average(
                state["points"],
                matches,
            ),

        f"{prefix}_goals_for":
            state["goals_for"],

        f"{prefix}_goals_against":
            state["goals_against"],

        f"{prefix}_goals_for_per_match":
            safe_average(
                state["goals_for"],
                matches,
            ),

        f"{prefix}_goals_against_per_match":
            safe_average(
                state["goals_against"],
                matches,
            ),

        f"{prefix}_goal_difference":
            (
                state["goals_for"]
                -
                state["goals_against"]
            ),

        # Home

        f"{prefix}_home_matches":
            state["home_matches"],

        f"{prefix}_home_wins":
            state["home_wins"],

        f"{prefix}_home_draws":
            state["home_draws"],

        f"{prefix}_home_losses":
            state["home_losses"],

        f"{prefix}_home_goals_for":
            state["home_goals_for"],

        f"{prefix}_home_goals_against":
            state["home_goals_against"],

        # Away

        f"{prefix}_away_matches":
            state["away_matches"],

        f"{prefix}_away_wins":
            state["away_wins"],

        f"{prefix}_away_draws":
            state["away_draws"],

        f"{prefix}_away_losses":
            state["away_losses"],

        f"{prefix}_away_goals_for":
            state["away_goals_for"],

        f"{prefix}_away_goals_against":
            state["away_goals_against"],

        # Recent 5/10

        f"{prefix}_last10_matches":
            recent["matches"],

        f"{prefix}_last10_wins":
            recent["wins"],

        f"{prefix}_last10_draws":
            recent["draws"],

        f"{prefix}_last10_losses":
            recent["losses"],

        f"{prefix}_last10_points":
            recent["points"],

        f"{prefix}_last10_goals_for":
            recent["goals_for"],

        f"{prefix}_last10_goals_against":
            recent["goals_against"],
    }

    last5 = list(
        state["recent"]
    )[-5:]

    recent5 = recent_statistics(
        last5
    )

    features.update(
        {
            f"{prefix}_last5_matches":
                recent5["matches"],

            f"{prefix}_last5_wins":
                recent5["wins"],

            f"{prefix}_last5_draws":
                recent5["draws"],

            f"{prefix}_last5_losses":
                recent5["losses"],

            f"{prefix}_last5_points":
                recent5["points"],

            f"{prefix}_last5_goals_for":
                recent5["goals_for"],

            f"{prefix}_last5_goals_against":
                recent5["goals_against"],
        }
    )

    return features


# ============================================================
# Update team state after a completed match
# ============================================================

def update_team_state(
    state,
    result,
    goals_for,
    goals_against,
    venue,
):
    state["matches"] += 1

    state["goals_for"] += goals_for

    state["goals_against"] += goals_against

    if result == "W":

        state["wins"] += 1
        state["points"] += 3

    elif result == "D":

        state["draws"] += 1
        state["points"] += 1

    else:

        state["losses"] += 1

    if venue == "home":

        state["home_matches"] += 1

        state["home_goals_for"] += goals_for

        state["home_goals_against"] += (
            goals_against
        )

        if result == "W":
            state["home_wins"] += 1

        elif result == "D":
            state["home_draws"] += 1

        else:
            state["home_losses"] += 1

    else:

        state["away_matches"] += 1

        state["away_goals_for"] += goals_for

        state["away_goals_against"] += (
            goals_against
        )

        if result == "W":
            state["away_wins"] += 1

        elif result == "D":
            state["away_draws"] += 1

        else:
            state["away_losses"] += 1

    state["recent"].append(
        {
            "result": result,
            "goals_for": goals_for,
            "goals_against": goals_against,
        }
    )


# ============================================================
# Feature construction
# ============================================================

def build_historical_features(
    dataframe: pd.DataFrame,
):
    """
    Build strictly pre-match historical features.

    A row's features are generated BEFORE its result is
    added to the relevant team states.
    """

    dataframe = dataframe.copy()

    dataframe = (
        dataframe
        .sort_values(
            [
                "date",
                "fixture_id",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    states = defaultdict(
        empty_team_state
    )

    output_rows = []

    for _, match in dataframe.iterrows():

        home_id = int(
            match["home_team_id"]
        )

        away_id = int(
            match["away_team_id"]
        )

        home_state = states[
            home_id
        ]

        away_state = states[
            away_id
        ]

        # ----------------------------------------------------
        # IMPORTANT:
        # Features are captured BEFORE the current match.
        # ----------------------------------------------------

        row = {
            "fixture_id":
                int(match["fixture_id"]),

            "season":
                int(match["season"]),

            "date":
                match["date"],

            "home_team_id":
                home_id,

            "home_team_name":
                match["home_team_name"],

            "away_team_id":
                away_id,

            "away_team_name":
                match["away_team_name"],
        }

        row.update(
            team_features(
                home_state,
                "home",
            )
        )

        row.update(
            team_features(
                away_state,
                "away",
            )
        )

        # ----------------------------------------------------
        # Difference features
        # ----------------------------------------------------

        difference_pairs = [
            (
                "points_per_match",
                "points_per_match",
            ),
            (
                "goals_for_per_match",
                "goals_for_per_match",
            ),
            (
                "goals_against_per_match",
                "goals_against_per_match",
            ),
            (
                "goal_difference",
                "goal_difference",
            ),
            (
                "last5_points",
                "last5_points",
            ),
            (
                "last10_points",
                "last10_points",
            ),
            (
                "last5_goals_for",
                "last5_goals_for",
            ),
            (
                "last10_goals_for",
                "last10_goals_for",
            ),
        ]

        for home_key, away_key in difference_pairs:

            row[
                f"diff_{home_key}"
            ] = (
                row[f"home_{home_key}"]
                -
                row[f"away_{away_key}"]
            )

        # ----------------------------------------------------
        # Cross-season prior
        #
        # The state is deliberately NOT reset between seasons.
        # This means previous-season information remains
        # available at the beginning of a new season.
        # ----------------------------------------------------

        row[
            "home_prior_matches"
        ] = home_state["matches"]

        row[
            "away_prior_matches"
        ] = away_state["matches"]

        row[
            "home_prior_points"
        ] = home_state["points"]

        row[
            "away_prior_points"
        ] = away_state["points"]

        # ----------------------------------------------------
        # Target
        # ----------------------------------------------------

        row[
            "home_goals"
        ] = int(
            match["home_goals"]
        )

        row[
            "away_goals"
        ] = int(
            match["away_goals"]
        )

        row[
            "target"
        ] = int(
            match["target"]
        )

        row[
            "target_label"
        ] = match[
            "target_label"
        ]

        output_rows.append(
            row
        )

        # ----------------------------------------------------
        # NOW update states using the current match.
        #
        # This guarantees no current-match leakage.
        # ----------------------------------------------------

        home_goals = int(
            match["home_goals"]
        )

        away_goals = int(
            match["away_goals"]
        )

        if home_goals > away_goals:

            home_result = "W"
            away_result = "L"

        elif home_goals < away_goals:

            home_result = "L"
            away_result = "W"

        else:

            home_result = "D"
            away_result = "D"

        update_team_state(
            home_state,
            home_result,
            home_goals,
            away_goals,
            "home",
        )

        update_team_state(
            away_state,
            away_result,
            away_goals,
            home_goals,
            "away",
        )

    result = pd.DataFrame(
        output_rows
    )

    return result


# ============================================================
# Metadata
# ============================================================

def feature_metadata():

    return {
        "stage": "7.4.2",
        "leakage_rule":
            "Only matches before the current fixture "
            "are used to calculate features.",
        "features": {
            "matches":
                "Number of previous matches.",
            "wins":
                "Previous wins.",
            "draws":
                "Previous draws.",
            "losses":
                "Previous losses.",
            "points":
                "Previous league points.",
            "points_per_match":
                "Previous points divided by previous matches.",
            "goals_for":
                "Previous goals scored.",
            "goals_against":
                "Previous goals conceded.",
            "goal_difference":
                "Previous goals scored minus conceded.",
            "home_*":
                "Historical home-performance statistics.",
            "away_*":
                "Historical away-performance statistics.",
            "last5_*":
                "Statistics from the previous five matches.",
            "last10_*":
                "Statistics from the previous ten matches.",
            "diff_*":
                "Home-team feature minus away-team feature.",
            "prior_*":
                "Historical cross-season information available "
                "before the fixture.",
        },
        "targets": {
            "0": "draw",
            "1": "home_win",
            "2": "away_win",
        },
    }
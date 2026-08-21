"""Leakage-safe historical-strength features for FixtureIQ.

The feature definitions in this module deliberately use only matches completed
before the target fixture. Cross-season carry-over is allowed only from the
immediately preceding EPL season; it never bridges a relegation/promotion gap.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd


HOME_POINTS = {"H": 3, "D": 1, "A": 0}
AWAY_POINTS = {"H": 0, "D": 1, "A": 3}

HISTORICAL_STRENGTH_COLUMNS = [
    "HomePreviousSeasonPPG",
    "AwayPreviousSeasonPPG",
    "HomePreviousSeasonDataAvailable",
    "AwayPreviousSeasonDataAvailable",
    "HomeCrossSeasonRecentPPG",
    "AwayCrossSeasonRecentPPG",
    "HomeCrossSeasonMatchesUsed",
    "AwayCrossSeasonMatchesUsed",
]


def _season_order(historical: pd.DataFrame) -> List[str]:
    """Return seasons ordered by their first match date."""
    return (
        historical.groupby("Season", sort=False)["Date"]
        .min()
        .sort_values()
        .index.astype(str)
        .tolist()
    )


def _team_match_history(historical: pd.DataFrame) -> pd.DataFrame:
    """Convert fixture rows into one chronological row per team appearance."""
    required = {"Date", "Season", "HomeTeam", "AwayTeam", "FTR"}
    missing = required.difference(historical.columns)
    if missing:
        raise ValueError(
            "Historical data is missing required columns: "
            + ", ".join(sorted(missing))
        )

    data = historical.copy()
    data["Date"] = pd.to_datetime(data["Date"], errors="raise")

    home = data[["Date", "Season", "HomeTeam", "FTR"]].copy()
    home = home.rename(columns={"HomeTeam": "Team"})
    home["Points"] = home["FTR"].map(HOME_POINTS)

    away = data[["Date", "Season", "AwayTeam", "FTR"]].copy()
    away = away.rename(columns={"AwayTeam": "Team"})
    away["Points"] = away["FTR"].map(AWAY_POINTS)

    team_matches = pd.concat(
        [
            home[["Date", "Season", "Team", "Points"]],
            away[["Date", "Season", "Team", "Points"]],
        ],
        ignore_index=True,
    )

    duplicates = team_matches.duplicated(["Date", "Season", "Team"], keep=False)
    if duplicates.any():
        sample = team_matches.loc[
            duplicates, ["Date", "Season", "Team"]
        ].head(10)
        raise ValueError(
            "A team appears more than once on the same EPL date; exact fixture "
            "ordering would be required. Sample:\n"
            + sample.to_string(index=False)
        )

    return team_matches.sort_values(["Date", "Team"]).reset_index(drop=True)


def build_team_historical_strength(historical: pd.DataFrame) -> pd.DataFrame:
    """Build historical-strength features at team-match level.

    Features
    --------
    PreviousSeasonPPG
        Final EPL points-per-game from the immediately previous EPL season.
        Missing for promoted/new teams that were not in the immediately
        previous EPL season.
    PreviousSeasonDataAvailable
        1 when PreviousSeasonPPG exists, otherwise 0.
    CrossSeasonRecentPPG
        PPG over up to five completed EPL matches before the fixture. At a
        season boundary, the previous season's final five matches are carried
        forward only if the club was also in the immediately previous EPL
        season. This prevents stale EPL form from bridging a relegation gap.
    CrossSeasonMatchesUsed
        Number of completed matches used by CrossSeasonRecentPPG (0..5).
    """
    data = historical.copy()
    data["Date"] = pd.to_datetime(data["Date"], errors="raise")
    seasons = _season_order(data)
    previous_season: Dict[str, Optional[str]] = {
        season: seasons[index - 1] if index > 0 else None
        for index, season in enumerate(seasons)
    }

    team_matches = _team_match_history(data)

    # Final PPG for every team-season. This is safe only when used by a later
    # season, which is enforced by the previous_season lookup below.
    season_summary = (
        team_matches.groupby(["Season", "Team"], as_index=False)
        .agg(SeasonPoints=("Points", "sum"), SeasonMatches=("Points", "size"))
    )
    season_summary["SeasonPPG"] = (
        season_summary["SeasonPoints"] / season_summary["SeasonMatches"]
    )
    ppg_lookup = {
        (row.Season, row.Team): float(row.SeasonPPG)
        for row in season_summary.itertuples(index=False)
    }

    rows = []
    previous_season_last_five: Dict[str, List[int]] = {}

    for season_index, season in enumerate(seasons):
        season_matches = team_matches.loc[
            team_matches["Season"] == season
        ].sort_values(["Date", "Team"])

        # Each team's list starts with the immediately previous EPL season's
        # final five matches only. Promoted teams start empty.
        current_history: Dict[str, List[int]] = {}

        for match in season_matches.itertuples(index=False):
            team = match.Team

            if team not in current_history:
                seed = (
                    list(previous_season_last_five.get(team, []))
                    if season_index > 0
                    else []
                )
                current_history[team] = seed

            prior_points = current_history[team]
            matches_used = min(5, len(prior_points))

            if matches_used:
                recent_points = float(sum(prior_points[-5:]))
                cross_season_ppg = recent_points / matches_used
            else:
                cross_season_ppg = np.nan

            prior_season = previous_season[season]
            previous_ppg = (
                ppg_lookup.get((prior_season, team), np.nan)
                if prior_season is not None
                else np.nan
            )

            rows.append(
                {
                    "Date": match.Date,
                    "Season": season,
                    "Team": team,
                    "PreviousSeasonPPG": previous_ppg,
                    "PreviousSeasonDataAvailable": int(
                        not pd.isna(previous_ppg)
                    ),
                    "CrossSeasonRecentPPG": cross_season_ppg,
                    "CrossSeasonMatchesUsed": int(matches_used),
                }
            )

            # The target match result enters history only AFTER its pre-match
            # feature row has been recorded.
            current_history[team].append(int(match.Points))
            current_history[team] = current_history[team][-5:]

        # Only teams present in this season are eligible to seed the next one.
        # This is what prevents carry-over across a season spent outside EPL.
        previous_season_last_five = {
            team: list(points[-5:])
            for team, points in current_history.items()
        }

    result = pd.DataFrame(rows)

    if not result["CrossSeasonMatchesUsed"].between(0, 5).all():
        raise AssertionError("CrossSeasonMatchesUsed must be between 0 and 5")

    non_missing_ppg = result["CrossSeasonRecentPPG"].dropna()
    if not non_missing_ppg.between(0, 3).all():
        raise AssertionError("CrossSeasonRecentPPG must be between 0 and 3")

    return result.sort_values(["Date", "Team"]).reset_index(drop=True)


def add_historical_strength_features(
    matches: pd.DataFrame,
    historical: pd.DataFrame,
) -> pd.DataFrame:
    """Merge leakage-safe historical-strength features onto fixture rows."""
    output = matches.copy()
    output["Date"] = pd.to_datetime(output["Date"], errors="raise")

    team_features = build_team_historical_strength(historical)

    home_features = team_features.rename(
        columns={
            "Team": "HomeTeam",
            "PreviousSeasonPPG": "HomePreviousSeasonPPG",
            "PreviousSeasonDataAvailable": "HomePreviousSeasonDataAvailable",
            "CrossSeasonRecentPPG": "HomeCrossSeasonRecentPPG",
            "CrossSeasonMatchesUsed": "HomeCrossSeasonMatchesUsed",
        }
    )[
        [
            "Date",
            "Season",
            "HomeTeam",
            "HomePreviousSeasonPPG",
            "HomePreviousSeasonDataAvailable",
            "HomeCrossSeasonRecentPPG",
            "HomeCrossSeasonMatchesUsed",
        ]
    ]

    away_features = team_features.rename(
        columns={
            "Team": "AwayTeam",
            "PreviousSeasonPPG": "AwayPreviousSeasonPPG",
            "PreviousSeasonDataAvailable": "AwayPreviousSeasonDataAvailable",
            "CrossSeasonRecentPPG": "AwayCrossSeasonRecentPPG",
            "CrossSeasonMatchesUsed": "AwayCrossSeasonMatchesUsed",
        }
    )[
        [
            "Date",
            "Season",
            "AwayTeam",
            "AwayPreviousSeasonPPG",
            "AwayPreviousSeasonDataAvailable",
            "AwayCrossSeasonRecentPPG",
            "AwayCrossSeasonMatchesUsed",
        ]
    ]

    before_rows = len(output)

    output = output.merge(
        home_features,
        on=["Date", "Season", "HomeTeam"],
        how="left",
        validate="one_to_one",
    )
    output = output.merge(
        away_features,
        on=["Date", "Season", "AwayTeam"],
        how="left",
        validate="one_to_one",
    )

    if len(output) != before_rows:
        raise AssertionError("Historical-strength merge changed fixture row count")

    return output

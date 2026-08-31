"""
FixtureIQ Stage 7.3.4
Historical Dataset Reconciliation.

Compares source API responses with the processed
historical dataset for selected seasons.

Checks:
- Record counts
- Fixture IDs
- Teams
- Scores
- Seasons
- Missing records
- Unexpected records
"""

import argparse
import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BASE_DIR),
)


from backend.config import (
    API_FOOTBALL_LEAGUE_ID,
    validate_config,
)

from backend.providers.api_football import (
    APIFootballProvider,
)

from backend.providers.historical import (
    HISTORICAL_FILE,
    load_historical_fixtures,
)


REPORT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "historical_reconciliation_report.json"
)


def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "FixtureIQ historical dataset reconciliation"
        )
    )

    parser.add_argument(
        "--seasons",
        nargs="+",
        type=int,
        required=True,
        help=(
            "Seasons to reconcile. "
            "Example: --seasons 2023 2024"
        ),
    )

    return parser.parse_args()


def build_api_fixture_map(
    response,
):
    """
    Build fixture ID -> source record mapping.
    """

    result = {}

    for item in response:

        fixture = item.get(
            "fixture",
            {},
        )

        fixture_id = fixture.get(
            "id"
        )

        if fixture_id is not None:

            result[int(fixture_id)] = item

    return result


def main():

    args = parse_args()

    seasons = sorted(
        set(args.seasons)
    )

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.3.4"
    )

    print(
        "Historical Dataset Reconciliation"
    )

    print("=" * 50)

    validate_config()

    dataset = load_historical_fixtures(
        HISTORICAL_FILE
    )

    if dataset.empty:

        print(
            "\nHistorical dataset is empty."
        )

        sys.exit(1)

    provider = APIFootballProvider()

    season_reports = []

    overall_pass = True

    # ========================================================
    # Season loop
    # ========================================================

    for season in seasons:

        print(
            "\n" + "-" * 50
        )

        print(
            f"SEASON {season}"
        )

        print(
            "-" * 50
        )

        # ----------------------------------------------------
        # Fetch source
        # ----------------------------------------------------

        payload = provider.get_fixtures(
            API_FOOTBALL_LEAGUE_ID,
            season,
        )

        response = payload.get(
            "response",
            [],
        )

        errors = payload.get(
            "errors",
            {},
        )

        if (
            isinstance(
                errors,
                dict,
            )
            and
            errors.get("plan")
        ):

            print(
                "Provider limitation:"
            )

            print(
                json.dumps(
                    errors,
                    indent=2,
                )
            )

            overall_pass = False

            season_reports.append(
                {
                    "season": season,
                    "status":
                        "LIMITED_BY_PLAN",
                }
            )

            continue

        source_map = (
            build_api_fixture_map(
                response
            )
        )

        # ----------------------------------------------------
        # Processed subset
        # ----------------------------------------------------

        processed_subset = (
            dataset[
                dataset["season"]
                == season
            ]
        )

        processed_map = {
            int(row.fixture_id):
                row
            for row in
            processed_subset.itertuples(
                index=False
            )
        }

        source_ids = set(
            source_map.keys()
        )

        processed_ids = set(
            processed_map.keys()
        )

        missing_ids = sorted(
            source_ids
            -
            processed_ids
        )

        unexpected_ids = sorted(
            processed_ids
            -
            source_ids
        )

        # ----------------------------------------------------
        # Field comparison
        # ----------------------------------------------------

        team_mismatches = []
        score_mismatches = []
        season_mismatches = []

        common_ids = (
            source_ids
            &
            processed_ids
        )

        for fixture_id in common_ids:

            source = source_map[
                fixture_id
            ]

            processed = processed_map[
                fixture_id
            ]

            source_fixture = (
                source.get(
                    "fixture",
                    {},
                )
            )

            source_teams = (
                source.get(
                    "teams",
                    {},
                )
            )

            source_goals = (
                source.get(
                    "goals",
                    {},
                )
            )

            source_home = (
                source_teams
                .get(
                    "home",
                    {},
                )
            )

            source_away = (
                source_teams
                .get(
                    "away",
                    {},
                )
            )

            # Teams

            if (
                source_home.get("id")
                !=
                processed.home_team_id
                or
                source_away.get("id")
                !=
                processed.away_team_id
            ):

                team_mismatches.append(
                    fixture_id
                )

            # Scores

            source_home_goals = (
                source_goals.get(
                    "home"
                )
            )

            source_away_goals = (
                source_goals.get(
                    "away"
                )
            )

            if (
                source_home_goals
                !=
                processed.home_goals
                or
                source_away_goals
                !=
                processed.away_goals
            ):

                score_mismatches.append(
                    fixture_id
                )

            # Season

            if (
                int(processed.season)
                !=
                season
            ):

                season_mismatches.append(
                    fixture_id
                )

        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------

        season_pass = (
            len(source_ids)
            ==
            len(processed_ids)
            and
            not missing_ids
            and
            not unexpected_ids
            and
            not team_mismatches
            and
            not score_mismatches
            and
            not season_mismatches
        )

        if not season_pass:

            overall_pass = False

        print(
            f"Source records: "
            f"{len(source_ids)}"
        )

        print(
            f"Processed records: "
            f"{len(processed_ids)}"
        )

        print(
            f"Missing records: "
            f"{len(missing_ids)}"
        )

        print(
            f"Unexpected records: "
            f"{len(unexpected_ids)}"
        )

        print(
            f"Team mismatches: "
            f"{len(team_mismatches)}"
        )

        print(
            f"Score mismatches: "
            f"{len(score_mismatches)}"
        )

        print(
            f"Season mismatches: "
            f"{len(season_mismatches)}"
        )

        print(
            f"Reconciliation: "
            f"{'PASS' if season_pass else 'FAIL'}"
        )

        season_reports.append(
            {
                "season": season,
                "source_records":
                    len(source_ids),
                "processed_records":
                    len(processed_ids),
                "missing_records":
                    len(missing_ids),
                "unexpected_records":
                    len(unexpected_ids),
                "team_mismatches":
                    len(team_mismatches),
                "score_mismatches":
                    len(score_mismatches),
                "season_mismatches":
                    len(season_mismatches),
                "missing_fixture_ids":
                    missing_ids,
                "unexpected_fixture_ids":
                    unexpected_ids,
                "overall_pass":
                    season_pass,
            }
        )

    # ========================================================
    # Overall dataset check
    # ========================================================

    dataset_ids_unique = (
        dataset["fixture_id"]
        .is_unique
    )

    dataset_seasons = sorted(
        set(
            dataset["season"]
            .astype(int)
            .tolist()
        )
    )

    requested_seasons_present = all(
        season in dataset_seasons
        for season in seasons
    )

    overall_pass = (
        overall_pass
        and
        dataset_ids_unique
        and
        requested_seasons_present
    )

    report = {
        "stage": "7.3.4",
        "requested_seasons":
            seasons,
        "dataset":
            str(HISTORICAL_FILE),
        "dataset_records":
            len(dataset),
        "dataset_seasons":
            dataset_seasons,
        "dataset_fixture_ids_unique":
            bool(dataset_ids_unique),
        "requested_seasons_present":
            bool(requested_seasons_present),
        "season_reports":
            season_reports,
        "overall_pass":
            bool(overall_pass),
    }

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with REPORT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # ========================================================
    # Final
    # ========================================================

    print(
        "\n" + "=" * 50
    )

    print(
        "RECONCILIATION SUMMARY"
    )

    print(
        "=" * 50
    )

    print(
        f"Dataset records: "
        f"{len(dataset)}"
    )

    print(
        f"Dataset seasons: "
        f"{dataset_seasons}"
    )

    print(
        f"Global fixture IDs unique: "
        f"{'PASS' if dataset_ids_unique else 'FAIL'}"
    )

    print(
        f"Requested seasons present: "
        f"{'PASS' if requested_seasons_present else 'FAIL'}"
    )

    print(
        f"\nReport saved:"
    )

    print(
        REPORT_FILE
    )

    print(
        "\nSTAGE 7.3.4: "
        f"{'PASS' if overall_pass else 'FAIL'}"
    )

    if not overall_pass:

        sys.exit(1)


if __name__ == "__main__":
    main()
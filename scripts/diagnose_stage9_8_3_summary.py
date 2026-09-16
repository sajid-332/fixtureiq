import csv
import math
import re
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FILE = (
    ROOT
    / "data"
    / "processed"
    / "intelligence"
    / "match_intelligence.csv"
)


def load_rows():

    with FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        return list(
            csv.DictReader(file)
        )


def d(row, field):

    return Decimal(
        str(
            row[field]
        ).strip()
    )


def normalized_word(value):

    return (
        str(value)
        .strip()
        .upper()
        .replace("-", "_")
        .replace(" ", "_")
    )


def displayed_number_matches(
    text_number,
    expected,
):

    observed = float(
        text_number
    )

    if "." in text_number:

        decimals = len(
            text_number.split(".", 1)[1]
        )

    else:

        decimals = 0

    tolerance = (
        10 ** (-decimals)
    ) / 2 + 1e-10

    return (
        abs(
            observed - expected
        )
        <= tolerance
    )


def expected_alignment(
    label,
    score,
):

    if label == "Home Win":

        if score >= 2:
            return "SUPPORTIVE"

        if score <= -2:
            return "CONTRADICTORY"

        if score == 0:
            return "NEUTRAL"

        return "MIXED"

    if label == "Away Win":

        if score <= -2:
            return "SUPPORTIVE"

        if score >= 2:
            return "CONTRADICTORY"

        if score == 0:
            return "NEUTRAL"

        return "MIXED"

    if label == "Draw":

        if abs(score) <= 1:
            return "SUPPORTIVE"

        if abs(score) == 2:
            return "MIXED"

        return "CONTRADICTORY"

    raise RuntimeError(
        f"Unknown label: {label}"
    )


def main():

    rows = load_rows()

    for row in rows:

        fixture_id = row[
            "fixture_id"
        ]

        home_team = row[
            "home_team_name"
        ].strip()

        away_team = row[
            "away_team_name"
        ].strip()

        label = row[
            "stage7_predicted_label"
        ].strip()

        alignment = row[
            "stage9_context_alignment"
        ].strip()

        confidence_band = row[
            "stage9_confidence_band"
        ].strip()

        uncertainty_band = row[
            "stage9_uncertainty_band"
        ].strip()

        support_score = int(
            Decimal(
                row[
                    "stage9_context_support_score"
                ]
            )
        )

        summary = row[
            "stage9_explanation_summary"
        ].strip()

        probabilities = [
            d(
                row,
                "stage7_prob_home_win",
            ),
            d(
                row,
                "stage7_prob_draw",
            ),
            d(
                row,
                "stage7_prob_away_win",
            ),
        ]

        sorted_probs = sorted(
            probabilities,
            reverse=True,
        )

        top = sorted_probs[0]
        second = sorted_probs[1]

        margin = (
            top - second
        )

        checks = {}

        # ----------------------------------------
        # Subject
        # ----------------------------------------

        subject_match = re.search(
            (
                r"Stage 7 gives\s+(.+?)\s+"
                r"the highest probability at"
            ),
            summary,
            flags=re.IGNORECASE,
        )

        if label == "Home Win":

            expected_subjects = {
                home_team.casefold()
            }

        elif label == "Away Win":

            expected_subjects = {
                away_team.casefold()
            }

        else:

            expected_subjects = {
                "draw",
                "the draw",
            }

        observed_subject = (
            subject_match.group(1).strip()
            if subject_match
            else None
        )

        checks[
            "subject"
        ] = (
            subject_match is not None
            and
            observed_subject.casefold()
            in expected_subjects
        )

        # ----------------------------------------
        # Top probability
        # ----------------------------------------

        top_match = re.search(
            (
                r"highest probability at\s+"
                r"([0-9]+(?:\.[0-9]+)?)%"
            ),
            summary,
            flags=re.IGNORECASE,
        )

        checks[
            "top_probability"
        ] = (
            top_match is not None
            and
            displayed_number_matches(
                top_match.group(1),
                float(top) * 100,
            )
        )

        # ----------------------------------------
        # Margin
        # ----------------------------------------

        margin_match = re.search(
            (
                r"([0-9]+(?:\.[0-9]+)?)"
                r"\s+percentage points above "
                r"the next outcome"
            ),
            summary,
            flags=re.IGNORECASE,
        )

        checks[
            "margin"
        ] = (
            margin_match is not None
            and
            displayed_number_matches(
                margin_match.group(1),
                float(margin) * 100,
            )
        )

        # ----------------------------------------
        # Score
        # ----------------------------------------

        score_match = re.search(
            (
                r"fixed context score is\s+"
                r"([+-]?\d+)"
            ),
            summary,
            flags=re.IGNORECASE,
        )

        checks[
            "support_score"
        ] = (
            score_match is not None
            and
            int(
                score_match.group(1)
            )
            ==
            support_score
        )

        # ----------------------------------------
        # Signal counts + team names
        # ----------------------------------------

        signal_match = re.search(
            (
                r"(\d+)\s+signals favor\s+(.+?),\s+"
                r"(\d+)\s+favor\s+(.+?),\s+and\s+"
                r"(\d+)\s+are neutral or unavailable"
            ),
            summary,
            flags=re.IGNORECASE,
        )

        checks[
            "signal_pattern"
        ] = (
            signal_match is not None
        )

        if signal_match:

            observed_first_count = int(
                signal_match.group(1)
            )

            observed_first_team = (
                signal_match.group(2)
                .strip()
            )

            observed_second_count = int(
                signal_match.group(3)
            )

            observed_second_team = (
                signal_match.group(4)
                .strip()
            )

            observed_neutral = int(
                signal_match.group(5)
            )

            checks[
                "first_team_is_home"
            ] = (
                observed_first_team.casefold()
                ==
                home_team.casefold()
            )

            checks[
                "second_team_is_away"
            ] = (
                observed_second_team.casefold()
                ==
                away_team.casefold()
            )

            checks[
                "signal_total_is_5"
            ] = (
                observed_first_count
                +
                observed_second_count
                +
                observed_neutral
                ==
                5
            )

            checks[
                "signal_score_matches"
            ] = (
                observed_first_count
                -
                observed_second_count
                ==
                support_score
            )

        # ----------------------------------------
        # Alignment / confidence / uncertainty
        # ----------------------------------------

        state_match = re.search(
            (
                r"Context alignment is\s+([^;]+);\s+"
                r"confidence is\s+([^ ]+)\s+and\s+"
                r"uncertainty is\s+([^\.]+)"
            ),
            summary,
            flags=re.IGNORECASE,
        )

        checks[
            "state_pattern"
        ] = (
            state_match is not None
        )

        if state_match:

            observed_alignment = (
                normalized_word(
                    state_match.group(1)
                )
            )

            observed_confidence = (
                normalized_word(
                    state_match.group(2)
                )
            )

            observed_uncertainty = (
                normalized_word(
                    state_match.group(3)
                )
            )

            checks[
                "alignment"
            ] = (
                observed_alignment
                ==
                normalized_word(
                    alignment
                )
            )

            checks[
                "confidence_band"
            ] = (
                observed_confidence
                ==
                normalized_word(
                    confidence_band
                )
            )

            checks[
                "uncertainty_band"
            ] = (
                observed_uncertainty
                ==
                normalized_word(
                    uncertainty_band
                )
            )

        # ----------------------------------------
        # Disclaimer
        # ----------------------------------------

        disclaimer = (
            "This interprets the existing prediction "
            "and does not alter or replace it."
        )

        checks[
            "disclaimer"
        ] = (
            disclaimer.casefold()
            in
            summary.casefold()
        )

        # ----------------------------------------
        # Overall
        # ----------------------------------------

        failed = [
            key
            for key, value
            in checks.items()
            if not value
        ]

        if failed:

            print("=" * 72)

            print(
                "FIRST FAILING FIXTURE"
            )

            print("=" * 72)

            print(
                "fixture_id:",
                fixture_id,
            )

            print(
                "home_team:",
                home_team,
            )

            print(
                "away_team:",
                away_team,
            )

            print(
                "predicted_label:",
                label,
            )

            print(
                "support_score:",
                support_score,
            )

            print(
                "alignment:",
                alignment,
            )

            print(
                "confidence_band:",
                confidence_band,
            )

            print(
                "uncertainty_band:",
                uncertainty_band,
            )

            print()

            print(
                "SUMMARY:"
            )

            print(summary)

            print()

            print(
                "FAILED CHECKS:"
            )

            for key in failed:

                print(
                    " -",
                    key,
                )

            print()

            print(
                "ALL CHECKS:"
            )

            for key, value in checks.items():

                print(
                    f" {key}: "
                    f"{'PASS' if value else 'FAIL'}"
                )

            print("=" * 72)

            return

    print("=" * 72)

    print(
        "ALL EXPLANATION SUMMARIES: PASS"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
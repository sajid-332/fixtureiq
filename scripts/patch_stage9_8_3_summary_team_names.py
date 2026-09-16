from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TARGET = (
    ROOT
    / "scripts"
    / "verify_stage9_8_3_intelligence_integrity.py"
)


OLD = '''            signals_match = re.search(
                (
                    r"(\\d+)\\s+signals favor home,\\s+"
                    r"(\\d+)\\s+favor away,\\s+and\\s+"
                    r"(\\d+)\\s+are neutral or unavailable"
                ),
                summary,
                flags=re.IGNORECASE,
            )

            if not signals_match:

                summary_ok = False

            else:

                observed_counts = (
                    int(
                        signals_match.group(1)
                    ),
                    int(
                        signals_match.group(2)
                    ),
                    int(
                        signals_match.group(3)
                    ),
                )

                expected_counts = (
                    home_signal_count,
                    away_signal_count,
                    neutral_signal_count,
                )

                if (
                    observed_counts
                    !=
                    expected_counts
                ):

                    summary_ok = False
'''


NEW = '''            # Stage 9.5 explanation summaries use the
            # canonical team names rather than the literal
            # words "home" and "away".
            #
            # Example:
            #   2 signals favor Brentford,
            #   3 favor Chelsea,
            #   and 0 are neutral or unavailable.

            signals_match = re.search(
                (
                    r"(\\d+)\\s+signals favor\\s+(.+?),\\s+"
                    r"(\\d+)\\s+favor\\s+(.+?),\\s+and\\s+"
                    r"(\\d+)\\s+are neutral or unavailable"
                ),
                summary,
                flags=re.IGNORECASE,
            )

            if not signals_match:

                summary_ok = False

            else:

                observed_home_count = int(
                    signals_match.group(1)
                )

                observed_home_team = (
                    signals_match
                    .group(2)
                    .strip()
                )

                observed_away_count = int(
                    signals_match.group(3)
                )

                observed_away_team = (
                    signals_match
                    .group(4)
                    .strip()
                )

                observed_neutral_count = int(
                    signals_match.group(5)
                )

                if (
                    observed_home_count
                    !=
                    home_signal_count
                ):

                    summary_ok = False

                if (
                    observed_away_count
                    !=
                    away_signal_count
                ):

                    summary_ok = False

                if (
                    observed_neutral_count
                    !=
                    neutral_signal_count
                ):

                    summary_ok = False

                if (
                    observed_home_team.casefold()
                    !=
                    home_team.casefold()
                ):

                    summary_ok = False

                if (
                    observed_away_team.casefold()
                    !=
                    away_team.casefold()
                ):

                    summary_ok = False
'''


def main():

    text = TARGET.read_text(
        encoding="utf-8"
    )

    if NEW in text:

        print(
            "Stage 9.8.3 summary-team patch "
            "already applied."
        )

        return

    if OLD not in text:

        raise RuntimeError(
            "Expected verifier block was not found. "
            "No file was changed."
        )

    updated = text.replace(
        OLD,
        NEW,
        1,
    )

    temporary = TARGET.with_suffix(
        ".py.tmp"
    )

    temporary.write_text(
        updated,
        encoding="utf-8",
    )

    temporary.replace(
        TARGET
    )

    print(
        "Stage 9.8.3 summary-team patch: PASS"
    )


if __name__ == "__main__":

    main()
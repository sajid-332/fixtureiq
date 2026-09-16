from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TARGET = (
    ROOT
    / "scripts"
    / "verify_stage9_8_3_intelligence_integrity.py"
)


OLD = '''            else:
                expected_subjects = {
                    "draw",
                    "the draw",
                }
'''


NEW = '''            else:
                # Stage 9.5's deterministic Draw explanation
                # uses "a draw" as the natural-language subject.
                # Accept the locked semantic equivalents while
                # still rejecting unrelated wording.
                expected_subjects = {
                    "draw",
                    "a draw",
                    "the draw",
                }
'''


def main():

    text = TARGET.read_text(
        encoding="utf-8"
    )

    if NEW in text:

        print(
            "Stage 9.8.3 draw-subject patch "
            "already applied."
        )

        return

    if OLD not in text:

        raise RuntimeError(
            "Expected Draw subject block not found. "
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
        "Stage 9.8.3 draw-subject patch: PASS"
    )


if __name__ == "__main__":

    main()
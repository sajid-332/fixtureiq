from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TARGET = (
    ROOT
    / "scripts"
    / "verify_stage10_2_1_10_2_2.py"
)


OLD = '''        re.search(
            (
                r"(?m)^"
                r"FIXTUREIQ_API_BASE_URL="
                r"http://127\\\\.0\\\\.0\\\\.1:5000"
                r"\\\\s*$"
            ),
            env_example,
        )
'''


NEW = '''        re.search(
            (
                r"(?m)^"
                r"FIXTUREIQ_API_BASE_URL="
                r"http://127\\.0\\.0\\.1:5000"
                r"\\s*$"
            ),
            env_example,
        )
'''


def main() -> None:

    text = TARGET.read_text(
        encoding="utf-8"
    )

    if NEW in text:

        print(
            "Stage 10.2.2 env regex patch "
            "already applied."
        )

        return

    if OLD not in text:

        raise RuntimeError(
            "Expected verifier regex block "
            "not found. No file was changed."
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
        "Stage 10.2.2 env regex patch: PASS"
    )


if __name__ == "__main__":

    main()
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TARGET = (
    ROOT
    / "scripts"
    / "build_stage10_2_5_10_2_6.py"
)


OLD = '''    for parameter in params:

        lines.append(
            (
                f"  {parameter}: "
                "string | number,"
            )
        )
'''


NEW = '''    for parameter in params:

        parameter_type = (
            "string"
            if parameter
            ==
            "teamName"
            else
            "string | number"
        )

        lines.append(
            (
                f"  {parameter}: "
                f"{parameter_type},"
            )
        )
'''


def main() -> None:

    text = TARGET.read_text(
        encoding="utf-8"
    )

    if NEW in text:

        print(
            "Stage 10.2.6 parameter-type patch "
            "already applied."
        )

        return

    if OLD not in text:

        raise RuntimeError(
            "Expected render_wrapper block not found. "
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
        "Stage 10.2.6 parameter-type patch: PASS"
    )


if __name__ == "__main__":

    main()
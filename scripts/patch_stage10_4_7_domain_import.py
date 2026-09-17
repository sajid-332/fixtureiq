from pathlib import Path


PATH = Path(
    "scripts/build_stage10_4_7_10_4_8.py"
)


OLD = r'''    pattern = re.compile(
        (
            r'import\s+type\s*\{'
            r'[\s\S]*?'
            r'\}\s*from\s*'
            r'["\']\.\./\.\./lib/domain/types["\'];'
        )
    )
'''


NEW = r'''    pattern = re.compile(
        (
            r'import\s+type\s*\{'
            r'[^}]*'
            r'\}\s*from\s*'
            r'["\']\.\./\.\./lib/domain/types["\'];'
        )
    )
'''


def main() -> None:

    if not PATH.exists():
        raise RuntimeError(
            f"Missing builder: {PATH}"
        )

    source = PATH.read_text(
        encoding="utf-8"
    )


    if NEW in source:

        print(
            "Builder domain-import matcher "
            "already patched."
        )

        return


    if OLD not in source:

        raise RuntimeError(
            (
                "Expected old domain-import "
                "matcher was not found."
            )
        )


    updated = source.replace(
        OLD,
        NEW,
        1,
    )


    PATH.write_text(
        updated,
        encoding="utf-8",
    )


    print(
        "PATCH COMPLETE"
    )

    print(
        "Domain import matcher can no longer "
        "consume the ReactNode import."
    )


if __name__ == "__main__":
    main()
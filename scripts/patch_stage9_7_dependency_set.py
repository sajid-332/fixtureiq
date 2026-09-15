from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TARGET = (
    ROOT
    / "backend"
    / "services"
    / "match_intelligence_service.py"
)


OLD = '''        if (
            set(
                dependency_identity
            )
            !=
            set(
                allowed_inputs
            )
        ):

            raise MatchIntelligenceNotReadyError(
                (
                    "Stage 9.2 dynamic dependency set "
                    "no longer matches Stage 9.1."
                )
            )

        resolved = {}
'''


NEW = '''        # Stage 9.2 records the 11 dynamic Stage 7/8
        # inputs declared by Stage 9.1, plus its two immutable
        # Stage 9.1 foundation artifacts.
        #
        # The dynamic source set must remain exact. The two
        # Stage 9.1 artifacts are legitimate internal
        # dependencies, not additional production inputs.

        expected_dependency_names = (
            set(
                allowed_inputs
            )
            |
            {
                "stage9_intelligence_contract",
                "stage9_intelligence_contract_verification",
            }
        )

        if (
            set(
                dependency_identity
            )
            !=
            expected_dependency_names
        ):

            raise MatchIntelligenceNotReadyError(
                (
                    "Stage 9.2 dependency set no longer "
                    "matches the locked Stage 9 foundation."
                )
            )

        resolved = {}
'''


def main():

    text = TARGET.read_text(
        encoding="utf-8"
    )

    if NEW in text:

        print(
            "Stage 9.7 dependency-set patch "
            "already applied."
        )

        return

    if OLD not in text:

        raise RuntimeError(
            "Expected Stage 9.7 patch target not found. "
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
        "Stage 9.7 dependency-set patch: PASS"
    )


if __name__ == "__main__":

    main()
from pathlib import Path


PATH = Path(
    "scripts/build_stage10_4_7_10_4_8.py"
)


REPLACEMENT = r'''def discover_band_types(
    source: str,
) -> tuple[str, str]:

    exported_type_names = list(
        dict.fromkeys(
            re.findall(
                (
                    r"\bexport\s+type\s+"
                    r"([A-Za-z_$][A-Za-z0-9_$]*)"
                    r"\b"
                ),
                source,
            )
        )
    )


    if not exported_type_names:

        raise RuntimeError(
            (
                "No exported TypeScript type "
                "aliases were found in the "
                "locked domain model."
            )
        )


    def find_named_type(
        *terms: str,
    ) -> str | None:

        matches = [
            name
            for name in exported_type_names
            if all(
                term.lower()
                in
                name.lower()

                for term in terms
            )
        ]


        if len(matches) == 1:

            return matches[0]


        return None


    # --------------------------------------------------------
    # Prefer explicit semantic names.
    # --------------------------------------------------------

    confidence_type = (
        "ConfidenceBand"
        if
        "ConfidenceBand"
        in
        exported_type_names
        else
        find_named_type(
            "confidence",
            "band",
        )
    )


    uncertainty_type = (
        "UncertaintyBand"
        if
        "UncertaintyBand"
        in
        exported_type_names
        else
        find_named_type(
            "uncertainty",
            "band",
        )
    )


    if (
        confidence_type
        and
        uncertainty_type
    ):

        return (
            confidence_type,
            uncertainty_type,
        )


    # --------------------------------------------------------
    # A shared domain band type is also valid.
    # Example:
    #
    # export type IntelligenceBand =
    #   | "VERY_LOW"
    #   | "LOW"
    #   ...
    #
    # or:
    #
    # export type IntelligenceBand =
    #   typeof INTELLIGENCE_BANDS[number]
    # --------------------------------------------------------

    band_named_types = [
        name
        for name in exported_type_names
        if "band" in name.lower()
    ]


    if len(
        band_named_types
    ) == 1:

        shared_type = (
            band_named_types[0]
        )


        return (
            confidence_type
            or
            shared_type,

            uncertainty_type
            or
            shared_type,
        )


    # --------------------------------------------------------
    # Inspect complete type declaration regions without
    # requiring semicolons.
    # --------------------------------------------------------

    type_starts = list(
        re.finditer(
            (
                r"\bexport\s+type\s+"
                r"([A-Za-z_$][A-Za-z0-9_$]*)"
                r"\s*="
            ),
            source,
        )
    )


    literal_candidates: list[str] = []


    for index, match in enumerate(
        type_starts
    ):

        name = match.group(1)

        body_start = match.end()

        body_end = (
            type_starts[
                index + 1
            ].start()
            if
            index + 1
            <
            len(
                type_starts
            )
            else
            len(
                source
            )
        )


        body = source[
            body_start:
            body_end
        ]


        values = set(
            re.findall(
                (
                    r'["\']'
                    r"(VERY_LOW|LOW|MODERATE|HIGH|VERY_HIGH)"
                    r'["\']'
                ),
                body,
            )
        )


        if BAND_VALUES.issubset(
            values
        ):

            literal_candidates.append(
                name
            )


    band_literal_candidates = [
        name
        for name in literal_candidates
        if "band" in name.lower()
    ]


    candidate_pool = (
        band_literal_candidates
        or
        literal_candidates
    )


    if (
        not confidence_type
        and
        len(
            candidate_pool
        )
        ==
        1
    ):

        confidence_type = (
            candidate_pool[0]
        )


    if (
        not uncertainty_type
        and
        len(
            candidate_pool
        )
        ==
        1
    ):

        uncertainty_type = (
            candidate_pool[0]
        )


    if (
        confidence_type
        and
        uncertainty_type
    ):

        return (
            confidence_type,
            uncertainty_type,
        )


    raise RuntimeError(
        (
            "Could not uniquely discover the "
            "locked confidence/uncertainty "
            "band TypeScript type. "
            "Exported types: "
            f"{exported_type_names}. "
            "Literal band candidates: "
            f"{candidate_pool}."
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


    start = source.find(
        "def discover_band_types("
    )

    end = source.find(
        "\ndef build_domain_import(",
        start,
    )


    if start < 0 or end < 0:

        raise RuntimeError(
            (
                "Could not safely locate "
                "discover_band_types()."
            )
        )


    updated = (
        source[:start]
        +
        REPLACEMENT.rstrip()
        +
        "\n\n"
        +
        source[
            end + 1:
        ]
    )


    PATH.write_text(
        updated,
        encoding="utf-8",
    )


    print(
        "PATCH COMPLETE"
    )

    print(
        "Updated:"
    )

    print(
        f"  {PATH}"
    )


if __name__ == "__main__":

    main()
from pathlib import Path


BUILDER = Path(
    "scripts/build_stage10_4_11_10_4_12.py"
)

VERIFIER = Path(
    "scripts/verify_stage10_4_12.py"
)


NUMERIC_NORMALIZER = r'''
const NUMERIC_TRANSPORT_FIELDS =
  new Set<string>(
    [
      "stage7_prob_home_win",
      "stage7_prob_draw",
      "stage7_prob_away_win",
      "stage7_confidence",
      "stage9_top_probability",
      "stage9_probability_margin",
      "stage9_context_support_score",
    ],
  );


function normalizeTransportRecord(
  value: JsonObject,
): JsonObject {

  const normalized: {
    [key: string]:
      JsonValue;
  } = {
    ...value,
  };


  for (
    const field
    of
    NUMERIC_TRANSPORT_FIELDS
  ) {

    const current =
      normalized[
        field
      ];


    if (
      typeof current === "string"
      &&
      current.trim().length > 0
    ) {

      const parsed =
        Number(
          current,
        );


      if (
        Number.isFinite(
          parsed,
        )
      ) {

        normalized[
          field
        ] = parsed;
      }
    }
  }


  return normalized;
}


'''


def replace_once(
    source: str,
    old: str,
    new: str,
    label: str,
) -> str:

    count = source.count(
        old
    )

    if count != 1:

        raise RuntimeError(
            (
                f"{label}: expected exactly "
                f"one occurrence, found {count}."
            )
        )

    return source.replace(
        old,
        new,
        1,
    )


def patch_builder() -> None:

    if not BUILDER.exists():

        raise RuntimeError(
            f"Missing builder: {BUILDER}"
        )


    source = BUILDER.read_text(
        encoding="utf-8"
    )


    # --------------------------------------------------------
    # 1. Lock kickoff to the proven Stage 9 API field `date`
    # when the older 10.2.6 validator does not expose a
    # kickoff/date property.
    # --------------------------------------------------------

    old_raise = '''    raise RuntimeError(
        (
            "Could not uniquely discover the "
            "kickoff source field from the "
            "validated intelligence record. "
            f"Validated fields: {fields}"
        )
    )
'''


    new_raise = '''    # Stage 9 `/api/v1/intelligence/upcoming`
    # is the authoritative intelligence API.
    #
    # Its verified runtime payload exposes the fixture kickoff
    # as `date`. Stage 10.2.6 predates kickoff presentation and
    # therefore does not validate that field explicitly.
    #
    # Keep the fallback exact and fail closed for any unrelated
    # validator shape.
    if (
        "fixture_id"
        in
        fields
        and
        "home_team_name"
        in
        fields
        and
        "away_team_name"
        in
        fields
        and
        "stage7_prob_home_win"
        in
        fields
        and
        "stage9_context_alignment"
        in
        fields
    ):
        return (
            "date",
            fields,
        )

    raise RuntimeError(
        (
            "Could not lock the Stage 9 "
            "kickoff source field. "
            f"Validated fields: {fields}"
        )
    )
'''


    if new_raise not in source:

        source = replace_once(
            source,
            old_raise,
            new_raise,
            "kickoff discovery fallback",
        )


    # --------------------------------------------------------
    # 2. Add transport-only number normalization.
    #
    # Stage 9 API JSON currently emits numeric values as JSON
    # strings. MatchCard formatters correctly accept numbers.
    #
    # This conversion changes representation only:
    #   "0.4678" -> 0.4678
    #
    # It does NOT normalize probabilities, calculate confidence,
    # derive predictions, or modify Stage 7 / Stage 9 authority.
    # --------------------------------------------------------

    parse_marker = (
        "function parseMatch(\n"
        "  value: JsonObject,\n"
        "): UpcomingDashboardMatch {\n"
    )


    if (
        "const NUMERIC_TRANSPORT_FIELDS"
        not in
        source
    ):

        source = replace_once(
            source,
            parse_marker,
            (
                NUMERIC_NORMALIZER
                +
                parse_marker
            ),
            "numeric transport normalizer",
        )


    old_parse_call = '''    const match =
      parseMatch(
        value,
      );
'''


    new_parse_call = '''    const match =
      parseMatch(
        normalizeTransportRecord(
          value,
        ),
      );
'''


    if new_parse_call not in source:

        source = replace_once(
            source,
            old_parse_call,
            new_parse_call,
            "normalized match parse",
        )


    # --------------------------------------------------------
    # 3. Correct contract provenance wording.
    # --------------------------------------------------------

    old_discovered = '''            "discovered_from":
                relative(
                    VALIDATION_FILE
                ),
'''


    new_discovered = '''            "discovered_from":
                "STAGE_9_INTELLIGENCE_API_PAYLOAD",

            "validator_note":
                (
                    "Stage 10.2.6 validates the "
                    "intelligence record but does not "
                    "type the kickoff date field."
                ),

            "transport_numeric_string_coercion":
                True,
'''


    if new_discovered not in source:

        source = replace_once(
            source,
            old_discovered,
            new_discovered,
            "kickoff contract provenance",
        )


    BUILDER.write_text(
        source,
        encoding="utf-8",
    )


    print(
        "Builder patched:"
    )

    print(
        f"  {BUILDER}"
    )


def patch_verifier() -> None:

    if not VERIFIER.exists():

        raise RuntimeError(
            f"Missing verifier: {VERIFIER}"
        )


    source = VERIFIER.read_text(
        encoding="utf-8"
    )


    anchor = '''    check(
        "Duplicate fixture protection",
        (
            "seen.has"
            in
            extractor_source
            and
            "seen.add"
            in
            extractor_source
        ),
        failures,
    )


'''


    checks = '''    check(
        "Transport numeric fields normalized",
        (
            "NUMERIC_TRANSPORT_FIELDS"
            in
            extractor_source
            and
            "normalizeTransportRecord"
            in
            extractor_source
            and
            "Number("
            in
            re.sub(
                r"\\s+",
                "",
                extractor_source,
            )
        ),
        failures,
    )


    check(
        "Transport normalization copies source record",
        (
            "...value"
            in
            re.sub(
                r"\\s+",
                "",
                extractor_source,
            )
        ),
        failures,
    )


    check(
        "No probability renormalization",
        (
            "normalizeProbability"
            not in
            extractor_source
            and
            "renormal"
            not in
            extractor_source.lower()
        ),
        failures,
    )


'''


    if (
        "Transport numeric fields normalized"
        not in
        source
    ):

        source = replace_once(
            source,
            anchor,
            anchor + checks,
            "transport verifier checks",
        )


    VERIFIER.write_text(
        source,
        encoding="utf-8",
    )


    print(
        "Verifier patched:"
    )

    print(
        f"  {VERIFIER}"
    )


def main() -> None:

    patch_builder()

    patch_verifier()

    print()

    print(
        "STAGE 10.4.11 / 10.4.12 "
        "TRANSPORT PATCH: COMPLETE"
    )


if __name__ == "__main__":

    main()
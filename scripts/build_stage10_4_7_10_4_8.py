from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FRONTEND = ROOT / "frontend"
APP_ROOT = FRONTEND / "app"

DOCS = ROOT / "docs" / "stage10"

FRONTEND_DATA = (
    ROOT
    / "data"
    / "processed"
    / "frontend"
)


PREVIOUS_VERIFICATION_FILE = (
    FRONTEND_DATA
    / "stage10_4_5_10_4_6_verification.json"
)

OUTCOME_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_predicted_outcome_contract.json"
)

PROBABILITY_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_probabilities_contract.json"
)

LOADER_CONTRACT_FILE = (
    DOCS
    / "frontend_upcoming_dashboard_loader_contract.json"
)

MATCH_CARD_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-card.tsx"
)

LOADER_FILE = (
    FRONTEND
    / "lib"
    / "dashboard"
    / "load-upcoming-matches.ts"
)

DOMAIN_TYPES_FILE = (
    FRONTEND
    / "lib"
    / "domain"
    / "types.ts"
)

PROBABILITY_FORMATTER_FILE = (
    FRONTEND
    / "lib"
    / "formatters"
    / "probability.ts"
)


CONFIDENCE_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_confidence_contract.json"
)

UNCERTAINTY_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_uncertainty_contract.json"
)


CONFIDENCE_SECTION = '''        <section
          aria-label="Prediction confidence"
          className="
            rounded-lg
            border border-slate-200
            px-4 py-3
          "
        >
          <div
            className="
              flex items-end
              justify-between gap-4
            "
          >
            <div>
              <p
                className="
                  text-xs font-medium uppercase
                  tracking-wide text-slate-500
                "
              >
                Confidence
              </p>

              <p
                className="
                  mt-1 text-base font-semibold
                  tabular-nums text-slate-950
                "
                data-stage7-field="stage7_confidence"
              >
                {formatProbability(
                  stage7_confidence,
                )}
              </p>
            </div>

            <p
              className="
                text-sm font-semibold
                text-slate-700
              "
              data-stage9-field="confidence_band"
            >
              {confidence_band}
            </p>
          </div>
        </section>

'''


UNCERTAINTY_SECTION = '''        <section
          aria-label="Prediction uncertainty"
          className="
            rounded-lg
            border border-slate-200
            px-4 py-3
          "
        >
          <div
            className="
              flex items-center
              justify-between gap-4
            "
          >
            <p
              className="
                text-xs font-medium uppercase
                tracking-wide text-slate-500
              "
            >
              Uncertainty
            </p>

            <p
              className="
                text-sm font-semibold
                text-slate-700
              "
              data-stage9-field="uncertainty_band"
            >
              {uncertainty_band}
            </p>
          </div>
        </section>

'''


BAND_VALUES = {
    "VERY_LOW",
    "LOW",
    "MODERATE",
    "HIGH",
    "VERY_HIGH",
}


def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise RuntimeError(
            f"Missing artifact: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        payload = json.load(file)

    if not isinstance(
        payload,
        dict,
    ):

        raise RuntimeError(
            f"Expected JSON object: {path}"
        )

    return payload


def optional_json(
    path: Path,
) -> dict | None:

    if not path.exists():

        return None

    return load_json(path)


def sha256_file(
    path: Path,
) -> str:

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as file:

        for chunk in iter(
            lambda:
                file.read(
                    1024 * 1024
                ),
            b"",
        ):

            digest.update(chunk)

    return digest.hexdigest()


def relative(
    path: Path,
) -> str:

    return (
        str(
            path.resolve()
            .relative_to(
                ROOT.resolve()
            )
        )
        .replace("\\", "/")
    )


def identity(
    path: Path,
) -> dict:

    return {
        "sha256":
            sha256_file(path)
    }


def save_text_atomic(
    path: Path,
    text: str,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        text,
        encoding="utf-8",
    )

    temporary.replace(path)


def save_json_atomic(
    path: Path,
    payload: dict,
) -> None:

    save_text_atomic(
        path,
        json.dumps(
            payload,
            indent=2,
        )
        +
        "\n",
    )


def current_route_pages() -> dict:

    output = {}

    for path in sorted(
        APP_ROOT.rglob(
            "page.tsx"
        )
    ):

        output[
            relative(path)
        ] = {
            "sha256":
                sha256_file(path)
        }

    return output


def discover_band_types(
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

def build_domain_import(
    confidence_type: str,
    uncertainty_type: str | None = None,
) -> str:

    names = [
        "OutcomeLabel",
        confidence_type,
    ]


    if (
        uncertainty_type
        and
        uncertainty_type
        not in
        names
    ):

        names.append(
            uncertainty_type
        )


    lines = "\n".join(
        f"  {name},"
        for name in names
    )


    return (
        "import type {\n"
        f"{lines}\n"
        '} from "../../lib/domain/types";'
    )


def replace_domain_import(
    source: str,
    replacement: str,
) -> str:

    pattern = re.compile(
        (
            r'import\s+type\s*\{'
            r'[^}]*'
            r'\}\s*from\s*'
            r'["\']\.\./\.\./lib/domain/types["\'];'
        )
    )


    matches = list(
        pattern.finditer(
            source
        )
    )


    if len(
        matches
    ) != 1:

        raise RuntimeError(
            (
                "Expected exactly one domain "
                "type import in MatchCard."
            )
        )


    return pattern.sub(
        replacement,
        source,
        count=1,
    )


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
                f"{label}: expected one anchor, "
                f"found {count}."
            )
        )


    return source.replace(
        old,
        new,
        1,
    )


def add_confidence(
    source: str,
    confidence_type: str,
) -> str:

    updated = replace_domain_import(
        source,
        build_domain_import(
            confidence_type,
        ),
    )


    updated = replace_once(
        updated,
        (
            "    stage7_predicted_label:\n"
            "      OutcomeLabel;\n"
        ),
        (
            "    stage7_predicted_label:\n"
            "      OutcomeLabel;\n"
            "\n"
            "    stage7_confidence: number;\n"
            "    confidence_band:\n"
            f"      {confidence_type};\n"
        ),
        "confidence props",
    )


    updated = replace_once(
        updated,
        (
            "  stage7_predicted_label,\n"
            "  children,\n"
        ),
        (
            "  stage7_predicted_label,\n"
            "  stage7_confidence,\n"
            "  confidence_band,\n"
            "  children,\n"
        ),
        "confidence destructuring",
    )


    updated = replace_once(
        updated,
        "        {children ? (\n",
        (
            CONFIDENCE_SECTION
            +
            "        {children ? (\n"
        ),
        "confidence presentation",
    )


    return updated


def add_uncertainty(
    source: str,
    confidence_type: str,
    uncertainty_type: str,
) -> str:

    updated = replace_domain_import(
        source,
        build_domain_import(
            confidence_type,
            uncertainty_type,
        ),
    )


    updated = replace_once(
        updated,
        (
            "    confidence_band:\n"
            f"      {confidence_type};\n"
        ),
        (
            "    confidence_band:\n"
            f"      {confidence_type};\n"
            "\n"
            "    uncertainty_band:\n"
            f"      {uncertainty_type};\n"
        ),
        "uncertainty prop",
    )


    updated = replace_once(
        updated,
        (
            "  confidence_band,\n"
            "  children,\n"
        ),
        (
            "  confidence_band,\n"
            "  uncertainty_band,\n"
            "  children,\n"
        ),
        "uncertainty destructuring",
    )


    updated = replace_once(
        updated,
        "        {children ? (\n",
        (
            UNCERTAINTY_SECTION
            +
            "        {children ? (\n"
        ),
        "uncertainty presentation",
    )


    return updated


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.4.7 + 10.4.8"
    )

    print(
        "CONFIDENCE + UNCERTAINTY BUILD"
    )

    print("=" * 72)


    previous = load_json(
        PREVIOUS_VERIFICATION_FILE
    )

    outcome_contract = load_json(
        OUTCOME_CONTRACT_FILE
    )

    probability_contract = load_json(
        PROBABILITY_CONTRACT_FILE
    )

    loader_contract = load_json(
        LOADER_CONTRACT_FILE
    )


    if (
        previous.get(
            "status"
        )
        !=
        "PASS"
    ):

        raise RuntimeError(
            "10.4.5/10.4.6 verification is not PASS."
        )


    if (
        previous.get(
            "stage_10_4_5_complete"
        )
        is not True
        or
        previous.get(
            "stage_10_4_6_complete"
        )
        is not True
    ):

        raise RuntimeError(
            "10.4.5/10.4.6 are not complete."
        )


    if (
        previous.get(
            "stage10_ready_for_10_4_7"
        )
        is not True
    ):

        raise RuntimeError(
            "10.4.6 did not authorize 10.4.7."
        )


    for path in [
        MATCH_CARD_FILE,
        LOADER_FILE,
        DOMAIN_TYPES_FILE,
        PROBABILITY_FORMATTER_FILE,
    ]:

        if not path.exists():

            raise RuntimeError(
                f"Missing required source: {path}"
            )


    expected_pages = (
        outcome_contract
        .get(
            "protected_state",
            {}
        )
        .get(
            "route_page_identity",
            {},
        )
    )


    if (
        not isinstance(
            expected_pages,
            dict,
        )
        or
        not expected_pages
    ):

        raise RuntimeError(
            "Protected route identity missing."
        )


    if (
        current_route_pages()
        !=
        expected_pages
    ):

        raise RuntimeError(
            "Route pages changed after 10.4.6."
        )


    expected_loader_sha = (
        outcome_contract
        .get(
            "protected_state",
            {}
        )
        .get(
            "loader_sha256"
        )
    )


    if (
        sha256_file(
            LOADER_FILE
        )
        !=
        expected_loader_sha
        or
        sha256_file(
            LOADER_FILE
        )
        !=
        loader_contract.get(
            "source_sha256"
        )
    ):

        raise RuntimeError(
            "Dashboard loader changed after 10.4.6."
        )


    expected_formatter_sha = (
        probability_contract.get(
            "probability_formatter_sha256"
        )
    )


    if (
        sha256_file(
            PROBABILITY_FORMATTER_FILE
        )
        !=
        expected_formatter_sha
    ):

        raise RuntimeError(
            (
                "Probability formatter changed "
                "after 10.4.6."
            )
        )


    expected_domain_sha = (
        outcome_contract
        .get(
            "protected_state",
            {}
        )
        .get(
            "domain_types_sha256"
        )
    )


    if (
        sha256_file(
            DOMAIN_TYPES_FILE
        )
        !=
        expected_domain_sha
    ):

        raise RuntimeError(
            "Domain types changed after 10.4.6."
        )


    domain_source = (
        DOMAIN_TYPES_FILE.read_text(
            encoding="utf-8"
        )
    )


    (
        confidence_type,
        uncertainty_type,
    ) = discover_band_types(
        domain_source
    )


    print()

    print(
        "Discovered domain band types:"
    )

    print(
        f"  confidence:  {confidence_type}"
    )

    print(
        f"  uncertainty: {uncertainty_type}"
    )


    existing_confidence = (
        optional_json(
            CONFIDENCE_CONTRACT_FILE
        )
    )

    existing_uncertainty = (
        optional_json(
            UNCERTAINTY_CONTRACT_FILE
        )
    )


    # ========================================================
    # Fully built state
    # ========================================================

    if (
        existing_uncertainty
        and
        sha256_file(
            MATCH_CARD_FILE
        )
        ==
        existing_uncertainty.get(
            "match_card_after_uncertainty_sha256"
        )
    ):

        print()

        print(
            "10.4.7 / 10.4.8 already built."
        )

        print("=" * 72)

        print(
            "STAGE 10.4.7 CONFIDENCE: BUILT"
        )

        print(
            "STAGE 10.4.8 UNCERTAINTY: BUILT"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

        print("=" * 72)

        return


    # ========================================================
    # Stage 10.4.7
    # ========================================================

    current_card_sha = (
        sha256_file(
            MATCH_CARD_FILE
        )
    )


    if (
        existing_confidence
        and
        current_card_sha
        ==
        existing_confidence.get(
            "match_card_after_confidence_sha256"
        )
    ):

        confidence_contract = (
            existing_confidence
        )

        print()

        print(
            "10.4.7 confidence already built."
        )

    else:

        expected_outcome_sha = (
            outcome_contract.get(
                "match_card_after_outcome_sha256"
            )
        )


        if (
            current_card_sha
            !=
            expected_outcome_sha
        ):

            raise RuntimeError(
                (
                    "MatchCard no longer matches "
                    "verified 10.4.6 output."
                )
            )


        before_confidence_sha = (
            current_card_sha
        )


        card_source = (
            MATCH_CARD_FILE.read_text(
                encoding="utf-8"
            )
        )


        confidence_source = (
            add_confidence(
                card_source,
                confidence_type,
            )
        )


        save_text_atomic(
            MATCH_CARD_FILE,
            confidence_source,
        )


        after_confidence_sha = (
            sha256_file(
                MATCH_CARD_FILE
            )
        )


        confidence_contract = {
            "stage":
                "10.4.7",

            "version":
                "1.0.0",

            "name":
                "MATCH_CONFIDENCE",

            "status":
                "LOCKED",

            "source":
                relative(
                    MATCH_CARD_FILE
                ),

            "authority": {
                "stage7_confidence":
                    "STAGE_7_PREDICTION",

                "confidence_band":
                    "STAGE_9_INTELLIGENCE",
            },

            "source_fields": [
                "stage7_confidence",
                "confidence_band",
            ],

            "domain_type":
                confidence_type,

            "presentation": {
                "numeric_confidence":
                    True,

                "numeric_formatter":
                    "formatProbability",

                "confidence_band":
                    True,

                "band_display":
                    "DIRECT_SOURCE_VALUE",

                "band_recalculated":
                    False,

                "thresholds_in_frontend":
                    False,
            },

            "implementation": {
                "server_component":
                    True,

                "confidence_recalculation":
                    False,

                "confidence_band_derivation":
                    False,

                "probability_comparison":
                    False,

                "api_access":
                    False,

                "provider_access":
                    False,

                "artifact_access":
                    False,
            },

            "transition": {
                "match_card_before_confidence_sha256":
                    before_confidence_sha,

                "match_card_after_confidence_sha256":
                    after_confidence_sha,
            },

            "match_card_after_confidence_sha256":
                after_confidence_sha,

            "protected_state": {
                "route_page_identity":
                    expected_pages,

                "loader_sha256":
                    sha256_file(
                        LOADER_FILE
                    ),

                "domain_types_sha256":
                    sha256_file(
                        DOMAIN_TYPES_FILE
                    ),

                "probability_formatter_sha256":
                    sha256_file(
                        PROBABILITY_FORMATTER_FILE
                    ),
            },

            "dependency_identity": {
                relative(
                    PREVIOUS_VERIFICATION_FILE
                ):
                    identity(
                        PREVIOUS_VERIFICATION_FILE
                    ),

                relative(
                    OUTCOME_CONTRACT_FILE
                ):
                    identity(
                        OUTCOME_CONTRACT_FILE
                    ),

                relative(
                    DOMAIN_TYPES_FILE
                ):
                    identity(
                        DOMAIN_TYPES_FILE
                    ),

                relative(
                    PROBABILITY_FORMATTER_FILE
                ):
                    identity(
                        PROBABILITY_FORMATTER_FILE
                    ),

                relative(
                    LOADER_FILE
                ):
                    identity(
                        LOADER_FILE
                    ),
            },

            "promotion": {
                "stage10_4_7_complete":
                    False,

                "stage10_4_complete":
                    False,

                "stage10_complete":
                    False,
            },

            "generated_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),
        }


        save_json_atomic(
            CONFIDENCE_CONTRACT_FILE,
            confidence_contract,
        )


    # ========================================================
    # Stage 10.4.8
    # ========================================================

    if (
        sha256_file(
            MATCH_CARD_FILE
        )
        !=
        confidence_contract.get(
            "match_card_after_confidence_sha256"
        )
    ):

        raise RuntimeError(
            "10.4.7 MatchCard SHA mismatch."
        )


    before_uncertainty_sha = (
        sha256_file(
            MATCH_CARD_FILE
        )
    )


    confidence_source = (
        MATCH_CARD_FILE.read_text(
            encoding="utf-8"
        )
    )


    uncertainty_source = (
        add_uncertainty(
            confidence_source,
            confidence_type,
            uncertainty_type,
        )
    )


    save_text_atomic(
        MATCH_CARD_FILE,
        uncertainty_source,
    )


    after_uncertainty_sha = (
        sha256_file(
            MATCH_CARD_FILE
        )
    )


    uncertainty_contract = {
        "stage":
            "10.4.8",

        "version":
            "1.0.0",

        "name":
            "MATCH_UNCERTAINTY",

        "status":
            "LOCKED",

        "source":
            relative(
                MATCH_CARD_FILE
            ),

        "authority":
            "STAGE_9_INTELLIGENCE",

        "source_field":
            "uncertainty_band",

        "domain_type":
            uncertainty_type,

        "presentation": {
            "band_display":
                "DIRECT_SOURCE_VALUE",

            "frontend_entropy_calculation":
                False,

            "frontend_band_derivation":
                False,

            "frontend_thresholds":
                False,

            "source_value_modified":
                False,
        },

        "implementation": {
            "server_component":
                True,

            "entropy_calculation":
                False,

            "uncertainty_recalculation":
                False,

            "confidence_mutation":
                False,

            "api_access":
                False,

            "provider_access":
                False,

            "artifact_access":
                False,
        },

        "transition": {
            "match_card_before_uncertainty_sha256":
                before_uncertainty_sha,

            "match_card_after_uncertainty_sha256":
                after_uncertainty_sha,
        },

        "match_card_after_uncertainty_sha256":
            after_uncertainty_sha,

        "protected_state": {
            "route_page_identity":
                expected_pages,

            "loader_sha256":
                sha256_file(
                    LOADER_FILE
                ),

            "domain_types_sha256":
                sha256_file(
                    DOMAIN_TYPES_FILE
                ),

            "probability_formatter_sha256":
                sha256_file(
                    PROBABILITY_FORMATTER_FILE
                ),
        },

        "dependency_identity": {
            relative(
                PREVIOUS_VERIFICATION_FILE
            ):
                identity(
                    PREVIOUS_VERIFICATION_FILE
                ),

            relative(
                CONFIDENCE_CONTRACT_FILE
            ):
                identity(
                    CONFIDENCE_CONTRACT_FILE
                ),

            relative(
                DOMAIN_TYPES_FILE
            ):
                identity(
                    DOMAIN_TYPES_FILE
                ),

            relative(
                PROBABILITY_FORMATTER_FILE
            ):
                identity(
                    PROBABILITY_FORMATTER_FILE
                ),

            relative(
                LOADER_FILE
            ):
                identity(
                    LOADER_FILE
                ),
        },

        "promotion": {
            "stage10_4_8_complete":
                False,

            "stage10_4_complete":
                False,

            "stage10_complete":
                False,
        },

        "generated_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }


    save_json_atomic(
        UNCERTAINTY_CONTRACT_FILE,
        uncertainty_contract,
    )


    # ========================================================
    # Final protection
    # ========================================================

    if (
        current_route_pages()
        !=
        expected_pages
    ):

        raise RuntimeError(
            (
                "Route pages changed during "
                "10.4.7/10.4.8."
            )
        )


    if (
        sha256_file(
            LOADER_FILE
        )
        !=
        expected_loader_sha
    ):

        raise RuntimeError(
            (
                "Dashboard loader changed during "
                "10.4.7/10.4.8."
            )
        )


    if (
        sha256_file(
            DOMAIN_TYPES_FILE
        )
        !=
        expected_domain_sha
    ):

        raise RuntimeError(
            (
                "Domain types changed during "
                "10.4.7/10.4.8."
            )
        )


    if (
        sha256_file(
            PROBABILITY_FORMATTER_FILE
        )
        !=
        expected_formatter_sha
    ):

        raise RuntimeError(
            (
                "Probability formatter changed during "
                "10.4.7/10.4.8."
            )
        )


    print()

    print(
        "MatchCard confidence + uncertainty:"
    )

    print(
        f"  {relative(MATCH_CARD_FILE)}"
    )

    print()

    print("=" * 72)

    print(
        "STAGE 10.4.7 CONFIDENCE: BUILT"
    )

    print(
        "STAGE 10.4.8 UNCERTAINTY: BUILT"
    )

    print(
        "STAGE 10 IS NOT YET PROMOTED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
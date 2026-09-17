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
    / "stage10_4_7_10_4_8_verification.json"
)

UNCERTAINTY_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_uncertainty_contract.json"
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


ALIGNMENT_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_context_alignment_contract.json"
)

EXPLANATION_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_explanation_preview_contract.json"
)


ALIGNMENT_VALUES = {
    "SUPPORTIVE",
    "MIXED",
    "CONTRADICTORY",
    "NEUTRAL",
}


ALIGNMENT_SECTION = '''        <section
          aria-label="Context alignment"
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
              Context alignment
            </p>

            <p
              className="
                text-sm font-semibold
                text-slate-700
              "
              data-stage9-field="context_alignment"
            >
              {context_alignment}
            </p>
          </div>
        </section>

'''


EXPLANATION_SECTION = '''        <section
          aria-label="Explanation preview"
          className="
            rounded-lg
            border border-slate-200
            px-4 py-4
          "
        >
          <p
            className="
              text-xs font-medium uppercase
              tracking-wide text-slate-500
            "
          >
            Match intelligence
          </p>

          <h3
            className="
              mt-2 text-base font-semibold
              text-slate-950
            "
            data-stage9-field="explanation_headline"
          >
            {explanation_headline}
          </h3>

          <p
            className="
              mt-2 text-sm leading-6
              text-slate-600
            "
            data-stage9-field="explanation_summary"
          >
            {explanation_summary}
          </p>
        </section>

'''


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

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(
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


def discover_alignment_type(
    source: str,
) -> str:

    exported_names = list(
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


    if "ContextAlignment" in exported_names:
        return "ContextAlignment"


    semantic_candidates = [
        name
        for name in exported_names
        if "alignment" in name.lower()
    ]


    if len(
        semantic_candidates
    ) == 1:

        return semantic_candidates[0]


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


    literal_candidates = []


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
            len(type_starts)
            else
            len(source)
        )

        body = source[
            body_start:
            body_end
        ]


        values = set(
            re.findall(
                (
                    r'["\']'
                    r"(SUPPORTIVE|MIXED|CONTRADICTORY|NEUTRAL)"
                    r'["\']'
                ),
                body,
            )
        )


        if ALIGNMENT_VALUES.issubset(
            values
        ):
            literal_candidates.append(
                name
            )


    if len(
        literal_candidates
    ) == 1:

        return literal_candidates[0]


    raise RuntimeError(
        (
            "Could not uniquely discover the "
            "locked context-alignment domain type. "
            f"Exported types: {exported_names}. "
            f"Candidates: {literal_candidates}."
        )
    )


def ensure_domain_type_import(
    source: str,
    type_name: str,
) -> str:

    pattern = re.compile(
        (
            r'import\s+type\s*\{'
            r'(?P<body>[^}]*)'
            r'\}\s*from\s*'
            r'["\']\.\./\.\./lib/domain/types["\'];'
        )
    )


    matches = list(
        pattern.finditer(
            source
        )
    )


    if len(matches) != 1:

        raise RuntimeError(
            (
                "Expected exactly one domain "
                "type import in MatchCard."
            )
        )


    match = matches[0]

    existing = re.findall(
        r"\b[A-Za-z_$][A-Za-z0-9_$]*\b",
        match.group(
            "body"
        ),
    )


    if type_name in existing:
        return source


    names = [
        *existing,
        type_name,
    ]


    replacement = (
        "import type {\n"
        +
        "".join(
            f"  {name},\n"
            for name in names
        )
        +
        '} from "../../lib/domain/types";'
    )


    return (
        source[
            :match.start()
        ]
        +
        replacement
        +
        source[
            match.end():
        ]
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


def add_context_alignment(
    source: str,
    alignment_type: str,
) -> str:

    updated = ensure_domain_type_import(
        source,
        alignment_type,
    )


    prop_pattern = re.compile(
        (
            r"("
            r"    uncertainty_band:\n"
            r"      [A-Za-z_$][A-Za-z0-9_$]*;\n"
            r")"
        )
    )


    if len(
        prop_pattern.findall(
            updated
        )
    ) != 1:

        raise RuntimeError(
            (
                "Could not uniquely locate "
                "uncertainty_band prop."
            )
        )


    updated = prop_pattern.sub(
        (
            r"\1"
            +
            "\n"
            +
            "    context_alignment:\n"
            +
            f"      {alignment_type};\n"
        ),
        updated,
        count=1,
    )


    updated = replace_once(
        updated,
        (
            "  uncertainty_band,\n"
            "  children,\n"
        ),
        (
            "  uncertainty_band,\n"
            "  context_alignment,\n"
            "  children,\n"
        ),
        "context alignment destructuring",
    )


    updated = replace_once(
        updated,
        "        {children ? (\n",
        (
            ALIGNMENT_SECTION
            +
            "        {children ? (\n"
        ),
        "context alignment presentation",
    )


    return updated


def add_explanation_preview(
    source: str,
    alignment_type: str,
) -> str:

    prop_anchor = (
        "    context_alignment:\n"
        f"      {alignment_type};\n"
    )


    updated = replace_once(
        source,
        prop_anchor,
        (
            prop_anchor
            +
            "\n"
            +
            "    explanation_headline: string;\n"
            +
            "    explanation_summary: string;\n"
        ),
        "explanation props",
    )


    updated = replace_once(
        updated,
        (
            "  context_alignment,\n"
            "  children,\n"
        ),
        (
            "  context_alignment,\n"
            "  explanation_headline,\n"
            "  explanation_summary,\n"
            "  children,\n"
        ),
        "explanation destructuring",
    )


    updated = replace_once(
        updated,
        "        {children ? (\n",
        (
            EXPLANATION_SECTION
            +
            "        {children ? (\n"
        ),
        "explanation presentation",
    )


    return updated


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.4.9 + 10.4.10"
    )

    print(
        "CONTEXT ALIGNMENT + EXPLANATION PREVIEW BUILD"
    )

    print("=" * 72)


    previous = load_json(
        PREVIOUS_VERIFICATION_FILE
    )

    uncertainty_contract = load_json(
        UNCERTAINTY_CONTRACT_FILE
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
            "10.4.7/10.4.8 verification is not PASS."
        )


    if (
        previous.get(
            "stage_10_4_7_complete"
        )
        is not True
        or
        previous.get(
            "stage_10_4_8_complete"
        )
        is not True
    ):
        raise RuntimeError(
            "10.4.7/10.4.8 are not complete."
        )


    if (
        previous.get(
            "stage10_ready_for_10_4_9"
        )
        is not True
    ):
        raise RuntimeError(
            "10.4.8 did not authorize 10.4.9."
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


    protected = (
        uncertainty_contract.get(
            "protected_state",
            {},
        )
    )


    expected_pages = protected.get(
        "route_page_identity",
        {},
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
            "Route pages changed after 10.4.8."
        )


    expected_loader_sha = protected.get(
        "loader_sha256"
    )

    expected_domain_sha = protected.get(
        "domain_types_sha256"
    )

    expected_formatter_sha = protected.get(
        "probability_formatter_sha256"
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
            "Dashboard loader changed after 10.4.8."
        )


    if (
        sha256_file(
            DOMAIN_TYPES_FILE
        )
        !=
        expected_domain_sha
    ):
        raise RuntimeError(
            "Domain types changed after 10.4.8."
        )


    if (
        sha256_file(
            PROBABILITY_FORMATTER_FILE
        )
        !=
        expected_formatter_sha
    ):
        raise RuntimeError(
            "Probability formatter changed after 10.4.8."
        )


    domain_source = (
        DOMAIN_TYPES_FILE.read_text(
            encoding="utf-8"
        )
    )


    alignment_type = (
        discover_alignment_type(
            domain_source
        )
    )


    print()

    print(
        "Discovered context-alignment type:"
    )

    print(
        f"  {alignment_type}"
    )


    existing_alignment = (
        optional_json(
            ALIGNMENT_CONTRACT_FILE
        )
    )

    existing_explanation = (
        optional_json(
            EXPLANATION_CONTRACT_FILE
        )
    )


    # ========================================================
    # Fully built idempotent state
    # ========================================================

    if (
        existing_explanation
        and
        sha256_file(
            MATCH_CARD_FILE
        )
        ==
        existing_explanation.get(
            "match_card_after_explanation_sha256"
        )
    ):

        print()

        print(
            "10.4.9 / 10.4.10 already built."
        )

        print("=" * 72)

        print(
            "STAGE 10.4.9 CONTEXT ALIGNMENT: BUILT"
        )

        print(
            "STAGE 10.4.10 EXPLANATION PREVIEW: BUILT"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

        print("=" * 72)

        return


    # ========================================================
    # Stage 10.4.9
    # ========================================================

    current_card_sha = (
        sha256_file(
            MATCH_CARD_FILE
        )
    )


    if (
        existing_alignment
        and
        current_card_sha
        ==
        existing_alignment.get(
            "match_card_after_alignment_sha256"
        )
    ):

        alignment_contract = (
            existing_alignment
        )

        print()

        print(
            "10.4.9 alignment already built."
        )

    else:

        expected_uncertainty_sha = (
            uncertainty_contract.get(
                "match_card_after_uncertainty_sha256"
            )
        )


        if (
            current_card_sha
            !=
            expected_uncertainty_sha
        ):
            raise RuntimeError(
                (
                    "MatchCard no longer matches "
                    "verified 10.4.8 output."
                )
            )


        before_alignment_sha = (
            current_card_sha
        )


        card_source = (
            MATCH_CARD_FILE.read_text(
                encoding="utf-8"
            )
        )


        alignment_source = (
            add_context_alignment(
                card_source,
                alignment_type,
            )
        )


        save_text_atomic(
            MATCH_CARD_FILE,
            alignment_source,
        )


        after_alignment_sha = (
            sha256_file(
                MATCH_CARD_FILE
            )
        )


        alignment_contract = {
            "stage":
                "10.4.9",

            "version":
                "1.0.0",

            "name":
                "MATCH_CONTEXT_ALIGNMENT",

            "status":
                "LOCKED",

            "source":
                relative(
                    MATCH_CARD_FILE
                ),

            "authority":
                "STAGE_9_INTELLIGENCE",

            "source_field":
                "context_alignment",

            "domain_type":
                alignment_type,

            "allowed_values": [
                "SUPPORTIVE",
                "MIXED",
                "CONTRADICTORY",
                "NEUTRAL",
            ],

            "presentation": {
                "direct_source_value":
                    True,

                "derived_from_support_score":
                    False,

                "frontend_alignment_rules":
                    False,

                "color_only_meaning":
                    False,
            },

            "implementation": {
                "server_component":
                    True,

                "alignment_recalculation":
                    False,

                "context_support_score_used":
                    False,

                "api_access":
                    False,

                "provider_access":
                    False,

                "artifact_access":
                    False,
            },

            "transition": {
                "match_card_before_alignment_sha256":
                    before_alignment_sha,

                "match_card_after_alignment_sha256":
                    after_alignment_sha,
            },

            "match_card_after_alignment_sha256":
                after_alignment_sha,

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
                    UNCERTAINTY_CONTRACT_FILE
                ):
                    identity(
                        UNCERTAINTY_CONTRACT_FILE
                    ),

                relative(
                    DOMAIN_TYPES_FILE
                ):
                    identity(
                        DOMAIN_TYPES_FILE
                    ),

                relative(
                    LOADER_FILE
                ):
                    identity(
                        LOADER_FILE
                    ),
            },

            "promotion": {
                "stage10_4_9_complete":
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
            ALIGNMENT_CONTRACT_FILE,
            alignment_contract,
        )


    # ========================================================
    # Stage 10.4.10
    # ========================================================

    if (
        sha256_file(
            MATCH_CARD_FILE
        )
        !=
        alignment_contract.get(
            "match_card_after_alignment_sha256"
        )
    ):
        raise RuntimeError(
            "10.4.9 MatchCard SHA mismatch."
        )


    before_explanation_sha = (
        sha256_file(
            MATCH_CARD_FILE
        )
    )


    alignment_source = (
        MATCH_CARD_FILE.read_text(
            encoding="utf-8"
        )
    )


    explanation_source = (
        add_explanation_preview(
            alignment_source,
            alignment_type,
        )
    )


    save_text_atomic(
        MATCH_CARD_FILE,
        explanation_source,
    )


    after_explanation_sha = (
        sha256_file(
            MATCH_CARD_FILE
        )
    )


    explanation_contract = {
        "stage":
            "10.4.10",

        "version":
            "1.0.0",

        "name":
            "MATCH_EXPLANATION_PREVIEW",

        "status":
            "LOCKED",

        "source":
            relative(
                MATCH_CARD_FILE
            ),

        "authority":
            "STAGE_9_INTELLIGENCE",

        "source_fields": [
            "explanation_headline",
            "explanation_summary",
        ],

        "presentation": {
            "headline_direct":
                True,

            "summary_direct":
                True,

            "frontend_generated_text":
                False,

            "frontend_rewrite":
                False,

            "frontend_truncation":
                False,

            "fallback_explanation":
                False,
        },

        "implementation": {
            "server_component":
                True,

            "llm_usage":
                False,

            "explanation_generation":
                False,

            "prediction_logic":
                False,

            "api_access":
                False,

            "provider_access":
                False,

            "artifact_access":
                False,
        },

        "transition": {
            "match_card_before_explanation_sha256":
                before_explanation_sha,

            "match_card_after_explanation_sha256":
                after_explanation_sha,
        },

        "match_card_after_explanation_sha256":
            after_explanation_sha,

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
                ALIGNMENT_CONTRACT_FILE
            ):
                identity(
                    ALIGNMENT_CONTRACT_FILE
                ),

            relative(
                DOMAIN_TYPES_FILE
            ):
                identity(
                    DOMAIN_TYPES_FILE
                ),

            relative(
                LOADER_FILE
            ):
                identity(
                    LOADER_FILE
                ),
        },

        "promotion": {
            "stage10_4_10_complete":
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
        EXPLANATION_CONTRACT_FILE,
        explanation_contract,
    )


    # ========================================================
    # Final protections
    # ========================================================

    if (
        current_route_pages()
        !=
        expected_pages
    ):
        raise RuntimeError(
            (
                "Route pages changed during "
                "10.4.9/10.4.10."
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
                "10.4.9/10.4.10."
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
                "10.4.9/10.4.10."
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
                "10.4.9/10.4.10."
            )
        )


    print()

    print(
        "MatchCard context alignment + explanation:"
    )

    print(
        f"  {relative(MATCH_CARD_FILE)}"
    )

    print()

    print("=" * 72)

    print(
        "STAGE 10.4.9 CONTEXT ALIGNMENT: BUILT"
    )

    print(
        "STAGE 10.4.10 EXPLANATION PREVIEW: BUILT"
    )

    print(
        "STAGE 10 IS NOT YET PROMOTED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
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


STAGE10_3_FINAL = (
    FRONTEND_DATA
    / "stage10_3_final_verification.json"
)

MAPPED_API_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "mapped.ts"
)

RESULT_API_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "result.ts"
)

VALIDATED_API_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "validated.ts"
)

HOME_PAGE_FILE = (
    APP_ROOT
    / "page.tsx"
)


LOADER_FILE = (
    FRONTEND
    / "lib"
    / "dashboard"
    / "load-upcoming-matches.ts"
)

MATCH_CARD_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-card.tsx"
)


LOADER_CONTRACT_FILE = (
    DOCS
    / "frontend_upcoming_dashboard_loader_contract.json"
)

MATCH_CARD_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_base_contract.json"
)


def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise RuntimeError(
            f"Missing required JSON artifact: {path}"
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


def route_page_identity() -> dict:

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


def discover_upcoming_mapped_export(
    source: str,
) -> str:

    exported_names: set[str] = set()


    function_pattern = re.compile(
        (
            r"export\s+"
            r"(?:async\s+)?"
            r"function\s+"
            r"([A-Za-z_$][A-Za-z0-9_$]*)"
        )
    )


    const_pattern = re.compile(
        (
            r"export\s+const\s+"
            r"([A-Za-z_$][A-Za-z0-9_$]*)"
        )
    )


    for pattern in [
        function_pattern,
        const_pattern,
    ]:

        exported_names.update(
            pattern.findall(
                source
            )
        )


    candidates = sorted(
        name
        for name in exported_names
        if (
            "upcoming"
            in
            name.lower()
            and
            "intelligence"
            in
            name.lower()
        )
    )


    if not candidates:

        candidates = sorted(
            name
            for name in exported_names
            if "upcoming" in name.lower()
        )


    if len(candidates) != 1:

        raise RuntimeError(
            (
                "Could not uniquely discover the "
                "mapped upcoming-intelligence API export. "
                f"Candidates: {candidates}"
            )
        )


    chosen = candidates[0]


    if chosen not in source:

        raise RuntimeError(
            "Discovered export missing from mapped.ts."
        )


    return chosen


def build_loader_source(
    mapped_export: str,
) -> str:

    return f'''import "server-only";

import {{
  {mapped_export},
}} from "../api/mapped";


export async function loadUpcomingMatches() {{
  return {mapped_export}();
}}
'''


MATCH_CARD_SOURCE = '''import type {
  ReactNode,
} from "react";


type MatchCardProps =
  Readonly<{
    children?:
      ReactNode;
  }>;


export function MatchCard({
  children,
}: MatchCardProps) {
  return (
    <article
      className="
        overflow-hidden rounded-xl
        border border-slate-200
        bg-white shadow-sm
      "
      data-fixtureiq-component="match-card"
    >
      {children}
    </article>
  );
}
'''


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.4.1 + 10.4.2"
    )

    print(
        "UPCOMING DASHBOARD LOADER + MATCHCARD BASE BUILD"
    )

    print("=" * 72)


    stage10_3 = load_json(
        STAGE10_3_FINAL
    )


    if (
        stage10_3.get(
            "status"
        )
        !=
        "PASS"
    ):

        raise RuntimeError(
            "Stage 10.3 final verification is not PASS."
        )


    if (
        stage10_3.get(
            "stage_10_3_complete"
        )
        is not True
    ):

        raise RuntimeError(
            "Stage 10.3 is not COMPLETE."
        )


    if (
        stage10_3.get(
            "stage10_ready_for_10_4_1"
        )
        is not True
    ):

        raise RuntimeError(
            "Stage 10.3 did not authorize 10.4.1."
        )


    required_existing = [
        MAPPED_API_FILE,
        RESULT_API_FILE,
        VALIDATED_API_FILE,
        HOME_PAGE_FILE,
    ]


    for path in required_existing:

        if not path.exists():

            raise RuntimeError(
                f"Missing required frontend file: {path}"
            )


    route_pages_before = (
        route_page_identity()
    )


    mapped_before_sha = (
        sha256_file(
            MAPPED_API_FILE
        )
    )

    result_before_sha = (
        sha256_file(
            RESULT_API_FILE
        )
    )

    validated_before_sha = (
        sha256_file(
            VALIDATED_API_FILE
        )
    )


    mapped_source = (
        MAPPED_API_FILE.read_text(
            encoding="utf-8"
        )
    )


    mapped_export = (
        discover_upcoming_mapped_export(
            mapped_source
        )
    )


    print()

    print(
        "Discovered Stage 10.2 mapped upcoming export:"
    )

    print(
        f"  {mapped_export}"
    )


    # ========================================================
    # Stage 10.4.1
    # ========================================================

    loader_source = (
        build_loader_source(
            mapped_export
        )
    )


    save_text_atomic(
        LOADER_FILE,
        loader_source,
    )


    loader_contract = {
        "stage":
            "10.4.1",

        "version":
            "1.0.0",

        "name":
            "UPCOMING_MATCHES_DASHBOARD_LOADER",

        "status":
            "LOCKED",

        "source":
            relative(
                LOADER_FILE
            ),

        "export":
            "loadUpcomingMatches",

        "upstream": {
            "mapped_api_source":
                relative(
                    MAPPED_API_FILE
                ),

            "mapped_export":
                mapped_export,

            "backend_authority":
                "STAGE_9_INTELLIGENCE",

            "endpoint_authority":
                "/api/v1/intelligence/upcoming",
        },

        "implementation": {
            "server_only":
                True,

            "shared_mapped_api_client":
                True,

            "direct_fetch":
                False,

            "direct_backend_url":
                False,

            "response_transformation":
                False,

            "probability_transformation":
                False,

            "sorting":
                False,

            "filtering":
                False,

            "retry":
                False,

            "stale_fallback":
                False,

            "cache_storage":
                False,

            "provider_access":
                False,

            "artifact_access":
                False,
        },

        "data_state_authority":
            "STAGE_10_2_MAPPED_API_RESULT",

        "deferred_to_later_stages": [
            "dashboard rendering",
            "match identity",
            "kickoff display",
            "probability display",
            "predicted outcome",
            "confidence",
            "uncertainty",
            "context alignment",
            "explanation preview",
            "detail links",
        ],

        "source_sha256":
            sha256_file(
                LOADER_FILE
            ),

        "protected_state": {
            "route_page_identity":
                route_pages_before,

            "mapped_api_sha256":
                mapped_before_sha,

            "result_api_sha256":
                result_before_sha,

            "validated_api_sha256":
                validated_before_sha,
        },

        "dependency_identity": {
            relative(
                STAGE10_3_FINAL
            ):
                identity(
                    STAGE10_3_FINAL
                ),

            relative(
                MAPPED_API_FILE
            ):
                identity(
                    MAPPED_API_FILE
                ),

            relative(
                RESULT_API_FILE
            ):
                identity(
                    RESULT_API_FILE
                ),

            relative(
                VALIDATED_API_FILE
            ):
                identity(
                    VALIDATED_API_FILE
                ),
        },

        "promotion": {
            "stage10_4_1_complete":
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
        LOADER_CONTRACT_FILE,
        loader_contract,
    )


    # ========================================================
    # Stage 10.4.2
    # ========================================================

    save_text_atomic(
        MATCH_CARD_FILE,
        MATCH_CARD_SOURCE,
    )


    match_card_contract = {
        "stage":
            "10.4.2",

        "version":
            "1.0.0",

        "name":
            "MATCH_CARD_BASE",

        "status":
            "LOCKED",

        "source":
            relative(
                MATCH_CARD_FILE
            ),

        "component":
            "MatchCard",

        "semantic_element":
            "article",

        "role": {
            "structural_container_only":
                True,

            "accepts_children":
                True,

            "server_component":
                True,
        },

        "base_visual_structure": {
            "border":
                True,

            "rounded":
                True,

            "background":
                True,

            "shadow":
                True,

            "responsive_feature_logic":
                False,
        },

        "not_implemented_yet": {
            "identity":
                "10.4.3",

            "kickoff":
                "10.4.4",

            "probabilities":
                "10.4.5",

            "predicted_outcome":
                "10.4.6",

            "confidence":
                "10.4.7",

            "uncertainty":
                "10.4.8",

            "context_alignment":
                "10.4.9",

            "explanation_preview":
                "10.4.10",

            "detail_links":
                "10.4.11",
        },

        "safety": {
            "api_access":
                False,

            "provider_access":
                False,

            "artifact_access":
                False,

            "prediction_logic":
                False,

            "probability_logic":
                False,

            "frontend_prediction":
                False,
        },

        "source_sha256":
            sha256_file(
                MATCH_CARD_FILE
            ),

        "protected_state": {
            "route_page_identity":
                route_pages_before,

            "loader_sha256":
                sha256_file(
                    LOADER_FILE
                ),
        },

        "dependency_identity": {
            relative(
                STAGE10_3_FINAL
            ):
                identity(
                    STAGE10_3_FINAL
                ),

            relative(
                LOADER_CONTRACT_FILE
            ):
                identity(
                    LOADER_CONTRACT_FILE
                ),

            relative(
                LOADER_FILE
            ):
                identity(
                    LOADER_FILE
                ),
        },

        "promotion": {
            "stage10_4_2_complete":
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
        MATCH_CARD_CONTRACT_FILE,
        match_card_contract,
    )


    # ========================================================
    # Protection
    # ========================================================

    if (
        route_page_identity()
        !=
        route_pages_before
    ):

        raise RuntimeError(
            (
                "Route pages changed during "
                "10.4.1/10.4.2 build."
            )
        )


    if (
        sha256_file(
            MAPPED_API_FILE
        )
        !=
        mapped_before_sha
    ):

        raise RuntimeError(
            "mapped.ts changed during build."
        )


    if (
        sha256_file(
            RESULT_API_FILE
        )
        !=
        result_before_sha
    ):

        raise RuntimeError(
            "result.ts changed during build."
        )


    if (
        sha256_file(
            VALIDATED_API_FILE
        )
        !=
        validated_before_sha
    ):

        raise RuntimeError(
            "validated.ts changed during build."
        )


    print()

    print(
        "Upcoming dashboard loader:"
    )

    print(
        f"  {relative(LOADER_FILE)}"
    )


    print(
        "MatchCard base:"
    )

    print(
        f"  {relative(MATCH_CARD_FILE)}"
    )


    print()

    print(
        "Dashboard page intentionally unchanged:"
    )

    print(
        f"  {relative(HOME_PAGE_FILE)}"
    )


    print()

    print("=" * 72)

    print(
        "STAGE 10.4.1 UPCOMING MATCHES LOADER: BUILT"
    )

    print(
        "STAGE 10.4.2 MATCHCARD BASE: BUILT"
    )

    print(
        "STAGE 10 IS NOT YET PROMOTED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
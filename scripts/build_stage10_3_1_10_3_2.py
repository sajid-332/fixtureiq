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


STAGE10_2_FINAL_FILE = (
    FRONTEND_DATA
    / "stage10_2_final_verification.json"
)

ROUTE_ARCHITECTURE_FILE = (
    DOCS
    / "frontend_route_architecture.json"
)


LAYOUT_FILE = (
    APP_ROOT
    / "layout.tsx"
)

GLOBALS_FILE = (
    APP_ROOT
    / "globals.css"
)

HEADER_FILE = (
    FRONTEND
    / "components"
    / "shell"
    / "site-header.tsx"
)


LAYOUT_CONTRACT_FILE = (
    DOCS
    / "frontend_global_layout_contract.json"
)

HEADER_CONTRACT_FILE = (
    DOCS
    / "frontend_header_navigation_contract.json"
)


HEADER_IMPORT = (
    'import { SiteHeader } '
    'from "../components/shell/site-header";'
)


HEADER_SOURCE = '''import Link from "next/link";


export function SiteHeader() {
  return (
    <header
      className="
        border-b border-slate-200
        bg-white
      "
      data-fixtureiq-shell="header"
    >
      <div
        className="
          mx-auto flex min-h-16 w-full
          max-w-7xl items-center
          justify-between gap-4
          px-4 sm:px-6 lg:px-8
        "
      >
        <Link
          href="/"
          aria-label="FixtureIQ home"
          className="
            flex min-w-0 items-center
            gap-3 font-semibold
            tracking-tight text-slate-950
          "
        >
          <span>
            FixtureIQ
          </span>

          <span
            className="
              hidden text-xs font-medium
              text-slate-500 sm:inline
            "
          >
            Premier League Intelligence
          </span>
        </Link>

        <nav
          aria-label="Primary navigation"
        >
          <Link
            href="/"
            className="
              inline-flex min-h-10
              items-center rounded-md
              px-3 text-sm font-medium
              text-slate-700
              transition-colors
              hover:bg-slate-100
              hover:text-slate-950
              focus-visible:outline-none
              focus-visible:ring-2
              focus-visible:ring-slate-400
              focus-visible:ring-offset-2
            "
          >
            Upcoming
          </Link>
        </nav>
      </div>
    </header>
  );
}
'''


def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise RuntimeError(
            f"Missing required artifact: {path}"
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


def get_route_page_identity() -> dict:

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


def verify_route_pages_unchanged(
    before: dict,
) -> None:

    after = (
        get_route_page_identity()
    )

    if after != before:

        raise RuntimeError(
            (
                "Route page identity changed while "
                "building 10.3.1/10.3.2. "
                "Build aborted."
            )
        )


def patch_layout(
    source: str,
) -> str:

    updated = source


    if (
        "./globals.css"
        not in
        updated
    ):

        raise RuntimeError(
            (
                "Existing root layout does not "
                "import ./globals.css. "
                "Refusing to rewrite unknown layout."
            )
        )


    if (
        "SiteHeader"
        not in
        updated
    ):

        globals_import_pattern = re.compile(
            (
                r'(^\s*import\s+'
                r'["\']\.\/globals\.css["\'];?\s*$)'
            ),
            re.MULTILINE,
        )

        match = (
            globals_import_pattern.search(
                updated
            )
        )

        if match is None:

            raise RuntimeError(
                (
                    "Could not locate the existing "
                    "globals.css import safely."
                )
            )

        updated = (
            updated[
                :match.end()
            ]
            +
            "\n"
            +
            HEADER_IMPORT
            +
            updated[
                match.end():
            ]
        )


    if (
        "<SiteHeader />"
        not in
        updated
    ):

        body_pattern = re.compile(
            r"<body(?P<attrs>[^>]*)>",
            re.MULTILINE,
        )

        match = body_pattern.search(
            updated
        )

        if match is None:

            raise RuntimeError(
                (
                    "Could not locate the existing "
                    "<body> element safely."
                )
            )

        body_open = match.group(0)

        replacement = (
            body_open
            +
            "\n"
            +
            "        <SiteHeader />"
        )

        updated = (
            updated[
                :match.start()
            ]
            +
            replacement
            +
            updated[
                match.end():
            ]
        )


    if (
        updated.count(
            "<SiteHeader />"
        )
        !=
        1
    ):

        raise RuntimeError(
            (
                "Root layout must contain exactly "
                "one SiteHeader."
            )
        )


    return updated


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.3.1 + 10.3.2"
    )

    print(
        "GLOBAL APPLICATION LAYOUT + HEADER / NAVIGATION BUILD"
    )

    print("=" * 72)


    stage10_2 = load_json(
        STAGE10_2_FINAL_FILE
    )

    route_architecture = load_json(
        ROUTE_ARCHITECTURE_FILE
    )


    if (
        stage10_2.get(
            "status"
        )
        !=
        "PASS"
    ):

        raise RuntimeError(
            "Stage 10.2 final verification is not PASS."
        )


    if (
        stage10_2.get(
            "stage_10_2_complete"
        )
        is not True
    ):

        raise RuntimeError(
            "Stage 10.2 is not marked complete."
        )


    if (
        stage10_2.get(
            "stage10_ready_for_10_3_1"
        )
        is not True
    ):

        raise RuntimeError(
            "Stage 10.2 did not authorize 10.3.1."
        )


    if (
        route_architecture.get(
            "status"
        )
        !=
        "LOCKED"
    ):

        raise RuntimeError(
            (
                "Stage 10.1.4 route architecture "
                "is not LOCKED."
            )
        )


    for path in [
        LAYOUT_FILE,
        GLOBALS_FILE,
    ]:

        if not path.exists():

            raise RuntimeError(
                f"Missing frontend shell file: {path}"
            )


    route_pages_before = (
        get_route_page_identity()
    )


    original_layout = (
        LAYOUT_FILE.read_text(
            encoding="utf-8"
        )
    )


    layout_before_sha = (
        sha256_file(
            LAYOUT_FILE
        )
    )


    updated_layout = patch_layout(
        original_layout
    )


    save_text_atomic(
        HEADER_FILE,
        HEADER_SOURCE,
    )


    save_text_atomic(
        LAYOUT_FILE,
        updated_layout,
    )


    verify_route_pages_unchanged(
        route_pages_before
    )


    layout_contract = {
        "stage":
            "10.3.1",

        "version":
            "1.0.0",

        "name":
            "GLOBAL_APPLICATION_LAYOUT",

        "status":
            "LOCKED",

        "framework":
            "NEXTJS_APP_ROUTER",

        "root_layout":
            relative(
                LAYOUT_FILE
            ),

        "global_styles":
            relative(
                GLOBALS_FILE
            ),

        "shell_structure": {
            "html_root":
                True,

            "body_root":
                True,

            "global_header":
                True,

            "children_slot":
                True,

            "main_container_owned_by":
                "10.3.3",

            "footer_owned_by":
                "10.3.4",

            "typography_polish_owned_by":
                "10.3.5",

            "mobile_navigation_owned_by":
                "10.3.6",
        },

        "implementation": {
            "existing_layout_patched":
                True,

            "existing_layout_replaced_blindly":
                False,

            "globals_css_preserved":
                True,

            "route_pages_modified":
                False,

            "data_fetching_added":
                False,

            "api_calls_added":
                False,

            "client_component_required":
                False,
        },

        "layout_before_sha256":
            layout_before_sha,

        "layout_after_sha256":
            sha256_file(
                LAYOUT_FILE
            ),

        "protected_route_page_identity":
            route_pages_before,

        "dependency_identity": {
            relative(
                STAGE10_2_FINAL_FILE
            ):
                identity(
                    STAGE10_2_FINAL_FILE
                ),

            relative(
                ROUTE_ARCHITECTURE_FILE
            ):
                identity(
                    ROUTE_ARCHITECTURE_FILE
                ),
        },

        "promotion": {
            "stage10_3_1_complete":
                False,

            "stage10_3_complete":
                False,

            "stage10_complete":
                False,
        },

        "generated_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }


    header_contract = {
        "stage":
            "10.3.2",

        "version":
            "1.0.0",

        "name":
            "HEADER_NAVIGATION",

        "status":
            "LOCKED",

        "source":
            relative(
                HEADER_FILE
            ),

        "component":
            "SiteHeader",

        "framework_primitives": {
            "next_link":
                True,

            "server_component":
                True,
        },

        "brand": {
            "name":
                "FixtureIQ",

            "home_href":
                "/",
        },

        "navigation": {
            "aria_label":
                "Primary navigation",

            "static_links": [
                {
                    "label":
                        "Upcoming",

                    "href":
                        "/",
                }
            ],

            "dynamic_match_index_invented":
                False,

            "dynamic_team_index_invented":
                False,

            "placeholder_navigation":
                False,
        },

        "boundaries": {
            "mobile_menu_implemented":
                False,

            "mobile_menu_owner":
                "10.3.6",

            "api_access":
                False,

            "prediction_logic":
                False,

            "direct_artifact_access":
                False,

            "provider_access":
                False,
        },

        "source_sha256":
            sha256_file(
                HEADER_FILE
            ),

        "dependency_identity": {
            relative(
                STAGE10_2_FINAL_FILE
            ):
                identity(
                    STAGE10_2_FINAL_FILE
                ),

            relative(
                ROUTE_ARCHITECTURE_FILE
            ):
                identity(
                    ROUTE_ARCHITECTURE_FILE
                ),

            relative(
                LAYOUT_CONTRACT_FILE
            ):
                {},
        },

        "promotion": {
            "stage10_3_2_complete":
                False,

            "stage10_3_complete":
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
        LAYOUT_CONTRACT_FILE,
        layout_contract,
    )


    header_contract[
        "dependency_identity"
    ][
        relative(
            LAYOUT_CONTRACT_FILE
        )
    ] = identity(
        LAYOUT_CONTRACT_FILE
    )


    save_json_atomic(
        HEADER_CONTRACT_FILE,
        header_contract,
    )


    print()

    print(
        "Root layout:"
    )

    print(
        f"  {relative(LAYOUT_FILE)}"
    )


    print(
        "Header:"
    )

    print(
        f"  {relative(HEADER_FILE)}"
    )


    print()

    print(
        "Route pages preserved:"
    )

    print(
        f"  {len(route_pages_before)}"
    )


    print()

    print(
        "Global navigation:"
    )

    print(
        "  FixtureIQ -> /"
    )

    print(
        "  Upcoming  -> /"
    )


    print()

    print("=" * 72)

    print(
        "STAGE 10.3.1 GLOBAL APPLICATION LAYOUT: BUILT"
    )

    print(
        "STAGE 10.3.2 HEADER / NAVIGATION: BUILT"
    )

    print(
        "STAGE 10 IS NOT YET PROMOTED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
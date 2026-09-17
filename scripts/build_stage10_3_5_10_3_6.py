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
    / "stage10_3_3_10_3_4_verification.json"
)

LAYOUT_CONTRACT_FILE = (
    DOCS
    / "frontend_global_layout_contract.json"
)

HEADER_CONTRACT_FILE = (
    DOCS
    / "frontend_header_navigation_contract.json"
)

MAIN_CONTRACT_FILE = (
    DOCS
    / "frontend_main_container_contract.json"
)

FOOTER_CONTRACT_FILE = (
    DOCS
    / "frontend_footer_contract.json"
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

MAIN_FILE = (
    FRONTEND
    / "components"
    / "shell"
    / "main-container.tsx"
)

FOOTER_FILE = (
    FRONTEND
    / "components"
    / "shell"
    / "site-footer.tsx"
)

MOBILE_NAV_FILE = (
    FRONTEND
    / "components"
    / "shell"
    / "mobile-navigation.tsx"
)


TYPOGRAPHY_CONTRACT_FILE = (
    DOCS
    / "frontend_typography_layout_contract.json"
)

MOBILE_NAV_CONTRACT_FILE = (
    DOCS
    / "frontend_mobile_navigation_contract.json"
)


TYPOGRAPHY_MARKER = (
    "/* FixtureIQ Stage 10.3.5 "
    "Typography / Layout */"
)


TYPOGRAPHY_BLOCK = r'''
/* FixtureIQ Stage 10.3.5 Typography / Layout */

html {
  min-width: 320px;
  background: #f8fafc;
}

body {
  min-height: 100vh;
  background: #f8fafc;
  color: #0f172a;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

h1,
h2,
h3 {
  text-wrap: balance;
}

p {
  text-wrap: pretty;
}

::selection {
  background: #cbd5e1;
  color: #0f172a;
}
'''


MOBILE_NAV_SOURCE = '''import Link from "next/link";


export function MobileNavigation() {
  return (
    <nav
      aria-label="Mobile navigation"
      className="sm:hidden"
      data-fixtureiq-shell="mobile-navigation"
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
  );
}
'''


MOBILE_IMPORT = (
    'import { MobileNavigation } '
    'from "./mobile-navigation";'
)


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


def current_route_page_identity() -> dict:

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


def expected_route_identity(
    main_contract: dict,
) -> dict:

    protected = (
        main_contract
        .get(
            "protected_state",
            {}
        )
        .get(
            "route_page_identity",
            {},
        )
    )

    if not isinstance(
        protected,
        dict,
    ):
        raise RuntimeError(
            "Protected route identity missing."
        )

    return protected


def verify_route_pages(
    expected: dict,
) -> None:

    current = (
        current_route_page_identity()
    )

    if current != expected:

        raise RuntimeError(
            (
                "Route pages changed during "
                "10.3.5/10.3.6."
            )
        )


def append_typography(
    source: str,
) -> str:

    if TYPOGRAPHY_MARKER in source:
        return source

    return (
        source.rstrip()
        +
        "\n\n"
        +
        TYPOGRAPHY_BLOCK.strip()
        +
        "\n"
    )


def add_mobile_import(
    source: str,
) -> str:

    if MOBILE_IMPORT in source:
        return source

    link_import = re.compile(
        (
            r'(^\s*import\s+Link\s+'
            r'from\s+["\']next/link["\'];?\s*$)'
        ),
        re.MULTILINE,
    )

    match = link_import.search(
        source
    )

    if match is None:

        raise RuntimeError(
            (
                "Could not safely locate "
                "next/link import."
            )
        )

    return (
        source[
            :match.end()
        ]
        +
        "\n"
        +
        MOBILE_IMPORT
        +
        source[
            match.end():
        ]
    )


def patch_desktop_navigation(
    source: str,
) -> str:

    updated = add_mobile_import(
        source
    )


    if (
        "<MobileNavigation />"
        in
        updated
    ):

        return updated


    pattern = re.compile(
        (
            r'(?P<indent>[ \t]*)'
            r'<nav\s*'
            r'aria-label="Primary navigation"'
            r'\s*>'
            r'(?P<body>[\s\S]*?)'
            r'</nav>'
        ),
        re.MULTILINE,
    )


    match = pattern.search(
        updated
    )


    if match is None:

        raise RuntimeError(
            (
                "Verified primary navigation "
                "could not be located."
            )
        )


    body = match.group(
        "body"
    )

    indent = match.group(
        "indent"
    )


    if "Upcoming" not in body:

        raise RuntimeError(
            (
                "Primary navigation no longer "
                "contains Upcoming."
            )
        )


    replacement = (
        f'{indent}<nav\n'
        f'{indent}  aria-label="Primary navigation"\n'
        f'{indent}  className="hidden sm:block"\n'
        f'{indent}>'
        f'{body}'
        f'{indent}</nav>\n'
        f'{indent}<MobileNavigation />'
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
            "<MobileNavigation />"
        )
        !=
        1
    ):

        raise RuntimeError(
            (
                "SiteHeader must render exactly "
                "one MobileNavigation."
            )
        )


    return updated


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.3.5 + 10.3.6"
    )

    print(
        "TYPOGRAPHY / LAYOUT + MOBILE NAVIGATION BUILD"
    )

    print("=" * 72)


    previous = load_json(
        PREVIOUS_VERIFICATION_FILE
    )

    layout_contract = load_json(
        LAYOUT_CONTRACT_FILE
    )

    header_contract = load_json(
        HEADER_CONTRACT_FILE
    )

    main_contract = load_json(
        MAIN_CONTRACT_FILE
    )

    footer_contract = load_json(
        FOOTER_CONTRACT_FILE
    )

    route_architecture = load_json(
        ROUTE_ARCHITECTURE_FILE
    )


    if (
        previous.get(
            "status"
        )
        !=
        "PASS"
    ):

        raise RuntimeError(
            (
                "10.3.3-10.3.4 verification "
                "is not PASS."
            )
        )


    if (
        previous.get(
            "stage10_ready_for_10_3_5"
        )
        is not True
    ):

        raise RuntimeError(
            (
                "10.3.4 did not authorize "
                "10.3.5."
            )
        )


    for label, payload in [
        (
            "layout",
            layout_contract,
        ),
        (
            "header",
            header_contract,
        ),
        (
            "main",
            main_contract,
        ),
        (
            "footer",
            footer_contract,
        ),
        (
            "route architecture",
            route_architecture,
        ),
    ]:

        if (
            payload.get(
                "status"
            )
            !=
            "LOCKED"
        ):

            raise RuntimeError(
                f"{label} contract is not LOCKED."
            )


    for path in [
        LAYOUT_FILE,
        GLOBALS_FILE,
        HEADER_FILE,
        MAIN_FILE,
        FOOTER_FILE,
    ]:

        if not path.exists():

            raise RuntimeError(
                f"Missing shell source: {path}"
            )


    route_identity = (
        expected_route_identity(
            main_contract
        )
    )


    verify_route_pages(
        route_identity
    )


    expected_layout_sha = (
        footer_contract
        .get(
            "layout_transition",
            {}
        )
        .get(
            "after_footer_sha256"
        )
    )


    if (
        sha256_file(
            LAYOUT_FILE
        )
        !=
        expected_layout_sha
    ):

        raise RuntimeError(
            (
                "layout.tsx changed after "
                "10.3.4 verification."
            )
        )


    if (
        sha256_file(
            MAIN_FILE
        )
        !=
        main_contract.get(
            "source_sha256"
        )
    ):

        raise RuntimeError(
            (
                "MainContainer changed after "
                "10.3.3 verification."
            )
        )


    if (
        sha256_file(
            FOOTER_FILE
        )
        !=
        footer_contract.get(
            "source_sha256"
        )
    ):

        raise RuntimeError(
            (
                "SiteFooter changed after "
                "10.3.4 verification."
            )
        )


    # ========================================================
    # Stage 10.3.5
    # ========================================================

    existing_typography_contract = (
        optional_json(
            TYPOGRAPHY_CONTRACT_FILE
        )
    )


    globals_before_sha = (
        sha256_file(
            GLOBALS_FILE
        )
    )


    if (
        existing_typography_contract
        and
        globals_before_sha
        ==
        existing_typography_contract.get(
            "globals_after_sha256"
        )
    ):

        print(
            "\n10.3.5 already built; "
            "keeping verified typography source."
        )

        typography_contract = (
            existing_typography_contract
        )

    else:

        expected_globals_sha = (
            footer_contract
            .get(
                "protected_state",
                {}
            )
            .get(
                "globals_css_sha256"
            )
        )


        if (
            globals_before_sha
            !=
            expected_globals_sha
        ):

            raise RuntimeError(
                (
                    "globals.css changed after "
                    "10.3.4 verification."
                )
            )


        globals_source = (
            GLOBALS_FILE.read_text(
                encoding="utf-8"
            )
        )


        updated_globals = (
            append_typography(
                globals_source
            )
        )


        save_text_atomic(
            GLOBALS_FILE,
            updated_globals,
        )


        globals_after_sha = (
            sha256_file(
                GLOBALS_FILE
            )
        )


        typography_contract = {
            "stage":
                "10.3.5",

            "version":
                "1.0.0",

            "name":
                "TYPOGRAPHY_LAYOUT",

            "status":
                "LOCKED",

            "source":
                relative(
                    GLOBALS_FILE
                ),

            "policy": {
                "minimum_document_width_px":
                    320,

                "minimum_body_height":
                    "100vh",

                "page_background":
                    "#f8fafc",

                "default_text":
                    "#0f172a",

                "font_smoothing":
                    True,

                "balanced_headings":
                    True,

                "pretty_paragraph_wrapping":
                    True,

                "selection_style":
                    True,
            },

            "responsibility": {
                "global_visual_baseline":
                    True,

                "feature_page_styles":
                    False,

                "component_specific_styles":
                    False,

                "mobile_navigation":
                    False,

                "data_fetching":
                    False,

                "prediction_logic":
                    False,
            },

            "globals_before_sha256":
                globals_before_sha,

            "globals_after_sha256":
                globals_after_sha,

            "protected_state": {
                "layout_sha256":
                    sha256_file(
                        LAYOUT_FILE
                    ),

                "header_before_10_3_6_sha256":
                    sha256_file(
                        HEADER_FILE
                    ),

                "main_sha256":
                    sha256_file(
                        MAIN_FILE
                    ),

                "footer_sha256":
                    sha256_file(
                        FOOTER_FILE
                    ),

                "route_page_identity":
                    route_identity,
            },

            "dependency_identity": {
                relative(
                    PREVIOUS_VERIFICATION_FILE
                ):
                    identity(
                        PREVIOUS_VERIFICATION_FILE
                    ),

                relative(
                    MAIN_CONTRACT_FILE
                ):
                    identity(
                        MAIN_CONTRACT_FILE
                    ),

                relative(
                    FOOTER_CONTRACT_FILE
                ):
                    identity(
                        FOOTER_CONTRACT_FILE
                    ),
            },

            "promotion": {
                "stage10_3_5_complete":
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
            TYPOGRAPHY_CONTRACT_FILE,
            typography_contract,
        )


    verify_route_pages(
        route_identity
    )


    # ========================================================
    # Stage 10.3.6
    # ========================================================

    existing_mobile_contract = (
        optional_json(
            MOBILE_NAV_CONTRACT_FILE
        )
    )


    current_header_sha = (
        sha256_file(
            HEADER_FILE
        )
    )


    mobile_already_built = (
        existing_mobile_contract
        is not None
        and
        current_header_sha
        ==
        existing_mobile_contract.get(
            "header_after_sha256"
        )
        and
        MOBILE_NAV_FILE.exists()
        and
        sha256_file(
            MOBILE_NAV_FILE
        )
        ==
        existing_mobile_contract.get(
            "mobile_navigation_sha256"
        )
    )


    if mobile_already_built:

        print(
            "\n10.3.6 already built; "
            "keeping verified mobile navigation."
        )

        mobile_contract = (
            existing_mobile_contract
        )

    else:

        if (
            current_header_sha
            !=
            header_contract.get(
                "source_sha256"
            )
        ):

            raise RuntimeError(
                (
                    "SiteHeader changed after "
                    "10.3.2 verification and does "
                    "not match an existing "
                    "10.3.6 build."
                )
            )


        header_before_sha = (
            current_header_sha
        )


        save_text_atomic(
            MOBILE_NAV_FILE,
            MOBILE_NAV_SOURCE,
        )


        header_source = (
            HEADER_FILE.read_text(
                encoding="utf-8"
            )
        )


        updated_header = (
            patch_desktop_navigation(
                header_source
            )
        )


        save_text_atomic(
            HEADER_FILE,
            updated_header,
        )


        header_after_sha = (
            sha256_file(
                HEADER_FILE
            )
        )


        mobile_contract = {
            "stage":
                "10.3.6",

            "version":
                "1.0.0",

            "name":
                "MOBILE_NAVIGATION",

            "status":
                "LOCKED",

            "source":
                relative(
                    MOBILE_NAV_FILE
                ),

            "header_source":
                relative(
                    HEADER_FILE
                ),

            "component":
                "MobileNavigation",

            "implementation": {
                "server_component":
                    True,

                "next_link":
                    True,

                "javascript_menu_state":
                    False,

                "hamburger_required":
                    False,

                "reason":
                    (
                        "Only one valid static "
                        "navigation destination "
                        "currently exists."
                    ),

                "mobile_breakpoint":
                    "sm",

                "mobile_visibility":
                    "sm:hidden",

                "desktop_navigation_visibility":
                    "hidden sm:block",
            },

            "navigation": {
                "aria_label":
                    "Mobile navigation",

                "links": [
                    {
                        "label":
                            "Upcoming",

                        "href":
                            "/",
                    }
                ],

                "invented_matches_index":
                    False,

                "invented_teams_index":
                    False,
            },

            "responsibility": {
                "presentation_only":
                    True,

                "api_access":
                    False,

                "provider_access":
                    False,

                "artifact_access":
                    False,

                "prediction_logic":
                    False,
            },

            "header_before_sha256":
                header_before_sha,

            "header_after_sha256":
                header_after_sha,

            "mobile_navigation_sha256":
                sha256_file(
                    MOBILE_NAV_FILE
                ),

            "protected_state": {
                "layout_sha256":
                    sha256_file(
                        LAYOUT_FILE
                    ),

                "globals_sha256":
                    sha256_file(
                        GLOBALS_FILE
                    ),

                "main_sha256":
                    sha256_file(
                        MAIN_FILE
                    ),

                "footer_sha256":
                    sha256_file(
                        FOOTER_FILE
                    ),

                "route_page_identity":
                    route_identity,
            },

            "dependency_identity": {
                relative(
                    PREVIOUS_VERIFICATION_FILE
                ):
                    identity(
                        PREVIOUS_VERIFICATION_FILE
                    ),

                relative(
                    HEADER_CONTRACT_FILE
                ):
                    identity(
                        HEADER_CONTRACT_FILE
                    ),

                relative(
                    ROUTE_ARCHITECTURE_FILE
                ):
                    identity(
                        ROUTE_ARCHITECTURE_FILE
                    ),

                relative(
                    TYPOGRAPHY_CONTRACT_FILE
                ):
                    identity(
                        TYPOGRAPHY_CONTRACT_FILE
                    ),
            },

            "promotion": {
                "stage10_3_6_complete":
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
            MOBILE_NAV_CONTRACT_FILE,
            mobile_contract,
        )


    verify_route_pages(
        route_identity
    )


    if (
        sha256_file(
            LAYOUT_FILE
        )
        !=
        typography_contract[
            "protected_state"
        ][
            "layout_sha256"
        ]
    ):

        raise RuntimeError(
            (
                "layout.tsx changed during "
                "10.3.5/10.3.6."
            )
        )


    if (
        sha256_file(
            MAIN_FILE
        )
        !=
        main_contract.get(
            "source_sha256"
        )
    ):

        raise RuntimeError(
            (
                "MainContainer changed during "
                "10.3.5/10.3.6."
            )
        )


    if (
        sha256_file(
            FOOTER_FILE
        )
        !=
        footer_contract.get(
            "source_sha256"
        )
    ):

        raise RuntimeError(
            (
                "SiteFooter changed during "
                "10.3.5/10.3.6."
            )
        )


    print()

    print(
        "Typography / layout:"
    )

    print(
        f"  {relative(GLOBALS_FILE)}"
    )


    print(
        "Mobile navigation:"
    )

    print(
        f"  {relative(MOBILE_NAV_FILE)}"
    )


    print(
        "Header integration:"
    )

    print(
        f"  {relative(HEADER_FILE)}"
    )


    print()

    print("=" * 72)

    print(
        "STAGE 10.3.5 TYPOGRAPHY / LAYOUT: BUILT"
    )

    print(
        "STAGE 10.3.6 MOBILE NAVIGATION: BUILT"
    )

    print(
        "STAGE 10 IS NOT YET PROMOTED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
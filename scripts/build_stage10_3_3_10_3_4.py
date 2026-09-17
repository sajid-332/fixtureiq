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
    / "stage10_3_1_10_3_2_verification.json"
)

LAYOUT_CONTRACT_FILE = (
    DOCS
    / "frontend_global_layout_contract.json"
)

HEADER_CONTRACT_FILE = (
    DOCS
    / "frontend_header_navigation_contract.json"
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

MAIN_CONTAINER_FILE = (
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


MAIN_CONTRACT_FILE = (
    DOCS
    / "frontend_main_container_contract.json"
)

FOOTER_CONTRACT_FILE = (
    DOCS
    / "frontend_footer_contract.json"
)


MAIN_IMPORT = (
    'import { MainContainer } '
    'from "../components/shell/main-container";'
)

FOOTER_IMPORT = (
    'import { SiteFooter } '
    'from "../components/shell/site-footer";'
)


MAIN_CONTAINER_SOURCE = '''import type {
  ReactNode,
} from "react";


type MainContainerProps =
  Readonly<{
    children:
      ReactNode;
  }>;


export function MainContainer({
  children,
}: MainContainerProps) {
  return (
    <main
      id="main-content"
      className="
        mx-auto w-full max-w-7xl
        px-4 py-8
        sm:px-6 sm:py-10
        lg:px-8 lg:py-12
      "
      data-fixtureiq-shell="main"
    >
      {children}
    </main>
  );
}
'''


FOOTER_SOURCE = '''export function SiteFooter() {
  return (
    <footer
      className="
        border-t border-slate-200
        bg-white
      "
      data-fixtureiq-shell="footer"
    >
      <div
        className="
          mx-auto flex w-full max-w-7xl
          flex-col gap-3 px-4 py-6
          sm:px-6
          md:flex-row
          md:items-center
          md:justify-between
          lg:px-8
        "
      >
        <div>
          <p
            className="
              text-sm font-semibold
              text-slate-900
            "
          >
            FixtureIQ
          </p>

          <p
            className="
              mt-1 text-sm
              text-slate-500
            "
          >
            Premier League match intelligence
          </p>
        </div>

        <p
          className="
            max-w-xl text-sm
            leading-6 text-slate-500
            md:text-right
          "
        >
          Predictions are estimates,
          not guaranteed outcomes.
        </p>
      </div>
    </footer>
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


def verify_route_pages(
    expected: dict,
) -> None:

    current = (
        current_route_page_identity()
    )

    if current != expected:

        raise RuntimeError(
            (
                "Route page identity changed. "
                "10.3.3/10.3.4 must not "
                "modify feature pages."
            )
        )


def insert_import_after_header(
    source: str,
    import_line: str,
) -> str:

    if import_line in source:

        return source

    pattern = re.compile(
        (
            r'(^\s*import\s+\{\s*SiteHeader\s*\}\s+'
            r'from\s+["\']'
            r'\.\.\/components\/shell\/site-header'
            r'["\'];?\s*$)'
        ),
        re.MULTILINE,
    )

    match = pattern.search(
        source
    )

    if match is None:

        raise RuntimeError(
            (
                "Verified SiteHeader import "
                "could not be located safely."
            )
        )

    return (
        source[
            :match.end()
        ]
        +
        "\n"
        +
        import_line
        +
        source[
            match.end():
        ]
    )


def patch_main_container(
    source: str,
) -> str:

    updated = insert_import_after_header(
        source,
        MAIN_IMPORT,
    )

    if (
        "<MainContainer>"
        in
        updated
    ):

        return updated

    pattern = re.compile(
        (
            r'(?P<header>'
            r'<SiteHeader\s*/>'
            r')'
            r'(?P<space>\s*)'
            r'\{children\}'
        ),
        re.MULTILINE,
    )

    match = pattern.search(
        updated
    )

    if match is None:

        raise RuntimeError(
            (
                "Expected verified shell sequence "
                "<SiteHeader /> + {children} "
                "was not found."
            )
        )

    replacement = (
        "<SiteHeader />\n"
        "        <MainContainer>\n"
        "          {children}\n"
        "        </MainContainer>"
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
            "<MainContainer>"
        )
        !=
        1
    ):

        raise RuntimeError(
            (
                "Root layout must render exactly "
                "one MainContainer."
            )
        )

    return updated


def patch_footer(
    source: str,
) -> str:

    updated = insert_import_after_header(
        source,
        FOOTER_IMPORT,
    )

    if (
        "<SiteFooter />"
        in
        updated
    ):

        return updated

    pattern = re.compile(
        r"</MainContainer>"
    )

    match = pattern.search(
        updated
    )

    if match is None:

        raise RuntimeError(
            (
                "MainContainer must exist before "
                "adding SiteFooter."
            )
        )

    replacement = (
        "</MainContainer>\n"
        "        <SiteFooter />"
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
            "<SiteFooter />"
        )
        !=
        1
    ):

        raise RuntimeError(
            (
                "Root layout must render exactly "
                "one SiteFooter."
            )
        )

    return updated


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.3.3 + 10.3.4"
    )

    print(
        "MAIN CONTAINER + FOOTER BUILD"
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
                "10.3.1-10.3.2 verification "
                "is not PASS."
            )
        )


    if (
        previous.get(
            "stage10_ready_for_10_3_3"
        )
        is not True
    ):

        raise RuntimeError(
            (
                "10.3.2 did not authorize "
                "10.3.3."
            )
        )


    if (
        layout_contract.get(
            "status"
        )
        !=
        "LOCKED"
    ):

        raise RuntimeError(
            "10.3.1 layout contract is not LOCKED."
        )


    if (
        header_contract.get(
            "status"
        )
        !=
        "LOCKED"
    ):

        raise RuntimeError(
            "10.3.2 header contract is not LOCKED."
        )


    if (
        route_architecture.get(
            "status"
        )
        !=
        "LOCKED"
    ):

        raise RuntimeError(
            "Route architecture is not LOCKED."
        )


    required_existing = [
        LAYOUT_FILE,
        GLOBALS_FILE,
        HEADER_FILE,
    ]


    for path in required_existing:

        if not path.exists():

            raise RuntimeError(
                f"Missing shell file: {path}"
            )


    current_layout_sha = (
        sha256_file(
            LAYOUT_FILE
        )
    )


    if (
        current_layout_sha
        !=
        layout_contract.get(
            "layout_after_sha256"
        )
    ):

        raise RuntimeError(
            (
                "Current layout.tsx no longer "
                "matches verified Stage 10.3.1 "
                "starting state."
            )
        )


    if (
        sha256_file(
            HEADER_FILE
        )
        !=
        header_contract.get(
            "source_sha256"
        )
    ):

        raise RuntimeError(
            (
                "SiteHeader changed after "
                "Stage 10.3.2 verification."
            )
        )


    protected_pages = (
        layout_contract.get(
            "protected_route_page_identity",
            {}
        )
    )


    if not isinstance(
        protected_pages,
        dict,
    ):

        raise RuntimeError(
            "Protected route-page identity missing."
        )


    verify_route_pages(
        protected_pages
    )


    globals_before_sha = (
        sha256_file(
            GLOBALS_FILE
        )
    )

    header_before_sha = (
        sha256_file(
            HEADER_FILE
        )
    )

    layout_before_main_sha = (
        sha256_file(
            LAYOUT_FILE
        )
    )


    # ========================================================
    # Stage 10.3.3
    # ========================================================

    save_text_atomic(
        MAIN_CONTAINER_FILE,
        MAIN_CONTAINER_SOURCE,
    )


    layout_source = (
        LAYOUT_FILE.read_text(
            encoding="utf-8"
        )
    )


    layout_with_main = (
        patch_main_container(
            layout_source
        )
    )


    save_text_atomic(
        LAYOUT_FILE,
        layout_with_main,
    )


    layout_after_main_sha = (
        sha256_file(
            LAYOUT_FILE
        )
    )


    verify_route_pages(
        protected_pages
    )


    main_contract = {
        "stage":
            "10.3.3",

        "version":
            "1.0.0",

        "name":
            "MAIN_CONTAINER",

        "status":
            "LOCKED",

        "source":
            relative(
                MAIN_CONTAINER_FILE
            ),

        "component":
            "MainContainer",

        "semantic_element":
            "main",

        "main_id":
            "main-content",

        "container": {
            "full_width":
                True,

            "centered":
                True,

            "max_width":
                "max-w-7xl",

            "responsive_horizontal_padding":
                True,

            "responsive_vertical_padding":
                True,
        },

        "responsibility": {
            "wraps_route_children":
                True,

            "feature_page_content":
                False,

            "data_fetching":
                False,

            "api_access":
                False,

            "prediction_logic":
                False,

            "footer":
                False,

            "typography_system":
                False,

            "mobile_navigation":
                False,
        },

        "layout_transition": {
            "before_sha256":
                layout_before_main_sha,

            "after_main_sha256":
                layout_after_main_sha,
        },

        "source_sha256":
            sha256_file(
                MAIN_CONTAINER_FILE
            ),

        "protected_state": {
            "globals_css_sha256":
                globals_before_sha,

            "site_header_sha256":
                header_before_sha,

            "route_page_identity":
                protected_pages,
        },

        "dependency_identity": {
            relative(
                PREVIOUS_VERIFICATION_FILE
            ):
                identity(
                    PREVIOUS_VERIFICATION_FILE
                ),

            relative(
                LAYOUT_CONTRACT_FILE
            ):
                identity(
                    LAYOUT_CONTRACT_FILE
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
        },

        "promotion": {
            "stage10_3_3_complete":
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
        MAIN_CONTRACT_FILE,
        main_contract,
    )


    # ========================================================
    # Stage 10.3.4
    # ========================================================

    layout_before_footer_sha = (
        sha256_file(
            LAYOUT_FILE
        )
    )


    if (
        layout_before_footer_sha
        !=
        layout_after_main_sha
    ):

        raise RuntimeError(
            (
                "Unexpected layout mutation "
                "between 10.3.3 and 10.3.4."
            )
        )


    save_text_atomic(
        FOOTER_FILE,
        FOOTER_SOURCE,
    )


    layout_source = (
        LAYOUT_FILE.read_text(
            encoding="utf-8"
        )
    )


    layout_with_footer = (
        patch_footer(
            layout_source
        )
    )


    save_text_atomic(
        LAYOUT_FILE,
        layout_with_footer,
    )


    layout_after_footer_sha = (
        sha256_file(
            LAYOUT_FILE
        )
    )


    verify_route_pages(
        protected_pages
    )


    if (
        sha256_file(
            GLOBALS_FILE
        )
        !=
        globals_before_sha
    ):

        raise RuntimeError(
            (
                "globals.css changed during "
                "10.3.3/10.3.4."
            )
        )


    if (
        sha256_file(
            HEADER_FILE
        )
        !=
        header_before_sha
    ):

        raise RuntimeError(
            (
                "SiteHeader changed during "
                "10.3.3/10.3.4."
            )
        )


    footer_contract = {
        "stage":
            "10.3.4",

        "version":
            "1.0.0",

        "name":
            "SITE_FOOTER",

        "status":
            "LOCKED",

        "source":
            relative(
                FOOTER_FILE
            ),

        "component":
            "SiteFooter",

        "semantic_element":
            "footer",

        "content": {
            "brand":
                "FixtureIQ",

            "product_context":
                "Premier League match intelligence",

            "disclaimer":
                (
                    "Predictions are estimates, "
                    "not guaranteed outcomes."
                ),

            "invented_navigation":
                False,
        },

        "responsibility": {
            "global_shell_footer":
                True,

            "data_fetching":
                False,

            "api_access":
                False,

            "prediction_logic":
                False,

            "provider_access":
                False,

            "artifact_access":
                False,

            "mobile_navigation":
                False,
        },

        "layout_transition": {
            "before_footer_sha256":
                layout_before_footer_sha,

            "after_footer_sha256":
                layout_after_footer_sha,
        },

        "source_sha256":
            sha256_file(
                FOOTER_FILE
            ),

        "protected_state": {
            "globals_css_sha256":
                globals_before_sha,

            "site_header_sha256":
                header_before_sha,

            "route_page_identity":
                protected_pages,
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
        },

        "promotion": {
            "stage10_3_4_complete":
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
        FOOTER_CONTRACT_FILE,
        footer_contract,
    )


    print()

    print(
        "Main container:"
    )

    print(
        f"  {relative(MAIN_CONTAINER_FILE)}"
    )


    print(
        "Footer:"
    )

    print(
        f"  {relative(FOOTER_FILE)}"
    )


    print()

    print(
        "Final shell:"
    )

    print(
        "  SiteHeader"
    )

    print(
        "  MainContainer"
    )

    print(
        "  SiteFooter"
    )


    print()

    print("=" * 72)

    print(
        "STAGE 10.3.3 MAIN CONTAINER: BUILT"
    )

    print(
        "STAGE 10.3.4 FOOTER: BUILT"
    )

    print(
        "STAGE 10 IS NOT YET PROMOTED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
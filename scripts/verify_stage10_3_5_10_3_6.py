from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
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


PREVIOUS_FILE = (
    FRONTEND_DATA
    / "stage10_3_3_10_3_4_verification.json"
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

TYPOGRAPHY_CONTRACT_FILE = (
    DOCS
    / "frontend_typography_layout_contract.json"
)

MOBILE_CONTRACT_FILE = (
    DOCS
    / "frontend_mobile_navigation_contract.json"
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

MOBILE_FILE = (
    FRONTEND
    / "components"
    / "shell"
    / "mobile-navigation.tsx"
)


OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_3_5_10_3_6_verification.json"
)


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


def sha256_file(
    path: Path,
) -> str:

    digest = hashlib.sha256()

    with path.open("rb") as file:

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


def resolve_project_path(
    value: str,
) -> Path:

    raw = Path(value)

    resolved = (
        raw.resolve()
        if raw.is_absolute()
        else
        (
            ROOT
            / raw
        ).resolve()
    )

    resolved.relative_to(
        ROOT.resolve()
    )

    return resolved


def save_json_atomic(
    path: Path,
    payload: dict,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temporary.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=2,
        )

        file.write("\n")

    temporary.replace(path)


def check(
    label: str,
    condition,
    failures: list[str],
) -> bool:

    passed = bool(
        condition
    )

    print(
        f"{label}: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    if not passed:

        failures.append(
            label
        )

    return passed


def verify_dependencies(
    payload: dict,
    label: str,
    failures: list[str],
) -> None:

    identities = payload.get(
        "dependency_identity",
        {}
    )

    check(
        f"{label} dependency identity exists",
        isinstance(
            identities,
            dict,
        )
        and
        bool(
            identities
        ),
        failures,
    )


    if not isinstance(
        identities,
        dict,
    ):

        return


    for path_text, declared in (
        identities.items()
    ):

        try:

            expected = (
                declared.get(
                    "sha256",
                    "",
                )
                if isinstance(
                    declared,
                    dict,
                )
                else ""
            )

            path = resolve_project_path(
                path_text
            )

            current = (
                bool(
                    expected
                )
                and
                path.exists()
                and
                sha256_file(
                    path
                )
                ==
                expected
            )

        except Exception:

            current = False


        check(
            (
                f"{label}: "
                f"{Path(path_text).name} current"
            ),
            current,
            failures,
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


def run_typescript_check() -> tuple[
    bool,
    str,
]:

    npm = (
        shutil.which(
            "npm.cmd"
        )
        or
        shutil.which(
            "npm"
        )
    )


    if npm is None:

        return (
            False,
            "npm executable not found.",
        )


    result = subprocess.run(
        [
            npm,
            "exec",
            "--",
            "tsc",
            "--noEmit",
        ],
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        check=False,
    )


    output = (
        (result.stdout or "")
        +
        (result.stderr or "")
    ).strip()


    return (
        result.returncode == 0,
        output,
    )


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.3.5 + 10.3.6"
    )

    print(
        "TYPOGRAPHY / LAYOUT + MOBILE NAVIGATION VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        PREVIOUS_FILE,
        HEADER_CONTRACT_FILE,
        MAIN_CONTRACT_FILE,
        FOOTER_CONTRACT_FILE,
        TYPOGRAPHY_CONTRACT_FILE,
        MOBILE_CONTRACT_FILE,
        LAYOUT_FILE,
        GLOBALS_FILE,
        HEADER_FILE,
        MAIN_FILE,
        FOOTER_FILE,
        MOBILE_FILE,
    ]


    print(
        "\n1. REQUIRED ARTIFACTS"
    )


    for path in required:

        check(
            relative(path),
            path.exists(),
            failures,
        )


    if failures:

        sys.exit(1)


    previous = load_json(
        PREVIOUS_FILE
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

    typography = load_json(
        TYPOGRAPHY_CONTRACT_FILE
    )

    mobile = load_json(
        MOBILE_CONTRACT_FILE
    )


    layout_source = (
        LAYOUT_FILE.read_text(
            encoding="utf-8"
        )
    )

    globals_source = (
        GLOBALS_FILE.read_text(
            encoding="utf-8"
        )
    )

    header_source = (
        HEADER_FILE.read_text(
            encoding="utf-8"
        )
    )

    main_source = (
        MAIN_FILE.read_text(
            encoding="utf-8"
        )
    )

    footer_source = (
        FOOTER_FILE.read_text(
            encoding="utf-8"
        )
    )

    mobile_source = (
        MOBILE_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. STAGE 10.3.3 / 10.3.4 FOUNDATION"
    )


    check(
        "Previous verification PASS",
        previous.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )


    check(
        "10.3.3 complete",
        previous.get(
            "stage_10_3_3_complete"
        )
        is True,
        failures,
    )


    check(
        "10.3.4 complete",
        previous.get(
            "stage_10_3_4_complete"
        )
        is True,
        failures,
    )


    check(
        "10.3.4 authorized 10.3.5",
        previous.get(
            "stage10_ready_for_10_3_5"
        )
        is True,
        failures,
    )


    print(
        "\n3. STAGE 10.3.5 CONTRACT"
    )


    check(
        "Typography contract stage exact",
        typography.get(
            "stage"
        )
        ==
        "10.3.5",
        failures,
    )


    check(
        "Typography contract LOCKED",
        typography.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    policy = typography.get(
        "policy",
        {}
    )


    check(
        "Minimum document width = 320",
        policy.get(
            "minimum_document_width_px"
        )
        ==
        320,
        failures,
    )


    check(
        "Body minimum height = 100vh",
        policy.get(
            "minimum_body_height"
        )
        ==
        "100vh",
        failures,
    )


    check(
        "Font smoothing locked",
        policy.get(
            "font_smoothing"
        )
        is True,
        failures,
    )


    check(
        "Balanced headings locked",
        policy.get(
            "balanced_headings"
        )
        is True,
        failures,
    )


    check(
        "Pretty paragraph wrapping locked",
        policy.get(
            "pretty_paragraph_wrapping"
        )
        is True,
        failures,
    )


    print(
        "\n4. GLOBAL TYPOGRAPHY SOURCE"
    )


    check(
        "10.3.5 CSS marker present once",
        globals_source.count(
            (
                "FixtureIQ Stage 10.3.5 "
                "Typography / Layout"
            )
        )
        ==
        1,
        failures,
    )


    check(
        "HTML minimum width present",
        "min-width: 320px"
        in
        globals_source,
        failures,
    )


    check(
        "Body minimum height present",
        "min-height: 100vh"
        in
        globals_source,
        failures,
    )


    check(
        "Body foreground present",
        "color: #0f172a"
        in
        globals_source,
        failures,
    )


    check(
        "Font smoothing present",
        "-webkit-font-smoothing"
        in
        globals_source,
        failures,
    )


    check(
        "Heading balance present",
        "text-wrap: balance"
        in
        globals_source,
        failures,
    )


    check(
        "Paragraph pretty wrap present",
        "text-wrap: pretty"
        in
        globals_source,
        failures,
    )


    check(
        "Selection style present",
        "::selection"
        in
        globals_source,
        failures,
    )


    check(
        "globals.css SHA current",
        typography.get(
            "globals_after_sha256"
        )
        ==
        sha256_file(
            GLOBALS_FILE
        ),
        failures,
    )


    print(
        "\n5. STAGE 10.3.6 CONTRACT"
    )


    check(
        "Mobile contract stage exact",
        mobile.get(
            "stage"
        )
        ==
        "10.3.6",
        failures,
    )


    check(
        "Mobile contract LOCKED",
        mobile.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    implementation = mobile.get(
        "implementation",
        {}
    )


    check(
        "Mobile navigation is server component",
        implementation.get(
            "server_component"
        )
        is True,
        failures,
    )


    check(
        "No unnecessary JS menu state",
        implementation.get(
            "javascript_menu_state"
        )
        is False,
        failures,
    )


    check(
        "Hamburger not required",
        implementation.get(
            "hamburger_required"
        )
        is False,
        failures,
    )


    check(
        "Mobile breakpoint exact",
        implementation.get(
            "mobile_breakpoint"
        )
        ==
        "sm",
        failures,
    )


    print(
        "\n6. MOBILE NAVIGATION SOURCE"
    )


    check(
        "Next Link imported",
        'from "next/link"'
        in
        mobile_source,
        failures,
    )


    check(
        "Mobile nav semantic element present",
        "<nav"
        in
        mobile_source
        and
        "</nav>"
        in
        mobile_source,
        failures,
    )


    check(
        "Mobile navigation aria-label present",
        (
            'aria-label="Mobile navigation"'
            in
            mobile_source
        ),
        failures,
    )


    check(
        "Mobile-only visibility present",
        "sm:hidden"
        in
        mobile_source,
        failures,
    )


    check(
        "Upcoming link present",
        "Upcoming"
        in
        mobile_source,
        failures,
    )


    hrefs = re.findall(
        (
            r'href\s*=\s*'
            r'["\']([^"\']+)["\']'
        ),
        mobile_source,
    )


    check(
        "Mobile navigation links root only",
        bool(
            hrefs
        )
        and
        set(
            hrefs
        )
        ==
        {"/"},
        failures,
    )


    check(
        "No invented matches index",
        'href="/matches"'
        not in
        mobile_source,
        failures,
    )


    check(
        "No invented teams index",
        'href="/teams"'
        not in
        mobile_source,
        failures,
    )


    check(
        "Mobile navigation has no client directive",
        '"use client"'
        not in
        mobile_source
        and
        "'use client'"
        not in
        mobile_source,
        failures,
    )


    print(
        "\n7. HEADER MOBILE INTEGRATION"
    )


    check(
        "MobileNavigation import present",
        "mobile-navigation"
        in
        header_source,
        failures,
    )


    check(
        "Exactly one MobileNavigation rendered",
        header_source.count(
            "<MobileNavigation />"
        )
        ==
        1,
        failures,
    )


    check(
        "Desktop primary nav still exists",
        (
            'aria-label="Primary navigation"'
            in
            header_source
        ),
        failures,
    )


    check(
        "Desktop primary nav hidden on mobile",
        re.search(
            (
                r'aria-label="Primary navigation"'
                r'[\s\S]{0,150}'
                r'className="hidden sm:block"'
            ),
            header_source,
        )
        is not None,
        failures,
    )


    check(
        "Header transition begins at 10.3.2 SHA",
        mobile.get(
            "header_before_sha256"
        )
        ==
        header_contract.get(
            "source_sha256"
        ),
        failures,
    )


    check(
        "Current header equals 10.3.6 output",
        mobile.get(
            "header_after_sha256"
        )
        ==
        sha256_file(
            HEADER_FILE
        ),
        failures,
    )


    check(
        "Mobile component SHA current",
        mobile.get(
            "mobile_navigation_sha256"
        )
        ==
        sha256_file(
            MOBILE_FILE
        ),
        failures,
    )


    print(
        "\n8. PREVIOUS SHELL PRESERVATION"
    )


    typography_protected = (
        typography.get(
            "protected_state",
            {}
        )
    )

    mobile_protected = (
        mobile.get(
            "protected_state",
            {}
        )
    )


    check(
        "layout.tsx preserved",
        (
            typography_protected.get(
                "layout_sha256"
            )
            ==
            sha256_file(
                LAYOUT_FILE
            )
            and
            mobile_protected.get(
                "layout_sha256"
            )
            ==
            sha256_file(
                LAYOUT_FILE
            )
        ),
        failures,
    )


    check(
        "MainContainer preserved",
        (
            typography_protected.get(
                "main_sha256"
            )
            ==
            sha256_file(
                MAIN_FILE
            )
            and
            mobile_protected.get(
                "main_sha256"
            )
            ==
            sha256_file(
                MAIN_FILE
            )
            and
            main_contract.get(
                "source_sha256"
            )
            ==
            sha256_file(
                MAIN_FILE
            )
        ),
        failures,
    )


    check(
        "SiteFooter preserved",
        (
            typography_protected.get(
                "footer_sha256"
            )
            ==
            sha256_file(
                FOOTER_FILE
            )
            and
            mobile_protected.get(
                "footer_sha256"
            )
            ==
            sha256_file(
                FOOTER_FILE
            )
            and
            footer_contract.get(
                "source_sha256"
            )
            ==
            sha256_file(
                FOOTER_FILE
            )
        ),
        failures,
    )


    protected_pages = (
        mobile_protected.get(
            "route_page_identity",
            {}
        )
    )


    check(
        "Route pages preserved",
        isinstance(
            protected_pages,
            dict,
        )
        and
        bool(
            protected_pages
        )
        and
        protected_pages
        ==
        current_route_pages(),
        failures,
    )


    print(
        "\n9. PRESENTATION-ONLY BOUNDARY"
    )


    combined_source = "\n".join(
        [
            layout_source,
            globals_source,
            header_source,
            main_source,
            footer_source,
            mobile_source,
        ]
    )


    check(
        "No shell fetch",
        re.search(
            r"\bfetch\s*\(",
            combined_source,
        )
        is None,
        failures,
    )


    check(
        "No API client import",
        "lib/api"
        not in
        combined_source,
        failures,
    )


    for term in [
        "data/processed",
        "data\\processed",
        "data/historical",
        "data\\historical",
        ".joblib",
        "football-data.org",
        "api-football",
        "api-sports",
    ]:

        check(
            f"Shell excludes: {term}",
            term.lower()
            not in
            combined_source.lower(),
            failures,
        )


    print(
        "\n10. DEPENDENCY FRESHNESS"
    )


    verify_dependencies(
        typography,
        "10.3.5",
        failures,
    )


    verify_dependencies(
        mobile,
        "10.3.6",
        failures,
    )


    print(
        "\n11. TYPESCRIPT COMPILER"
    )


    compiler_ok, compiler_output = (
        run_typescript_check()
    )


    check(
        "TypeScript --noEmit",
        compiler_ok,
        failures,
    )


    if (
        not compiler_ok
        and
        compiler_output
    ):

        print()

        print(
            compiler_output
        )


    print(
        "\n12. NO PREMATURE PROMOTION"
    )


    typography_promotion = (
        typography.get(
            "promotion",
            {}
        )
    )

    mobile_promotion = (
        mobile.get(
            "promotion",
            {}
        )
    )


    check(
        "10.3.5 did not self-promote",
        typography_promotion.get(
            "stage10_3_5_complete"
        )
        is False,
        failures,
    )


    check(
        "10.3.6 did not self-promote",
        mobile_promotion.get(
            "stage10_3_6_complete"
        )
        is False,
        failures,
    )


    check(
        "Stage 10.3 remains incomplete",
        (
            typography_promotion.get(
                "stage10_3_complete"
            )
            is False
            and
            mobile_promotion.get(
                "stage10_3_complete"
            )
            is False
        ),
        failures,
    )


    check(
        "Stage 10 remains incomplete",
        (
            typography_promotion.get(
                "stage10_complete"
            )
            is False
            and
            mobile_promotion.get(
                "stage10_complete"
            )
            is False
        ),
        failures,
    )


    print(
        "\n13. SAVE VERIFICATION EVIDENCE"
    )


    passed = (
        len(
            failures
        )
        ==
        0
    )


    if passed:

        evidence = {
            "stage":
                "10.3.5-10.3.6",

            "name":
                (
                    "TYPOGRAPHY_LAYOUT_AND_"
                    "MOBILE_NAVIGATION_VERIFICATION"
                ),

            "status":
                "PASS",

            "stage_10_3_5_complete":
                True,

            "stage_10_3_6_complete":
                True,

            "typography_layout":
                "LOCKED_AND_VERIFIED",

            "mobile_navigation":
                "LOCKED_AND_VERIFIED",

            "mobile_navigation_design": {
                "server_rendered":
                    True,

                "hamburger_menu":
                    False,

                "javascript_state":
                    False,

                "valid_static_route":
                    "/",
            },

            "shell_preservation": {
                "layout":
                    True,

                "main_container":
                    True,

                "footer":
                    True,

                "route_pages":
                    True,
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
            },

            "typescript_compiler":
                "PASS",

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "stage10_ready_for_10_3_7":
                True,

            "stage10_3_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.3.7",

            "failures":
                [],
        }


        save_json_atomic(
            OUTPUT_FILE,
            evidence,
        )


        print(
            relative(
                OUTPUT_FILE
            )
        )


    print(
        "\n"
        +
        "=" * 72
    )


    if passed:

        print(
            "STAGE 10.3.5: PASS"
        )

        print(
            "TYPOGRAPHY / LAYOUT: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.3.6: PASS"
        )

        print(
            "MOBILE NAVIGATION: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.3.7"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.3.5 / 10.3.6: FAIL"
        )

        print()

        print(
            "Failures:"
        )

        for failure in failures:

            print(
                f"  - {failure}"
            )


    print(
        "=" * 72
    )


    sys.exit(
        0
        if passed
        else 1
    )


if __name__ == "__main__":

    main()
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


# ============================================================
# Prior Stage 10.3 verification evidence
# ============================================================

VERIFICATION_10_3_1_2 = (
    FRONTEND_DATA
    / "stage10_3_1_10_3_2_verification.json"
)

VERIFICATION_10_3_3_4 = (
    FRONTEND_DATA
    / "stage10_3_3_10_3_4_verification.json"
)

VERIFICATION_10_3_5_6 = (
    FRONTEND_DATA
    / "stage10_3_5_10_3_6_verification.json"
)


# ============================================================
# Stage 10.3 contracts
# ============================================================

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

TYPOGRAPHY_CONTRACT_FILE = (
    DOCS
    / "frontend_typography_layout_contract.json"
)

MOBILE_CONTRACT_FILE = (
    DOCS
    / "frontend_mobile_navigation_contract.json"
)

ROUTE_ARCHITECTURE_FILE = (
    DOCS
    / "frontend_route_architecture.json"
)


# ============================================================
# Shell source files
# ============================================================

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
    / "stage10_3_final_verification.json"
)


# ============================================================
# Helpers
# ============================================================

def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise RuntimeError(
            f"Missing JSON artifact: {path}"
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
            /
            raw
        ).resolve()
    )

    resolved.relative_to(
        ROOT.resolve()
    )

    return resolved


def identity(
    path: Path,
) -> dict:

    return {
        "sha256":
            sha256_file(path)
    }


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


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.3.7"
    )

    print(
        "FINAL APPLICATION SHELL & NAVIGATION VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        VERIFICATION_10_3_1_2,
        VERIFICATION_10_3_3_4,
        VERIFICATION_10_3_5_6,
        LAYOUT_CONTRACT_FILE,
        HEADER_CONTRACT_FILE,
        MAIN_CONTRACT_FILE,
        FOOTER_CONTRACT_FILE,
        TYPOGRAPHY_CONTRACT_FILE,
        MOBILE_CONTRACT_FILE,
        ROUTE_ARCHITECTURE_FILE,
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

        print(
            "\n"
            +
            "=" * 72
        )

        print(
            "STAGE 10.3.7: FAIL"
        )

        print(
            "STAGE 10.3: INCOMPLETE"
        )

        print(
            "=" * 72
        )

        sys.exit(1)


    # ========================================================
    # Load verification evidence
    # ========================================================

    verification_1_2 = load_json(
        VERIFICATION_10_3_1_2
    )

    verification_3_4 = load_json(
        VERIFICATION_10_3_3_4
    )

    verification_5_6 = load_json(
        VERIFICATION_10_3_5_6
    )


    # ========================================================
    # Load contracts
    # ========================================================

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

    typography_contract = load_json(
        TYPOGRAPHY_CONTRACT_FILE
    )

    mobile_contract = load_json(
        MOBILE_CONTRACT_FILE
    )

    route_architecture = load_json(
        ROUTE_ARCHITECTURE_FILE
    )


    # ========================================================
    # Load sources
    # ========================================================

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


    # ========================================================
    # 2. Substage evidence
    # ========================================================

    print(
        "\n2. STAGE 10.3 SUBSTAGE EVIDENCE"
    )


    evidence_checks = [
        (
            "10.3.1",
            verification_1_2,
            "stage_10_3_1_complete",
        ),
        (
            "10.3.2",
            verification_1_2,
            "stage_10_3_2_complete",
        ),
        (
            "10.3.3",
            verification_3_4,
            "stage_10_3_3_complete",
        ),
        (
            "10.3.4",
            verification_3_4,
            "stage_10_3_4_complete",
        ),
        (
            "10.3.5",
            verification_5_6,
            "stage_10_3_5_complete",
        ),
        (
            "10.3.6",
            verification_5_6,
            "stage_10_3_6_complete",
        ),
    ]


    for (
        stage,
        evidence,
        completion_key,
    ) in evidence_checks:

        check(
            f"{stage} verification PASS",
            evidence.get(
                "status"
            )
            ==
            "PASS",
            failures,
        )

        check(
            f"{stage} completion persisted",
            evidence.get(
                completion_key
            )
            is True,
            failures,
        )


    check(
        "10.3.6 authorized 10.3.7",
        verification_5_6.get(
            "stage10_ready_for_10_3_7"
        )
        is True,
        failures,
    )


    # ========================================================
    # 3. Contract chain
    # ========================================================

    print(
        "\n3. LOCKED CONTRACT CHAIN"
    )


    contracts = [
        (
            "10.3.1",
            layout_contract,
        ),
        (
            "10.3.2",
            header_contract,
        ),
        (
            "10.3.3",
            main_contract,
        ),
        (
            "10.3.4",
            footer_contract,
        ),
        (
            "10.3.5",
            typography_contract,
        ),
        (
            "10.3.6",
            mobile_contract,
        ),
    ]


    for stage, contract in contracts:

        check(
            f"{stage} contract stage exact",
            contract.get(
                "stage"
            )
            ==
            stage,
            failures,
        )

        check(
            f"{stage} contract LOCKED",
            contract.get(
                "status"
            )
            ==
            "LOCKED",
            failures,
        )


    check(
        "Route architecture remains LOCKED",
        route_architecture.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    # ========================================================
    # 4. Final shell structure
    # ========================================================

    print(
        "\n4. FINAL SHELL STRUCTURE"
    )


    check(
        "SiteHeader import present",
        "site-header"
        in
        layout_source,
        failures,
    )


    check(
        "MainContainer import present",
        "main-container"
        in
        layout_source,
        failures,
    )


    check(
        "SiteFooter import present",
        "site-footer"
        in
        layout_source,
        failures,
    )


    check(
        "Exactly one SiteHeader rendered",
        layout_source.count(
            "<SiteHeader />"
        )
        ==
        1,
        failures,
    )


    check(
        "Exactly one MainContainer rendered",
        layout_source.count(
            "<MainContainer>"
        )
        ==
        1
        and
        layout_source.count(
            "</MainContainer>"
        )
        ==
        1,
        failures,
    )


    check(
        "Exactly one SiteFooter rendered",
        layout_source.count(
            "<SiteFooter />"
        )
        ==
        1,
        failures,
    )


    header_position = (
        layout_source.find(
            "<SiteHeader />"
        )
    )

    main_position = (
        layout_source.find(
            "<MainContainer>"
        )
    )

    footer_position = (
        layout_source.find(
            "<SiteFooter />"
        )
    )


    check(
        "Shell order Header -> Main -> Footer",
        (
            header_position
            >=
            0
            and
            main_position
            >
            header_position
            and
            footer_position
            >
            main_position
        ),
        failures,
    )


    check(
        "Route children inside MainContainer",
        re.search(
            (
                r"<MainContainer>"
                r"[\s\S]*?"
                r"\{children\}"
                r"[\s\S]*?"
                r"</MainContainer>"
            ),
            layout_source,
        )
        is not None,
        failures,
    )


    # ========================================================
    # 5. Final source identity
    # ========================================================

    print(
        "\n5. FINAL SOURCE IDENTITY"
    )


    final_layout_sha = (
        footer_contract
        .get(
            "layout_transition",
            {}
        )
        .get(
            "after_footer_sha256"
        )
    )


    check(
        "layout.tsx current",
        final_layout_sha
        ==
        sha256_file(
            LAYOUT_FILE
        ),
        failures,
    )


    check(
        "globals.css current",
        typography_contract.get(
            "globals_after_sha256"
        )
        ==
        sha256_file(
            GLOBALS_FILE
        ),
        failures,
    )


    check(
        "SiteHeader current",
        mobile_contract.get(
            "header_after_sha256"
        )
        ==
        sha256_file(
            HEADER_FILE
        ),
        failures,
    )


    check(
        "MainContainer current",
        main_contract.get(
            "source_sha256"
        )
        ==
        sha256_file(
            MAIN_FILE
        ),
        failures,
    )


    check(
        "SiteFooter current",
        footer_contract.get(
            "source_sha256"
        )
        ==
        sha256_file(
            FOOTER_FILE
        ),
        failures,
    )


    check(
        "MobileNavigation current",
        mobile_contract.get(
            "mobile_navigation_sha256"
        )
        ==
        sha256_file(
            MOBILE_FILE
        ),
        failures,
    )


    # ========================================================
    # 6. Semantic structure
    # ========================================================

    print(
        "\n6. SEMANTIC SHELL ELEMENTS"
    )


    check(
        "Header semantic element",
        "<header"
        in
        header_source
        and
        "</header>"
        in
        header_source,
        failures,
    )


    check(
        "Main semantic element",
        "<main"
        in
        main_source
        and
        "</main>"
        in
        main_source,
        failures,
    )


    check(
        "Main content ID present",
        'id="main-content"'
        in
        main_source,
        failures,
    )


    check(
        "Footer semantic element",
        "<footer"
        in
        footer_source
        and
        "</footer>"
        in
        footer_source,
        failures,
    )


    check(
        "Desktop primary navigation semantic element",
        (
            "<nav"
            in
            header_source
            and
            'aria-label="Primary navigation"'
            in
            header_source
        ),
        failures,
    )


    check(
        "Mobile navigation semantic element",
        (
            "<nav"
            in
            mobile_source
            and
            'aria-label="Mobile navigation"'
            in
            mobile_source
        ),
        failures,
    )


    # ========================================================
    # 7. Navigation integrity
    # ========================================================

    print(
        "\n7. NAVIGATION INTEGRITY"
    )


    header_hrefs = re.findall(
        (
            r'href\s*=\s*'
            r'["\']([^"\']+)["\']'
        ),
        header_source,
    )


    mobile_hrefs = re.findall(
        (
            r'href\s*=\s*'
            r'["\']([^"\']+)["\']'
        ),
        mobile_source,
    )


    check(
        "Header links only valid root route",
        bool(
            header_hrefs
        )
        and
        set(
            header_hrefs
        )
        ==
        {"/"},
        failures,
    )


    check(
        "Mobile links only valid root route",
        bool(
            mobile_hrefs
        )
        and
        set(
            mobile_hrefs
        )
        ==
        {"/"},
        failures,
    )


    check(
        "No invented /matches index",
        (
            'href="/matches"'
            not in
            header_source
            and
            'href="/matches"'
            not in
            mobile_source
        ),
        failures,
    )


    check(
        "No invented /teams index",
        (
            'href="/teams"'
            not in
            header_source
            and
            'href="/teams"'
            not in
            mobile_source
        ),
        failures,
    )


    check(
        "Desktop navigation hidden on mobile",
        re.search(
            (
                r'aria-label="Primary navigation"'
                r'[\s\S]{0,160}'
                r'className="hidden sm:block"'
            ),
            header_source,
        )
        is not None,
        failures,
    )


    check(
        "Mobile navigation hidden at sm+",
        "sm:hidden"
        in
        mobile_source,
        failures,
    )


    check(
        "No unnecessary client navigation state",
        (
            '"use client"'
            not in
            header_source
            and
            "'use client'"
            not in
            header_source
            and
            '"use client"'
            not in
            mobile_source
            and
            "'use client'"
            not in
            mobile_source
        ),
        failures,
    )


    # ========================================================
    # 8. Main container
    # ========================================================

    print(
        "\n8. MAIN CONTAINER"
    )


    for class_name in [
        "mx-auto",
        "w-full",
        "max-w-7xl",
        "px-4",
        "sm:px-6",
        "lg:px-8",
    ]:

        check(
            (
                "Main container class: "
                f"{class_name}"
            ),
            class_name
            in
            main_source,
            failures,
        )


    check(
        "Main container renders children",
        "{children}"
        in
        main_source,
        failures,
    )


    # ========================================================
    # 9. Footer
    # ========================================================

    print(
        "\n9. FOOTER"
    )


    check(
        "FixtureIQ footer brand present",
        "FixtureIQ"
        in
        footer_source,
        failures,
    )


    check(
        "Premier League product context present",
        (
            "Premier League match intelligence"
            in
            footer_source
        ),
        failures,
    )


    check(
        "Prediction disclaimer present",
        (
            "Predictions are estimates"
            in
            footer_source
            and
            "not guaranteed outcomes"
            in
            footer_source
        ),
        failures,
    )


    # ========================================================
    # 10. Typography/layout baseline
    # ========================================================

    print(
        "\n10. TYPOGRAPHY / LAYOUT BASELINE"
    )


    check(
        "Minimum 320px document width",
        "min-width: 320px"
        in
        globals_source,
        failures,
    )


    check(
        "Minimum 100vh body height",
        "min-height: 100vh"
        in
        globals_source,
        failures,
    )


    check(
        "Global foreground established",
        "color: #0f172a"
        in
        globals_source,
        failures,
    )


    check(
        "Font smoothing established",
        "-webkit-font-smoothing"
        in
        globals_source,
        failures,
    )


    check(
        "Heading balance established",
        "text-wrap: balance"
        in
        globals_source,
        failures,
    )


    check(
        "Paragraph wrapping established",
        "text-wrap: pretty"
        in
        globals_source,
        failures,
    )


    # ========================================================
    # 11. Route page preservation
    # ========================================================

    print(
        "\n11. ROUTE PAGE PRESERVATION"
    )


    protected_pages = (
        mobile_contract
        .get(
            "protected_state",
            {}
        )
        .get(
            "route_page_identity",
            {},
        )
    )


    check(
        "Protected route identity exists",
        isinstance(
            protected_pages,
            dict,
        )
        and
        bool(
            protected_pages
        ),
        failures,
    )


    check(
        "Route pages unchanged",
        protected_pages
        ==
        current_route_pages(),
        failures,
    )


    # ========================================================
    # 12. Presentation-only boundary
    # ========================================================

    print(
        "\n12. PRESENTATION-ONLY BOUNDARY"
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
        "No fetch in application shell",
        re.search(
            r"\bfetch\s*\(",
            combined_source,
        )
        is None,
        failures,
    )


    check(
        "No frontend API client imports",
        "lib/api"
        not in
        combined_source,
        failures,
    )


    forbidden_terms = [
        "data/processed",
        "data\\processed",
        "data/historical",
        "data\\historical",
        ".joblib",
        "football-data.org",
        "api-football",
        "api-sports",
    ]


    for term in forbidden_terms:

        check(
            f"Shell excludes: {term}",
            term.lower()
            not in
            combined_source.lower(),
            failures,
        )


    check(
        "No prediction probability calculation",
        re.search(
            (
                r"prob_(?:home|draw|away)"
                r"\s*[\+\-\*/]"
            ),
            combined_source,
            re.IGNORECASE,
        )
        is None,
        failures,
    )


    # ========================================================
    # 13. Dependency freshness
    # ========================================================

    print(
        "\n13. CONTRACT DEPENDENCY FRESHNESS"
    )


    for stage, contract in contracts:

        verify_dependencies(
            contract,
            stage,
            failures,
        )


    # ========================================================
    # 14. TypeScript
    # ========================================================

    print(
        "\n14. TYPESCRIPT COMPILER"
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


    # ========================================================
    # 15. Promotion safety
    # ========================================================

    print(
        "\n15. PROMOTION SAFETY"
    )


    check(
        "Previous evidence did not prematurely complete Stage 10.3",
        verification_5_6.get(
            "stage10_3_complete"
        )
        is False,
        failures,
    )


    check(
        "Previous evidence did not promote Stage 10",
        verification_5_6.get(
            "stage10_complete"
        )
        is False,
        failures,
    )


    for stage, contract in contracts:

        promotion = contract.get(
            "promotion",
            {}
        )

        check(
            (
                f"{stage} contract does not "
                "claim overall Stage 10 complete"
            ),
            isinstance(
                promotion,
                dict,
            )
            and
            promotion.get(
                "stage10_complete"
            )
            is False,
            failures,
        )


    # ========================================================
    # 16. Final Stage 10.3 promotion
    # ========================================================

    print(
        "\n16. STAGE 10.3.7 FINAL DECISION"
    )


    passed = (
        len(
            failures
        )
        ==
        0
    )


    if passed:

        dependency_paths = [
            VERIFICATION_10_3_1_2,
            VERIFICATION_10_3_3_4,
            VERIFICATION_10_3_5_6,
            LAYOUT_CONTRACT_FILE,
            HEADER_CONTRACT_FILE,
            MAIN_CONTRACT_FILE,
            FOOTER_CONTRACT_FILE,
            TYPOGRAPHY_CONTRACT_FILE,
            MOBILE_CONTRACT_FILE,
            ROUTE_ARCHITECTURE_FILE,
            LAYOUT_FILE,
            GLOBALS_FILE,
            HEADER_FILE,
            MAIN_FILE,
            FOOTER_FILE,
            MOBILE_FILE,
        ]


        final_artifact = {
            "stage":
                "10.3.7",

            "stage_group":
                "10.3",

            "name":
                (
                    "APPLICATION_SHELL_AND_"
                    "NAVIGATION_FINAL_VERIFICATION"
                ),

            "status":
                "PASS",

            "stage_10_3_1_complete":
                True,

            "stage_10_3_2_complete":
                True,

            "stage_10_3_3_complete":
                True,

            "stage_10_3_4_complete":
                True,

            "stage_10_3_5_complete":
                True,

            "stage_10_3_6_complete":
                True,

            "stage_10_3_7_complete":
                True,

            "stage_10_3_complete":
                True,

            "application_shell":
                "VERIFIED",

            "shell": {
                "header":
                    "VERIFIED",

                "main_container":
                    "VERIFIED",

                "footer":
                    "VERIFIED",

                "typography_layout":
                    "VERIFIED",

                "mobile_navigation":
                    "VERIFIED",
            },

            "shell_order": [
                "SiteHeader",
                "MainContainer",
                "SiteFooter",
            ],

            "navigation": {
                "desktop":
                    "VERIFIED",

                "mobile":
                    "VERIFIED",

                "static_destination":
                    "/",

                "invented_matches_index":
                    False,

                "invented_teams_index":
                    False,

                "unnecessary_client_state":
                    False,
            },

            "safety": {
                "route_pages_modified":
                    False,

                "api_access":
                    False,

                "provider_access":
                    False,

                "artifact_access":
                    False,

                "prediction_logic":
                    False,

                "probability_mutation":
                    False,
            },

            "typescript_compiler":
                "PASS",

            "dependency_identity": {
                relative(path):
                    identity(path)

                for path in dependency_paths
            },

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "stage10_ready_for_10_4_1":
                True,

            "stage10_complete":
                False,

            "next_stage":
                "10.4.1",

            "failures":
                [],
        }


        save_json_atomic(
            OUTPUT_FILE,
            final_artifact,
        )


        print(
            "Final verification artifact:"
        )

        print(
            f"  {relative(OUTPUT_FILE)}"
        )


    print(
        "\n"
        +
        "=" * 72
    )


    if passed:

        print(
            "STAGE 10.3.7: PASS"
        )

        print(
            "APPLICATION SHELL & NAVIGATION: VERIFIED"
        )

        print()

        print(
            "STAGE 10.3: COMPLETE"
        )

        print(
            "STAGE 10 READY FOR 10.4.1"
        )

        print()

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.3.7: FAIL"
        )

        print(
            "STAGE 10.3: INCOMPLETE"
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
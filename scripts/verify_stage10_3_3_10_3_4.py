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

MAIN_CONTRACT_FILE = (
    DOCS
    / "frontend_main_container_contract.json"
)

FOOTER_CONTRACT_FILE = (
    DOCS
    / "frontend_footer_contract.json"
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


OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_3_3_10_3_4_verification.json"
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
            /
            raw
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

    passed = bool(condition)

    print(
        f"{label}: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    if not passed:

        failures.append(label)

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
        bool(identities),
        failures,
    )

    if not isinstance(
        identities,
        dict,
    ):

        return


    for path_text, identity in (
        identities.items()
    ):

        try:

            expected = (
                identity.get(
                    "sha256",
                    "",
                )
                if isinstance(
                    identity,
                    dict,
                )
                else ""
            )

            path = resolve_project_path(
                path_text
            )

            current = (
                bool(expected)
                and
                path.exists()
                and
                sha256_file(path)
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
        shutil.which("npm.cmd")
        or
        shutil.which("npm")
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


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.3.3 + 10.3.4"
    )

    print(
        "MAIN CONTAINER + FOOTER VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        PREVIOUS_FILE,
        LAYOUT_CONTRACT_FILE,
        HEADER_CONTRACT_FILE,
        MAIN_CONTRACT_FILE,
        FOOTER_CONTRACT_FILE,
        LAYOUT_FILE,
        GLOBALS_FILE,
        HEADER_FILE,
        MAIN_FILE,
        FOOTER_FILE,
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


    layout_source = (
        LAYOUT_FILE.read_text(
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

    header_source = (
        HEADER_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. STAGE 10.3.1 / 10.3.2 FOUNDATION"
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
        "10.3.1 complete",
        previous.get(
            "stage_10_3_1_complete"
        )
        is True,
        failures,
    )


    check(
        "10.3.2 complete",
        previous.get(
            "stage_10_3_2_complete"
        )
        is True,
        failures,
    )


    check(
        "10.3.2 authorized 10.3.3",
        previous.get(
            "stage10_ready_for_10_3_3"
        )
        is True,
        failures,
    )


    check(
        "10.3.1 contract remains LOCKED",
        layout_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "10.3.2 contract remains LOCKED",
        header_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    print(
        "\n3. STAGE 10.3.3 MAIN CONTAINER CONTRACT"
    )


    check(
        "Main contract stage exact",
        main_contract.get(
            "stage"
        )
        ==
        "10.3.3",
        failures,
    )


    check(
        "Main contract LOCKED",
        main_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Main component exact",
        main_contract.get(
            "component"
        )
        ==
        "MainContainer",
        failures,
    )


    check(
        "Main semantic element exact",
        main_contract.get(
            "semantic_element"
        )
        ==
        "main",
        failures,
    )


    check(
        "Main content ID exact",
        main_contract.get(
            "main_id"
        )
        ==
        "main-content",
        failures,
    )


    print(
        "\n4. MAIN CONTAINER SOURCE"
    )


    check(
        "ReactNode type imported",
        "ReactNode"
        in
        main_source,
        failures,
    )


    check(
        "Main semantic element present",
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
        "main-content ID present",
        'id="main-content"'
        in
        main_source,
        failures,
    )


    check(
        "Route children rendered",
        "{children}"
        in
        main_source,
        failures,
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
                "Main container class present: "
                f"{class_name}"
            ),
            class_name
            in
            main_source,
            failures,
        )


    check(
        "Main container remains server component",
        '"use client"'
        not in
        main_source
        and
        "'use client'"
        not in
        main_source,
        failures,
    )


    print(
        "\n5. STAGE 10.3.4 FOOTER CONTRACT"
    )


    check(
        "Footer contract stage exact",
        footer_contract.get(
            "stage"
        )
        ==
        "10.3.4",
        failures,
    )


    check(
        "Footer contract LOCKED",
        footer_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Footer component exact",
        footer_contract.get(
            "component"
        )
        ==
        "SiteFooter",
        failures,
    )


    check(
        "Footer semantic element exact",
        footer_contract.get(
            "semantic_element"
        )
        ==
        "footer",
        failures,
    )


    print(
        "\n6. FOOTER SOURCE"
    )


    check(
        "Footer semantic element present",
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
        "FixtureIQ brand present",
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


    check(
        "Footer remains server component",
        '"use client"'
        not in
        footer_source
        and
        "'use client'"
        not in
        footer_source,
        failures,
    )


    print(
        "\n7. ROOT LAYOUT INTEGRATION"
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
        "Exactly one SiteHeader",
        layout_source.count(
            "<SiteHeader />"
        )
        ==
        1,
        failures,
    )


    check(
        "Exactly one MainContainer",
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
        "Exactly one SiteFooter",
        layout_source.count(
            "<SiteFooter />"
        )
        ==
        1,
        failures,
    )


    header_index = (
        layout_source.find(
            "<SiteHeader />"
        )
    )

    main_index = (
        layout_source.find(
            "<MainContainer>"
        )
    )

    footer_index = (
        layout_source.find(
            "<SiteFooter />"
        )
    )


    check(
        "Shell render order Header -> Main -> Footer",
        (
            header_index
            >=
            0
            and
            main_index
            >
            header_index
            and
            footer_index
            >
            main_index
        ),
        failures,
    )


    check(
        "Children live inside MainContainer",
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


    print(
        "\n8. LAYOUT TRANSITION CHAIN"
    )


    main_transition = (
        main_contract.get(
            "layout_transition",
            {}
        )
    )

    footer_transition = (
        footer_contract.get(
            "layout_transition",
            {}
        )
    )


    check(
        "10.3.3 starts from verified 10.3.1 layout",
        main_transition.get(
            "before_sha256"
        )
        ==
        layout_contract.get(
            "layout_after_sha256"
        ),
        failures,
    )


    check(
        "10.3.4 starts from 10.3.3 output",
        footer_transition.get(
            "before_footer_sha256"
        )
        ==
        main_transition.get(
            "after_main_sha256"
        ),
        failures,
    )


    check(
        "Current layout equals 10.3.4 final output",
        footer_transition.get(
            "after_footer_sha256"
        )
        ==
        sha256_file(
            LAYOUT_FILE
        ),
        failures,
    )


    print(
        "\n9. PREVIOUS SHELL PRESERVATION"
    )


    main_protected = (
        main_contract.get(
            "protected_state",
            {}
        )
    )

    footer_protected = (
        footer_contract.get(
            "protected_state",
            {}
        )
    )


    check(
        "globals.css unchanged",
        (
            main_protected.get(
                "globals_css_sha256"
            )
            ==
            sha256_file(
                GLOBALS_FILE
            )
            and
            footer_protected.get(
                "globals_css_sha256"
            )
            ==
            sha256_file(
                GLOBALS_FILE
            )
        ),
        failures,
    )


    check(
        "SiteHeader unchanged",
        (
            main_protected.get(
                "site_header_sha256"
            )
            ==
            sha256_file(
                HEADER_FILE
            )
            and
            footer_protected.get(
                "site_header_sha256"
            )
            ==
            sha256_file(
                HEADER_FILE
            )
            and
            header_contract.get(
                "source_sha256"
            )
            ==
            sha256_file(
                HEADER_FILE
            )
        ),
        failures,
    )


    protected_pages = (
        main_protected.get(
            "route_page_identity",
            {}
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
        "All route pages unchanged",
        protected_pages
        ==
        current_route_pages(),
        failures,
    )


    print(
        "\n10. PRESENTATION-ONLY BOUNDARY"
    )


    combined_source = "\n".join(
        [
            layout_source,
            header_source,
            main_source,
            footer_source,
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
        "No shell API client import",
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


    print(
        "\n11. 10.3.5 / 10.3.6 BOUNDARIES"
    )


    check(
        "Typography system not implemented in this stage",
        main_contract.get(
            "responsibility",
            {}
        ).get(
            "typography_system"
        )
        is False,
        failures,
    )


    check(
        "Main container does not own mobile navigation",
        main_contract.get(
            "responsibility",
            {}
        ).get(
            "mobile_navigation"
        )
        is False,
        failures,
    )


    check(
        "Footer does not own mobile navigation",
        footer_contract.get(
            "responsibility",
            {}
        ).get(
            "mobile_navigation"
        )
        is False,
        failures,
    )


    print(
        "\n12. SOURCE IDENTITY"
    )


    check(
        "main-container.tsx SHA current",
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
        "site-footer.tsx SHA current",
        footer_contract.get(
            "source_sha256"
        )
        ==
        sha256_file(
            FOOTER_FILE
        ),
        failures,
    )


    print(
        "\n13. DEPENDENCY FRESHNESS"
    )


    verify_dependencies(
        main_contract,
        "10.3.3",
        failures,
    )


    verify_dependencies(
        footer_contract,
        "10.3.4",
        failures,
    )


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


    print(
        "\n15. NO PREMATURE PROMOTION"
    )


    main_promotion = (
        main_contract.get(
            "promotion",
            {}
        )
    )

    footer_promotion = (
        footer_contract.get(
            "promotion",
            {}
        )
    )


    check(
        "10.3.3 contract did not self-promote",
        main_promotion.get(
            "stage10_3_3_complete"
        )
        is False,
        failures,
    )


    check(
        "10.3.4 contract did not self-promote",
        footer_promotion.get(
            "stage10_3_4_complete"
        )
        is False,
        failures,
    )


    check(
        "Stage 10.3 remains incomplete",
        (
            main_promotion.get(
                "stage10_3_complete"
            )
            is False
            and
            footer_promotion.get(
                "stage10_3_complete"
            )
            is False
        ),
        failures,
    )


    check(
        "Stage 10 remains incomplete",
        (
            main_promotion.get(
                "stage10_complete"
            )
            is False
            and
            footer_promotion.get(
                "stage10_complete"
            )
            is False
        ),
        failures,
    )


    print(
        "\n16. SAVE VERIFICATION EVIDENCE"
    )


    passed = (
        len(failures)
        ==
        0
    )


    if passed:

        evidence = {
            "stage":
                "10.3.3-10.3.4",

            "name":
                (
                    "MAIN_CONTAINER_AND_"
                    "FOOTER_VERIFICATION"
                ),

            "status":
                "PASS",

            "stage_10_3_3_complete":
                True,

            "stage_10_3_4_complete":
                True,

            "main_container":
                "LOCKED_AND_VERIFIED",

            "footer":
                "LOCKED_AND_VERIFIED",

            "shell_order": [
                "SiteHeader",
                "MainContainer",
                "SiteFooter",
            ],

            "route_pages_preserved":
                True,

            "globals_css_preserved":
                True,

            "site_header_preserved":
                True,

            "safety": {
                "api_access":
                    False,

                "provider_access":
                    False,

                "artifact_access":
                    False,

                "prediction_logic":
                    False,

                "typography_system_added":
                    False,

                "mobile_navigation_added":
                    False,
            },

            "typescript_compiler":
                "PASS",

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "stage10_ready_for_10_3_5":
                True,

            "stage10_3_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.3.5",

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
            "STAGE 10.3.3: PASS"
        )

        print(
            "MAIN CONTAINER: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.3.4: PASS"
        )

        print(
            "FOOTER: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.3.5"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.3.3 / 10.3.4: FAIL"
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
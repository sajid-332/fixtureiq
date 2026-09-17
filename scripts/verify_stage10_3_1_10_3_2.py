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


STAGE10_2_FINAL_FILE = (
    FRONTEND_DATA
    / "stage10_2_final_verification.json"
)

ROUTE_ARCHITECTURE_FILE = (
    DOCS
    / "frontend_route_architecture.json"
)

LAYOUT_CONTRACT_FILE = (
    DOCS
    / "frontend_global_layout_contract.json"
)

HEADER_CONTRACT_FILE = (
    DOCS
    / "frontend_header_navigation_contract.json"
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


OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_3_1_10_3_2_verification.json"
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


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.3.1 + 10.3.2"
    )

    print(
        "GLOBAL LAYOUT + HEADER / NAVIGATION VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        STAGE10_2_FINAL_FILE,
        ROUTE_ARCHITECTURE_FILE,
        LAYOUT_CONTRACT_FILE,
        HEADER_CONTRACT_FILE,
        LAYOUT_FILE,
        GLOBALS_FILE,
        HEADER_FILE,
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


    stage10_2 = load_json(
        STAGE10_2_FINAL_FILE
    )

    route_architecture = load_json(
        ROUTE_ARCHITECTURE_FILE
    )

    layout_contract = load_json(
        LAYOUT_CONTRACT_FILE
    )

    header_contract = load_json(
        HEADER_CONTRACT_FILE
    )


    layout_source = (
        LAYOUT_FILE.read_text(
            encoding="utf-8"
        )
    )

    header_source = (
        HEADER_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. STAGE 10.2 FOUNDATION"
    )


    check(
        "Stage 10.2 final verification PASS",
        stage10_2.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )


    check(
        "Stage 10.2 complete",
        stage10_2.get(
            "stage_10_2_complete"
        )
        is True,
        failures,
    )


    check(
        "Stage 10.2 authorized 10.3.1",
        stage10_2.get(
            "stage10_ready_for_10_3_1"
        )
        is True,
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


    print(
        "\n3. STAGE 10.3.1 GLOBAL LAYOUT CONTRACT"
    )


    check(
        "Layout contract stage exact",
        layout_contract.get(
            "stage"
        )
        ==
        "10.3.1",
        failures,
    )


    check(
        "Layout contract LOCKED",
        layout_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    structure = (
        layout_contract.get(
            "shell_structure",
            {}
        )
    )


    check(
        "Global HTML root locked",
        structure.get(
            "html_root"
        )
        is True,
        failures,
    )


    check(
        "Global body root locked",
        structure.get(
            "body_root"
        )
        is True,
        failures,
    )


    check(
        "Global header locked",
        structure.get(
            "global_header"
        )
        is True,
        failures,
    )


    check(
        "Children slot locked",
        structure.get(
            "children_slot"
        )
        is True,
        failures,
    )


    check(
        "Main container still owned by 10.3.3",
        structure.get(
            "main_container_owned_by"
        )
        ==
        "10.3.3",
        failures,
    )


    check(
        "Footer still owned by 10.3.4",
        structure.get(
            "footer_owned_by"
        )
        ==
        "10.3.4",
        failures,
    )


    print(
        "\n4. ROOT LAYOUT SOURCE"
    )


    check(
        "globals.css import preserved",
        "./globals.css"
        in
        layout_source,
        failures,
    )


    check(
        "SiteHeader import present",
        "site-header"
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
        "HTML root present",
        "<html"
        in
        layout_source
        and
        "</html>"
        in
        layout_source,
        failures,
    )


    check(
        "Body root present",
        "<body"
        in
        layout_source
        and
        "</body>"
        in
        layout_source,
        failures,
    )


    check(
        "Children still rendered",
        "{children}"
        in
        layout_source,
        failures,
    )


    check(
        "10.3.3 main container not implemented early",
        "<main"
        not in
        layout_source,
        failures,
    )


    check(
        "10.3.4 footer not implemented early",
        "<footer"
        not in
        layout_source,
        failures,
    )


    implementation = (
        layout_contract.get(
            "implementation",
            {}
        )
    )


    check(
        "Existing layout patched safely",
        implementation.get(
            "existing_layout_patched"
        )
        is True,
        failures,
    )


    check(
        "Blind layout replacement prohibited",
        implementation.get(
            "existing_layout_replaced_blindly"
        )
        is False,
        failures,
    )


    check(
        "Route pages not modified",
        implementation.get(
            "route_pages_modified"
        )
        is False,
        failures,
    )


    print(
        "\n5. PROTECTED ROUTE PAGE IDENTITY"
    )


    protected_pages = (
        layout_contract.get(
            "protected_route_page_identity",
            {}
        )
    )


    check(
        "Protected page identity exists",
        isinstance(
            protected_pages,
            dict,
        )
        and
        bool(protected_pages),
        failures,
    )


    if isinstance(
        protected_pages,
        dict,
    ):

        for path_text, identity in (
            protected_pages.items()
        ):

            try:

                path = resolve_project_path(
                    path_text
                )

                current = (
                    path.exists()
                    and
                    sha256_file(path)
                    ==
                    identity.get(
                        "sha256"
                    )
                )

            except Exception:

                current = False


            check(
                (
                    "Route page unchanged: "
                    f"{Path(path_text).name} "
                    f"({path_text})"
                ),
                current,
                failures,
            )


    print(
        "\n6. STAGE 10.3.2 HEADER CONTRACT"
    )


    check(
        "Header contract stage exact",
        header_contract.get(
            "stage"
        )
        ==
        "10.3.2",
        failures,
    )


    check(
        "Header contract LOCKED",
        header_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Header component exact",
        header_contract.get(
            "component"
        )
        ==
        "SiteHeader",
        failures,
    )


    framework = (
        header_contract.get(
            "framework_primitives",
            {}
        )
    )


    check(
        "Next Link locked",
        framework.get(
            "next_link"
        )
        is True,
        failures,
    )


    check(
        "Header remains server component",
        framework.get(
            "server_component"
        )
        is True,
        failures,
    )


    print(
        "\n7. HEADER / NAVIGATION SOURCE"
    )


    check(
        "Next Link imported",
        'from "next/link"'
        in
        header_source,
        failures,
    )


    check(
        "FixtureIQ brand present",
        "FixtureIQ"
        in
        header_source,
        failures,
    )


    check(
        "Header semantic element present",
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
        "Navigation semantic element present",
        "<nav"
        in
        header_source
        and
        "</nav>"
        in
        header_source,
        failures,
    )


    check(
        "Primary navigation aria-label present",
        (
            'aria-label="Primary navigation"'
            in
            header_source
        ),
        failures,
    )


    check(
        "Upcoming label present",
        "Upcoming"
        in
        header_source,
        failures,
    )


    hrefs = re.findall(
        r'href\s*=\s*["\']([^"\']+)["\']',
        header_source,
    )


    check(
        "Header contains navigation links",
        bool(hrefs),
        failures,
    )


    check(
        "Every current header link targets root",
        bool(hrefs)
        and
        set(hrefs)
        ==
        {"/"},
        failures,
    )


    check(
        "No invented /matches index link",
        'href="/matches"'
        not in
        header_source,
        failures,
    )


    check(
        "No invented /teams index link",
        'href="/teams"'
        not in
        header_source,
        failures,
    )


    check(
        "No client directive",
        '"use client"'
        not in
        header_source
        and
        "'use client'"
        not in
        header_source,
        failures,
    )


    print(
        "\n8. PRESENTATION-ONLY BOUNDARY"
    )


    combined_source = (
        layout_source
        +
        "\n"
        +
        header_source
    )


    check(
        "No fetch in shell",
        re.search(
            r"\bfetch\s*\(",
            combined_source,
        )
        is None,
        failures,
    )


    check(
        "No API client imports in shell",
        "/lib/api/"
        not in
        combined_source
        and
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
        "\n9. SOURCE IDENTITY"
    )


    check(
        "layout.tsx SHA current",
        layout_contract.get(
            "layout_after_sha256"
        )
        ==
        sha256_file(
            LAYOUT_FILE
        ),
        failures,
    )


    check(
        "site-header.tsx SHA current",
        header_contract.get(
            "source_sha256"
        )
        ==
        sha256_file(
            HEADER_FILE
        ),
        failures,
    )


    print(
        "\n10. DEPENDENCY FRESHNESS"
    )


    verify_dependencies(
        layout_contract,
        "10.3.1",
        failures,
    )


    verify_dependencies(
        header_contract,
        "10.3.2",
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


    layout_promotion = (
        layout_contract.get(
            "promotion",
            {}
        )
    )

    header_promotion = (
        header_contract.get(
            "promotion",
            {}
        )
    )


    check(
        "10.3.1 contract did not self-promote",
        layout_promotion.get(
            "stage10_3_1_complete"
        )
        is False,
        failures,
    )


    check(
        "10.3.2 contract did not self-promote",
        header_promotion.get(
            "stage10_3_2_complete"
        )
        is False,
        failures,
    )


    check(
        "Stage 10.3 remains incomplete",
        (
            layout_promotion.get(
                "stage10_3_complete"
            )
            is False
            and
            header_promotion.get(
                "stage10_3_complete"
            )
            is False
        ),
        failures,
    )


    check(
        "Stage 10 remains incomplete",
        (
            layout_promotion.get(
                "stage10_complete"
            )
            is False
            and
            header_promotion.get(
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
        len(failures)
        ==
        0
    )


    if passed:

        evidence = {
            "stage":
                "10.3.1-10.3.2",

            "name":
                (
                    "GLOBAL_LAYOUT_AND_"
                    "HEADER_NAVIGATION_VERIFICATION"
                ),

            "status":
                "PASS",

            "stage_10_3_1_complete":
                True,

            "stage_10_3_2_complete":
                True,

            "global_application_layout":
                "LOCKED_AND_VERIFIED",

            "header_navigation":
                "LOCKED_AND_VERIFIED",

            "route_pages_preserved":
                True,

            "server_component_shell":
                True,

            "navigation": {
                "brand_home":
                    "/",

                "upcoming":
                    "/",

                "invented_matches_index":
                    False,

                "invented_teams_index":
                    False,
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

                "main_container_implemented":
                    False,

                "footer_implemented":
                    False,

                "mobile_navigation_implemented":
                    False,
            },

            "typescript_compiler":
                "PASS",

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "stage10_ready_for_10_3_3":
                True,

            "stage10_3_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.3.3",

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
            "STAGE 10.3.1: PASS"
        )

        print(
            "GLOBAL APPLICATION LAYOUT: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.3.2: PASS"
        )

        print(
            "HEADER / NAVIGATION: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.3.3"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.3.1 / 10.3.2: FAIL"
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
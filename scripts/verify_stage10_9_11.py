from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
DOCS = ROOT / "docs" / "stage10"
DATA = ROOT / "data" / "processed" / "frontend"


STAGE10_8_FINAL = (
    DATA
    / "stage10_8_final_verification.json"
)

STAGE10_9_PARTIAL = (
    DATA
    / "stage10_9_1_10_9_10_verification.json"
)

RESPONSIVE_CONTRACT = (
    DOCS
    / "frontend_responsive_product_polish_contract.json"
)

FINAL_OUTPUT = (
    DATA
    / "stage10_9_final_verification.json"
)


RESPONSIVE_CSS = (
    FRONTEND
    / "app"
    / "stage10-responsive.css"
)

LAYOUT = (
    FRONTEND
    / "app"
    / "layout.tsx"
)

ROOT_PAGE = (
    FRONTEND
    / "app"
    / "page.tsx"
)

MATCH_PAGE = (
    FRONTEND
    / "app"
    / "matches"
    / "[fixtureId]"
    / "page.tsx"
)

TEAM_PAGE = (
    FRONTEND
    / "app"
    / "teams"
    / "[teamName]"
    / "page.tsx"
)

MATCH_CARD = (
    FRONTEND
    / "components"
    / "matches"
    / "match-card.tsx"
)

PROBABILITY_BAR = (
    FRONTEND
    / "components"
    / "ui"
    / "probability-bar.tsx"
)

TEAM_COMPARISON_ROW = (
    FRONTEND
    / "components"
    / "ui"
    / "team-comparison-row.tsx"
)

EXPLANATION = (
    FRONTEND
    / "components"
    / "ui"
    / "intelligence-explanation.tsx"
)

RETRY_ACTION = (
    FRONTEND
    / "components"
    / "runtime"
    / "retry-action.tsx"
)

ERROR_STATE = (
    FRONTEND
    / "components"
    / "ui"
    / "error-state.tsx"
)

LOADING_STATE = (
    FRONTEND
    / "components"
    / "ui"
    / "loading-state.tsx"
)

EMPTY_STATE = (
    FRONTEND
    / "components"
    / "ui"
    / "empty-state.tsx"
)

SITE_HEADER = (
    FRONTEND
    / "components"
    / "shell"
    / "site-header.tsx"
)

MOBILE_NAV = (
    FRONTEND
    / "components"
    / "shell"
    / "mobile-navigation.tsx"
)

MAIN_CONTAINER = (
    FRONTEND
    / "components"
    / "shell"
    / "main-container.tsx"
)


def relative(path: Path) -> str:

    return str(
        path.resolve().relative_to(
            ROOT.resolve()
        )
    ).replace(
        "\\",
        "/",
    )


def sha256_file(path: Path) -> str:

    digest = hashlib.sha256()

    with path.open("rb") as file:

        for chunk in iter(
            lambda: file.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(
                chunk
            )

    return digest.hexdigest()


def load_json(path: Path) -> dict:

    if not path.exists():

        raise RuntimeError(
            f"Missing JSON: {relative(path)}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        value = json.load(
            file
        )

    if not isinstance(
        value,
        dict,
    ):

        raise RuntimeError(
            f"Expected JSON object: {relative(path)}"
        )

    return value


def save_json(
    path: Path,
    value: dict,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            value,
            indent=2,
        )
        +
        "\n",
        encoding="utf-8",
    )

    temporary.replace(
        path
    )


def npm_path() -> str:

    executable = (
        shutil.which("npm.cmd")
        or
        shutil.which("npm")
    )

    if executable is None:

        raise RuntimeError(
            "npm executable not found."
        )

    return executable


def run_command(
    args: list[str],
    cwd: Path,
    env: dict | None = None,
) -> tuple[bool, str]:

    result = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    output = (
        result.stdout
        +
        result.stderr
    ).strip()

    return (
        result.returncode == 0,
        output,
    )


failures: list[str] = []


def verify(
    label: str,
    condition: bool,
) -> None:

    print(
        f"{label}: "
        +
        (
            "PASS"
            if condition
            else "FAIL"
        )
    )

    if not condition:

        failures.append(
            label
        )


def source(path: Path) -> str:

    return path.read_text(
        encoding="utf-8"
    )


def main() -> None:

    print(
        "=" * 72
    )

    print(
        "FixtureIQ Stage 10.9.11"
    )

    print(
        "RESPONSIVE UI + PRODUCT POLISH FINAL VERIFICATION"
    )

    print(
        "=" * 72
    )


    required_files = [
        STAGE10_8_FINAL,
        STAGE10_9_PARTIAL,
        RESPONSIVE_CONTRACT,
        RESPONSIVE_CSS,
        LAYOUT,
        ROOT_PAGE,
        MATCH_PAGE,
        TEAM_PAGE,
        MATCH_CARD,
        PROBABILITY_BAR,
        TEAM_COMPARISON_ROW,
        EXPLANATION,
        RETRY_ACTION,
        ERROR_STATE,
        LOADING_STATE,
        EMPTY_STATE,
        SITE_HEADER,
        MOBILE_NAV,
        MAIN_CONTAINER,
    ]


    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    for path in required_files:

        verify(
            relative(path),
            path.exists(),
        )


    if failures:

        print(
            "\nRequired files missing. "
            "Cannot continue safely."
        )

        raise SystemExit(1)


    stage8 = load_json(
        STAGE10_8_FINAL
    )

    partial = load_json(
        STAGE10_9_PARTIAL
    )

    contract = load_json(
        RESPONSIVE_CONTRACT
    )


    print(
        "\n2. STAGE 10.8 FOUNDATION"
    )

    verify(
        "Stage 10.8 status PASS",
        stage8.get(
            "status"
        )
        ==
        "PASS",
    )

    verify(
        "Stage 10.8 complete",
        stage8.get(
            "stage10_8_complete"
        )
        is True,
    )

    verify(
        "Stage 10.8 authorized 10.9.1",
        stage8.get(
            "stage10_ready_for_10_9_1"
        )
        is True,
    )


    print(
        "\n3. STAGE 10.9.1 - 10.9.10 FOUNDATION"
    )

    verify(
        "Partial verification status PASS",
        partial.get(
            "status"
        )
        ==
        "PASS",
    )

    for number in range(
        1,
        11,
    ):

        verify(
            f"Stage 10.9.{number} complete",
            partial.get(
                f"stage_10_9_{number}_complete"
            )
            is True,
        )

    verify(
        "Authorized for 10.9.11",
        partial.get(
            "stage10_ready_for_10_9_11"
        )
        is True,
    )

    verify(
        "10.9 not promoted early",
        partial.get(
            "stage10_9_complete"
        )
        is False,
    )

    verify(
        "Stage 10 not promoted early",
        partial.get(
            "stage10_complete"
        )
        is False,
    )


    print(
        "\n4. RESPONSIVE CONTRACT"
    )

    verify(
        "Contract stage exact",
        contract.get(
            "stage"
        )
        ==
        "10.9.1-10.9.10",
    )

    verify(
        "Contract LOCKED",
        contract.get(
            "status"
        )
        ==
        "LOCKED",
    )

    verify(
        "Presentation authority only",
        contract.get(
            "presentation_authority_only"
        )
        is True,
    )

    verify(
        "Mobile breakpoint exact",
        contract.get(
            "breakpoints",
            {},
        ).get(
            "mobile_max_px"
        )
        ==
        639,
    )

    verify(
        "Tablet min exact",
        contract.get(
            "breakpoints",
            {},
        ).get(
            "tablet_min_px"
        )
        ==
        640,
    )

    verify(
        "Tablet max exact",
        contract.get(
            "breakpoints",
            {},
        ).get(
            "tablet_max_px"
        )
        ==
        1023,
    )

    verify(
        "Desktop min exact",
        contract.get(
            "breakpoints",
            {},
        ).get(
            "desktop_min_px"
        )
        ==
        1024,
    )


    print(
        "\n5. SOURCE IDENTITY"
    )

    contract_identity = contract.get(
        "source_identity",
        {},
    )

    verify(
        "Responsive CSS SHA exact",
        contract_identity.get(
            relative(
                RESPONSIVE_CSS
            )
        )
        ==
        sha256_file(
            RESPONSIVE_CSS
        ),
    )

    verify(
        "Layout SHA exact",
        contract_identity.get(
            relative(
                LAYOUT
            )
        )
        ==
        sha256_file(
            LAYOUT
        ),
    )

    dependency_identity = contract.get(
        "dependency_identity",
        {},
    )

    verify(
        "Stage 10.8 dependency current",
        dependency_identity.get(
            relative(
                STAGE10_8_FINAL
            )
        )
        ==
        sha256_file(
            STAGE10_8_FINAL
        ),
    )

    partial_dependencies = partial.get(
        "dependency_identity",
        {},
    )

    verify(
        "Partial responsive contract current",
        partial_dependencies.get(
            relative(
                RESPONSIVE_CONTRACT
            )
        )
        ==
        sha256_file(
            RESPONSIVE_CONTRACT
        ),
    )


    css = source(
        RESPONSIVE_CSS
    )

    layout_source = source(
        LAYOUT
    )

    root_source = source(
        ROOT_PAGE
    )

    match_source = source(
        MATCH_PAGE
    )

    team_source = source(
        TEAM_PAGE
    )

    card_source = source(
        MATCH_CARD
    )

    probability_source = source(
        PROBABILITY_BAR
    )

    comparison_source = source(
        TEAM_COMPARISON_ROW
    )

    explanation_source = source(
        EXPLANATION
    )

    retry_source = source(
        RETRY_ACTION
    )


    print(
        "\n6. 10.9.1 MOBILE DASHBOARD"
    )

    verify(
        "Mobile media query",
        "@media (max-width: 639px)"
        in
        css,
    )

    verify(
        "Dashboard responsive selector",
        '[data-fixtureiq-dashboard-state="READY"]'
        in
        css,
    )

    verify(
        "MatchCard responsive selector",
        '[data-fixtureiq-component="match-card"]'
        in
        css,
    )

    verify(
        "Dashboard remains dynamic",
        '"force-dynamic"'
        in
        root_source,
    )


    print(
        "\n7. 10.9.2 MOBILE DETAIL"
    )

    verify(
        "Team comparison responsive",
        '[data-fixtureiq-component="team-comparison-row"]'
        in
        css,
    )

    verify(
        "Explanation responsive",
        '[data-fixtureiq-component="intelligence-explanation"]'
        in
        css,
    )

    verify(
        "Match detail remains dynamic",
        '"force-dynamic"'
        in
        match_source,
    )


    print(
        "\n8. 10.9.3 TABLET"
    )

    verify(
        "Tablet media query",
        (
            "@media (min-width: 640px) "
            "and (max-width: 1023px)"
        )
        in
        css,
    )


    print(
        "\n9. 10.9.4 DESKTOP"
    )

    verify(
        "Desktop media query",
        "@media (min-width: 1024px)"
        in
        css,
    )

    verify(
        "Desktop explanation width",
        "max-width: 80ch;"
        in
        css,
    )


    print(
        "\n10. 10.9.5 PROBABILITY RESPONSIVENESS"
    )

    verify(
        "ProbabilityBar source exists",
        len(
            probability_source.strip()
        )
        >
        0,
    )

    verify(
        "Probability selector",
        '[data-fixtureiq-component="probability-bar"]'
        in
        css,
    )

    verify(
        "Probability progress responsive",
        (
            '[data-fixtureiq-component="probability-bar"] progress'
            in
            css
        ),
    )

    verify(
        "Probability width responsive",
        "width: 100%;"
        in
        css,
    )


    print(
        "\n11. 10.9.6 LONG TEAM NAMES"
    )

    verify(
        "Long text wrapping enabled",
        "overflow-wrap: anywhere;"
        in
        css,
    )

    verify(
        "Match team heading covered",
        (
            '[data-fixtureiq-component="match-card"] h2'
            in
            css
        ),
    )

    verify(
        "MatchCard identity source preserved",
        "homeTeamName"
        in
        card_source
        and
        "awayTeamName"
        in
        card_source,
    )


    print(
        "\n12. 10.9.7 LONG EXPLANATIONS"
    )

    verify(
        "Explanation selector present",
        '[data-fixtureiq-component="intelligence-explanation"]'
        in
        css,
    )

    verify(
        "Explanation readable line-height",
        "line-height: 1.65;"
        in
        css,
    )

    verify(
        "Explanation component preserved",
        len(
            explanation_source.strip()
        )
        >
        0,
    )


    print(
        "\n13. 10.9.8 ACCESSIBILITY BASICS"
    )

    verify(
        "Focus visible support",
        ":focus-visible"
        in
        css,
    )

    verify(
        "Reduced motion support",
        "prefers-reduced-motion"
        in
        css,
    )

    verify(
        "Higher contrast support",
        "prefers-contrast: more"
        in
        css,
    )

    verify(
        "44px button target",
        "min-height: 44px;"
        in
        css,
    )

    verify(
        "Error state preserved",
        ERROR_STATE.exists(),
    )

    verify(
        "Loading state preserved",
        LOADING_STATE.exists(),
    )

    verify(
        "Empty state preserved",
        EMPTY_STATE.exists(),
    )


    print(
        "\n14. 10.9.9 KEYBOARD / NAVIGATION"
    )

    verify(
        "Anchor focus visible",
        "a[href]:focus-visible"
        in
        css,
    )

    verify(
        "Button focus visible",
        "button:focus-visible"
        in
        css,
    )

    verify(
        "Retry uses real button",
        'type="button"'
        in
        retry_source,
    )

    verify(
        "Retry uses Next navigation",
        "useRouter"
        in
        retry_source
        and
        "router.refresh()"
        in
        retry_source,
    )

    verify(
        "Site header exists",
        SITE_HEADER.exists(),
    )

    verify(
        "Mobile navigation exists",
        MOBILE_NAV.exists(),
    )


    print(
        "\n15. 10.9.10 VISUAL CONSISTENCY"
    )

    verify(
        "Shared card radius token",
        "--fixtureiq-radius-card"
        in
        css,
    )

    verify(
        "Shared border token",
        "--fixtureiq-border"
        in
        css,
    )

    verify(
        "Shared focus token",
        "--fixtureiq-focus"
        in
        css,
    )

    verify(
        "Responsive CSS loaded globally",
        'import "./stage10-responsive.css";'
        in
        layout_source,
    )

    verify(
        "Main container preserved",
        MAIN_CONTAINER.exists(),
    )


    print(
        "\n16. PRESENTATION-ONLY SAFETY"
    )

    combined_ui = "\n".join(
        [
            css,
            layout_source,
        ]
    )

    forbidden = [
        "fetch(",
        ".csv",
        ".joblib",
        "football-data.org",
        "api-football",
        "api-sports",
        "Math.max(",
        "recalibr",
        "predict_proba",
        "joblib.load",
    ]

    for token in forbidden:

        verify(
            f"No forbidden UI logic: {token}",
            token
            not in
            combined_ui,
        )


    rules = contract.get(
        "rules",
        {},
    )

    verify(
        "Probability not modified",
        rules.get(
            "probability_value_modified"
        )
        is False,
    )

    verify(
        "Prediction logic not added",
        rules.get(
            "prediction_logic_added"
        )
        is False,
    )

    verify(
        "Context logic not added",
        rules.get(
            "context_logic_added"
        )
        is False,
    )

    verify(
        "Explanation not rewritten",
        rules.get(
            "explanation_rewritten"
        )
        is False,
    )


    print(
        "\n17. RUNTIME / FAILURE UX PRESERVATION"
    )

    for path, route_source in [
        (
            ROOT_PAGE,
            root_source,
        ),
        (
            MATCH_PAGE,
            match_source,
        ),
        (
            TEAM_PAGE,
            team_source,
        ),
    ]:

        verify(
            (
                f"{relative(path)} "
                "force-dynamic"
            ),
            '"force-dynamic"'
            in
            route_source,
        )

        for token in [
            "localStorage",
            "sessionStorage",
            "previousData",
            "previousResponse",
            "staleData",
            "fallbackData",
        ]:

            verify(
                (
                    f"{relative(path)} "
                    f"no {token}"
                ),
                token
                not in
                route_source,
            )


    print(
        "\n18. COMPONENT PRESERVATION"
    )

    verify(
        "MatchCard marker preserved",
        'data-fixtureiq-component="match-card"'
        in
        card_source,
    )

    verify(
        "Team comparison source preserved",
        len(
            comparison_source.strip()
        )
        >
        0,
    )

    verify(
        "Probability source preserved",
        len(
            probability_source.strip()
        )
        >
        0,
    )


    print(
        "\n19. TYPESCRIPT"
    )

    npm = npm_path()

    ts_ok, ts_output = run_command(
        [
            npm,
            "exec",
            "--",
            "tsc",
            "--noEmit",
        ],
        FRONTEND,
    )

    verify(
        "TypeScript --noEmit",
        ts_ok,
    )

    if not ts_ok:

        print()
        print(
            ts_output
        )


    print(
        "\n20. PRODUCTION BUILD"
    )

    environment = os.environ.copy()

    environment.setdefault(
        "FIXTUREIQ_API_BASE_URL",
        "http://127.0.0.1:5000",
    )

    build_ok, build_output = run_command(
        [
            npm,
            "run",
            "build",
        ],
        FRONTEND,
        environment,
    )

    verify(
        "Next.js production build",
        build_ok,
    )

    if not build_ok:

        print()
        print(
            build_output
        )


    print(
        "\n21. NO PREMATURE STAGE 10 PROMOTION"
    )

    verify(
        "Stage 10.9 partial did not promote Stage 10",
        partial.get(
            "stage10_complete"
        )
        is False,
    )

    verify(
        "Responsive contract did not promote Stage 10",
        contract.get(
            "stage10_complete"
        )
        is False,
    )


    print(
        "\n22. SAVE FINAL VERIFICATION"
    )


    if failures:

        print()
        print(
            "=" * 72
        )

        print(
            "STAGE 10.9.11: FAIL"
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

        raise SystemExit(1)


    final = {
        "stage":
            "10.9.11",

        "name":
            "RESPONSIVE_UI_PRODUCT_POLISH_FINAL_VERIFICATION",

        "status":
            "PASS",

        "stage_10_9_1_complete":
            True,

        "stage_10_9_2_complete":
            True,

        "stage_10_9_3_complete":
            True,

        "stage_10_9_4_complete":
            True,

        "stage_10_9_5_complete":
            True,

        "stage_10_9_6_complete":
            True,

        "stage_10_9_7_complete":
            True,

        "stage_10_9_8_complete":
            True,

        "stage_10_9_9_complete":
            True,

        "stage_10_9_10_complete":
            True,

        "stage_10_9_11_complete":
            True,

        "responsive_verification": {
            "mobile_dashboard":
                "PASS",

            "mobile_detail":
                "PASS",

            "tablet":
                "PASS",

            "desktop":
                "PASS",

            "probability_responsiveness":
                "PASS",

            "long_team_names":
                "PASS",

            "long_explanations":
                "PASS",

            "accessibility_basics":
                "PASS",

            "keyboard_navigation":
                "PASS",

            "visual_consistency":
                "PASS",
        },

        "presentation_integrity": {
            "prediction_modified":
                False,

            "probability_modified":
                False,

            "context_modified":
                False,

            "explanation_modified":
                False,

            "direct_provider_access":
                False,

            "direct_artifact_access":
                False,

            "stale_fallback":
                False,
        },

        "typescript":
            "PASS",

        "production_build":
            "PASS",

        "stage10_9_complete":
            True,

        "stage10_ready_for_10_10_1":
            True,

        "stage10_complete":
            False,

        "next_stage":
            "10.10.1",

        "dependency_identity": {
            relative(
                STAGE10_8_FINAL
            ):
                sha256_file(
                    STAGE10_8_FINAL
                ),

            relative(
                STAGE10_9_PARTIAL
            ):
                sha256_file(
                    STAGE10_9_PARTIAL
                ),

            relative(
                RESPONSIVE_CONTRACT
            ):
                sha256_file(
                    RESPONSIVE_CONTRACT
                ),

            relative(
                RESPONSIVE_CSS
            ):
                sha256_file(
                    RESPONSIVE_CSS
                ),

            relative(
                LAYOUT
            ):
                sha256_file(
                    LAYOUT
                ),
        },

        "verified_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }


    save_json(
        FINAL_OUTPUT,
        final,
    )

    print(
        relative(
            FINAL_OUTPUT
        )
    )

    print()
    print(
        "=" * 72
    )

    print(
        "STAGE 10.9.11: PASS"
    )

    print(
        "RESPONSIVE UI & PRODUCT POLISH: VERIFIED"
    )

    print()

    print(
        "STAGE 10.9: COMPLETE"
    )

    print(
        "STAGE 10 READY FOR 10.10.1"
    )

    print(
        "STAGE 10 IS NOT YET PROMOTED"
    )

    print(
        "=" * 72
    )


if __name__ == "__main__":

    main()
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
    / "stage10_4_1_10_4_2_verification.json"
)

BASE_CARD_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_base_contract.json"
)

LOADER_CONTRACT_FILE = (
    DOCS
    / "frontend_upcoming_dashboard_loader_contract.json"
)

IDENTITY_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_identity_contract.json"
)

KICKOFF_CONTRACT_FILE = (
    DOCS
    / "frontend_match_card_kickoff_contract.json"
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

FORMATTER_FILE = (
    FRONTEND
    / "lib"
    / "formatters"
    / "kickoff.ts"
)


OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_4_3_10_4_4_verification.json"
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

    temporary = (
        path.with_suffix(
            path.suffix + ".tmp"
        )
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
        failures.append(label)

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

    dependencies = payload.get(
        "dependency_identity",
        {},
    )


    check(
        f"{label} dependency identity exists",
        isinstance(
            dependencies,
            dict,
        )
        and
        bool(
            dependencies
        ),
        failures,
    )


    if not isinstance(
        dependencies,
        dict,
    ):
        return


    for path_text, declared in (
        dependencies.items()
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
        "FixtureIQ Stage 10.4.3 + 10.4.4"
    )

    print(
        "MATCH IDENTITY + KICKOFF VERIFICATION"
    )

    print("=" * 72)


    failures: list[str] = []


    required = [
        PREVIOUS_FILE,
        BASE_CARD_CONTRACT_FILE,
        LOADER_CONTRACT_FILE,
        IDENTITY_CONTRACT_FILE,
        KICKOFF_CONTRACT_FILE,
        MATCH_CARD_FILE,
        LOADER_FILE,
        FORMATTER_FILE,
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

    base_card = load_json(
        BASE_CARD_CONTRACT_FILE
    )

    loader_contract = load_json(
        LOADER_CONTRACT_FILE
    )

    identity_contract = load_json(
        IDENTITY_CONTRACT_FILE
    )

    kickoff_contract = load_json(
        KICKOFF_CONTRACT_FILE
    )


    card_source = (
        MATCH_CARD_FILE.read_text(
            encoding="utf-8"
        )
    )

    formatter_source = (
        FORMATTER_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. STAGE 10.4.1 / 10.4.2 FOUNDATION"
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
        "10.4.1 complete",
        previous.get(
            "stage_10_4_1_complete"
        )
        is True,
        failures,
    )


    check(
        "10.4.2 complete",
        previous.get(
            "stage_10_4_2_complete"
        )
        is True,
        failures,
    )


    check(
        "10.4.2 authorized 10.4.3",
        previous.get(
            "stage10_ready_for_10_4_3"
        )
        is True,
        failures,
    )


    print(
        "\n3. STAGE 10.4.3 CONTRACT"
    )


    check(
        "Identity stage exact",
        identity_contract.get(
            "stage"
        )
        ==
        "10.4.3",
        failures,
    )


    check(
        "Identity contract LOCKED",
        identity_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Identity fields exact",
        identity_contract.get(
            "identity_fields"
        )
        ==
        [
            "homeTeamName",
            "awayTeamName",
        ],
        failures,
    )


    identity_transition = (
        identity_contract.get(
            "transition",
            {},
        )
    )


    check(
        "10.4.3 starts from 10.4.2 MatchCard",
        identity_transition.get(
            "match_card_before_identity_sha256"
        )
        ==
        base_card.get(
            "source_sha256"
        ),
        failures,
    )


    print(
        "\n4. MATCH IDENTITY SOURCE"
    )


    check(
        "homeTeamName prop present",
        "homeTeamName: string"
        in
        card_source,
        failures,
    )


    check(
        "awayTeamName prop present",
        "awayTeamName: string"
        in
        card_source,
        failures,
    )


    check(
        "Home label present",
        ">Home<"
        in
        re.sub(
            r"\s+",
            "",
            card_source,
        ),
        failures,
    )


    check(
        "Away label present",
        ">Away<"
        in
        re.sub(
            r"\s+",
            "",
            card_source,
        ),
        failures,
    )


    check(
        "Home team rendered",
        "{homeTeamName}"
        in
        card_source,
        failures,
    )


    check(
        "Away team rendered",
        "{awayTeamName}"
        in
        card_source,
        failures,
    )


    check(
        "Accessible match label",
        (
            'aria-label={`${homeTeamName} vs '
            '${awayTeamName}`}'
        )
        in
        card_source,
        failures,
    )


    print(
        "\n5. STAGE 10.4.4 CONTRACT"
    )


    check(
        "Kickoff stage exact",
        kickoff_contract.get(
            "stage"
        )
        ==
        "10.4.4",
        failures,
    )


    check(
        "Kickoff contract LOCKED",
        kickoff_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )


    check(
        "Kickoff field exact",
        kickoff_contract.get(
            "kickoff_field"
        )
        ==
        "kickoffUtc",
        failures,
    )


    kickoff_transition = (
        kickoff_contract.get(
            "transition",
            {},
        )
    )


    check(
        "10.4.4 starts from 10.4.3 output",
        kickoff_transition.get(
            "match_card_before_kickoff_sha256"
        )
        ==
        identity_contract.get(
            "match_card_after_identity_sha256"
        ),
        failures,
    )


    check(
        "Current MatchCard equals 10.4.4 output",
        kickoff_contract.get(
            "match_card_after_kickoff_sha256"
        )
        ==
        sha256_file(
            MATCH_CARD_FILE
        ),
        failures,
    )


    check(
        "Kickoff formatter SHA current",
        kickoff_contract.get(
            "formatter_sha256"
        )
        ==
        sha256_file(
            FORMATTER_FILE
        ),
        failures,
    )


    print(
        "\n6. KICKOFF SOURCE"
    )


    check(
        "kickoffUtc prop present",
        "kickoffUtc: string"
        in
        card_source,
        failures,
    )


    check(
        "Formatter imported",
        "formatKickoffUtc"
        in
        card_source,
        failures,
    )


    check(
        "Semantic time element present",
        (
            "<time"
            in
            card_source
            and
            "</time>"
            in
            card_source
        ),
        failures,
    )


    check(
        "time dateTime uses raw timestamp",
        "dateTime={kickoffUtc}"
        in
        card_source,
        failures,
    )


    check(
        "Kickoff label rendered",
        "{kickoffLabel} UTC"
        in
        card_source,
        failures,
    )


    print(
        "\n7. FORMATTER IMPLEMENTATION"
    )


    check(
        "Intl.DateTimeFormat used",
        "new Intl.DateTimeFormat"
        in
        formatter_source,
        failures,
    )


    check(
        "Locale en-GB",
        '"en-GB"'
        in
        formatter_source,
        failures,
    )


    check(
        "UTC timezone explicit",
        'timeZone: "UTC"'
        in
        formatter_source,
        failures,
    )


    check(
        "Native Date used",
        "new Date(value)"
        in
        formatter_source,
        failures,
    )


    check(
        "Invalid date detection used",
        "Number.isNaN"
        in
        formatter_source,
        failures,
    )


    check(
        "Invalid timestamps fail closed",
        "throw new RangeError"
        in
        formatter_source,
        failures,
    )


    check(
        "No manual date string assembly",
        re.search(
            (
                r"getUTC(?:Date|Month|FullYear|Hours|Minutes)"
            ),
            formatter_source,
        )
        is None,
        failures,
    )


    print(
        "\n8. ROUTE / LOADER PRESERVATION"
    )


    protected_pages = (
        kickoff_contract
        .get(
            "protected_state",
            {},
        )
        .get(
            "route_page_identity",
            {},
        )
    )


    check(
        "Route pages unchanged",
        protected_pages
        ==
        current_route_pages(),
        failures,
    )


    check(
        "Dashboard loader unchanged",
        kickoff_contract
        .get(
            "protected_state",
            {},
        )
        .get(
            "loader_sha256"
        )
        ==
        sha256_file(
            LOADER_FILE
        )
        ==
        loader_contract.get(
            "source_sha256"
        ),
        failures,
    )


    print(
        "\n9. LATER FEATURES NOT IMPLEMENTED EARLY"
    )


    forbidden_later_terms = [
        "stage7_prob_home_win",
        "stage7_prob_draw",
        "stage7_prob_away_win",
        "stage7_predicted_label",
        "confidence_band",
        "uncertainty_band",
        "context_alignment",
        "explanation_summary",
        "/matches/",
    ]


    for term in forbidden_later_terms:

        check(
            f"MatchCard excludes: {term}",
            term
            not in
            card_source,
            failures,
        )


    print(
        "\n10. PRESENTATION-ONLY SAFETY"
    )


    combined_source = (
        card_source
        +
        "\n"
        +
        formatter_source
    )


    check(
        "No fetch",
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
            f"Sources exclude: {term}",
            term.lower()
            not in
            combined_source.lower(),
            failures,
        )


    check(
        "No client component directive",
        (
            '"use client"'
            not in
            combined_source
            and
            "'use client'"
            not in
            combined_source
        ),
        failures,
    )


    print(
        "\n11. DEPENDENCY FRESHNESS"
    )


    verify_dependencies(
        identity_contract,
        "10.4.3",
        failures,
    )


    verify_dependencies(
        kickoff_contract,
        "10.4.4",
        failures,
    )


    print(
        "\n12. TYPESCRIPT COMPILER"
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
        "\n13. NO PREMATURE PROMOTION"
    )


    identity_promotion = (
        identity_contract.get(
            "promotion",
            {},
        )
    )

    kickoff_promotion = (
        kickoff_contract.get(
            "promotion",
            {},
        )
    )


    check(
        "10.4.3 did not self-promote",
        identity_promotion.get(
            "stage10_4_3_complete"
        )
        is False,
        failures,
    )


    check(
        "10.4.4 did not self-promote",
        kickoff_promotion.get(
            "stage10_4_4_complete"
        )
        is False,
        failures,
    )


    check(
        "Stage 10.4 remains incomplete",
        (
            identity_promotion.get(
                "stage10_4_complete"
            )
            is False
            and
            kickoff_promotion.get(
                "stage10_4_complete"
            )
            is False
        ),
        failures,
    )


    check(
        "Stage 10 remains incomplete",
        (
            identity_promotion.get(
                "stage10_complete"
            )
            is False
            and
            kickoff_promotion.get(
                "stage10_complete"
            )
            is False
        ),
        failures,
    )


    print(
        "\n14. SAVE VERIFICATION EVIDENCE"
    )


    passed = (
        len(failures)
        ==
        0
    )


    if passed:

        evidence = {
            "stage":
                "10.4.3-10.4.4",

            "name":
                (
                    "MATCH_IDENTITY_AND_"
                    "KICKOFF_VERIFICATION"
                ),

            "status":
                "PASS",

            "stage_10_4_3_complete":
                True,

            "stage_10_4_4_complete":
                True,

            "match_identity":
                "LOCKED_AND_VERIFIED",

            "match_kickoff":
                "LOCKED_AND_VERIFIED",

            "kickoff_format": {
                "timezone":
                    "UTC",

                "locale":
                    "en-GB",

                "library":
                    "Intl.DateTimeFormat",

                "invalid_timestamp_policy":
                    "FAIL_CLOSED",
            },

            "safety": {
                "route_pages_modified":
                    False,

                "dashboard_loader_modified":
                    False,

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
            },

            "typescript_compiler":
                "PASS",

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "stage10_ready_for_10_4_5":
                True,

            "stage10_4_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.4.5",

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
            "STAGE 10.4.3: PASS"
        )

        print(
            "MATCH IDENTITY: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.4.4: PASS"
        )

        print(
            "MATCH KICKOFF: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.4.5"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.4.3 / 10.4.4: FAIL"
        )

        print()

        print(
            "Failures:"
        )

        for failure in failures:
            print(
                f"  - {failure}"
            )


    print("=" * 72)


    sys.exit(
        0
        if passed
        else 1
    )


if __name__ == "__main__":
    main()
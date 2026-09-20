from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
DOCS = ROOT / "docs" / "stage10"

FRONTEND_DATA = (
    ROOT
    / "data"
    / "processed"
    / "frontend"
)


PREVIOUS_FILE = (
    FRONTEND_DATA
    / "stage10_8_1_10_8_4_verification.json"
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


CONNECTION_ERROR_STATE_FILE = (
    FRONTEND
    / "components"
    / "runtime"
    / "connection-error-state.tsx"
)

EMPTY_FIXTURES_STATE_FILE = (
    FRONTEND
    / "components"
    / "runtime"
    / "empty-fixtures-state.tsx"
)


ERROR_STATE_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "error-state.tsx"
)

EMPTY_STATE_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "empty-state.tsx"
)

FRESHNESS_INDICATOR_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "freshness-indicator.tsx"
)


API_CLIENT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "client.ts"
)

RESULT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "result.ts"
)

UPCOMING_LOADER_FILE = (
    FRONTEND
    / "lib"
    / "dashboard"
    / "load-upcoming-matches.ts"
)

TEAM_LOADER_FILE = (
    FRONTEND
    / "lib"
    / "teams"
    / "load-team-intelligence.ts"
)

TEAM_CONTEXT_LOADER_FILE = (
    FRONTEND
    / "lib"
    / "teams"
    / "load-team-context.ts"
)


NOT_READY_CONTRACT_FILE = (
    DOCS
    / "frontend_runtime_not_ready_ux_contract.json"
)

ERROR_STATE_CONTRACT_FILE = (
    DOCS
    / "frontend_error_state_contract.json"
)

EMPTY_STATE_CONTRACT_FILE = (
    DOCS
    / "frontend_empty_state_contract.json"
)

FRESHNESS_CONTRACT_FILE = (
    DOCS
    / "frontend_freshness_indicator_contract.json"
)


CONNECTION_ERROR_CONTRACT_FILE = (
    DOCS
    / "frontend_runtime_connection_error_contract.json"
)

EMPTY_FIXTURES_CONTRACT_FILE = (
    DOCS
    / "frontend_runtime_empty_fixtures_contract.json"
)

NO_STALE_FALLBACK_CONTRACT_FILE = (
    DOCS
    / "frontend_runtime_no_stale_fallback_contract.json"
)

FAILED_REFRESH_CONTRACT_FILE = (
    DOCS
    / "frontend_runtime_failed_refresh_isolation_contract.json"
)


CONNECTION_ERROR_STATE_SOURCE = '''import {
  ErrorState,
} from "../ui/error-state";

import {
  FreshnessIndicator,
} from "../ui/freshness-indicator";


type ConnectionErrorStateProps =
  Readonly<{
    httpStatus:
      number | null;

    resource:
      string;
  }>;


export function ConnectionErrorState({
  httpStatus,
  resource,
}: ConnectionErrorStateProps) {

  return (
    <section
      data-fixtureiq-component="connection-error-state"
      data-fixtureiq-runtime-state="CONNECTION_ERROR"
    >
      <ErrorState
        title={`${resource} cannot be reached`}
        message={
          "FixtureIQ could not reach the backend service. "
          +
          "No older result is being shown."
        }
      />

      <div className="mt-4">
        <FreshnessIndicator
          state="CONNECTION_ERROR"
          httpStatus={
            httpStatus
          }
        />
      </div>
    </section>
  );
}
'''


EMPTY_FIXTURES_STATE_SOURCE = '''import {
  EmptyState,
} from "../ui/empty-state";


export function EmptyFixturesState() {

  return (
    <div
      data-fixtureiq-component="empty-fixtures-state"
      data-fixtureiq-runtime-state="EMPTY_FIXTURES"
    >
      <EmptyState
        title="No upcoming matches"
        message={
          "FixtureIQ received a ready response with no upcoming fixtures. "
          +
          "No previous fixture list is being reused."
        }
      />
    </div>
  );
}
'''


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

        payload = json.load(
            file
        )

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

    return load_json(
        path
    )


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

            digest.update(
                chunk
            )

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
        .replace(
            "\\",
            "/",
        )
    )


def identity(
    path: Path,
) -> dict:

    return {
        "sha256":
            sha256_file(
                path
            )
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

    temporary.replace(
        path
    )


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


def ensure_component_identity(
    source: Path,
    contract: Path,
) -> None:

    if not source.exists():
        raise RuntimeError(
            f"Missing component: {source}"
        )

    payload = load_json(
        contract
    )

    expected = payload.get(
        "component_sha256"
    )

    if (
        not isinstance(
            expected,
            str,
        )
        or
        expected
        !=
        sha256_file(
            source
        )
    ):
        raise RuntimeError(
            (
                "Previously verified component changed: "
                f"{relative(source)}"
            )
        )


def prepend_import(
    source: str,
    component: str,
    import_path: str,
) -> str:

    token = (
        "import {\n"
        f"  {component},\n"
        f'}} from "{import_path}";'
    )

    if token in source:
        return source

    return (
        token
        +
        "\n\n"
        +
        source
    )


def add_primary_connection_error_branch(
    source: str,
    resource: str,
) -> str:

    existing_branch = re.search(
        (
            r"<ConnectionErrorState"
            r"[\s\S]*?"
            r'resource="'
            +
            re.escape(
                resource
            )
            +
            r'"'
            r"[\s\S]*?/>"
        ),
        source,
    )


    if existing_branch is not None:
        return source


    pattern = re.compile(
        r"""
        (?P<indent>^[ \t]*)
        if
        \s*
        \(
        \s*
        result\.state
        \s*
        !==
        \s*
        "READY"
        \s*
        \)
        \s*
        \{
        """,
        re.MULTILINE
        |
        re.VERBOSE,
    )


    match = pattern.search(
        source
    )


    if match is None:

        raise RuntimeError(
            (
                "Could not find primary generic "
                f"non-READY branch for {resource}."
            )
        )


    indent = match.group(
        "indent"
    )


    branch = (
        f'{indent}if (\n'
        f'{indent}  result.state ===\n'
        f'{indent}  "CONNECTION_ERROR"\n'
        f'{indent}) {{\n\n'
        f'{indent}  return (\n'
        f'{indent}    <ConnectionErrorState\n'
        f'{indent}      httpStatus={{\n'
        f'{indent}        result.status\n'
        f'{indent}      }}\n'
        f'{indent}      resource="{resource}"\n'
        f'{indent}    />\n'
        f'{indent}  );\n'
        f'{indent}}}\n\n\n'
    )


    return (
        source[
            :match.start()
        ]
        +
        branch
        +
        source[
            match.start():
        ]
    )


def add_team_context_connection_error_branch(
    source: str,
) -> str:

    if (
        'resource="Team context"'
        in source
        and
        "ConnectionErrorState"
        in source
        and
        "standingsResult.state ==="
        in source
        and
        '"CONNECTION_ERROR"'
        in source
    ):
        return source


    pattern = re.compile(
        r'''
        (?P<indent>^[ \t]*)
        if
        \s*
        \(
        \s*
        standingsResult\.state
        \s*
        !==
        \s*
        "READY"
        \s*
        \|\|
        \s*
        formResult\.state
        \s*
        !==
        \s*
        "READY"
        \s*
        \)
        \s*
        \{
        ''',
        re.MULTILINE
        |
        re.VERBOSE,
    )


    match = pattern.search(
        source
    )


    if match is None:

        raise RuntimeError(
            (
                "Could not find Team context "
                "generic non-READY branch."
            )
        )


    indent = match.group(
        "indent"
    )


    branch = (
        f'{indent}if (\n'
        f'{indent}  standingsResult.state ===\n'
        f'{indent}  "CONNECTION_ERROR"\n'
        f'{indent}  ||\n'
        f'{indent}  formResult.state ===\n'
        f'{indent}  "CONNECTION_ERROR"\n'
        f'{indent}) {{\n\n'
        f'{indent}  return (\n'
        f'{indent}    <ConnectionErrorState\n'
        f'{indent}      httpStatus={{\n'
        f'{indent}        standingsResult.state === "CONNECTION_ERROR"\n'
        f'{indent}          ? standingsResult.status\n'
        f'{indent}          : formResult.state === "CONNECTION_ERROR"\n'
        f'{indent}            ? formResult.status\n'
        f'{indent}            : null\n'
        f'{indent}      }}\n'
        f'{indent}      resource="Team context"\n'
        f'{indent}    />\n'
        f'{indent}  );\n'
        f'{indent}}}\n\n\n'
    )


    return (
        source[
            :match.start()
        ]
        +
        branch
        +
        source[
            match.start():
        ]
    )


def find_matching_brace(
    source: str,
    opening_index: int,
) -> int:

    depth = 0

    quote: str | None = None
    escaped = False


    for index in range(
        opening_index,
        len(
            source
        ),
    ):

        character = source[
            index
        ]


        if quote is not None:

            if escaped:
                escaped = False
                continue

            if character == "\\":
                escaped = True
                continue

            if character == quote:
                quote = None

            continue


        if character in {
            '"',
            "'",
            "`",
        }:

            quote = character
            continue


        if character == "{":
            depth += 1

        elif character == "}":

            depth -= 1

            if depth == 0:
                return index


    raise RuntimeError(
        "Could not match block brace."
    )


def replace_root_empty_branch(
    source: str,
) -> str:

    if (
        "<EmptyFixturesState"
        in source
    ):
        return source


    pattern = re.compile(
        r'''
        (?P<indent>^[ \t]*)
        if
        \s*
        \(
        \s*
        (?P<variable>[A-Za-z_$][A-Za-z0-9_$]*)
        \s*
        \.
        \s*
        length
        \s*
        ===
        \s*
        0
        \s*
        \)
        \s*
        \{
        ''',
        re.MULTILINE
        |
        re.VERBOSE,
    )


    match = pattern.search(
        source
    )


    if match is None:

        raise RuntimeError(
            (
                "Could not find dashboard READY "
                "zero-fixture branch."
            )
        )


    opening_index = (
        match.end()
        -
        1
    )

    closing_index = find_matching_brace(
        source,
        opening_index,
    )

    indent = match.group(
        "indent"
    )

    variable = match.group(
        "variable"
    )


    replacement = (
        f'{indent}if (\n'
        f'{indent}  {variable}.length ===\n'
        f'{indent}  0\n'
        f'{indent}) {{\n\n'
        f'{indent}  return (\n'
        f'{indent}    <EmptyFixturesState />\n'
        f'{indent}  );\n'
        f'{indent}}}'
    )


    return (
        source[
            :match.start()
        ]
        +
        replacement
        +
        source[
            closing_index
            +
            1:
        ]
    )


def check_failure_before_data(
    source: str,
    label: str,
) -> None:

    result_assignment = re.search(
        r"""
        \b
        (?:const|let)
        \s+
        result
        \s*
        =
        \s*
        await
        \b
        """,
        source,
        re.VERBOSE,
    )


    if result_assignment is None:

        raise RuntimeError(
            (
                f"{label}: awaited result assignment "
                "not found."
            )
        )


    request_scope = source[
        result_assignment.start():
    ]


    data_position = request_scope.find(
        "result.data"
    )

    connection_position = request_scope.find(
        '"CONNECTION_ERROR"'
    )

    not_ready_position = request_scope.find(
        '"NOT_READY"'
    )


    if data_position == -1:

        raise RuntimeError(
            f"{label}: result.data not found."
        )


    if (
        connection_position == -1
        or
        connection_position
        >
        data_position
    ):

        raise RuntimeError(
            (
                f"{label}: CONNECTION_ERROR "
                "is not handled before data extraction."
            )
        )


    if (
        not_ready_position == -1
        or
        not_ready_position
        >
        data_position
    ):

        raise RuntimeError(
            (
                f"{label}: NOT_READY "
                "is not handled before data extraction."
            )
        )


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.8.5 - 10.8.8"
    )

    print(
        "NETWORK + EMPTY + NO-STALE + FAILED-REFRESH ISOLATION BUILD"
    )

    print("=" * 72)


    previous = load_json(
        PREVIOUS_FILE
    )


    if (
        previous.get(
            "status"
        )
        !=
        "PASS"
    ):

        raise RuntimeError(
            "10.8.1-10.8.4 verification is not PASS."
        )


    for key in [
        "stage_10_8_1_complete",
        "stage_10_8_2_complete",
        "stage_10_8_3_complete",
        "stage_10_8_4_complete",
    ]:

        if (
            previous.get(
                key
            )
            is not True
        ):

            raise RuntimeError(
                f"Previous stage flag incomplete: {key}"
            )


    if (
        previous.get(
            "stage10_ready_for_10_8_5"
        )
        is not True
    ):

        raise RuntimeError(
            "10.8.4 did not authorize 10.8.5."
        )


    required = [
        ROOT_PAGE,
        MATCH_PAGE,
        TEAM_PAGE,
        ERROR_STATE_FILE,
        EMPTY_STATE_FILE,
        FRESHNESS_INDICATOR_FILE,
        API_CLIENT_FILE,
        RESULT_FILE,
        UPCOMING_LOADER_FILE,
        TEAM_LOADER_FILE,
        TEAM_CONTEXT_LOADER_FILE,
        NOT_READY_CONTRACT_FILE,
        ERROR_STATE_CONTRACT_FILE,
        EMPTY_STATE_CONTRACT_FILE,
        FRESHNESS_CONTRACT_FILE,
    ]


    for path in required:

        if not path.exists():

            raise RuntimeError(
                f"Missing source: {path}"
            )


    ensure_component_identity(
        ERROR_STATE_FILE,
        ERROR_STATE_CONTRACT_FILE,
    )

    ensure_component_identity(
        EMPTY_STATE_FILE,
        EMPTY_STATE_CONTRACT_FILE,
    )

    ensure_component_identity(
        FRESHNESS_INDICATOR_FILE,
        FRESHNESS_CONTRACT_FILE,
    )


    not_ready_contract = load_json(
        NOT_READY_CONTRACT_FILE
    )


    route_contract_pairs = [
        (
            ROOT_PAGE,
            "root_page_after_sha256",
        ),
        (
            MATCH_PAGE,
            "match_page_after_sha256",
        ),
        (
            TEAM_PAGE,
            "team_page_after_sha256",
        ),
    ]


    baseline_route_sha: dict[
        Path,
        str,
    ] = {}


    partial_markers = {
        ROOT_PAGE: (
            "ConnectionErrorState",
            "EmptyFixturesState",
        ),

        MATCH_PAGE: (
            "ConnectionErrorState",
        ),

        TEAM_PAGE: (
            "ConnectionErrorState",
        ),
    }


    for path, key in route_contract_pairs:

        expected = not_ready_contract.get(
            key
        )


        if not isinstance(
            expected,
            str,
        ):

            raise RuntimeError(
                (
                    "Missing verified Stage 10.8.4 "
                    f"route SHA: {key}"
                )
            )


        baseline_route_sha[
            path
        ] = expected


        current = sha256_file(
            path
        )


        if current == expected:
            continue


        source = path.read_text(
            encoding="utf-8"
        )


        markers = partial_markers[
            path
        ]


        if not all(
            marker in source
            for marker in markers
        ):

            raise RuntimeError(
                (
                    "Route changed outside the known "
                    "partial Stage 10.8.5 recovery state: "
                    f"{relative(path)}"
                )
            )


        print(
            (
                "RECOVERY: accepting known partial "
                "Stage 10.8.5 route state: "
                f"{relative(path)}"
            )
        )


    result_source = (
        RESULT_FILE.read_text(
            encoding="utf-8"
        )
    )


    if (
        '"CONNECTION_ERROR"'
        not in
        result_source
    ):

        raise RuntimeError(
            (
                "ApiRequestResult does not expose "
                "CONNECTION_ERROR."
            )
        )


    client_source = (
        API_CLIENT_FILE.read_text(
            encoding="utf-8"
        )
    )


    if (
        re.search(
            r'''cache\s*:\s*["']no-store["']''',
            client_source,
        )
        is None
    ):

        raise RuntimeError(
            (
                "HTTP client is not locked "
                "to cache: no-store."
            )
        )


    connection_existing = optional_json(
        CONNECTION_ERROR_CONTRACT_FILE
    )


    if (
        CONNECTION_ERROR_STATE_FILE.exists()
        and
        connection_existing is None
        and
        CONNECTION_ERROR_STATE_FILE.read_text(
            encoding="utf-8"
        )
        !=
        CONNECTION_ERROR_STATE_SOURCE
    ):

        raise RuntimeError(
            (
                "connection-error-state.tsx exists "
                "without its Stage 10.8.5 contract "
                "and does not match the intended source."
            )
        )


    empty_existing = optional_json(
        EMPTY_FIXTURES_CONTRACT_FILE
    )


    if (
        EMPTY_FIXTURES_STATE_FILE.exists()
        and
        empty_existing is None
        and
        EMPTY_FIXTURES_STATE_FILE.read_text(
            encoding="utf-8"
        )
        !=
        EMPTY_FIXTURES_STATE_SOURCE
    ):

        raise RuntimeError(
            (
                "empty-fixtures-state.tsx exists "
                "without its Stage 10.8.6 contract "
                "and does not match the intended source."
            )
        )


    root_before = baseline_route_sha[
        ROOT_PAGE
    ]

    match_before = baseline_route_sha[
        MATCH_PAGE
    ]

    team_before = baseline_route_sha[
        TEAM_PAGE
    ]


    save_text_atomic(
        CONNECTION_ERROR_STATE_FILE,
        CONNECTION_ERROR_STATE_SOURCE,
    )

    save_text_atomic(
        EMPTY_FIXTURES_STATE_FILE,
        EMPTY_FIXTURES_STATE_SOURCE,
    )


    # --------------------------------------------------------
    # 10.8.5 — CONNECTION_ERROR
    # --------------------------------------------------------

    root_source = (
        ROOT_PAGE.read_text(
            encoding="utf-8"
        )
    )

    root_source = prepend_import(
        root_source,
        "ConnectionErrorState",
        "../components/runtime/connection-error-state",
    )

    root_source = add_primary_connection_error_branch(
        root_source,
        "Upcoming match intelligence",
    )


    match_source = (
        MATCH_PAGE.read_text(
            encoding="utf-8"
        )
    )

    match_source = prepend_import(
        match_source,
        "ConnectionErrorState",
        "../../../components/runtime/connection-error-state",
    )

    match_source = add_primary_connection_error_branch(
        match_source,
        "Match intelligence",
    )


    team_source = (
        TEAM_PAGE.read_text(
            encoding="utf-8"
        )
    )

    team_source = prepend_import(
        team_source,
        "ConnectionErrorState",
        "../../../components/runtime/connection-error-state",
    )

    team_source = add_primary_connection_error_branch(
        team_source,
        "Team intelligence",
    )

    team_source = add_team_context_connection_error_branch(
        team_source,
    )


    # --------------------------------------------------------
    # 10.8.6 — READY + ZERO FIXTURES
    # --------------------------------------------------------

    root_source = prepend_import(
        root_source,
        "EmptyFixturesState",
        "../components/runtime/empty-fixtures-state",
    )

    root_source = replace_root_empty_branch(
        root_source,
    )


    save_text_atomic(
        ROOT_PAGE,
        root_source,
    )

    save_text_atomic(
        MATCH_PAGE,
        match_source,
    )

    save_text_atomic(
        TEAM_PAGE,
        team_source,
    )


    # --------------------------------------------------------
    # Validate fresh-only architecture before locking 10.8.7/8
    # --------------------------------------------------------

    for label, path in [
        (
            "dashboard",
            ROOT_PAGE,
        ),
        (
            "match",
            MATCH_PAGE,
        ),
        (
            "team",
            TEAM_PAGE,
        ),
    ]:

        source = path.read_text(
            encoding="utf-8"
        )


        if (
            '"force-dynamic"'
            not in
            source
        ):

            raise RuntimeError(
                f"{label} route is not force-dynamic."
            )


        for forbidden in [
            '"use client"',
            "'use client'",
            "useState(",
            "useEffect(",
            "localStorage",
            "sessionStorage",
            "previousData",
            "previousResponse",
            "fallbackData",
            "staleData",
            "unstable_cache",
        ]:

            if (
                forbidden
                in
                source
            ):

                raise RuntimeError(
                    (
                        f"{label} route contains "
                        f"stale-state mechanism: {forbidden}"
                    )
                )


    check_failure_before_data(
        ROOT_PAGE.read_text(
            encoding="utf-8"
        ),
        "dashboard",
    )

    check_failure_before_data(
        MATCH_PAGE.read_text(
            encoding="utf-8"
        ),
        "match",
    )

    check_failure_before_data(
        TEAM_PAGE.read_text(
            encoding="utf-8"
        ),
        "team",
    )


    root_after = sha256_file(
        ROOT_PAGE
    )

    match_after = sha256_file(
        MATCH_PAGE
    )

    team_after = sha256_file(
        TEAM_PAGE
    )


    connection_contract = {
        "stage":
            "10.8.5",

        "version":
            "1.0.0",

        "name":
            "NETWORK_UNAVAILABLE_UX",

        "status":
            "LOCKED",

        "mapped_state":
            "CONNECTION_ERROR",

        "component":
            "ConnectionErrorState",

        "source":
            relative(
                CONNECTION_ERROR_STATE_FILE
            ),

        "behavior": {
            "dashboard_explicit":
                True,

            "match_explicit":
                True,

            "team_explicit":
                True,

            "team_context_explicit":
                True,

            "old_data_displayed":
                False,

            "stale_fallback":
                False,

            "retry_logic":
                False,
        },

        "component_sha256":
            sha256_file(
                CONNECTION_ERROR_STATE_FILE
            ),

        "root_page_before_sha256":
            root_before,

        "match_page_before_sha256":
            match_before,

        "team_page_before_sha256":
            team_before,

        "root_page_after_sha256":
            root_after,

        "match_page_after_sha256":
            match_after,

        "team_page_after_sha256":
            team_after,

        "dependency_identity": {
            relative(
                PREVIOUS_FILE
            ):
                identity(
                    PREVIOUS_FILE
                ),

            relative(
                RESULT_FILE
            ):
                identity(
                    RESULT_FILE
                ),

            relative(
                ERROR_STATE_CONTRACT_FILE
            ):
                identity(
                    ERROR_STATE_CONTRACT_FILE
                ),

            relative(
                FRESHNESS_CONTRACT_FILE
            ):
                identity(
                    FRESHNESS_CONTRACT_FILE
                ),
        },

        "promotion": {
            "stage10_8_5_complete":
                False,

            "stage10_8_complete":
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
        CONNECTION_ERROR_CONTRACT_FILE,
        connection_contract,
    )


    empty_contract = {
        "stage":
            "10.8.6",

        "version":
            "1.0.0",

        "name":
            "EMPTY_UPCOMING_FIXTURES_UX",

        "status":
            "LOCKED",

        "required_parent_state":
            "READY",

        "component":
            "EmptyFixturesState",

        "source":
            relative(
                EMPTY_FIXTURES_STATE_FILE
            ),

        "behavior": {
            "zero_records_only":
                True,

            "empty_is_not_error":
                True,

            "old_fixture_list_reused":
                False,

            "fallback_fixture_list":
                False,

            "synthetic_fixture":
                False,
        },

        "component_sha256":
            sha256_file(
                EMPTY_FIXTURES_STATE_FILE
            ),

        "root_page_sha256":
            root_after,

        "dependency_identity": {
            relative(
                CONNECTION_ERROR_CONTRACT_FILE
            ):
                identity(
                    CONNECTION_ERROR_CONTRACT_FILE
                ),

            relative(
                EMPTY_STATE_CONTRACT_FILE
            ):
                identity(
                    EMPTY_STATE_CONTRACT_FILE
                ),
        },

        "promotion": {
            "stage10_8_6_complete":
                False,

            "stage10_8_complete":
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
        EMPTY_FIXTURES_CONTRACT_FILE,
        empty_contract,
    )


    no_stale_contract = {
        "stage":
            "10.8.7",

        "version":
            "1.0.0",

        "name":
            "NO_STALE_FALLBACK_POLICY",

        "status":
            "LOCKED",

        "policy":
            "CURRENT_REQUEST_ONLY_FAIL_CLOSED",

        "http_client": {
            "source":
                relative(
                    API_CLIENT_FILE
                ),

            "cache_mode":
                "no-store",

            "sha256":
                sha256_file(
                    API_CLIENT_FILE
                ),
        },

        "routes": {
            "/":
                root_after,

            "/matches/[fixtureId]":
                match_after,

            "/teams/[teamName]":
                team_after,
        },

        "loaders": {
            relative(
                UPCOMING_LOADER_FILE
            ):
                sha256_file(
                    UPCOMING_LOADER_FILE
                ),

            relative(
                TEAM_LOADER_FILE
            ):
                sha256_file(
                    TEAM_LOADER_FILE
                ),

            relative(
                TEAM_CONTEXT_LOADER_FILE
            ):
                sha256_file(
                    TEAM_CONTEXT_LOADER_FILE
                ),
        },

        "behavior": {
            "force_dynamic_routes":
                True,

            "browser_storage":
                False,

            "module_response_cache":
                False,

            "previous_response_reuse":
                False,

            "fallback_data":
                False,

            "failed_request_contains_ready_data":
                False,

            "stale_fallback":
                False,
        },

        "dependency_identity": {
            relative(
                EMPTY_FIXTURES_CONTRACT_FILE
            ):
                identity(
                    EMPTY_FIXTURES_CONTRACT_FILE
                ),

            relative(
                API_CLIENT_FILE
            ):
                identity(
                    API_CLIENT_FILE
                ),

            relative(
                RESULT_FILE
            ):
                identity(
                    RESULT_FILE
                ),
        },

        "promotion": {
            "stage10_8_7_complete":
                False,

            "stage10_8_complete":
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
        NO_STALE_FALLBACK_CONTRACT_FILE,
        no_stale_contract,
    )


    failed_refresh_contract = {
        "stage":
            "10.8.8",

        "version":
            "1.0.0",

        "name":
            "FAILED_REFRESH_RESULT_ISOLATION",

        "status":
            "LOCKED",

        "policy":
            "FAILURE_REPLACES_PRIOR_READY_VIEW",

        "routes": {
            "/": {
                "sha256":
                    root_after,

                "failure_before_result_data":
                    True,
            },

            "/matches/[fixtureId]": {
                "sha256":
                    match_after,

                "failure_before_result_data":
                    True,
            },

            "/teams/[teamName]": {
                "sha256":
                    team_after,

                "failure_before_result_data":
                    True,
            },
        },

        "behavior": {
            "failed_refresh_keeps_old_match":
                False,

            "failed_refresh_keeps_old_fixture_list":
                False,

            "failed_refresh_keeps_old_team_data":
                False,

            "client_state_retention":
                False,

            "browser_storage_retention":
                False,

            "stale_fallback":
                False,

            "current_request_failure_rendered":
                True,
        },

        "dependency_identity": {
            relative(
                NO_STALE_FALLBACK_CONTRACT_FILE
            ):
                identity(
                    NO_STALE_FALLBACK_CONTRACT_FILE
                ),

            relative(
                CONNECTION_ERROR_CONTRACT_FILE
            ):
                identity(
                    CONNECTION_ERROR_CONTRACT_FILE
                ),

            relative(
                NOT_READY_CONTRACT_FILE
            ):
                identity(
                    NOT_READY_CONTRACT_FILE
                ),
        },

        "promotion": {
            "stage10_8_8_complete":
                False,

            "stage10_8_complete":
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
        FAILED_REFRESH_CONTRACT_FILE,
        failed_refresh_contract,
    )


    print()

    print(
        "Runtime components:"
    )

    print(
        f"  {relative(CONNECTION_ERROR_STATE_FILE)}"
    )

    print(
        f"  {relative(EMPTY_FIXTURES_STATE_FILE)}"
    )

    print()

    print("=" * 72)

    print(
        "STAGE 10.8.5 NETWORK UNAVAILABLE: BUILT"
    )

    print(
        "STAGE 10.8.6 EMPTY FIXTURES: BUILT"
    )

    print(
        "STAGE 10.8.7 NO STALE FALLBACK: LOCKED"
    )

    print(
        "STAGE 10.8.8 FAILED REFRESH ISOLATION: LOCKED"
    )

    print(
        "VERIFICATION STILL REQUIRED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
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
    / "stage10_7_final_verification.json"
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


APP_LOADING_FILE = (
    FRONTEND
    / "app"
    / "loading.tsx"
)

MATCH_LOADING_FILE = (
    FRONTEND
    / "app"
    / "matches"
    / "[fixtureId]"
    / "loading.tsx"
)

TEAM_LOADING_FILE = (
    FRONTEND
    / "app"
    / "teams"
    / "[teamName]"
    / "loading.tsx"
)


GLOBAL_NOT_FOUND_FILE = (
    FRONTEND
    / "app"
    / "not-found.tsx"
)

MATCH_NOT_FOUND_FILE = (
    FRONTEND
    / "app"
    / "matches"
    / "[fixtureId]"
    / "not-found.tsx"
)

TEAM_NOT_FOUND_FILE = (
    FRONTEND
    / "app"
    / "teams"
    / "[teamName]"
    / "not-found.tsx"
)


READY_STATE_FILE = (
    FRONTEND
    / "components"
    / "runtime"
    / "ready-state.tsx"
)

NOT_READY_STATE_FILE = (
    FRONTEND
    / "components"
    / "runtime"
    / "service-not-ready-state.tsx"
)


LOADING_STATE_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "loading-state.tsx"
)

EMPTY_STATE_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "empty-state.tsx"
)

ERROR_STATE_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "error-state.tsx"
)

FRESHNESS_INDICATOR_FILE = (
    FRONTEND
    / "components"
    / "ui"
    / "freshness-indicator.tsx"
)

RESULT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "result.ts"
)


TEAM_UNKNOWN_CONTRACT = (
    DOCS
    / "frontend_team_unknown_team_contract.json"
)

LOADING_STATE_CONTRACT = (
    DOCS
    / "frontend_loading_state_contract.json"
)

EMPTY_STATE_CONTRACT = (
    DOCS
    / "frontend_empty_state_contract.json"
)

ERROR_STATE_CONTRACT = (
    DOCS
    / "frontend_error_state_contract.json"
)

FRESHNESS_CONTRACT = (
    DOCS
    / "frontend_freshness_indicator_contract.json"
)


READY_CONTRACT = (
    DOCS
    / "frontend_runtime_ready_state_contract.json"
)

LOADING_UX_CONTRACT = (
    DOCS
    / "frontend_runtime_loading_ux_contract.json"
)

NOT_FOUND_UX_CONTRACT = (
    DOCS
    / "frontend_runtime_not_found_ux_contract.json"
)

NOT_READY_UX_CONTRACT = (
    DOCS
    / "frontend_runtime_not_ready_ux_contract.json"
)


READY_STATE_SOURCE = '''import type {
  ReactNode,
} from "react";


type ReadyStateProps =
  Readonly<{
    children:
      ReactNode;
  }>;


export function ReadyState({
  children,
}: ReadyStateProps) {

  return (
    <div
      data-fixtureiq-component="ready-state"
      data-fixtureiq-runtime-state="READY"
    >
      {children}
    </div>
  );
}
'''


NOT_READY_STATE_SOURCE = '''import {
  ErrorState,
} from "../ui/error-state";

import {
  FreshnessIndicator,
} from "../ui/freshness-indicator";


type ServiceNotReadyStateProps =
  Readonly<{
    state:
      "NOT_READY";

    httpStatus:
      number | null;

    resource:
      string;
  }>;


export function ServiceNotReadyState({
  state,
  httpStatus,
  resource,
}: ServiceNotReadyStateProps) {

  return (
    <section
      data-fixtureiq-component="service-not-ready-state"
      data-fixtureiq-runtime-state="NOT_READY"
    >
      <ErrorState
        title={`${resource} is temporarily unavailable`}
        message={
          "FixtureIQ does not have a current ready response "
          +
          "for this resource. No older result is being shown."
        }
      />

      <div className="mt-4">
        <FreshnessIndicator
          state={
            state
          }
          httpStatus={
            httpStatus
          }
        />
      </div>
    </section>
  );
}
'''


APP_LOADING_SOURCE = '''import {
  LoadingState,
} from "../components/ui/loading-state";


export default function Loading() {

  return (
    <LoadingState
      label="Loading upcoming match intelligence..."
    />
  );
}
'''


MATCH_LOADING_SOURCE = '''import {
  LoadingState,
} from "../../../components/ui/loading-state";


export default function Loading() {

  return (
    <LoadingState
      label="Loading match intelligence..."
    />
  );
}
'''


TEAM_LOADING_SOURCE = '''import {
  LoadingState,
} from "../../../components/ui/loading-state";


export default function Loading() {

  return (
    <LoadingState
      label="Loading team intelligence..."
    />
  );
}
'''


GLOBAL_NOT_FOUND_SOURCE = '''import Link from "next/link";

import {
  EmptyState,
} from "../components/ui/empty-state";


export default function NotFound() {

  return (
    <EmptyState
      title="Page not found"
      message={
        "The requested FixtureIQ page could not be found."
      }
      action={
        <Link
          href="/"
          className="
            text-sm font-semibold
            text-slate-950
            underline
            underline-offset-4
          "
        >
          Back to upcoming matches
        </Link>
      }
    />
  );
}
'''


MATCH_NOT_FOUND_SOURCE = '''import Link from "next/link";

import {
  EmptyState,
} from "../../../components/ui/empty-state";


export default function MatchNotFound() {

  return (
    <EmptyState
      title="Match not found"
      message={
        "FixtureIQ does not have current intelligence "
        +
        "for this match."
      }
      action={
        <Link
          href="/"
          className="
            text-sm font-semibold
            text-slate-950
            underline
            underline-offset-4
          "
        >
          Back to upcoming matches
        </Link>
      }
    />
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


def ensure_known_component(
    source: Path,
    contract: Path,
) -> None:

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
        sha256_file(
            source
        )
        !=
        expected
    ):
        raise RuntimeError(
            (
                "Previously verified component changed: "
                f"{relative(source)}"
            )
        )


def prepend_import(
    source: str,
    import_path: str,
) -> str:

    token = (
        'import {\n'
        '  ServiceNotReadyState,\n'
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


def add_primary_not_ready_branch(
    source: str,
    resource: str,
) -> str:

    marker = (
        f'resource="{resource}"'
    )

    if marker in source:
        return source


    pattern = re.compile(
        r'''
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
                "Could not find primary non-READY branch "
                f"for {resource}."
            )
        )


    indent = match.group(
        "indent"
    )


    block = (
        f'{indent}if (\n'
        f'{indent}  result.state ===\n'
        f'{indent}  "NOT_READY"\n'
        f'{indent}) {{\n\n'
        f'{indent}  return (\n'
        f'{indent}    <ServiceNotReadyState\n'
        f'{indent}      state="NOT_READY"\n'
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
        block
        +
        source[
            match.start():
        ]
    )


def add_team_context_not_ready_branch(
    source: str,
) -> str:

    marker = (
        'resource="Team context"'
    )

    if marker in source:
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
                "non-READY branch."
            )
        )


    indent = match.group(
        "indent"
    )


    block = (
        f'{indent}if (\n'
        f'{indent}  standingsResult.state ===\n'
        f'{indent}  "NOT_READY"\n'
        f'{indent}  ||\n'
        f'{indent}  formResult.state ===\n'
        f'{indent}  "NOT_READY"\n'
        f'{indent}) {{\n\n'
        f'{indent}  return (\n'
        f'{indent}    <ServiceNotReadyState\n'
        f'{indent}      state="NOT_READY"\n'
        f'{indent}      httpStatus={{\n'
        f'{indent}        standingsResult.state === "NOT_READY"\n'
        f'{indent}          ? standingsResult.status\n'
        f'{indent}          : formResult.state === "NOT_READY"\n'
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
        block
        +
        source[
            match.start():
        ]
    )


def refuse_unknown_generated(
    paths: list[Path],
    contract: dict | None,
    key: str,
) -> None:

    existing = [
        path
        for path in paths
        if path.exists()
    ]


    if not existing:
        return


    if contract is None:
        raise RuntimeError(
            (
                "Stage 10.8 generated files already exist "
                "without matching contract."
            )
        )


    expected = contract.get(
        key,
        {},
    )


    if not isinstance(
        expected,
        dict,
    ):
        raise RuntimeError(
            "Invalid existing Stage 10.8 contract."
        )


    for path in existing:

        declared = expected.get(
            relative(
                path
            )
        )

        if (
            not isinstance(
                declared,
                str,
            )
            or
            declared
            !=
            sha256_file(
                path
            )
        ):
            raise RuntimeError(
                (
                    "Existing Stage 10.8 file does not "
                    f"match contract: {relative(path)}"
                )
            )


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.8.1 - 10.8.4"
    )

    print(
        "READY + LOADING + 404 + NOT_READY UX BUILD"
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
            "Stage 10.7 final verification is not PASS."
        )


    if (
        previous.get(
            "stage10_7_complete"
        )
        is not True
    ):
        raise RuntimeError(
            "Stage 10.7 is not complete."
        )


    if (
        previous.get(
            "stage10_ready_for_10_8_1"
        )
        is not True
    ):
        raise RuntimeError(
            "Stage 10.7 did not authorize 10.8.1."
        )


    required = [
        ROOT_PAGE,
        MATCH_PAGE,
        TEAM_PAGE,
        TEAM_NOT_FOUND_FILE,
        LOADING_STATE_FILE,
        EMPTY_STATE_FILE,
        ERROR_STATE_FILE,
        FRESHNESS_INDICATOR_FILE,
        RESULT_FILE,
        TEAM_UNKNOWN_CONTRACT,
        LOADING_STATE_CONTRACT,
        EMPTY_STATE_CONTRACT,
        ERROR_STATE_CONTRACT,
        FRESHNESS_CONTRACT,
    ]


    for path in required:

        if not path.exists():
            raise RuntimeError(
                f"Missing source: {path}"
            )


    ensure_known_component(
        LOADING_STATE_FILE,
        LOADING_STATE_CONTRACT,
    )

    ensure_known_component(
        EMPTY_STATE_FILE,
        EMPTY_STATE_CONTRACT,
    )

    ensure_known_component(
        ERROR_STATE_FILE,
        ERROR_STATE_CONTRACT,
    )

    ensure_known_component(
        FRESHNESS_INDICATOR_FILE,
        FRESHNESS_CONTRACT,
    )


    team_unknown = load_json(
        TEAM_UNKNOWN_CONTRACT
    )


    if (
        team_unknown.get(
            "not_found_page_sha256"
        )
        !=
        sha256_file(
            TEAM_NOT_FOUND_FILE
        )
    ):
        raise RuntimeError(
            "Verified team 404 page changed."
        )


    result_source = (
        RESULT_FILE.read_text(
            encoding="utf-8"
        )
    )


    for token in [
        '"READY"',
        '"NOT_FOUND"',
        '"NOT_READY"',
        '"CONNECTION_ERROR"',
        "404",
        "503",
    ]:

        if token not in result_source:
            raise RuntimeError(
                (
                    "API result mapping missing "
                    f"required runtime token: {token}"
                )
            )


    match_source = (
        MATCH_PAGE.read_text(
            encoding="utf-8"
        )
    )

    team_source = (
        TEAM_PAGE.read_text(
            encoding="utf-8"
        )
    )


    for label, source in [
        (
            "match route",
            match_source,
        ),
        (
            "team route",
            team_source,
        ),
    ]:

        if (
            '"NOT_FOUND"'
            not in
            source
            or
            "notFound();"
            not in
            source
        ):
            raise RuntimeError(
                (
                    f"{label} does not preserve "
                    "NOT_FOUND -> notFound()."
                )
            )


    final_existing = optional_json(
        NOT_READY_UX_CONTRACT
    )


    generated_loading = [
        APP_LOADING_FILE,
        MATCH_LOADING_FILE,
        TEAM_LOADING_FILE,
    ]

    generated_not_found = [
        GLOBAL_NOT_FOUND_FILE,
        MATCH_NOT_FOUND_FILE,
    ]

    generated_runtime = [
        READY_STATE_FILE,
        NOT_READY_STATE_FILE,
    ]


    if (
        final_existing
        and
        all(
            path.exists()
            for path
            in (
                generated_loading
                +
                generated_not_found
                +
                generated_runtime
            )
        )
        and
        final_existing.get(
            "root_page_after_sha256"
        )
        ==
        sha256_file(
            ROOT_PAGE
        )
        and
        final_existing.get(
            "match_page_after_sha256"
        )
        ==
        sha256_file(
            MATCH_PAGE
        )
        and
        final_existing.get(
            "team_page_after_sha256"
        )
        ==
        sha256_file(
            TEAM_PAGE
        )
    ):

        print()

        print(
            "10.8.1 - 10.8.4 already built."
        )

        print("=" * 72)

        print(
            "STAGE 10.8.1 READY UX: BUILT"
        )

        print(
            "STAGE 10.8.2 LOADING UX: BUILT"
        )

        print(
            "STAGE 10.8.3 404 UX: BUILT"
        )

        print(
            "STAGE 10.8.4 NOT_READY UX: BUILT"
        )

        print(
            "VERIFICATION STILL REQUIRED"
        )

        print("=" * 72)

        return


    refuse_unknown_generated(
        generated_loading,
        optional_json(
            LOADING_UX_CONTRACT
        ),
        "boundary_sha256",
    )

    refuse_unknown_generated(
        generated_not_found,
        optional_json(
            NOT_FOUND_UX_CONTRACT
        ),
        "boundary_sha256",
    )


    root_before = sha256_file(
        ROOT_PAGE
    )

    match_before = sha256_file(
        MATCH_PAGE
    )

    team_before = sha256_file(
        TEAM_PAGE
    )


    save_text_atomic(
        READY_STATE_FILE,
        READY_STATE_SOURCE,
    )

    save_text_atomic(
        NOT_READY_STATE_FILE,
        NOT_READY_STATE_SOURCE,
    )


    save_text_atomic(
        APP_LOADING_FILE,
        APP_LOADING_SOURCE,
    )

    save_text_atomic(
        MATCH_LOADING_FILE,
        MATCH_LOADING_SOURCE,
    )

    save_text_atomic(
        TEAM_LOADING_FILE,
        TEAM_LOADING_SOURCE,
    )


    save_text_atomic(
        GLOBAL_NOT_FOUND_FILE,
        GLOBAL_NOT_FOUND_SOURCE,
    )

    save_text_atomic(
        MATCH_NOT_FOUND_FILE,
        MATCH_NOT_FOUND_SOURCE,
    )


    # --------------------------------------------------------
    # Wire explicit NOT_READY handling into the three
    # already-verified server routes.
    # --------------------------------------------------------

    root_source = (
        ROOT_PAGE.read_text(
            encoding="utf-8"
        )
    )

    root_source = prepend_import(
        root_source,
        "../components/runtime/service-not-ready-state",
    )

    root_source = add_primary_not_ready_branch(
        root_source,
        "Upcoming match intelligence",
    )

    save_text_atomic(
        ROOT_PAGE,
        root_source,
    )


    match_source = (
        MATCH_PAGE.read_text(
            encoding="utf-8"
        )
    )

    match_source = prepend_import(
        match_source,
        "../../../components/runtime/service-not-ready-state",
    )

    match_source = add_primary_not_ready_branch(
        match_source,
        "Match intelligence",
    )

    save_text_atomic(
        MATCH_PAGE,
        match_source,
    )


    team_source = (
        TEAM_PAGE.read_text(
            encoding="utf-8"
        )
    )

    team_source = prepend_import(
        team_source,
        "../../../components/runtime/service-not-ready-state",
    )

    team_source = add_primary_not_ready_branch(
        team_source,
        "Team intelligence",
    )

    team_source = add_team_context_not_ready_branch(
        team_source,
    )

    save_text_atomic(
        TEAM_PAGE,
        team_source,
    )


    ready_contract = {
        "stage":
            "10.8.1",

        "version":
            "1.0.0",

        "name":
            "READY_STATE_UX",

        "status":
            "LOCKED",

        "mapped_state":
            "READY",

        "component":
            "ReadyState",

        "source":
            relative(
                READY_STATE_FILE
            ),

        "behavior": {
            "renders_caller_content":
                True,

            "data_derivation":
                False,

            "prediction_modification":
                False,

            "stale_fallback":
                False,

            "network_logic":
                False,
        },

        "component_sha256":
            sha256_file(
                READY_STATE_FILE
            ),

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
        },

        "promotion": {
            "stage10_8_1_complete":
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
        READY_CONTRACT,
        ready_contract,
    )


    loading_boundaries = {
        relative(path):
            sha256_file(
                path
            )

        for path in generated_loading
    }


    loading_contract = {
        "stage":
            "10.8.2",

        "version":
            "1.0.0",

        "name":
            "NEXT_APP_ROUTER_LOADING_UX",

        "status":
            "LOCKED",

        "reusable_component":
            relative(
                LOADING_STATE_FILE
            ),

        "boundary_sha256":
            loading_boundaries,

        "routes": [
            "/",
            "/matches/[fixtureId]",
            "/teams/[teamName]",
        ],

        "behavior": {
            "next_loading_boundaries":
                True,

            "aria_busy":
                True,

            "client_timer":
                False,

            "data_fetch":
                False,

            "stale_content":
                False,
        },

        "dependency_identity": {
            relative(
                READY_CONTRACT
            ):
                identity(
                    READY_CONTRACT
                ),

            relative(
                LOADING_STATE_CONTRACT
            ):
                identity(
                    LOADING_STATE_CONTRACT
                ),
        },

        "promotion": {
            "stage10_8_2_complete":
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
        LOADING_UX_CONTRACT,
        loading_contract,
    )


    not_found_boundaries = {
        relative(path):
            sha256_file(
                path
            )

        for path in generated_not_found
    }


    not_found_contract = {
        "stage":
            "10.8.3",

        "version":
            "1.0.0",

        "name":
            "NOT_FOUND_404_UX",

        "status":
            "LOCKED",

        "mapped_state":
            "NOT_FOUND",

        "mapped_http_status":
            404,

        "boundary_sha256":
            not_found_boundaries,

        "existing_team_boundary": {
            "source":
                relative(
                    TEAM_NOT_FOUND_FILE
                ),

            "sha256":
                sha256_file(
                    TEAM_NOT_FOUND_FILE
                ),
        },

        "route_behavior": {
            "match_not_found_uses_next_notFound":
                True,

            "team_not_found_uses_next_notFound":
                True,

            "fuzzy_matching":
                False,

            "automatic_substitution":
                False,

            "stale_fallback":
                False,
        },

        "dependency_identity": {
            relative(
                LOADING_UX_CONTRACT
            ):
                identity(
                    LOADING_UX_CONTRACT
                ),

            relative(
                TEAM_UNKNOWN_CONTRACT
            ):
                identity(
                    TEAM_UNKNOWN_CONTRACT
                ),

            relative(
                EMPTY_STATE_CONTRACT
            ):
                identity(
                    EMPTY_STATE_CONTRACT
                ),
        },

        "promotion": {
            "stage10_8_3_complete":
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
        NOT_FOUND_UX_CONTRACT,
        not_found_contract,
    )


    not_ready_contract = {
        "stage":
            "10.8.4",

        "version":
            "1.0.0",

        "name":
            "API_503_NOT_READY_UX",

        "status":
            "LOCKED",

        "mapped_state":
            "NOT_READY",

        "mapped_http_status":
            503,

        "component":
            "ServiceNotReadyState",

        "source":
            relative(
                NOT_READY_STATE_FILE
            ),

        "behavior": {
            "explicit_not_ready_branch":
                True,

            "root_route":
                True,

            "match_route":
                True,

            "team_route":
                True,

            "team_context":
                True,

            "stale_fallback":
                False,

            "retry_logic":
                False,

            "network_error_handling":
                False,
        },

        "component_sha256":
            sha256_file(
                NOT_READY_STATE_FILE
            ),

        "root_page_before_sha256":
            root_before,

        "root_page_after_sha256":
            sha256_file(
                ROOT_PAGE
            ),

        "match_page_before_sha256":
            match_before,

        "match_page_after_sha256":
            sha256_file(
                MATCH_PAGE
            ),

        "team_page_before_sha256":
            team_before,

        "team_page_after_sha256":
            sha256_file(
                TEAM_PAGE
            ),

        "dependency_identity": {
            relative(
                NOT_FOUND_UX_CONTRACT
            ):
                identity(
                    NOT_FOUND_UX_CONTRACT
                ),

            relative(
                ERROR_STATE_CONTRACT
            ):
                identity(
                    ERROR_STATE_CONTRACT
                ),

            relative(
                FRESHNESS_CONTRACT
            ):
                identity(
                    FRESHNESS_CONTRACT
                ),

            relative(
                RESULT_FILE
            ):
                identity(
                    RESULT_FILE
                ),
        },

        "promotion": {
            "stage10_8_4_complete":
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
        NOT_READY_UX_CONTRACT,
        not_ready_contract,
    )


    print()

    print(
        "Runtime components:"
    )

    print(
        f"  {relative(READY_STATE_FILE)}"
    )

    print(
        f"  {relative(NOT_READY_STATE_FILE)}"
    )

    print()

    print(
        "Loading boundaries:"
    )

    for path in generated_loading:

        print(
            f"  {relative(path)}"
        )

    print()

    print(
        "404 boundaries:"
    )

    for path in generated_not_found:

        print(
            f"  {relative(path)}"
        )

    print(
        f"  {relative(TEAM_NOT_FOUND_FILE)}"
    )

    print()

    print("=" * 72)

    print(
        "STAGE 10.8.1 READY UX: BUILT"
    )

    print(
        "STAGE 10.8.2 LOADING UX: BUILT"
    )

    print(
        "STAGE 10.8.3 404 UX: BUILT"
    )

    print(
        "STAGE 10.8.4 NOT_READY UX: BUILT"
    )

    print(
        "VERIFICATION STILL REQUIRED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
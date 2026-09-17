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
DOCS = ROOT / "docs" / "stage10"

FRONTEND_DATA = (
    ROOT
    / "data"
    / "processed"
    / "frontend"
)


RESULT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "result.ts"
)

MAPPED_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "mapped.ts"
)

RUNTIME_TEST_FILE = (
    FRONTEND
    / "scripts"
    / "verify-stage10-api-result-mapping.mjs"
)

CONTRACT_FILE = (
    DOCS
    / "frontend_http_error_mapping_contract.json"
)

PREVIOUS_FILE = (
    FRONTEND_DATA
    / "stage10_2_5_10_2_6_verification.json"
)

VALIDATION_CONTRACT_FILE = (
    DOCS
    / "frontend_response_validation_contract.json"
)

INTELLIGENCE_CONTRACT_FILE = (
    DOCS
    / "frontend_intelligence_api_client_contract.json"
)

PRODUCTION_CONTRACT_FILE = (
    DOCS
    / "frontend_production_api_client_contract.json"
)

CONTEXT_CONTRACT_FILE = (
    DOCS
    / "frontend_context_api_client_contract.json"
)

OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_2_7_verification.json"
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

            path = resolve_project_path(
                path_text
            )

            expected = str(
                identity.get(
                    "sha256",
                    "",
                )
            )

            current = (
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


def run_runtime_tests() -> tuple[
    bool,
    str,
]:

    node = shutil.which(
        "node"
    )

    if node is None:
        return (
            False,
            "Node executable not found.",
        )

    result = subprocess.run(
        [
            node,
            str(
                RUNTIME_TEST_FILE
            ),
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
        result.returncode == 0
        and
        (
            "STAGE 10.2.7 "
            "HTTP / ERROR-STATE MAPPING TESTS: PASS"
            in
            output
        ),
        output,
    )


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.2.7"
    )

    print(
        "HTTP / ERROR-STATE MAPPING VERIFICATION"
    )

    print("=" * 72)

    failures: list[str] = []


    required = [
        RESULT_FILE,
        MAPPED_FILE,
        RUNTIME_TEST_FILE,
        CONTRACT_FILE,
        PREVIOUS_FILE,
        VALIDATION_CONTRACT_FILE,
        INTELLIGENCE_CONTRACT_FILE,
        PRODUCTION_CONTRACT_FILE,
        CONTEXT_CONTRACT_FILE,
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


    contract = load_json(
        CONTRACT_FILE
    )

    previous = load_json(
        PREVIOUS_FILE
    )

    intelligence = load_json(
        INTELLIGENCE_CONTRACT_FILE
    )

    production = load_json(
        PRODUCTION_CONTRACT_FILE
    )

    context = load_json(
        CONTEXT_CONTRACT_FILE
    )


    result_source = (
        RESULT_FILE.read_text(
            encoding="utf-8"
        )
    )

    mapped_source = (
        MAPPED_FILE.read_text(
            encoding="utf-8"
        )
    )


    print(
        "\n2. 10.2.5 / 10.2.6 FOUNDATION"
    )

    check(
        "Previous verification PASS",
        previous.get("status")
        ==
        "PASS",
        failures,
    )

    check(
        "10.2.5 complete",
        previous.get(
            "stage_10_2_5_complete"
        )
        is True,
        failures,
    )

    check(
        "10.2.6 complete",
        previous.get(
            "stage_10_2_6_complete"
        )
        is True,
        failures,
    )

    check(
        "10.2.6 authorized 10.2.7",
        previous.get(
            "stage10_ready_for_10_2_7"
        )
        is True,
        failures,
    )


    print(
        "\n3. STAGE 10.2.7 CONTRACT"
    )

    check(
        "Contract stage exact",
        contract.get("stage")
        ==
        "10.2.7",
        failures,
    )

    check(
        "Contract LOCKED",
        contract.get("status")
        ==
        "LOCKED",
        failures,
    )


    mapping = contract.get(
        "mapping",
        {}
    )


    expected_mapping = {
        "HTTP_200":
            "READY",

        "HTTP_404":
            "NOT_FOUND",

        "HTTP_503":
            "NOT_READY",

        "NETWORK_FAILURE":
            "CONNECTION_ERROR",

        "INVALID_RESPONSE":
            "CONNECTION_ERROR",

        "UNEXPECTED_HTTP_STATUS":
            "CONNECTION_ERROR",
    }


    check(
        "HTTP/error mapping exact",
        mapping
        ==
        expected_mapping,
        failures,
    )


    print(
        "\n4. RESULT MAPPER SOURCE"
    )

    for state in [
        "READY",
        "NOT_FOUND",
        "NOT_READY",
        "CONNECTION_ERROR",
    ]:

        check(
            f"Terminal state present: {state}",
            f'"{state}"'
            in
            result_source,
            failures,
        )


    for status in [
        "200",
        "404",
        "503",
    ]:

        check(
            f"HTTP status mapping present: {status}",
            (
                f"response.status === {status}"
                in
                result_source
            ),
            failures,
        )


    check(
        "Mapper checks response.ok for READY",
        "response.ok"
        in
        result_source,
        failures,
    )


    check(
        "Validation errors recognized",
        "ApiValidationError"
        in
        result_source,
        failures,
    )


    check(
        "Malformed JSON recognized",
        "SyntaxError"
        in
        result_source,
        failures,
    )


    check(
        "Non-JSON response recognized",
        (
            "FixtureIQ backend returned "
            "a non-JSON response."
            in
            result_source
        ),
        failures,
    )


    check(
        "No direct fetch in mapper",
        re.search(
            r"\bfetch\s*\(",
            result_source,
        )
        is None,
        failures,
    )


    print(
        "\n5. FAILURE / STALE-DATA POLICY"
    )


    failure_policy = contract.get(
        "failure_policy",
        {}
    )


    check(
        "No stale fallback",
        failure_policy.get(
            "stale_fallback"
        )
        is False,
        failures,
    )

    check(
        "Previous READY payload not preserved",
        failure_policy.get(
            "previous_ready_payload_preserved"
        )
        is False,
        failures,
    )

    check(
        "No automatic retry",
        failure_policy.get(
            "automatic_retry"
        )
        is False,
        failures,
    )

    check(
        "Fail closed",
        failure_policy.get(
            "fail_closed"
        )
        is True,
        failures,
    )


    print(
        "\n6. MAPPED API SURFACE"
    )


    production_functions = (
        production.get(
            "generated_functions",
            []
        )
    )

    context_functions = (
        context.get(
            "generated_functions",
            []
        )
    )

    expected_count = (
        5
        +
        len(
            production_functions
        )
        +
        len(
            context_functions
        )
    )


    check(
        "Mapped function count exact",
        contract.get(
            "mapped_function_count"
        )
        ==
        expected_count,
        failures,
    )


    check(
        "Mapped surface server-only",
        'import "server-only";'
        in
        mapped_source,
        failures,
    )


    check(
        "Mapped surface uses validated API",
        '"./validated"'
        in
        mapped_source,
        failures,
    )


    check(
        "Mapped surface uses result mapper",
        "mapValidatedApiRequest"
        in
        mapped_source,
        failures,
    )


    check(
        "Mapped surface does not call fetch",
        re.search(
            r"\bfetch\s*\(",
            mapped_source,
        )
        is None,
        failures,
    )


    check(
        "Mapped surface has no axios",
        "axios"
        not in
        mapped_source.lower(),
        failures,
    )


    for item in contract.get(
        "mapped_functions",
        []
    ):

        name = item.get(
            "result_function"
        )

        check(
            f"Mapped export exists: {name}",
            isinstance(
                name,
                str,
            )
            and
            f"export function {name}"
            in
            mapped_source,
            failures,
        )


    print(
        "\n7. AUTHORITY BOUNDARY"
    )


    responsibility = contract.get(
        "responsibility",
        {}
    )


    for key in [
        "stage7_prediction_authority",
        "stage8_context_authority",
        "stage9_intelligence_authority",
        "stage10_presentation_authority",
    ]:

        check(
            key,
            responsibility.get(key)
            is True,
            failures,
        )


    for key in [
        "prediction_logic_added",
        "probabilities_modified",
        "context_modified",
        "intelligence_modified",
        "provider_access",
        "artifact_access",
    ]:

        check(
            key,
            responsibility.get(key)
            is False,
            failures,
        )


    print(
        "\n8. SOURCE IDENTITY"
    )


    source_identity = contract.get(
        "source_identity",
        {}
    )


    for path in [
        RESULT_FILE,
        MAPPED_FILE,
        RUNTIME_TEST_FILE,
    ]:

        expected = (
            source_identity
            .get(
                relative(path),
                {},
            )
            .get(
                "sha256"
            )
        )

        check(
            f"{path.name} SHA current",
            expected
            ==
            sha256_file(path),
            failures,
        )


    print(
        "\n9. DEPENDENCY FRESHNESS"
    )


    verify_dependencies(
        contract,
        "10.2.7",
        failures,
    )


    print(
        "\n10. RUNTIME MAPPING TESTS"
    )


    runtime_ok, runtime_output = (
        run_runtime_tests()
    )


    check(
        "HTTP/error mapping runtime tests",
        runtime_ok,
        failures,
    )


    if runtime_output:

        print()
        print(runtime_output)


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
        print(compiler_output)


    print(
        "\n12. NO PREMATURE PROMOTION"
    )


    promotion = contract.get(
        "promotion",
        {}
    )


    check(
        "10.2.7 did not self-promote",
        promotion.get(
            "stage10_2_7_complete"
        )
        is False,
        failures,
    )

    check(
        "Stage 10.2 remains incomplete",
        promotion.get(
            "stage10_2_complete"
        )
        is False,
        failures,
    )

    check(
        "Stage 10 remains incomplete",
        promotion.get(
            "stage10_complete"
        )
        is False,
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
                "10.2.7",

            "name":
                "HTTP_ERROR_STATE_MAPPING_VERIFICATION",

            "status":
                "PASS",

            "stage_10_2_7_complete":
                True,

            "http_error_state_mapping":
                "LOCKED_AND_VERIFIED",

            "mapping": {
                "200":
                    "READY",

                "404":
                    "NOT_FOUND",

                "503":
                    "NOT_READY",

                "network":
                    "CONNECTION_ERROR",

                "invalid_response":
                    "CONNECTION_ERROR",

                "unexpected_http":
                    "CONNECTION_ERROR",
            },

            "runtime_tests":
                "PASS",

            "typescript_compiler":
                "PASS",

            "stale_data_protection": {
                "failure_contains_ready_data":
                    False,

                "previous_ready_payload_reused":
                    False,

                "stale_fallback":
                    False,
            },

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "stage10_ready_for_10_2_8":
                True,

            "stage10_2_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.2.8",

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
        + "=" * 72
    )


    if passed:

        print(
            "STAGE 10.2.7: PASS"
        )

        print(
            "HTTP / ERROR-STATE MAPPING: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.2.8"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.2.7: FAIL"
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
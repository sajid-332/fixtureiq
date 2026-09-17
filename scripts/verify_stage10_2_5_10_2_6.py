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


CONTEXT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "context.ts"
)

VALIDATION_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "validation.ts"
)

VALIDATED_API_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "validated.ts"
)

RUNTIME_TEST_FILE = (
    FRONTEND
    / "scripts"
    / "verify-stage10-api-validation.mjs"
)

INTELLIGENCE_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "intelligence.ts"
)

PRODUCTION_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "production.ts"
)

SHARED_CLIENT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "client.ts"
)


CONTEXT_CONTRACT_FILE = (
    DOCS
    / "frontend_context_api_client_contract.json"
)

VALIDATION_CONTRACT_FILE = (
    DOCS
    / "frontend_response_validation_contract.json"
)

ENDPOINT_CONTRACT_FILE = (
    DOCS
    / "frontend_api_endpoint_contract.json"
)

HTTP_CLIENT_CONTRACT_FILE = (
    DOCS
    / "frontend_http_client_contract.json"
)

INTELLIGENCE_CONTRACT_FILE = (
    DOCS
    / "frontend_intelligence_api_client_contract.json"
)

PRODUCTION_CONTRACT_FILE = (
    DOCS
    / "frontend_production_api_client_contract.json"
)

PREVIOUS_FILE = (
    FRONTEND_DATA
    / "stage10_2_3_10_2_4_verification.json"
)

PACKAGE_JSON_FILE = (
    FRONTEND
    / "package.json"
)

PACKAGE_LOCK_FILE = (
    FRONTEND
    / "package-lock.json"
)

OUTPUT_FILE = (
    FRONTEND_DATA
    / "stage10_2_5_10_2_6_verification.json"
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

    if raw.is_absolute():

        resolved = raw.resolve()

    else:

        resolved = (
            ROOT
            / raw
        ).resolve()

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

        expected_sha = (
            identity.get(
                "sha256",
                ""
            )
            if isinstance(
                identity,
                dict,
            )
            else ""
        )

        try:

            path = resolve_project_path(
                path_text
            )

            current = (
                bool(expected_sha)
                and
                path.exists()
                and
                sha256_file(path)
                ==
                expected_sha
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


def run_runtime_validation_tests() -> tuple[
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
            "STAGE 10.2.6 "
            "RUNTIME VALIDATION TESTS: PASS"
            in
            output
        ),
        output,
    )


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.2.5 + 10.2.6"
    )

    print(
        "CONTEXT CLIENT + RESPONSE VALIDATION VERIFICATION"
    )

    print("=" * 72)

    failures: list[str] = []

    required_files = [
        CONTEXT_FILE,
        VALIDATION_FILE,
        VALIDATED_API_FILE,
        RUNTIME_TEST_FILE,
        INTELLIGENCE_FILE,
        PRODUCTION_FILE,
        SHARED_CLIENT_FILE,
        CONTEXT_CONTRACT_FILE,
        VALIDATION_CONTRACT_FILE,
        ENDPOINT_CONTRACT_FILE,
        HTTP_CLIENT_CONTRACT_FILE,
        INTELLIGENCE_CONTRACT_FILE,
        PRODUCTION_CONTRACT_FILE,
        PREVIOUS_FILE,
        PACKAGE_JSON_FILE,
        PACKAGE_LOCK_FILE,
    ]

    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    for path in required_files:

        check(
            relative(path),
            path.exists(),
            failures,
        )

    if failures:

        sys.exit(1)

    context_contract = load_json(
        CONTEXT_CONTRACT_FILE
    )

    validation_contract = load_json(
        VALIDATION_CONTRACT_FILE
    )

    endpoint_contract = load_json(
        ENDPOINT_CONTRACT_FILE
    )

    http_contract = load_json(
        HTTP_CLIENT_CONTRACT_FILE
    )

    intelligence_contract = load_json(
        INTELLIGENCE_CONTRACT_FILE
    )

    production_contract = load_json(
        PRODUCTION_CONTRACT_FILE
    )

    previous = load_json(
        PREVIOUS_FILE
    )

    context_source = (
        CONTEXT_FILE.read_text(
            encoding="utf-8"
        )
    )

    validation_source = (
        VALIDATION_FILE.read_text(
            encoding="utf-8"
        )
    )

    validated_source = (
        VALIDATED_API_FILE.read_text(
            encoding="utf-8"
        )
    )

    print(
        "\n2. STAGE 10.2.3 / 10.2.4 FOUNDATION"
    )

    check(
        "Previous verification PASS",
        previous.get("status")
        ==
        "PASS",
        failures,
    )

    check(
        "10.2.3 complete",
        previous.get(
            "stage_10_2_3_complete"
        )
        is True,
        failures,
    )

    check(
        "10.2.4 complete",
        previous.get(
            "stage_10_2_4_complete"
        )
        is True,
        failures,
    )

    check(
        "10.2.4 authorized 10.2.5",
        previous.get(
            "stage10_ready_for_10_2_5"
        )
        is True,
        failures,
    )

    for label, payload in [
        (
            "HTTP client contract",
            http_contract,
        ),
        (
            "Intelligence client contract",
            intelligence_contract,
        ),
        (
            "Production client contract",
            production_contract,
        ),
    ]:

        check(
            f"{label} remains LOCKED",
            payload.get("status")
            ==
            "LOCKED",
            failures,
        )

    print(
        "\n3. STAGE 10.2.5 CONTEXT CLIENT"
    )

    check(
        "Context contract stage exact",
        context_contract.get(
            "stage"
        )
        ==
        "10.2.5",
        failures,
    )

    check(
        "Context contract LOCKED",
        context_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )

    check(
        "Stage 8 remains context authority",
        context_contract.get(
            "authority"
        )
        ==
        "STAGE8_CONTEXT",
        failures,
    )

    locked_context_routes = {
        route

        for route in endpoint_contract.get(
            "route_set",
            []
        )

        if route.startswith(
            "/api/v1/context"
        )
    }

    check(
        "Exactly 10 locked context routes",
        len(
            locked_context_routes
        )
        ==
        10,
        failures,
    )

    contract_context_routes = set(
        context_contract.get(
            "routes",
            []
        )
    )

    check(
        "Context route set exactly matches 10.1.3",
        contract_context_routes
        ==
        locked_context_routes,
        failures,
    )

    check(
        "Context route count exact",
        context_contract.get(
            "route_count"
        )
        ==
        10,
        failures,
    )

    context_functions = (
        context_contract.get(
            "generated_functions",
            []
        )
    )

    check(
        "One context wrapper per route",
        len(
            context_functions
        )
        ==
        10,
        failures,
    )

    for item in context_functions:

        function = item.get(
            "function"
        )

        route = item.get(
            "route"
        )

        check(
            f"Context export exists: {function}",
            isinstance(
                function,
                str,
            )
            and
            re.search(
                (
                    r"export\s+function\s+"
                    +
                    re.escape(
                        function
                    )
                    +
                    r"\s*\("
                ),
                context_source,
            )
            is not None,
            failures,
        )

        check(
            f"Context route locked: {route}",
            route
            in
            locked_context_routes,
            failures,
        )

    check(
        "Context client server-only",
        'import "server-only";'
        in
        context_source,
        failures,
    )

    check(
        "Context client uses shared transport",
        "fixtureIqApiGet"
        in
        context_source,
        failures,
    )

    check(
        "Context client does not call fetch directly",
        re.search(
            r"\bfetch\s*\(",
            context_source,
        )
        is None,
        failures,
    )

    check(
        "Context client does not use axios",
        "axios"
        not in
        context_source.lower(),
        failures,
    )

    context_impl = (
        context_contract.get(
            "implementation",
            {}
        )
    )

    check(
        "Context routes not guessed",
        context_impl.get(
            "routes_manually_guessed"
        )
        is False,
        failures,
    )

    check(
        "Context recalculation forbidden",
        context_impl.get(
            "context_recalculation"
        )
        is False,
        failures,
    )

    check(
        "Context provider access forbidden",
        context_impl.get(
            "provider_access"
        )
        is False,
        failures,
    )

    print(
        "\n4. STAGE 10.2.6 VALIDATION CONTRACT"
    )

    check(
        "Validation contract stage exact",
        validation_contract.get(
            "stage"
        )
        ==
        "10.2.6",
        failures,
    )

    check(
        "Validation contract LOCKED",
        validation_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )

    implementation = (
        validation_contract.get(
            "implementation",
            {}
        )
    )

    check(
        "Native TS runtime guards locked",
        implementation.get(
            "approach"
        )
        ==
        "NATIVE_TYPESCRIPT_RUNTIME_GUARDS",
        failures,
    )

    check(
        "No new package dependency installed",
        implementation.get(
            "new_dependency_installed"
        )
        is False,
        failures,
    )

    check(
        "Package lock not intentionally mutated",
        implementation.get(
            "package_lock_mutated"
        )
        is False,
        failures,
    )

    for key in [
        "json_structure_validation",
        "finite_number_validation",
        "probability_range_validation",
        "outcome_enum_validation",
        "confidence_band_validation",
        "uncertainty_band_validation",
        "context_alignment_validation",
        "context_support_range_validation",
        "production_record_validation",
        "intelligence_record_validation",
        "context_identity_validation",
        "error_payloads_supported",
        "validated_transport_wrappers",
    ]:

        check(
            key,
            implementation.get(key)
            is True,
            failures,
        )

    print(
        "\n5. VALIDATION SOURCE"
    )

    required_exports = [
        "ApiValidationError",
        "assertJsonValue",
        "validateProductionApiPayload",
        "validateIntelligenceApiPayload",
        "validateContextApiPayload",
    ]

    for name in required_exports:

        check(
            f"Validation export exists: {name}",
            (
                f"export function {name}"
                in
                validation_source
            )
            or
            (
                f"export class {name}"
                in
                validation_source
            ),
            failures,
        )

    for api in [
        "Array.isArray",
        "Object.entries",
        "Number.isFinite",
        "Number.isInteger",
        "new Set",
    ]:

        check(
            f"Standard library validation API used: {api}",
            api
            in
            validation_source,
            failures,
        )

    check(
        "No eval in validator",
        re.search(
            r"\beval\s*\(",
            validation_source,
        )
        is None,
        failures,
    )

    check(
        "No Function constructor",
        "new Function"
        not in
        validation_source,
        failures,
    )

    print(
        "\n6. VALIDATED CLIENT SURFACE"
    )

    check(
        "Validated client server-only",
        'import "server-only";'
        in
        validated_source,
        failures,
    )

    check(
        "Validated client imports intelligence transport",
        '"./intelligence"'
        in
        validated_source,
        failures,
    )

    check(
        "Validated client imports production transport",
        '"./production"'
        in
        validated_source,
        failures,
    )

    check(
        "Validated client imports context transport",
        '"./context"'
        in
        validated_source,
        failures,
    )

    check(
        "Validated client does not call fetch directly",
        re.search(
            r"\bfetch\s*\(",
            validated_source,
        )
        is None,
        failures,
    )

    intelligence_wrappers = [
        "getValidatedIntelligenceStatus",
        "getValidatedIntelligenceMatches",
        "getValidatedIntelligenceMatch",
        "getValidatedTeamIntelligence",
        "getValidatedUpcomingIntelligence",
    ]

    for name in intelligence_wrappers:

        check(
            f"Validated intelligence wrapper: {name}",
            f"export async function {name}"
            in
            validated_source,
            failures,
        )

    production_functions = (
        production_contract.get(
            "generated_functions",
            []
        )
    )

    for item in production_functions:

        raw_name = str(
            item.get(
                "function",
                "",
            )
        )

        expected = (
            "getValidated"
            +
            raw_name[3:]
        )

        check(
            f"Validated production wrapper: {expected}",
            f"export async function {expected}"
            in
            validated_source,
            failures,
        )

    for item in context_functions:

        raw_name = str(
            item.get(
                "function",
                "",
            )
        )

        expected = (
            "getValidated"
            +
            raw_name[3:]
        )

        check(
            f"Validated context wrapper: {expected}",
            f"export async function {expected}"
            in
            validated_source,
            failures,
        )

    print(
        "\n7. AUTHORITY / INTEGRITY BOUNDARY"
    )

    authority = (
        validation_contract.get(
            "authority_preservation",
            {}
        )
    )

    check(
        "Stage 7 prediction authority preserved",
        authority.get(
            "stage7_prediction"
        )
        is True,
        failures,
    )

    check(
        "Stage 8 context authority preserved",
        authority.get(
            "stage8_context"
        )
        is True,
        failures,
    )

    check(
        "Stage 9 intelligence authority preserved",
        authority.get(
            "stage9_intelligence"
        )
        is True,
        failures,
    )

    check(
        "Stage 10 presentation-only retained",
        authority.get(
            "stage10_presentation_only"
        )
        is True,
        failures,
    )

    check(
        "Probabilities not recalculated",
        authority.get(
            "probabilities_recalculated"
        )
        is False,
        failures,
    )

    check(
        "Context not recalculated",
        authority.get(
            "context_recalculated"
        )
        is False,
        failures,
    )

    check(
        "Intelligence not recalculated",
        authority.get(
            "intelligence_recalculated"
        )
        is False,
        failures,
    )

    semantic_mapping = (
        validation_contract.get(
            "semantic_http_mapping",
            {}
        )
    )

    check(
        "HTTP semantic mapping deferred",
        semantic_mapping.get(
            "implemented_here"
        )
        is False,
        failures,
    )

    check(
        "HTTP semantic mapping owner = 10.2.7",
        semantic_mapping.get(
            "owner"
        )
        ==
        "10.2.7",
        failures,
    )

    print(
        "\n8. SOURCE IDENTITY"
    )

    check(
        "context.ts SHA current",
        context_contract.get(
            "source_sha256"
        )
        ==
        sha256_file(
            CONTEXT_FILE
        ),
        failures,
    )

    source_identity = (
        validation_contract.get(
            "source_identity",
            {}
        )
    )

    for path in [
        VALIDATION_FILE,
        VALIDATED_API_FILE,
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
        context_contract,
        "10.2.5",
        failures,
    )

    verify_dependencies(
        validation_contract,
        "10.2.6",
        failures,
    )

    print(
        "\n10. RUNTIME VALIDATION TESTS"
    )

    runtime_ok, runtime_output = (
        run_runtime_validation_tests()
    )

    check(
        "Runtime validator positive/negative tests",
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

        print(
            compiler_output
        )

    print(
        "\n12. NO PREMATURE PROMOTION"
    )

    context_promotion = (
        context_contract.get(
            "promotion",
            {}
        )
    )

    validation_promotion = (
        validation_contract.get(
            "promotion",
            {}
        )
    )

    check(
        "10.2.5 contract did not self-promote",
        context_promotion.get(
            "stage10_2_5_complete"
        )
        is False,
        failures,
    )

    check(
        "10.2.6 contract did not self-promote",
        validation_promotion.get(
            "stage10_2_6_complete"
        )
        is False,
        failures,
    )

    check(
        "Stage 10.2 remains incomplete",
        (
            context_promotion.get(
                "stage10_2_complete"
            )
            is False
            and
            validation_promotion.get(
                "stage10_2_complete"
            )
            is False
        ),
        failures,
    )

    check(
        "Stage 10 remains incomplete",
        (
            context_promotion.get(
                "stage10_complete"
            )
            is False
            and
            validation_promotion.get(
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
                "10.2.5-10.2.6",

            "name":
                (
                    "CONTEXT_API_CLIENT_AND_"
                    "TYPED_RESPONSE_VALIDATION_VERIFICATION"
                ),

            "status":
                "PASS",

            "stage_10_2_5_complete":
                True,

            "stage_10_2_6_complete":
                True,

            "context_api_client":
                "LOCKED_AND_VERIFIED",

            "typed_response_validation":
                "LOCKED_AND_VERIFIED",

            "context_route_count":
                10,

            "validation_runtime_tests":
                "PASS",

            "typescript_compiler":
                "PASS",

            "validation": {
                "json_structure":
                    True,

                "production_records":
                    True,

                "intelligence_records":
                    True,

                "context_identity":
                    True,

                "probability_ranges":
                    True,

                "enum_domains":
                    True,

                "support_score_range":
                    True,

                "validated_wrappers":
                    True,
            },

            "safety": {
                "new_dependency_added":
                    False,

                "direct_fetch":
                    False,

                "direct_provider_access":
                    False,

                "model_access":
                    False,

                "prediction_recalculation":
                    False,

                "context_recalculation":
                    False,

                "intelligence_recalculation":
                    False,

                "stale_fallback":
                    False,

                "semantic_error_mapping":
                    False,
            },

            "dependency_identity": {
                relative(
                    CONTEXT_FILE
                ): {
                    "sha256":
                        sha256_file(
                            CONTEXT_FILE
                        )
                },

                relative(
                    VALIDATION_FILE
                ): {
                    "sha256":
                        sha256_file(
                            VALIDATION_FILE
                        )
                },

                relative(
                    VALIDATED_API_FILE
                ): {
                    "sha256":
                        sha256_file(
                            VALIDATED_API_FILE
                        )
                },

                relative(
                    CONTEXT_CONTRACT_FILE
                ): {
                    "sha256":
                        sha256_file(
                            CONTEXT_CONTRACT_FILE
                        )
                },

                relative(
                    VALIDATION_CONTRACT_FILE
                ): {
                    "sha256":
                        sha256_file(
                            VALIDATION_CONTRACT_FILE
                        )
                },

                relative(
                    PREVIOUS_FILE
                ): {
                    "sha256":
                        sha256_file(
                            PREVIOUS_FILE
                        )
                },
            },

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "stage10_ready_for_10_2_7":
                True,

            "stage10_2_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.2.7",

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
            "STAGE 10.2.5: PASS"
        )

        print(
            "CONTEXT API CLIENT: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.2.6: PASS"
        )

        print(
            "TYPED RESPONSE VALIDATION: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.2.7"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.2.5 / 10.2.6: FAIL"
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
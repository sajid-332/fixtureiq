from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

FRONTEND_ROOT = (
    ROOT
    / "frontend"
)

PACKAGE_JSON = (
    FRONTEND_ROOT
    / "package.json"
)

AUDIT_FILE = (
    ROOT
    / "docs"
    / "stage10"
    / "frontend_audit.json"
)

CONTRACT_FILE = (
    ROOT
    / "docs"
    / "stage10"
    / "frontend_responsibility_contract.json"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "frontend"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "stage10_1_1_10_1_2_verification.json"
)


def load_json(
    path: Path,
) -> dict:

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
            f"Expected JSON object: {path}"
        )

    return value


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


def check(
    label: str,
    condition,
    failures: list[str],
) -> None:

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

        file.write(
            "\n"
        )

    temporary.replace(
        path
    )


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.1.1 + 10.1.2"
    )

    print(
        "FRONTEND AUDIT + RESPONSIBILITY BOUNDARY VERIFICATION"
    )

    print("=" * 72)

    failures: list[str] = []

    print(
        "\n1. REQUIRED FILES"
    )

    for path in [
        PACKAGE_JSON,
        AUDIT_FILE,
        CONTRACT_FILE,
    ]:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        print(
            "\nRequired files missing."
        )

        sys.exit(1)

    package_json = load_json(
        PACKAGE_JSON
    )

    audit = load_json(
        AUDIT_FILE
    )

    contract = load_json(
        CONTRACT_FILE
    )

    print(
        "\n2. STAGE 10.1.1 FRONTEND AUDIT"
    )

    check(
        "Audit stage exact",
        audit.get(
            "stage"
        )
        ==
        "10.1.1",
        failures,
    )

    check(
        "Audit status PASS",
        audit.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )

    framework = audit.get(
        "framework",
        {}
    )

    check(
        "Next.js detected",
        bool(
            framework.get(
                "next"
            )
        ),
        failures,
    )

    check(
        "React detected",
        bool(
            framework.get(
                "react"
            )
        ),
        failures,
    )

    check(
        "TypeScript detected",
        bool(
            framework.get(
                "typescript"
            )
        ),
        failures,
    )

    routing = audit.get(
        "routing",
        {}
    )

    check(
        "App Router detected",
        routing.get(
            "app_router"
        )
        is True,
        failures,
    )

    check(
        "App Router root recorded",
        bool(
            routing.get(
                "app_root"
            )
        ),
        failures,
    )

    audit_scope = audit.get(
        "audit_scope",
        {}
    )

    for key in [
        "ui_modified",
        "dependencies_modified",
        "backend_modified",
        "stage7_modified",
        "stage8_modified",
        "stage9_modified",
    ]:

        check(
            f"Audit did not modify {key}",
            audit_scope.get(
                key
            )
            is False,
            failures,
        )

    risks = audit.get(
        "responsibility_boundary_risks",
        {}
    )

    check(
        "No direct artifact/provider boundary risk found",
        risks.get(
            "count"
        )
        ==
        0,
        failures,
    )

    print(
        "\n3. STAGE 10.1.2 RESPONSIBILITY CONTRACT"
    )

    check(
        "Contract stage exact",
        contract.get(
            "stage"
        )
        ==
        "10.1.2",
        failures,
    )

    check(
        "Contract version locked",
        contract.get(
            "version"
        )
        ==
        "1.0.0",
        failures,
    )

    check(
        "Contract status LOCKED",
        contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )

    authority = contract.get(
        "authority",
        {}
    )

    expected_authority = {
        "stage7":
            "PREDICTION_AUTHORITY",

        "stage8":
            "CONTEXT_AUTHORITY",

        "stage9":
            "INTELLIGENCE_AUTHORITY",

        "stage10":
            "PRESENTATION_AUTHORITY",
    }

    check(
        "Authority mapping exact",
        authority
        ==
        expected_authority,
        failures,
    )

    print(
        "\n4. API BOUNDARY"
    )

    api_policy = contract.get(
        "api_policy",
        {}
    )

    check(
        "HTTP JSON transport",
        api_policy.get(
            "transport"
        )
        ==
        "HTTP_JSON",
        failures,
    )

    check(
        "GET is the only allowed method",
        api_policy.get(
            "allowed_methods"
        )
        ==
        ["GET"],
        failures,
    )

    check(
        "Direct artifact access forbidden",
        api_policy.get(
            "direct_artifact_access"
        )
        is False,
        failures,
    )

    check(
        "Direct provider access forbidden",
        api_policy.get(
            "direct_provider_access"
        )
        is False,
        failures,
    )

    check(
        "Write requests forbidden",
        api_policy.get(
            "write_requests_allowed"
        )
        is False,
        failures,
    )

    check(
        "Stale fallback forbidden",
        api_policy.get(
            "stale_fallback"
        )
        is False,
        failures,
    )

    check(
        "Exact endpoint lock belongs to 10.1.3",
        api_policy.get(
            "exact_endpoint_lock_owner"
        )
        ==
        "10.1.3",
        failures,
    )

    print(
        "\n5. PREDICTION INTEGRITY BOUNDARY"
    )

    prediction = contract.get(
        "prediction_integrity",
        {}
    )

    checks = {
        "Stage 7 owns probabilities":
            prediction.get(
                "stage7_owns_probabilities"
            )
            is True,

        "Stage 7 owns predicted label":
            prediction.get(
                "stage7_owns_predicted_label"
            )
            is True,

        "Stage 7 owns confidence":
            prediction.get(
                "stage7_owns_confidence"
            )
            is True,

        "Stage 8 cannot modify prediction":
            prediction.get(
                "stage8_may_modify_prediction"
            )
            is False,

        "Stage 9 cannot modify prediction":
            prediction.get(
                "stage9_may_modify_prediction"
            )
            is False,

        "Stage 10 cannot modify prediction":
            prediction.get(
                "stage10_may_modify_prediction"
            )
            is False,

        "Display rounding allowed":
            prediction.get(
                "display_rounding_allowed"
            )
            is True,

        "Display rounding does not modify source":
            prediction.get(
                "display_rounding_changes_source_value"
            )
            is False,

        "Frontend prediction logic forbidden":
            prediction.get(
                "frontend_prediction_logic_allowed"
            )
            is False,
    }

    for label, condition in checks.items():

        check(
            label,
            condition,
            failures,
        )

    print(
        "\n6. CONTEXT / INTELLIGENCE AUTHORITY"
    )

    context_integrity = contract.get(
        "context_integrity",
        {}
    )

    intelligence_integrity = contract.get(
        "intelligence_integrity",
        {}
    )

    check(
        "Stage 8 owns context",
        context_integrity.get(
            "stage8_owns_current_context"
        )
        is True,
        failures,
    )

    check(
        "Frontend cannot recalculate context",
        context_integrity.get(
            "stage10_may_recalculate_context"
        )
        is False,
        failures,
    )

    for key in [
        "stage9_owns_uncertainty",
        "stage9_owns_context_support_score",
        "stage9_owns_context_alignment",
        "stage9_owns_explanation",
        "stage10_may_display_intelligence",
    ]:

        check(
            key,
            intelligence_integrity.get(
                key
            )
            is True,
            failures,
        )

    check(
        "Frontend cannot recalculate intelligence",
        intelligence_integrity.get(
            "stage10_may_recalculate_intelligence"
        )
        is False,
        failures,
    )

    print(
        "\n7. RUNTIME / FRESHNESS BOUNDARY"
    )

    runtime = contract.get(
        "runtime_state_policy",
        {}
    )

    check(
        "200 maps to READY",
        runtime.get(
            "200"
        )
        ==
        "READY",
        failures,
    )

    check(
        "404 maps to NOT_FOUND",
        runtime.get(
            "404"
        )
        ==
        "NOT_FOUND",
        failures,
    )

    check(
        "503 maps to NOT_READY",
        runtime.get(
            "503"
        )
        ==
        "NOT_READY",
        failures,
    )

    check(
        "Network failure explicit",
        runtime.get(
            "network_failure"
        )
        ==
        "CONNECTION_ERROR",
        failures,
    )

    check(
        "No stale response after 503",
        runtime.get(
            "previous_successful_response_may_be_used_after_503"
        )
        is False,
        failures,
    )

    check(
        "No stale response after network failure",
        runtime.get(
            "previous_successful_response_may_be_used_after_network_failure"
        )
        is False,
        failures,
    )

    check(
        "NOT_READY must be visible",
        runtime.get(
            "backend_not_ready_must_be_visible_to_user"
        )
        is True,
        failures,
    )

    print(
        "\n8. SECRETS BOUNDARY"
    )

    secrets = contract.get(
        "secrets_policy",
        {}
    )

    check(
        "No provider API keys in frontend",
        secrets.get(
            "provider_api_keys_in_frontend"
        )
        is False,
        failures,
    )

    check(
        "No backend secret keys in frontend",
        secrets.get(
            "backend_secret_keys_in_frontend"
        )
        is False,
        failures,
    )

    check(
        "No secrets in NEXT_PUBLIC env",
        secrets.get(
            "secret_values_in_next_public_environment"
        )
        is False,
        failures,
    )

    print(
        "\n9. NO PREMATURE STAGE 10 PROMOTION"
    )

    promotion = contract.get(
        "promotion",
        {}
    )

    check(
        "Stage 10 not complete",
        promotion.get(
            "stage10_complete"
        )
        is False,
        failures,
    )

    check(
        "Stage 10.1 not complete yet",
        promotion.get(
            "stage10_1_complete"
        )
        is False,
        failures,
    )

    check(
        "Promotion not authorized",
        promotion.get(
            "promotion_authorized"
        )
        is False,
        failures,
    )

    print(
        "\n10. SAVE VERIFICATION EVIDENCE"
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
                "10.1.1-10.1.2",

            "status":
                "PASS",

            "stage_10_1_1_complete":
                True,

            "stage_10_1_2_complete":
                True,

            "frontend_audit":
                "VERIFIED",

            "frontend_backend_boundary":
                "LOCKED_AND_VERIFIED",

            "framework": {
                "next":
                    framework.get(
                        "next"
                    ),

                "react":
                    framework.get(
                        "react"
                    ),

                "typescript":
                    framework.get(
                        "typescript"
                    ),

                "app_router":
                    routing.get(
                        "app_router"
                    ),
            },

            "authority": authority,

            "safety": {
                "frontend_is_presentation_only":
                    True,

                "direct_artifact_access":
                    False,

                "direct_provider_access":
                    False,

                "frontend_prediction_logic":
                    False,

                "prediction_mutation":
                    False,

                "context_recalculation":
                    False,

                "intelligence_recalculation":
                    False,

                "stale_fallback":
                    False,

                "write_api_requests":
                    False,
            },

            "dependency_identity": {
                relative(
                    PACKAGE_JSON
                ): {
                    "sha256":
                        sha256_file(
                            PACKAGE_JSON
                        )
                },

                relative(
                    AUDIT_FILE
                ): {
                    "sha256":
                        sha256_file(
                            AUDIT_FILE
                        )
                },

                relative(
                    CONTRACT_FILE
                ): {
                    "sha256":
                        sha256_file(
                            CONTRACT_FILE
                        )
                },
            },

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "stage10_ready_for_10_1_3":
                True,

            "stage10_complete":
                False,

            "next_stage":
                "10.1.3",

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
            "STAGE 10.1.1: PASS"
        )

        print(
            "EXISTING NEXT.JS FRONTEND AUDIT: VERIFIED"
        )

        print()

        print(
            "STAGE 10.1.2: PASS"
        )

        print(
            "FRONTEND / BACKEND RESPONSIBILITY BOUNDARY: LOCKED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.1.3"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.1.1 / 10.1.2: FAIL"
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
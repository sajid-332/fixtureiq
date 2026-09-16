from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
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


AUDIT_FILE = (
    ROOT
    / "docs"
    / "stage10"
    / "frontend_audit.json"
)

RESPONSIBILITY_FILE = (
    ROOT
    / "docs"
    / "stage10"
    / "frontend_responsibility_contract.json"
)

ENDPOINT_CONTRACT_FILE = (
    ROOT
    / "docs"
    / "stage10"
    / "frontend_api_endpoint_contract.json"
)

STAGE_10_1_3_FILE = (
    ROOT
    / "data"
    / "processed"
    / "frontend"
    / "stage10_1_3_verification.json"
)

ROUTE_CONTRACT_FILE = (
    ROOT
    / "docs"
    / "stage10"
    / "frontend_route_architecture.json"
)

DOMAIN_CONTRACT_FILE = (
    ROOT
    / "docs"
    / "stage10"
    / "frontend_domain_model_contract.json"
)

DOMAIN_TYPES_FILE = (
    FRONTEND_ROOT
    / "lib"
    / "domain"
    / "types.ts"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "processed"
    / "frontend"
    / "stage10_1_4_10_1_5_verification.json"
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


def resolve_project_path(
    value: str,
) -> Path:

    raw = Path(
        str(value)
    )

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

        file.write(
            "\n"
        )

    temporary.replace(
        path
    )


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


def verify_dependency_identity(
    payload: dict,
    prefix: str,
    failures: list[str],
) -> None:

    identities = payload.get(
        "dependency_identity",
        {}
    )

    check(
        f"{prefix} dependency identity exists",
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

    for (
        path_text,
        identity,
    ) in identities.items():

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
                path.exists()
                and
                sha256_file(
                    path
                )
                ==
                expected_sha
            )

        except Exception:

            current = False

        check(
            (
                f"{prefix}: "
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
        cwd=FRONTEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    output = (
        (
            result.stdout
            or ""
        )
        +
        (
            result.stderr
            or ""
        )
    ).strip()

    return (
        result.returncode
        ==
        0,
        output,
    )


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.1.4 + 10.1.5"
    )

    print(
        "ROUTE ARCHITECTURE + TYPESCRIPT DOMAIN VERIFICATION"
    )

    print("=" * 72)

    failures: list[str] = []

    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    required = [
        AUDIT_FILE,
        RESPONSIBILITY_FILE,
        ENDPOINT_CONTRACT_FILE,
        STAGE_10_1_3_FILE,
        ROUTE_CONTRACT_FILE,
        DOMAIN_CONTRACT_FILE,
        DOMAIN_TYPES_FILE,
    ]

    for path in required:

        check(
            relative(
                path
            ),
            path.exists(),
            failures,
        )

    if failures:

        sys.exit(1)

    audit = load_json(
        AUDIT_FILE
    )

    responsibility = load_json(
        RESPONSIBILITY_FILE
    )

    endpoint_contract = load_json(
        ENDPOINT_CONTRACT_FILE
    )

    previous = load_json(
        STAGE_10_1_3_FILE
    )

    route_contract = load_json(
        ROUTE_CONTRACT_FILE
    )

    domain_contract = load_json(
        DOMAIN_CONTRACT_FILE
    )

    print(
        "\n2. PREVIOUS STAGE 10 FOUNDATION"
    )

    check(
        "Stage 10.1.3 PASS",
        previous.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )

    check(
        "Stage 10.1.3 complete",
        previous.get(
            "stage_10_1_3_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 10.1.3 authorized 10.1.4",
        previous.get(
            "stage10_ready_for_10_1_4"
        )
        is True,
        failures,
    )

    check(
        "Responsibility boundary remains LOCKED",
        responsibility.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )

    check(
        "Endpoint contract remains LOCKED",
        endpoint_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )

    print(
        "\n3. STAGE 10.1.4 ROUTE ARCHITECTURE"
    )

    check(
        "Route contract stage exact",
        route_contract.get(
            "stage"
        )
        ==
        "10.1.4",
        failures,
    )

    check(
        "Route contract version exact",
        route_contract.get(
            "version"
        )
        ==
        "1.0.0",
        failures,
    )

    check(
        "Route contract LOCKED",
        route_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )

    check(
        "Next.js App Router locked",
        route_contract.get(
            "router"
        )
        ==
        "NEXTJS_APP_ROUTER",
        failures,
    )

    expected_app_root = (
        audit.get(
            "routing",
            {}
        )
        .get(
            "app_root"
        )
    )

    check(
        "App root matches 10.1.1 audit",
        route_contract.get(
            "app_root"
        )
        ==
        expected_app_root,
        failures,
    )

    routes = route_contract.get(
        "routes",
        []
    )

    check(
        "Exactly 3 user-facing routes locked",
        isinstance(
            routes,
            list,
        )
        and
        len(
            routes
        )
        ==
        3,
        failures,
    )

    expected_routes = {
        "/": (
            "UPCOMING_MATCHES_DASHBOARD",
            "10.4",
            "/api/v1/intelligence/upcoming",
        ),

        "/matches/[fixtureId]": (
            "MATCH_INTELLIGENCE_DETAIL",
            "10.5",
            (
                "/api/v1/intelligence/"
                "matches/<fixture_id>"
            ),
        ),

        "/teams/[teamName]": (
            "TEAM_INTELLIGENCE_VIEW",
            "10.6",
            (
                "/api/v1/intelligence/"
                "team/<path:team_name>"
            ),
        ),
    }

    route_map = {
        item.get(
            "path"
        ):
            item

        for item in routes

        if isinstance(
            item,
            dict,
        )
    }

    check(
        "Frontend route set exact",
        set(
            route_map
        )
        ==
        set(
            expected_routes
        ),
        failures,
    )

    locked_backend_routes = set(
        endpoint_contract.get(
            "route_set",
            []
        )
    )

    for (
        route_path,
        (
            purpose,
            owner,
            backend_route,
        ),
    ) in expected_routes.items():

        item = route_map.get(
            route_path,
            {}
        )

        check(
            f"{route_path}: purpose exact",
            item.get(
                "purpose"
            )
            ==
            purpose,
            failures,
        )

        check(
            f"{route_path}: implementation owner exact",
            item.get(
                "implementation_owner"
            )
            ==
            owner,
            failures,
        )

        check(
            f"{route_path}: backend mapping exact",
            item.get(
                "primary_backend_route"
            )
            ==
            backend_route,
            failures,
        )

        check(
            f"{route_path}: backend route exists in 10.1.3 lock",
            backend_route
            in
            locked_backend_routes,
            failures,
        )

        check(
            f"{route_path}: Stage 7 prediction authority",
            item.get(
                "prediction_authority"
            )
            ==
            "STAGE7",
            failures,
        )

        check(
            f"{route_path}: Stage 8 context authority",
            item.get(
                "context_authority"
            )
            ==
            "STAGE8",
            failures,
        )

        check(
            f"{route_path}: Stage 9 intelligence authority",
            item.get(
                "intelligence_authority"
            )
            ==
            "STAGE9",
            failures,
        )

        check(
            f"{route_path}: Stage 10 presentation authority",
            item.get(
                "presentation_authority"
            )
            ==
            "STAGE10",
            failures,
        )

    principles = route_contract.get(
        "routing_principles",
        {}
    )

    check(
        "Server-first routing",
        principles.get(
            "server_first"
        )
        is True,
        failures,
    )

    check(
        "Client components only when required",
        principles.get(
            "client_components_only_when_required"
        )
        is True,
        failures,
    )

    check(
        "No frontend prediction routes",
        principles.get(
            "frontend_prediction_routes"
        )
        is False,
        failures,
    )

    check(
        "No frontend API route handlers required",
        principles.get(
            "frontend_api_route_handlers_required"
        )
        is False,
        failures,
    )

    creation_policy = route_contract.get(
        "route_creation_policy",
        {}
    )

    check(
        "10.1.4 did not prematurely create feature pages",
        creation_policy.get(
            "10_1_4_creates_page_files"
        )
        is False,
        failures,
    )

    print(
        "\n4. STAGE 10.1.5 DOMAIN MODEL CONTRACT"
    )

    check(
        "Domain contract stage exact",
        domain_contract.get(
            "stage"
        )
        ==
        "10.1.5",
        failures,
    )

    check(
        "Domain contract version exact",
        domain_contract.get(
            "version"
        )
        ==
        "1.0.0",
        failures,
    )

    check(
        "Domain contract LOCKED",
        domain_contract.get(
            "status"
        )
        ==
        "LOCKED",
        failures,
    )

    check(
        "TypeScript source path exact",
        domain_contract.get(
            "typescript_source"
        )
        ==
        relative(
            DOMAIN_TYPES_FILE
        ),
        failures,
    )

    check(
        "TypeScript source SHA current",
        domain_contract.get(
            "typescript_sha256"
        )
        ==
        sha256_file(
            DOMAIN_TYPES_FILE
        ),
        failures,
    )

    design = domain_contract.get(
        "design",
        {}
    )

    check(
        "Domain models immutable",
        design.get(
            "immutable_models"
        )
        is True,
        failures,
    )

    check(
        "Readonly utility used",
        design.get(
            "typescript_readonly_utility"
        )
        is True,
        failures,
    )

    check(
        "Pick utility used",
        design.get(
            "typescript_pick_utility"
        )
        is True,
        failures,
    )

    check(
        "Stage 7 prediction authority retained",
        design.get(
            "prediction_authority"
        )
        ==
        "STAGE7",
        failures,
    )

    check(
        "Stage 8 context authority retained",
        design.get(
            "context_authority"
        )
        ==
        "STAGE8",
        failures,
    )

    check(
        "Stage 9 intelligence authority retained",
        design.get(
            "intelligence_authority"
        )
        ==
        "STAGE9",
        failures,
    )

    check(
        "Stage 10 presentation authority retained",
        design.get(
            "presentation_authority"
        )
        ==
        "STAGE10",
        failures,
    )

    check(
        "No frontend prediction logic",
        design.get(
            "frontend_prediction_logic"
        )
        is False,
        failures,
    )

    check(
        "No frontend context recalculation",
        design.get(
            "frontend_context_recalculation"
        )
        is False,
        failures,
    )

    check(
        "No frontend intelligence recalculation",
        design.get(
            "frontend_intelligence_recalculation"
        )
        is False,
        failures,
    )

    print(
        "\n5. REQUIRED TYPESCRIPT DOMAIN EXPORTS"
    )

    required_exports = {
        "OutcomeLabel",
        "ConfidenceBand",
        "UncertaintyBand",
        "ContextAlignment",
        "ContextSupportScore",
        "FixtureIdentity",
        "Stage7Prediction",
        "Stage9Intelligence",
        "MatchIntelligence",
        "MatchContextView",
        "MatchCardModel",
        "MatchDetailModel",
        "TeamMatchModel",
        "FixtureRouteParams",
        "TeamRouteParams",
        "UiDataState",
        "ProbabilityDisplay",
    }

    exported_domains = set(
        domain_contract.get(
            "exported_domains",
            []
        )
    )

    check(
        "Required domain exports declared",
        required_exports.issubset(
            exported_domains
        ),
        failures,
    )

    types_source = (
        DOMAIN_TYPES_FILE
        .read_text(
            encoding="utf-8"
        )
    )

    for name in sorted(
        required_exports
    ):

        check(
            f"TypeScript export exists: {name}",
            (
                f"export type {name}"
                in
                types_source
            )
            or
            (
                f"export interface {name}"
                in
                types_source
            ),
            failures,
        )

    print(
        "\n6. PREDICTION FIELD CONTRACT"
    )

    required_prediction_fields = {
        "fixture_id",
        "home_team_name",
        "away_team_name",

        "stage7_prob_home_win",
        "stage7_prob_draw",
        "stage7_prob_away_win",
        "stage7_predicted_label",
        "stage7_confidence",

        "stage9_top_probability",
        "stage9_probability_margin",

        "stage9_confidence_band",
        "stage9_uncertainty_band",

        "stage9_context_support_score",
        "stage9_context_alignment",

        "stage9_explanation_headline",
        "stage9_explanation_summary",
    }

    contract_fields = set(
        domain_contract.get(
            "core_stage9_fields",
            []
        )
    )

    check(
        "Core Stage 9 field set exact",
        contract_fields
        ==
        required_prediction_fields,
        failures,
    )

    for field in sorted(
        required_prediction_fields
    ):

        check(
            f"TypeScript field exists: {field}",
            field
            in
            types_source,
            failures,
        )

    print(
        "\n7. DISPLAY INTEGRITY"
    )

    display_rules = domain_contract.get(
        "display_rules",
        {}
    )

    check(
        "Display rounding permitted",
        display_rules.get(
            "display_rounding_allowed"
        )
        is True,
        failures,
    )

    check(
        "Display rounding cannot alter source",
        display_rules.get(
            "display_rounding_may_change_source"
        )
        is False,
        failures,
    )

    check(
        "Raw probability retained",
        display_rules.get(
            "raw_probability_retained"
        )
        is True,
        failures,
    )

    print(
        "\n8. RUNTIME VALIDATION BOUNDARY"
    )

    runtime_validation = domain_contract.get(
        "runtime_validation",
        {}
    )

    check(
        "Runtime validation not prematurely implemented",
        runtime_validation.get(
            "implemented_in_10_1_5"
        )
        is False,
        failures,
    )

    check(
        "Runtime validation owner = 10.2.6",
        runtime_validation.get(
            "owner"
        )
        ==
        "10.2.6",
        failures,
    )

    wire_schema = domain_contract.get(
        "wire_schema",
        {}
    )

    check(
        "Wire schema intentionally not finalized",
        wire_schema.get(
            "fully_locked_in_10_1_5"
        )
        is False,
        failures,
    )

    check(
        "Wire schema owner = 10.2.6",
        wire_schema.get(
            "finalization_owner"
        )
        ==
        "10.2.6",
        failures,
    )

    print(
        "\n9. DEPENDENCY FRESHNESS"
    )

    verify_dependency_identity(
        route_contract,
        "10.1.4",
        failures,
    )

    verify_dependency_identity(
        domain_contract,
        "10.1.5",
        failures,
    )

    print(
        "\n10. TYPESCRIPT COMPILER"
    )

    (
        typescript_ok,
        compiler_output,
    ) = run_typescript_check()

    check(
        "npx/TypeScript compiler --noEmit",
        typescript_ok,
        failures,
    )

    if (
        not typescript_ok
        and
        compiler_output
    ):

        print()

        print(
            "TypeScript compiler output:"
        )

        print(
            compiler_output
        )

    print(
        "\n11. NO PREMATURE PROMOTION"
    )

    route_promotion = route_contract.get(
        "promotion",
        {}
    )

    domain_promotion = domain_contract.get(
        "promotion",
        {}
    )

    check(
        "10.1.4 contract did not self-promote",
        route_promotion.get(
            "stage10_1_4_complete"
        )
        is False,
        failures,
    )

    check(
        "10.1.5 contract did not self-promote",
        domain_promotion.get(
            "stage10_1_5_complete"
        )
        is False,
        failures,
    )

    check(
        "Stage 10.1 remains incomplete",
        (
            route_promotion.get(
                "stage10_1_complete"
            )
            is False
            and
            domain_promotion.get(
                "stage10_1_complete"
            )
            is False
        ),
        failures,
    )

    check(
        "Stage 10 remains incomplete",
        (
            route_promotion.get(
                "stage10_complete"
            )
            is False
            and
            domain_promotion.get(
                "stage10_complete"
            )
            is False
        ),
        failures,
    )

    print(
        "\n12. SAVE VERIFICATION EVIDENCE"
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
                "10.1.4-10.1.5",

            "name":
                (
                    "FRONTEND_ROUTE_ARCHITECTURE_"
                    "AND_TYPESCRIPT_DOMAIN_VERIFICATION"
                ),

            "status":
                "PASS",

            "stage_10_1_4_complete":
                True,

            "stage_10_1_5_complete":
                True,

            "route_architecture":
                "LOCKED_AND_VERIFIED",

            "typescript_domain_models":
                "LOCKED_AND_VERIFIED",

            "router":
                "NEXTJS_APP_ROUTER",

            "user_facing_route_count":
                3,

            "typescript_compiler":
                "PASS",

            "authority": {
                "stage7":
                    "PREDICTION",

                "stage8":
                    "CONTEXT",

                "stage9":
                    "INTELLIGENCE",

                "stage10":
                    "PRESENTATION",
            },

            "safety": {
                "frontend_prediction_logic":
                    False,

                "frontend_context_recalculation":
                    False,

                "frontend_intelligence_recalculation":
                    False,

                "direct_artifact_access":
                    False,

                "feature_pages_created":
                    False,

                "runtime_validation_prematurely_implemented":
                    False,
            },

            "dependency_identity": {
                relative(
                    AUDIT_FILE
                ): {
                    "sha256":
                        sha256_file(
                            AUDIT_FILE
                        )
                },

                relative(
                    RESPONSIBILITY_FILE
                ): {
                    "sha256":
                        sha256_file(
                            RESPONSIBILITY_FILE
                        )
                },

                relative(
                    ENDPOINT_CONTRACT_FILE
                ): {
                    "sha256":
                        sha256_file(
                            ENDPOINT_CONTRACT_FILE
                        )
                },

                relative(
                    STAGE_10_1_3_FILE
                ): {
                    "sha256":
                        sha256_file(
                            STAGE_10_1_3_FILE
                        )
                },

                relative(
                    ROUTE_CONTRACT_FILE
                ): {
                    "sha256":
                        sha256_file(
                            ROUTE_CONTRACT_FILE
                        )
                },

                relative(
                    DOMAIN_CONTRACT_FILE
                ): {
                    "sha256":
                        sha256_file(
                            DOMAIN_CONTRACT_FILE
                        )
                },

                relative(
                    DOMAIN_TYPES_FILE
                ): {
                    "sha256":
                        sha256_file(
                            DOMAIN_TYPES_FILE
                        )
                },
            },

            "verified_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "stage10_ready_for_10_1_6":
                True,

            "stage10_1_complete":
                False,

            "stage10_complete":
                False,

            "next_stage":
                "10.1.6",

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
            "STAGE 10.1.4: PASS"
        )

        print(
            "FRONTEND ROUTE ARCHITECTURE: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10.1.5: PASS"
        )

        print(
            "TYPESCRIPT DOMAIN MODELS: LOCKED AND VERIFIED"
        )

        print()

        print(
            "STAGE 10 READY FOR 10.1.6"
        )

        print(
            "STAGE 10 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 10.1.4 / 10.1.5: FAIL"
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
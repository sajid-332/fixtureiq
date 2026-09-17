from __future__ import annotations

import hashlib
import json
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


PREVIOUS_VERIFICATION_FILE = (
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


def load_json(
    path: Path,
) -> dict:

    if not path.exists():
        raise RuntimeError(
            f"Missing required artifact: {path}"
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


def identity(
    path: Path,
) -> dict:

    return {
        "sha256":
            sha256_file(path)
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

    temporary.replace(path)


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


RESULT_SOURCE = r'''/*
 * FixtureIQ Stage 10.2.7
 *
 * Maps validated backend responses into the
 * locked Stage 10 UI runtime states.
 *
 * No retry.
 * No cache fallback.
 * No stale data preservation.
 * No prediction/context/intelligence mutation.
 */

import type {
  FixtureIqApiJsonResponse,
} from "./client";

import type {
  JsonValue,
} from "./validation";


export type ApiTerminalState =
  | "READY"
  | "NOT_FOUND"
  | "NOT_READY"
  | "CONNECTION_ERROR";


export type ApiConnectionFailure =
  | "NETWORK_ERROR"
  | "INVALID_RESPONSE"
  | "UNEXPECTED_HTTP_STATUS";


export type ApiReadyResult =
  Readonly<{
    state:
      "READY";

    status:
      200;

    data:
      JsonValue;

    failure:
      null;
  }>;


export type ApiNotFoundResult =
  Readonly<{
    state:
      "NOT_FOUND";

    status:
      404;

    failure:
      "NOT_FOUND";
  }>;


export type ApiNotReadyResult =
  Readonly<{
    state:
      "NOT_READY";

    status:
      503;

    failure:
      "NOT_READY";
  }>;


export type ApiConnectionErrorResult =
  Readonly<{
    state:
      "CONNECTION_ERROR";

    status:
      number | null;

    failure:
      ApiConnectionFailure;
  }>;


export type ApiRequestResult =
  | ApiReadyResult
  | ApiNotFoundResult
  | ApiNotReadyResult
  | ApiConnectionErrorResult;


function getErrorName(
  error: unknown
): string | null {

  if (
    error instanceof Error
  ) {
    return error.name;
  }

  if (
    typeof error === "object"
    &&
    error !== null
    &&
    "name" in error
    &&
    typeof (
      error as {
        readonly name?: unknown;
      }
    ).name
    ===
    "string"
  ) {
    return (
      error as {
        readonly name: string;
      }
    ).name;
  }

  return null;
}


function getErrorMessage(
  error: unknown
): string {

  if (
    error instanceof Error
  ) {
    return error.message;
  }

  return "";
}


function isInvalidResponseError(
  error: unknown
): boolean {

  const name =
    getErrorName(error);

  const message =
    getErrorMessage(error);

  return (
    name ===
    "ApiValidationError"
    ||
    name ===
    "SyntaxError"
    ||
    message.includes(
      "FixtureIQ backend returned a non-JSON response."
    )
  );
}


function connectionError(
  failure:
    ApiConnectionFailure,
  status:
    number | null
): ApiConnectionErrorResult {

  return {
    state:
      "CONNECTION_ERROR",

    status,

    failure,
  };
}


export async function mapValidatedApiRequest(
  request:
    () =>
      Promise<
        FixtureIqApiJsonResponse<JsonValue>
      >
): Promise<ApiRequestResult> {

  try {

    const response =
      await request();


    if (
      response.status === 200
      &&
      response.ok
    ) {
      return {
        state:
          "READY",

        status:
          200,

        data:
          response.data,

        failure:
          null,
      };
    }


    if (
      response.status === 404
    ) {
      return {
        state:
          "NOT_FOUND",

        status:
          404,

        failure:
          "NOT_FOUND",
      };
    }


    if (
      response.status === 503
    ) {
      return {
        state:
          "NOT_READY",

        status:
          503,

        failure:
          "NOT_READY",
      };
    }


    return connectionError(
      "UNEXPECTED_HTTP_STATUS",
      response.status
    );

  } catch (error) {

    if (
      isInvalidResponseError(
        error
      )
    ) {
      return connectionError(
        "INVALID_RESPONSE",
        null
      );
    }


    return connectionError(
      "NETWORK_ERROR",
      null
    );
  }
}
'''


RUNTIME_TEST_SOURCE = r'''import fs from "node:fs";
import { Buffer } from "node:buffer";
import ts from "typescript";


const sourceUrl =
  new URL(
    "../lib/api/result.ts",
    import.meta.url
  );


const source =
  fs.readFileSync(
    sourceUrl,
    "utf8"
  );


const transpiled =
  ts.transpileModule(
    source,
    {
      compilerOptions: {
        target:
          ts.ScriptTarget.ES2022,

        module:
          ts.ModuleKind.ES2022,

        strict:
          true,
      },
    }
  );


const moduleUrl =
  "data:text/javascript;base64,"
  +
  Buffer
    .from(
      transpiled.outputText,
      "utf8"
    )
    .toString("base64");


const {
  mapValidatedApiRequest,
} =
  await import(moduleUrl);


function assert(
  condition,
  label
) {

  if (!condition) {

    console.error(
      `${label}: FAIL`
    );

    process.exitCode = 1;

    return;
  }

  console.log(
    `${label}: PASS`
  );
}


const readyPayload = {
  fixture_id:
    "fixture-1",

  value:
    0.5046,
};


const ready =
  await mapValidatedApiRequest(
    async () => ({
      status:
        200,

      ok:
        true,

      data:
        readyPayload,
    })
  );


assert(
  ready.state ===
  "READY",
  "HTTP 200 maps to READY"
);


assert(
  ready.status === 200,
  "READY preserves HTTP 200"
);


assert(
  ready.data ===
  readyPayload,
  "READY preserves payload identity"
);


const notFound =
  await mapValidatedApiRequest(
    async () => ({
      status:
        404,

      ok:
        false,

      data: {
        status:
          "NOT_FOUND",
      },
    })
  );


assert(
  notFound.state ===
  "NOT_FOUND",
  "HTTP 404 maps to NOT_FOUND"
);


assert(
  !(
    "data"
    in
    notFound
  ),
  "404 contains no stale data"
);


const notReady =
  await mapValidatedApiRequest(
    async () => ({
      status:
        503,

      ok:
        false,

      data: {
        status:
          "NOT_READY",
      },
    })
  );


assert(
  notReady.state ===
  "NOT_READY",
  "HTTP 503 maps to NOT_READY"
);


assert(
  !(
    "data"
    in
    notReady
  ),
  "503 contains no stale data"
);


const unexpected =
  await mapValidatedApiRequest(
    async () => ({
      status:
        500,

      ok:
        false,

      data: {
        status:
          "ERROR",
      },
    })
  );


assert(
  unexpected.state ===
  "CONNECTION_ERROR"
  &&
  unexpected.failure ===
  "UNEXPECTED_HTTP_STATUS"
  &&
  unexpected.status ===
  500,
  "Unexpected HTTP maps to CONNECTION_ERROR"
);


const inconsistent200 =
  await mapValidatedApiRequest(
    async () => ({
      status:
        200,

      ok:
        false,

      data: {
        status:
          "ERROR",
      },
    })
  );


assert(
  inconsistent200.state ===
  "CONNECTION_ERROR"
  &&
  inconsistent200.failure ===
  "UNEXPECTED_HTTP_STATUS",
  "Invalid HTTP 200 state fails closed"
);


const network =
  await mapValidatedApiRequest(
    async () => {
      throw new TypeError(
        "fetch failed"
      );
    }
  );


assert(
  network.state ===
  "CONNECTION_ERROR"
  &&
  network.failure ===
  "NETWORK_ERROR"
  &&
  network.status ===
  null,
  "Network failure maps to CONNECTION_ERROR"
);


const validationError =
  await mapValidatedApiRequest(
    async () => {

      const error =
        new TypeError(
          "schema rejected"
        );

      error.name =
        "ApiValidationError";

      throw error;
    }
  );


assert(
  validationError.state ===
  "CONNECTION_ERROR"
  &&
  validationError.failure ===
  "INVALID_RESPONSE",
  "Validation failure maps to CONNECTION_ERROR"
);


const malformedJson =
  await mapValidatedApiRequest(
    async () => {
      throw new SyntaxError(
        "Unexpected token"
      );
    }
  );


assert(
  malformedJson.state ===
  "CONNECTION_ERROR"
  &&
  malformedJson.failure ===
  "INVALID_RESPONSE",
  "Malformed JSON maps to CONNECTION_ERROR"
);


const nonJson =
  await mapValidatedApiRequest(
    async () => {
      throw new TypeError(
        "FixtureIQ backend returned a non-JSON response."
      );
    }
  );


assert(
  nonJson.state ===
  "CONNECTION_ERROR"
  &&
  nonJson.failure ===
  "INVALID_RESPONSE",
  "Non-JSON response maps to CONNECTION_ERROR"
);


const firstRequest =
  await mapValidatedApiRequest(
    async () => ({
      status:
        200,

      ok:
        true,

      data: {
        fixture_id:
          "old-fixture",
      },
    })
  );


const secondRequest =
  await mapValidatedApiRequest(
    async () => ({
      status:
        503,

      ok:
        false,

      data: {
        status:
          "NOT_READY",
      },
    })
  );


assert(
  firstRequest.state ===
  "READY"
  &&
  secondRequest.state ===
  "NOT_READY"
  &&
  !(
    "data"
    in
    secondRequest
  ),
  "Failed refresh cannot reuse previous READY payload"
);


if (
  process.exitCode
  !==
  1
) {
  console.log(
    "STAGE 10.2.7 HTTP / ERROR-STATE MAPPING TESTS: PASS"
  );
}
'''


def validated_name(
    raw_name: str,
) -> str:

    if not raw_name.startswith(
        "get"
    ):
        raise RuntimeError(
            f"Unexpected API function: {raw_name}"
        )

    return (
        "getValidated"
        +
        raw_name[3:]
    )


def result_name(
    raw_name: str,
) -> str:

    return (
        raw_name
        +
        "Result"
    )


def parameter_type(
    parameter: str,
) -> str:

    if (
        parameter
        ==
        "team_name"
    ):
        return "string"

    return "string | number"


def camel_case(
    value: str,
) -> str:

    parts = value.split("_")

    return (
        parts[0]
        +
        "".join(
            part[:1].upper()
            +
            part[1:]

            for part in parts[1:]
        )
    )


def render_wrapper(
    raw_name: str,
    parameters: list[str],
) -> str:

    validated = validated_name(
        raw_name
    )

    output = result_name(
        raw_name
    )

    parameter_variables = [
        camel_case(parameter)

        for parameter
        in parameters
    ]

    lines = [
        f"export function {output}(",
    ]

    for (
        source_parameter,
        variable,
    ) in zip(
        parameters,
        parameter_variables,
        strict=True,
    ):

        lines.append(
            (
                f"  {variable}: "
                f"{parameter_type(source_parameter)},"
            )
        )

    lines.append(
        (
            "  options: "
            "FixtureIqApiGetOptions = {}"
        )
    )

    lines.extend(
        [
            "): Promise<ApiRequestResult> {",
            "  return mapValidatedApiRequest(",
            "    () =>",
            f"      validatedApi.{validated}(",
        ]
    )

    for variable in (
        parameter_variables
    ):

        lines.append(
            f"        {variable},"
        )

    lines.extend(
        [
            "        options",
            "      )",
            "  );",
            "}",
            "",
            "",
        ]
    )

    return "\n".join(lines)


def build_mapped_source(
    production_functions: list[dict],
    context_functions: list[dict],
) -> tuple[str, list[dict]]:

    intelligence = [
        {
            "function":
                "getIntelligenceStatus",

            "parameters":
                [],
        },
        {
            "function":
                "getIntelligenceMatches",

            "parameters":
                [],
        },
        {
            "function":
                "getIntelligenceMatch",

            "parameters": [
                "fixture_id"
            ],
        },
        {
            "function":
                "getTeamIntelligence",

            "parameters": [
                "team_name"
            ],
        },
        {
            "function":
                "getUpcomingIntelligence",

            "parameters":
                [],
        },
    ]

    all_entries = (
        intelligence
        +
        production_functions
        +
        context_functions
    )

    lines = [
        'import "server-only";',
        "",
        'import type {',
        "  FixtureIqApiGetOptions,",
        '} from "./client";',
        "",
        'import * as validatedApi',
        '  from "./validated";',
        "",
        'import {',
        "  mapValidatedApiRequest,",
        "  type ApiRequestResult,",
        '} from "./result";',
        "",
        "",
    ]

    mapped_contract = []

    for entry in all_entries:

        raw_name = str(
            entry.get(
                "function",
                "",
            )
        )

        parameters = list(
            entry.get(
                "parameters",
                [],
            )
        )

        lines.append(
            render_wrapper(
                raw_name,
                parameters,
            )
        )

        mapped_contract.append(
            {
                "source_function":
                    raw_name,

                "validated_function":
                    validated_name(
                        raw_name
                    ),

                "result_function":
                    result_name(
                        raw_name
                    ),

                "parameters":
                    parameters,
            }
        )

    return (
        "\n".join(lines).rstrip()
        +
        "\n",
        mapped_contract,
    )


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.2.7"
    )

    print(
        "HTTP / ERROR-STATE MAPPING BUILD"
    )

    print("=" * 72)


    previous = load_json(
        PREVIOUS_VERIFICATION_FILE
    )

    validation_contract = load_json(
        VALIDATION_CONTRACT_FILE
    )

    intelligence_contract = load_json(
        INTELLIGENCE_CONTRACT_FILE
    )

    production_contract = load_json(
        PRODUCTION_CONTRACT_FILE
    )

    context_contract = load_json(
        CONTEXT_CONTRACT_FILE
    )


    if (
        previous.get("status")
        !=
        "PASS"
    ):
        raise RuntimeError(
            "10.2.5-10.2.6 verification is not PASS."
        )


    if (
        previous.get(
            "stage10_ready_for_10_2_7"
        )
        is not True
    ):
        raise RuntimeError(
            "10.2.6 did not authorize 10.2.7."
        )


    for label, payload in [
        (
            "validation contract",
            validation_contract,
        ),
        (
            "intelligence contract",
            intelligence_contract,
        ),
        (
            "production contract",
            production_contract,
        ),
        (
            "context contract",
            context_contract,
        ),
    ]:

        if (
            payload.get("status")
            !=
            "LOCKED"
        ):
            raise RuntimeError(
                f"{label} is not LOCKED."
            )


    production_functions = list(
        production_contract.get(
            "generated_functions",
            []
        )
    )

    context_functions = list(
        context_contract.get(
            "generated_functions",
            []
        )
    )


    mapped_source, mapped_functions = (
        build_mapped_source(
            production_functions,
            context_functions,
        )
    )


    save_text_atomic(
        RESULT_FILE,
        RESULT_SOURCE,
    )

    save_text_atomic(
        MAPPED_FILE,
        mapped_source,
    )

    save_text_atomic(
        RUNTIME_TEST_FILE,
        RUNTIME_TEST_SOURCE,
    )


    contract = {
        "stage":
            "10.2.7",

        "version":
            "1.0.0",

        "name":
            "FRONTEND_HTTP_ERROR_STATE_MAPPING",

        "status":
            "LOCKED",

        "result_mapper_source":
            relative(
                RESULT_FILE
            ),

        "mapped_api_source":
            relative(
                MAPPED_FILE
            ),

        "runtime_test_source":
            relative(
                RUNTIME_TEST_FILE
            ),

        "mapping": {
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
        },

        "ready_policy": {
            "requires_http_200":
                True,

            "requires_response_ok":
                True,

            "payload_preserved":
                True,

            "payload_recalculated":
                False,

            "payload_mutated":
                False,
        },

        "failure_policy": {
            "failure_payload_exposed_as_ready_data":
                False,

            "previous_ready_payload_preserved":
                False,

            "stale_fallback":
                False,

            "automatic_retry":
                False,

            "silent_status_coercion":
                False,

            "fail_closed":
                True,
        },

        "error_classification": {
            "ApiValidationError":
                "INVALID_RESPONSE",

            "SyntaxError":
                "INVALID_RESPONSE",

            "non_json_backend_response":
                "INVALID_RESPONSE",

            "fetch_or_transport_failure":
                "NETWORK_ERROR",

            "other_http_status":
                "UNEXPECTED_HTTP_STATUS",
        },

        "mapped_functions":
            mapped_functions,

        "mapped_function_count":
            len(
                mapped_functions
            ),

        "responsibility": {
            "stage7_prediction_authority":
                True,

            "stage8_context_authority":
                True,

            "stage9_intelligence_authority":
                True,

            "stage10_presentation_authority":
                True,

            "prediction_logic_added":
                False,

            "probabilities_modified":
                False,

            "context_modified":
                False,

            "intelligence_modified":
                False,

            "provider_access":
                False,

            "artifact_access":
                False,
        },

        "source_identity": {
            relative(
                RESULT_FILE
            ):
                identity(
                    RESULT_FILE
                ),

            relative(
                MAPPED_FILE
            ):
                identity(
                    MAPPED_FILE
                ),

            relative(
                RUNTIME_TEST_FILE
            ):
                identity(
                    RUNTIME_TEST_FILE
                ),
        },

        "dependency_identity": {
            relative(
                PREVIOUS_VERIFICATION_FILE
            ):
                identity(
                    PREVIOUS_VERIFICATION_FILE
                ),

            relative(
                VALIDATION_CONTRACT_FILE
            ):
                identity(
                    VALIDATION_CONTRACT_FILE
                ),

            relative(
                INTELLIGENCE_CONTRACT_FILE
            ):
                identity(
                    INTELLIGENCE_CONTRACT_FILE
                ),

            relative(
                PRODUCTION_CONTRACT_FILE
            ):
                identity(
                    PRODUCTION_CONTRACT_FILE
                ),

            relative(
                CONTEXT_CONTRACT_FILE
            ):
                identity(
                    CONTEXT_CONTRACT_FILE
                ),
        },

        "promotion": {
            "stage10_2_7_complete":
                False,

            "stage10_2_complete":
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
        CONTRACT_FILE,
        contract,
    )


    print()

    print(
        "Locked terminal mapping:"
    )

    print(
        "  HTTP 200 -> READY"
    )

    print(
        "  HTTP 404 -> NOT_FOUND"
    )

    print(
        "  HTTP 503 -> NOT_READY"
    )

    print(
        "  Network -> CONNECTION_ERROR"
    )

    print(
        "  Invalid response -> CONNECTION_ERROR"
    )

    print(
        "  Unexpected HTTP -> CONNECTION_ERROR"
    )

    print()

    print(
        "Mapped API wrappers:"
    )

    print(
        f"  {len(mapped_functions)}"
    )

    print()

    print("=" * 72)

    print(
        "STAGE 10.2.7 HTTP / ERROR-STATE MAPPING: BUILT"
    )

    print(
        "STAGE 10 IS NOT YET PROMOTED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
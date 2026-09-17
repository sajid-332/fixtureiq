import fs from "node:fs";
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

/*
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

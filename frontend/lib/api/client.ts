import "server-only";

import {
  getFixtureIqApiBaseUrl,
} from "./config";


const ALLOWED_API_NAMESPACES = [
  "/api/health",
  "/api/v1/production",
  "/api/v1/context",
  "/api/v1/intelligence",
] as const;


export type FixtureIqApiGetOptions =
  Readonly<{
    signal?: AbortSignal;
  }>;


export type FixtureIqApiJsonResponse<
  T = unknown
> =
  Readonly<{
    status: number;
    ok: boolean;
    data: T;
  }>;


function isAllowedApiPath(
  pathname: string
): boolean {
  return (
    pathname
    ===
    "/api/health"
    ||
    ALLOWED_API_NAMESPACES
      .slice(1)
      .some(
        (namespace) =>
          pathname === namespace
          ||
          pathname.startsWith(
            `${namespace}/`
          )
      )
  );
}


export function buildFixtureIqApiUrl(
  pathname: string
): URL {
  if (
    !pathname.startsWith("/")
  ) {
    throw new Error(
      "FixtureIQ API paths must begin with '/'."
    );
  }

  if (
    pathname.startsWith("//")
  ) {
    throw new Error(
      "Protocol-relative API URLs are forbidden."
    );
  }

  const baseUrl =
    getFixtureIqApiBaseUrl();

  const base =
    new URL(
      `${baseUrl}/`
    );

  const url =
    new URL(
      pathname,
      base
    );

  if (
    url.origin
    !==
    base.origin
  ) {
    throw new Error(
      "Cross-origin API path override is forbidden."
    );
  }

  if (
    url.search
    ||
    url.hash
  ) {
    throw new Error(
      "Query strings and fragments are not supported by the shared client contract."
    );
  }

  if (
    !isAllowedApiPath(
      url.pathname
    )
  ) {
    throw new Error(
      `Frontend access to API path is not allowed: ${url.pathname}`
    );
  }

  return url;
}


async function parseJsonResponse<
  T
>(
  response: Response
): Promise<T> {
  const contentType =
    response.headers
      .get("content-type")
      ?.toLowerCase()
    ??
    "";

  if (
    !contentType.includes(
      "application/json"
    )
  ) {
    throw new TypeError(
      [
        "FixtureIQ backend returned",
        "a non-JSON response.",
      ].join(" ")
    );
  }

  return (
    await response.json()
  ) as T;
}


export async function fixtureIqApiGet<
  T = unknown
>(
  pathname: string,
  options:
    FixtureIqApiGetOptions
    =
    {}
): Promise<
  FixtureIqApiJsonResponse<T>
> {
  const url =
    buildFixtureIqApiUrl(
      pathname
    );

  const response =
    await fetch(
      url,
      {
        method:
          "GET",

        headers: {
          Accept:
            "application/json",
        },

        cache:
          "no-store",

        credentials:
          "omit",

        redirect:
          "error",

        signal:
          options.signal,
      }
    );

  const data =
    await parseJsonResponse<T>(
      response
    );

  return {
    status:
      response.status,

    ok:
      response.ok,

    data,
  };
}
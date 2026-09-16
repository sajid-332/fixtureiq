import "server-only";


export const FIXTUREIQ_API_BASE_URL_ENV =
  "FIXTUREIQ_API_BASE_URL" as const;


const DEVELOPMENT_API_BASE_URL =
  "http://127.0.0.1:5000";


export type FixtureIqApiEnvironment =
  Readonly<{
    baseUrl: string;

    source:
      | "environment"
      | "development_default";
  }>;


function normalizeApiBaseUrl(
  rawValue: string
): string {
  const value = rawValue.trim();

  if (!value) {
    throw new Error(
      "FixtureIQ API base URL is empty."
    );
  }

  const url = new URL(value);

  if (
    url.protocol !== "http:"
    &&
    url.protocol !== "https:"
  ) {
    throw new Error(
      "FixtureIQ API base URL must use HTTP or HTTPS."
    );
  }

  if (
    url.username
    ||
    url.password
  ) {
    throw new Error(
      "FixtureIQ API base URL must not contain credentials."
    );
  }

  if (
    url.pathname !== "/"
    &&
    url.pathname !== ""
  ) {
    throw new Error(
      "FixtureIQ API base URL must contain only the origin."
    );
  }

  if (url.search) {
    throw new Error(
      "FixtureIQ API base URL must not contain query parameters."
    );
  }

  if (url.hash) {
    throw new Error(
      "FixtureIQ API base URL must not contain a fragment."
    );
  }

  return url.origin;
}


export function getFixtureIqApiEnvironment():
  FixtureIqApiEnvironment {

  const configuredValue =
    process.env
      .FIXTUREIQ_API_BASE_URL
      ?.trim();

  if (configuredValue) {
    return {
      baseUrl:
        normalizeApiBaseUrl(
          configuredValue
        ),

      source:
        "environment",
    };
  }

  if (
    process.env.NODE_ENV
    ===
    "production"
  ) {
    throw new Error(
      [
        `${FIXTUREIQ_API_BASE_URL_ENV} is required`,
        "when the FixtureIQ frontend runs in production.",
      ].join(" ")
    );
  }

  return {
    baseUrl:
      normalizeApiBaseUrl(
        DEVELOPMENT_API_BASE_URL
      ),

    source:
      "development_default",
  };
}


export function getFixtureIqApiBaseUrl():
  string {

  return (
    getFixtureIqApiEnvironment()
      .baseUrl
  );
}
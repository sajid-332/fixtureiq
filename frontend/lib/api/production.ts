import "server-only";

import {
  fixtureIqApiGet,
  type FixtureIqApiGetOptions,
  type FixtureIqApiJsonResponse,
} from "./client";


export const PRODUCTION_API_ROUTES = {
  HEALTH:
    "/api/v1/production/health",

  READINESS:
    "/api/v1/production/readiness",

  STATUS:
    "/api/v1/production/status",

} as const;


export type ProductionApiResponse =
  FixtureIqApiJsonResponse<unknown>;

export function getProductionHealth(
  options: FixtureIqApiGetOptions = {}
): Promise<ProductionApiResponse> {
  return fixtureIqApiGet<unknown>(
    "/api/v1/production/health",
    options
  );
}


export function getProductionReadiness(
  options: FixtureIqApiGetOptions = {}
): Promise<ProductionApiResponse> {
  return fixtureIqApiGet<unknown>(
    "/api/v1/production/readiness",
    options
  );
}


export function getProductionStatus(
  options: FixtureIqApiGetOptions = {}
): Promise<ProductionApiResponse> {
  return fixtureIqApiGet<unknown>(
    "/api/v1/production/status",
    options
  );
}

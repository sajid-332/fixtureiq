import "server-only";

import {
  fixtureIqApiGet,
  type FixtureIqApiGetOptions,
  type FixtureIqApiJsonResponse,
} from "./client";


export const INTELLIGENCE_API_ROUTES = {
  STATUS:
    "/api/v1/intelligence/status",

  MATCHES:
    "/api/v1/intelligence/matches",

  MATCH:
    "/api/v1/intelligence/matches/<fixture_id>",

  TEAM:
    "/api/v1/intelligence/team/<path:team_name>",

  UPCOMING:
    "/api/v1/intelligence/upcoming",
} as const;


export type IntelligenceApiResponse =
  FixtureIqApiJsonResponse<unknown>;


export function getIntelligenceStatus(
  options: FixtureIqApiGetOptions = {}
): Promise<IntelligenceApiResponse> {
  return fixtureIqApiGet<unknown>(
    "/api/v1/intelligence/status",
    options
  );
}


export function getIntelligenceMatches(
  options: FixtureIqApiGetOptions = {}
): Promise<IntelligenceApiResponse> {
  return fixtureIqApiGet<unknown>(
    "/api/v1/intelligence/matches",
    options
  );
}


export function getIntelligenceMatch(
  fixtureId: string | number,
  options: FixtureIqApiGetOptions = {}
): Promise<IntelligenceApiResponse> {
  const encodedFixtureId =
    encodeURIComponent(
      String(fixtureId)
    );

  return fixtureIqApiGet<unknown>(
    `/api/v1/intelligence/matches/${encodedFixtureId}`,
    options
  );
}


export function getTeamIntelligence(
  teamName: string,
  options: FixtureIqApiGetOptions = {}
): Promise<IntelligenceApiResponse> {
  const encodedTeamName =
    encodeURIComponent(
      teamName
    );

  return fixtureIqApiGet<unknown>(
    `/api/v1/intelligence/team/${encodedTeamName}`,
    options
  );
}


export function getUpcomingIntelligence(
  options: FixtureIqApiGetOptions = {}
): Promise<IntelligenceApiResponse> {
  return fixtureIqApiGet<unknown>(
    "/api/v1/intelligence/upcoming",
    options
  );
}

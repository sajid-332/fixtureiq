import "server-only";

import {
  fixtureIqApiGet,
  type FixtureIqApiGetOptions,
  type FixtureIqApiJsonResponse,
} from "./client";


export const CONTEXT_API_ROUTES = {
  FIXTURES:
    "/api/v1/context/fixtures",

  FIXTURES_BY_FIXTURE_ID:
    "/api/v1/context/fixtures/<fixture_id>",

  FIXTURES_TEAM_BY_TEAM_NAME:
    "/api/v1/context/fixtures/team/<path:team_name>",

  FORM:
    "/api/v1/context/form",

  FORM_BY_TEAM_NAME:
    "/api/v1/context/form/<path:team_name>",

  STANDINGS:
    "/api/v1/context/standings",

  STANDINGS_BY_TEAM_NAME:
    "/api/v1/context/standings/<path:team_name>",

  STATUS:
    "/api/v1/context/status",

  TEAMS:
    "/api/v1/context/teams",

  TEAMS_BY_TEAM_NAME:
    "/api/v1/context/teams/<path:team_name>",

} as const;


export type ContextApiResponse =
  FixtureIqApiJsonResponse<unknown>;

export function getContextFixtures(
  options: FixtureIqApiGetOptions = {}
): Promise<ContextApiResponse> {
  return fixtureIqApiGet<unknown>(
    "/api/v1/context/fixtures",
    options
  );
}


export function getContextFixturesByFixtureId(
  fixtureId: string | number,
  options: FixtureIqApiGetOptions = {}
): Promise<ContextApiResponse> {
  return fixtureIqApiGet<unknown>(
    `/api/v1/context/fixtures/${encodeURIComponent(String(fixtureId))}`,
    options
  );
}


export function getContextFixturesTeamByTeamName(
  teamName: string | number,
  options: FixtureIqApiGetOptions = {}
): Promise<ContextApiResponse> {
  return fixtureIqApiGet<unknown>(
    `/api/v1/context/fixtures/team/${encodeURIComponent(String(teamName))}`,
    options
  );
}


export function getContextForm(
  options: FixtureIqApiGetOptions = {}
): Promise<ContextApiResponse> {
  return fixtureIqApiGet<unknown>(
    "/api/v1/context/form",
    options
  );
}


export function getContextFormByTeamName(
  teamName: string | number,
  options: FixtureIqApiGetOptions = {}
): Promise<ContextApiResponse> {
  return fixtureIqApiGet<unknown>(
    `/api/v1/context/form/${encodeURIComponent(String(teamName))}`,
    options
  );
}


export function getContextStandings(
  options: FixtureIqApiGetOptions = {}
): Promise<ContextApiResponse> {
  return fixtureIqApiGet<unknown>(
    "/api/v1/context/standings",
    options
  );
}


export function getContextStandingsByTeamName(
  teamName: string | number,
  options: FixtureIqApiGetOptions = {}
): Promise<ContextApiResponse> {
  return fixtureIqApiGet<unknown>(
    `/api/v1/context/standings/${encodeURIComponent(String(teamName))}`,
    options
  );
}


export function getContextStatus(
  options: FixtureIqApiGetOptions = {}
): Promise<ContextApiResponse> {
  return fixtureIqApiGet<unknown>(
    "/api/v1/context/status",
    options
  );
}


export function getContextTeams(
  options: FixtureIqApiGetOptions = {}
): Promise<ContextApiResponse> {
  return fixtureIqApiGet<unknown>(
    "/api/v1/context/teams",
    options
  );
}


export function getContextTeamsByTeamName(
  teamName: string | number,
  options: FixtureIqApiGetOptions = {}
): Promise<ContextApiResponse> {
  return fixtureIqApiGet<unknown>(
    `/api/v1/context/teams/${encodeURIComponent(String(teamName))}`,
    options
  );
}

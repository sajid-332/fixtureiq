import "server-only";

import type {
  FixtureIqApiGetOptions,
} from "./client";

import * as validatedApi
  from "./validated";

import {
  mapValidatedApiRequest,
  type ApiRequestResult,
} from "./result";


export function getIntelligenceStatusResult(
  options: FixtureIqApiGetOptions = {}
): Promise<ApiRequestResult> {
  return mapValidatedApiRequest(
    () =>
      validatedApi.getValidatedIntelligenceStatus(
        options
      )
  );
}


export function getIntelligenceMatchesResult(
  options: FixtureIqApiGetOptions = {}
): Promise<ApiRequestResult> {
  return mapValidatedApiRequest(
    () =>
      validatedApi.getValidatedIntelligenceMatches(
        options
      )
  );
}


export function getIntelligenceMatchResult(
  fixtureId: string | number,
  options: FixtureIqApiGetOptions = {}
): Promise<ApiRequestResult> {
  return mapValidatedApiRequest(
    () =>
      validatedApi.getValidatedIntelligenceMatch(
        fixtureId,
        options
      )
  );
}


export function getTeamIntelligenceResult(
  teamName: string,
  options: FixtureIqApiGetOptions = {}
): Promise<ApiRequestResult> {
  return mapValidatedApiRequest(
    () =>
      validatedApi.getValidatedTeamIntelligence(
        teamName,
        options
      )
  );
}


export function getUpcomingIntelligenceResult(
  options: FixtureIqApiGetOptions = {}
): Promise<ApiRequestResult> {
  return mapValidatedApiRequest(
    () =>
      validatedApi.getValidatedUpcomingIntelligence(
        options
      )
  );
}


export function getProductionHealthResult(
  options: FixtureIqApiGetOptions = {}
): Promise<ApiRequestResult> {
  return mapValidatedApiRequest(
    () =>
      validatedApi.getValidatedProductionHealth(
        options
      )
  );
}


export function getProductionReadinessResult(
  options: FixtureIqApiGetOptions = {}
): Promise<ApiRequestResult> {
  return mapValidatedApiRequest(
    () =>
      validatedApi.getValidatedProductionReadiness(
        options
      )
  );
}


export function getProductionStatusResult(
  options: FixtureIqApiGetOptions = {}
): Promise<ApiRequestResult> {
  return mapValidatedApiRequest(
    () =>
      validatedApi.getValidatedProductionStatus(
        options
      )
  );
}


export function getContextFixturesResult(
  options: FixtureIqApiGetOptions = {}
): Promise<ApiRequestResult> {
  return mapValidatedApiRequest(
    () =>
      validatedApi.getValidatedContextFixtures(
        options
      )
  );
}


export function getContextFixturesByFixtureIdResult(
  fixtureId: string | number,
  options: FixtureIqApiGetOptions = {}
): Promise<ApiRequestResult> {
  return mapValidatedApiRequest(
    () =>
      validatedApi.getValidatedContextFixturesByFixtureId(
        fixtureId,
        options
      )
  );
}


export function getContextFixturesTeamByTeamNameResult(
  teamName: string,
  options: FixtureIqApiGetOptions = {}
): Promise<ApiRequestResult> {
  return mapValidatedApiRequest(
    () =>
      validatedApi.getValidatedContextFixturesTeamByTeamName(
        teamName,
        options
      )
  );
}


export function getContextFormResult(
  options: FixtureIqApiGetOptions = {}
): Promise<ApiRequestResult> {
  return mapValidatedApiRequest(
    () =>
      validatedApi.getValidatedContextForm(
        options
      )
  );
}


export function getContextFormByTeamNameResult(
  teamName: string,
  options: FixtureIqApiGetOptions = {}
): Promise<ApiRequestResult> {
  return mapValidatedApiRequest(
    () =>
      validatedApi.getValidatedContextFormByTeamName(
        teamName,
        options
      )
  );
}


export function getContextStandingsResult(
  options: FixtureIqApiGetOptions = {}
): Promise<ApiRequestResult> {
  return mapValidatedApiRequest(
    () =>
      validatedApi.getValidatedContextStandings(
        options
      )
  );
}


export function getContextStandingsByTeamNameResult(
  teamName: string,
  options: FixtureIqApiGetOptions = {}
): Promise<ApiRequestResult> {
  return mapValidatedApiRequest(
    () =>
      validatedApi.getValidatedContextStandingsByTeamName(
        teamName,
        options
      )
  );
}


export function getContextStatusResult(
  options: FixtureIqApiGetOptions = {}
): Promise<ApiRequestResult> {
  return mapValidatedApiRequest(
    () =>
      validatedApi.getValidatedContextStatus(
        options
      )
  );
}


export function getContextTeamsResult(
  options: FixtureIqApiGetOptions = {}
): Promise<ApiRequestResult> {
  return mapValidatedApiRequest(
    () =>
      validatedApi.getValidatedContextTeams(
        options
      )
  );
}


export function getContextTeamsByTeamNameResult(
  teamName: string,
  options: FixtureIqApiGetOptions = {}
): Promise<ApiRequestResult> {
  return mapValidatedApiRequest(
    () =>
      validatedApi.getValidatedContextTeamsByTeamName(
        teamName,
        options
      )
  );
}

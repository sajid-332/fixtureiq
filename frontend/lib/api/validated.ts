import "server-only";

import type {
  FixtureIqApiGetOptions,
  FixtureIqApiJsonResponse,
} from "./client";

import * as intelligenceApi
  from "./intelligence";

import * as productionApi
  from "./production";

import * as contextApi
  from "./context";

import {
  type JsonValue,
  validateContextApiPayload,
  validateIntelligenceApiPayload,
  validateProductionApiPayload,
} from "./validation";


export type ValidatedApiResponse =
  FixtureIqApiJsonResponse<JsonValue>;


function withValidatedData(
  response:
    FixtureIqApiJsonResponse<unknown>,
  validator:
    (value: unknown) => JsonValue
): ValidatedApiResponse {
  return {
    status:
      response.status,

    ok:
      response.ok,

    data:
      validator(
        response.data
      ),
  };
}


export async function getValidatedIntelligenceStatus(
  options: FixtureIqApiGetOptions = {}
): Promise<ValidatedApiResponse> {
  const response =
    await intelligenceApi.getIntelligenceStatus(
      options
    );

  return withValidatedData(
    response,
    validateIntelligenceApiPayload
  );
}


export async function getValidatedIntelligenceMatches(
  options: FixtureIqApiGetOptions = {}
): Promise<ValidatedApiResponse> {
  const response =
    await intelligenceApi.getIntelligenceMatches(
      options
    );

  return withValidatedData(
    response,
    validateIntelligenceApiPayload
  );
}


export async function getValidatedIntelligenceMatch(
  fixtureId: string | number,
  options: FixtureIqApiGetOptions = {}
): Promise<ValidatedApiResponse> {
  const response =
    await intelligenceApi.getIntelligenceMatch(
      fixtureId,
      options
    );

  return withValidatedData(
    response,
    validateIntelligenceApiPayload
  );
}


export async function getValidatedTeamIntelligence(
  teamName: string,
  options: FixtureIqApiGetOptions = {}
): Promise<ValidatedApiResponse> {
  const response =
    await intelligenceApi.getTeamIntelligence(
      teamName,
      options
    );

  return withValidatedData(
    response,
    validateIntelligenceApiPayload
  );
}


export async function getValidatedUpcomingIntelligence(
  options: FixtureIqApiGetOptions = {}
): Promise<ValidatedApiResponse> {
  const response =
    await intelligenceApi.getUpcomingIntelligence(
      options
    );

  return withValidatedData(
    response,
    validateIntelligenceApiPayload
  );
}


export async function getValidatedProductionHealth(
  options: FixtureIqApiGetOptions = {}
): Promise<ValidatedApiResponse> {
  const response =
    await productionApi.getProductionHealth(
      options
    );

  return withValidatedData(
    response,
    validateProductionApiPayload
  );
}


export async function getValidatedProductionReadiness(
  options: FixtureIqApiGetOptions = {}
): Promise<ValidatedApiResponse> {
  const response =
    await productionApi.getProductionReadiness(
      options
    );

  return withValidatedData(
    response,
    validateProductionApiPayload
  );
}


export async function getValidatedProductionStatus(
  options: FixtureIqApiGetOptions = {}
): Promise<ValidatedApiResponse> {
  const response =
    await productionApi.getProductionStatus(
      options
    );

  return withValidatedData(
    response,
    validateProductionApiPayload
  );
}


export async function getValidatedContextFixtures(
  options: FixtureIqApiGetOptions = {}
): Promise<ValidatedApiResponse> {
  const response =
    await contextApi.getContextFixtures(
      options
    );

  return withValidatedData(
    response,
    validateContextApiPayload
  );
}


export async function getValidatedContextFixturesByFixtureId(
  fixtureId: string | number,
  options: FixtureIqApiGetOptions = {}
): Promise<ValidatedApiResponse> {
  const response =
    await contextApi.getContextFixturesByFixtureId(
      fixtureId,
      options
    );

  return withValidatedData(
    response,
    validateContextApiPayload
  );
}


export async function getValidatedContextFixturesTeamByTeamName(
  teamName: string,
  options: FixtureIqApiGetOptions = {}
): Promise<ValidatedApiResponse> {
  const response =
    await contextApi.getContextFixturesTeamByTeamName(
      teamName,
      options
    );

  return withValidatedData(
    response,
    validateContextApiPayload
  );
}


export async function getValidatedContextForm(
  options: FixtureIqApiGetOptions = {}
): Promise<ValidatedApiResponse> {
  const response =
    await contextApi.getContextForm(
      options
    );

  return withValidatedData(
    response,
    validateContextApiPayload
  );
}


export async function getValidatedContextFormByTeamName(
  teamName: string,
  options: FixtureIqApiGetOptions = {}
): Promise<ValidatedApiResponse> {
  const response =
    await contextApi.getContextFormByTeamName(
      teamName,
      options
    );

  return withValidatedData(
    response,
    validateContextApiPayload
  );
}


export async function getValidatedContextStandings(
  options: FixtureIqApiGetOptions = {}
): Promise<ValidatedApiResponse> {
  const response =
    await contextApi.getContextStandings(
      options
    );

  return withValidatedData(
    response,
    validateContextApiPayload
  );
}


export async function getValidatedContextStandingsByTeamName(
  teamName: string,
  options: FixtureIqApiGetOptions = {}
): Promise<ValidatedApiResponse> {
  const response =
    await contextApi.getContextStandingsByTeamName(
      teamName,
      options
    );

  return withValidatedData(
    response,
    validateContextApiPayload
  );
}


export async function getValidatedContextStatus(
  options: FixtureIqApiGetOptions = {}
): Promise<ValidatedApiResponse> {
  const response =
    await contextApi.getContextStatus(
      options
    );

  return withValidatedData(
    response,
    validateContextApiPayload
  );
}


export async function getValidatedContextTeams(
  options: FixtureIqApiGetOptions = {}
): Promise<ValidatedApiResponse> {
  const response =
    await contextApi.getContextTeams(
      options
    );

  return withValidatedData(
    response,
    validateContextApiPayload
  );
}


export async function getValidatedContextTeamsByTeamName(
  teamName: string,
  options: FixtureIqApiGetOptions = {}
): Promise<ValidatedApiResponse> {
  const response =
    await contextApi.getContextTeamsByTeamName(
      teamName,
      options
    );

  return withValidatedData(
    response,
    validateContextApiPayload
  );
}

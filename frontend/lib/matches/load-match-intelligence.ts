import "server-only";

import {
  getIntelligenceMatchResult,
} from "../api/mapped";


export function loadMatchIntelligence(
  fixtureId: string,
) {
  return getIntelligenceMatchResult(
    fixtureId,
  );
}

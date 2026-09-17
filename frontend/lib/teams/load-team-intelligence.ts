import "server-only";

import {
  getTeamIntelligenceResult,
} from "../api/mapped";


export function loadTeamIntelligence(
  teamName: string,
) {
  return getTeamIntelligenceResult(
    teamName,
  );
}

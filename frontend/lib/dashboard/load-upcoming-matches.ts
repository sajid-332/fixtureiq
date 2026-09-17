import "server-only";

import {
  getUpcomingIntelligenceResult,
} from "../api/mapped";


export async function loadUpcomingMatches() {
  return getUpcomingIntelligenceResult();
}

import "server-only";

import {
  getContextFormByTeamNameResult,
  getContextStandingsByTeamNameResult,
} from "../api/mapped";


export function loadTeamContext(
  teamName: string,
) {

  return Promise.all(
    [
      getContextStandingsByTeamNameResult(
        teamName,
      ),

      getContextFormByTeamNameResult(
        teamName,
      ),
    ] as const,
  );
}

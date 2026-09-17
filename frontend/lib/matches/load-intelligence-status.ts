import "server-only";

import {
  getIntelligenceStatusResult,
} from "../api/mapped";


export function loadIntelligenceStatus() {
  return getIntelligenceStatusResult();
}

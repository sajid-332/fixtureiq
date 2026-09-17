from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FRONTEND = ROOT / "frontend"

DOCS = ROOT / "docs" / "stage10"

FRONTEND_DATA = (
    ROOT
    / "data"
    / "processed"
    / "frontend"
)


PREVIOUS_FILE = (
    FRONTEND_DATA
    / "stage10_5_1_10_5_2_verification.json"
)

HEADER_CONTRACT_FILE = (
    DOCS
    / "frontend_match_fixture_header_contract.json"
)

DASHBOARD_CONTRACT_FILE = (
    DOCS
    / "frontend_upcoming_dashboard_contract.json"
)


OVERVIEW_CONTRACT_FILE = (
    DOCS
    / "frontend_match_prediction_overview_contract.json"
)

PROBABILITY_CONTRACT_FILE = (
    DOCS
    / "frontend_match_probability_visualization_contract.json"
)

CONFIDENCE_CONTRACT_FILE = (
    DOCS
    / "frontend_match_confidence_contract.json"
)

UNCERTAINTY_CONTRACT_FILE = (
    DOCS
    / "frontend_match_uncertainty_contract.json"
)


ROUTE_PAGE_FILE = (
    FRONTEND
    / "app"
    / "matches"
    / "[fixtureId]"
    / "page.tsx"
)

ROOT_PAGE_FILE = (
    FRONTEND
    / "app"
    / "page.tsx"
)

MATCH_CARD_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-card.tsx"
)

HEADER_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-fixture-header.tsx"
)

HEADER_RECORD_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "match-header-record.ts"
)

MATCH_LOADER_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "load-match-intelligence.ts"
)

PREDICTION_RECORD_FILE = (
    FRONTEND
    / "lib"
    / "matches"
    / "match-prediction-record.ts"
)


OVERVIEW_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-prediction-overview.tsx"
)

PROBABILITY_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-probability-visualization.tsx"
)

CONFIDENCE_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-confidence.tsx"
)

UNCERTAINTY_COMPONENT_FILE = (
    FRONTEND
    / "components"
    / "matches"
    / "match-uncertainty.tsx"
)


DOMAIN_TYPES_FILE = (
    FRONTEND
    / "lib"
    / "domain"
    / "types.ts"
)

MAPPED_API_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "mapped.ts"
)

RESULT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "result.ts"
)

KICKOFF_FORMATTER_FILE = (
    FRONTEND
    / "lib"
    / "formatters"
    / "kickoff.ts"
)

PROBABILITY_FORMATTER_FILE = (
    FRONTEND
    / "lib"
    / "formatters"
    / "probability.ts"
)


PREDICTION_RECORD_SOURCE = '''import "server-only";

import {
  FIVE_LEVEL_BANDS,
  OUTCOME_LABELS,
} from "../domain/types";

import type {
  ConfidenceBand,
  FixtureId,
  OutcomeLabel,
  UncertaintyBand,
} from "../domain/types";

import type {
  JsonValue,
} from "../api/validation";


type JsonObject =
  Readonly<{
    [key: string]:
      JsonValue;
  }>;


export type MatchPredictionRecord =
  Readonly<{
    fixture_id:
      FixtureId;

    stage7_prob_home_win:
      number;

    stage7_prob_draw:
      number;

    stage7_prob_away_win:
      number;

    stage7_predicted_label:
      OutcomeLabel;

    stage7_confidence:
      number;

    stage9_confidence_band:
      ConfidenceBand;

    stage9_uncertainty_band:
      UncertaintyBand;
  }>;


const outcomeLabels =
  new Set<string>(
    OUTCOME_LABELS,
  );


const fiveLevelBands =
  new Set<string>(
    FIVE_LEVEL_BANDS,
  );


function isObject(
  value: JsonValue,
): value is JsonObject {

  return (
    typeof value === "object"
    &&
    value !== null
    &&
    !Array.isArray(
      value,
    )
  );
}


function isFixtureId(
  value: JsonValue | undefined,
): value is FixtureId {

  return (
    (
      typeof value === "string"
      &&
      value.length > 0
    )
    ||
    (
      typeof value === "number"
      &&
      Number.isFinite(
        value,
      )
    )
  );
}


function transportNumber(
  value: JsonValue | undefined,
  field: string,
): number {

  if (
    typeof value === "number"
    &&
    Number.isFinite(
      value,
    )
  ) {
    return value;
  }


  if (
    typeof value === "string"
    &&
    value.trim().length > 0
  ) {

    const parsed =
      Number(
        value,
      );


    if (
      Number.isFinite(
        parsed,
      )
    ) {
      return parsed;
    }
  }


  throw new TypeError(
    `Invalid numeric match field: ${field}`,
  );
}


function probability(
  value: JsonValue | undefined,
  field: string,
): number {

  const parsed =
    transportNumber(
      value,
      field,
    );


  if (
    parsed < 0
    ||
    parsed > 1
  ) {
    throw new RangeError(
      `Invalid probability match field: ${field}`,
    );
  }


  return parsed;
}


function outcomeLabel(
  value: JsonValue | undefined,
): OutcomeLabel {

  if (
    typeof value !== "string"
    ||
    !outcomeLabels.has(
      value,
    )
  ) {
    throw new TypeError(
      "Invalid Stage 7 predicted label.",
    );
  }


  return value as OutcomeLabel;
}


function confidenceBand(
  value: JsonValue | undefined,
): ConfidenceBand {

  if (
    typeof value !== "string"
    ||
    !fiveLevelBands.has(
      value,
    )
  ) {
    throw new TypeError(
      "Invalid Stage 9 confidence band.",
    );
  }


  return value as ConfidenceBand;
}


function uncertaintyBand(
  value: JsonValue | undefined,
): UncertaintyBand {

  if (
    typeof value !== "string"
    ||
    !fiveLevelBands.has(
      value,
    )
  ) {
    throw new TypeError(
      "Invalid Stage 9 uncertainty band.",
    );
  }


  return value as UncertaintyBand;
}


function looksLikePredictionRecord(
  value: JsonObject,
): boolean {

  return (
    "fixture_id"
    in value
    &&
    "stage7_prob_home_win"
    in value
    &&
    "stage7_prob_draw"
    in value
    &&
    "stage7_prob_away_win"
    in value
    &&
    "stage7_predicted_label"
    in value
    &&
    "stage7_confidence"
    in value
    &&
    "stage9_confidence_band"
    in value
    &&
    "stage9_uncertainty_band"
    in value
  );
}


function parsePredictionRecord(
  value: JsonObject,
): MatchPredictionRecord {

  const fixtureId =
    value.fixture_id;


  if (
    !isFixtureId(
      fixtureId,
    )
  ) {
    throw new TypeError(
      "Invalid match prediction fixture_id.",
    );
  }


  return {
    fixture_id:
      fixtureId,

    stage7_prob_home_win:
      probability(
        value.stage7_prob_home_win,
        "stage7_prob_home_win",
      ),

    stage7_prob_draw:
      probability(
        value.stage7_prob_draw,
        "stage7_prob_draw",
      ),

    stage7_prob_away_win:
      probability(
        value.stage7_prob_away_win,
        "stage7_prob_away_win",
      ),

    stage7_predicted_label:
      outcomeLabel(
        value.stage7_predicted_label,
      ),

    stage7_confidence:
      probability(
        value.stage7_confidence,
        "stage7_confidence",
      ),

    stage9_confidence_band:
      confidenceBand(
        value.stage9_confidence_band,
      ),

    stage9_uncertainty_band:
      uncertaintyBand(
        value.stage9_uncertainty_band,
      ),
  };
}


function collectPredictionRecord(
  value: JsonValue,
  expectedFixtureId: string,
  output: MatchPredictionRecord[],
): void {

  if (
    Array.isArray(
      value,
    )
  ) {

    for (
      const item
      of
      value
    ) {

      collectPredictionRecord(
        item,
        expectedFixtureId,
        output,
      );
    }

    return;
  }


  if (
    !isObject(
      value,
    )
  ) {
    return;
  }


  if (
    looksLikePredictionRecord(
      value,
    )
  ) {

    const record =
      parsePredictionRecord(
        value,
      );


    if (
      String(
        record.fixture_id,
      )
      ===
      expectedFixtureId
    ) {

      output.push(
        record,
      );
    }

    return;
  }


  for (
    const child
    of
    Object.values(
      value,
    )
  ) {

    collectPredictionRecord(
      child,
      expectedFixtureId,
      output,
    );
  }
}


export function extractMatchPredictionRecord(
  data: JsonValue,
  expectedFixtureId: string,
): MatchPredictionRecord {

  const records:
    MatchPredictionRecord[] =
      [];


  collectPredictionRecord(
    data,
    expectedFixtureId,
    records,
  );


  if (
    records.length === 0
  ) {
    throw new Error(
      "Requested fixture prediction is absent from the READY match-intelligence response.",
    );
  }


  if (
    records.length !== 1
  ) {
    throw new Error(
      "Requested fixture prediction appears more than once.",
    );
  }


  return records[0];
}
'''


OVERVIEW_COMPONENT_SOURCE = '''import type {
  OutcomeLabel,
} from "../../lib/domain/types";


type MatchPredictionOverviewProps =
  Readonly<{
    predictedLabel:
      OutcomeLabel;
  }>;


export function MatchPredictionOverview({
  predictedLabel,
}: MatchPredictionOverviewProps) {

  return (
    <section
      aria-labelledby="prediction-overview-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-prediction-overview"
    >
      <p
        className="
          text-xs font-medium
          uppercase tracking-wide
          text-slate-500
        "
      >
        FixtureIQ prediction
      </p>

      <h2
        id="prediction-overview-heading"
        className="
          mt-2 text-lg font-bold
          text-slate-950
        "
      >
        Predicted outcome
      </h2>

      <p
        className="
          mt-3 text-xl font-semibold
          text-slate-900
        "
        data-stage7-field="stage7_predicted_label"
      >
        {predictedLabel}
      </p>
    </section>
  );
}
'''


PROBABILITY_COMPONENT_SOURCE = '''import {
  formatProbability,
} from "../../lib/formatters/probability";


type MatchProbabilityVisualizationProps =
  Readonly<{
    homeProbability:
      number;

    drawProbability:
      number;

    awayProbability:
      number;
  }>;


type ProbabilityRowProps =
  Readonly<{
    label:
      string;

    probability:
      number;

    sourceField:
      string;
  }>;


function ProbabilityRow({
  label,
  probability,
  sourceField,
}: ProbabilityRowProps) {

  return (
    <div>
      <div
        className="
          flex items-center
          justify-between gap-4
        "
      >
        <span
          className="
            text-sm font-medium
            text-slate-700
          "
        >
          {label}
        </span>

        <span
          className="
            text-sm font-semibold
            text-slate-950
          "
          data-stage7-field={
            sourceField
          }
        >
          {formatProbability(
            probability,
          )}
        </span>
      </div>

      <progress
        aria-label={`${label} probability`}
        className="
          mt-2 block h-2
          w-full
        "
        max={1}
        value={
          probability
        }
      />
    </div>
  );
}


export function MatchProbabilityVisualization({
  homeProbability,
  drawProbability,
  awayProbability,
}: MatchProbabilityVisualizationProps) {

  return (
    <section
      aria-labelledby="match-probabilities-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-probability-visualization"
    >
      <h2
        id="match-probabilities-heading"
        className="
          text-lg font-bold
          text-slate-950
        "
      >
        Outcome probabilities
      </h2>

      <div
        className="
          mt-5 space-y-5
        "
      >
        <ProbabilityRow
          label="Home win"
          probability={
            homeProbability
          }
          sourceField="stage7_prob_home_win"
        />

        <ProbabilityRow
          label="Draw"
          probability={
            drawProbability
          }
          sourceField="stage7_prob_draw"
        />

        <ProbabilityRow
          label="Away win"
          probability={
            awayProbability
          }
          sourceField="stage7_prob_away_win"
        />
      </div>
    </section>
  );
}
'''


CONFIDENCE_COMPONENT_SOURCE = '''import type {
  ConfidenceBand,
} from "../../lib/domain/types";

import {
  formatProbability,
} from "../../lib/formatters/probability";


type MatchConfidenceProps =
  Readonly<{
    confidence:
      number;

    confidenceBand:
      ConfidenceBand;
  }>;


export function MatchConfidence({
  confidence,
  confidenceBand,
}: MatchConfidenceProps) {

  return (
    <section
      aria-labelledby="match-confidence-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-confidence"
    >
      <h2
        id="match-confidence-heading"
        className="
          text-base font-bold
          text-slate-950
        "
      >
        Confidence
      </h2>

      <dl
        className="
          mt-4 space-y-3
        "
      >
        <div
          className="
            flex items-center
            justify-between gap-4
          "
        >
          <dt
            className="
              text-sm text-slate-600
            "
          >
            Stage 7 confidence
          </dt>

          <dd
            className="
              text-sm font-semibold
              text-slate-950
            "
            data-stage7-field="stage7_confidence"
          >
            {formatProbability(
              confidence,
            )}
          </dd>
        </div>

        <div
          className="
            flex items-center
            justify-between gap-4
          "
        >
          <dt
            className="
              text-sm text-slate-600
            "
          >
            Confidence band
          </dt>

          <dd
            className="
              text-sm font-semibold
              text-slate-950
            "
            data-stage9-field="stage9_confidence_band"
          >
            {confidenceBand}
          </dd>
        </div>
      </dl>
    </section>
  );
}
'''


UNCERTAINTY_COMPONENT_SOURCE = '''import type {
  UncertaintyBand,
} from "../../lib/domain/types";


type MatchUncertaintyProps =
  Readonly<{
    uncertaintyBand:
      UncertaintyBand;
  }>;


export function MatchUncertainty({
  uncertaintyBand,
}: MatchUncertaintyProps) {

  return (
    <section
      aria-labelledby="match-uncertainty-heading"
      className="
        rounded-xl
        border border-slate-200
        bg-white
        px-5 py-5
        shadow-sm
        sm:px-6
      "
      data-fixtureiq-component="match-uncertainty"
    >
      <h2
        id="match-uncertainty-heading"
        className="
          text-base font-bold
          text-slate-950
        "
      >
        Uncertainty
      </h2>

      <p
        className="
          mt-4 text-sm
          text-slate-600
        "
      >
        Stage 9 uncertainty band
      </p>

      <p
        className="
          mt-1 text-sm font-semibold
          text-slate-950
        "
        data-stage9-field="stage9_uncertainty_band"
      >
        {uncertaintyBand}
      </p>
    </section>
  );
}
'''


COMPONENT_IMPORTS = '''import {
  MatchPredictionOverview,
} from "../../../components/matches/match-prediction-overview";

import {
  MatchProbabilityVisualization,
} from "../../../components/matches/match-probability-visualization";

import {
  MatchConfidence,
} from "../../../components/matches/match-confidence";

import {
  MatchUncertainty,
} from "../../../components/matches/match-uncertainty";

'''


RECORD_IMPORT = '''import {
  extractMatchPredictionRecord,
} from "../../../lib/matches/match-prediction-record";

'''


PREDICTION_READ = '''  const prediction =
    extractMatchPredictionRecord(
      result.data,
      fixtureId,
    );


'''


DETAIL_SECTIONS = '''      <div
        className="
          mt-6 space-y-6
        "
      >
        <MatchPredictionOverview
          predictedLabel={
            prediction.stage7_predicted_label
          }
        />

        <MatchProbabilityVisualization
          homeProbability={
            prediction.stage7_prob_home_win
          }
          drawProbability={
            prediction.stage7_prob_draw
          }
          awayProbability={
            prediction.stage7_prob_away_win
          }
        />

        <div
          className="
            grid gap-6
            md:grid-cols-2
          "
        >
          <MatchConfidence
            confidence={
              prediction.stage7_confidence
            }
            confidenceBand={
              prediction.stage9_confidence_band
            }
          />

          <MatchUncertainty
            uncertaintyBand={
              prediction.stage9_uncertainty_band
            }
          />
        </div>
      </div>
'''


def load_json(
    path: Path,
) -> dict:

    if not path.exists():
        raise RuntimeError(
            f"Missing artifact: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        payload = json.load(
            file
        )

    if not isinstance(
        payload,
        dict,
    ):
        raise RuntimeError(
            f"Expected JSON object: {path}"
        )

    return payload


def optional_json(
    path: Path,
) -> dict | None:

    if not path.exists():
        return None

    return load_json(
        path
    )


def sha256_file(
    path: Path,
) -> str:

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as file:

        for chunk in iter(
            lambda:
                file.read(
                    1024 * 1024
                ),
            b"",
        ):
            digest.update(
                chunk
            )

    return digest.hexdigest()


def relative(
    path: Path,
) -> str:

    return (
        str(
            path.resolve()
            .relative_to(
                ROOT.resolve()
            )
        )
        .replace(
            "\\",
            "/",
        )
    )


def identity(
    path: Path,
) -> dict:

    return {
        "sha256":
            sha256_file(
                path
            )
    }


def save_text_atomic(
    path: Path,
    text: str,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        text,
        encoding="utf-8",
    )

    temporary.replace(
        path
    )


def save_json_atomic(
    path: Path,
    payload: dict,
) -> None:

    save_text_atomic(
        path,
        json.dumps(
            payload,
            indent=2,
        )
        +
        "\n",
    )


def replace_once(
    source: str,
    old: str,
    new: str,
    label: str,
) -> str:

    count = source.count(
        old
    )

    if count != 1:

        raise RuntimeError(
            (
                f"{label}: expected exactly "
                f"one anchor, found {count}."
            )
        )

    return source.replace(
        old,
        new,
        1,
    )


def common_protected_state() -> dict:

    return {
        "header_component_sha256":
            sha256_file(
                HEADER_COMPONENT_FILE
            ),

        "header_record_sha256":
            sha256_file(
                HEADER_RECORD_FILE
            ),

        "match_loader_sha256":
            sha256_file(
                MATCH_LOADER_FILE
            ),

        "domain_types_sha256":
            sha256_file(
                DOMAIN_TYPES_FILE
            ),

        "mapped_api_sha256":
            sha256_file(
                MAPPED_API_FILE
            ),

        "result_sha256":
            sha256_file(
                RESULT_FILE
            ),

        "kickoff_formatter_sha256":
            sha256_file(
                KICKOFF_FORMATTER_FILE
            ),

        "probability_formatter_sha256":
            sha256_file(
                PROBABILITY_FORMATTER_FILE
            ),

        "dashboard_page_sha256":
            sha256_file(
                ROOT_PAGE_FILE
            ),

        "dashboard_match_card_sha256":
            sha256_file(
                MATCH_CARD_FILE
            ),
    }


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.5.3 - 10.5.6"
    )

    print(
        "PREDICTION OVERVIEW + PROBABILITIES + CONFIDENCE + UNCERTAINTY"
    )

    print("=" * 72)


    previous = load_json(
        PREVIOUS_FILE
    )

    header_contract = load_json(
        HEADER_CONTRACT_FILE
    )

    dashboard_contract = load_json(
        DASHBOARD_CONTRACT_FILE
    )


    if (
        previous.get(
            "status"
        )
        !=
        "PASS"
    ):
        raise RuntimeError(
            "10.5.1/10.5.2 verification is not PASS."
        )


    if (
        previous.get(
            "stage_10_5_1_complete"
        )
        is not True
        or
        previous.get(
            "stage_10_5_2_complete"
        )
        is not True
    ):
        raise RuntimeError(
            "10.5.1/10.5.2 are not complete."
        )


    if (
        previous.get(
            "stage10_ready_for_10_5_3"
        )
        is not True
    ):
        raise RuntimeError(
            "10.5.2 did not authorize 10.5.3."
        )


    required = [
        ROUTE_PAGE_FILE,
        ROOT_PAGE_FILE,
        MATCH_CARD_FILE,
        HEADER_COMPONENT_FILE,
        HEADER_RECORD_FILE,
        MATCH_LOADER_FILE,
        DOMAIN_TYPES_FILE,
        MAPPED_API_FILE,
        RESULT_FILE,
        KICKOFF_FORMATTER_FILE,
        PROBABILITY_FORMATTER_FILE,
    ]


    for path in required:

        if not path.exists():
            raise RuntimeError(
                f"Missing source: {path}"
            )


    expected_route_sha = (
        header_contract.get(
            "route_page_after_header_sha256"
        )
    )


    final_contract = optional_json(
        UNCERTAINTY_CONTRACT_FILE
    )


    if (
        final_contract
        and
        PREDICTION_RECORD_FILE.exists()
        and
        OVERVIEW_COMPONENT_FILE.exists()
        and
        PROBABILITY_COMPONENT_FILE.exists()
        and
        CONFIDENCE_COMPONENT_FILE.exists()
        and
        UNCERTAINTY_COMPONENT_FILE.exists()
        and
        sha256_file(
            ROUTE_PAGE_FILE
        )
        ==
        final_contract.get(
            "route_page_after_10_5_6_sha256"
        )
        and
        sha256_file(
            UNCERTAINTY_COMPONENT_FILE
        )
        ==
        final_contract.get(
            "component_sha256"
        )
    ):

        print()

        print(
            "10.5.3 - 10.5.6 already built."
        )

        print("=" * 72)

        print(
            "STAGE 10.5.3 PREDICTION OVERVIEW: BUILT"
        )

        print(
            "STAGE 10.5.4 3-WAY VISUALIZATION: BUILT"
        )

        print(
            "STAGE 10.5.5 CONFIDENCE: BUILT"
        )

        print(
            "STAGE 10.5.6 UNCERTAINTY: BUILT"
        )

        print(
            "VERIFICATION STILL REQUIRED"
        )

        print("=" * 72)

        return


    if (
        sha256_file(
            ROUTE_PAGE_FILE
        )
        !=
        expected_route_sha
    ):
        raise RuntimeError(
            (
                "Match detail route no longer matches "
                "verified 10.5.2 output."
            )
        )


    if (
        sha256_file(
            ROOT_PAGE_FILE
        )
        !=
        dashboard_contract.get(
            "page_after_dashboard_sha256"
        )
    ):
        raise RuntimeError(
            "Dashboard page changed after Stage 10.4."
        )


    if (
        sha256_file(
            MATCH_CARD_FILE
        )
        !=
        dashboard_contract.get(
            "match_card_sha256"
        )
    ):
        raise RuntimeError(
            "Dashboard MatchCard changed after Stage 10.4."
        )


    route_before_sha = (
        sha256_file(
            ROUTE_PAGE_FILE
        )
    )


    # ========================================================
    # Create 10.5.3 - 10.5.6 sources
    # ========================================================

    save_text_atomic(
        PREDICTION_RECORD_FILE,
        PREDICTION_RECORD_SOURCE,
    )

    save_text_atomic(
        OVERVIEW_COMPONENT_FILE,
        OVERVIEW_COMPONENT_SOURCE,
    )

    save_text_atomic(
        PROBABILITY_COMPONENT_FILE,
        PROBABILITY_COMPONENT_SOURCE,
    )

    save_text_atomic(
        CONFIDENCE_COMPONENT_FILE,
        CONFIDENCE_COMPONENT_SOURCE,
    )

    save_text_atomic(
        UNCERTAINTY_COMPONENT_FILE,
        UNCERTAINTY_COMPONENT_SOURCE,
    )


    # ========================================================
    # Evolve verified 10.5.2 route
    # ========================================================

    route_source = (
        ROUTE_PAGE_FILE.read_text(
            encoding="utf-8"
        )
    )


    header_import = '''import {
  MatchFixtureHeader,
} from "../../../components/matches/match-fixture-header";

'''


    route_source = replace_once(
        route_source,
        header_import,
        (
            header_import
            +
            COMPONENT_IMPORTS
        ),
        "detail component imports",
    )


    header_record_import = '''import {
  extractMatchFixtureHeader,
} from "../../../lib/matches/match-header-record";

'''


    route_source = replace_once(
        route_source,
        header_record_import,
        (
            header_record_import
            +
            RECORD_IMPORT
        ),
        "prediction record import",
    )


    return_anchor = '''  return (
    <article
'''


    route_source = replace_once(
        route_source,
        return_anchor,
        (
            PREDICTION_READ
            +
            return_anchor
        ),
        "prediction extraction",
    )


    article_close = '''    </article>
'''


    route_source = replace_once(
        route_source,
        article_close,
        (
            DETAIL_SECTIONS
            +
            article_close
        ),
        "prediction detail sections",
    )


    save_text_atomic(
        ROUTE_PAGE_FILE,
        route_source,
    )


    route_after_sha = (
        sha256_file(
            ROUTE_PAGE_FILE
        )
    )


    protected = (
        common_protected_state()
    )


    common_dependencies = {
        relative(
            PREVIOUS_FILE
        ):
            identity(
                PREVIOUS_FILE
            ),

        relative(
            HEADER_CONTRACT_FILE
        ):
            identity(
                HEADER_CONTRACT_FILE
            ),

        relative(
            DOMAIN_TYPES_FILE
        ):
            identity(
                DOMAIN_TYPES_FILE
            ),

        relative(
            PROBABILITY_FORMATTER_FILE
        ):
            identity(
                PROBABILITY_FORMATTER_FILE
            ),
    }


    # ========================================================
    # 10.5.3
    # ========================================================

    overview_contract = {
        "stage":
            "10.5.3",

        "version":
            "1.0.0",

        "name":
            "MATCH_PREDICTION_OVERVIEW",

        "status":
            "LOCKED",

        "component_source":
            relative(
                OVERVIEW_COMPONENT_FILE
            ),

        "record_source":
            relative(
                PREDICTION_RECORD_FILE
            ),

        "authority":
            "STAGE_7_PREDICTION",

        "source_field":
            "stage7_predicted_label",

        "presentation": {
            "direct_source_label":
                True,

            "frontend_argmax":
                False,

            "frontend_prediction_derivation":
                False,

            "probability_visualization_owned_by":
                "10.5.4",
        },

        "component_sha256":
            sha256_file(
                OVERVIEW_COMPONENT_FILE
            ),

        "record_source_sha256":
            sha256_file(
                PREDICTION_RECORD_FILE
            ),

        "route_page_before_10_5_3_sha256":
            route_before_sha,

        "route_page_after_10_5_3_to_10_5_6_sha256":
            route_after_sha,

        "protected_state":
            protected,

        "dependency_identity":
            common_dependencies,

        "promotion": {
            "stage10_5_3_complete":
                False,

            "stage10_5_complete":
                False,

            "stage10_complete":
                False,
        },

        "generated_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }


    save_json_atomic(
        OVERVIEW_CONTRACT_FILE,
        overview_contract,
    )


    # ========================================================
    # 10.5.4
    # ========================================================

    probability_contract = {
        "stage":
            "10.5.4",

        "version":
            "1.0.0",

        "name":
            "MATCH_THREE_WAY_PROBABILITY_VISUALIZATION",

        "status":
            "LOCKED",

        "component_source":
            relative(
                PROBABILITY_COMPONENT_FILE
            ),

        "authority":
            "STAGE_7_PREDICTION",

        "source_fields": [
            "stage7_prob_home_win",
            "stage7_prob_draw",
            "stage7_prob_away_win",
        ],

        "visualization": {
            "native_progress_element":
                True,

            "progress_max":
                1,

            "raw_probability_as_value":
                True,

            "display_formatter":
                "formatProbability",

            "probability_normalization":
                False,

            "probability_recalibration":
                False,

            "probability_sorting":
                False,
        },

        "component_sha256":
            sha256_file(
                PROBABILITY_COMPONENT_FILE
            ),

        "route_page_after_10_5_4_sha256":
            route_after_sha,

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                OVERVIEW_CONTRACT_FILE
            ):
                identity(
                    OVERVIEW_CONTRACT_FILE
                ),

            relative(
                PROBABILITY_FORMATTER_FILE
            ):
                identity(
                    PROBABILITY_FORMATTER_FILE
                ),
        },

        "promotion": {
            "stage10_5_4_complete":
                False,

            "stage10_5_complete":
                False,

            "stage10_complete":
                False,
        },

        "generated_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }


    save_json_atomic(
        PROBABILITY_CONTRACT_FILE,
        probability_contract,
    )


    # ========================================================
    # 10.5.5
    # ========================================================

    confidence_contract = {
        "stage":
            "10.5.5",

        "version":
            "1.0.0",

        "name":
            "MATCH_CONFIDENCE",

        "status":
            "LOCKED",

        "component_source":
            relative(
                CONFIDENCE_COMPONENT_FILE
            ),

        "authorities": {
            "stage7_confidence":
                "STAGE_7_PREDICTION",

            "stage9_confidence_band":
                "STAGE_9_INTELLIGENCE",
        },

        "source_fields": [
            "stage7_confidence",
            "stage9_confidence_band",
        ],

        "presentation": {
            "stage7_confidence_formatted_only":
                True,

            "stage9_band_direct":
                True,

            "frontend_thresholds":
                False,

            "frontend_band_derivation":
                False,
        },

        "component_sha256":
            sha256_file(
                CONFIDENCE_COMPONENT_FILE
            ),

        "route_page_after_10_5_5_sha256":
            route_after_sha,

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                PROBABILITY_CONTRACT_FILE
            ):
                identity(
                    PROBABILITY_CONTRACT_FILE
                ),

            relative(
                PROBABILITY_FORMATTER_FILE
            ):
                identity(
                    PROBABILITY_FORMATTER_FILE
                ),
        },

        "promotion": {
            "stage10_5_5_complete":
                False,

            "stage10_5_complete":
                False,

            "stage10_complete":
                False,
        },

        "generated_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }


    save_json_atomic(
        CONFIDENCE_CONTRACT_FILE,
        confidence_contract,
    )


    # ========================================================
    # 10.5.6
    # ========================================================

    uncertainty_contract = {
        "stage":
            "10.5.6",

        "version":
            "1.0.0",

        "name":
            "MATCH_UNCERTAINTY",

        "status":
            "LOCKED",

        "component_source":
            relative(
                UNCERTAINTY_COMPONENT_FILE
            ),

        "authority":
            "STAGE_9_INTELLIGENCE",

        "source_field":
            "stage9_uncertainty_band",

        "presentation": {
            "direct_source_band":
                True,

            "entropy_calculation":
                False,

            "normalized_entropy_calculation":
                False,

            "frontend_thresholds":
                False,

            "frontend_band_derivation":
                False,
        },

        "component_sha256":
            sha256_file(
                UNCERTAINTY_COMPONENT_FILE
            ),

        "route_page_after_10_5_6_sha256":
            route_after_sha,

        "record_source_sha256":
            sha256_file(
                PREDICTION_RECORD_FILE
            ),

        "protected_state":
            protected,

        "dependency_identity": {
            relative(
                CONFIDENCE_CONTRACT_FILE
            ):
                identity(
                    CONFIDENCE_CONTRACT_FILE
                ),

            relative(
                PREDICTION_RECORD_FILE
            ):
                identity(
                    PREDICTION_RECORD_FILE
                ),
        },

        "promotion": {
            "stage10_5_6_complete":
                False,

            "stage10_5_complete":
                False,

            "stage10_complete":
                False,
        },

        "generated_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }


    save_json_atomic(
        UNCERTAINTY_CONTRACT_FILE,
        uncertainty_contract,
    )


    print()

    print(
        "Prediction record:"
    )

    print(
        f"  {relative(PREDICTION_RECORD_FILE)}"
    )

    print()

    print(
        "Components:"
    )

    for path in [
        OVERVIEW_COMPONENT_FILE,
        PROBABILITY_COMPONENT_FILE,
        CONFIDENCE_COMPONENT_FILE,
        UNCERTAINTY_COMPONENT_FILE,
    ]:

        print(
            f"  {relative(path)}"
        )


    print()

    print(
        "Detail route:"
    )

    print(
        f"  {relative(ROUTE_PAGE_FILE)}"
    )


    print()

    print("=" * 72)

    print(
        "STAGE 10.5.3 PREDICTION OVERVIEW: BUILT"
    )

    print(
        "STAGE 10.5.4 3-WAY VISUALIZATION: BUILT"
    )

    print(
        "STAGE 10.5.5 CONFIDENCE: BUILT"
    )

    print(
        "STAGE 10.5.6 UNCERTAINTY: BUILT"
    )

    print(
        "VERIFICATION STILL REQUIRED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
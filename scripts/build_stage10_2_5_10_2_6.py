from __future__ import annotations

import hashlib
import json
import re
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


ENDPOINT_CONTRACT_FILE = (
    DOCS
    / "frontend_api_endpoint_contract.json"
)

HTTP_CLIENT_CONTRACT_FILE = (
    DOCS
    / "frontend_http_client_contract.json"
)

INTELLIGENCE_CONTRACT_FILE = (
    DOCS
    / "frontend_intelligence_api_client_contract.json"
)

PRODUCTION_CONTRACT_FILE = (
    DOCS
    / "frontend_production_api_client_contract.json"
)

PREVIOUS_VERIFICATION_FILE = (
    FRONTEND_DATA
    / "stage10_2_3_10_2_4_verification.json"
)


SHARED_CLIENT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "client.ts"
)

INTELLIGENCE_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "intelligence.ts"
)

PRODUCTION_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "production.ts"
)

CONTEXT_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "context.ts"
)

VALIDATION_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "validation.ts"
)

VALIDATED_API_FILE = (
    FRONTEND
    / "lib"
    / "api"
    / "validated.ts"
)

RUNTIME_TEST_FILE = (
    FRONTEND
    / "scripts"
    / "verify-stage10-api-validation.mjs"
)

PACKAGE_JSON_FILE = (
    FRONTEND
    / "package.json"
)

PACKAGE_LOCK_FILE = (
    FRONTEND
    / "package-lock.json"
)


CONTEXT_CONTRACT_FILE = (
    DOCS
    / "frontend_context_api_client_contract.json"
)

VALIDATION_CONTRACT_FILE = (
    DOCS
    / "frontend_response_validation_contract.json"
)


PARAM_PATTERN = re.compile(
    r"<(?:[^:>]+:)?([A-Za-z_][A-Za-z0-9_]*)>"
)


def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise RuntimeError(
            f"Missing required artifact: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        payload = json.load(file)

    if not isinstance(
        payload,
        dict,
    ):

        raise RuntimeError(
            f"Expected JSON object: {path}"
        )

    return payload


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

            digest.update(chunk)

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
        .replace("\\", "/")
    )


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

    temporary.replace(path)


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


def identity(
    path: Path,
) -> dict:

    return {
        "sha256":
            sha256_file(path)
    }


def pascal_case(
    value: str,
) -> str:

    words = re.findall(
        r"[A-Za-z0-9]+",
        value,
    )

    return "".join(
        word[:1].upper()
        +
        word[1:]

        for word in words
    )


def camel_case(
    value: str,
) -> str:

    converted = pascal_case(value)

    if not converted:

        raise RuntimeError(
            f"Cannot convert name: {value}"
        )

    return (
        converted[:1].lower()
        +
        converted[1:]
    )


def parameter_names(
    route: str,
) -> list[str]:

    return PARAM_PATTERN.findall(
        route
    )


def route_key(
    route: str,
    prefix: str,
) -> str:

    suffix = route[
        len(prefix):
    ].strip("/")

    if not suffix:

        return "ROOT"

    parts = []

    for segment in suffix.split("/"):

        match = PARAM_PATTERN.fullmatch(
            segment
        )

        if match:

            parts.extend(
                [
                    "BY",
                    match.group(1).upper(),
                ]
            )

        else:

            parts.append(
                re.sub(
                    r"[^A-Za-z0-9]+",
                    "_",
                    segment,
                ).upper()
            )

    return "_".join(
        item
        for item in parts
        if item
    )


def function_name(
    route: str,
    prefix: str,
    family: str,
) -> str:

    suffix = route[
        len(prefix):
    ].strip("/")

    if not suffix:

        return f"get{family}"

    output = [
        f"get{family}"
    ]

    for segment in suffix.split("/"):

        match = PARAM_PATTERN.fullmatch(
            segment
        )

        if match:

            output.append("By")

            output.append(
                pascal_case(
                    match.group(1)
                )
            )

        else:

            output.append(
                pascal_case(segment)
            )

    return "".join(output)


def route_expression(
    route: str,
) -> str:

    parameters = parameter_names(
        route
    )

    if not parameters:

        return json.dumps(route)

    pieces = []
    cursor = 0

    for match in PARAM_PATTERN.finditer(
        route
    ):

        pieces.append(
            route[
                cursor:
                match.start()
            ]
        )

        variable = camel_case(
            match.group(1)
        )

        pieces.append(
            "${encodeURIComponent("
            f"String({variable})"
            ")}"
        )

        cursor = match.end()

    pieces.append(
        route[cursor:]
    )

    return (
        "`"
        +
        "".join(pieces)
        +
        "`"
    )


def build_context_client(
    routes: list[str],
) -> tuple[str, list[dict]]:

    entries = []

    seen_keys = set()
    seen_functions = set()

    prefix = "/api/v1/context"

    for route in routes:

        key = route_key(
            route,
            prefix,
        )

        name = function_name(
            route,
            prefix,
            "Context",
        )

        if key in seen_keys:

            raise RuntimeError(
                f"Duplicate context route key: {key}"
            )

        if name in seen_functions:

            raise RuntimeError(
                f"Duplicate context function: {name}"
            )

        seen_keys.add(key)
        seen_functions.add(name)

        entries.append(
            {
                "key":
                    key,

                "function":
                    name,

                "route":
                    route,

                "parameters":
                    parameter_names(
                        route
                    ),
            }
        )

    lines = [
        'import "server-only";',
        "",
        "import {",
        "  fixtureIqApiGet,",
        "  type FixtureIqApiGetOptions,",
        "  type FixtureIqApiJsonResponse,",
        '} from "./client";',
        "",
        "",
        "export const CONTEXT_API_ROUTES = {",
    ]

    for entry in entries:

        lines.extend(
            [
                f"  {entry['key']}:",
                f"    {json.dumps(entry['route'])},",
                "",
            ]
        )

    lines.extend(
        [
            "} as const;",
            "",
            "",
            "export type ContextApiResponse =",
            "  FixtureIqApiJsonResponse<unknown>;",
            "",
        ]
    )

    for entry in entries:

        params = [
            camel_case(parameter)
            for parameter
            in entry[
                "parameters"
            ]
        ]

        lines.append(
            (
                f"export function "
                f"{entry['function']}("
            )
        )

        for parameter in params:

            lines.append(
                (
                    f"  {parameter}: "
                    "string | number,"
                )
            )

        lines.append(
            (
                "  options: "
                "FixtureIqApiGetOptions = {}"
            )
        )

        lines.append(
            "): Promise<ContextApiResponse> {"
        )

        lines.append(
            "  return fixtureIqApiGet<unknown>("
        )

        lines.append(
            (
                "    "
                +
                route_expression(
                    entry["route"]
                )
                +
                ","
            )
        )

        lines.append(
            "    options"
        )

        lines.append(
            "  );"
        )

        lines.append(
            "}"
        )

        lines.append("")
        lines.append("")

    return (
        "\n".join(lines).rstrip()
        +
        "\n",
        entries,
    )


VALIDATION_SOURCE = r'''/*
 * FixtureIQ Stage 10.2.6
 *
 * Runtime validation for backend JSON responses.
 *
 * This module intentionally uses native TypeScript / JavaScript
 * runtime facilities instead of introducing a new dependency
 * that would mutate the already-locked package dependency chain.
 *
 * Stage 7 = prediction authority
 * Stage 8 = context authority
 * Stage 9 = intelligence authority
 * Stage 10 = presentation only
 */


export type JsonPrimitive =
  | string
  | number
  | boolean
  | null;


export type JsonValue =
  | JsonPrimitive
  | JsonValue[]
  | {
      readonly [key: string]:
        JsonValue;
    };


export type JsonObject =
  Readonly<
    Record<
      string,
      JsonValue
    >
  >;


export const OUTCOME_LABELS =
  new Set(
    [
      "Home Win",
      "Draw",
      "Away Win",
    ] as const
  );


export const FIVE_LEVEL_BANDS =
  new Set(
    [
      "VERY_LOW",
      "LOW",
      "MODERATE",
      "HIGH",
      "VERY_HIGH",
    ] as const
  );


export const CONTEXT_ALIGNMENTS =
  new Set(
    [
      "SUPPORTIVE",
      "MIXED",
      "CONTRADICTORY",
      "NEUTRAL",
    ] as const
  );


export class ApiValidationError
  extends TypeError {

  constructor(
    message: string
  ) {
    super(message);

    this.name =
      "ApiValidationError";
  }
}


function fail(
  path: string,
  message: string
): never {
  throw new ApiValidationError(
    `${path}: ${message}`
  );
}


function isObject(
  value: unknown
): value is Record<
  string,
  unknown
> {
  return (
    typeof value === "object"
    &&
    value !== null
    &&
    !Array.isArray(value)
  );
}


function assertFiniteNumber(
  value: unknown,
  path: string
): asserts value is number {
  if (
    typeof value !== "number"
    ||
    !Number.isFinite(value)
  ) {
    fail(
      path,
      "expected a finite number"
    );
  }
}


function assertProbability(
  value: unknown,
  path: string
): asserts value is number {
  assertFiniteNumber(
    value,
    path
  );

  if (
    value < 0
    ||
    value > 1
  ) {
    fail(
      path,
      "expected probability in [0, 1]"
    );
  }
}


function assertString(
  value: unknown,
  path: string
): asserts value is string {
  if (
    typeof value !== "string"
  ) {
    fail(
      path,
      "expected a string"
    );
  }
}


function assertFixtureId(
  value: unknown,
  path: string
): asserts value is string | number {
  if (
    typeof value === "string"
  ) {
    return;
  }

  if (
    typeof value === "number"
    &&
    Number.isFinite(value)
  ) {
    return;
  }

  fail(
    path,
    "expected fixture ID as string or finite number"
  );
}


function assertIntegerRange(
  value: unknown,
  minimum: number,
  maximum: number,
  path: string
): asserts value is number {
  assertFiniteNumber(
    value,
    path
  );

  if (
    !Number.isInteger(value)
    ||
    value < minimum
    ||
    value > maximum
  ) {
    fail(
      path,
      (
        "expected integer between "
        +
        `${minimum} and ${maximum}`
      )
    );
  }
}


function assertSetMember(
  value: unknown,
  allowed:
    ReadonlySet<string>,
  path: string
): asserts value is string {
  assertString(
    value,
    path
  );

  if (
    !allowed.has(value)
  ) {
    fail(
      path,
      `unexpected value: ${value}`
    );
  }
}


export function assertJsonValue(
  value: unknown,
  path = "$"
): asserts value is JsonValue {

  if (
    value === null
    ||
    typeof value === "string"
    ||
    typeof value === "boolean"
  ) {
    return;
  }

  if (
    typeof value === "number"
  ) {
    if (
      !Number.isFinite(value)
    ) {
      fail(
        path,
        "JSON number must be finite"
      );
    }

    return;
  }

  if (
    Array.isArray(value)
  ) {
    value.forEach(
      (
        item,
        index
      ) => {
        assertJsonValue(
          item,
          `${path}[${index}]`
        );
      }
    );

    return;
  }

  if (
    isObject(value)
  ) {
    for (
      const [
        key,
        item,
      ]
      of
      Object.entries(value)
    ) {
      assertJsonValue(
        item,
        `${path}.${key}`
      );
    }

    return;
  }

  fail(
    path,
    "expected valid JSON value"
  );
}


function visitObjects(
  value: JsonValue,
  visitor: (
    value: JsonObject,
    path: string
  ) => void,
  path = "$"
): void {

  if (
    Array.isArray(value)
  ) {
    value.forEach(
      (
        item,
        index
      ) => {
        visitObjects(
          item,
          visitor,
          `${path}[${index}]`
        );
      }
    );

    return;
  }

  if (
    typeof value !== "object"
    ||
    value === null
  ) {
    return;
  }

  visitor(
    value,
    path
  );

  for (
    const [
      key,
      item,
    ]
    of
    Object.entries(value)
  ) {
    visitObjects(
      item,
      visitor,
      `${path}.${key}`
    );
  }
}


function validateStatusField(
  value: JsonObject,
  path: string
): void {
  if (
    "status"
    in
    value
  ) {
    assertString(
      value.status,
      `${path}.status`
    );
  }
}


const PRODUCTION_MARKERS =
  new Set(
    [
      "prob_home_win",
      "prob_draw",
      "prob_away_win",
      "predicted_label",
    ]
  );


function looksLikeProductionPrediction(
  value: JsonObject
): boolean {
  return Array.from(
    PRODUCTION_MARKERS
  ).some(
    (key) =>
      key
      in
      value
  );
}


function validateProductionPrediction(
  value: JsonObject,
  path: string
): void {

  assertFixtureId(
    value.fixture_id,
    `${path}.fixture_id`
  );

  assertString(
    value.home_team_name,
    `${path}.home_team_name`
  );

  assertString(
    value.away_team_name,
    `${path}.away_team_name`
  );

  assertProbability(
    value.prob_home_win,
    `${path}.prob_home_win`
  );

  assertProbability(
    value.prob_draw,
    `${path}.prob_draw`
  );

  assertProbability(
    value.prob_away_win,
    `${path}.prob_away_win`
  );

  assertSetMember(
    value.predicted_label,
    OUTCOME_LABELS,
    `${path}.predicted_label`
  );

  assertProbability(
    value.confidence,
    `${path}.confidence`
  );
}


const INTELLIGENCE_MARKERS =
  new Set(
    [
      "stage9_top_probability",
      "stage9_probability_margin",
      "stage9_context_alignment",
      "stage9_context_support_score",
    ]
  );


function looksLikeIntelligenceRecord(
  value: JsonObject
): boolean {
  return Array.from(
    INTELLIGENCE_MARKERS
  ).some(
    (key) =>
      key
      in
      value
  );
}


function validateIntelligenceRecord(
  value: JsonObject,
  path: string
): void {

  assertFixtureId(
    value.fixture_id,
    `${path}.fixture_id`
  );

  assertString(
    value.home_team_name,
    `${path}.home_team_name`
  );

  assertString(
    value.away_team_name,
    `${path}.away_team_name`
  );


  assertProbability(
    value.stage7_prob_home_win,
    `${path}.stage7_prob_home_win`
  );

  assertProbability(
    value.stage7_prob_draw,
    `${path}.stage7_prob_draw`
  );

  assertProbability(
    value.stage7_prob_away_win,
    `${path}.stage7_prob_away_win`
  );

  assertSetMember(
    value.stage7_predicted_label,
    OUTCOME_LABELS,
    `${path}.stage7_predicted_label`
  );

  assertProbability(
    value.stage7_confidence,
    `${path}.stage7_confidence`
  );


  assertProbability(
    value.stage9_top_probability,
    `${path}.stage9_top_probability`
  );

  assertProbability(
    value.stage9_probability_margin,
    `${path}.stage9_probability_margin`
  );

  assertSetMember(
    value.stage9_confidence_band,
    FIVE_LEVEL_BANDS,
    `${path}.stage9_confidence_band`
  );

  assertSetMember(
    value.stage9_uncertainty_band,
    FIVE_LEVEL_BANDS,
    `${path}.stage9_uncertainty_band`
  );

  assertIntegerRange(
    value.stage9_context_support_score,
    -5,
    5,
    `${path}.stage9_context_support_score`
  );

  assertSetMember(
    value.stage9_context_alignment,
    CONTEXT_ALIGNMENTS,
    `${path}.stage9_context_alignment`
  );

  assertString(
    value.stage9_explanation_headline,
    `${path}.stage9_explanation_headline`
  );

  assertString(
    value.stage9_explanation_summary,
    `${path}.stage9_explanation_summary`
  );
}


function validateContextIdentity(
  value: JsonObject,
  path: string
): void {

  if (
    "fixture_id"
    in
    value
  ) {
    assertFixtureId(
      value.fixture_id,
      `${path}.fixture_id`
    );

    if (
      "home_team_name"
      in
      value
      ||
      "away_team_name"
      in
      value
    ) {
      assertString(
        value.home_team_name,
        `${path}.home_team_name`
      );

      assertString(
        value.away_team_name,
        `${path}.away_team_name`
      );
    }
  }

  if (
    "team_name"
    in
    value
  ) {
    assertString(
      value.team_name,
      `${path}.team_name`
    );
  }
}


function validateBasePayload(
  input: unknown
): JsonValue {

  assertJsonValue(input);

  visitObjects(
    input,
    (
      value,
      path
    ) => {
      validateStatusField(
        value,
        path
      );
    }
  );

  return input;
}


export function validateProductionApiPayload(
  input: unknown
): JsonValue {

  const value =
    validateBasePayload(
      input
    );

  visitObjects(
    value,
    (
      candidate,
      path
    ) => {
      if (
        looksLikeProductionPrediction(
          candidate
        )
      ) {
        validateProductionPrediction(
          candidate,
          path
        );
      }
    }
  );

  return value;
}


export function validateIntelligenceApiPayload(
  input: unknown
): JsonValue {

  const value =
    validateBasePayload(
      input
    );

  visitObjects(
    value,
    (
      candidate,
      path
    ) => {
      if (
        looksLikeIntelligenceRecord(
          candidate
        )
      ) {
        validateIntelligenceRecord(
          candidate,
          path
        );
      }
    }
  );

  return value;
}


export function validateContextApiPayload(
  input: unknown
): JsonValue {

  const value =
    validateBasePayload(
      input
    );

  visitObjects(
    value,
    (
      candidate,
      path
    ) => {
      validateContextIdentity(
        candidate,
        path
      );
    }
  );

  return value;
}
'''


RUNTIME_TEST_SOURCE = r'''import fs from "node:fs";
import { Buffer } from "node:buffer";
import ts from "typescript";


const validationUrl =
  new URL(
    "../lib/api/validation.ts",
    import.meta.url
  );


const source =
  fs.readFileSync(
    validationUrl,
    "utf8"
  );


const transpiled =
  ts.transpileModule(
    source,
    {
      compilerOptions: {
        target:
          ts.ScriptTarget.ES2022,

        module:
          ts.ModuleKind.ES2022,

        strict:
          true,
      },
    }
  );


const dataUrl =
  "data:text/javascript;base64,"
  +
  Buffer
    .from(
      transpiled.outputText,
      "utf8"
    )
    .toString("base64");


const validation =
  await import(dataUrl);


const {
  validateProductionApiPayload,
  validateIntelligenceApiPayload,
  validateContextApiPayload,
} = validation;


function expectPass(
  label,
  callback
) {
  try {
    callback();

    console.log(
      `${label}: PASS`
    );
  } catch (error) {
    console.error(
      `${label}: FAIL`
    );

    console.error(error);

    process.exitCode = 1;
  }
}


function expectReject(
  label,
  callback
) {
  try {
    callback();

    console.error(
      `${label}: FAIL`
    );

    process.exitCode = 1;
  } catch {
    console.log(
      `${label}: PASS`
    );
  }
}


const validProduction = {
  status:
    "READY",

  predictions: [
    {
      fixture_id:
        "fixture-1",

      home_team_name:
        "Home",

      away_team_name:
        "Away",

      prob_home_win:
        0.5,

      prob_draw:
        0.25,

      prob_away_win:
        0.25,

      predicted_label:
        "Home Win",

      confidence:
        0.5,
    },
  ],
};


const invalidProduction = {
  predictions: [
    {
      fixture_id:
        "fixture-1",

      home_team_name:
        "Home",

      away_team_name:
        "Away",

      prob_home_win:
        "0.5",

      prob_draw:
        0.25,

      prob_away_win:
        0.25,

      predicted_label:
        "Home Win",

      confidence:
        0.5,
    },
  ],
};


const validIntelligence = {
  status:
    "READY",

  match: {
    fixture_id:
      "fixture-1",

    home_team_name:
      "Home",

    away_team_name:
      "Away",

    stage7_prob_home_win:
      0.5,

    stage7_prob_draw:
      0.25,

    stage7_prob_away_win:
      0.25,

    stage7_predicted_label:
      "Home Win",

    stage7_confidence:
      0.5,

    stage9_top_probability:
      0.5,

    stage9_probability_margin:
      0.25,

    stage9_confidence_band:
      "MODERATE",

    stage9_uncertainty_band:
      "HIGH",

    stage9_context_support_score:
      2,

    stage9_context_alignment:
      "SUPPORTIVE",

    stage9_explanation_headline:
      "FixtureIQ explanation",

    stage9_explanation_summary:
      "Deterministic interpretation.",
  },
};


const invalidIntelligence = {
  ...validIntelligence,

  match: {
    ...validIntelligence.match,

    stage9_context_support_score:
      6,
  },
};


const validContext = {
  status:
    "READY",

  fixtures: [
    {
      fixture_id:
        "fixture-1",

      home_team_name:
        "Home",

      away_team_name:
        "Away",
    },
  ],

  teams: [
    {
      team_name:
        "Home",
    },
  ],
};


const invalidContext = {
  teams: [
    {
      team_name:
        123,
    },
  ],
};


const notReadyPayload = {
  status:
    "NOT_READY",

  service:
    "match_intelligence",
};


expectPass(
  "Valid production payload accepted",
  () =>
    validateProductionApiPayload(
      validProduction
    )
);


expectReject(
  "Invalid production probability rejected",
  () =>
    validateProductionApiPayload(
      invalidProduction
    )
);


expectPass(
  "Valid intelligence payload accepted",
  () =>
    validateIntelligenceApiPayload(
      validIntelligence
    )
);


expectReject(
  "Invalid intelligence support score rejected",
  () =>
    validateIntelligenceApiPayload(
      invalidIntelligence
    )
);


expectPass(
  "Valid context payload accepted",
  () =>
    validateContextApiPayload(
      validContext
    )
);


expectReject(
  "Invalid context identity rejected",
  () =>
    validateContextApiPayload(
      invalidContext
    )
);


expectPass(
  "NOT_READY payload accepted",
  () =>
    validateIntelligenceApiPayload(
      notReadyPayload
    )
);


expectReject(
  "Undefined JSON value rejected",
  () =>
    validateContextApiPayload(
      {
        status:
          "READY",

        bad:
          undefined,
      }
    )
);


if (
  process.exitCode
  !==
  1
) {
  console.log(
    "STAGE 10.2.6 RUNTIME VALIDATION TESTS: PASS"
  );
}
'''


def validated_function_name(
    raw_name: str,
) -> str:

    if not raw_name.startswith(
        "get"
    ):

        raise RuntimeError(
            f"Unexpected API function: {raw_name}"
        )

    return (
        "getValidated"
        +
        raw_name[3:]
    )


def render_wrapper(
    family_namespace: str,
    raw_function: str,
    parameters: list[str],
    validator: str,
) -> str:

    wrapper = validated_function_name(
        raw_function
    )

    params = [
        camel_case(parameter)
        for parameter in parameters
    ]

    lines = [
        f"export async function {wrapper}(",
    ]

    for parameter in params:

        parameter_type = (
            "string"
            if parameter
            ==
            "teamName"
            else
            "string | number"
        )

        lines.append(
            (
                f"  {parameter}: "
                f"{parameter_type},"
            )
        )

    lines.append(
        (
            "  options: "
            "FixtureIqApiGetOptions = {}"
        )
    )

    lines.extend(
        [
            "): Promise<ValidatedApiResponse> {",
            "  const response =",
            f"    await {family_namespace}.{raw_function}(",
        ]
    )

    for parameter in params:

        lines.append(
            f"      {parameter},"
        )

    lines.append(
        "      options"
    )

    lines.extend(
        [
            "    );",
            "",
            "  return withValidatedData(",
            "    response,",
            f"    {validator}",
            "  );",
            "}",
            "",
            "",
        ]
    )

    return "\n".join(lines)


def build_validated_api_source(
    production_entries: list[dict],
    context_entries: list[dict],
) -> str:

    lines = [
        'import "server-only";',
        "",
        'import type {',
        "  FixtureIqApiGetOptions,",
        "  FixtureIqApiJsonResponse,",
        '} from "./client";',
        "",
        'import * as intelligenceApi',
        '  from "./intelligence";',
        "",
        'import * as productionApi',
        '  from "./production";',
        "",
        'import * as contextApi',
        '  from "./context";',
        "",
        'import {',
        "  type JsonValue,",
        "  validateContextApiPayload,",
        "  validateIntelligenceApiPayload,",
        "  validateProductionApiPayload,",
        '} from "./validation";',
        "",
        "",
        "export type ValidatedApiResponse =",
        "  FixtureIqApiJsonResponse<JsonValue>;",
        "",
        "",
        "function withValidatedData(",
        "  response:",
        "    FixtureIqApiJsonResponse<unknown>,",
        "  validator:",
        "    (value: unknown) => JsonValue",
        "): ValidatedApiResponse {",
        "  return {",
        "    status:",
        "      response.status,",
        "",
        "    ok:",
        "      response.ok,",
        "",
        "    data:",
        "      validator(",
        "        response.data",
        "      ),",
        "  };",
        "}",
        "",
        "",
    ]

    intelligence_entries = [
        (
            "getIntelligenceStatus",
            [],
        ),
        (
            "getIntelligenceMatches",
            [],
        ),
        (
            "getIntelligenceMatch",
            [
                "fixture_id"
            ],
        ),
        (
            "getTeamIntelligence",
            [
                "team_name"
            ],
        ),
        (
            "getUpcomingIntelligence",
            [],
        ),
    ]

    for raw_name, parameters in (
        intelligence_entries
    ):

        lines.append(
            render_wrapper(
                "intelligenceApi",
                raw_name,
                parameters,
                "validateIntelligenceApiPayload",
            )
        )

    for entry in production_entries:

        lines.append(
            render_wrapper(
                "productionApi",
                entry["function"],
                entry.get(
                    "parameters",
                    [],
                ),
                "validateProductionApiPayload",
            )
        )

    for entry in context_entries:

        lines.append(
            render_wrapper(
                "contextApi",
                entry["function"],
                entry.get(
                    "parameters",
                    [],
                ),
                "validateContextApiPayload",
            )
        )

    return (
        "\n".join(lines).rstrip()
        +
        "\n"
    )


def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 10.2.5 + 10.2.6"
    )

    print(
        "CONTEXT CLIENT + TYPED RESPONSE VALIDATION BUILD"
    )

    print("=" * 72)

    endpoint_contract = load_json(
        ENDPOINT_CONTRACT_FILE
    )

    http_contract = load_json(
        HTTP_CLIENT_CONTRACT_FILE
    )

    intelligence_contract = load_json(
        INTELLIGENCE_CONTRACT_FILE
    )

    production_contract = load_json(
        PRODUCTION_CONTRACT_FILE
    )

    previous = load_json(
        PREVIOUS_VERIFICATION_FILE
    )

    if (
        previous.get("status")
        !=
        "PASS"
    ):

        raise RuntimeError(
            "10.2.3-10.2.4 verification is not PASS."
        )

    if (
        previous.get(
            "stage10_ready_for_10_2_5"
        )
        is not True
    ):

        raise RuntimeError(
            "10.2.4 did not authorize 10.2.5."
        )

    for name, payload in [
        (
            "endpoint contract",
            endpoint_contract,
        ),
        (
            "HTTP client contract",
            http_contract,
        ),
        (
            "intelligence client contract",
            intelligence_contract,
        ),
        (
            "production client contract",
            production_contract,
        ),
    ]:

        if (
            payload.get("status")
            !=
            "LOCKED"
        ):

            raise RuntimeError(
                f"{name} is not LOCKED."
            )

    locked_routes = set(
        endpoint_contract.get(
            "route_set",
            []
        )
    )

    context_routes = sorted(
        route
        for route in locked_routes
        if route.startswith(
            "/api/v1/context"
        )
    )

    if (
        len(context_routes)
        !=
        10
    ):

        raise RuntimeError(
            (
                "Stage 8 context route count "
                "must remain exactly 10; "
                f"found {len(context_routes)}."
            )
        )

    (
        context_source,
        context_entries,
    ) = build_context_client(
        context_routes
    )

    production_entries = (
        production_contract.get(
            "generated_functions",
            []
        )
    )

    if not isinstance(
        production_entries,
        list,
    ):

        raise RuntimeError(
            "Production generated function contract invalid."
        )

    validated_source = (
        build_validated_api_source(
            production_entries,
            context_entries,
        )
    )

    save_text_atomic(
        CONTEXT_FILE,
        context_source,
    )

    save_text_atomic(
        VALIDATION_FILE,
        VALIDATION_SOURCE,
    )

    save_text_atomic(
        VALIDATED_API_FILE,
        validated_source,
    )

    save_text_atomic(
        RUNTIME_TEST_FILE,
        RUNTIME_TEST_SOURCE,
    )

    context_contract = {
        "stage":
            "10.2.5",

        "version":
            "1.0.0",

        "name":
            "FRONTEND_CONTEXT_API_CLIENT",

        "status":
            "LOCKED",

        "source":
            relative(
                CONTEXT_FILE
            ),

        "server_only":
            True,

        "authority":
            "STAGE8_CONTEXT",

        "shared_transport":
            relative(
                SHARED_CLIENT_FILE
            ),

        "route_source":
            "STAGE10_1_3_LOCKED_ENDPOINT_CONTRACT",

        "routes":
            context_routes,

        "route_count":
            len(
                context_routes
            ),

        "generated_functions":
            context_entries,

        "implementation": {
            "routes_manually_guessed":
                False,

            "shared_http_client_only":
                True,

            "direct_fetch":
                False,

            "get_only":
                True,

            "dynamic_segments_encoded":
                True,

            "context_recalculation":
                False,

            "model_access":
                False,

            "provider_access":
                False,

            "stale_fallback":
                False,
        },

        "source_sha256":
            sha256_file(
                CONTEXT_FILE
            ),

        "dependency_identity": {
            relative(
                ENDPOINT_CONTRACT_FILE
            ):
                identity(
                    ENDPOINT_CONTRACT_FILE
                ),

            relative(
                HTTP_CLIENT_CONTRACT_FILE
            ):
                identity(
                    HTTP_CLIENT_CONTRACT_FILE
                ),

            relative(
                PREVIOUS_VERIFICATION_FILE
            ):
                identity(
                    PREVIOUS_VERIFICATION_FILE
                ),

            relative(
                SHARED_CLIENT_FILE
            ):
                identity(
                    SHARED_CLIENT_FILE
                ),
        },

        "promotion": {
            "stage10_2_5_complete":
                False,

            "stage10_2_complete":
                False,

            "stage10_complete":
                False,
        },

        "generated_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }

    validation_contract = {
        "stage":
            "10.2.6",

        "version":
            "1.0.0",

        "name":
            "FRONTEND_TYPED_RUNTIME_RESPONSE_VALIDATION",

        "status":
            "LOCKED",

        "validation_source":
            relative(
                VALIDATION_FILE
            ),

        "validated_client_source":
            relative(
                VALIDATED_API_FILE
            ),

        "runtime_test_source":
            relative(
                RUNTIME_TEST_FILE
            ),

        "implementation": {
            "approach":
                "NATIVE_TYPESCRIPT_RUNTIME_GUARDS",

            "new_dependency_installed":
                False,

            "package_lock_mutated":
                False,

            "json_structure_validation":
                True,

            "finite_number_validation":
                True,

            "probability_range_validation":
                True,

            "outcome_enum_validation":
                True,

            "confidence_band_validation":
                True,

            "uncertainty_band_validation":
                True,

            "context_alignment_validation":
                True,

            "context_support_range_validation":
                True,

            "production_record_validation":
                True,

            "intelligence_record_validation":
                True,

            "context_identity_validation":
                True,

            "error_payloads_supported":
                True,

            "validated_transport_wrappers":
                True,
        },

        "authority_preservation": {
            "stage7_prediction":
                True,

            "stage8_context":
                True,

            "stage9_intelligence":
                True,

            "stage10_presentation_only":
                True,

            "probabilities_recalculated":
                False,

            "context_recalculated":
                False,

            "intelligence_recalculated":
                False,
        },

        "semantic_http_mapping": {
            "implemented_here":
                False,

            "owner":
                "10.2.7",
        },

        "runtime_tests": {
            "valid_production_accepted":
                True,

            "invalid_production_rejected":
                True,

            "valid_intelligence_accepted":
                True,

            "invalid_intelligence_rejected":
                True,

            "valid_context_accepted":
                True,

            "invalid_context_rejected":
                True,

            "not_ready_payload_supported":
                True,

            "invalid_json_value_rejected":
                True,
        },

        "source_identity": {
            relative(
                VALIDATION_FILE
            ):
                identity(
                    VALIDATION_FILE
                ),

            relative(
                VALIDATED_API_FILE
            ):
                identity(
                    VALIDATED_API_FILE
                ),

            relative(
                RUNTIME_TEST_FILE
            ):
                identity(
                    RUNTIME_TEST_FILE
                ),
        },

        "dependency_identity": {
            relative(
                CONTEXT_CONTRACT_FILE
            ):
                identity(
                    CONTEXT_CONTRACT_FILE
                )
                if
                CONTEXT_CONTRACT_FILE.exists()
                else
                {},

            relative(
                INTELLIGENCE_CONTRACT_FILE
            ):
                identity(
                    INTELLIGENCE_CONTRACT_FILE
                ),

            relative(
                PRODUCTION_CONTRACT_FILE
            ):
                identity(
                    PRODUCTION_CONTRACT_FILE
                ),

            relative(
                INTELLIGENCE_FILE
            ):
                identity(
                    INTELLIGENCE_FILE
                ),

            relative(
                PRODUCTION_FILE
            ):
                identity(
                    PRODUCTION_FILE
                ),

            relative(
                PACKAGE_JSON_FILE
            ):
                identity(
                    PACKAGE_JSON_FILE
                ),

            relative(
                PACKAGE_LOCK_FILE
            ):
                identity(
                    PACKAGE_LOCK_FILE
                ),
        },

        "promotion": {
            "stage10_2_6_complete":
                False,

            "stage10_2_complete":
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
        CONTEXT_CONTRACT_FILE,
        context_contract,
    )

    # Rebuild validation contract now that context contract exists,
    # so its dependency SHA is exact.
    validation_contract[
        "dependency_identity"
    ][
        relative(
            CONTEXT_CONTRACT_FILE
        )
    ] = identity(
        CONTEXT_CONTRACT_FILE
    )

    save_json_atomic(
        VALIDATION_CONTRACT_FILE,
        validation_contract,
    )

    print()

    print(
        "Context routes discovered from 10.1.3:"
    )

    for entry in context_entries:

        print(
            (
                f"  {entry['function']} "
                f"-> {entry['route']}"
            )
        )

    print()

    print(
        f"Context client: "
        f"{relative(CONTEXT_FILE)}"
    )

    print(
        f"Runtime validation: "
        f"{relative(VALIDATION_FILE)}"
    )

    print(
        f"Validated API surface: "
        f"{relative(VALIDATED_API_FILE)}"
    )

    print(
        f"Runtime validation tests: "
        f"{relative(RUNTIME_TEST_FILE)}"
    )

    print()

    print("=" * 72)

    print(
        "STAGE 10.2.5 CONTEXT API CLIENT: BUILT"
    )

    print(
        "STAGE 10.2.6 TYPED RESPONSE VALIDATION: BUILT"
    )

    print(
        "STAGE 10 IS NOT YET PROMOTED"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
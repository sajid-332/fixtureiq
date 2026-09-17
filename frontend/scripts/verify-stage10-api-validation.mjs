import fs from "node:fs";
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

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const FRONTEND_ROOT = path.resolve(__dirname, "..");
const PROJECT_ROOT = path.resolve(FRONTEND_ROOT, "..");

const OUTPUT_DIR = path.join(
  PROJECT_ROOT,
  "docs",
  "stage10"
);

const OUTPUT_FILE = path.join(
  OUTPUT_DIR,
  "frontend_audit.json"
);

const IGNORED_DIRECTORIES = new Set([
  "node_modules",
  ".next",
  ".git",
  "dist",
  "out",
  "coverage",
]);

const SOURCE_EXTENSIONS = new Set([
  ".ts",
  ".tsx",
  ".js",
  ".jsx",
  ".mjs",
  ".cjs",
]);

function toProjectRelative(filePath) {
  return path
    .relative(PROJECT_ROOT, filePath)
    .replaceAll("\\", "/");
}

function exists(filePath) {
  return fs.existsSync(filePath);
}

function readJson(filePath) {
  return JSON.parse(
    fs.readFileSync(
      filePath,
      "utf8"
    )
  );
}

function readText(filePath) {
  return fs.readFileSync(
    filePath,
    "utf8"
  );
}

function walk(directory) {
  if (!exists(directory)) {
    return [];
  }

  const result = [];

  for (
    const entry
    of fs.readdirSync(
      directory,
      {
        withFileTypes: true,
      }
    )
  ) {
    if (
      entry.isDirectory()
      &&
      IGNORED_DIRECTORIES.has(
        entry.name
      )
    ) {
      continue;
    }

    const fullPath = path.join(
      directory,
      entry.name
    );

    if (entry.isDirectory()) {
      result.push(
        ...walk(fullPath)
      );

      continue;
    }

    result.push(fullPath);
  }

  return result;
}

function dependencyVersion(
  packageJson,
  name
) {
  return (
    packageJson.dependencies?.[name]
    ??
    packageJson.devDependencies?.[name]
    ??
    null
  );
}

function detectPackageManager() {
  const candidates = [
    ["npm", "package-lock.json"],
    ["pnpm", "pnpm-lock.yaml"],
    ["yarn", "yarn.lock"],
    ["bun", "bun.lockb"],
    ["bun", "bun.lock"],
  ];

  for (
    const [manager, lockfile]
    of candidates
  ) {
    if (
      exists(
        path.join(
          FRONTEND_ROOT,
          lockfile
        )
      )
    ) {
      return {
        manager,
        lockfile,
      };
    }
  }

  return {
    manager: null,
    lockfile: null,
  };
}

function findConfigFile(names) {
  for (const name of names) {
    const candidate = path.join(
      FRONTEND_ROOT,
      name
    );

    if (exists(candidate)) {
      return toProjectRelative(
        candidate
      );
    }
  }

  return null;
}

function getLineHits(
  filePath,
  patterns
) {
  const text = readText(
    filePath
  );

  const lines = text.split(
    /\r?\n/
  );

  const hits = [];

  lines.forEach(
    (line, index) => {
      for (
        const {
          name,
          regex,
        }
        of patterns
      ) {
        regex.lastIndex = 0;

        if (regex.test(line)) {
          hits.push({
            category: name,
            file:
              toProjectRelative(
                filePath
              ),
            line: index + 1,
            sample:
              line.trim().slice(
                0,
                220
              ),
          });
        }
      }
    }
  );

  return hits;
}

function uniqueFiles(
  hits
) {
  return [
    ...new Set(
      hits.map(
        (item) => item.file
      )
    ),
  ];
}

function main() {
  console.log(
    "=".repeat(72)
  );

  console.log(
    "FixtureIQ Stage 10.1.1"
  );

  console.log(
    "EXISTING NEXT.JS FRONTEND AUDIT"
  );

  console.log(
    "=".repeat(72)
  );

  const packageJsonPath = path.join(
    FRONTEND_ROOT,
    "package.json"
  );

  if (!exists(packageJsonPath)) {
    throw new Error(
      "frontend/package.json not found."
    );
  }

  const packageJson = readJson(
    packageJsonPath
  );

  const allFiles = walk(
    FRONTEND_ROOT
  );

  const sourceFiles = allFiles.filter(
    (filePath) => {
      const relative =
        toProjectRelative(
          filePath
        );

      if (
        relative.startsWith(
          "frontend/scripts/"
        )
      ) {
        return false;
      }

      return SOURCE_EXTENSIONS.has(
        path.extname(
          filePath
        ).toLowerCase()
      );
    }
  );

  const appRouterCandidates = [
    path.join(
      FRONTEND_ROOT,
      "app"
    ),
    path.join(
      FRONTEND_ROOT,
      "src",
      "app"
    ),
  ];

  const pagesRouterCandidates = [
    path.join(
      FRONTEND_ROOT,
      "pages"
    ),
    path.join(
      FRONTEND_ROOT,
      "src",
      "pages"
    ),
  ];

  const appRoot =
    appRouterCandidates.find(
      exists
    )
    ?? null;

  const pagesRoot =
    pagesRouterCandidates.find(
      exists
    )
    ?? null;

  const pageFiles =
    sourceFiles.filter(
      (filePath) =>
        /^page\.(tsx?|jsx?)$/i.test(
          path.basename(filePath)
        )
    );

  const layoutFiles =
    sourceFiles.filter(
      (filePath) =>
        /^layout\.(tsx?|jsx?)$/i.test(
          path.basename(filePath)
        )
    );

  const routeHandlerFiles =
    sourceFiles.filter(
      (filePath) =>
        /^route\.(tsx?|jsx?)$/i.test(
          path.basename(filePath)
        )
    );

  const clientComponents =
    sourceFiles.filter(
      (filePath) => {
        const text =
          readText(filePath)
            .trimStart();

        return (
          text.startsWith(
            '"use client"'
          )
          ||
          text.startsWith(
            "'use client'"
          )
        );
      }
    );

  const usagePatterns = [
    {
      name: "fetch",
      regex:
        /\bfetch\s*\(/,
    },
    {
      name: "axios",
      regex:
        /\baxios(?:\.|\s*\()/,
    },
    {
      name: "fixtureiq_api",
      regex:
        /\/api\/(?:v1\/(?:production|context|intelligence)|health)/i,
    },
    {
      name: "next_public_env",
      regex:
        /\bNEXT_PUBLIC_[A-Z0-9_]+\b/,
    },
    {
      name: "hardcoded_localhost",
      regex:
        /https?:\/\/(?:localhost|127\.0\.0\.1)(?::\d+)?/i,
    },
  ];

  const boundaryRiskPatterns = [
    {
      name: "direct_processed_data_access",
      regex:
        /data[\\/]+processed/i,
    },
    {
      name: "direct_historical_data_access",
      regex:
        /data[\\/]+historical/i,
    },
    {
      name: "direct_model_artifact_access",
      regex:
        /\.joblib\b/i,
    },
    {
      name: "direct_intelligence_csv_access",
      regex:
        /match_intelligence(?:_base)?\.csv/i,
    },
    {
      name: "direct_context_csv_access",
      regex:
        /enriched_upcoming_fixtures\.csv/i,
    },
    {
      name: "direct_provider_api_access",
      regex:
        /\b(?:api-football|api-sports|football-data\.org)\b/i,
    },
    {
      name: "node_fs_runtime_access",
      regex:
        /(?:from\s+["'](?:node:)?fs["']|require\(["'](?:node:)?fs["']\))/i,
    },
  ];

  const usageHits = [];
  const boundaryRiskHits = [];

  for (
    const sourceFile
    of sourceFiles
  ) {
    usageHits.push(
      ...getLineHits(
        sourceFile,
        usagePatterns
      )
    );

    boundaryRiskHits.push(
      ...getLineHits(
        sourceFile,
        boundaryRiskPatterns
      )
    );
  }

  const packageManager =
    detectPackageManager();

  const audit = {
    stage: "10.1.1",
    name:
      "EXISTING_NEXTJS_FRONTEND_AUDIT",
    status: "PASS",

    generated_at_utc:
      new Date().toISOString(),

    frontend_root: "frontend",

    framework: {
      next:
        dependencyVersion(
          packageJson,
          "next"
        ),

      react:
        dependencyVersion(
          packageJson,
          "react"
        ),

      react_dom:
        dependencyVersion(
          packageJson,
          "react-dom"
        ),

      typescript:
        dependencyVersion(
          packageJson,
          "typescript"
        ),

      tailwindcss:
        dependencyVersion(
          packageJson,
          "tailwindcss"
        ),

      eslint:
        dependencyVersion(
          packageJson,
          "eslint"
        ),
    },

    package_manager:
      packageManager,

    config: {
      package_json:
        "frontend/package.json",

      tsconfig:
        exists(
          path.join(
            FRONTEND_ROOT,
            "tsconfig.json"
          )
        ),

      next_config:
        findConfigFile([
          "next.config.ts",
          "next.config.mjs",
          "next.config.js",
          "next.config.cjs",
        ]),

      eslint_config:
        findConfigFile([
          "eslint.config.mjs",
          "eslint.config.js",
          ".eslintrc.json",
          ".eslintrc.js",
        ]),

      postcss_config:
        findConfigFile([
          "postcss.config.mjs",
          "postcss.config.js",
          "postcss.config.cjs",
        ]),
    },

    routing: {
      app_router:
        Boolean(appRoot),

      app_root:
        appRoot
          ? toProjectRelative(
              appRoot
            )
          : null,

      pages_router:
        Boolean(pagesRoot),

      pages_root:
        pagesRoot
          ? toProjectRelative(
              pagesRoot
            )
          : null,

      page_files:
        pageFiles.map(
          toProjectRelative
        ),

      layout_files:
        layoutFiles.map(
          toProjectRelative
        ),

      route_handler_files:
        routeHandlerFiles.map(
          toProjectRelative
        ),
    },

    source: {
      source_file_count:
        sourceFiles.length,

      client_component_count:
        clientComponents.length,

      client_components:
        clientComponents.map(
          toProjectRelative
        ),

      public_directory:
        exists(
          path.join(
            FRONTEND_ROOT,
            "public"
          )
        ),
    },

    api_usage: {
      fetch_files:
        uniqueFiles(
          usageHits.filter(
            (item) =>
              item.category ===
              "fetch"
          )
        ),

      axios_files:
        uniqueFiles(
          usageHits.filter(
            (item) =>
              item.category ===
              "axios"
          )
        ),

      fixtureiq_api_reference_files:
        uniqueFiles(
          usageHits.filter(
            (item) =>
              item.category ===
              "fixtureiq_api"
          )
        ),

      next_public_env_files:
        uniqueFiles(
          usageHits.filter(
            (item) =>
              item.category ===
              "next_public_env"
          )
        ),

      hardcoded_localhost_files:
        uniqueFiles(
          usageHits.filter(
            (item) =>
              item.category ===
              "hardcoded_localhost"
          )
        ),

      detailed_hits:
        usageHits,
    },

    responsibility_boundary_risks: {
      count:
        boundaryRiskHits.length,

      files:
        uniqueFiles(
          boundaryRiskHits
        ),

      hits:
        boundaryRiskHits,
    },

    audit_scope: {
      ui_modified: false,
      dependencies_modified: false,
      backend_modified: false,
      stage7_modified: false,
      stage8_modified: false,
      stage9_modified: false,
    },
  };

  fs.mkdirSync(
    OUTPUT_DIR,
    {
      recursive: true,
    }
  );

  fs.writeFileSync(
    OUTPUT_FILE,
    JSON.stringify(
      audit,
      null,
      2
    )
    + "\n",
    "utf8"
  );

  console.log(
    `Next.js: ${
      audit.framework.next
      ?? "NOT FOUND"
    }`
  );

  console.log(
    `React: ${
      audit.framework.react
      ?? "NOT FOUND"
    }`
  );

  console.log(
    `TypeScript: ${
      audit.framework.typescript
      ?? "NOT FOUND"
    }`
  );

  console.log(
    `App Router: ${
      audit.routing.app_router
      ? "YES"
      : "NO"
    }`
  );

  console.log(
    `Pages Router: ${
      audit.routing.pages_router
      ? "YES"
      : "NO"
    }`
  );

  console.log(
    `Source files: ${
      audit.source.source_file_count
    }`
  );

  console.log(
    `Existing API-reference files: ${
      audit.api_usage
        .fixtureiq_api_reference_files
        .length
    }`
  );

  console.log(
    `Boundary-risk hits: ${
      audit
        .responsibility_boundary_risks
        .count
    }`
  );

  if (
    boundaryRiskHits.length
    >
    0
  ) {
    console.log(
      "\nBoundary-risk candidates:"
    );

    for (
      const hit
      of boundaryRiskHits
    ) {
      console.log(
        `  ${hit.file}:${hit.line} `
        + `[${hit.category}]`
      );
    }
  }

  console.log(
    `\nSaved: ${
      toProjectRelative(
        OUTPUT_FILE
      )
    }`
  );

  console.log(
    "\n"
    + "=".repeat(72)
  );

  console.log(
    "STAGE 10.1.1 FRONTEND AUDIT: COMPLETE"
  );

  console.log(
    "=".repeat(72)
  );
}

main();
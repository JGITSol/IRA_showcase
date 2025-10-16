# Puppeteer UI Regression Checks

This directory contains lightweight headless-browser smoke tests for the user interfaces exposed by the project. The suite visits configured URLs, performs basic availability assertions and optionally captures screenshots for visual regression tracking.

## Prerequisites

- Node.js 18 or newer (Puppeteer bundles a compatible Chromium build automatically).
- The web targets must be running locally (for example the FastAPI service on `http://localhost:8000` and the Streamlit dashboard on `http://localhost:8501`).

## Installation

```pwsh
cd tests/puppeteer
npm install
```

> The first run will download a recent Chromium build which can take a minute.

## Usage

Run the default test suite and capture screenshots:

```pwsh
npm test
```

Key options (pass after `--`):

- `--headful` – open Chrome with a visible window for debugging.
- `--only=api-docs,streamlit-dashboard` – run a subset of routes.
- `--base-url=http://staging.internal` – override the configured base URL.
- `--dry-run` – print the plan without opening a browser.

Examples:

```pwsh
# Dry-run to confirm configuration
npm test -- --dry-run

# Run only the API endpoints
npm test -- --only=api-docs,api-health

# Launch with a visible browser window
npm test -- --headful
```

Screenshots are written to `output/` (git-ignored). Each new run overwrites the existing PNG for deterministic diffs.

## Configuration

Edit `puppeteer.config.json` to add or adjust routes. Each route supports:

| Field | Description |
| --- | --- |
| `name` | Friendly identifier used in logs and filenames. |
| `path` | Path appended to the base URL. |
| `url` | Absolute URL (overrides `baseUrl + path`). |
| `waitForSelector` | Optional CSS selector to await before capturing a screenshot. |
| `expectStatus` | Expected HTTP status code (defaults to treating non-2xx as failures). |
| `screenshot` | Set to `false` to skip screenshot capture. |
| `fullPage` | Set to `false` to capture only the initial viewport. |
| `expectTitle` | Optional exact page title to assert. |
| `expectText` | String or `{ selector, value }` object to validate page content. |

The top-level `baseUrl`, `outputDir`, `viewport`, `waitUntil`, `timeout`, and `selectorTimeout` keys provide sensible defaults for all routes.

Environment variable `PUPPETEER_BASE_URL` overrides `baseUrl` at runtime.

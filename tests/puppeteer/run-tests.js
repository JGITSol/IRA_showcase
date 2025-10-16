#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

/**
 * Simple argument parser that converts CLI flags to a dictionary.
 * Supported forms:
 *   --flag             => { flag: true }
 *   --flag=value       => { flag: "value" }
 *   --flag value       => { flag: "value" }
 */
function parseArgs(argv) {
  const args = {};
  const tokens = argv.slice(2);
  while (tokens.length > 0) {
    const token = tokens.shift();
    if (!token.startsWith('--')) {
      continue;
    }
    const keyValue = token.replace(/^--/, '').split('=');
    const key = keyValue[0];
    if (keyValue.length > 1) {
      args[key] = keyValue.slice(1).join('=');
    } else if (tokens[0] && !tokens[0].startsWith('--')) {
      args[key] = tokens.shift();
    } else {
      args[key] = true;
    }
  }
  return args;
}

const args = parseArgs(process.argv);

if (args.help || args.h) {
  console.log(`Usage: node run-tests.js [options]\n\nOptions:\n  --only=name1,name2    Run only the named routes from the config\n  --base-url=url        Override the configured base URL\n  --output-dir=path     Override the screenshot output directory\n  --dry-run             Print the resolved test plan without running\n  --setup               Prepare output directories and exit\n  --headful             Launch Chrome in headed mode for debugging\n`);
  process.exit(0);
}

const configPath = path.resolve(__dirname, 'puppeteer.config.json');
if (!fs.existsSync(configPath)) {
  console.error(`Unable to locate config file at ${configPath}`);
  process.exit(1);
}

const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
const baseUrl = args['base-url'] || process.env.PUPPETEER_BASE_URL || config.baseUrl;
const outputDir = path.resolve(__dirname, args['output-dir'] || config.outputDir || './output');
const waitUntil = config.waitUntil || 'networkidle2';
const defaultTimeout = Number(config.timeout) || 30000;
const defaultSelectorTimeout = Number(config.selectorTimeout) || 15000;
const viewport = config.viewport || { width: 1280, height: 720 };

if (!baseUrl && !config.routes.every((route) => !!route.url)) {
  console.error('No baseUrl provided and at least one route relies on it.');
  process.exit(1);
}

function ensureOutputDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

ensureOutputDir(outputDir);

if (args.setup) {
  console.log(`Prepared Puppeteer output directory at ${outputDir}`);
  process.exit(0);
}

function slugify(value) {
  return value
    .toString()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .replace(/-{2,}/g, '-');
}

function resolveUrl(route) {
  if (route.url) {
    return route.url;
  }
  const routePath = route.path || '/';
  return new URL(routePath, baseUrl).toString();
}

function shouldRunRoute(route, onlyNames) {
  if (!onlyNames || onlyNames.length === 0) {
    return true;
  }
  return onlyNames.includes(route.name);
}

const only = args.only ? String(args.only).split(',').map((name) => name.trim()).filter(Boolean) : [];
const routes = (config.routes || []).filter((route) => shouldRunRoute(route, only));

if (routes.length === 0) {
  console.warn('No routes selected for Puppeteer run. Check your --only filter or config.');
  process.exit(0);
}

if (args['dry-run']) {
  console.log('Planned Puppeteer checks:');
  routes.forEach((route) => {
    console.log(`- ${route.name || route.path}: ${resolveUrl(route)}`);
  });
  process.exit(0);
}

async function run() {
  const launchOptions = { headless: args.headful ? false : 'new' };
  const browser = await puppeteer.launch(launchOptions);
  const overall = [];
  let hasErrors = false;

  try {
    for (const route of routes) {
      const name = route.name || slugify(route.path || route.url || 'route');
      const url = resolveUrl(route);
      const page = await browser.newPage();
      await page.setViewport(viewport);

      const result = { name, url };

      try {
        const response = await page.goto(url, {
          waitUntil: route.waitUntil || waitUntil,
          timeout: Number(route.timeout) || defaultTimeout,
        });

        if (route.expectStatus) {
          const status = response ? response.status() : undefined;
          if (status !== route.expectStatus) {
            throw new Error(`Expected status ${route.expectStatus} but received ${status}`);
          }
        } else if (response && !response.ok() && route.allowFailure !== true) {
          throw new Error(`Request failed for ${url} with status ${response.status()}`);
        }

        if (route.waitForSelector) {
          await page.waitForSelector(route.waitForSelector, {
            timeout: Number(route.selectorTimeout) || defaultSelectorTimeout,
          });
        }

        if (route.expectTitle) {
          const title = await page.title();
          if (title !== route.expectTitle) {
            throw new Error(`Expected title "${route.expectTitle}" but found "${title}"`);
          }
        }

        if (route.expectText) {
          const textFound = await page.evaluate((selector, expected) => {
            if (!selector) {
              return document.body.innerText.includes(expected);
            }
            const el = document.querySelector(selector);
            return el ? el.innerText.includes(expected) : false;
          }, route.expectText.selector || null, route.expectText.value || route.expectText);

          if (!textFound) {
            throw new Error(`Could not find expected text for ${name}`);
          }
        }

        if (route.screenshot !== false) {
          const fullPage = route.fullPage !== false;
          const fileName = `${slugify(name || route.path || url)}.png`;
          const filePath = path.join(outputDir, fileName);
          await page.screenshot({ path: filePath, fullPage });
          result.screenshot = path.relative(path.resolve(__dirname, '..', '..'), filePath);
        }

        result.success = true;
        console.log(`✔ ${name} (${url})`);
      } catch (error) {
        hasErrors = true;
        result.success = false;
        result.error = error.message || String(error);
        console.error(`✖ ${name} (${url}) -> ${result.error}`);
      } finally {
        await page.close();
        overall.push(result);
      }
    }
  } finally {
    await browser.close();
  }

  if (overall.some((item) => item.screenshot)) {
    console.log(`Screenshots saved to ${outputDir}`);
  }

  if (hasErrors) {
    process.exitCode = 1;
  }
}

run().catch((error) => {
  console.error(`Unexpected Puppeteer failure: ${error.message || error}`);
  process.exit(1);
});

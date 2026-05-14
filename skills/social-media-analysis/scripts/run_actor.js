#!/usr/bin/env node
/**
 * Run an Apify actor and download results.
 * Usage:
 *   node --env-file=.env run_actor.js \
 *     --actor "actor-name" \
 *     --input '{"searchTerms":["..."],"maxItems":200}' \
 *     --output result.json \
 *     --format json
 */

const fs = require("fs");
const path = require("path");

const APIFY_TOKEN = process.env.APIFY_TOKEN;
if (!APIFY_TOKEN) {
  console.error("Error: APIFY_TOKEN not found in environment.");
  process.exit(1);
}

function parseArgs() {
  const args = process.argv.slice(2);
  const opts = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--actor") opts.actor = args[++i];
    else if (args[i] === "--input") opts.input = args[++i];
    else if (args[i] === "--output") opts.output = args[++i];
    else if (args[i] === "--format") opts.format = args[++i];
  }
  return opts;
}

async function apifyRequest(url, options = {}) {
  const res = await fetch(url, {
    ...options,
    headers: {
      Authorization: `Bearer ${APIFY_TOKEN}`,
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  if (!res.ok) {
      const txt = await res.text();
      throw new Error(`Apify HTTP ${res.status}: ${txt}`);
  }
  return res.json();
}

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function run() {
  const opts = parseArgs();
  if (!opts.actor || !opts.input || !opts.output) {
    console.error("Usage: node run_actor.js --actor <name> --input '<json>' --output <file> [--format json]");
    process.exit(1);
  }

  const actorId = opts.actor.replace(/\//g, "~");
  const inputPayload = JSON.parse(opts.input);
  const outputPath = path.resolve(opts.output);
  const format = opts.format || "json";

  console.log(`Starting actor: ${actorId}`);
  console.log(`Input: ${JSON.stringify(inputPayload, null, 2)}`);

  // 1. Start run
  const runData = await apifyRequest(
    `https://api.apify.com/v2/acts/${actorId}/runs`,
    {
      method: "POST",
      body: JSON.stringify(inputPayload),
    }
  );

  const runId = runData.data.id;
  const runUrl = `https://api.apify.com/v2/acts/${actorId}/runs/${runId}`;
  console.log(`Run started: ${runId}`);

  // 2. Poll until finished
  let status = "RUNNING";
  while (["RUNNING", "READY"].includes(status)) {
    await sleep(5000);
    const statusData = await apifyRequest(runUrl);
    status = statusData.data.status;
    console.log(`Status: ${status}`);
  }

  if (status !== "SUCCEEDED") {
    console.error(`Actor failed with status: ${status}`);
    process.exit(1);
  }

  // 3. Download dataset
  const datasetId = runData.data.defaultDatasetId;
  const datasetUrl = `https://api.apify.com/v2/datasets/${datasetId}/items?format=${format}`;
  console.log(`Downloading dataset: ${datasetUrl}`);

  const itemsRes = await fetch(datasetUrl, {
    headers: { Authorization: `Bearer ${APIFY_TOKEN}` },
  });
  if (!itemsRes.ok) {
    throw new Error(`Download failed: ${itemsRes.status}`);
  }

  const items = await itemsRes.json();
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, JSON.stringify(items, null, 2), "utf-8");

  console.log(`Saved ${items.length} items to ${outputPath}`);
}

run().catch(err => {
  console.error(err);
  process.exit(1);
});

#!/usr/bin/env node
/**
 * Cluster analyzed sentiments into thematic core voices.
 * Usage:
 *   node --env-file=.env cluster_voices.js \
 *     --input analyzed_data.json \
 *     --output voices.json
 *
 * Reliability stack:
 *   1. Clusters key_phrase (concise) instead of full text
 *   2. Caps input at 50 items per polarity, confidence > 0.7
 *   3. temperature=0 + json_object response format
 *   4. HTTP retry with exponential backoff
 *   5. Strict schema validation
 *   6. One-shot self-correction on validation failure
 *   7. Hard fallback to top-5-by-engagement if all else fails
 */

const fs = require("fs");
const path = require("path");

const DEEPSEEK_KEY = process.env.DEEPSEEK_API_KEY;
if (!DEEPSEEK_KEY) {
  console.error("Error: DEEPSEEK_API_KEY not found in environment.");
  process.exit(1);
}

const API_URL = "https://api.deepseek.com/chat/completions";
const MAX_ITEMS = 50;
const MIN_CONFIDENCE = 0.7;
const MAX_CLUSTERS = 5;
const MIN_CLUSTERS = 1;

function parseArgs() {
  const args = process.argv.slice(2);
  const opts = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--input") opts.input = args[++i];
    else if (args[i] === "--output") opts.output = args[++i];
  }
  return opts;
}

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function getEngagement(item) {
  if (typeof item.likeCount === "number") return item.likeCount;
  if (typeof item.score === "number") return item.score;
  return item.confidence || 0;
}

function selectRepresentative(items) {
  // Prefer Reddit top-level comments (depth: 0), then highest engagement
  const sorted = [...items].sort((a, b) => {
    const depthA = a.depth ?? 0;
    const depthB = b.depth ?? 0;
    if (depthA !== depthB) return depthA - depthB;
    return getEngagement(b) - getEngagement(a);
  });
  return sorted[0];
}

function buildPrompt(polarity, items) {
  const label = polarity === "positive" ? "好评" : "差评";
  const lines = items.map((it, i) => `${i + 1}. "${it.key_phrase}"`);

  return `You are a thematic clustering expert. I will give you a numbered list of short key phrases extracted from social media comments. Your job is to group them into thematic clusters.

Task: Cluster the following ${label} key phrases into ${Math.min(MAX_CLUSTERS, items.length)}-${Math.max(MIN_CLUSTERS, Math.min(3, items.length))} themes.

Input phrases:
${lines.join("\n")}

Rules:
- Each phrase can belong to ONLY ONE cluster.
- A cluster should contain phrases that express the SAME type of ${polarity === "positive" ? "praise/approval" : "criticism/complaint"}.
- If a phrase is unique and doesn't fit any group, it can be its own cluster of size 1.
- Return at least ${MIN_CLUSTERS} cluster(s) and at most ${Math.min(MAX_CLUSTERS, items.length)} cluster(s).
- Theme names must be concise (max 15 Chinese characters or 30 English characters).
- ONLY use item_numbers from the list above (1 to ${items.length}). Do NOT invent numbers.

Output STRICT JSON:
{
  "clusters": [
    {
      "theme": "concise theme name",
      "item_numbers": [1, 3, 5],
      "reason": "brief explanation of why these belong together"
    }
  ]
}`;
}

async function callClustering(prompt, timeoutMs = 30000, attempt = 1) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      signal: controller.signal,
      headers: {
        Authorization: `Bearer ${DEEPSEEK_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "deepseek-chat",
        messages: [
          { role: "system", content: "You are a helpful assistant that clusters text into themes. Always return valid JSON." },
          { role: "user", content: prompt },
        ],
        temperature: 0,
        response_format: { type: "json_object" },
      }),
    });
    clearTimeout(timer);

    if (res.status === 429) {
      if (attempt <= 3) {
        const backoff = Math.pow(2, attempt) * 1000 + Math.random() * 1000;
        console.log(`  Rate limited (429). Backing off ${(backoff / 1000).toFixed(1)}s... (attempt ${attempt}/3)`);
        await sleep(backoff);
        return callClustering(prompt, timeoutMs, attempt + 1);
      }
      throw new Error("Rate limited after 3 retries");
    }

    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`DeepSeek HTTP ${res.status}: ${txt}`);
    }

    const data = await res.json();
    const raw = data.choices?.[0]?.message?.content || "{}";
    return JSON.parse(raw);
  } catch (err) {
    clearTimeout(timer);
    if (err.name === "AbortError") throw new Error("Timeout");
    throw err;
  }
}

function validateResult(result, itemCount) {
  if (!result || typeof result !== "object") return "Result is not an object";
  if (!Array.isArray(result.clusters)) return "Missing 'clusters' array";
  if (result.clusters.length < MIN_CLUSTERS) return `Too few clusters: ${result.clusters.length} < ${MIN_CLUSTERS}`;
  if (result.clusters.length > MAX_CLUSTERS) return `Too many clusters: ${result.clusters.length} > ${MAX_CLUSTERS}`;

  const usedIndices = new Set();
  for (let i = 0; i < result.clusters.length; i++) {
    const c = result.clusters[i];
    if (!c.theme || typeof c.theme !== "string") return `Cluster ${i} missing theme`;
    if (!Array.isArray(c.item_numbers)) return `Cluster ${i} missing item_numbers`;
    if (c.item_numbers.length === 0) return `Cluster ${i} has empty item_numbers`;

    for (const n of c.item_numbers) {
      if (typeof n !== "number" || n < 1 || n > itemCount || !Number.isInteger(n)) {
        return `Cluster ${i} has invalid item_number: ${n} (valid: 1-${itemCount})`;
      }
      if (usedIndices.has(n)) {
        return `Duplicate item_number ${n} across clusters`;
      }
      usedIndices.add(n);
    }
  }
  return null; // valid
}

async function selfCorrect(prompt, errorMsg) {
  const correctionPrompt = `Your previous response had a validation error:\n${errorMsg}\n\nPlease fix the error and return valid JSON with the exact same format. Do not add extra commentary.\n\n${prompt}`;
  console.log(`  Self-correcting: ${errorMsg}`);
  return callClustering(correctionPrompt, 30000, 1);
}

function fallbackCluster(items, polarity) {
  console.log(`  Falling back to top-5-by-engagement for ${polarity}`);
  const sorted = [...items].sort((a, b) => getEngagement(b) - getEngagement(a));
  const top = sorted.slice(0, 5);
  return top.map(item => ({
    theme: item.key_phrase,
    representative: item,
    cluster_size: 1,
    avg_confidence: item.confidence || 0,
  }));
}

async function clusterPolarity(items, polarity) {
  if (items.length === 0) return [];

  // 1. Quality filter + cap
  const filtered = items
    .filter(it => (it.confidence || 0) >= MIN_CONFIDENCE && it.key_phrase)
    .sort((a, b) => getEngagement(b) - getEngagement(a))
    .slice(0, MAX_ITEMS);

  if (filtered.length === 0) {
    // If no high-confidence items, fall back to all items with key_phrase
    const alt = items.filter(it => it.key_phrase).slice(0, MAX_ITEMS);
    if (alt.length === 0) return [];
    return fallbackCluster(alt, polarity);
  }

  const prompt = buildPrompt(polarity, filtered);

  // 2. Primary attempt
  let result;
  try {
    result = await callClustering(prompt);
  } catch (err) {
    console.log(`  Primary clustering failed for ${polarity}: ${err.message}`);
    return fallbackCluster(filtered, polarity);
  }

  // 3. Validate
  let error = validateResult(result, filtered.length);

  // 4. Self-correct once
  if (error) {
    try {
      result = await selfCorrect(prompt, error);
      error = validateResult(result, filtered.length);
    } catch (err) {
      console.log(`  Self-correction failed for ${polarity}: ${err.message}`);
      return fallbackCluster(filtered, polarity);
    }
  }

  if (error) {
    console.log(`  Validation failed after self-correction for ${polarity}: ${error}`);
    return fallbackCluster(filtered, polarity);
  }

  // 5. Build final output
  const clusters = result.clusters.map(c => {
    const clusterItems = c.item_numbers.map(n => filtered[n - 1]);
    const representative = selectRepresentative(clusterItems);
    const avgConfidence = clusterItems.reduce((sum, it) => sum + (it.confidence || 0), 0) / clusterItems.length;
    return {
      theme: c.theme,
      representative,
      cluster_size: clusterItems.length,
      avg_confidence: Math.round(avgConfidence * 100) / 100,
    };
  });

  console.log(`  ${polarity}: ${clusters.length} clusters from ${filtered.length} items`);
  return clusters;
}

async function main() {
  const opts = parseArgs();
  if (!opts.input || !opts.output) {
    console.error("Usage: node cluster_voices.js --input <file> --output <file>");
    process.exit(1);
  }

  const inputPath = path.resolve(opts.input);
  const outputPath = path.resolve(opts.output);

  const raw = JSON.parse(fs.readFileSync(inputPath, "utf-8"));
  const items = Array.isArray(raw) ? raw : [];

  if (items.length === 0) {
    fs.writeFileSync(outputPath, JSON.stringify({ positive: [], negative: [] }, null, 2), "utf-8");
    console.log("No items to cluster. Wrote empty voices.");
    return;
  }

  const positive = items.filter(it => it.sentiment === "positive");
  const negative = items.filter(it => it.sentiment === "negative");

  console.log(`Clustering ${positive.length} positive, ${negative.length} negative items...`);

  const [posClusters, negClusters] = await Promise.all([
    clusterPolarity(positive, "positive"),
    clusterPolarity(negative, "negative"),
  ]);

  const output = {
    positive: posClusters,
    negative: negClusters,
  };

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, JSON.stringify(output, null, 2), "utf-8");

  console.log(`Done. Positive clusters: ${posClusters.length}, Negative clusters: ${negClusters.length}`);
  console.log(`Output saved to ${outputPath}`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});

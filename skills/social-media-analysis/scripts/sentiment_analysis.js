#!/usr/bin/env node
/**
 * Batch sentiment analysis via DeepSeek API with checkpoint/resume support.
 * Usage:
 *   node --env-file=.env sentiment_analysis.js \
 *     --input cleaned_data.json \
 *     --output analyzed_data.json \
 *     --concurrency 10 \
 *     --timeout 30000
 *
 * Features:
 * - Auto-resume: if output file exists, skips already-analyzed items
 * - Streaming save: persists progress after every batch
 * - Adaptive concurrency: dynamically adjusts based on failure rate
 * - Exponential backoff on 429 errors
 */

const fs = require("fs");
const path = require("path");

const DEEPSEEK_KEY = process.env.DEEPSEEK_API_KEY;
if (!DEEPSEEK_KEY) {
  console.error("Error: DEEPSEEK_API_KEY not found in environment.");
  process.exit(1);
}

const API_URL = "https://api.deepseek.com/chat/completions";
const SYSTEM_PROMPT = `You are a social-media sentiment analysis expert.
Analyze the given text and output STRICT JSON with these fields:
- sentiment: "positive" | "negative" | "neutral"
- confidence: 0.0-1.0
- key_phrase: the core idea in the original language (max 100 chars)
- reasoning: brief explanation in Chinese (for downstream reporting)

Core Rules:
- positive: praise, approval, support, recommendation
- negative: criticism, doubt, opposition, sarcasm, irony
- neutral: objective statement, no clear emotion, pure information
- Map "sarcastic" to "negative" in the final sentiment field.
- Do not over-interpret factual announcements as positive/negative.
- For quote tweets or forum replies, judge by the comment/reply, not the original post.

CRITICAL patterns you MUST recognize:

1. Sarcasm / Irony (negative):
   "Amazing, it crashed again 👏" → negative
   "Love how they 'innovated' by copying everyone else" → negative
   "Yeah no" → negative

2. Misdirected criticism (check who the negative is REALLY aimed at):
   "No shade to Exa but what an absurd thing for Google to do. Whoever runs partnerships at Exa deserves a gigantic raise." → positive (for Exa)
   The word "absurd" criticizes Google, NOT Exa. "deserves a gigantic raise" is direct praise.

3. Concessive praise (positive despite initial flaw):
   "It's a bit pricey ngl, but the quality is unmatched" → positive
   "Not perfect, but honestly the best I've used" → positive

4. Bait-and-switch criticism (negative):
   "Looks stunning on the surface, but under the hood it's a mess" → negative
   "Great marketing, terrible product" → negative

5. Social media slang (context-dependent):
   "Mid" → negative  "Slaps" / "Hits different" → positive
   "No cap" + praise → positive  "Cap" / "That's cap" → negative
   "Insane" + praise → positive  "Insane" + criticism → negative

6. Emoji cues (do not decide alone, combine with text):
   🙄 😒 🤡 → usually negative/sarcastic  👏 in criticism → sarcastic

7. Reddit context:
   - For posts, analyze title + selfText together as one unit.
   - For comments, analyze body only.
   - "Based" → positive (approval)  "Cringe" → negative  "Copium" → negative (delusion)`;

function parseArgs() {
  const args = process.argv.slice(2);
  const opts = { concurrency: 10, timeout: 30000 };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--input") opts.input = args[++i];
    else if (args[i] === "--output") opts.output = args[++i];
    else if (args[i] === "--concurrency") opts.concurrency = parseInt(args[++i], 10);
    else if (args[i] === "--timeout") opts.timeout = parseInt(args[++i], 10);
  }
  return opts;
}

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function analyzeOne(text, timeoutMs, attempt = 1) {
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
          { role: "system", content: SYSTEM_PROMPT },
          { role: "user", content: text },
        ],
        temperature: 0.3,
        response_format: { type: "json_object" },
      }),
    });
    clearTimeout(timer);

    if (res.status === 429) {
      if (attempt <= 3) {
        const backoff = Math.pow(2, attempt) * 1000 + Math.random() * 1000;
        console.log(`\n  Rate limited (429). Backing off ${(backoff/1000).toFixed(1)}s... (attempt ${attempt}/3)`);
        await sleep(backoff);
        return analyzeOne(text, timeoutMs, attempt + 1);
      }
      throw new Error("Rate limited after 3 retries");
    }

    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`DeepSeek HTTP ${res.status}: ${txt}`);
    }

    const data = await res.json();
    const raw = data.choices?.[0]?.message?.content || "{}";
    const parsed = JSON.parse(raw);

    const s = String(parsed.sentiment).toLowerCase();
    if (s === "sarcastic") parsed.sentiment = "negative";
    else if (!["positive", "negative", "neutral"].includes(s)) parsed.sentiment = "neutral";

    return {
      sentiment: parsed.sentiment,
      confidence: typeof parsed.confidence === "number" ? parsed.confidence : 0.5,
      key_phrase: parsed.key_phrase || "",
      reasoning: parsed.reasoning || "",
    };
  } catch (err) {
    clearTimeout(timer);
    if (err.name === "AbortError") throw new Error("Timeout");
    throw err;
  }
}

function saveProgress(outputPath, items) {
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, JSON.stringify(items, null, 2), "utf-8");
}

async function runWithCheckpoint(items, outputPath, initialConcurrency, timeoutMs) {
  let completed = items.filter(i => i.sentiment !== undefined).length;
  let failCount = 0;
  let concurrency = initialConcurrency;
  const total = items.length;

  // Find indices that still need analysis
  const pendingIndices = items
    .map((item, i) => (item.sentiment === undefined ? i : -1))
    .filter(i => i !== -1);

  if (pendingIndices.length === 0) {
    console.log("All items already analyzed. Resuming from checkpoint.");
    return { failCount };
  }

  console.log(`${completed}/${total} already analyzed. Analyzing remaining ${pendingIndices.length}...`);

  let idxPointer = 0;
  let batchFailCount = 0;
  let batchCount = 0;

  async function worker() {
    while (idxPointer < pendingIndices.length) {
      const i = pendingIndices[idxPointer++];
      const item = items[i];
      const text = item.text || "";

      if (!text.trim()) {
        items[i] = { ...item, sentiment: "neutral", confidence: 0, key_phrase: "", reasoning: "Empty text" };
        completed++;
        batchCount++;
        process.stdout.write(`\rProgress: ${completed}/${total}`);
        continue;
      }

      try {
        const result = await analyzeOne(text, timeoutMs);
        items[i] = { ...item, ...result };
        completed++;
        batchCount++;
        process.stdout.write(`\rProgress: ${completed}/${total}`);
      } catch (err) {
        failCount++;
        batchFailCount++;
        items[i] = { ...item, sentiment: "error", confidence: 0, key_phrase: "", reasoning: err.message };
        completed++;
        batchCount++;
        process.stdout.write(`\rProgress: ${completed}/${total} (failures: ${failCount})`);
      }

      // Save progress every 10 items or when batch is large
      if (batchCount >= 10) {
        saveProgress(outputPath, items);
        batchCount = 0;

        // Adaptive concurrency adjustment
        const batchFailRate = batchFailCount / 10;
        if (batchFailRate > 0.4 && concurrency > 3) {
          concurrency = Math.max(3, Math.floor(concurrency * 0.6));
          console.log(`\n  High failure rate detected. Reducing concurrency to ${concurrency}.`);
        } else if (batchFailRate > 0.2 && concurrency > 5) {
          concurrency = Math.max(5, Math.floor(concurrency * 0.7));
          console.log(`\n  Elevated failure rate. Reducing concurrency to ${concurrency}.`);
        }
        batchFailCount = 0;
      }
    }
  }

  const workers = Array.from({ length: concurrency }, () => worker());
  await Promise.all(workers);

  // Final save
  saveProgress(outputPath, items);
  console.log(); // newline
  return { failCount };
}

async function main() {
  const opts = parseArgs();
  if (!opts.input || !opts.output) {
    console.error("Usage: node sentiment_analysis.js --input <file> --output <file> [--concurrency 10] [--timeout 30000]");
    process.exit(1);
  }

  const inputPath = path.resolve(opts.input);
  const outputPath = path.resolve(opts.output);

  const raw = JSON.parse(fs.readFileSync(inputPath, "utf-8"));
  const items = Array.isArray(raw) ? raw : [];
  console.log(`Loaded ${items.length} items for analysis`);

  if (items.length === 0) {
    fs.writeFileSync(outputPath, "[]", "utf-8");
    console.log("No items to analyze. Wrote empty array.");
    return;
  }

  // Resume from checkpoint if output exists
  let workingItems = items;
  if (fs.existsSync(outputPath)) {
    try {
      const existing = JSON.parse(fs.readFileSync(outputPath, "utf-8"));
      if (Array.isArray(existing) && existing.length === items.length) {
        workingItems = existing;
        console.log(`Found existing output. Resuming from checkpoint...`);
      } else {
        console.log(`Existing output mismatch (length ${existing.length} vs ${items.length}). Starting fresh.`);
      }
    } catch {
      console.log("Existing output corrupted. Starting fresh.");
    }
  }

  const { failCount } = await runWithCheckpoint(workingItems, outputPath, opts.concurrency, opts.timeout);

  // Retry errors once more with minimum concurrency
  const errorIndices = workingItems
    .map((r, i) => (r.sentiment === "error" ? i : -1))
    .filter(i => i !== -1);

  if (errorIndices.length > 0 && errorIndices.length <= workingItems.length * 0.5) {
    console.log(`Retrying ${errorIndices.length} failed items with concurrency=2...`);
    let retryIdx = 0;
    async function retryWorker() {
      while (retryIdx < errorIndices.length) {
        const i = errorIndices[retryIdx++];
        try {
          const result = await analyzeOne(workingItems[i].text, opts.timeout);
          workingItems[i] = { ...workingItems[i], ...result };
          process.stdout.write(`\rRetry progress: ${retryIdx}/${errorIndices.length}`);
        } catch (err) {
          process.stdout.write(`\rRetry progress: ${retryIdx}/${errorIndices.length} (still failing)`);
        }
      }
    }
    await Promise.all([retryWorker(), retryWorker()]);
    saveProgress(outputPath, workingItems);
    console.log();
  }

  const finalFailCount = workingItems.filter(r => r.sentiment === "error").length;
  console.log(`Done. Total: ${workingItems.length}, Success: ${workingItems.length - finalFailCount}, Failed: ${finalFailCount}`);
  console.log(`Output saved to ${outputPath}`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});

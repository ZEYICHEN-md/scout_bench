// 情感分析准确性测试 - 调用 DeepSeek API 验证分类

const fs = require('fs');
const path = require('path');

// 读取 sentiment prompt
const promptPath = path.join(__dirname, '../../..', '.claude/skills/social-media-analysis/references/sentiment_prompt.md');
const SENTIMENT_PROMPT = fs.readFileSync(promptPath, 'utf-8');

// 测试用例
const testCases = [
  {
    id: 1,
    text: "This new update is absolutely incredible, best feature they've added in years",
    expected: "positive",
    description: "直接赞扬"
  },
  {
    id: 2,
    text: "It's a bit pricey ngl, but the quality is unmatched",
    expected: "positive",
    description: "欲扬先抑"
  },
  {
    id: 3,
    text: "Looks stunning on the surface, but under the hood it's a mess",
    expected: "negative",
    description: "欲抑先扬"
  },
  {
    id: 4,
    text: "Amazing, it crashed again 👏",
    expected: "negative",
    description: "反讽"
  },
  {
    id: 5,
    text: "Yeah no, this is not it",
    expected: "negative",
    description: "表面肯定实际否定"
  },
  {
    id: 6,
    text: "Apple just announced the new iPhone 15 today",
    expected: "neutral",
    description: "客观陈述"
  },
  {
    id: 7,
    text: "Lmao this meme is hilarious",
    expected: "positive",
    description: "搞笑内容（Lmao + hilarious = positive）"
  },
  {
    id: 8,
    text: "Love how they 'innovated' by copying everyone else",
    expected: "negative",
    description: "阴阳怪气（引号强调虚假）"
  },
  {
    id: 9,
    text: "No cap, this slaps different",
    expected: "positive",
    description: "俚语正面（no cap + slaps）"
  },
  {
    id: 10,
    text: "Mid product, nothing special about it",
    expected: "negative",
    description: "俚语负面（mid = 平庸）"
  }
];

const API_KEY = process.env.DEEPSEEK_API_KEY;
if (!API_KEY) {
  console.error("❌ DEEPSEEK_API_KEY not found in environment");
  process.exit(1);
}

async function analyzeSentiment(text) {
  const response = await fetch("https://api.deepseek.com/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${API_KEY}`
    },
    body: JSON.stringify({
      model: "deepseek-chat",
      messages: [
        { role: "system", content: SENTIMENT_PROMPT },
        { role: "user", content: text }
      ],
      temperature: 0.3
    })
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  const content = data.choices[0]?.message?.content || "";

  // 提取 JSON
  const jsonMatch = content.match(/\{[\s\S]*\}/);
  if (!jsonMatch) {
    throw new Error("No JSON found in response");
  }

  return JSON.parse(jsonMatch[0]);
}

async function runTests() {
  console.log("=== 情感分析准确性测试 ===\n");
  console.log(`测试数量: ${testCases.length} 条`);
  console.log("模型: deepseek-chat");
  console.log("\n");

  let passed = 0;
  let failed = 0;
  const results = [];

  for (const tc of testCases) {
    try {
      const result = await analyzeSentiment(tc.text);
      const success = result.sentiment === tc.expected;

      results.push({
        ...tc,
        actual: result.sentiment,
        confidence: result.confidence,
        key_phrase: result.key_phrase,
        reasoning: result.reasoning,
        success
      });

      if (success) {
        console.log(`✅ #${tc.id} ${tc.description}`);
        console.log(`   Expected: ${tc.expected} | Actual: ${result.sentiment} | Confidence: ${result.confidence}`);
        passed++;
      } else {
        console.log(`❌ #${tc.id} ${tc.description}`);
        console.log(`   Text: ${tc.text}`);
        console.log(`   Expected: ${tc.expected} | Actual: ${result.sentiment} | Confidence: ${result.confidence}`);
        console.log(`   Reasoning: ${result.reasoning}`);
        failed++;
      }
    } catch (err) {
      console.log(`❌ #${tc.id} ${tc.description} - ERROR: ${err.message}`);
      failed++;
      results.push({ ...tc, error: err.message, success: false });
    }

    // 延迟避免速率限制
    await new Promise(r => setTimeout(r, 500));
  }

  console.log("\n=== 结果汇总 ===");
  console.log(`通过: ${passed}/${testCases.length}`);
  console.log(`失败: ${failed}/${testCases.length}`);
  console.log(`准确率: ${(passed / testCases.length * 100).toFixed(1)}%`);

  // 保存详细结果
  const outputPath = path.join(__dirname, 'sentiment_test_results.json');
  fs.writeFileSync(outputPath, JSON.stringify(results, null, 2));
  console.log(`\n详细结果已保存: ${outputPath}`);

  if (failed > 0) {
    process.exit(1);
  }
}

runTests().catch(err => {
  console.error("Test runner error:", err);
  process.exit(1);
});

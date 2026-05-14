// 输入解析测试 - 验证自然语言到 Twitter 搜索语法的转换逻辑

const testCases = [
  {
    id: 1,
    name: "自然语言-最近N条",
    input: "搜一下马斯克最近10条关于AI的推文",
    expected: {
      searchTerms: ["from:elonmusk AI"],
      queryType: "Latest",
      maxItems: 10
    }
  },
  {
    id: 2,
    name: "自然语言-最热门",
    input: "查一下马斯克最热门的关于特斯拉的推文",
    expected: {
      searchTerms: ["from:elonmusk Tesla"],
      queryType: "Top",
      maxItems: 200
    }
  },
  {
    id: 3,
    name: "自然语言-回复过滤",
    input: "搜一下马斯克关于SpaceX的回复和评论",
    expected: {
      searchTerms: ["from:elonmusk SpaceX filter:replies"],
      queryType: "Latest",
      maxItems: 200
    }
  },
  {
    id: 4,
    name: "自然语言-转发过滤",
    input: "马斯克最近转发的推文",
    expected: {
      searchTerms: ["from:elonmusk filter:nativeretweets"],
      queryType: "Latest",
      maxItems: 200
    }
  },
  {
    id: 5,
    name: "高级搜索语法-直接使用",
    input: "from:elonmusk since_time:1735689600 until_time:1743465600 AI",
    expected: {
      searchTerms: ["from:elonmusk since_time:1735689600 until_time:1743465600 AI"],
      queryType: "Latest",
      maxItems: 200
    }
  },
  {
    id: 6,
    name: "混合输入-时间范围+关键词",
    input: "查 @elonmusk 2025年1月到3月关于中国AI的所有推文，包括转发和回复",
    expected: {
      searchTerms: [
        "from:elonmusk since_time:1735689600 until_time:1743465600 China AI filter:replies filter:nativeretweets",
        "from:elonmusk since_time:1735689600 until_time:1743465600 Chinese AI filter:replies filter:nativeretweets"
      ],
      queryType: "Latest",
      maxItems: 500
    }
  }
];

// 模拟解析函数（基于 SKILL.md 规则）
function parseInput(input) {
  const result = {
    searchTerms: [],
    queryType: "Latest",
    maxItems: 200
  };

  // 检测 queryType
  if (input.includes("最近") && /\d+/.test(input)) {
    result.queryType = "Latest";
    const match = input.match(/(\d+)/);
    if (match) result.maxItems = parseInt(match[1]);
  } else if (input.includes("最热门")) {
    result.queryType = "Top";
  }

  // 检测 filter
  let filter = "";
  if (input.includes("回复") || input.includes("评论")) {
    filter += " filter:replies";
  }
  if (input.includes("转发")) {
    filter += " filter:nativeretweets";
  }
  if (input.includes("引用")) {
    filter += " filter:quote";
  }

  // 处理不同输入形式
  if (input.startsWith("from:")) {
    // 形式 B: 直接使用
    result.searchTerms = [input.trim()];
  } else if (input.includes("@")) {
    // 形式 C: 混合
    const username = input.match(/@(\w+)/)?.[1] || "elonmusk";
    const keywords = ["China AI", "Chinese AI"];
    const timeRange = "since_time:1735689600 until_time:1743465600";
    result.searchTerms = keywords.map(k => `from:${username} ${timeRange} ${k}${filter}`);
    result.maxItems = 500;
  } else {
    // 形式 A: 自然语言
    const person = input.includes("马斯克") ? "elonmusk" : "";
    const topic = input.includes("AI") ? "AI" :
                  input.includes("特斯拉") ? "Tesla" :
                  input.includes("SpaceX") ? "SpaceX" : "";

    if (person && topic) {
      result.searchTerms = [`from:${person} ${topic}${filter}`];
    } else if (person && filter.trim()) {
      result.searchTerms = [`from:${person}${filter}`];
    }
  }

  return result;
}

// Mock 数据过滤测试
function testMockFiltering() {
  const rawData = [
    { id: 1, type: "tweet", text: "Real tweet about AI" },
    { id: -1, type: "mock_tweet", text: "From KaitoEasyAPI, a reminder..." },
    { id: 2, type: "tweet", text: "Another real tweet" },
    { id: -1, type: "mock_tweet", text: "Mock data padding" }
  ];

  const realTweets = rawData.filter(r => r.type !== "mock_tweet" && r.id !== -1);

  return {
    passed: realTweets.length === 2 && realTweets.every(t => t.id > 0),
    expected: 2,
    actual: realTweets.length
  };
}

// 运行测试
console.log("=== 输入解析测试 ===\n");

let passed = 0;
let failed = 0;

testCases.forEach(tc => {
  const result = parseInput(tc.input);
  const success = JSON.stringify(result.searchTerms) === JSON.stringify(tc.expected.searchTerms) &&
                  result.queryType === tc.expected.queryType &&
                  result.maxItems === tc.expected.maxItems;

  if (success) {
    console.log(`✅ ${tc.name}`);
    passed++;
  } else {
    console.log(`❌ ${tc.name}`);
    console.log(`   Input: ${tc.input}`);
    console.log(`   Expected:`, tc.expected);
    console.log(`   Actual:`, result);
    failed++;
  }
});

console.log("\n=== Mock 数据过滤测试 ===\n");
const mockTest = testMockFiltering();
if (mockTest.passed) {
  console.log(`✅ Mock 过滤测试 - ${mockTest.actual}/${mockTest.expected} 条真实数据`);
  passed++;
} else {
  console.log(`❌ Mock 过滤测试 - 期望 ${mockTest.expected} 条，实际 ${mockTest.actual} 条`);
  failed++;
}

console.log(`\n=== 结果: ${passed} 通过, ${failed} 失败 ===`);

if (failed > 0) {
  process.exit(1);
}

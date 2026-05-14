---
name: mongodb
description: 单一 MongoDB skill，内部按 collection profile 分层，对外只需安装和使用这一个 skill。
version: 3.0.0
author: Bin
state: stable
enabled: true
tags:
  - database
  - mongodb
  - sourcing-system
  - data-entry
maintainer: Bin
---

# MongoDB Skill

单一 MongoDB skill，内部按 collection 分层：每个 collection 独立一个 `<name>_ops.py`，`mongo_skill.py` 只做 re-export。

当前支持的 collection：

| collection | database | profile |
|---|---|---|
| `signals` | `sourcing_system` | `profiles/signals.json` |
| `companies` | `sourcing_system` | `profiles/companies.json` |
| `wechat.articles` | `db1` | `profiles/wechat_articles.json` |

## 连接配置

按下面的优先级读取：

1. 显式传入的 `uri`
2. 环境变量 `MONGODB_URI`
3. `skills/mongodb/mongodb.json`
4. 本地 `.openclaw/mongodb.json`（兼容旧配置）

当前仓库默认把共享连接写在 `skills/mongodb/mongodb.json`：

```json
{
  "uri": "mongodb://user:pass@host:port/db?authSource=admin"
}
```

也可以继续使用环境变量覆盖：

```bash
export MONGODB_URI="mongodb://user:pass@host:port/db?authSource=admin"
```

## API

### signals

| 函数 | 说明 |
|---|---|
| `insert_signal(source_type, source_id, sector, title, ...)` | 写入/更新信号（幂等） |
| `find_signal(source_type, source_id)` | 按来源查单条信号 |
| `get_signals_by_company(company_name, limit=20)` | 按公司查近期信号 |
| `get_signals_by_sector(sector, days=30, limit=100)` | 按赛道查近期信号 |
| `count_signals(sector=None, days=None)` | 统计信号数量 |

### companies

| 函数 | 说明 |
|---|---|
| `insert_company(name, sector, direction="AI", author="Bin", description=None, metadata=None)` | 写入/更新公司（幂等） |
| `get_company_by_name(name)` | 按名称查公司 |
| `get_all_companies(sector=None, status=None)` | 列出公司（可筛选） |
| `update_company_status(name, status)` | 更新公司状态 |
| `count_companies(sector=None)` | 统计公司数量 |

`companies` 写入时 `direction` 和 `author` 为必填字段；未显式传入时分别默认 `AI` 和 `Bin`。

### wechat_articles（db1 / wechat.articles）

| 函数 | 说明 |
|---|---|
| `upsert_article(source_id, wx_name, title, batch, ...)` | 写入/更新文章（幂等，`source_id` 即原始 `_id`） |
| `get_article(source_id)` | 按 source_id 查单篇文章 |
| `get_articles_by_wx_name(wx_name, limit=20)` | 按公众号查文章 |
| `get_articles_by_batch(batch, limit=200)` | 按批次（YYYY-MM-DD）查文章 |
| `get_articles_with_individuals(batch=None, limit=50)` | 查包含 individuals 提取结果的文章 |
| `count_articles(wx_name=None, batch=None)` | 统计文章数量 |

> **`individuals` 字段说明**：每篇文章携带一个人物提取数组，每条记录包含
> `entrepreneur_name / technical_field / former_company / former_position /
> current_company / current_position / is_chinese / is_startup /
> is_recent_resignation / has_funding / is_tech_domain / is_strong_sign /
> has_big_company_experience` 等布尔与文本字段。

## 新增 Collection 的步骤

只需要 3 步，**不需要改动任何现有文件**（除了 `mongo_skill.py` 的 re-export 块）：

```
1. profiles/<name>.json       ← 定义 schema、allowed_ops、unique_keys 等
2. scripts/<name>_ops.py      ← collection 专属函数
3. scripts/mongo_skill.py     ← 加一个 import 块 + __all__ 条目
   (可选) SKILL.md            ← 补充 API 文档
```

### profiles/<name>.json 模板

```json
{
  "skill_name": "mongodb/<name>",
  "database": "sourcing_system",
  "collection": "<name>",
  "allowed_ops": ["find", "insert", "upsert", "update"],
  "allowed_fields": ["field_a", "field_b", "metadata"],
  "required_fields": ["field_a"],
  "unique_keys": ["field_a"],
  "default_sort": [["updated_at", -1]],
  "default_limit": 50
}
```

### scripts/<name>_ops.py 模板

```python
"""<Name> collection operations."""
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from base_ops import find_many, find_one, load_profile, upsert_one

_PROFILE = load_profile(_SCRIPT_DIR.parent / "profiles" / "<name>.json")


def insert_<name>(field_a: str, ...) -> str:
    return upsert_one(_PROFILE, {"field_a": field_a, ...})


def get_<name>_by_field(field_a: str):
    return find_one(_PROFILE, {"field_a": field_a})
```

## 文件结构

```
skills/mongodb/
  SKILL.md
  README.md
  mongodb.json              ← 默认共享连接配置
  requirements.txt
  profiles/
    signals.json              ← signals collection schema
    companies.json            ← companies collection schema
    wechat_articles.json      ← wechat.articles collection schema
    <name>.json               ← 新增时只加这一个文件（schema）
  scripts/
    client.py                 ← MongoDB 连接/序列化工具
    base_ops.py               ← profile 驱动的通用 CRUD
    signals_ops.py            ← signals 专属函数
    companies_ops.py          ← companies 专属函数
    wechat_articles_ops.py    ← wechat.articles 专属函数
    <name>_ops.py             ← 新增时只加这一个文件（函数）
    mongo_skill.py            ← 统一 re-export 入口
```

---
name: mongodb
description: 标准化的 MongoDB 数据插入 skill，支持 signal（信号）和 company（公司）数据的增删改查，以及赛道排名、IC投票和周排名管理。基于 sourcing_system 数据库。
version: 1.0.0
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

## 功能概述

这个 skill 提供了一组简洁的命令，用于向 MongoDB 的 `sourcing_system` 数据库插入和查询标准化数据。支持以下实体：

- **signal** - 源头信号（source_type, source_id, sector, title, summary, signal_date）
- **company** - 公司信息（name, sector, description）
- **sector_ranking** - 赛道排名（周排名、理由、来源信号）
- **ic_vote** - IC（投资委员会）投票（session, company, role, score, argument）
- **weekly_ranking** - 最终周排名（final_rank, final_score, recommendation）
- **manual_input** - 手动输入记录

所有操作自动连接 MongoDB（从环境变量 `MONGODB_URI` 读取），支持 upsert（存在即更新）。

## 连接配置

在运行命令前，确保环境变量已设置：

```bash
export MONGODB_URI="mongodb://username:password@host:port/database?authSource=admin"
```

你的代码中默认 URI 指向 AliCloud MongoDB。如需修改，可在技能配置中覆盖。

## 命令

### 插入信号 (signal)

**命令格式：**
```
插入信号：来源类型=新闻，来源ID=news-001，赛道=AI，标题=新模型发布，日期=2026-04-15，摘要=详细内容...
```

**必需字段：**
- `来源类型` (source_type) - 如：新闻、研报、社交媒体、内部
- `来源ID` (source_id) - 唯一标识符（如新闻链接ID）
- `赛道` (sector) - 行业分类（如 AI、生物科技、金融）
- `标题` (title) - 信号标题
- `日期` (signal_date) - 事件日期，格式 YYYY-MM-DD

**可选字段：**
- `摘要` (summary) - 详细描述
- `元数据` (metadata) - JSON 格式的附加信息

**示例：**
```
插入信号：来源类型=研报，来源ID=report-2026-04，赛道=新能源，标题=电池技术突破，日期=2026-04-14，摘要=某公司发布固态电池...
```

### 插入公司 (company)

**命令格式：**
```
插入公司：名称=未来智能，赛道=AI，描述=专注AGI研发...
```

**必需字段：**
- `名称` (name) - 公司全名
- `赛道` (sector) - 行业分类

**可选字段：**
- `描述` (description) - 公司简介
- `元数据` (metadata) - JSON 附加信息

**示例：**
```
插入公司：名称=深度思维，赛道=AI，描述=深度学习框架开发商
```

### 查询公司

**命令格式：**
```
查询公司：名称=未来智能
```

返回公司的完整信息（包括 createdAt、updatedAt）。

### 查询某赛道的信号

**命令格式：**
```
查询信号：赛道=AI，天数=30，限制=50
```

参数：
- `赛道` (sector) - 必需
- `天数` (days) - 可选，默认 30 天
- `限制` (limit) - 可选，默认 100 条

### 查询某公司的信号

**命令格式：**
```
查询信号：公司=未来智能，限制=20
```

### 插入赛道排名

**命令格式：**
```
插入赛道排名：周起始=2026-04-13，赛道=AI，公司=深度思维，排名=1，理由=技术领先，来源信号=[id1,id2]
```

**必需字段：**
- `周起始` (week_start) - 周一的日期 YYYY-MM-DD
- `赛道` (sector)
- `公司` (company_name)
- `排名` (rank) - 整数
- `理由` (rationale) - 文字说明
- `来源信号` (source_signals) - 信号ID列表，JSON 数组

### 插入 IC 投票

**命令格式：**
```
插入IC投票：会话ID=session123，公司=深度思维，角色=技术评委，评分=85，论点=团队强，结论=推荐
```

**必需字段：**
- `会话ID` (session_id) - IC 会议 session ID
- `公司` (company_name)
- `角色` (role) - 如：技术、业务、财务
- `评分` (score) - 0-100
- `论点` (argument) - 评分理由
- `结论` (verdict) - 同意/反对/保留

### 插入周排名

**命令格式：**
```
插入周排名：周起始=2026-04-13，公司=深度思维，最终排名=1，最终分数=92，建议=重点投资，行动项=["尽调","打款"]
```

**必需字段：**
- `周起始` (week_start)
- `公司` (company_name)
- `最终排名` (final_rank)
- `最终分数` (final_score)
- `建议` (recommendation)
- `行动项` (action_items) - JSON 数组

### 创建 IC 会话

**命令格式：**
```
创建IC会话：周起始=2026-04-13
```

返回新创建的 session ID。

### 获取周排名

**命令格式：**
```
获取周排名：周起始=2026-04-13
```

### 获取赛道排名

**命令格式：**
```
获取赛道排名：周起始=2026-04-13，赛道=AI
```

## 输出格式

所有查询操作返回 JSON 格式的数据，包含：
- `id` - MongoDB 的 `_id` 字符串
- 业务字段（name, title, sector 等）
- `created_at` / `updated_at` 时间戳（ISO 格式）

插入/更新操作返回创建/更新的文档 ID。

## 错误处理

- **连接失败** - 检查 `MONGODB_URI` 是否正确，网络是否可达
- **重复键** - `insert_signal` 和 `insert_company` 使用 upsert，会更新已有记录
- **字段缺失** - 必需字段未提供时会返回错误提示

## 示例工作流

```
1. 插入公司：名称=深度思维，赛道=AI，描述=AGI研发
2. 插入信号：来源类型=新闻，来源ID=technews-001，赛道=AI，标题=融资公告，日期=2026-04-15，摘要=深度思维完成B轮...
3. 查询信号：赛道=AI，天数=7
4. 插入赛道排名：周起始=2026-04-13，赛道=AI，公司=深度思维，排名=1，理由=技术突破，来源信号=[...]
5. 创建IC会话：周起始=2026-04-13
6. 插入IC投票：会话ID=xxx，公司=深度思维，角色=技术，评分=90，论点=...
7. 插入周排名：周起始=2026-04-13，公司=深度思维，最终排名=1，最终分数=92...
```

## 安装依赖

```bash
pip install pymongo
# 或
pip install -r requirements.txt
```

requirements.txt:
```
pymongo>=4.0.0
```

## 技术细节

- 数据库：`sourcing_system`
- 主要集合：`signals`, `companies`, `sector_rankings`, `ic_sessions`, `ic_votes`, `weekly_rankings`, `manual_inputs`
- 连接池：全局单例，自动重连
- 序列化：`ObjectId` → `str`，`datetime` → ISO 8601

## 注意事项

1. 所有日期字段使用 `YYYY-MM-DD` 格式（信号日期）或 ISO 8601（时间戳）
2. `source_id` 和 `name` 组合作为 upsert 的唯一键，避免重复
3. 元数据字段（metadata）可传递任意 JSON 对象
4. 来源信号列表（source_signals）需为 JSON 数组，如 `["id1", "id2"]`

---

**这个 skill 已经准备好使用了。** 把它放到 `~/.openclaw/skills/mongodb/` 目录下，OpenClaw 会自动加载。需要我帮你创建目录结构并复制文件吗？或者你想先试用一下命令？

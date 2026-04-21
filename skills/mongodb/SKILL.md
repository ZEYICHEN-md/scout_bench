---
name: mongodb
description: 单一 MongoDB skill，支持 signals、companies 以及排名和投票等 collection。内部按 collection profile 分层，但外部仍然只需安装和使用这一个 skill。
version: 2.1.0
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

这是一个单一 MongoDB skill。

它内部对不同 collection 做了 profile 分层，但对外仍然只需要一个安装入口。当前支持：

- `signals`
- `companies`
- `sector_rankings`
- `ic_sessions`
- `ic_votes`
- `weekly_rankings`
- `manual_inputs`

## 连接配置

统一从环境变量读取连接信息：

```bash
export MONGODB_URI="mongodb://user:pass@host:port/db?authSource=admin"
```

## 支持的能力

### 信号

- 插入信号
- 按 `source_type + source_id` 查询信号
- 按赛道查询近期信号
- 按公司查询近期信号

### 公司

- 插入公司
- 查询公司
- 查询公司列表
- 更新公司状态

### 高级集合

- 赛道排名管理
- IC 会话和投票
- 周排名
- 手动输入日志

## API

脚本 API 包括：

- `insert_signal`
- `find_signal`
- `get_signals_by_sector`
- `get_signals_by_company`
- `insert_company`
- `get_company_by_name`
- `get_all_companies`
- `update_company_status`
- `insert_sector_ranking`
- `get_sector_rankings`
- `create_ic_session`
- `insert_ic_vote`
- `get_ic_votes`
- `insert_weekly_ranking`
- `get_weekly_rankings`
- `insert_manual_input`
- `get_manual_inputs`

其中 `signals` 和 `companies` 相关逻辑走内部 profile 和共享 CRUD，外部调用方式不变。

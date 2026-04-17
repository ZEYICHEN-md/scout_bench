# MongoDB Skill - 快速开始

## 安装

```bash
pip install -r requirements.txt
```

## 配置

连接 URI 已在代码中预配置（AliCloud MongoDB）。如需覆盖：

```bash
export MONGODB_URI="mongodb://user:pass@host:port/db?authSource=admin"
```

## 使用示例

### 1. 插入公司
```
插入公司：名称=未来智能，赛道=AI，描述=专注AGI研发
```

### 2. 插入信号
```
插入信号：来源类型=新闻，来源ID=technews-001，赛道=AI，标题=融资公告，摘要=未来智能完成B轮融资...
```

### 3. 查询某赛道的近期信号
```
查询信号：赛道=AI，天数=7，限制=50
```

### 4. 创建并提交 IC 投票
```
创建IC会话：周起始=2026-04-13
插入IC投票：会话ID=xxx，公司=未来智能，角色=技术，评分=85，论点=团队强，结论=同意
```

### 5. 生成周排名
```
插入周排名：周起始=2026-04-13，公司=未来智能，最终排名=1，最终分数=92，建议=重点投资，行动项=["尽调","打款"]
获取周排名：周起始=2026-04-13
```

## 集合结构

| 集合名 | 用途 | Upsert 键 |
|--------|------|-----------|
| `companies` | 公司基本信息 | name + sector |
| `signals` | 源头信号 | source_type + source_id |
| `sector_rankings` | 每周赛道内排名 | week_start + sector + rank |
| `ic_sessions` | IC 会议会话 | week_start（查重） |
| `ic_votes` | IC 投票记录 | 无（每次 insert） |
| `weekly_rankings` | 最终周排名 | week_start + company_name |
| `manual_inputs` | 手动输入日志 | 无（每次 insert） |

## 字段说明

### signal
- `source_type`: 新闻 | 研报 | 社交媒体 | 内部
- `source_id`: 唯一标识（需保证来源内不重复）
- `sector`: 赛道（如 AI、生物科技）
- `title`: 信号标题
- `summary`: 信号摘要
- `metadata`: {源链接、作者、标签...}

### company
- `name`: 公司名（同 sector 下唯一）
- `sector`: 赛道
- `description`: 简介
- `metadata`: {官网、阶段、位置...}

### ic_vote
- `session_id`: IC 会话 ID
- `company_name`: 公司名
- `role`: 角色（技术、业务、财务）
- `score`: 评分 0-100
- `argument`: 评分理由
- `verdict`: 结论（同意/反对/保留）
- `agent_name`: 投票代理名称（可选，默认 "unknown"）

### weekly_ranking
- `week_start`: 周一日期 YYYY-MM-DD
- `company_name`: 公司名
- `final_rank`: 最终排名
- `final_score`: 最终分数
- `recommendation`: 建议
- `action_items`: 行动项列表（MongoDB 原生数组）

## 调试

运行测试脚本：
```bash
python scripts/mongo_skill.py
```

查看连接和集合信息。

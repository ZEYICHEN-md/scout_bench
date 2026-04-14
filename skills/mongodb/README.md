# MongoDB Skill - 快速开始

## 安装

```bash
cd ~/.openclaw/workspace/skills/mongodb
pip install -r requirements.txt
```

## 配置

确保环境变量已设置（OpenClaw 会自动继承）：

```bash
export MONGODB_URI="mongodb://user:pass@host:port/db?authSource=admin"
```

或在 OpenClaw 配置中为这个 skill 单独设置 env。

## 使用示例

### 1. 插入公司
```
插入公司：名称=未来智能，赛道=AI，描述=专注AGI研发
```

### 2. 插入信号
```
插入信号：来源类型=新闻，来源ID=technews-001，赛道=AI，标题=融资公告，日期=2026-04-15，摘要=未来智能完成B轮融资...
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

| 集合名 | 用途 |
|--------|------|
| `companies` | 公司基本信息 |
| `signals` | 源头信号（upsert by source_type + source_id） |
| `sector_rankings` | 每周赛道内排名 |
| `ic_sessions` | IC 会议会话 |
| `ic_votes` | IC 投票记录 |
| `weekly_rankings` | 最终周排名 |
| `manual_inputs` | 手动输入日志 |

## 字段说明

### signal
- `source_type`: 新闻\|研报\|社交媒体\|内部
- `source_id`: 唯一标识（需保证来源内不重复）
- `sector`: 赛道（如 AI、生物科技）
- `signal_date`: YYYY-MM-DD
- `summary`: 信号摘要
- `metadata`: {源链接、作者、标签...}

### company
- `name`: 公司名（唯一，同 sector 下）
- `sector`: 赛道
- `description`: 简介
- `metadata`: {官网、阶段、位置...}

## 调试

运行测试脚本：
```bash
python scripts/mongo_skill.py
```

查看连接和集合信息。

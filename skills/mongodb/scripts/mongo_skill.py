"""
MongoDB Skill 工具函数 - 标准化数据插入和查询
对应 Skill: mongodb (SKILL.md)
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

try:
    from bson import ObjectId
    from pymongo import ASCENDING, DESCENDING, MongoClient

    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

# MongoDB 连接配置（从环境变量读取，Skill 中也可覆盖）
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://intern:wpLPXeCwYEBNb2Dr67Wy@dds-wz9ee8fe60b30e34-pub.mongodb.rds.aliyuncs.com:3717/sourcing_system?authSource=admin",
)
DATABASE_NAME = "sourcing_system"

# 全局连接
_client = None
_db = None


def _serialize_doc(doc: Dict) -> Dict:
    """将 MongoDB 文档转换为可序列化的字典，_id 转为 id"""
    if doc is None:
        return None
    result = {}
    for k, v in doc.items():
        if k == "_id":
            result["id"] = str(v)
        elif isinstance(v, ObjectId):
            result[k] = str(v)
        elif isinstance(v, datetime):
            result[k] = v.isoformat()
        else:
            result[k] = v
    if "id" not in result and "_id" not in doc:
        result["id"] = None
    return result


def get_db():
    """获取数据库连接（单例）"""
    global _client, _db
    if _db is not None:
        return _db

    if not MONGODB_AVAILABLE:
        raise RuntimeError("pymongo 未安装，请运行: pip install pymongo")

    _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    _db = _client[DATABASE_NAME]
    return _db


def get_collection(name: str):
    """获取集合"""
    db = get_db()
    return db[name]


# ========== Signal 操作 ==========

def insert_signal(
    source_type: str,
    source_id: str,
    sector: str,
    title: str,
    signal_date: str,
    summary: str = None,
    metadata: Dict = None,
) -> str:
    """
    插入或更新信号（upsert）
    返回：_id 字符串
    """
    col = get_collection("signals")
    doc = {
        "source_type": source_type,
        "source_id": source_id,
        "sector": sector,
        "title": title,
        "summary": summary,
        "signal_date": signal_date,
        "metadata": metadata or {},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    result = col.update_one(
        {"source_type": source_type, "source_id": source_id}, {"$set": doc}, upsert=True
    )
    # upsert 时，如果插入新文档，result.upserted_id 存在；如果是更新，matched_count > 0
    if result.upserted_id:
        return str(result.upserted_id)
    # 更新模式下，查询返回 _id
    existing = col.find_one({"source_type": source_type, "source_id": source_id})
    return str(existing["_id"]) if existing else None


def get_signals_by_company(company_name: str, limit: int = 20) -> List[Dict]:
    """获取某公司的所有信号（按日期降序）"""
    col = get_collection("signals")
    cursor = (
        col.find({"company_name": company_name})
        .sort([("signal_date", DESCENDING), ("created_at", DESCENDING)])
        .limit(limit)
    )
    return [_serialize_doc(doc) for doc in cursor]


def get_signals_by_sector(sector: str, days: int = 30, limit: int = 100) -> List[Dict]:
    """获取某赛道的近期信号（按日期降序）"""
    col = get_collection("signals")
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    cursor = (
        col.find({"sector": sector, "signal_date": {"$gte": cutoff_date}})
        .sort([("signal_date", DESCENDING), ("created_at", DESCENDING)])
        .limit(limit)
    )
    return [_serialize_doc(doc) for doc in cursor]


def find_signal(source_type: str, source_id: str) -> Optional[Dict]:
    """根据 source_type + source_id 精确查找信号"""
    col = get_collection("signals")
    doc = col.find_one({"source_type": source_type, "source_id": source_id})
    return _serialize_doc(doc)


# ========== Company 操作 ==========

def insert_company(
    name: str,
    sector: str,
    description: str = None,
    metadata: Dict = None,
) -> str:
    """
    插入或更新公司（upsert）
    返回：_id 字符串
    """
    col = get_collection("companies")
    doc = {
        "name": name,
        "sector": sector,
        "description": description,
        "metadata": metadata or {},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    result = col.update_one(
        {"name": name, "sector": sector}, {"$set": doc}, upsert=True
    )
    if result.upserted_id:
        return str(result.upserted_id)
    existing = col.find_one({"name": name, "sector": sector})
    return str(existing["_id"]) if existing else None


def get_company_by_name(name: str) -> Optional[Dict]:
    """根据公司名称查找（不区分 sector）"""
    col = get_collection("companies")
    doc = col.find_one({"name": name})
    return _serialize_doc(doc) if doc else None


def get_all_companies(sector: str = None, status: str = None) -> List[Dict]:
    """获取所有公司（可过滤赛道或状态）"""
    col = get_collection("companies")
    query = {}
    if sector:
        query["sector"] = sector
    if status:
        query["status"] = status
    cursor = col.find(query).sort("updated_at", DESCENDING)
    return [_serialize_doc(doc) for doc in cursor]


def update_company_status(name: str, status: str) -> bool:
    """更新公司状态（如：active, inactive, under_review）"""
    col = get_collection("companies")
    result = col.update_one(
        {"name": name}, {"$set": {"status": status, "updated_at": datetime.utcnow()}}
    )
    return result.modified_count > 0


# ========== Sector Ranking 赛道排名 ==========

def insert_sector_ranking(
    week_start: str,
    sector: str,
    company_name: str,
    rank: int,
    rationale: str,
    source_signals: List,
) -> None:
    """
    插入或更新赛道周排名（upsert）
    week_start: 周一日期 YYYY-MM-DD
    source_signals: 信号ID列表（可以是 str 或 List[str]）
    """
    col = get_collection("sector_rankings")

    # 确保 source_signals 是 JSON 字符串
    if isinstance(source_signals, list):
        source_signals = json.dumps(source_signals)

    col.update_one(
        {"week_start": week_start, "sector": sector, "rank": rank},
        {
            "$set": {
                "company_name": company_name,
                "rationale": rationale,
                "source_signals": source_signals,
                "updated_at": datetime.utcnow(),
            }
        },
        upsert=True,
    )


def get_sector_rankings(week_start: str, sector: str = None) -> List[Dict]:
    """
    获取某周（或某周某赛道）的排名
    返回：关联了公司信息的排名列表（按 sector, rank 排序）
    """
    col_sr = get_collection("sector_rankings")
    col_c = get_collection("companies")

    query = {"week_start": week_start}
    if sector:
        query["sector"] = sector

    sort_fields = (
        [("sector", ASCENDING), ("rank", ASCENDING)]
        if not sector
        else [("rank", ASCENDING)]
    )
    rankings = list(col_sr.find(query).sort(sort_fields))

    result = []
    for sr in rankings:
        cname = sr.get("company_name")
        company = col_c.find_one({"name": cname}) if cname else None
        doc = _serialize_doc(sr)
        if company:
            doc["company_description"] = company.get("description")
            doc["company_sector"] = company.get("sector")
        result.append(doc)

    return result


# ========== IC Session & Votes 投资委员会 ==========

def create_ic_session(week_start: str) -> str:
    """创建 IC 会话（如果已存在则返回现有 ID）"""
    col = get_collection("ic_sessions")
    existing = col.find_one({"week_start": week_start})
    if existing:
        return str(existing["_id"])
    result = col.insert_one(
        {
            "week_start": week_start,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }
    )
    return str(result.inserted_id)


def insert_ic_vote(
    session_id: str,
    company_name: str,
    role: str,
    agent_name: str,
    score: int,
    argument: str,
    verdict: str,
) -> str:
    """
    插入 IC 投票
    verdict: 建议结果，如 "同意"、"反对"、"保留"
    """
    col = get_collection("ic_votes")

    # 获取 company_id
    company = get_company_by_name(company_name)
    company_id = company.get("id") if company else None

    result = col.insert_one(
        {
            "session_id": session_id,
            "company_id": company_id,
            "company_name": company_name,
            "role": role,
            "agent_name": agent_name,
            "score": score,
            "argument": argument,
            "verdict": verdict,
            "created_at": datetime.now().isoformat(),
        }
    )
    return str(result.inserted_id)


def get_ic_votes(session_id: str, company_name: str = None) -> List[Dict]:
    """获取 IC 投票记录"""
    col = get_collection("ic_votes")
    query = {"session_id": session_id}
    if company_name:
        query["company_name"] = company_name
    cursor = col.find(query).sort("created_at", ASCENDING)
    return [_serialize_doc(doc) for doc in cursor]


# ========== Weekly Ranking 最终周排名 ==========

def insert_weekly_ranking(
    week_start: str,
    company_name: str,
    final_rank: int,
    final_score: int,
    recommendation: str,
    action_items: List[str],
) -> None:
    """插入或更新最终周排名（upsert）"""
    col = get_collection("weekly_rankings")

    # 获取 company_id
    company = get_company_by_name(company_name)
    company_id = company.get("id") if company else None

    col.update_one(
        {"week_start": week_start, "company_name": company_name},
        {
            "$set": {
                "company_id": company_id,
                "final_rank": final_rank,
                "final_score": final_score,
                "recommendation": recommendation,
                "action_items": json.dumps(action_items) if isinstance(action_items, list) else action_items,
                "updated_at": datetime.utcnow(),
            }
        },
        upsert=True,
    )


def get_weekly_rankings(week_start: str) -> List[Dict]:
    """
    获取某周的最终排名列表（已关联公司信息，按 rank 排序）
    用于周报输出
    """
    col_wr = get_collection("weekly_rankings")
    col_c = get_collection("companies")

    rankings = list(col_wr.find({"week_start": week_start}).sort("final_rank", ASCENDING))

    result = []
    for wr in rankings:
        cname = wr.get("company_name")
        company = col_c.find_one({"name": cname}) if cname else None
        doc = _serialize_doc(wr)
        if company:
            doc["company_description"] = company.get("description")
            doc["company_sector"] = company.get("sector")
        result.append(doc)

    return result


# ========== Manual Input 手动输入 ==========

def insert_manual_input(
    input_type: str,
    content: Dict,
    created_by: str = "user",
) -> str:
    """
    插入手动输入记录
    input_type: "signal_override" | "company_note" | "ranking_adjustment" | "general"
    """
    col = get_collection("manual_inputs")

    result = col.insert_one(
        {
            "input_type": input_type,
            "content": json.dumps(content) if isinstance(content, dict) else content,
            "created_by": created_by,
            "created_at": datetime.now().isoformat(),
        }
    )
    return str(result.inserted_id)


def get_manual_inputs(input_type: str = None, limit: int = 50) -> List[Dict]:
    """获取手动输入记录"""
    col = get_collection("manual_inputs")
    query = {}
    if input_type:
        query["input_type"] = input_type
    cursor = col.find(query).sort("created_at", DESCENDING).limit(limit)
    return [_serialize_doc(doc) for doc in cursor]


# ========== 统计 ==========

def count_signals(sector: str = None, days: int = None) -> int:
    """统计信号数量"""
    col = get_collection("signals")
    query = {}
    if sector:
        query["sector"] = sector
    if days:
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        query["signal_date"] = {"$gte": cutoff}
    return col.count_documents(query)


def count_companies(sector: str = None) -> int:
    """统计公司数量"""
    col = get_collection("companies")
    query = {}
    if sector:
        query["sector"] = sector
    return col.count_documents(query)


# ========== 测试 ==========

if __name__ == "__main__":
    print("MongoDB Skill 工具函数测试")
    print(f"默认 URI: {MONGODB_URI}")
    print(f"pymongo 可用: {MONGODB_AVAILABLE}")

    try:
        db = get_db()
        print(f"已连接数据库: {db.name}")
        print(f"集合列表: {db.list_collection_names()}")
    except Exception as e:
        print(f"连接失败: {e}")

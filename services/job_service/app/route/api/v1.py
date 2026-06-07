from fastapi import APIRouter, status, HTTPException
from typing import List, Dict, Tuple
from uuid import UUID
from pydantic import BaseModel
import json

from crud import history_crud, jobs_crud
from schema import RecommendResponse, JobDetailResponse
from models.HistoryTable import HistoryTableSchema
from core.db import session as db_session
from sqlalchemy import text

router = APIRouter()

# ============================================================
# DB永続化ヘルパー（dreamer_profiles テーブル）
# ============================================================

def _save_profile(dreamer_id: str, job_scores: List[Tuple[int, float]]):
    """analyze結果をDBに保存（upsert）"""
    data = json.dumps([[jid, score] for jid, score in job_scores])
    db_session.execute(text("""
        INSERT INTO dreamer_profiles (dreamer_id, job_scores, updated_at)
        VALUES (:did, CAST(:data AS jsonb), NOW())
        ON CONFLICT (dreamer_id)
        DO UPDATE SET job_scores = CAST(:data AS jsonb), updated_at = NOW()
    """), {"did": dreamer_id, "data": data})
    db_session.commit()


def _load_profile(dreamer_id: str) -> List[Tuple[int, float]]:
    """DBからanalyze結果を読み込む"""
    row = db_session.execute(text(
        "SELECT job_scores FROM dreamer_profiles WHERE dreamer_id = :did"
    ), {"did": dreamer_id}).fetchone()
    if row is None:
        return []
    return [(int(item[0]), float(item[1])) for item in row[0]]


def _pop_next(dreamer_id: str) -> Tuple[int, float] | None:
    """先頭を取り出してDBを更新"""
    scores = _load_profile(dreamer_id)
    if not scores:
        return None
    head = scores[0]
    rest = scores[1:]
    _save_profile(dreamer_id, rest)
    return head


# ============================================================
# ベクトルDB（遅延初期化）
# ============================================================

_vector_db = None

def _get_vector_db():
    global _vector_db
    if _vector_db is None:
        try:
            from job_suggest import JobVectorDB
            _vector_db = JobVectorDB()
            print("[VectorDB] 初期化完了")
        except Exception as e:
            print(f"[VectorDB] 初期化失敗: {e}")
    return _vector_db


def _all_jobs_name_map():
    try:
        db_session.expire_all()  # 長時間処理後のセッション失効を防ぐ
    except Exception:
        pass
    _, all_jobs, _ = jobs_crud.read([])
    if not all_jobs:
        return {}
    return {(getattr(j, "name", "") or "").strip(): getattr(j, "job_id", 0)
            for j in all_jobs}


def _chroma_search_by_text(query_text: str) -> List[Tuple[int, float]]:
    vector_db = _get_vector_db()
    if vector_db is None:
        return []

    results = vector_db.search(query_text)
    if not results["ids"] or not results["ids"][0]:
        return []

    name_map = _all_jobs_name_map()
    n = len(results["ids"][0])
    ordered: List[Tuple[int, float]] = []
    seen_ids = set()

    for i in range(n):
        name = results["metadatas"][0][i].get("name", "")
        score = round(95 - (45 * i / max(n - 1, 1)), 1)
        jid = name_map.get(name.strip())
        if jid and jid not in seen_ids:
            ordered.append((jid, score))
            seen_ids.add(jid)

    # ChromaDBにない job をスコア0で末尾に
    _, all_jobs, _ = jobs_crud.read([])
    for j in all_jobs:
        jid = getattr(j, "job_id", 0)
        if jid not in seen_ids:
            ordered.append((jid, 0.0))
            seen_ids.add(jid)

    return ordered


def _reorder_by_feedback(dreamer_id: str, job_id: int, boost: bool):
    vector_db = _get_vector_db()
    scores = _load_profile(dreamer_id)
    if not vector_db or not scores:
        return

    _, jobs, _ = jobs_crud.read([["job_id", "==", job_id]])
    if not jobs:
        return
    job = jobs[0]
    job_name = (getattr(job, "name", "") or "").strip()
    job_desc = (getattr(job, "description", "") or "").strip()

    results = vector_db.search(f"{job_name} {job_desc}")
    if not results["ids"] or not results["ids"][0]:
        return

    name_map = _all_jobs_name_map()
    similar_ids: set = set()
    for i in range(len(results["ids"][0])):
        name = (results["metadatas"][0][i].get("name", "") or "").strip()
        jid = name_map.get(name)
        if jid and jid != job_id:
            similar_ids.add(jid)

    similar = [(jid, s) for jid, s in scores if jid in similar_ids]
    rest    = [(jid, s) for jid, s in scores if jid not in similar_ids]

    new_scores = (similar + rest) if boost else (rest + similar)
    _save_profile(dreamer_id, new_scores)
    print(f"[Feedback] dreamer={dreamer_id} {'boost' if boost else 'demote'} "
          f"job_id={job_id} 対象={len(similar_ids)}件")


# ============================================================
# analyze
# ============================================================

class AnswerItem(BaseModel):
    category: str
    q: str
    a: str

class AnalyzeRequest(BaseModel):
    dreamer_id: str
    answers: List[AnswerItem]


@router.post("/analyze")
async def analyze_answers(request: AnalyzeRequest):
    import os
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if not openai_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY が設定されていません")

    vector_db = _get_vector_db()
    if vector_db is None:
        raise HTTPException(status_code=500, detail="ベクトル検索エンジンの初期化に失敗しました")

    answers_for_suggest = [
        {"category": a.category, "q": a.q, "a": a.a}
        for a in request.answers
    ]

    profile_text = vector_db.agent.synthesize_user_query(answers_for_suggest)
    print(f"[Analyze] プロファイル: {profile_text[:80]}...")

    ordered = _chroma_search_by_text(profile_text)
    if not ordered:
        raise HTTPException(status_code=500, detail="ベクトル検索結果が0件です")

    _save_profile(request.dreamer_id, ordered)
    matched = len([x for x in ordered if x[1] > 0])
    print(f"[Analyze] DB保存: dreamer={request.dreamer_id} マッチ={matched}件")

    return {"status": "ok", "matched": matched}


# ============================================================
# recommend
# ============================================================

@router.get("/recommend/{dreamer_id}")
async def recommend(dreamer_id: UUID):
    import random

    next_item = _pop_next(str(dreamer_id))

    if next_item:
        job_id, similarity_score = next_item
        _, jobs, _ = jobs_crud.read([["job_id", "==", job_id]])
        if not jobs:
            _, jobs, _ = jobs_crud.read([])
        job = jobs[0] if jobs else None
    else:
        similarity_score = 0.0
        _, jobs, _ = jobs_crud.read([])
        job = random.choice(jobs) if jobs else None

    if not job:
        raise HTTPException(status_code=404, detail="jobデータがありません")

    job_id = getattr(job, "job_id", 0)

    _, new_hist, _ = history_crud.create(HistoryTableSchema(
        job_id=job_id,
        dreamer_id=str(dreamer_id),
    ))
    if not new_hist:
        raise HTTPException(status_code=500, detail="history作成に失敗")

    return {
        "recommendation": {
            "job_id": job_id,
            "history_id": str(new_hist.history_id),
            "name": getattr(job, "name", "") or "",
            "imgs": getattr(job, "imgs", []) or [],
            "salary": int(getattr(job, "salary", 0) or 0),
            "level": int(getattr(job, "level", 0) or 0),
            "age": int(getattr(job, "age", 0) or 0),
            "description": getattr(job, "description", "") or "",
            "similarity_score": similarity_score,
        }
    }


# ============================================================
# good / bad / save
# ============================================================

@router.put("/good/{history_id}", status_code=status.HTTP_200_OK)
async def mark_good(history_id: UUID):
    _, updated_list, _ = history_crud.update(
        [["history_id", "==", history_id]],
        {"good": True}
    )
    if not updated_list:
        raise HTTPException(status_code=404, detail="history が見つかりません")

    hist = updated_list[0]
    dreamer_id = str(getattr(hist, "dreamer_id", ""))
    job_id = int(getattr(hist, "job_id", 0))
    if dreamer_id and job_id:
        _reorder_by_feedback(dreamer_id, job_id, boost=True)

    return {"status": "ok"}


@router.put("/bad/{history_id}", status_code=status.HTTP_200_OK)
async def mark_bad(history_id: UUID):
    _, updated_list, _ = history_crud.update(
        [["history_id", "==", history_id]],
        {"bad": True}
    )
    if not updated_list:
        raise HTTPException(status_code=404, detail="history が見つかりません")

    hist = updated_list[0]
    dreamer_id = str(getattr(hist, "dreamer_id", ""))
    job_id = int(getattr(hist, "job_id", 0))
    if dreamer_id and job_id:
        _reorder_by_feedback(dreamer_id, job_id, boost=False)

    return {"status": "ok"}


@router.put("/save/{history_id}", status_code=status.HTTP_200_OK)
async def mark_save(history_id: UUID):
    history_crud.update(
        [["history_id", "==", history_id]],
        {"save": True}
    )
    return {"status": "ok"}


# ============================================================
# detail
# ============================================================

@router.get("/detail/{job_id}", response_model=JobDetailResponse)
async def get_detail(job_id: int):
    _, jobs, _ = jobs_crud.read([["job_id", "==", job_id]])
    if not jobs:
        raise HTTPException(status_code=404, detail="job が見つかりません")

    job = jobs[0]
    payload = {
        "job_id": getattr(job, "job_id", 0),
        "name": getattr(job, "name", "") or "",
        "description": getattr(job, "description", "") or "",
        "imgs": getattr(job, "imgs", []) or [],
        "salary": int(getattr(job, "salary", 0) or 0),
        "level": int(getattr(job, "level", 0) or 0),
        "end_time": getattr(job, "end_time", "") or "",
        "holiday": int(getattr(job, "holiday", 0) or 0),
        "overtime_hours": int(getattr(job, "overtime_hours", 0) or 0),
        "age": int(getattr(job, "age", 0) or 0),
        "tenure_years": int(getattr(job, "tenure_years", 0) or 0),
        "marriage_age": int(getattr(job, "marriage_age", 0) or 0),
        "gender_ratio": float(getattr(job, "gender_ratio", 0.0) or 0.0),
        "romance_rate": float(getattr(job, "romance_rate", 0.0) or 0.0),
        "social_signification": getattr(job, "social_signification", "") or "",
        "personality_traits": getattr(job, "personality_traits", "") or "",
        "growth_opportunities": getattr(job, "growth_opportunities", "") or "",
        "wrong_image": getattr(job, "wrong_image", "") or "",
        "uniform": bool(getattr(job, "uniform", False) or False),
        "work_life_balance": float(getattr(job, "work_life_balance", 0.0) or 0.0),
        "future_outlook": getattr(job, "future_outlook", "") or "",
        "rarity": float(getattr(job, "rarity", 0.0) or 0.0),
        "scandal_history": getattr(job, "scandal_history", "") or "",
        "focus_on_education": bool(getattr(job, "focus_on_education", False) or False),
        "focus_on_achievements": bool(getattr(job, "focus_on_achievements", False) or False),
        "appeal_points": getattr(job, "appeal_points", "") or "",
        "daily_routine": getattr(job, "daily_routine", "") or "",
        "comments": getattr(job, "comments", "") or "",
        "skills": getattr(job, "skills", []) or [],
        "certifications": getattr(job, "certifications", []) or [],
        "companies": getattr(job, "companies", []) or [],
        "talents": getattr(job, "talents", []) or [],
        "interests": getattr(job, "interests", []) or [],
    }
    return JobDetailResponse.model_validate(payload)

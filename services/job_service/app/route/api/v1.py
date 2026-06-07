from fastapi import APIRouter, status, HTTPException
from typing import List, Dict, Tuple
from uuid import UUID
from pydantic import BaseModel

from crud import history_crud, jobs_crud
from schema import RecommendResponse, JobDetailResponse
from models.HistoryTable import HistoryTableSchema

router = APIRouter()

# ============================================================
# キャッシュ
# dreamer_id(str) -> [(job_id, similarity_score), ...]
# スコア順に並んでいて、recommend のたびに先頭から消費する
# ============================================================
_recommend_cache: Dict[str, List[Tuple[int, float]]] = {}

# ベクトルDB（遅延初期化）
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
    """job_name -> job_id の辞書を返す"""
    _, all_jobs, _ = jobs_crud.read([])
    return {(getattr(j, "name", "") or "").strip(): getattr(j, "job_id", 0)
            for j in all_jobs}


def _chroma_search_by_text(query_text: str) -> List[Tuple[int, float]]:
    """
    テキストでChromaDB検索 → [(job_id, score), ...] を返す
    マッチしない jobはDB全件をスコア0で末尾に付加
    """
    vector_db = _get_vector_db()
    if vector_db is None:
        return []

    results = vector_db.search(query_text)
    if not results["ids"] or not results["ids"][0]:
        return []

    name_map = _all_jobs_name_map()

    ordered: List[Tuple[int, float]] = []
    # L2距離: 小さいほど類似。相対スコアで 1位=95%, n位=50% に正規化
    n = len(results["ids"][0])
    seen_ids = set()
    for i in range(len(results["ids"][0])):
        name = results["metadatas"][0][i].get("name", "")
        score = round(95 - (45 * i / max(n - 1, 1)), 1)  # 95% → 50%
        jid = name_map.get(name.strip())
        if jid and jid not in seen_ids:
            ordered.append((jid, score))
            seen_ids.add(jid)

    # ChromaDBにないジョブをスコア0で末尾に追加（フォールバック）
    _, all_jobs, _ = jobs_crud.read([])
    for j in all_jobs:
        jid = getattr(j, "job_id", 0)
        if jid not in seen_ids:
            ordered.append((jid, 0.0))
            seen_ids.add(jid)

    return ordered


def _reorder_cache(dreamer_id: str, job_id: int, boost: bool):
    """
    good(boost=True)  → 類似jobをキャッシュ先頭へ
    bad (boost=False) → 類似jobをキャッシュ末尾へ
    """
    vector_db = _get_vector_db()
    cache_key = str(dreamer_id)
    if vector_db is None or cache_key not in _recommend_cache:
        return

    # 対象jobの名前・説明を取得してベクトル検索
    _, jobs, _ = jobs_crud.read([["job_id", "==", job_id]])
    if not jobs:
        return
    job = jobs[0]
    job_name = (getattr(job, "name", "") or "").strip()
    job_desc = (getattr(job, "description", "") or "").strip()
    query = f"{job_name} {job_desc}"

    results = vector_db.search(query)
    if not results["ids"] or not results["ids"][0]:
        return

    name_map = _all_jobs_name_map()
    similar_ids: set = set()
    for i in range(len(results["ids"][0])):
        name = (results["metadatas"][0][i].get("name", "") or "").strip()
        jid = name_map.get(name)
        if jid and jid != job_id:
            similar_ids.add(jid)

    current = _recommend_cache[cache_key]
    similar_items = [(jid, s) for jid, s in current if jid in similar_ids]
    rest_items    = [(jid, s) for jid, s in current if jid not in similar_ids]

    if boost:
        _recommend_cache[cache_key] = similar_items + rest_items
    else:
        _recommend_cache[cache_key] = rest_items + similar_items

    print(f"[Cache] dreamer={dreamer_id} {'boost' if boost else 'demote'} job_id={job_id} "
          f"対象={len(similar_ids)}件")


# ============================================================
# analyze  ─ init-answers から呼ばれる
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
    """回答をベクトル検索で分析し job_id リストをキャッシュに保存"""
    import os
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if not openai_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY が設定されていません")

    vector_db = _get_vector_db()
    if vector_db is None:
        raise HTTPException(status_code=500, detail="ベクトル検索エンジンの初期化に失敗しました")

    # 1. 回答リストを job_suggest の形式に変換
    answers_for_suggest = [
        {"category": a.category, "q": a.q, "a": a.a}
        for a in request.answers
    ]

    # 2. OpenAI でユーザープロファイル生成
    profile_text = vector_db.agent.synthesize_user_query(answers_for_suggest)
    print(f"[Analyze] プロファイル: {profile_text[:80]}...")

    # 3. ChromaDB でベクトル検索 → スコア順 job リスト
    ordered = _chroma_search_by_text(profile_text)
    if not ordered:
        raise HTTPException(status_code=500, detail="ベクトル検索結果が0件です")

    _recommend_cache[request.dreamer_id] = ordered
    matched = len([x for x in ordered if x[1] > 0])
    print(f"[Analyze] キャッシュ保存: dreamer={request.dreamer_id} "
          f"ベクトルマッチ={matched}件 / 全{len(ordered)}件")

    return {"status": "ok", "matched": matched}


# ============================================================
# recommend ─ スコア順に1件ずつ返す
# ============================================================

@router.get("/recommend/{dreamer_id}")
async def recommend(dreamer_id: UUID):
    """スコア順上位のジョブを1件返す"""
    import random

    cache_key = str(dreamer_id)
    cached = _recommend_cache.get(cache_key)

    if cached:
        job_id, similarity_score = cached[0]
        _recommend_cache[cache_key] = cached[1:]
        _, jobs, _ = jobs_crud.read([["job_id", "==", job_id]])
        if not jobs:
            _, jobs, _ = jobs_crud.read([])
    else:
        similarity_score = 0.0
        _, jobs, _ = jobs_crud.read([])

    if not jobs:
        raise HTTPException(status_code=404, detail="jobデータがありません")

    job = jobs[0] if cached else random.choice(jobs)
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
    """いいね登録 → 類似ジョブをキャッシュ先頭へ"""
    _, updated_list, error = history_crud.update(
        [["history_id", "==", history_id]],
        {"good": True}
    )
    if not updated_list:
        raise HTTPException(status_code=404, detail="history が見つかりません")

    hist = updated_list[0]
    dreamer_id = str(getattr(hist, "dreamer_id", ""))
    job_id = int(getattr(hist, "job_id", 0))

    if dreamer_id and job_id:
        _reorder_cache(dreamer_id, job_id, boost=True)

    return {"status": "ok"}


@router.put("/bad/{history_id}", status_code=status.HTTP_200_OK)
async def mark_bad(history_id: UUID):
    """バッド登録 → 類似ジョブをキャッシュ末尾へ"""
    _, updated_list, error = history_crud.update(
        [["history_id", "==", history_id]],
        {"bad": True}
    )
    if not updated_list:
        raise HTTPException(status_code=404, detail="history が見つかりません")

    hist = updated_list[0]
    dreamer_id = str(getattr(hist, "dreamer_id", ""))
    job_id = int(getattr(hist, "job_id", 0))

    if dreamer_id and job_id:
        _reorder_cache(dreamer_id, job_id, boost=False)

    return {"status": "ok"}


@router.put("/save/{history_id}", status_code=status.HTTP_200_OK)
async def mark_save(history_id: UUID):
    """保存登録"""
    _, updated_list, error = history_crud.update(
        [["history_id", "==", history_id]],
        {"save": True}
    )
    return {"status": "ok"}


# ============================================================
# detail
# ============================================================

@router.get("/detail/{job_id}", response_model=JobDetailResponse)
async def get_detail(job_id: int):
    _, jobs, error = jobs_crud.read([["job_id", "==", job_id]])
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

from fastapi import APIRouter, Depends, status, HTTPException
from typing import List, Any, Dict
from uuid import UUID
from pydantic import BaseModel

from crud import history_crud, jobs_crud
from schema import RecommendResponse, JobDetailResponse
from models.HistoryTable import HistoryTableSchema

# /api/v1/job
router = APIRouter()


# ================
# analyze (init-answers から呼ばれる)
# ================

class AnswerItem(BaseModel):
    category: str
    q: str
    a: str

class AnalyzeRequest(BaseModel):
    dreamer_id: str
    answers: List[AnswerItem]

# dreamer_id -> job_ids のキャッシュ（プロセス内メモリ）
_recommend_cache: Dict[str, List[int]] = {}

@router.post("/analyze")
async def analyze_answers(request: AnalyzeRequest):
    """回答を分析して job_id リストをキャッシュに保存"""
    import os
    from openai import OpenAI

    openai_key = os.getenv("OPENAI_API_KEY", "")
    if not openai_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY が設定されていません")

    # 回答テキストを整形
    log_text = "\n".join([
        f"[{a.category}] Q: {a.q}\nA: {a.a}" for a in request.answers
    ])

    client = OpenAI(api_key=openai_key)

    # OpenAI でプロファイルを生成
    profile_prompt = f"""
あなたは「職業データ翻訳家」です。
ユーザーのインタビュー回答をもとに、この人物が理想とする職業の「検索用記述データ」を作成してください。

【インタビュー回答】
{log_text}

【出力フォーマット（この構文を厳守）】
- 思考スタイル: [特徴を簡潔に]
- コミュニケーション: [特徴を簡潔に]
- 行動特性: [特徴を簡潔に]
- 環境の好み: [特徴を簡潔に]
- 価値観: [特徴を簡潔に]
- 向いている職業タイプ: [職業の特徴を200字程度で]
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": profile_prompt}],
        temperature=0.3,
    )
    profile_text = resp.choices[0].message.content or ""

    # job DB から全件取得してキーワードマッチで上位 10 件を選ぶ（簡易版）
    _, all_jobs, _ = jobs_crud.read([])
    if not all_jobs:
        raise HTTPException(status_code=500, detail="job データが0件です")

    # profile_text に job 名が含まれているかでスコアリング（簡易）
    scored = []
    for job in all_jobs:
        name = getattr(job, "name", "") or ""
        desc = getattr(job, "description", "") or ""
        score = 0
        for word in (name + " " + desc).split():
            if word in profile_text:
                score += 1
        scored.append((score, getattr(job, "job_id", 0)))

    scored.sort(reverse=True)
    top_job_ids = [job_id for _, job_id in scored[:10]]

    _recommend_cache[request.dreamer_id] = top_job_ids
    return {"status": "ok", "job_ids": top_job_ids}

@router.get("/detail/{job_id}", response_model=JobDetailResponse)
async def _(job_id: int):
    """job情報の取得"""

    _, jobs, error = jobs_crud.read([
        ["job_id", "==", job_id]
    ])


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

@router.put("/good/{history_id}", status_code=status.HTTP_200_OK)
async def _(history_id: UUID):
    """ジョブに対する「いいね」登録（履歴の更新）"""
    _, updated, error = history_crud.update(
        [["history_id", "==", history_id]],
        {"good": True}
    )

    return status.HTTP_200_OK

@router.put("/bad/{history_id}", status_code=status.HTTP_200_OK)
async def _(history_id: UUID):
    """ジョブに対する「バッド」登録（履歴の更新）"""
    _, updated, error = history_crud.update(
        [["history_id", "==", history_id]],
        {"bad": True}
    )
    return status.HTTP_200_OK

@router.put("/save/{history_id}", status_code=status.HTTP_200_OK)
async def _(history_id: UUID):
    """ジョブに対する「保存」登録（履歴の更新）"""
    _, updated, error = history_crud.update(
        [["history_id", "==", history_id]],
        {"save": True}
    )
    return {"message": "保存登録が完了しました"}


@router.get("/recommend/{dreamer_id}")
async def _(dreamer_id: UUID):
    """Dreamerにおすすめの職業を1件返す"""
    import random

    job_ids = _recommend_cache.get(str(dreamer_id))
    if job_ids:
        job_id = random.choice(job_ids)
        _, jobs, _ = jobs_crud.read([["job_id", "==", job_id]])
    else:
        _, jobs, _ = jobs_crud.read([])

    if not jobs:
        raise HTTPException(status_code=404, detail="jobデータがありません")

    job = random.choice(jobs)
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
            "similarity_score": 0.0,
        }
    }

import os
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
from dotenv import load_dotenv

# --- 設定 ---
load_dotenv("services\job_service\.job_env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print(OPENAI_API_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)
GENERATION_MODEL_NAME = "gpt-4o-mini"
LOCAL_EMBEDDING_MODEL = "sonoisa/sentence-bert-base-ja-mean-tokens"
PERSIST_DIRECTORY = "./chroma_db"

app = FastAPI(title="Job Matching API", description="30の質問から職業をマッチングするAPI")

# CORSの設定 (フロントエンドから接続する場合に必要)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- データモデルの定義 ---
class Answer(BaseModel):
    category: str
    q: str
    a: str

class InterviewRequest(BaseModel):
    log: List[Answer]

# --- 内部ロジッククラス ---
class RecommenderService:
    def __init__(self):
        # 起動時に一度だけモデルをロード
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=LOCAL_EMBEDDING_MODEL
        )
        self.chroma_client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
        self.collection = self.chroma_client.get_or_create_collection(
            name="openai_precision_matching",
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"}
        )

    def synthesize_profile(self, interview_log: List[Answer]):
        log_text = "\n".join([f"[{item.category}] Q: {item.q}\nA: {item.a}" for item in interview_log])
        
        prompt = f"""
        あなたは「職業データ翻訳家」です。
        ユーザーのインタビュー回答をもとに、この人物が理想とする職業の「検索用記述データ」を作成してください。
        
        【出力フォーマット（この構文を厳守）】
        この仕事は、[具体的な操作対象]を操作・扱い、[主な目的]を達成することに特化しています。
        具体的には、[具体的な業務内容]を行います。
        成果を出すためには、[得意なツールやスキル]を駆使し、[求める成果物]を生み出すことが求められます。
        思考タイプとしては、[ユーザーの思考の癖]が必要とされ、
        環境としては、[理想の環境]で、[対人距離感]を持って働くことが適しています。

        【ユーザーの回答データ】
        {log_text}
        """

        response = client.chat.completions.create(
            model=GENERATION_MODEL_NAME,
            messages=[
                {"role": "system", "content": "あなたは洞察力の鋭いプロファイリングAIです。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()

    def search_jobs(self, query_text: str):
        results = self.collection.query(query_texts=[query_text], n_results=100)
        
        formatted_results = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "rank": i + 1,
                    "name": results['metadatas'][0][i]['name'],
                    "score": round((1 - results['distances'][0][i]) * 100, 1),
                    "analysis": results['metadatas'][0][i]['analysis']
                })
        return formatted_results

# サービスのインスタンス化
service = RecommenderService()

# --- エンドポイント ---

@app.get("/questions")
def get_questions():
    """フロントエンドに質問リストを返すエンドポイント"""
    # 既存の DetailedInterview クラスの categories データをそのまま返します
    from main_logic import DetailedInterview
    interview = DetailedInterview()
    return interview.categories

@app.post("/analyze")
async def analyze_and_search(request: InterviewRequest):
    """回答ログを受け取り、プロフィール生成と検索を実行する"""
    try:
        # 1. 回答からプロファイルを生成 (OpenAI)
        profile_text = service.synthesize_profile(request.log)
        
        # 2. ベクトルDBで検索 (ChromaDB)
        jobs = service.search_jobs(profile_text)
        
        return {
            "status": "success",
            "user_profile": profile_text,
            "recommendations": jobs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# サーバー起動コマンド: uvicorn main:app --reload
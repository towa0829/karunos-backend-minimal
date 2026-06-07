-- dreamerのanalyze結果（job_idとscoreのリスト）を永続化するテーブル
CREATE TABLE IF NOT EXISTS dreamer_profiles (
    dreamer_id UUID PRIMARY KEY,
    job_scores JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

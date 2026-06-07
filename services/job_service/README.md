# Job Service

[システム設計](https://www.notion.so/Karynos-backend-module-1b39a9038f388050816afe733aa3cdfc?source=copy_link#2899a9038f38808aa984c1d67ac464fe)

| **項目** | **内容** |
|-----------|-----------|
| **サービス名** | job_service |
| **主な責務** | ・Job Matching<br>・Job パラメータ表示<br>・Job ストレージ<br>・Job Suggestion |
| **通信方法** | API |
| **ルート** | `job/` |
| **構成コンテナ** | APIサーバー（job_service）<br>DBサーバー（job-db） |
| **実装言語** | Python |

## フォルダ構成

```
│  .job_env                                   // 環境変数
│  Dockerfile                                
│  README.md
│  requirements.txt                           // Pythonライブラリ一覧 
│
├─app
│  │  crud.py                                 // DB操作関係
│  │  main.py                                 // 実行不ファイル
│  │　schemas.py                              // 型定義ファイル
│  │
│  ├─core                                      
│  │  │  config.py                            // 設定ファイル
│  │  │  db.py                                // DB接続関係
│  │
│  ├─models　　　　　　　　　　　　　　　　　　　 // DBテーブル関係
│  │ │   base.py                              
│  │
│  ├─route
│  │  │  main_router.py                       // ルートルーティング
│  │  │
│  │  ├─api
│  │  │  │  v1.py                             // APIルーティング
│  │  │
│  │  ├─ws
│  │     │  v1.py                             // WebSocketルーティング
│  │
│  └─shared
│
└─db
   │  init.sql                                 // DB初回実行ファイル
```

## テスト設計
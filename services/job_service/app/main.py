from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from route.main_router import router as main_router
from core.config import settings

app = FastAPI(
    title = settings.SERVICE_NAME,
    root_path = settings.PREFIX
)

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
]

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],       
    allow_headers=["*"],       
)

app.include_router(main_router)
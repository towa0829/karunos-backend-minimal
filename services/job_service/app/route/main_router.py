from fastapi import APIRouter

from route.api.v1 import router as http_router
from route.ws.v1 import router as ws_router

from core.config import settings

VERSION_PREFIX = "/v1"

router = APIRouter()
router.include_router(http_router, prefix=f"/api{VERSION_PREFIX}", tags=[settings.TAG])
router.include_router(ws_router, prefix=f"/ws{VERSION_PREFIX}",  tags=[settings.TAG])
from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.api.insights import router as insight_router

app = FastAPI()
app.include_router(chat_router)
app.include_router(insight_router)

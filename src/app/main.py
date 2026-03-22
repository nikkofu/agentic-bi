import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.insights import router as insight_router
from app.api.reports import router as reports_router
from app.api.reporting import router as reporting_router

app = FastAPI()
dev_viewer_origins = [
    origin.strip()
    for origin in os.getenv(
        "AGENTIC_BI_DEV_VIEWER_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:4173,http://localhost:4173",
    ).split(",")
    if origin.strip()
]
if dev_viewer_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=dev_viewer_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
app.include_router(chat_router)
app.include_router(insight_router)
app.include_router(reports_router)
app.include_router(reporting_router)

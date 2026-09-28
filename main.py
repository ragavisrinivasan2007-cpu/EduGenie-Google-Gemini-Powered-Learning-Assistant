from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.models import (
    ExplanationRequest,
    LearningRecommendationResponse,
    QuizRequest,
    QuizResponse,
    SummaryRequest,
)
from backend.services.gemini_service import GeminiService

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"

app = FastAPI(
    title="EduGenie",
    version="1.0.0",
    description="Google Gemini powered learning assistant.",
)

origins = [
    item.strip()
    for item in os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000",
    ).split(",")
    if item.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

gemini = GeminiService()

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def home() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "EduGenie",
        "gemini_configured": gemini.configured,
        "demo_mode": gemini.demo_mode,
        "model": gemini.model_name,
    }


@app.get("/qna")
async def qna(
    question: str = Query(..., min_length=1, max_length=4000)
) -> dict[str, str]:
    try:
        return {"answer": gemini.answer_question(question.strip())}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


# The original documentation calls this endpoint /qga in places.
@app.get("/qga")
async def qga(
    question: str = Query(..., min_length=1, max_length=4000)
) -> dict[str, str]:
    return await qna(question)


@app.post("/explain")
async def explain(payload: ExplanationRequest) -> dict[str, str]:
    try:
        return {
            "topic": payload.topic,
            "explanation": gemini.explain_topic(payload.topic),
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/summarize")
async def summarize(payload: SummaryRequest) -> dict[str, str]:
    try:
        return {"summary": gemini.summarize_text(payload.text)}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/quiz", response_model=QuizResponse)
async def quiz(payload: QuizRequest) -> QuizResponse:
    try:
        return gemini.generate_quiz(payload.text, payload.question_count)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get(
    "/learn/recommendations",
    response_model=LearningRecommendationResponse,
)
async def learning_recommendations(
    topic: str = Query(..., min_length=1, max_length=500)
) -> LearningRecommendationResponse:
    try:
        return gemini.get_learning_recommendations(topic.strip())
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

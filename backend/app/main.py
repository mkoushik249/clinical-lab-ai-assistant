import logging
import time

import openai
import psycopg

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.agent import run_agent
from app.database import get_connection
from app.lab_repository import (
    get_active_lab_tests,
    get_lab_test_by_code,
    search_lab_test,
)
from app.models import ChatRequest, ChatResponse, LabTest


logger = logging.getLogger("uvicorn.error")


app = FastAPI(
    title="Clinical Laboratory AI Assistant",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_request(
    request: Request,
    call_next,
):
    start_time = time.perf_counter()

    try:
        response = await call_next(request)

    except Exception:
        duration_ms = (
            time.perf_counter() - start_time
        ) * 1000

        logger.exception(
            "request method=%s path=%s status=500 duration_ms=%.1f",
            request.method,
            request.url.path,
            duration_ms,
        )

        raise

    duration_ms = (
        time.perf_counter() - start_time
    ) * 1000

    logger.info(
        "request method=%s path=%s status=%s duration_ms=%.1f",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )

    return response


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
    }


@app.get("/api/db-health")
def database_health_check():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()

    return {
        "status": "ok",
        "database": "connected",
        "result": result[0],
    }


@app.get(
    "/api/lab-tests",
    response_model=list[LabTest],
)
def list_lab_results():
    return get_active_lab_tests()


@app.get(
    "/api/lab-tests/{test_code}",
    response_model=LabTest,
)
def get_lab_test(test_code: str):
    lab_test = get_lab_test_by_code(
        test_code.upper()
    )

    if lab_test is None:
        raise HTTPException(
            status_code=404,
            detail="Lab test not found",
        )

    return lab_test


@app.get(
    "/api/lab-tests/search/{search_text}",
    response_model=LabTest,
)
def search_lab_test_endpoint(
    search_text: str,
):
    lab_test = search_lab_test(
        search_text
    )

    if lab_test is None:
        raise HTTPException(
            status_code=404,
            detail="Lab test not found",
        )

    return lab_test

@app.post(
    "/api/chat",
    response_model=ChatResponse,
)
def chat(request: ChatRequest):
    try:
        result = run_agent(
            request.question,
            request.history,
        )

    except (
        openai.APIConnectionError,
        openai.APITimeoutError,
        openai.RateLimitError,
    ):
        logger.exception(
            "OpenAI service unavailable during /api/chat"
        )

        raise HTTPException(
            status_code=503,
            detail="The AI service is temporarily unavailable.",
        )

    except openai.APIStatusError as exc:
        logger.exception(
            "OpenAI API error status=%s",
            exc.status_code,
        )

        if exc.status_code >= 500:
            raise HTTPException(
                status_code=503,
                detail="The AI service is temporarily unavailable.",
            )

        raise HTTPException(
            status_code=502,
            detail="The AI service could not process the request.",
        )

    except psycopg.Error:
        logger.exception(
            "Database error during /api/chat"
        )

        raise HTTPException(
            status_code=503,
            detail="The laboratory data service is temporarily unavailable.",
        )

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
    )

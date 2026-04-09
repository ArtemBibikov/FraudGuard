from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import redis.asyncio as redis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from .config import settings

from .utils.admin_utils import create_admin_user, create_tables_user
from .users.router import router as users_router
from .user_management.router import router as users_management_router
from .fraudrules.router import router as fraud_rules_router
from .transactions.router import router as transactions_router
from .statistics.router import router as statistics_router


@asynccontextmanager
async def lifespan(app: FastAPI):

    await create_tables_user()

    await create_admin_user()
    
    redis_client = await redis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        encoding="utf-8",
        decode_responses=True
    )
    # TODO: Redis кеш инициализирован для будущей оптимизации производительности сервиса
    # В настоящее время отключен в statistics эндпоинтах для чистой отладки тестов
    # План: Добавить @cache() декораторы к statistics эндпоинтам после тестов.
    FastAPICache.init(RedisBackend(redis_client), prefix="cache")

    yield
    
    await redis_client.close()

app = FastAPI(
    title="Anti-fraud Service API",
    description="REST API для обнаружения мошеннических транзакций",
    lifespan=lifespan
)

app.include_router(users_router, prefix="/api/v1")
app.include_router(users_management_router, prefix="/api/v1")
app.include_router(fraud_rules_router, prefix="/api/v1")
app.include_router(transactions_router, prefix="/api/v1")
app.include_router(statistics_router, prefix="/api/v1/stats")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        data = dict(exc.detail)
        if "path" not in data:
            data["path"] = request.url.path
        return JSONResponse(status_code=exc.status_code, content=data)

    code_map = {
        status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
        status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
        status.HTTP_403_FORBIDDEN: "FORBIDDEN",
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
        status.HTTP_409_CONFLICT: "CONFLICT",
        status.HTTP_422_UNPROCESSABLE_ENTITY: "VALIDATION_FAILED",
        status.HTTP_423_LOCKED: "USER_INACTIVE",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "INTERNAL_SERVER_ERROR",
    }

    data = {
        "code": code_map.get(exc.status_code, "INTERNAL_SERVER_ERROR"),
        "message": str(exc.detail),
        "path": request.url.path,
    }

    return JSONResponse(status_code=exc.status_code, content=data)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    field_errors = []
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error['loc'] if loc != 'body')
        field_errors.append({
            "field": field_path,
            "issue": error['msg'],
            "rejectedValue": error.get('input')
        })

    def sort_key(err: dict) -> int:
        if err.get("field") == "location.latitude":
            return 0
        if err.get("field") == "location.longitude":
            return 1
        return 2

    field_errors.sort(key=sort_key)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": "VALIDATION_FAILED",
            "message": "Validation failed",
            "path": request.url.path,
            "fieldErrors": field_errors
        }
    )

@app.get("/api/v1/ping")
async def ping():
    return {"status": "ok"}

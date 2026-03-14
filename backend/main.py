import logging
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from analyzer import preload_models
from pipeline import translate_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)

log = logging.getLogger(__name__)


from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Preload models on startup."""
    preload_models()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


class TranslateRequest(BaseModel):
    text: str
    source_lang: str = "auto"
    target_lang: str = "en"
    context: str | None = None
    mode: str = "simple"
    text_offset: int | None = None


@app.post("/translate")
def translate(req: TranslateRequest):
    try:
        result = translate_pipeline(
            text=req.text,
            context=req.context or "",
            source_lang=req.source_lang,
            target_lang=req.target_lang,
            mode=req.mode,
            text_offset=req.text_offset,
        )
        return result.to_dict()
    except Exception as e:
        log.error(f"[ERROR] Translation failed: {e}")
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/cache/stats")
def cache_stats():
    from cache import cache
    return cache.stats()


@app.post("/cache/clear")
def cache_clear():
    from cache import cache
    cache.clear()
    return {"status": "cleared"}

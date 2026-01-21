from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from translator import translate_simple, translate_smart

app = FastAPI()

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


@app.post("/translate")
def translate(req: TranslateRequest):
    if req.mode == "smart":
        result = translate_smart(req.text, req.context or "", req.source_lang, req.target_lang)
    else:
        result = translate_simple(req.text, req.source_lang, req.target_lang)
    return {"translation": result, "mode": req.mode}


@app.get("/health")
def health():
    return {"status": "ok"}

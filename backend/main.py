import asyncio
import logging
import traceback
from contextlib import asynccontextmanager
from functools import partial

import stripe
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from analyzer import preload_models
from auth import get_current_user
from config import settings
from db import get_db, get_usage, increment_usage
from pipeline import translate_pipeline
from translator import translate_simple

stripe.api_key = settings.stripe_secret_key

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    preload_models()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "DELETE"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


class TranslateRequest(BaseModel):
    text: str
    source_lang: str = "auto"
    target_lang: str = "en"
    context: str | None = None
    mode: str = "simple"
    text_offset: int | None = None


MAX_WORDS = 8
PHRASE_MIN_WORDS = 3


@app.post("/translate")
async def translate(req: TranslateRequest, user_id: str = Depends(get_current_user)):
    word_count = len((req.text or "").split())
    if word_count == 0 or word_count > MAX_WORDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": f"Selection must be 1–{MAX_WORDS} words.", "code": "TOO_LONG"},
        )

    used, limit, _plan, _cust = get_usage(user_id)
    if used >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"message": "Daily limit reached", "used": used, "limit": limit},
        )

    try:
        loop = asyncio.get_event_loop()
        if word_count >= PHRASE_MIN_WORDS:
            simple = await loop.run_in_executor(
                None,
                partial(translate_simple, req.text, req.source_lang, req.target_lang),
            )
            response = {"translation": simple["translation"]}
        else:
            result = await loop.run_in_executor(
                None,
                partial(
                    translate_pipeline,
                    text=req.text,
                    context=req.context or "",
                    source_lang=req.source_lang,
                    target_lang=req.target_lang,
                    mode=req.mode,
                    text_offset=req.text_offset,
                ),
            )
            response = result.to_dict()
    except Exception as e:
        log.error(f"[ERROR] Translation failed: {e}")
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Translation failed. Please try again.")

    increment_usage(user_id)

    response["usage"] = {"used": used + 1, "limit": limit}
    return response


@app.get("/usage")
def usage(user_id: str = Depends(get_current_user)):
    used, limit, plan, _cust = get_usage(user_id)
    return {"used": used, "limit": limit, "plan": plan}


class SaveWordRequest(BaseModel):
    text: str
    translation: str
    context: str | None = None
    source_url: str | None = None
    data: dict | None = None
    offset: int | None = None


@app.get("/words")
def list_words(user_id: str = Depends(get_current_user)):
    result = (
        get_db().table("saved_words")
        .select("*")
        .eq("user_id", user_id)
        .filter("deleted_at", "is", "null")
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


@app.post("/words", status_code=status.HTTP_201_CREATED)
def save_word(req: SaveWordRequest, user_id: str = Depends(get_current_user)):
    result = get_db().table("saved_words").insert({
        "user_id": user_id,
        "text": req.text,
        "translation": req.translation,
        "context": req.context,
        "source_url": req.source_url,
        "data": req.data,
        "offset": req.offset,
    }).execute()
    return result.data[0]


@app.delete("/words/{word_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_word(word_id: str, user_id: str = Depends(get_current_user)):
    from datetime import datetime, timezone
    result = (
        get_db().table("saved_words")
        .update({"deleted_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", word_id)
        .eq("user_id", user_id)
        .filter("deleted_at", "is", "null")
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found")


@app.get("/trash")
def list_trash(user_id: str = Depends(get_current_user)):
    result = (
        get_db().table("saved_words")
        .select("*")
        .eq("user_id", user_id)
        .filter("deleted_at", "not.is", "null")
        .order("deleted_at", desc=True)
        .execute()
    )
    return result.data


@app.delete("/trash/{word_id}", status_code=status.HTTP_204_NO_CONTENT)
def purge_word(word_id: str, user_id: str = Depends(get_current_user)):
    result = (
        get_db().table("saved_words")
        .delete()
        .eq("id", word_id)
        .eq("user_id", user_id)
        .filter("deleted_at", "not.is", "null")
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found in trash")


@app.post("/trash/{word_id}/restore", status_code=status.HTTP_200_OK)
def restore_word(word_id: str, user_id: str = Depends(get_current_user)):
    result = (
        get_db().table("saved_words")
        .update({"deleted_at": None})
        .eq("id", word_id)
        .eq("user_id", user_id)
        .filter("deleted_at", "not.is", "null")
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found in trash")
    return result.data[0]


@app.get("/checkout")
def create_checkout(user_id: str = Depends(get_current_user)):
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": settings.stripe_price_id, "quantity": 1}],
        success_url=f"{settings.backend_url}/checkout/success",
        cancel_url=f"{settings.backend_url}/checkout/cancel",
        metadata={"user_id": user_id},
    )
    return {"url": session.url}


@app.get("/portal")
def create_portal(user_id: str = Depends(get_current_user)):
    _used, _limit, _plan, stripe_customer_id = get_usage(user_id)
    if not stripe_customer_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active subscription")
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=f"{settings.backend_url}/static/privacy.html",
    )
    return {"url": session.url}


@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.stripe_webhook_secret)
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    db = get_db()

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        user_id = session_obj["metadata"].get("user_id")
        if user_id:
            db.table("profiles").update({
                "plan": "pro",
                "daily_limit": 500,
                "stripe_customer_id": session_obj.get("customer"),
            }).eq("id", user_id).execute()
            log.info(f"[STRIPE] Upgraded user {user_id} to pro")

    elif event["type"] == "customer.subscription.deleted":
        # Find user by Stripe customer ID
        customer_id = event["data"]["object"]["customer"]
        # Look up which user has this customer — stored in checkout session metadata
        # Simplest approach: search profiles by stripe_customer_id column (added below)
        result = db.table("profiles").select("id").eq("stripe_customer_id", customer_id).execute()
        if result.data:
            user_id = result.data[0]["id"]
            db.table("profiles").update({"plan": "free", "daily_limit": 50}).eq("id", user_id).execute()
            log.info(f"[STRIPE] Downgraded user {user_id} to free")

    return {"status": "ok"}


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

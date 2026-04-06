import logging
from datetime import date

from supabase import create_client, Client

from config import settings

log = logging.getLogger(__name__)

_client: Client | None = None


def get_db() -> Client:
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return _client


def get_usage(user_id: str) -> tuple[int, int, str, str | None]:
    """Return (today_count, daily_limit, plan, stripe_customer_id) for the user."""
    db = get_db()
    today = date.today().isoformat()

    profile = db.table("profiles").select("daily_limit, plan, stripe_customer_id").eq("id", user_id).single().execute()
    daily_limit: int = profile.data["daily_limit"]
    plan: str = profile.data.get("plan", "free")
    stripe_customer_id: str | None = profile.data.get("stripe_customer_id")

    usage = db.table("usage").select("count").eq("user_id", user_id).eq("date", today).execute()
    count: int = usage.data[0]["count"] if usage.data else 0

    return count, daily_limit, plan, stripe_customer_id


def increment_usage(user_id: str) -> None:
    """Upsert today's usage row, incrementing the count by 1."""
    db = get_db()
    today = date.today().isoformat()

    db.rpc("increment_usage", {"p_user_id": user_id, "p_date": today}).execute()

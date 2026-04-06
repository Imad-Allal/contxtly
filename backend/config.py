from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str
    redis_url: str = "redis://localhost:6379"
    supabase_url: str
    supabase_jwt_secret: str
    supabase_service_role_key: str
    stripe_secret_key: str
    stripe_webhook_secret: str
    stripe_price_id: str
    backend_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"


settings = Settings()

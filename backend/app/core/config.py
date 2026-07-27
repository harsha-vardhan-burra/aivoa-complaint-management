from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    # gemma2-9b-it (the prior default) was deprecated by Groq in 2025
    # and has since been decommissioned; openai/gpt-oss-120b is Groq's
    # current recommended general-purpose model and is also one of the
    # models Groq's own docs demonstrate strict Structured Outputs
    # (response_format=json_schema) with, which this service relies on.
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    DATABASE_URL: str = "postgresql+psycopg://user:password@localhost:5432/aivoa_complaints"
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    class Config:
        env_file = ".env"

settings = Settings()

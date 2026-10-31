from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    JWT_SECRET: str

    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    EMAIL_VERIFY_EXPIRE_HOURS: int = 24

    # Where the confirmation link points (the React app)
    FRONTEND_URL: str = "http://localhost:5173"

    # Outgoing mail. Leave SMTP_HOST empty in development: the confirmation
    # link is then printed to the server console instead of being emailed.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "SubNexus <no-reply@subnexus.local>"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()

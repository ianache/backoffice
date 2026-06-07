from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "mysql+asyncmy://backoffice:backoffice@localhost:3306/backoffice"
    internal_secret: str = "dev-internal-secret-change-in-prod"
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "mysql+asyncmy://backoffice:backoffice@localhost:3306/backoffice"
    internal_secret: str = "dev-internal-secret-change-in-prod"
    debug: bool = False

    # Keycloak connection (used by auth middleware and admin service)
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "master"

    # Keycloak Admin API client credentials (confidential client with manage-users)
    keycloak_admin_client_id: str = "backoffice-backend"
    keycloak_admin_client_secret: str = ""

    # SDK shared secret — SDK clients pass as Authorization: Bearer <sdk_key>
    sdk_secret_key: str = "dev-sdk-secret-change-in-prod"

    # BFF internal health-check target (Health Checker Engine, Phase 17)
    bff_internal_url: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

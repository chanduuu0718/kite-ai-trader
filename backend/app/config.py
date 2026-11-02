from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "KITE AI TRADER"
    api_prefix: str = "/api"
    demo_mode: bool = True
    cors_origins: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    @property
    def cors_origin_list(self):
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]
settings = Settings()

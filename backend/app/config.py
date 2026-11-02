from pathlib import Path\nfrom pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "KITE AI TRADER"
    api_prefix: str = "/api"
    demo_mode: bool = True
    cors_origins: str = "http://localhost:5173"
    indian_api_key: str = ""
    indian_api_base_url: str = "https://stock.indianapi.in"

    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[1] / ".env", extra="ignore")

    @property
    def cors_origin_list(self):
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


settings = Settings()

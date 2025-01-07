import json
from typing import Optional, List

from pydantic import field_validator, Field
from pydantic_settings import SettingsConfigDict, BaseSettings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=['.env', '../.env', '../../.env', '../../../.env', '../echelon/.env'],
                                      extra='ignore',
                                      env_file_encoding="utf-8")

    HOST: str = "0.0.0.0"
    PORT: int = 8080
    APP_NAME: str = "echelon"
    OTEL_ENABLED: bool = True
    OTEL_TRACE_UPLOAD_ENABLED: bool = False
    OTEL_TRACE_UPLOAD_URL: str = "http://127.0.0.1:4318/v1/traces"
    OPENAI_API_KEY: Optional[str] = None
    X_BEARER_TOKENS: List[str] = None
    SEARCHAPI_API_KEY: Optional[str] = None
    API_KEYS: List[str] = Field(default_factory=list)
    C_PRO_API_KEY: Optional[str] = None
    C_PRO_BASE_URL: Optional[str] = None
    BQ_API_KEY: Optional[str] = None
    BQ_BASE_URL: Optional[str] = None
    E_API_KEY: Optional[str] = None
    E_BASE_URL: Optional[str] = None
    B_API_KEY: Optional[str] = None
    B_API_URL: Optional[str] = None
    D_API_KEY: Optional[str] = None
    D_BASE_URL: Optional[str] = None

    @field_validator('API_KEYS', mode='before')
    def validator_api_keys(cls, v):
        if isinstance(v, str):
            v_list = json.loads(v)
            if isinstance(v_list, list):
                return v_list
        return v


SETTINGS = Settings()

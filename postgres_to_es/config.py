from typing import Optional, Dict
from pydantic import BaseModel


class DSNSettings(BaseModel):
    host: str
    port: int
    dbname: str
    password: str
    user: str
    options: str


class PostgresSettings(BaseModel):
    dsn: DSNSettings
    limit: Optional[int]


class ESHost(BaseModel):
    host: str
    port: int


class ESSettings(BaseModel):
    default_host: ESHost
    index_name: str
    index_config: str


class ETLSettings(BaseModel):
    postgres: PostgresSettings
    es: ESSettings
    fetch_delay: float
    state_file_name: str
    log_status_period: float


class Config(BaseModel):
    etl: ETLSettings
    logger: Dict

import os
import pathlib

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_root: str = pathlib.Path(__file__).parent.resolve().as_posix()
    app_name: str = os.getenv("APP_NAME", default="fastapi-app")
    app_port: int = os.getenv("APP_PORT", default=8000)

    log_config_path: str = (
        pathlib.Path(__file__).with_name("logging.ini").resolve().as_posix()
    )
    socketserver_log_config_path: str = (
        pathlib.Path(__file__)
        .with_name("socketserver_logging.ini")
        .resolve()
        .as_posix()
    )

    module_root: str = "/opt/modules"

    offline_path: str = "/tmp/bold-public-portal"
    cache_path: str = "/tmp/bold-public-portal/cache"

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0

    couchbase_endpoint: str = os.getenv("COUCHBASE_ENDPOINT", default="couchbase://couchbase")
    couchbase_user: str = os.getenv("COUCHBASE_USER", default="")
    couchbase_password: str = os.getenv("COUCHBASE_PASSWORD", default="")
    couchbase_timeout: int = 7200

    app_url: str = "http://fastapi-app:8000"
    caos_url: str = "https://caos.boldsystems.org"


settings = Settings()

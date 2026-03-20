from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Banking API"
    mysql_user: str = "root"
    mysql_password: str = "root"
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_db: str = "bankingapp_new"
    jwt_secret: str = "change_me_hs512_secret"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def database_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}"
        )


settings = Settings()

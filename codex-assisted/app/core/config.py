from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "mysql+asyncmy://root:password@localhost:3306/bankingapp_new"
    jwt_secret: str = "CHANGE_ME"
    jwt_algorithm: str = "HS512"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    snowflake_account: str

    alpha_snowflake_user: str = ""
    alpha_private_key_path: str = ""
    alpha_private_key_passphrase: str = ""

    beta_snowflake_user: str = ""
    beta_private_key_path: str = ""
    beta_private_key_passphrase: str = ""

    cortex_base_url_override: str = ""

    coco_port: int = 8000
    log_level: str = "INFO"

    @property
    def cortex_base_url(self) -> str:
        if self.cortex_base_url_override:
            return self.cortex_base_url_override
        account_host = self.snowflake_account.replace("_", "-")
        return f"https://{account_host}.snowflakecomputing.com/api/v2/cortex"


settings = Settings()

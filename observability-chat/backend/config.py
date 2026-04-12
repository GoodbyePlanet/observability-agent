from pydantic import Field
from pydantic_settings import BaseSettings


class MCPServerConfig(BaseSettings):
    name: str
    url: str


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")
    max_agent_iterations: int = Field(default=10, alias="MAX_AGENT_ITERATIONS")
    cors_origins: list[str] = Field(
        default=["http://localhost:5173"], alias="CORS_ORIGINS"
    )
    mcp_servers: list[MCPServerConfig] = Field(
        default=[MCPServerConfig(name="tempo", url="http://tempo:3200/api/mcp")],
        alias="MCP_SERVERS",
    )


settings = Settings()

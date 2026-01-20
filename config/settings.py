# config/settings.py
import os
from dataclasses import dataclass
from typing import List, Dict, Any
import yaml
from dotenv import load_dotenv


@dataclass
class Settings:
    # 加载 .env 文件中的环境变量
    load_dotenv()
    # GitHub配置
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_API_URL: str = "https://api.github.com"

    # OpenAI配置
    OPENAI_API_KEY: str = os.getenv("LLM_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("LLM_MODEL_ID", "")
    OPENAI_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")

    # 飞书配置
    FEISHU_WEBHOOK_URL: str = os.getenv("FEISHU_WEBHOOK_URL", "")
    FEISHU_APP_ID: str = os.getenv("FEISHU_APP_ID", "")
    FEISHU_APP_SECRET: str = os.getenv("FEISHU_APP_SECRET", "")
    FEISHU_USER_ID: str = os.getenv("FEISHU_USER_ID")

    # Redis配置
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # MCP配置
    MCP_PORT: int = int(os.getenv("MCP_PORT", "8080"))

    @classmethod
    def load_projects_config(cls) -> Dict[str, Any]:
        """加载大数据项目配置"""
        with open('projects.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def validate(self):
        """验证配置"""
        if not self.GITHUB_TOKEN:
            raise ValueError("GITHUB_TOKEN is required")
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        if not self.FEISHU_WEBHOOK_URL:
            raise ValueError("FEISHU_WEBHOOK_URL is required")


settings = Settings()

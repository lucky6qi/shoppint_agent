import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    """Simplified configuration class"""
    
    # ═══════════════════════════════════════════════════════════
    # 🔴 LLM SETTINGS - Anthropic Claude API Key
    # ═══════════════════════════════════════════════════════════
    anthropic_api_key: Optional[str] = None
    
    # AH Website Settings
    ah_bonus_url: str = "https://www.ah.nl/bonus"
    ah_base_url: str = "https://www.ah.nl"
    
    # Data Storage
    shopping_history_file: str = "shopping_history.json"
    products_cache_file: str = "products_cache.json"
    
    # Scraper Settings
    max_products: int = 1000
    request_timeout: int = 10
    cache_expiry_hours: int = 6  # Cache expiry time in hours
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from .env file or environment variables"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        return cls(
            anthropic_api_key=api_key,
        )

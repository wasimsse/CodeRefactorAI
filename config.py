import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
COHERE_API_KEY = os.getenv('COHERE_API_KEY')

# Model Settings
DEFAULT_MODEL = 'gpt-3.5-turbo'
DEFAULT_PROVIDER = 'OpenAI'

# Refactoring Settings
MAX_TOKENS = 2000
TEMPERATURE = 0.7

# UI Settings
THEME = 'light'
DEBUG_MODE = False

class Config(BaseModel):
    """Configuration settings for the application."""
    
    # Application settings
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024)  # 10MB
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)
    GOOGLE_API_KEY: Optional[str] = Field(default=None)
    COHERE_API_KEY: Optional[str] = Field(default=None)
    
    # File paths
    BASE_DIR: Path = Field(default=Path(__file__).parent)
    UPLOAD_DIR: Path = Field(default=None)
    LOG_DIR: Path = Field(default=None)
    TEMP_DIR: Path = Field(default=None)
    OUTPUT_DIR: Path = Field(default=None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup_paths()
        self.setup_api_keys()
        
    def setup_paths(self):
        """Set up application paths."""
        self.UPLOAD_DIR = self.BASE_DIR / 'uploads'
        self.LOG_DIR = self.BASE_DIR / 'logs'
        self.TEMP_DIR = self.BASE_DIR / 'temp'
        self.OUTPUT_DIR = self.BASE_DIR / 'output'
        
        # Create necessary directories
        for directory in [self.UPLOAD_DIR, self.LOG_DIR, self.TEMP_DIR, self.OUTPUT_DIR]:
            os.makedirs(directory, exist_ok=True)
            
    def setup_api_keys(self):
        """Set up API keys from environment variables."""
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        self.COHERE_API_KEY = os.getenv("COHERE_API_KEY")
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self.settings[key] = value
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values."""
        self.settings.update(updates)

# Create a config instance that can be imported
config = Config()
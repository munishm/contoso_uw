"""Environment configuration loader."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class EnvironmentConfig:
    """
    Loads and provides access to environment-specific configuration.
    
    Automatically loads .env files based on APP_ENV variable or parameter.
    """
    
    def __init__(self, env: Optional[str] = None):
        """
        Initialize environment configuration.
        
        Args:
            env: Environment name (dev, staging, prod). If None, reads from APP_ENV.
        """
        self.env = env or os.getenv("APP_ENV", "dev")
        self._load_env_file()
    
    def _load_env_file(self) -> None:
        """Load environment-specific .env file."""
        # Try to load environment-specific file
        env_file = Path(f".env.{self.env}")
        if env_file.exists():
            load_dotenv(env_file)
        else:
            # Fall back to .env file
            default_env = Path(".env")
            if default_env.exists():
                load_dotenv(default_env)
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable value.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Environment variable value or default
        """
        return os.getenv(key, default)
    
    def get_required(self, key: str) -> str:
        """
        Get required environment variable value.
        
        Args:
            key: Environment variable name
            
        Returns:
            Environment variable value
            
        Raises:
            ValueError: If environment variable is not set
        """
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"Required environment variable not set: {key}")
        return value
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        Get boolean environment variable value.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Boolean value
        """
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")
    
    def get_int(self, key: str, default: int = 0) -> int:
        """
        Get integer environment variable value.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Integer value
        """
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.env == "dev"
    
    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.env == "staging"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env == "prod"


# Global config instance
config = EnvironmentConfig()

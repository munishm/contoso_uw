"""Shared authentication manager to avoid multiple authentication attempts."""

import logging
from typing import Optional, Dict, Any
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
from azure.core.exceptions import ClientAuthenticationError


logger = logging.getLogger(__name__)


class SharedAuthManager:
    """
    Singleton authentication manager that reuses credentials across classifiers.
    """
    
    _instance: Optional['SharedAuthManager'] = None
    _credential: Optional[Any] = None
    _token_cache: Dict[str, str] = {}
    
    def __new__(cls) -> 'SharedAuthManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_credential(self, tenant_id: str):
        """
        Get shared Azure credential instance.
        
        Args:
            tenant_id: Azure tenant ID
            
        Returns:
            Azure credential instance (shared/cached)
        """
        if self._credential is None:
            logger.info("Initializing shared Azure credential...")
            try:
                self._credential = DefaultAzureCredential()
                # Test the credential
                self._credential.get_token("https://cognitiveservices.azure.com/.default", tenant_id=tenant_id)
                logger.info("✓ Shared authentication initialized with DefaultAzureCredential")
            except (ClientAuthenticationError, TypeError) as e:
                logger.info(f"DefaultAzureCredential failed: {e}, using InteractiveBrowserCredential...")
                self._credential = InteractiveBrowserCredential(tenant_id=tenant_id)
                logger.info("✓ Shared authentication initialized with InteractiveBrowserCredential")
        
        return self._credential
    
    def get_token(self, tenant_id: str, scope: str = "https://cognitiveservices.azure.com/.default") -> str:
        """
        Get cached access token for the given scope.
        
        Args:
            tenant_id: Azure tenant ID
            scope: Token scope
            
        Returns:
            Access token string
        """
        cache_key = f"{tenant_id}:{scope}"
        
        # Check if we have a valid cached token
        if cache_key in self._token_cache:
            # In a production scenario, you'd want to check token expiration
            # For now, we'll refresh on each call to ensure validity
            pass
        
        try:
            credential = self.get_credential(tenant_id)
            token = credential.get_token(scope)
            self._token_cache[cache_key] = token.token
            logger.debug("✓ Token refreshed successfully")
            return token.token
        except Exception as e:
            # Clear credential cache and retry once
            if self._credential is not None:
                logger.warning(f"Token refresh failed, clearing credential cache: {e}")
                self._credential = None
                self._token_cache.clear()
                return self.get_token(tenant_id, scope)
            else:
                raise Exception(f"Authentication failed: {e}")
    
    def create_token_provider(self, tenant_id: str, scope: str = "https://cognitiveservices.azure.com/.default"):
        """
        Create a token provider function using shared authentication.
        
        Args:
            tenant_id: Azure tenant ID
            scope: Token scope
            
        Returns:
            Callable that returns an access token using shared auth
        """
        def token_provider():
            return self.get_token(tenant_id, scope)
        
        return token_provider


# Global shared instance
_shared_auth = SharedAuthManager()


def get_shared_credential(tenant_id: str):
    """
    Get shared Azure credential (replaces individual get_azure_credential calls).
    
    Args:
        tenant_id: Azure tenant ID
        
    Returns:
        Shared Azure credential instance
    """
    return _shared_auth.get_credential(tenant_id)


def create_shared_token_provider(tenant_id: str):
    """
    Create a shared token provider (replaces individual create_token_provider calls).
    
    Args:
        tenant_id: Azure tenant ID
        
    Returns:
        Shared token provider function
    """
    return _shared_auth.create_token_provider(tenant_id)


def get_shared_token(tenant_id: str, scope: str = "https://cognitiveservices.azure.com/.default") -> str:
    """
    Get shared access token directly.
    
    Args:
        tenant_id: Azure tenant ID
        scope: Token scope
        
    Returns:
        Access token string
    """
    return _shared_auth.get_token(tenant_id, scope)
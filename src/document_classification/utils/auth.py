"""Azure authentication utilities."""

import os
import logging
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
from azure.core.exceptions import ClientAuthenticationError


logger = logging.getLogger(__name__)


def get_azure_credential(tenant_id: str):
    """
    Get Azure credential for authentication.
    
    Args:
        tenant_id: Azure tenant ID
        
    Returns:
        Azure credential instance
    """
    try:
        credential = DefaultAzureCredential()
        # Test the credential
        credential.get_token("https://cognitiveservices.azure.com/.default", tenant_id=tenant_id)
        logger.info("Using DefaultAzureCredential")
        return credential
    except (ClientAuthenticationError, TypeError) as e:
        logger.info(f"DefaultAzureCredential failed: {e}, using InteractiveBrowserCredential...")
        return InteractiveBrowserCredential(tenant_id=tenant_id)


def create_token_provider(tenant_id: str):
    """
    Create a token provider function for Azure AD authentication.
    
    Args:
        tenant_id: Azure tenant ID
        
    Returns:
        Callable that returns an access token
    """
    def token_provider():
        try:
            # Try DefaultAzureCredential first
            credential = DefaultAzureCredential()
            token = credential.get_token("https://cognitiveservices.azure.com/.default")
            logger.info("Authentication successful using DefaultAzureCredential")
            return token.token
        except Exception as e:
            logger.debug(f"DefaultAzureCredential failed: {e}")
            logger.info("Trying InteractiveBrowserCredential...")
            
            try:
                # Fallback to InteractiveBrowserCredential
                credential = InteractiveBrowserCredential(tenant_id=tenant_id)
                token = credential.get_token("https://cognitiveservices.azure.com/.default")
                logger.info("Authentication successful using InteractiveBrowserCredential")
                return token.token
            except Exception as e2:
                raise Exception(f"Authentication failed: {e2}")
    
    return token_provider

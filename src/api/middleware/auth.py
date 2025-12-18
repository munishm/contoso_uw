"""
Bearer token authentication middleware.

Validates JWT tokens against Azure AD and extracts user claims.
"""

import logging
from typing import Any, Optional

import httpx
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.api.config.settings import Settings, get_settings
from src.api.middleware.correlation import get_correlation_id

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


class JWKSClient:
    """Client for fetching and caching JWKS keys."""

    _instance: Optional["JWKSClient"] = None
    _jwks: Optional[dict[str, Any]] = None
    _jwks_uri: Optional[str] = None

    def __new__(cls) -> "JWKSClient":
        """Ensure single instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_signing_key(self, token: str) -> Optional[jwt.PyJWK]:
        """
        Get the signing key for a token from JWKS.

        Args:
            token: The JWT token

        Returns:
            The signing key if found, None otherwise
        """
        settings = get_settings()

        if not settings.azure_ad_jwks_uri:
            logger.warning("JWKS URI not configured")
            return None

        # Fetch JWKS if not cached or URI changed
        if self._jwks is None or self._jwks_uri != settings.azure_ad_jwks_uri:
            await self._fetch_jwks(settings.azure_ad_jwks_uri)

        if not self._jwks:
            return None

        # Get the key ID from token header
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
        except jwt.exceptions.DecodeError:
            logger.warning("Failed to decode token header")
            return None

        if not kid:
            logger.warning("Token does not have a key ID (kid)")
            return None

        # Find the key in JWKS
        jwk_set = jwt.PyJWKSet.from_dict(self._jwks)
        for key in jwk_set.keys:
            if key.key_id == kid:
                return key

        logger.warning(f"Key ID {kid} not found in JWKS")
        return None

    async def _fetch_jwks(self, jwks_uri: str) -> None:
        """Fetch JWKS from Azure AD."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(jwks_uri, timeout=10.0)
                response.raise_for_status()
                self._jwks = response.json()
                self._jwks_uri = jwks_uri
                logger.info(f"Fetched JWKS from {jwks_uri}")
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            self._jwks = None


# Global JWKS client
jwks_client = JWKSClient()


class UserClaims:
    """User claims extracted from JWT token."""

    def __init__(
        self,
        user_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        roles: list[str] | None = None,
        raw_claims: dict[str, Any] | None = None,
    ):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.roles = roles or []
        self.raw_claims = raw_claims or {}


async def validate_token(token: str, settings: Settings) -> Optional[UserClaims]:
    """
    Validate a JWT token and extract user claims.

    Args:
        token: The JWT token
        settings: Application settings

    Returns:
        UserClaims if valid, None otherwise
    """
    # Get signing key
    signing_key = await jwks_client.get_signing_key(token)
    if not signing_key:
        return None

    try:
        # Decode and verify token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.azure_client_id,
            issuer=settings.azure_ad_issuer,
            options={
                "verify_exp": True,
                "verify_iat": True,
                "verify_aud": True,
                "verify_iss": True,
            },
        )

        # Extract claims
        user_id = payload.get("oid") or payload.get("sub")
        if not user_id:
            logger.warning("Token missing user identifier (oid/sub)")
            return None

        return UserClaims(
            user_id=user_id,
            email=payload.get("email") or payload.get("preferred_username"),
            name=payload.get("name"),
            roles=payload.get("roles", []),
            raw_claims=payload,
        )

    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidAudienceError:
        logger.warning("Token has invalid audience")
        return None
    except jwt.InvalidIssuerError:
        logger.warning("Token has invalid issuer")
        return None
    except jwt.PyJWTError as e:
        logger.warning(f"Token validation failed: {e}")
        return None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    settings: Settings = Depends(get_settings),
) -> UserClaims:
    """
    FastAPI dependency to get the current authenticated user.

    Args:
        request: The FastAPI request
        credentials: Bearer token credentials
        settings: Application settings

    Returns:
        UserClaims for the authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    correlation_id = get_correlation_id()

    # Check if auth is disabled (development only)
    if settings.disable_auth:
        logger.warning(
            "Authentication disabled - using mock user",
            extra={"correlation_id": correlation_id},
        )
        return UserClaims(
            user_id="dev-user",
            email="dev@example.com",
            name="Development User",
            roles=["admin"],
        )

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate token
    user_claims = await validate_token(credentials.credentials, settings)

    if not user_claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug(
        f"Authenticated user: {user_claims.user_id}",
        extra={"correlation_id": correlation_id, "user_id": user_claims.user_id},
    )

    return user_claims


async def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    settings: Settings = Depends(get_settings),
) -> Optional[UserClaims]:
    """
    FastAPI dependency to optionally get the current user.

    Does not raise an error if no token is provided.

    Returns:
        UserClaims if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        return await get_current_user(request, credentials, settings)
    except HTTPException:
        return None

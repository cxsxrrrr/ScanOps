"""
Clerk JWT Authentication backend for Django REST Framework.

Validates JWT tokens issued by Clerk and maps them to internal User objects.
"""
import logging

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions

logger = logging.getLogger(__name__)
User = get_user_model()

# Cached PyJWKClient instance
_jwk_client = None


def _get_jwk_client():
    """Get or create cached PyJWKClient."""
    global _jwk_client
    if _jwk_client is None:
        jwks_url = settings.CLERK_JWKS_URL
        if not jwks_url:
            raise exceptions.AuthenticationFailed(
                'CLERK_JWKS_URL not configured.'
            )
        _jwk_client = jwt.PyJWKClient(jwks_url, cache_keys=True)
    return _jwk_client


def _decode_clerk_token(token):
    """Decode and validate a Clerk JWT token."""
    try:
        client = _get_jwk_client()
        signing_key = client.get_signing_key_from_jwt(token)

        # Decode with validation
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=['RS256'],
            issuer=settings.CLERK_ISSUER or None,
            options={
                'verify_exp': True,
                'verify_iss': bool(settings.CLERK_ISSUER),
                'verify_aud': False,  # Clerk doesn't always set audience
            },
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise exceptions.AuthenticationFailed('Token has expired.')
    except jwt.InvalidIssuerError as e:
        logger.warning(f"JWT issuer mismatch: {e}")
        raise exceptions.AuthenticationFailed('Invalid token issuer.')
    except jwt.PyJWTError as e:
        logger.warning(f"JWT validation failed: {type(e).__name__}: {e}")
        raise exceptions.AuthenticationFailed('Invalid authentication token.')


class ClerkJWTAuthentication(authentication.BaseAuthentication):
    """
    DRF Authentication backend for Clerk.

    Extracts Bearer token from Authorization header, validates it
    against Clerk's JWKS, and returns the corresponding Django user.
    """

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Bearer '):
            return None  # No token, skip this backend

        token = auth_header[7:]  # Strip 'Bearer '

        if not token:
            return None

        # Decode and validate the Clerk JWT
        payload = _decode_clerk_token(token)
        clerk_user_id = payload.get('sub')

        if not clerk_user_id:
            raise exceptions.AuthenticationFailed('Token missing user identifier.')

        # Get or create the internal Django user
        try:
            user = User.objects.select_related('organization').get(
                clerk_user_id=clerk_user_id
            )
        except User.DoesNotExist:
            # Auto-create user on first authentication
            email = payload.get('email', payload.get('email_addresses', [{}])[0].get('email_address', ''))
            first_name = payload.get('first_name', '')
            last_name = payload.get('last_name', '')

            user = User.objects.create(
                clerk_user_id=clerk_user_id,
                username=clerk_user_id,  # Use clerk ID as username
                email=email or f'{clerk_user_id}@clerk.user',
                first_name=first_name,
                last_name=last_name,
            )
            logger.info(f"Auto-created user for Clerk ID: {clerk_user_id}")

        return (user, payload)

    def authenticate_header(self, request):
        return 'Bearer'

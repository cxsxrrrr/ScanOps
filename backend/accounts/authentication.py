"""
Clerk JWT Authentication backend for Django REST Framework.

Validates JWT tokens issued by Clerk and maps them to internal User objects.
"""
import logging

import jwt
import requests
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
            leeway=60,  # Allow 60s clock skew between Clerk and server
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


def _fetch_email_from_clerk_api(clerk_user_id):
    """Fetch the primary email for a Clerk user via the Backend API."""
    if not settings.CLERK_SECRET_KEY:
        return None
    try:
        response = requests.get(
            f'https://api.clerk.com/v1/users/{clerk_user_id}',
            headers={'Authorization': f'Bearer {settings.CLERK_SECRET_KEY}'},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        email_addresses = data.get('email_addresses', [])
        for e in email_addresses:
            if e.get('id') == data.get('primary_email_address_id'):
                return e.get('email_address')
        if email_addresses:
            return email_addresses[0].get('email_address')
    except Exception as e:
        logger.warning(f"Failed to fetch email from Clerk API for {clerk_user_id}: {e}")
    return None


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
        try:
            payload = _decode_clerk_token(token)
        except exceptions.AuthenticationFailed:
            logger.warning(f"JWT validation failed for token prefix: {token[:20]}...")
            raise
        clerk_user_id = payload.get('sub')

        if not clerk_user_id:
            raise exceptions.AuthenticationFailed('Token missing user identifier.')

        # Get or create / match the internal Django user
        email = payload.get(
            'email',
            next((e.get('email_address', '') for e in payload.get('email_addresses', []) if e.get('email_address')), '')
        )
        first_name = payload.get('first_name', '')
        last_name = payload.get('last_name', '')

        # If JWT doesn't carry a real email, try Clerk Backend API
        if not email or email == f'{clerk_user_id}@clerk.user':
            api_email = _fetch_email_from_clerk_api(clerk_user_id)
            if api_email:
                email = api_email

        user = None

        # 1. Try clerk_user_id lookup
        try:
            user = User.objects.select_related('organization').get(clerk_user_id=clerk_user_id)
        except User.DoesNotExist:
            pass

        # 2. If real email exists, always prefer the user with that email
        if email and email != f'{clerk_user_id}@clerk.user':
            try:
                email_user = User.objects.select_related('organization').get(email=email)
                if user and user.pk != email_user.pk:
                    user.clerk_user_id = None
                    user.save(update_fields=['clerk_user_id'])
                    logger.info(f"Unlinked Clerk ID {clerk_user_id} from {user.email}")
                email_user.clerk_user_id = clerk_user_id
                email_user.save(update_fields=['clerk_user_id'])
                user = email_user
                logger.info(f"Linked Clerk ID {clerk_user_id} to existing user {email}")
            except User.DoesNotExist:
                if not user:
                    from django.db import IntegrityError
                    try:
                        user = User.objects.create(
                            clerk_user_id=clerk_user_id,
                            username=clerk_user_id,
                            email=email,
                            first_name=first_name,
                            last_name=last_name,
                        )
                        logger.info(f"Auto-created user for Clerk ID: {clerk_user_id}")
                    except IntegrityError:
                        user = User.objects.get(clerk_user_id=clerk_user_id)
        elif not user:
            from django.db import IntegrityError
            try:
                user = User.objects.create(
                    clerk_user_id=clerk_user_id,
                    username=clerk_user_id,
                    email=email or f'{clerk_user_id}@clerk.user',
                    first_name=first_name,
                    last_name=last_name,
                )
                logger.info(f"Auto-created user for Clerk ID: {clerk_user_id}")
            except IntegrityError:
                user = User.objects.get(clerk_user_id=clerk_user_id)

        # If user still has a fake email, try to update it from Clerk API
        if user.email.endswith('@clerk.user'):
            api_email = _fetch_email_from_clerk_api(clerk_user_id)
            if api_email:
                user.email = api_email
                user.save(update_fields=['email'])
                logger.info(f"Updated email for user {clerk_user_id}: {api_email}")

        return (user, payload)

    def authenticate_header(self, request):
        return 'Bearer'

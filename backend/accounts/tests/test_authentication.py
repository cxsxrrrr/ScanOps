"""
Tests for ClerkJWTAuthentication — Priority 2 (Critical).

Tests JWT validation, auto-creation of users, and error handling.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from rest_framework.exceptions import AuthenticationFailed

from accounts.authentication import ClerkJWTAuthentication
from accounts.models import User, Organization


class ClerkJWTAuthenticationTest(TestCase):
    """Tests for the Clerk JWT authentication backend."""

    def setUp(self):
        self.auth = ClerkJWTAuthentication()
        self.factory = RequestFactory()
        self.org = Organization.objects.create(name='Test Org')
        self.user = User.objects.create_user(
            username='clerk_existing_123',
            email='existing@test.com',
            clerk_user_id='clerk_existing_123',
            organization=self.org,
        )

    def test_no_auth_header_returns_none(self):
        """Request without Authorization header → None (skip)."""
        request = self.factory.get('/')
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    def test_non_bearer_header_returns_none(self):
        """Authorization header without 'Bearer ' prefix → None."""
        request = self.factory.get('/', HTTP_AUTHORIZATION='Basic abc123')
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    def test_empty_bearer_token_returns_none(self):
        """'Bearer ' with no token → None."""
        request = self.factory.get('/', HTTP_AUTHORIZATION='Bearer ')
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    @patch('accounts.authentication._decode_clerk_token')
    def test_valid_token_returns_existing_user(self, mock_decode):
        """Valid token for existing user → returns (user, payload)."""
        mock_decode.return_value = {
            'sub': 'clerk_existing_123',
            'email': 'existing@test.com',
        }
        request = self.factory.get('/', HTTP_AUTHORIZATION='Bearer valid_token_123')
        user, payload = self.auth.authenticate(request)

        self.assertEqual(user.pk, self.user.pk)
        self.assertEqual(user.clerk_user_id, 'clerk_existing_123')
        self.assertEqual(payload['sub'], 'clerk_existing_123')

    @patch('accounts.authentication._decode_clerk_token')
    def test_valid_token_auto_creates_new_user(self, mock_decode):
        """Valid token for unknown clerk ID → auto-creates user."""
        mock_decode.return_value = {
            'sub': 'clerk_new_user_456',
            'email': 'newuser@test.com',
            'first_name': 'Samuel',
            'last_name': 'Rodríguez',
        }
        request = self.factory.get('/', HTTP_AUTHORIZATION='Bearer new_user_token')
        user, payload = self.auth.authenticate(request)

        self.assertEqual(user.clerk_user_id, 'clerk_new_user_456')
        self.assertEqual(user.email, 'newuser@test.com')
        self.assertEqual(user.first_name, 'Samuel')
        self.assertTrue(User.objects.filter(clerk_user_id='clerk_new_user_456').exists())

    @patch('accounts.authentication._decode_clerk_token')
    def test_token_missing_sub_raises_error(self, mock_decode):
        """Token without 'sub' claim → AuthenticationFailed."""
        mock_decode.return_value = {'email': 'no-sub@test.com'}
        request = self.factory.get('/', HTTP_AUTHORIZATION='Bearer bad_token')

        with self.assertRaises(AuthenticationFailed) as ctx:
            self.auth.authenticate(request)
        self.assertIn('missing user identifier', str(ctx.exception.detail).lower())

    @patch('accounts.authentication._decode_clerk_token')
    def test_expired_token_raises_error(self, mock_decode):
        """Expired JWT → AuthenticationFailed."""
        mock_decode.side_effect = AuthenticationFailed('Token has expired.')
        request = self.factory.get('/', HTTP_AUTHORIZATION='Bearer expired_token')

        with self.assertRaises(AuthenticationFailed) as ctx:
            self.auth.authenticate(request)
        self.assertIn('expired', str(ctx.exception.detail).lower())

    def test_authenticate_header_returns_bearer(self):
        """authenticate_header should return 'Bearer'."""
        request = self.factory.get('/')
        self.assertEqual(self.auth.authenticate_header(request), 'Bearer')

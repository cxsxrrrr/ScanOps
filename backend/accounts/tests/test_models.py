"""
Tests for accounts models — Priority 3.
"""
from django.test import TestCase
from accounts.models import User, Organization


class OrganizationModelTest(TestCase):
    """Tests for the Organization model."""

    def test_str_representation(self):
        """__str__ returns the org name."""
        org = Organization.objects.create(name='Mi Empresa')
        self.assertEqual(str(org), 'Mi Empresa')

    def test_default_plan_is_free(self):
        """Default plan should be 'free'."""
        org = Organization.objects.create(name='Test')
        self.assertEqual(org.plan, 'free')

    def test_default_url_limit_is_5(self):
        """Default URL limit should be 5."""
        org = Organization.objects.create(name='Test')
        self.assertEqual(org.url_limit, 5)

    def test_ordering_by_name(self):
        """Organizations ordered alphabetically by name."""
        Organization.objects.create(name='Zebra Corp')
        Organization.objects.create(name='Alpha Inc')
        orgs = list(Organization.objects.values_list('name', flat=True))
        self.assertEqual(orgs, ['Alpha Inc', 'Zebra Corp'])


class UserModelTest(TestCase):
    """Tests for the custom User model."""

    def setUp(self):
        self.org = Organization.objects.create(name='Test Org')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            organization=self.org,
        )

    def test_str_representation(self):
        """__str__ returns email and org."""
        self.assertEqual(str(self.user), 'test@example.com (Test Org)')

    def test_is_admin_user_false_by_default(self):
        """Default role is 'user', not admin."""
        self.assertFalse(self.user.is_admin_user)

    def test_is_admin_user_true_for_admins(self):
        """Admin role → is_admin_user returns True."""
        self.user.role = 'admin'
        self.user.save()
        self.assertTrue(self.user.is_admin_user)

    def test_clerk_user_id_unique(self):
        """clerk_user_id must be unique."""
        self.user.clerk_user_id = 'unique_clerk_id'
        self.user.save()
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='another',
                email='another@test.com',
                clerk_user_id='unique_clerk_id',
            )

    def test_user_without_organization(self):
        """User can exist without an organization."""
        user = User.objects.create_user(
            username='no_org',
            email='noorg@test.com',
        )
        self.assertIsNone(user.organization)

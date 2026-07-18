"""Tests for the organization invitation accept flow."""
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User, Organization, Invitation
from urls_manager.models import URLAsset


class AcceptInvitationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.target_org = Organization.objects.create(name='Target Org', plan='ultimate')
        self.inviter = User.objects.create_user(
            username='inviter', email='inviter@test.com', password='pass123',
            organization=self.target_org, role='org_admin',
        )
        self.invitation = Invitation.objects.create(
            organization=self.target_org, created_by=self.inviter,
        )

    def test_user_with_no_org_joins_directly(self):
        user = User.objects.create_user(username='newbie', email='newbie@test.com', password='pass123')
        self.client.force_authenticate(user=user)

        response = self.client.post(f'/api/auth/invitations/{self.invitation.token}/accept/', {
            'first_name': 'New', 'last_name': 'Bie',
        })
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.organization_id, self.target_org.id)

    def test_untouched_placeholder_org_is_auto_left(self):
        """A just-auto-created empty org (no other members, no URLs) shouldn't block the invite."""
        placeholder_org = Organization.objects.create(name='Org de Newbie', plan='free', url_limit=1)
        user = User.objects.create_user(
            username='newbie', email='newbie@test.com', password='pass123',
            organization=placeholder_org, role='org_admin',
        )
        self.client.force_authenticate(user=user)

        response = self.client.post(f'/api/auth/invitations/{self.invitation.token}/accept/', {})
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.organization_id, self.target_org.id)
        self.assertFalse(Organization.objects.filter(pk=placeholder_org.pk).exists())

    def test_real_org_with_other_members_blocks_join(self):
        real_org = Organization.objects.create(name='Real Org', plan='pro')
        User.objects.create_user(username='colleague', email='colleague@test.com', password='pass123', organization=real_org)
        user = User.objects.create_user(
            username='member', email='member@test.com', password='pass123',
            organization=real_org, role='user',
        )
        self.client.force_authenticate(user=user)

        response = self.client.post(f'/api/auth/invitations/{self.invitation.token}/accept/', {})
        self.assertEqual(response.status_code, 400)
        user.refresh_from_db()
        self.assertEqual(user.organization_id, real_org.id)
        self.assertTrue(Organization.objects.filter(pk=real_org.pk).exists())

    def test_org_with_registered_url_blocks_join(self):
        """Even as the sole member, an org with real usage isn't a throwaway placeholder."""
        used_org = Organization.objects.create(name='Used Org', plan='free', url_limit=1)
        URLAsset.objects.create(organization=used_org, url='https://example.com')
        user = User.objects.create_user(
            username='member', email='member@test.com', password='pass123',
            organization=used_org, role='org_admin',
        )
        self.client.force_authenticate(user=user)

        response = self.client.post(f'/api/auth/invitations/{self.invitation.token}/accept/', {})
        self.assertEqual(response.status_code, 400)
        user.refresh_from_db()
        self.assertEqual(user.organization_id, used_org.id)

    def test_expired_invitation_rejected(self):
        from datetime import timedelta
        from django.utils import timezone
        self.invitation.expires_at = timezone.now() - timedelta(days=1)
        self.invitation.save(update_fields=['expires_at'])

        user = User.objects.create_user(username='newbie', email='newbie@test.com', password='pass123')
        self.client.force_authenticate(user=user)
        response = self.client.post(f'/api/auth/invitations/{self.invitation.token}/accept/', {})
        self.assertEqual(response.status_code, 404)

    def test_member_limit_reached_rejected(self):
        limited_org = Organization.objects.create(name='Free Org', plan='free')
        User.objects.create_user(username='solo', email='solo@test.com', password='pass123', organization=limited_org)
        invite = Invitation.objects.create(organization=limited_org, created_by=self.inviter)

        user = User.objects.create_user(username='newbie2', email='newbie2@test.com', password='pass123')
        self.client.force_authenticate(user=user)
        response = self.client.post(f'/api/auth/invitations/{invite.token}/accept/', {})
        self.assertEqual(response.status_code, 400)

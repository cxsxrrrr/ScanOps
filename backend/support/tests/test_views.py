"""Tests for the support ticket endpoints."""
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User, Organization
from support.models import SupportTicket, TicketMessage


class SupportTicketTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name='PYME Test')
        self.other_org = Organization.objects.create(name='Other Org')

        self.user = User.objects.create_user(
            username='member', email='member@pyme.com', password='pass123',
            organization=self.org,
        )
        self.other_user = User.objects.create_user(
            username='other', email='other@other.com', password='pass123',
            organization=self.other_org,
        )
        self.platform_admin = User.objects.create_user(
            username='admin', email='admin@vigia.com', password='pass123',
            role='admin',
        )

    def test_create_ticket(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/support/tickets/', {
            'subject': 'No puedo escanear',
            'category': 'error',
            'priority': 'high',
            'body': 'El escaneo falla siempre.',
        })
        self.assertEqual(response.status_code, 201)
        ticket = SupportTicket.objects.get(pk=response.data['id'])
        self.assertEqual(ticket.organization_id, self.org.id)
        self.assertEqual(ticket.messages.count(), 1)

    def test_list_scoped_to_own_organization(self):
        SupportTicket.objects.create(organization=self.org, created_by=self.user, subject='A')
        SupportTicket.objects.create(organization=self.other_org, created_by=self.other_user, subject='B')

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/support/tickets/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['subject'], 'A')

    def test_platform_admin_sees_all_tickets(self):
        SupportTicket.objects.create(organization=self.org, created_by=self.user, subject='A')
        SupportTicket.objects.create(organization=self.other_org, created_by=self.other_user, subject='B')

        self.client.force_authenticate(user=self.platform_admin)
        response = self.client.get('/api/support/tickets/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_cannot_view_other_organization_ticket(self):
        ticket = SupportTicket.objects.create(organization=self.other_org, created_by=self.other_user, subject='B')

        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/support/tickets/{ticket.id}/')
        self.assertEqual(response.status_code, 404)

    def test_member_cannot_change_status(self):
        ticket = SupportTicket.objects.create(organization=self.org, created_by=self.user, subject='A')

        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f'/api/support/tickets/{ticket.id}/', {'status': 'closed'})
        self.assertEqual(response.status_code, 403)

    def test_admin_can_close_ticket(self):
        ticket = SupportTicket.objects.create(organization=self.org, created_by=self.user, subject='A')

        self.client.force_authenticate(user=self.platform_admin)
        response = self.client.patch(f'/api/support/tickets/{ticket.id}/', {'status': 'closed'})
        self.assertEqual(response.status_code, 200)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'closed')
        self.assertIsNotNone(ticket.closed_at)

    def test_add_message_reopens_closed_ticket_on_staff_reply(self):
        ticket = SupportTicket.objects.create(
            organization=self.org, created_by=self.user, subject='A', status='closed',
        )

        self.client.force_authenticate(user=self.platform_admin)
        response = self.client.post(f'/api/support/tickets/{ticket.id}/messages/', {'body': 'Ya lo revisamos.'})
        self.assertEqual(response.status_code, 201)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'in_progress')
        self.assertTrue(TicketMessage.objects.get(pk=response.data['id']).is_staff)

    def test_staff_reply_moves_open_ticket_to_in_progress(self):
        ticket = SupportTicket.objects.create(organization=self.org, created_by=self.user, subject='A')

        self.client.force_authenticate(user=self.platform_admin)
        response = self.client.post(f'/api/support/tickets/{ticket.id}/messages/', {'body': 'Lo vemos.'})
        self.assertEqual(response.status_code, 201)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'in_progress')

    def test_member_cannot_message_other_org_ticket(self):
        ticket = SupportTicket.objects.create(organization=self.other_org, created_by=self.other_user, subject='B')

        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/support/tickets/{ticket.id}/messages/', {'body': 'hola'})
        self.assertEqual(response.status_code, 404)

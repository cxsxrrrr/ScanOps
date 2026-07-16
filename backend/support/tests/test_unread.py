"""Tests for unread-message tracking (TicketRead) on support tickets."""
from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User, Organization
from support.models import SupportTicket, TicketMessage, TicketRead


class UnreadCountTest(TestCase):
    def setUp(self):
        patcher1 = patch('support.tasks.notify_new_ticket.delay')
        patcher2 = patch('support.tasks.notify_ticket_reply.delay')
        patcher1.start()
        patcher2.start()
        self.addCleanup(patcher1.stop)
        self.addCleanup(patcher2.stop)

        self.client = APIClient()
        self.org = Organization.objects.create(name='PYME Test')
        self.user = User.objects.create_user(
            username='member', email='member@pyme.com', password='pass123',
            organization=self.org,
        )
        self.admin = User.objects.create_user(
            username='admin', email='admin@vigia.com', password='pass123', role='admin',
        )
        self.ticket = SupportTicket.objects.create(
            organization=self.org, created_by=self.user, subject='A',
        )

    def test_member_sees_unread_staff_replies(self):
        TicketMessage.objects.create(ticket=self.ticket, is_staff=True, body='Hola')
        TicketMessage.objects.create(ticket=self.ticket, is_staff=True, body='Otra')

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/support/tickets/')
        self.assertEqual(response.data[0]['unread_count'], 2)

    def test_member_own_messages_dont_count_as_unread(self):
        TicketMessage.objects.create(ticket=self.ticket, is_staff=False, body='Mi mensaje')

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/support/tickets/')
        self.assertEqual(response.data[0]['unread_count'], 0)

    def test_viewing_ticket_marks_it_read(self):
        TicketMessage.objects.create(ticket=self.ticket, is_staff=True, body='Hola')

        self.client.force_authenticate(user=self.user)
        detail = self.client.get(f'/api/support/tickets/{self.ticket.id}/')
        self.assertEqual(detail.status_code, 200)
        self.assertTrue(TicketRead.objects.filter(ticket=self.ticket, user=self.user).exists())

        response = self.client.get('/api/support/tickets/')
        self.assertEqual(response.data[0]['unread_count'], 0)

    def test_new_reply_after_read_counts_again(self):
        self.client.force_authenticate(user=self.user)
        self.client.get(f'/api/support/tickets/{self.ticket.id}/')

        TicketMessage.objects.create(ticket=self.ticket, is_staff=True, body='Nueva respuesta')

        response = self.client.get('/api/support/tickets/')
        self.assertEqual(response.data[0]['unread_count'], 1)

    def test_admin_sees_unread_member_messages(self):
        TicketMessage.objects.create(ticket=self.ticket, is_staff=False, body='Ayuda porfa')

        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/support/tickets/')
        self.assertEqual(response.data[0]['unread_count'], 1)

    def test_admin_own_replies_dont_count_as_unread_for_admin(self):
        TicketMessage.objects.create(ticket=self.ticket, is_staff=True, body='Ya lo vemos')

        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/support/tickets/')
        self.assertEqual(response.data[0]['unread_count'], 0)

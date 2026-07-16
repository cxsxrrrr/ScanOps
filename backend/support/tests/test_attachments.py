"""Tests for screenshot attachments on support tickets/messages."""
import io
import shutil
import tempfile
from unittest.mock import patch
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import User, Organization
from support.models import SupportTicket, TicketAttachment

TEMP_MEDIA = tempfile.mkdtemp()


def _png_file(name='shot.png'):
    buf = io.BytesIO()
    Image.new('RGB', (10, 10), color='red').save(buf, format='PNG')
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type='image/png')


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TicketAttachmentTest(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

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

    def test_create_ticket_with_image_attachment(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/support/tickets/', {
            'subject': 'Error visual',
            'category': 'error',
            'priority': 'medium',
            'body': 'Mira la captura.',
            'images': [_png_file()],
        }, format='multipart')
        self.assertEqual(response.status_code, 201)
        ticket = SupportTicket.objects.get(pk=response.data['id'])
        self.assertEqual(TicketAttachment.objects.filter(message__ticket=ticket).count(), 1)
        self.assertEqual(len(response.data['messages'][0]['attachments']), 1)

    def test_reply_with_attachment(self):
        ticket = SupportTicket.objects.create(organization=self.org, created_by=self.user, subject='A')
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f'/api/support/tickets/{ticket.id}/messages/',
            {'body': 'Aquí está el fix', 'images': [_png_file()]},
            format='multipart',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data['attachments']), 1)

    def test_rejects_non_image_file(self):
        self.client.force_authenticate(user=self.user)
        fake = SimpleUploadedFile('note.txt', b'not an image', content_type='text/plain')
        response = self.client.post('/api/support/tickets/', {
            'subject': 'Error',
            'body': 'body',
            'images': [fake],
        }, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(SupportTicket.objects.count(), 0)

    def test_rejects_too_many_attachments(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/support/tickets/', {
            'subject': 'Error',
            'body': 'body',
            'images': [_png_file(f'{i}.png') for i in range(4)],
        }, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(SupportTicket.objects.count(), 0)

    def test_rejects_oversized_attachment(self):
        self.client.force_authenticate(user=self.user)
        buf = io.BytesIO()
        Image.new('RGB', (2500, 2500), color='blue').save(buf, format='PNG', compress_level=0)
        buf.seek(0)
        big = SimpleUploadedFile('big.png', buf.read(), content_type='image/png')
        self.assertGreater(big.size, 5 * 1024 * 1024)
        response = self.client.post('/api/support/tickets/', {
            'subject': 'Error',
            'body': 'body',
            'images': [big],
        }, format='multipart')
        self.assertEqual(response.status_code, 400)

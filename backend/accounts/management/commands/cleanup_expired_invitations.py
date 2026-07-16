"""Delete expired, never-accepted invitations so they don't accumulate forever."""
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Invitation


class Command(BaseCommand):
    help = 'Delete expired invitations that were never accepted.'

    def handle(self, *args, **options):
        deleted, _ = Invitation.objects.filter(
            accepted_by__isnull=True,
            expires_at__lt=timezone.now(),
        ).delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted} expired invitation(s).'))

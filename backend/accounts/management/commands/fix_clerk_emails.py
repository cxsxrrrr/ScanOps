import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Fix users with fake @clerk.user emails by fetching their real email from the Clerk API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would change without saving',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fake_users = User.objects.filter(email__endswith='@clerk.user')
        total = fake_users.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('No users with fake emails found.'))
            return

        self.stdout.write(f'Found {total} user(s) with @clerk.user email.\n')

        if not settings.CLERK_SECRET_KEY:
            self.stderr.write(self.style.ERROR(
                'CLERK_SECRET_KEY is not configured. Set it in .env to run this command.'
            ))
            return

        updated = 0
        failed = 0

        for user in fake_users:
            clerk_id = user.clerk_user_id
            if not clerk_id:
                self.stderr.write(self.style.WARNING(
                    f'  Skipping user {user.pk} ({user.email}): no clerk_user_id'
                ))
                failed += 1
                continue

            real_email = self._fetch_email_from_clerk(clerk_id)
            if not real_email:
                self.stderr.write(self.style.WARNING(
                    f'  Could not fetch email for {clerk_id}'
                ))
                failed += 1
                continue

            if dry_run:
                self.stdout.write(
                    f'  [DRY RUN] Would update user {user.pk}: {user.email} -> {real_email}'
                )
            else:
                user.email = real_email
                user.save(update_fields=['email'])
                self.stdout.write(self.style.SUCCESS(
                    f'  Updated user {user.pk}: {user.email} -> {real_email}'
                ))
            updated += 1

        self.stdout.write(f'\nDone: {updated} updated, {failed} failed out of {total} total.')

    @staticmethod
    def _fetch_email_from_clerk(clerk_user_id):
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
        except Exception:
            pass
        return None
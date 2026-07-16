"""Clerk Backend API helpers.

The session JWT Clerk issues doesn't always carry a real email claim (depends
on the JWT template configured in the Clerk dashboard), so some users end up
stored with the auto-generated placeholder email `{clerk_user_id}@clerk.user`
(see accounts.authentication.ClerkJWTAuthentication). This looks up the real
primary email from Clerk's Backend API for admin-panel display, and persists
it back onto the User row so the lookup only has to happen once per user.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

CLERK_API_BASE = 'https://api.clerk.com/v1'
PLACEHOLDER_SUFFIX = '@clerk.user'


def is_placeholder_email(email):
    return bool(email) and email.endswith(PLACEHOLDER_SUFFIX)


def backfill_real_emails(users):
    """For any user in `users` with a placeholder email, fetch and persist
    their real primary email from Clerk. Best-effort: network failures or a
    missing CLERK_SECRET_KEY silently leave the placeholder in place rather
    than breaking the admin panel.

    `users` — iterable of User instances (not a .values() queryset — we need
    real model instances to .save() the backfilled email).
    Returns the number of users updated.
    """
    if not settings.CLERK_SECRET_KEY:
        return 0

    targets = [u for u in users if is_placeholder_email(u.email) and u.clerk_user_id]
    if not targets:
        return 0

    try:
        resp = requests.get(
            f'{CLERK_API_BASE}/users',
            headers={'Authorization': f'Bearer {settings.CLERK_SECRET_KEY}'},
            params=[('user_id', u.clerk_user_id) for u in targets],
            timeout=5,
        )
        resp.raise_for_status()
        clerk_users = resp.json()
    except Exception as exc:
        logger.warning(f"Clerk Backend API lookup failed: {exc}")
        return 0

    email_by_clerk_id = {}
    for cu in clerk_users:
        primary_id = cu.get('primary_email_address_id')
        for addr in cu.get('email_addresses', []):
            if addr.get('id') == primary_id and addr.get('email_address'):
                email_by_clerk_id[cu['id']] = addr['email_address']
                break

    updated = 0
    for u in targets:
        real_email = email_by_clerk_id.get(u.clerk_user_id)
        if real_email and real_email != u.email:
            try:
                u.email = real_email
                u.save(update_fields=['email'])
                updated += 1
            except Exception as exc:
                # e.g. another user row already has this email — don't let
                # a single collision break the whole admin panel listing.
                logger.warning(f"Could not backfill email for {u.clerk_user_id}: {exc}")
    return updated

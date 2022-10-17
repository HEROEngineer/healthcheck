from __future__ import annotations

from django.conf import settings
from django.core import mail
from django.test.utils import override_settings

from hc.test import BaseTestCase


class ChangeEmailTestCase(BaseTestCase):
    def test_it_requires_sudo_mode(self):
        self.client.login(username="alice@example.org", password="password")

        r = self.client.get("/accounts/change_email/")
        self.assertContains(r, "We have sent a confirmation code")

    def test_it_shows_form(self):
        self.client.login(username="alice@example.org", password="password")
        self.set_sudo_flag()

        r = self.client.get("/accounts/change_email/")
        self.assertContains(r, "Change Account's Email Address")

    @override_settings(SITE_ROOT="http://testserver")
    def test_it_sends_link(self):
        self.client.login(username="alice@example.org", password="password")
        self.set_sudo_flag()

        payload = {"email": "alice2@example.org"}
        r = self.client.post("/accounts/change_email/", payload, follow=True)
        self.assertRedirects(r, "/accounts/change_email/")
        self.assertContains(r, "One Last Step")

        # The email addess should have not changed yet
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.email, "alice@example.org")
        self.assertTrue(self.alice.has_usable_password())

        # And email should have been sent
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, f"Log in to {settings.SITE_NAME}")
        html = message.alternatives[0][0]
        self.assertIn("http://testserver/accounts/change_email/", html)

    def test_it_requires_unique_email(self):
        self.client.login(username="alice@example.org", password="password")
        self.set_sudo_flag()

        payload = {"email": "bob@example.org"}
        r = self.client.post("/accounts/change_email/", payload)
        self.assertContains(r, "bob@example.org is already registered")

        self.alice.refresh_from_db()
        self.assertEqual(self.alice.email, "alice@example.org")

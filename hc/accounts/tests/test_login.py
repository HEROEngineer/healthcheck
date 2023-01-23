from __future__ import annotations

from django.conf import settings
from django.core import mail
from django.test.utils import override_settings

from hc.accounts.models import Credential
from hc.api.models import Check, TokenBucket
from hc.test import BaseTestCase


class LoginTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.checks_url = f"/projects/{self.project.code}/checks/"

    def test_it_shows_form(self):
        r = self.client.get("/accounts/login/")
        self.assertContains(r, "Email Me a Link")

    def test_it_redirects_authenticated_get(self):
        self.client.login(username="alice@example.org", password="password")

        r = self.client.get("/accounts/login/")
        self.assertRedirects(r, self.checks_url)

    @override_settings(SITE_ROOT="http://testserver", SITE_LOGO_URL=None)
    def test_it_sends_link(self):
        form = {"identity": "alice@example.org"}

        r = self.client.post("/accounts/login/", form)
        self.assertRedirects(r, "/accounts/login_link_sent/")

        # And email should have been sent
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, f"Log in to {settings.SITE_NAME}")
        html = message.alternatives[0][0]
        self.assertIn("http://testserver/static/img/logo.png", html)
        self.assertIn("http://testserver/docs/", html)

    @override_settings(SITE_LOGO_URL="https://example.org/logo.svg")
    def test_it_uses_custom_logo(self):
        self.client.post("/accounts/login/", {"identity": "alice@example.org"})
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn("https://example.org/logo.svg", html)

    def test_it_sends_link_with_next(self):
        form = {"identity": "alice@example.org"}

        r = self.client.post("/accounts/login/?next=" + self.channels_url, form)
        self.assertRedirects(r, "/accounts/login_link_sent/")
        self.assertIn("auto-login", r.cookies)

        # The check_token link should have a ?next= query parameter:
        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        self.assertTrue("/?next=" + self.channels_url in body)

    def test_it_handles_unknown_email(self):
        form = {"identity": "surprise@example.org"}

        r = self.client.post("/accounts/login/", form)
        self.assertRedirects(r, "/accounts/login_link_sent/")
        self.assertIn("auto-login", r.cookies)

        # There should be no sent emails.
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(SECRET_KEY="test-secret")
    def test_it_rate_limits_emails(self):
        # "d60d..." is sha1("alice@example.orgtest-secret")
        obj = TokenBucket(value="em-d60db3b2343e713a4de3e92d4eb417e4f05f06ab")
        obj.tokens = 0
        obj.save()

        form = {"identity": "alice@example.org"}

        r = self.client.post("/accounts/login/", form)
        self.assertContains(r, "Too many attempts")

        # No email should have been sent
        self.assertEqual(len(mail.outbox), 0)

    def test_it_rate_limits_client_ips(self):
        obj = TokenBucket(value="auth-ip-127.0.0.1")
        obj.tokens = 0
        obj.save()

        form = {"identity": "alice@example.org"}

        r = self.client.post("/accounts/login/", form)
        self.assertContains(r, "Too many attempts")

        # No email should have been sent
        self.assertEqual(len(mail.outbox), 0)

    def test_rate_limiter_uses_x_forwarded_for(self):
        obj = TokenBucket(value="auth-ip-127.0.0.2")
        obj.tokens = 0
        obj.save()

        form = {"identity": "alice@example.org"}
        xff = "127.0.0.2:1234,127.0.0.3"
        r = self.client.post("/accounts/login/", form, HTTP_X_FORWARDED_FOR=xff)
        self.assertContains(r, "Too many attempts")

        # No email should have been sent
        self.assertEqual(len(mail.outbox), 0)

    def test_it_pops_bad_link_from_session(self):
        self.client.session["bad_link"] = True
        self.client.get("/accounts/login/")
        assert "bad_link" not in self.client.session

    def test_it_ignores_case(self):
        form = {"identity": "ALICE@EXAMPLE.ORG"}

        r = self.client.post("/accounts/login/", form)
        self.assertRedirects(r, "/accounts/login_link_sent/")

        self.profile.refresh_from_db()
        self.assertTrue(self.profile.token)

    def test_it_handles_password(self):
        form = {"action": "login", "email": "alice@example.org", "password": "password"}

        r = self.client.post("/accounts/login/", form)
        self.assertRedirects(r, self.checks_url)

    @override_settings(SECRET_KEY="test-secret")
    def test_it_rate_limits_password_attempts(self):
        # "d60d..." is sha1("alice@example.orgtest-secret")
        obj = TokenBucket(value="pw-d60db3b2343e713a4de3e92d4eb417e4f05f06ab")
        obj.tokens = 0
        obj.save()

        form = {"action": "login", "email": "alice@example.org", "password": "password"}

        r = self.client.post("/accounts/login/", form)
        self.assertContains(r, "Too many attempts")

    def test_it_handles_password_login_with_redirect(self):
        check = Check.objects.create(project=self.project)

        form = {"action": "login", "email": "alice@example.org", "password": "password"}

        samples = [self.channels_url, "/checks/%s/details/" % check.code]

        for s in samples:
            r = self.client.post("/accounts/login/?next=%s" % s, form)
            self.assertRedirects(r, s)

    def test_it_handles_bad_next_parameter(self):
        form = {"action": "login", "email": "alice@example.org", "password": "password"}

        samples = [
            "/evil/",
            f"https://example.org/projects/{self.project.code}/checks/",
        ]

        for sample in samples:
            r = self.client.post("/accounts/login/?next=" + sample, form)
            self.assertRedirects(r, self.checks_url)

    def test_it_handles_wrong_password(self):
        form = {
            "action": "login",
            "email": "alice@example.org",
            "password": "wrong password",
        }

        r = self.client.post("/accounts/login/", form)
        self.assertContains(r, "Incorrect email or password")

    @override_settings(REGISTRATION_OPEN=False)
    def test_it_obeys_registration_open(self):
        r = self.client.get("/accounts/login/")
        self.assertNotContains(r, "Create Your Account")

    def test_it_redirects_to_webauthn_form(self):
        Credential.objects.create(user=self.alice, name="Alices Key")

        form = {"action": "login", "email": "alice@example.org", "password": "password"}
        r = self.client.post("/accounts/login/", form)
        self.assertRedirects(
            r, "/accounts/login/two_factor/", fetch_redirect_response=False
        )

        # It should not log the user in yet
        self.assertNotIn("_auth_user_id", self.client.session)

        # Instead, it should set 2fa_user_id in the session
        user_id, email, valid_until = self.client.session["2fa_user"]
        self.assertEqual(user_id, self.alice.id)

    def test_it_redirects_to_totp_form(self):
        self.profile.totp = "0" * 32
        self.profile.save()

        form = {"action": "login", "email": "alice@example.org", "password": "password"}
        r = self.client.post("/accounts/login/", form)
        self.assertRedirects(
            r, "/accounts/login/two_factor/totp/", fetch_redirect_response=False
        )

        # It should not log the user in yet
        self.assertNotIn("_auth_user_id", self.client.session)

        # Instead, it should set 2fa_user_id in the session
        user_id, email, valid_until = self.client.session["2fa_user"]
        self.assertEqual(user_id, self.alice.id)

    def test_it_handles_missing_profile(self):
        self.profile.delete()

        form = {"action": "login", "email": "alice@example.org", "password": "password"}

        r = self.client.post("/accounts/login/", form)
        self.assertRedirects(r, self.checks_url)

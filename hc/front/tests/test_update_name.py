from __future__ import annotations

from hc.api.models import Check
from hc.test import BaseTestCase


class UpdateNameTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.check = Check.objects.create(project=self.project)

        self.url = f"/checks/{self.check.code}/name/"
        self.redirect_url = f"/projects/{self.project.code}/checks/"

    def test_it_works(self):
        self.client.login(username="alice@example.org", password="password")
        r = self.client.post(self.url, data={"name": "Alice Was Here"})
        self.assertRedirects(r, self.redirect_url)

        self.check.refresh_from_db()
        self.assertEqual(self.check.name, "Alice Was Here")
        self.assertEqual(self.check.slug, "alice-was-here")

    def test_redirect_preserves_querystring(self):
        referer = self.redirect_url + "?tag=foo"

        self.client.login(username="alice@example.org", password="password")
        payload = {"name": "Alice Was Here"}
        r = self.client.post(self.url, data=payload, HTTP_REFERER=referer)
        self.assertRedirects(r, referer)

    def test_it_redirects_to_details(self):
        details_url = f"/checks/{self.check.code}/details/"
        self.client.login(username="alice@example.org", password="password")
        r = self.client.post(self.url, data={"name": "Hey"}, HTTP_REFERER=details_url)
        self.assertRedirects(r, details_url)

        self.check.refresh_from_db()
        self.assertEqual(self.check.name, "Hey")

    def test_team_access_works(self):
        payload = {"name": "Bob Was Here"}

        # Logging in as bob, not alice. Bob has team access so this
        # should work.
        self.client.login(username="bob@example.org", password="password")
        self.client.post(self.url, data=payload)

        self.check.refresh_from_db()
        self.assertEqual(self.check.name, "Bob Was Here")

    def test_it_allows_cross_team_access(self):
        self.client.login(username="bob@example.org", password="password")
        r = self.client.post(self.url, data={"name": "Bob Was Here"})
        self.assertRedirects(r, self.redirect_url)

    def test_it_checks_ownership(self):
        payload = {"name": "Charlie Sent This"}

        self.client.login(username="charlie@example.org", password="password")
        r = self.client.post(self.url, data=payload)
        self.assertEqual(r.status_code, 404)

    def test_it_requires_rw_access(self):
        self.bobs_membership.role = "r"
        self.bobs_membership.save()

        payload = {"name": "Charlie Sent This"}

        self.client.login(username="bob@example.org", password="password")
        r = self.client.post(self.url, data=payload)
        self.assertEqual(r.status_code, 403)

    def test_it_handles_bad_uuid(self):
        url = "/checks/not-uuid/name/"
        payload = {"name": "Alice Was Here"}

        self.client.login(username="alice@example.org", password="password")
        r = self.client.post(url, data=payload)
        self.assertEqual(r.status_code, 404)

    def test_it_handles_missing_uuid(self):
        # Valid UUID but there is no check for it:
        url = "/checks/6837d6ec-fc08-4da5-a67f-08a9ed1ccf62/name/"
        payload = {"name": "Alice Was Here"}

        self.client.login(username="alice@example.org", password="password")
        r = self.client.post(url, data=payload)
        self.assertEqual(r.status_code, 404)

    def test_it_sanitizes_tags(self):
        payload = {"tags": "  foo  bar\r\t \n  baz \n"}

        self.client.login(username="alice@example.org", password="password")
        self.client.post(self.url, data=payload)

        self.check.refresh_from_db()
        self.assertEqual(self.check.tags, "foo bar baz")

    def test_it_rejects_get(self):
        self.client.login(username="alice@example.org", password="password")
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 405)

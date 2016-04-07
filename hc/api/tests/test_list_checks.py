import json
from datetime import timedelta as td

from hc.api.models import Check, User
from hc.test import BaseTestCase
from hc.accounts.models import Profile

class ListChecksTestCase(BaseTestCase):

    def setUp(self):
        super(ListChecksTestCase, self).setUp()
        self.profile = Profile(user=self.alice, api_key="abc")
        self.profile.save()
        self.checks = [
            Check(user=self.alice, name="Alice 1", timeout=td(seconds=3600), grace=td(seconds=900)),
            Check(user=self.alice, name="Alice 2", timeout=td(seconds=86400), grace=td(seconds=3600)),
        ]
        for check in self.checks:
            check.save()

    def get(self, url, data):
        return self.client.generic('GET', url, json.dumps(data), 'application/json')

    def test_it_works(self):
        r = self.get("/api/v1/checks/", { "api_key": "abc" })

        self.assertEqual(r.status_code, 200)
        self.assertTrue("checks" in r.json())
        self.assertEqual(len(r.json()["checks"]), 2)

        checks = { check["name"]: check for check in r.json()["checks"] }
        self.assertEqual(checks["Alice 1"]["timeout"], 3600)
        self.assertEqual(checks["Alice 1"]["grace"],   900)
        self.assertEqual(checks["Alice 1"]["ping_url"],     self.checks[0].url())
        self.assertEqual(checks["Alice 2"]["timeout"], 86400)
        self.assertEqual(checks["Alice 2"]["grace"],   3600)
        self.assertEqual(checks["Alice 2"]["ping_url"],     self.checks[1].url())

    def test_it_shows_only_users_checks(self):
        bob = User(username="bob", email="bob@example.com")
        bob.save()
        bob_check = Check(user=bob, name="Bob 1")

        r = self.get("/api/v1/checks/", { "api_key": "abc" })

        self.assertEqual(len(r.json()["checks"]), 2)
        checks = { check["name"]: check for check in r.json()["checks"] }
        self.assertNotIn("Bob 1", checks)

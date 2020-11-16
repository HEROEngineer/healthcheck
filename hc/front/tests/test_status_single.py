from hc.api.models import Check, Ping
from hc.test import BaseTestCase


class StatusSingleTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.check = Check(project=self.project, name="Alice Was Here")
        self.check.save()

        self.url = "/checks/%s/status/" % self.check.code

    def test_it_works(self):
        self.client.login(username="alice@example.org", password="password")
        r = self.client.get(self.url)
        doc = r.json()

        self.assertEqual(doc["status"], "new")
        self.assertTrue("never received a ping" in doc["status_text"])
        self.assertTrue("not received any pings yet" in doc["events"])

    def test_it_returns_events(self):
        p = Ping.objects.create(owner=self.check, ua="test-user-agent", n=1)
        self.check.status = "up"
        self.check.last_ping = p.created
        self.check.save()

        self.client.login(username="alice@example.org", password="password")
        r = self.client.get(self.url)
        doc = r.json()

        self.assertEqual(doc["status"], "up")
        self.assertEqual(doc["updated"], str(p.created.timestamp()))
        self.assertTrue("test-user-agent" in doc["events"])

    def test_it_omits_events(self):
        p = Ping.objects.create(owner=self.check, ua="test-user-agent", n=1)
        self.check.status = "up"
        self.check.last_ping = p.created
        self.check.save()

        timestamp = str(p.created.timestamp())
        url = self.url + "?u=%s" % timestamp

        self.client.login(username="alice@example.org", password="password")
        r = self.client.get(url)
        doc = r.json()

        self.assertFalse("events" in doc)

    def test_it_allows_cross_team_access(self):
        self.client.login(username="bob@example.org", password="password")
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

    def test_it_handles_manual_resume(self):
        self.check.status = "paused"
        self.check.manual_resume = True
        self.check.save()

        self.client.login(username="alice@example.org", password="password")
        r = self.client.get(self.url)
        doc = r.json()

        self.assertEqual(doc["status"], "paused")
        self.assertIn("will ignore pings until resumed", doc["status_text"])
        self.assertIn("resume-btn", doc["status_text"])

    def test_resume_requires_rw_access(self):
        self.bobs_membership.rw = False
        self.bobs_membership.save()

        self.check.status = "paused"
        self.check.manual_resume = True
        self.check.save()

        self.client.login(username="bob@example.org", password="password")
        r = self.client.get(self.url)
        doc = r.json()

        self.assertEqual(doc["status"], "paused")
        self.assertIn("will ignore pings until resumed", doc["status_text"])
        self.assertNotIn("resume-btn", doc["status_text"])

from django.core import mail
from django.utils.timezone import now
from hc.api.models import Check
from hc.test import BaseTestCase


class TransferProjectTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()

        Check.objects.create(project=self.project)

        self.url = "/projects/%s/settings/" % self.project.code

    def test_transfer_project_works(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"transfer_project": "1", "email": "bob@example.org"}
        r = self.client.post(self.url, form)
        self.assertContains(r, "Transfer initiated!")

        self.bobs_membership.refresh_from_db()
        self.assertIsNotNone(self.bobs_membership.transfer_request_date)

        # Bob should receive an email notification
        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        self.assertTrue("/?next=" + self.url in body)

    def test_transfer_project_checks_ownership(self):
        self.client.login(username="bob@example.org", password="password")

        form = {"transfer_project": "1", "email": "bob@example.org"}
        r = self.client.post(self.url, form)
        self.assertEqual(r.status_code, 403)

    def test_transfer_project_checks_membership(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"transfer_project": "1", "email": "charlie@example.org"}
        r = self.client.post(self.url, form)
        self.assertEqual(r.status_code, 400)

    def test_cancel_works(self):
        self.bobs_membership.transfer_request_date = now()
        self.bobs_membership.save()

        self.client.login(username="alice@example.org", password="password")
        r = self.client.post(self.url, {"cancel_transfer": "1"})
        self.assertContains(r, "Transfer cancelled!")

        self.bobs_membership.refresh_from_db()
        self.assertIsNone(self.bobs_membership.transfer_request_date)

    def test_cancel_checks_ownership(self):
        self.bobs_membership.transfer_request_date = now()
        self.bobs_membership.save()

        self.client.login(username="bob@example.org", password="password")
        r = self.client.post(self.url, {"cancel_transfer": "1"})
        self.assertEqual(r.status_code, 403)

        self.bobs_membership.refresh_from_db()
        self.assertIsNotNone(self.bobs_membership.transfer_request_date)

    def test_it_shows_transfer_request(self):
        self.bobs_membership.transfer_request_date = now()
        self.bobs_membership.save()

        self.client.login(username="bob@example.org", password="password")
        r = self.client.get(self.url)
        self.assertContains(r, "would like to transfer")
        self.assertNotContains(r, "upgrade your account first")

    def test_it_shows_transfer_request_with_limit_notice(self):
        self.bobs_membership.transfer_request_date = now()
        self.bobs_membership.save()

        self.bobs_profile.check_limit = 0
        self.bobs_profile.save()

        self.client.login(username="bob@example.org", password="password")
        r = self.client.get(self.url)
        self.assertContains(r, "upgrade your account first")

    def test_accept_works(self):
        self.bobs_membership.transfer_request_date = now()
        self.bobs_membership.save()

        self.client.login(username="bob@example.org", password="password")
        r = self.client.post(self.url, {"accept_transfer": "1"})
        self.assertContains(r, "You are now the owner of this project!")

        self.project.refresh_from_db()
        # Bob should now be the owner
        self.assertEqual(self.project.owner, self.bob)

        # Alice, the previous owner, should now be a member
        self.assertTrue(self.project.team().filter(email="alice@example.org").exists())

    def test_accept_requires_a_transfer_request(self):
        self.client.login(username="bob@example.org", password="password")
        r = self.client.post(self.url, {"accept_transfer": "1"})
        self.assertEqual(r.status_code, 403)

        self.project.refresh_from_db()
        # Alice should still be the owner
        self.assertEqual(self.project.owner, self.alice)

    def test_only_the_proposed_owner_can_accept(self):
        self.bobs_membership.transfer_request_date = now()
        self.bobs_membership.save()

        self.client.login(username="alice@example.org", password="password")
        r = self.client.post(self.url, {"accept_transfer": "1"})
        self.assertEqual(r.status_code, 403)

    def test_it_checks_limits(self):
        self.bobs_membership.transfer_request_date = now()
        self.bobs_membership.save()

        self.bobs_profile.check_limit = 0
        self.bobs_profile.save()

        self.client.login(username="bob@example.org", password="password")
        r = self.client.post(self.url, {"accept_transfer": "1"})
        self.assertEqual(r.status_code, 400)

    def test_reject_works(self):
        self.bobs_membership.transfer_request_date = now()
        self.bobs_membership.save()

        self.client.login(username="bob@example.org", password="password")
        r = self.client.post(self.url, {"reject_transfer": "1"})
        self.assertEqual(r.status_code, 200)

        self.project.refresh_from_db()
        # Alice should still be the owner
        self.assertEqual(self.project.owner, self.alice)

        # The transfer_request_date should be cleared out
        self.bobs_membership.refresh_from_db()
        self.assertIsNone(self.bobs_membership.transfer_request_date)

    def test_only_the_proposed_owner_can_reject(self):
        self.bobs_membership.transfer_request_date = now()
        self.bobs_membership.save()

        self.client.login(username="alice@example.org", password="password")
        r = self.client.post(self.url, {"reject_transfer": "1"})
        self.assertEqual(r.status_code, 403)

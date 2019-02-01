from hc.test import BaseTestCase
from hc.api.models import Check


class BadgesTestCase(BaseTestCase):

    def test_it_shows_badges(self):
        Check.objects.create(project=self.project, tags="foo a-B_1  baz@")
        Check.objects.create(project=self.bobs_project, tags="bobs-tag")

        self.client.login(username="alice@example.org", password="password")
        r = self.client.get("/accounts/profile/badges/")
        self.assertContains(r, "foo.svg")
        self.assertContains(r, "a-B_1.svg")

        # Expect badge URLs only for tags that match \w+
        self.assertNotContains(r, "baz@.svg")

        # Expect only Alice's tags
        self.assertNotContains(r, "bobs-tag.svg")

    def test_it_uses_badge_key(self):
        Check.objects.create(project=self.project, tags="foo bar")
        Check.objects.create(project=self.bobs_project, tags="bobs-tag")

        self.project.badge_key = "alices-badge-key"
        self.project.save()

        self.client.login(username="alice@example.org", password="password")
        r = self.client.get("/accounts/profile/badges/")
        self.assertContains(r, "badge/alices-badge-key/")
        self.assertContains(r, "badge/alices-badge-key/")

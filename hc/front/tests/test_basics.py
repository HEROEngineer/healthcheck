from django.test import TestCase

from hc.api.models import Check


class BasicsTestCase(TestCase):

    def test_it_shows_welcome(self):
        r = self.client.get("/")
        self.assertContains(r, "Get Notified", status_code=200)

    def test_welcome_code(self):
        r = self.client.get("/")
        code = self.client.session["welcome_code"]
        assert Check.objects.filter(code=code).exists()

        self.client.session["welcome_code"] = "x"
        r = self.client.get("/")
        code = self.client.session["welcome_code"]
        assert r.status_code == 200
        assert code != "x"
        assert Check.objects.filter(code=code).exists()

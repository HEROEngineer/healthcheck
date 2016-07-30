import json

from hc.api.models import Channel
from hc.test import BaseTestCase
from mock import patch


class SlackCallbackTestCase(BaseTestCase):

    @patch("hc.front.views.requests.post")
    def test_it_works(self, mock_post):
        oauth_response = {
            "ok": True,
            "team_name": "foo",
            "incoming_webhook": {
                "url": "http://example.org",
                "channel": "bar"
            }
        }

        mock_post.return_value.text = json.dumps(oauth_response)
        mock_post.return_value.json.return_value = oauth_response

        url = "/integrations/add_slack_btn/?code=12345678"

        self.client.login(username="alice@example.org", password="password")
        r = self.client.get(url, follow=True)
        self.assertRedirects(r, "/integrations/")
        self.assertContains(r, "The Slack integration has been added!")

        ch = Channel.objects.get()
        self.assertEqual(ch.slack_team, "foo")
        self.assertEqual(ch.slack_channel, "bar")
        self.assertEqual(ch.slack_webhook_url, "http://example.org")

    @patch("hc.front.views.requests.post")
    def test_it_handles_error(self, mock_post):
        oauth_response = {
            "ok": False,
            "error": "something went wrong"
        }

        mock_post.return_value.text = json.dumps(oauth_response)
        mock_post.return_value.json.return_value = oauth_response

        url = "/integrations/add_slack_btn/?code=12345678"

        self.client.login(username="alice@example.org", password="password")
        r = self.client.get(url, follow=True)
        self.assertRedirects(r, "/integrations/")
        self.assertContains(r, "something went wrong")

# coding: utf-8

from __future__ import annotations

import json
from datetime import timedelta as td
from unittest.mock import patch

from django.test.utils import override_settings
from django.utils.timezone import now

from hc.api.models import Channel, Check, Notification, Ping
from hc.test import BaseTestCase


class NotifyMsTeamsTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.check = Check(project=self.project)
        self.check.status = "down"
        self.check.last_ping = now() - td(minutes=61)
        self.check.save()

        self.ping = Ping(owner=self.check)
        self.ping.created = now() - td(minutes=61)
        self.ping.save()

        self.channel = Channel(project=self.project)
        self.channel.kind = "msteams"
        self.channel.value = "http://example.com/webhook"
        self.channel.save()
        self.channel.checks.add(self.check)

    @patch("hc.api.transports.curl.request")
    def test_it_works(self, mock_post):
        mock_post.return_value.status_code = 200

        self.check.name = "_underscores_ & more"

        self.channel.notify(self.check)
        assert Notification.objects.count() == 1

        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        self.assertEqual(payload["@type"], "MessageCard")

        # summary and title should be the same, except
        # title should have any special HTML characters escaped
        self.assertEqual(payload["summary"], "“_underscores_ & more” is DOWN.")
        self.assertEqual(payload["title"], "“_underscores_ &amp; more” is DOWN.")

        facts = {f["name"]: f["value"] for f in payload["sections"][0]["facts"]}
        self.assertEqual(facts["Last Ping:"], "Success, an hour ago")

        # The payload should not contain check's code
        serialized = json.dumps(payload)
        self.assertNotIn(str(self.check.code), serialized)

    @patch("hc.api.transports.curl.request")
    def test_msteams_escapes_html_and_markdown_in_desc(self, mock_post):
        mock_post.return_value.status_code = 200

        self.check.desc = """
            TEST _underscore_ `backticks` <u>underline</u> \\backslash\\ "quoted"
        """

        self.channel.notify(self.check)

        args, kwargs = mock_post.call_args
        text = kwargs["json"]["sections"][0]["text"]

        self.assertIn(r"\_underscore\_", text)
        self.assertIn(r"\`backticks\`", text)
        self.assertIn("&lt;u&gt;underline&lt;/u&gt;", text)
        self.assertIn(r"\\backslash\\ ", text)
        self.assertIn("&quot;quoted&quot;", text)

    @override_settings(MSTEAMS_ENABLED=False)
    def test_it_requires_msteams_enabled(self):
        self.channel.notify(self.check)

        n = Notification.objects.get()
        self.assertEqual(n.error, "MS Teams notifications are not enabled.")

    @patch("hc.api.transports.curl.request")
    def test_it_handles_last_ping_fail(self, mock_post):
        mock_post.return_value.status_code = 200

        self.ping.kind = "fail"
        self.ping.save()

        self.channel.notify(self.check)
        assert Notification.objects.count() == 1

        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        facts = {f["name"]: f["value"] for f in payload["sections"][0]["facts"]}
        self.assertEqual(facts["Last Ping:"], "Failure, an hour ago")

    @patch("hc.api.transports.curl.request")
    def test_it_handles_last_ping_log(self, mock_post):
        mock_post.return_value.status_code = 200

        self.ping.kind = "log"
        self.ping.save()

        self.channel.notify(self.check)

        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        facts = {f["name"]: f["value"] for f in payload["sections"][0]["facts"]}
        self.assertEqual(facts["Last Ping:"], "Log, an hour ago")

    @patch("hc.api.transports.curl.request")
    def test_it_shows_ignored_nonzero_exitstatus(self, mock_post):
        mock_post.return_value.status_code = 200

        self.ping.kind = "ign"
        self.ping.exitstatus = 123
        self.ping.save()

        self.channel.notify(self.check)
        assert Notification.objects.count() == 1

        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        facts = {f["name"]: f["value"] for f in payload["sections"][0]["facts"]}
        self.assertEqual(facts["Last Ping:"], "Ignored, an hour ago")

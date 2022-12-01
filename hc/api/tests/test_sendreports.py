from __future__ import annotations

from datetime import date, datetime
from datetime import timedelta as td
from unittest.mock import Mock, patch

from django.core import mail
from django.test.utils import override_settings
from django.utils.timezone import now, utc

from hc.api.management.commands.sendreports import Command
from hc.api.models import Check
from hc.test import BaseTestCase

CURRENT_TIME = datetime(2020, 1, 13, 2, tzinfo=utc)
MOCK_NOW = Mock(return_value=CURRENT_TIME)


NAG_TEXT = """Hello,

This is a hourly reminder sent by Mychecks.

One check is currently DOWN.


Alices Project
==============

Status Name                                     Last Ping
------ ---------------------------------------- ----------------------
DOWN   Foo                                      now


--
Cheers,
Mychecks
"""


@override_settings(SITE_NAME="Mychecks")
@patch("hc.lib.date.timezone.now", MOCK_NOW)
@patch("hc.accounts.models.now", MOCK_NOW)
@patch("hc.api.management.commands.sendreports.timezone.now", MOCK_NOW)
class SendReportsTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()

        # Make alice eligible for a monthly report:
        self.profile.next_report_date = CURRENT_TIME - td(hours=1)
        # and for a nag
        self.profile.nag_period = td(hours=1)
        self.profile.next_nag_date = CURRENT_TIME - td(seconds=10)
        self.profile.save()

        # Disable bob's and charlie's monthly reports so they don't interfere
        self.bobs_profile.reports = "off"
        self.bobs_profile.save()

        self.charlies_profile.reports = "off"
        self.charlies_profile.save()

        # And it needs at least one check that has been pinged.
        self.check = Check(project=self.project, last_ping=now())
        self.check.name = "Foo"
        self.check.status = "down"
        self.check.save()

    def test_it_sends_monthly_report(self):
        cmd = Command(stdout=Mock())
        cmd.pause = Mock()  # don't pause for 1s

        found = cmd.handle_one_report()
        self.assertTrue(found)

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.next_report_date.date(), date(2020, 2, 1))
        self.assertEqual(self.profile.next_report_date.day, 1)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertTrue("List-Unsubscribe" in email.extra_headers)
        self.assertTrue("List-Unsubscribe-Post" in email.extra_headers)
        self.assertEqual(email.subject, "Monthly Report")
        self.assertIn("This is a monthly report", email.body)

        html = email.alternatives[0][0]
        self.assertIn("This is a monthly report", html)
        self.assertIn("Nov. 2019", html)
        self.assertIn("Dec. 2019", html)

    def test_it_sends_weekly_report(self):
        self.profile.reports = "weekly"
        self.profile.save()

        cmd = Command(stdout=Mock())
        cmd.pause = Mock()  # don't pause for 1s

        cmd.handle_one_report()

        email = mail.outbox[0]
        self.assertEqual(email.subject, "Weekly Report")
        self.assertIn("This is a weekly report", email.body)

        html = email.alternatives[0][0]
        self.assertIn("This is a weekly report", html)
        self.assertIn("Dec 30 - Jan 5", html)
        self.assertIn("Jan 6 - Jan 12", html)

    def test_it_handles_positive_utc_offset(self):
        self.profile.reports = "weekly"
        self.profile.tz = "America/New_York"
        self.profile.save()

        cmd = Command(stdout=Mock())
        cmd.pause = Mock()  # don't pause for 1s
        cmd.handle_one_report()

        email = mail.outbox[0]
        html = email.alternatives[0][0]
        # UTC:      Monday, Jan 13, 2AM.
        # New York: Sunday, Jan 12, 9PM.
        # The report should not contain the Jan 6 - Jan 12 week, because
        # in New York it is the current week.
        self.assertIn("Dec 23 - Dec 29", html)
        self.assertIn("Dec 30 - Jan 5", html)
        self.assertNotIn("Jan 6 - Jan 12", html)

    def test_it_handles_negative_utc_offset(self):
        self.profile.reports = "weekly"
        self.profile.tz = "Asia/Tokyo"
        self.profile.save()

        cmd = Command(stdout=Mock())
        cmd.pause = Mock()  # don't pause for 1s
        cmd.handle_one_report()

        email = mail.outbox[0]
        html = email.alternatives[0][0]
        # UTC:   Monday, Jan 13, 2AM.
        # Tokyo: Monday, Jan 13, 11AM
        self.assertNotIn("Dec 23 - Dec 29", html)
        self.assertIn("Dec 30 - Jan 5", html)
        self.assertIn("Jan 6 - Jan 12", html)

    def test_it_obeys_next_report_date(self):
        self.profile.next_report_date = CURRENT_TIME + td(days=1)
        self.profile.save()

        found = Command().handle_one_report()
        self.assertFalse(found)

    def test_it_fills_blank_next_monthly_report_date(self):
        self.profile.next_report_date = None
        self.profile.save()

        found = Command().handle_one_report()
        self.assertTrue(found)

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.next_report_date.date(), date(2020, 2, 1))
        self.assertEqual(len(mail.outbox), 0)

    def test_it_fills_blank_next_weekly_report_date(self):
        self.profile.reports = "weekly"
        self.profile.next_report_date = None
        self.profile.save()

        found = Command().handle_one_report()
        self.assertTrue(found)

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.next_report_date.date(), date(2020, 1, 20))
        self.assertEqual(len(mail.outbox), 0)

    def test_it_obeys_reports_off(self):
        self.profile.reports = "off"
        self.profile.save()

        found = Command().handle_one_report()
        self.assertFalse(found)

    def test_it_requires_pinged_checks(self):
        self.check.delete()

        found = Command().handle_one_report()
        self.assertTrue(found)

        # No email should have been sent:
        self.assertEqual(len(mail.outbox), 0)

    def test_it_sends_nag(self):
        cmd = Command(stdout=Mock())
        cmd.pause = Mock()  # don't pause for 1s

        found = cmd.handle_one_nag()
        self.assertTrue(found)

        self.profile.refresh_from_db()
        self.assertTrue(self.profile.next_nag_date > CURRENT_TIME)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        html = email.alternatives[0][0]
        self.assertNotIn(str(self.check.code), email.body)
        self.assertNotIn(str(self.check.code), html)

        self.assertEqual(email.body, NAG_TEXT)

    def test_it_obeys_next_nag_date(self):
        self.profile.next_nag_date = CURRENT_TIME + td(days=1)
        self.profile.save()

        # If next_nag_date is in future, a nag should not get sent.
        found = Command().handle_one_nag()
        self.assertFalse(found)

    def test_it_obeys_nag_period(self):
        self.profile.nag_period = td()
        self.profile.save()

        # If nag_period is 0 ("disabled"), a nag should not get sent.
        found = Command().handle_one_nag()
        self.assertFalse(found)

    def test_nags_require_down_checks(self):
        self.check.status = "up"
        self.check.save()

        found = Command().handle_one_nag()
        self.assertTrue(found)

        # No email should have been sent:
        self.assertEqual(len(mail.outbox), 0)

        # next_nag_date should now be unset
        self.profile.refresh_from_db()
        self.assertIsNone(self.profile.next_nag_date)

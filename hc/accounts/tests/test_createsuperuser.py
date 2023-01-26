from __future__ import annotations

from unittest.mock import Mock, patch

from django.contrib.auth.models import User

from hc.accounts.management.commands.createsuperuser import Command
from hc.test import BaseTestCase


class CreateSuperuserTestCase(BaseTestCase):
    def test_it_works(self):
        cmd = Command(stdout=Mock())
        with patch(cmd.__module__ + ".input") as mock_input:
            with patch(cmd.__module__ + ".getpass") as mock_getpass:
                mock_input.return_value = "superuser@example.org"
                mock_getpass.return_value = "hunter2"
                cmd.handle()

        u = User.objects.get(email="superuser@example.org")
        self.assertTrue(u.is_superuser)

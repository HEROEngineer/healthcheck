from django.contrib.auth.models import User
from django.test import TestCase
from hc.payments.models import Subscription
from mock import Mock, patch


class InvoiceTestCase(TestCase):

    def setUp(self):
        self.alice = User(username="alice", email="alice@example.org")
        self.alice.set_password("password")
        self.alice.save()

        self.sub = Subscription(user=self.alice)
        self.sub.subscription_id = "test-id"
        self.sub.customer_id = "test-customer-id"
        self.sub.save()

    @patch("hc.payments.views.braintree")
    def test_it_works(self, mock_braintree):

        tx = Mock()
        tx.id = "abc123"
        tx.customer_details.id = "test-customer-id"
        tx.created_at = None
        mock_braintree.Transaction.find.return_value = tx

        self.client.login(username="alice@example.org", password="password")
        r = self.client.get("/invoice/abc123/")
        self.assertContains(r, "ABC123")  # tx.id in uppercase

    @patch("hc.payments.views.braintree")
    def test_it_checks_customer_id(self, mock_braintree):

        tx = Mock()
        tx.id = "abc123"
        tx.customer_details.id = "test-another-customer-id"
        tx.created_at = None
        mock_braintree.Transaction.find.return_value = tx

        self.client.login(username="alice@example.org", password="password")
        r = self.client.get("/invoice/abc123/")
        self.assertEqual(r.status_code, 403)

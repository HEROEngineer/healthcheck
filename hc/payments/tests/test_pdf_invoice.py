from mock import Mock, patch

from django.utils.timezone import now
from hc.payments.models import Subscription
from hc.test import BaseTestCase
import six


class PdfInvoiceTestCase(BaseTestCase):

    def setUp(self):
        super(PdfInvoiceTestCase, self).setUp()
        self.sub = Subscription(user=self.alice)
        self.sub.subscription_id = "test-id"
        self.sub.customer_id = "test-customer-id"
        self.sub.save()

        self.tx = Mock()
        self.tx.id = "abc123"
        self.tx.customer_details.id = "test-customer-id"
        self.tx.created_at = now()
        self.tx.currency_iso_code = "USD"
        self.tx.amount = 5
        self.tx.subscription_details.billing_period_start_date = now()
        self.tx.subscription_details.billing_period_end_date = now()

    @patch("hc.payments.views.braintree")
    def test_it_works(self, mock_braintree):

        mock_braintree.Transaction.find.return_value = self.tx

        self.client.login(username="alice@example.org", password="password")
        r = self.client.get("/invoice/pdf/abc123/")
        self.assertTrue(six.b("ABC123") in r.content)
        self.assertTrue(six.b("alice@example.org") in r.content)

    @patch("hc.payments.views.braintree")
    def test_it_checks_customer_id(self, mock_braintree):

        tx = Mock()
        tx.id = "abc123"
        tx.customer_details.id = "test-another-customer-id"
        tx.created_at = None
        mock_braintree.Transaction.find.return_value = tx

        self.client.login(username="alice@example.org", password="password")
        r = self.client.get("/invoice/pdf/abc123/")
        self.assertEqual(r.status_code, 403)

    @patch("hc.payments.views.braintree")
    def test_it_shows_company_data(self, mock_braintree):
        self.profile.bill_to = "Alice and Partners"
        self.profile.save()

        mock_braintree.Transaction.find.return_value = self.tx

        self.client.login(username="alice@example.org", password="password")
        r = self.client.get("/invoice/pdf/abc123/")
        self.assertTrue(six.b("Alice and Partners") in r.content)

from django.urls import path

from . import views

urlpatterns = [
    path('pricing/',
         views.pricing,
         name="hc-pricing"),

    path('accounts/profile/billing/',
         views.billing,
         name="hc-billing"),

    path('accounts/profile/billing/history/',
         views.billing_history,
         name="hc-billing-history"),

    path('accounts/profile/billing/address/',
         views.address,
         name="hc-billing-address"),

    path('accounts/profile/billing/payment_method/',
         views.payment_method,
         name="hc-payment-method"),

    path('invoice/pdf/<slug:transaction_id>/',
         views.pdf_invoice,
         name="hc-invoice-pdf"),

    path('pricing/set_plan/',
         views.set_plan,
         name="hc-set-plan"),

    path('pricing/get_client_token/',
         views.get_client_token,
         name="hc-get-client-token"),

    path('pricing/charge/', views.charge_webhook),
]

from django.conf.urls import url

from hc.api import views

urlpatterns = [
    url(r'^ping/([\w-]+)/$', views.ping, name="hc-ping-slash"),
    url(r'^ping/([\w-]+)$', views.ping, name="hc-ping"),
    url(r'^api/v1/checks/$', views.create_check),
    url(r'^badge/([\w-]+)/([\w-]{8})/([\w-]+).svg$', views.badge, name="hc-badge"),
]

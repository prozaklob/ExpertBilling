from django.conf.urls import patterns, url
from views import PayView

urlpatterns = patterns('',
    url(r'^ru-sberbank/payment/$', PayView.as_view(), name='getpaid-rusberbank-pay'),
)

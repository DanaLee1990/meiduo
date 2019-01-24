from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^orders/(?P<order_id>\d+)/$',views.PaymentView.as_view(),name='pay'),
    url(r'^status/$', views.PaymentStatusView.as_view(), name='paystatus'),

]
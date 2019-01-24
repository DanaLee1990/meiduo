from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^places/$',views.OrderSettlementView.as_view()),
    url(r'^$', views.OrderView.as_view()),
]


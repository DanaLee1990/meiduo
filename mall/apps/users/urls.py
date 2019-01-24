from django.conf.urls import url
from . import views
from rest_framework_jwt.views import obtain_jwt_token
from apps.users.views import LoginMergeView

urlpatterns = [
    url(r'^usernames/(?P<username>\w{5,20})/count/$', views.RegisterUsernameAPIView.as_view(), name='username'),
    url(r'^phones/(?P<mobile>1[345789]\d{9})/count/$', views.RegisterMobileAPIView.as_view(), name='nobile'),
    url(r'^$', views.RegisterUsersAPIView.as_view(),name='register'),

    # url(r'^auths/$', obtain_jwt_token,name='auth'),
    url(r'^auths/$', LoginMergeView.as_view(), name='auth'),

    url(r'^infos/$',views.UserDetailView.as_view()),
    url(r'^emails/$',views.UserEmailView.as_view()),
    url(r'^emails/verification/$',views.VerificationEmailView.as_view()),
    url(r'^addresses/$', views.AddressView.as_view()),
    url(r'^addresses/list/$', views.AddressListView.as_view()),
    url(r'^addresses/(?P<addr_id>\d+)/$', views.AddressManageAPIView.as_view()),
    url(r'^addresses/setdefault/(?P<addr_id>\d+)/status/$', views.AddressSetDefaultAPIView.as_view()),
    url(r'^addresses/(?P<addr_id>\d+)/title/$', views.AddressSetTitleAPIView.as_view()),
    url(r'^browserhistories/$', views.UserBrowsingHistoryView.as_view()),
    url(r'^change_password/$', views.ChangePasswordView.as_view()),

]


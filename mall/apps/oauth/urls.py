from django.conf.urls import url
from .views import OAuthQQURLAPIView,QQAuthUserView

urlpatterns = [
    url(r'^qq/statues/$', OAuthQQURLAPIView.as_view()),
    url(r'^qq/users/$', QQAuthUserView.as_view()),

]
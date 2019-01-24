from django.conf.urls import url
from .views import RegisterImageAPIView,RegisterSmsCodeAPIView

urlpatterns = [
    url(r'^image/(?P<image_code_id>.+)/$', RegisterImageAPIView.as_view(), name='image'),
    url(r'^smscodes/(?P<mobile>1[35789]\d{9})/$',RegisterSmsCodeAPIView.as_view(),name='smscode'),

]
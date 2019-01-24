from django.conf.urls import url
from areas.views import AreasViewSet
from rest_framework.routers import DefaultRouter


urlpatterns = [

]

router = DefaultRouter()
router.register(r'infos',AreasViewSet,base_name='area')
urlpatterns += router.urls

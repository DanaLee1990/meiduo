from django.shortcuts import render
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from .serializers import SKUSerializer
from .models import SKU
from rest_framework_extensions.cache.mixins import ListCacheResponseMixin

# Create your views here.

"""
热销商品
请求方式　ＧＥＴ
请求路由　/goods/categories/(?P<category_id>\d+)/hotskus/
视图　　　ＬｉｓｔＡＰＩＶｉｅｗ

"""


class HotSKUListView(ListCacheResponseMixin, ListAPIView):

    serializer_class = SKUSerializer
    pagination_class = None

    def get_queryset(self):
        category_id = self.kwargs['category_id']
        return SKU.objects.filter(category_id=category_id,is_launched=True).order_by('-sales')[:2]


class SKUListView(ListAPIView):
    """
    商品列表数据
    GET /goods/categories/(?P<category_id>\d+)/skus/?page=xxx&page_size=xxx&ordering=xxx
    """

    serializer_class = SKUSerializer
    # 通过定义过滤后端 ，来实行排序行为
    filter_backends = [OrderingFilter]
    ordering_fields = ('create_time', 'price', 'sales')

    def get_queryset(self):
        categroy_id = self.kwargs.get("category_id")
        return SKU.objects.filter(category_id=categroy_id, is_launched=True)


from .serializers import SKUIndexSerializer
from drf_haystack.viewsets import HaystackViewSet

class SKUSearchViewSet(HaystackViewSet):
    """
    SKU搜索
    """
    index_models = [SKU]

    serializer_class = SKUIndexSerializer



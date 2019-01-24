from decimal import Decimal
from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from goods.models import SKU
from orders.serializers import OrderSettlementSerializer, OrderCommitSerializer
from rest_framework.generics import CreateAPIView

# Create your views here.


"""
用户点击去结算  跳转到place_order 页面

获取已选择的商品列表
请求方式 ： GET /orders/places/


"""


class OrderSettlementView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self,request):
        """ 订单结算实现 """
        user = request.user

        # 登陆用户，可以直接从redis中获取数据
        redis_conn = get_redis_connection('cart')
        redis_cart = redis_conn.hgetall('cart_%s'%user.id)
        redis_sku_selected = redis_conn.smembers('cart_selected_%s'%user.id)
        # 将已经被选择的商品的数据重组成一个字典{sku_id:count,sku_id:count,...}
        cart = {}
        for sku_id in redis_sku_selected:
            cart[int(sku_id)]=int(redis_cart[sku_id])

        # 根据redis中取出的sku_id查询商品
        ids = cart.keys()
        skus = SKU.objects.filter(pk__in=ids)
        # 给每一个商品动态添加count这个属性
        for sku in skus:
            sku.count = cart[sku.id]

        # 运费
        freight = Decimal('10.00')
        # 将数据进行序列化操作
        serializer = OrderSettlementSerializer({'freight':freight,'skus':skus})

        return Response(serializer.data)


class OrderView(CreateAPIView):
    """ 保存订单 必须是登陆用户才可以访问此接口 """
    permission_classes = [IsAuthenticated]

    serializer_class = OrderCommitSerializer

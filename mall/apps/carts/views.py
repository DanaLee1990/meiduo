import base64
import pickle
from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from carts.serializers import CartSerializer, CartSKUSerializer, CartDeleteSerializer
from goods.models import SKU

# Create your views here.


class CartView(APIView):
    """
    购物车

    POST /cart/  添加商品到购物车
    """
    def perform_authentication(self, request):
        """
        重写父类的用户验证方法，不在进入视图就检查JWT

        """

        pass

    def post(self,request):
        """
        思路：
        1、接收数据，进行校验
        2、获取商品id，count 和商品是否被选中的信息
        3、判断用户是否为登陆用户
            3.1 如果是登陆用户，就把数据保存到redis中
            3.2 如果不是登陆用户，就把数据保存到cookie中

        """
        # 接收数据
        data = request.data
        # 校验数据
        ser = CartSerializer(data=data)
        ser.is_valid(raise_exception=True)
        # 获取商品id count 和商品是否被选中的信息
        sku_id = ser.validated_data.get('sku_id')
        count = ser.validated_data.get('count')
        selected = ser.data.get('selected')
        # 判断用户是否为登陆用户
        try:
            user = request.user
        except Exception:
            user = None

        if user is not None and user.is_authenticated:
            # 如果用户存在，将购物车数据保存到redis
            redis_conn = get_redis_connection('cart')
            # 存到redis中的数据格式  hash 键：card_用户_id 值：{sku_id:count,sku_id:count}
            #  set  键： card_selected_用户_id  值：{sku_id,sku_id}
            # 先获取到之前的数据，然后再进行累加操作
            # redis_conn.hset('cart_%s'%user.id,sku_id,count)
            # redis_conn.hincrby('cart_%s'%user.id,sku_id,count)
            # if selected:
            #     redis_conn.sadd('cart_selected_%s'%user.id,sku_id)
            # 创建管道
            p1 = redis_conn.pipeline()
            # 将指令缓存到管道中
            p1.hincrby('cart_%s'%user.id,sku_id,count)
            if selected:
                p1.sadd('cart_selected_%s'%user.id,sku_id)
            # 执行指令
            p1.execute()
            # 返回响应
            return Response(ser.data)
        else:
            # 如果用户不存在，将购物车数据保存到Cookie中  {sku_id:{count:selected}}
            # 接收cookie
            cart_str = request.COOKIES.get('cart')
            if cart_str is not None:
                cart_dic = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dic = {}
            if sku_id in cart_dic:
                count_origin = cart_dic[sku_id]['count']
                count += count_origin
            cart_dic[sku_id]={
                'count':count,
                'selected':selected
            }
            # 设置cookie数据
            cookie_cart = base64.b64encode(pickle.dumps(cart_dic)).decode()
            response = Response(ser.data)
            response.set_cookie('cart',cookie_cart)
            return response

    def get(self,request):
        """
        根据用户是否存在，查询购物车信息
        如果用户存在  从redis中获取数据
        如果用户不存在  从cookie中获取数据

        """
        try:
            user = request.user
        except Exception:
            user = None
        if user is not None and user.is_authenticated:
            # 连接redis数据库
            redis_conn = get_redis_connection('cart')
            # 从redis数据库中获取购物车数据 redis_cart: sku_id count  redis_cart_selected: sku_id
            redis_cart = redis_conn.hgetall('cart_%s'%user.id)
            redis_cart_selected = redis_conn.smembers('cart_selected_%s'%user.id)
            cart = {}
            # 为了便于对商品的查询，把从redis中取出的数据的结构与cookie中取出的数据结构保持一致
            # cookie中的数据结构   {sku_id:{count:selected}}
            for sku_id,count in redis_cart.items():
                cart[int(sku_id)]={
                        'count':int(count),
                        'selected':sku_id in redis_cart_selected
                }


        else:
            # 从cookie中取出数据
            cart_cookie = request.COOKIES.get('cart')
            if cart_cookie:
                # 将取出的数据解码
                cart = pickle.loads(base64.b64decode(cart_cookie.encode()))
            else:
                cart = {}

        skus = SKU.objects.filter(pk__in=cart.keys())
        # 因为原来的模型中并没有 count字段和slected字段，所以需要给模型对象动态的添加这两个属性
        for sku in skus:
            sku.count=cart[sku.id]['count']
            sku.selected=cart[sku.id]['selected']
        # 将查询到的模型对象进行序列化操作
        serializer = CartSKUSerializer(skus,many=True)
        # 返回响应
        return Response(serializer.data)

    def put(self,request):
        """
        修改购物车

        """
        # 接收参数 校验参数
        cart_str = request.data
        serializer = CartSerializer(data=cart_str)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')
        # 判断用户是否存在
        try:
            user = request.user
        except Exception:
            user = None
        if user is not None and user.is_authenticated:
            # 用户存在
            redis_conn = get_redis_connection('cart')
            redis_conn.hset('cart_%s'%user.id,sku_id,count)
            if selected:
                redis_conn.sadd('cart_selected_%s'%user.id,sku_id)
            else:
                redis_conn.srem('cart_selected_%s'%user.id,sku_id)
            return Response(serializer.data)
        else:
            # 用户不存在
            # 从cookie中获取数据
            cart_cookie = request.COOKIES.get('cart')
            if cart_cookie:
                cart = pickle.loads(base64.b64decode(cart_cookie.encode()))
            else:
                cart = {}
            if sku_id in cart:
                cart[sku_id]={
                    'count':count,
                    'selected':selected
                }
            cart_str = base64.b64encode(pickle.dumps(cart)).decode()
            response = Response(serializer.data)
            response.set_cookie('cart',cart_str)
            return response

    def delete(self,request):
        """
        删除购物车商品

        """
        cart_str = request.data
        serializer = CartDeleteSerializer(data=cart_str)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')
        try:
            user = request.user
        except Exception:
            user = None
        if user is not None and user.is_authenticated:
            redis_conn = get_redis_connection('cart')
            redis_conn.hdel('cart_%s'%user.id,sku_id)
            redis_conn.srem('cart_selected_%s'%user.id,sku_id)
            return Response({'msg':'删除成功'},status=status.HTTP_204_NO_CONTENT)
        else:
            cart_cookie = request.COOKIES.get('cart')
            if cart_cookie:
                cart = pickle.loads(base64.b64decode(cart_cookie.encode()))
            else:
                cart = {}
            if sku_id in cart:
                del cart[sku_id]
            cart_cook = base64.b64encode(pickle.dumps(cart)).decode()
            response = Response(serializer.data)
            response.set_cookie('cart',cart_cook)
            return response


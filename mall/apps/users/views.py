from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework import status

from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from goods.models import SKU
from users.models import User, Address
from rest_framework.response import Response

# Create your views here.

# 验证用户名是否存在
class RegisterUsernameAPIView(APIView):
    def get(self,request,username):
        count = User.objects.filter(username=username).count()
        return Response({'count':count})


# 验证手机号是否存在
class RegisterMobileAPIView(APIView):
    def get(self,request,mobile):
        count = User.objects.filter(mobile=mobile).count()
        return Response({'count':count})

# 注册 视图
"""
1、明确需求
2、明确请求方式   请求路由
3、明确用哪一种视图
4、按步骤进行开发
"""
"""
1、需求， 用户点击注册，需要将参数
username password password2 mobile smscode is_allow 传递给后端
2、请求方式  POST
   请求路由 /users/
3、使用
4、具体步骤
    # 接收参数
    # 检验参数
    # 数据入库
    # 返回响应
"""
from .serializers import RegisterUsersSerializer, UserDetailSerializer


class RegisterUsersAPIView(APIView):
    def post(self,request):
        # 接收参数
        data = request.data
        # 检验参数
        serializer = RegisterUsersSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # 数据入库
        serializer.save()
        # 返回响应
        return Response(serializer.data)

"""
个人中心
需求分析：必须是已经登陆的用户才可以进入用户中心
前端需要传递用户的信息
"""


# 用户详情视图
class UserDetailView(RetrieveAPIView):
    # 添加权限   只允许认证过的用户访问此视图
    permission_classes = [IsAuthenticated]
    serializer_class = UserDetailSerializer
    # 因为没有传入id值，而三级视图RetrieveAPIView获取单个的用户需要pk值，
    # 所以需要重写  get_object 方法
    # 在类视图对象中也保存了请求对象request
    # request对象的user属性是通过认证检验之后的请求用户对象

    def get_object(self):
        return self.request.user


# 设置邮箱 视图   保存邮箱号到数据库

"""
需求分析：　必须是应经认证登陆过的用户　　因为是在用户中心
        用户点击　按钮　保存　将用户的邮箱号保存到数据库中
请求方式　ＰＵＴ　　请求路由　users/emails/
确定视图　三级视图　CreateAPIView
按步骤开发
    　接收参数
    　校验参数
    　数据入库
    　返回响应

"""
from .serializers import UserEmailSerialzer


class UserEmailView(UpdateAPIView):
    """
    保存邮箱
    """
    # 此视图　只允许认证用户访问
    permission_classes = [IsAuthenticated]

    serializer_class = UserEmailSerialzer

    def get_object(self):
        """ 重写获取单个用户的方法　"""
        return self.request.user



    """
    激活邮箱
    请求方式　GET  users/emails/verification/?token=xxx
    接收ｔｏｋｅｎ
    验证ｔｏｋｅｎ，获取user_id
    查询用户信息
    改变邮箱激活状态
    返回响应
    """


class VerificationEmailView(APIView):

    def get(self,request):
        data = request.query_params
        token = data.get('token')
        if token is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        from users.utils import check_token
        user_id = check_token(token)
        if user_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(pk=user_id)
        user.email_active = True
        user.save()
        return Response({'msg':'ok'})

from rest_framework.generics import CreateAPIView
from .serializers import AddressSerializer


class AddressView(CreateAPIView):
    """
    需求分析：　　新增收货地址
    明确要干什么　　　接收用户输入的地址信息，并保存到数据库
    请求方式　　ＰＯＳＴ
    请求路由　　/users/addresses/
    使用的视图：CreateAPIView
    按步骤进行开发：
        接收参数
        校验参数
        数据入库
        返回响应
    """
    # 添加用户权限
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer
    # 因为是新增数据所以  不需要设置　queryset


class AddressListView(APIView):
    """
    收货地址列表视图　查询该用户的所有收货地址
    请求方式　　　ＧＥＴ
    请求路由　　　users/addresses/list/
    类视图　　　　APIView
    按照步骤进行开发
    """

    # 添加权限
    permission_classes = [IsAuthenticated]

    def get(self,request):
        user = request.user
        addrs = Address.objects.filter(user_id=user.id).all()
        ser = AddressSerializer(instance=addrs,many=True)
        data = {
            'user_id':user.id,
            'default_address_id':user.default_address_id,
            'limit':20,
            'addresses':ser.data,
        }
        return Response(data)


class AddressManageAPIView(APIView):

    # 加权限
    permission_classes = [IsAuthenticated]
    """ 删除地址视图 """
    def delete(self,request,addr_id):
        addr = Address.objects.get(id=addr_id)
        addr.delete()
        return Response({'msg':'删除成功'})

    """ 修改地址 """
    def put(self, request, addr_id):
        data = request.data
        addr = Address.objects.get(id=addr_id)
        ser = AddressSerializer(instance=addr,data=data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)


class AddressSetDefaultAPIView(APIView):

    # 加权限
    permission_classes = [IsAuthenticated]
    def put(self,request,addr_id):
        user = request.user
        user.default_address_id = addr_id
        user.save()
        return Response({'msg':'设置默认地址成功'})


class AddressSetTitleAPIView(APIView):
    """　保存标题信息　"""

    # 加权限
    permission_classes = [IsAuthenticated]
    def put(self,request,addr_id):
        title = request.data['title']
        addr = Address.objects.get(id=addr_id)
        addr.title = title
        addr.save()
        return Response({'msg':'保存标题成功'})


"""
用户浏览历史记录：保存浏览记录到redis
后端接口设计：
请求方式：POST
请求路由： /users/browerhistories/
"""
from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from .serializers import AddUserBrowsingHistorySerializer


class UserBrowsingHistoryView(mixins.CreateModelMixin,GenericAPIView):
    serializer_class = AddUserBrowsingHistorySerializer
    permission_classes = [IsAuthenticated]

    def post(self,request):
        """ 保存 """
        return self.create(request)

    def get(self,request):
        """ 获取浏览记录 """
        user_id = request.user.id
        # 连接redis
        redis_conn = get_redis_connection('history')
        # 获取数据
        history_sku_ids = redis_conn.lrange('history_%s'%user_id,0,5)
        skus = []
        for sku_id in history_sku_ids:
            sku = SKU.objects.get(pk=sku_id)
            skus.append(sku)
        # 序列化
        from goods.serializers import SKUSerializer
        serializer = SKUSerializer(skus,many=True)
        return Response(serializer.data)


from rest_framework_jwt.views import ObtainJSONWebToken
class LoginMergeView(ObtainJSONWebToken):
    """
    登陆后合并购物车
    """
    def post(self, request,*args,**kwargs):

        response = super().post(request,*args,**kwargs)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.object.get('user') or request.user
            # user = serializer.validated_data.get("user")
            from carts.utils import merge_cookie_to_redis
            response = merge_cookie_to_redis(request,user,response)

        return response


"""
修改密码
接收参数：user_id  old_password   new_password
请求方式 POST
请求路由  users/change_password
视图   一级视图  APIView
"""


class ChangePasswordView(APIView):
    """ 修改用户密码 """
    # 认证用户 才能访问此接口
    permission_classes = [IsAuthenticated]

    def post(self,request):
        user = request.user
        data = request.data
        old_password = data.get('old_password')
        new_password = data.get('new_password')

        if user.check_password(old_password):
            user.password=new_password
            user.set_password(new_password)
            user.save()
        return Response({'msg':'密码修改成功'},status=status.HTTP_200_OK)

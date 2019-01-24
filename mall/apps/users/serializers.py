import re
from django_redis import get_redis_connection
from rest_framework import serializers

from goods.models import SKU
from users.models import User, Address


class RegisterUsersSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(label='校验密码', allow_null=False, allow_blank=False, write_only=True)
    sms_code = serializers.CharField(label='短信验证码', max_length=6, min_length=6, allow_null=False, allow_blank=False,
                                     write_only=True)
    allow = serializers.CharField(label='是否同意协议', allow_null=False, allow_blank=False, write_only=True)
    token = serializers.CharField(label='登录状态token', read_only=True)  # 增加token字段

    # 我们添加的三个字段只是用于验证, 不应该入库, 所以我们应该在他们入库前删除,
    # 入库的时候调用create方法, 于是我们重写create方法
    def create(self, validated_data):

        # 删除多余字段
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']

        # 方式一　user = User.objects.create(**validated_data)
        user = super().create(validated_data)
        # 修改密码
        user.set_password(validated_data['password'])
        user.save()

        from rest_framework_jwt.settings import api_settings
        # 补充生成记录登录状态的token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        user.token = token

        return user

    class Meta:
        model = User
        """
        ModelSerializer自生成字段的原理：
        它会对fields进行遍历，如果模型中有相应的字段，会自动生成，
        如果没有，会查看当前类有没有自己实现
        """
        fields = ['id','username','password','password2','sms_code','allow','mobile','token']
        extra_kwargs = {
            'id': {'read_only': True},
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }

    # 单个字段的校验有 手机号码,是否同意协议
    def validate_mobile(self, value):
        if not re.match(r'1[345789]\d{9}', value):
            raise serializers.ValidationError('手机号格式不正确')
        return value

    def validate_allow(self, value):
        # 注意,前端提交的是否同意,我们已经转换为字符串
        if value != 'true':
            raise serializers.ValidationError('您未同意协议')
        return value

    # 多字段校验, 密码是否一致, 短信是否一致
    def validate(self, attrs):

        # 比较密码
        password = attrs['password']
        password2 = attrs['password2']

        if password != password2:
            raise serializers.ValidationError('密码不一致')
        # 比较手机验证码
        # 获取用户提交的验证码
        code = attrs['sms_code']
        # 连接redis数据库
        redis_conn = get_redis_connection('code')
        # 获取手机号码
        mobile = attrs['mobile']
        # 获取redis中的验证码
        redis_code = redis_conn.get('sms_%s' % mobile)
        if redis_code is None:
            raise serializers.ValidationError('验证码过期')

        if redis_code.decode() != code:
            raise serializers.ValidationError('验证码不正确')

        return attrs


class UserDetailSerializer(serializers.ModelSerializer):
    """
    用户详情信息 序列化器
    """
    class Meta:
        model = User
        fields = ['id','username','email','email_active','mobile']


class UserEmailSerialzer(serializers.ModelSerializer):
    """
    邮箱序列化器
    """
    class Meta:
        model = User
        fields = ['id','email']
        extra_kwargs = {
            'email':{
                'required':True
            }
        }

    def update(self, instance, validated_data):
        email = validated_data['email']
        instance.email = email
        instance.save()

        from users.utils import generate_verify_email_url
        # 生成邮箱验证ｕｒｌ
        verify_url = generate_verify_email_url(instance.id,email)
        # 导入celery_tasks中的　发送邮件的方法
        from celery_tasks.email.tasks import send_verify_mail
        send_verify_mail.delay(email,verify_url)
        return instance


class AddressSerializer(serializers.ModelSerializer):

    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='省ID', required=True)
    city_id = serializers.IntegerField(label='市ID', required=True)
    district_id = serializers.IntegerField(label='区ID', required=True)
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')

    class Meta:
        model = Address
        exclude = ('user', 'is_deleted', 'create_time', 'update_time')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AddUserBrowsingHistorySerializer(serializers.Serializer):
    """ 添加用户浏览记录序列化器 """
    sku_id = serializers.IntegerField(label='商品编号',min_value=1,required=True)

    def validate_sku_id(self,value):
        """ 检查商品是否存在 """
        try:
            SKU.objects.get(pk=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')
        return value

    def create(self, validated_data):
        """ 保存至redis数据库 """

        # 获取用户信息
        user_id = self.context['request'].user.id
        sku_id = validated_data['sku_id']
        # 链接redis数据库
        redis_conn = get_redis_connection('history')
        # 移除已经存在的本记录
        redis_conn.lrem('history_%s'%user_id, 0, sku_id)
        # 添加新的记录
        redis_conn.lpush('history_%s'%user_id,sku_id)
        # 保存最多5条记录
        redis_conn.ltrim('history_%s'%user_id,0,4)

        return validated_data

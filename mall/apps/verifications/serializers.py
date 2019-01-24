

from rest_framework import serializers
from django_redis import get_redis_connection


# # 短信验证码 序列化器
# class RegisterSmsCodeSerializer(serializers.Serializer):
#
#     # 需要校验的数据   mobile  image_code   image_code_id
#     text = serializers.CharField(label='用户输入的验证码', max_length=4,min_length=4,required=True)
#     image_code_id = serializers.UUIDField(label='验证码唯一id',required=True)
#
#     def validate(self, attrs):
#         text = attrs['text']
#         image_code_id = attrs['image_code_id']
#         # 连接redis数据库
#         redis_conn = get_redis_connection('code')
#         # 从数据库中取出存好的 验证码
#         redis_text = redis_conn.get('img_'+str(image_code_id))   # 因为接收到的image_code_id是UUID类型，所以需要将它强转为str类型
#         # 校验  验证码是否已经过期
#         if not redis_text:
#             return serializers.ValidationError('验证码已经过期')
#         # 比较用户输入的验证码与保存的验证码是否相等    从redis数据库中取出的数据是二进制bytes类型，所以需要decode()
#         if text.lower() != redis_text.decode().lower():
#             return serializers.ValidationError('验证码输入有误')
#         return attrs


# 序列化器第二遍
"""
短信验证码 序列化器的实现思路
1、设置验证码的字段类型和属性   text  image_code_id
2、使用 validate() 函数进行校验
2.1 、从 attrs 中取出用户输入的 参数 text image_code_id
2.2 、连接redis数据库，从redis数据库中取出存好的 text 的值
2.3 、将用户输入的值与redis数据库中的值进行比对
2.4 、返回attrs
"""
class RegisterSmsCodeSerializer(serializers.Serializer):

    text = serializers.CharField(label='用户输入的图片验证码', max_length=4, min_length=4, required=True)
    image_code_id = serializers.UUIDField(label='图片验证码的唯一id', required=True)

    def validate(self, attrs):
        text = attrs['text']
        image_code_id = attrs['image_code_id']
        redis_conn = get_redis_connection('code')
        redis_text = redis_conn.get('img_'+str(image_code_id))
        if not redis_text:
            return serializers.ValidationError('图片验证码已经过期')
        if text.lower() != redis_text.decode().lower():
            return serializers.ValidationError('图片验证码输入有误')
        return attrs
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView

# Create your views here.


# 发送图片验证码


"""
1、明确需求
2、梳理思路
3、确定请求方式 和 路由   GET  verifications/imagecodes/(?P<image_code_id>.+)/
4、确定视图
5、按步骤进行开发


"""


# 1、接收参数
# 2、生成图片验证码
# 3、保存验证码到redis
# 4、返回图片验证码
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django.http import HttpResponse


# 返回图片验证码
class RegisterImageAPIView(APIView):
    def get(self, request, image_code_id):
        # 生成图片验证码
        text, image = captcha.generate_captcha()
        # 链接redis 数据库
        redis_conn = get_redis_connection('code')
        # 将 验证码 保存到指定的redis数据库
        redis_conn.setex('img_'+image_code_id,60,text)
        # 返回图片验证码
        return HttpResponse(image,content_type='image/jpeg')


# 发送手机验证码
"""
1、明确需求（知道要干什么）
2、请求方式  路由           verifications/smscode/(?P<mobile>1[35789]\d{9})/?text=xxx&image_code_id=xxx
3、确定用什么视图
4、按步骤开发
"""

# 校验参数
# 生成手机短信验证码
# 返回响应


import random
from .serializers import RegisterSmsCodeSerializer
from libs.yuntongxun.sms import CCP


class RegisterSmsCodeAPIView(APIView):
    def get(self,request,mobile):
        # 1、使用序列化器校验数据
        serializer = RegisterSmsCodeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        # 2、生成短信验证码
        sms_code = '%06d'%random.randint(0,999999)
        print(sms_code)
        # 3、将生成的短信验证码保存到redis数据库中
        redis_conn = get_redis_connection('code')
        redis_conn.setex('sms_'+mobile,5*60,sms_code)
        # 4、发送短信验证码
        # ccp = CCP()
        # ccp.send_template_sms(mobile,[sms_code,5],1)
        # 4.1、实现异步任务
        # from celery_tasks.sms.tasks import send_sms_code
        # # delay() 方法的参数 和任务（函数）的参数保持一致
        # send_sms_code.delay(mobile,sms_code)
        # 5、返回响应
        return Response({'msg': 'OK'})


















from django.db import models
from utils.models import BaseModel

# Create your models here.


"""
此处定义QQ身份（openid）与用户模型类User的关联关系
"""

class OAuthQQUser(BaseModel):
    """
    QQ登陆用户数据
    """
    user = models.ForeignKey('users.User', on_delete=models.CASCADE,verbose_name='用户')
    openid = models.CharField(max_length=64, unique=True, verbose_name='openid', db_index=True)

    class Meta:
        db_table = 'tb_oauth_qq'
        verbose_name = 'QQ登陆用户数据'
        verbose_name_plural = verbose_name

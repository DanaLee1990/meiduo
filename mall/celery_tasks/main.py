
import os
from celery import Celery


"""
1、celery
2、任务   创建任务文件夹   任务文件名必须是tasks
3、broker   中间人
4、worker
"""

# # 1.1 、第一种方式   ---加载当前工程的配置信息
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mall.settings")

# # 1.2、第二种方式   ---加载当前工程的配置信息
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'mall.settings'

# 2、创建一个celery 实例对象
# 参数main是指异步任务路径  一般就是设置 文件夹的名字（路径）   相当于给他起个名字
app = Celery('celery_tasks')


# 3、让celery 加载配置broker的配置文件config文件
# 设置config的路径就可以
app.config_from_object('celery_tasks.config')


# 4、celery会自动检测到tasks中的任务
# 自动检测的任务存放在一个列表中
# 列表中的元素；任务的包路径
app.autodiscover_tasks(['celery_tasks.sms','celery_tasks.email','celery_tasks.html'])



# worker
# 我们需要在虚拟环境中执行以下指令
# celery -A celery的实例对象文件路径 worker -l info
# celery -A celery_tasks.main worker -l info





























"""
任务：
    1、就是普通函数
    2、该函数必须通过celery的实例对象的tasks装饰其装饰
    3、该任务需要让celery实例对象自动检测
    4、任务（函数）需要使用任务名（函数名）.delay() 进行调用
"""
from libs.yuntongxun.sms import CCP
from celery_tasks.main import app


@app.task
def send_sms_code(mobile,sms_code):
    ccp = CCP()
    ccp.send_template_sms(mobile, [sms_code, 5], 1)

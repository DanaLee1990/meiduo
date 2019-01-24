from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from mall import settings
from itsdangerous import BadSignature


def generate_verify_email_url(user_id,email):
    data = {
        'user_id': user_id,
        'email': email
    }
    s = Serializer(settings.SECRET_KEY, 3600)
    token = s.dumps(data)
    verify_url = 'http://www.meiduo.site:8080/success_verify_email.html?token=' + token.decode()  # 指定编码格式
    return verify_url


def check_token(token):
    s = Serializer(settings.SECRET_KEY,3600)
    try:
        token = s.loads(token)
    except BadSignature:
        return None

    user_id = token.get('user_id')
    return user_id

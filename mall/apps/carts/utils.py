import base64
import pickle

from django_redis import get_redis_connection


def merge_cookie_to_redis(request,user,response):
    """
    将cookie中的购物车数据，合并到redis中

    :param request:
    :param user:
    :param response:
    :return:
    """
    cart_cookie = request.COOKIES.get('cart')
    if cart_cookie is not None:
        cart_dic = pickle.loads(base64.b64decode(cart_cookie))

        # 获取redis中的购物车数据
        redis_conn = get_redis_connection('cart')
        cart_sku_count = redis_conn.hgetall('cart_%s'%user.id)
        cart = {}
        for sku_id,count in cart_sku_count.items():
            cart[int(sku_id)] = int(count)

        sku_id_selected_ls = []
        # 获取cookie中的购物车数据
        for sku_id,cookie_count_selected in cart_dic.items():
            # 合并数据  redis中有就覆盖  没有就增加
            cart[sku_id] = cookie_count_selected['count']

            # 将被勾选的cookie中的sku_id，添加到指定空列表
            if cookie_count_selected['selected']:
                sku_id_selected_ls.append(sku_id)

        # 将cart 与 sku_id 保存到redis中
        redis_conn.hmset('cart_%s'%user.id,cart)
        if len(sku_id_selected_ls)>0:
            redis_conn.sadd('cart_selected_%s'%user.id,*sku_id_selected_ls)

        # 删除原来的cookie
        response.delete_cookie('cart')
        return response
    else:
        return response

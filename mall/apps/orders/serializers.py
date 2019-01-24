from decimal import Decimal
from django.utils import timezone
from django_redis import get_redis_connection
from rest_framework import serializers
from django.db import transaction
from goods.models import SKU
from orders.models import OrderInfo, OrderGoods


class CartSKUSerializer(serializers.ModelSerializer):
    """
    购物车商品数据序列化器
    """
    count = serializers.IntegerField(label='数量')

    class Meta:
        model = SKU
        fields = ('id', 'name', 'default_image_url', 'price', 'count')


class OrderSettlementSerializer(serializers.Serializer):
    """
    订单结算数据序列化器
    """
    freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)
    skus = CartSKUSerializer(many=True)


class OrderCommitSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderInfo
        fields = ('order_id', 'address', 'pay_method')
        read_only_fields = ('order_id',)
        extra_kwargs = {
            'address': {
                'write_only': True,
                'required': True,
            },
            'pay_method': {
                'write_only': True,
                'required': True
            }
        }

    def create(self, validated_data):
        # 获取当前下单的用户
        user = self.context['request'].user
        # 生成订单号
        order_id = timezone.now().strftime('%Y%m%d%H%m%s') + '%06d'%user.id
        # 保存订单基本信息数据 OrderInfo
        address = validated_data['address']
        pay_method = validated_data['pay_method']
        import time
        time.sleep(6)
        with transaction.atomic():
            # 创建原点，如果发生异常则回滚到这里
            save_id = transaction.savepoint()
            try:
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal('0'),
                    freight=Decimal('10.0'),
                    pay_method=pay_method,
                    status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'] if pay_method==OrderInfo.PAY_METHODS_ENUM['CASH'] else OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                )
                # 从redis中获取购物车结算商品数据
                redis_conn = get_redis_connection('cart')
                redis_sku_count = redis_conn.hgetall('cart_%s'%user.id)
                redis_sku_id = redis_conn.smembers('cart_selected_%s'%user.id)
                cart = {}
                for sku_id in redis_sku_id:
                    cart[int(sku_id)]=int(redis_sku_count[sku_id])
                sku_ids = cart.keys()
                # 遍历结算商品：

                for sku_id in sku_ids:
                    # 出现对同一个商品进行争抢下单时，如果失败，再次尝试，直到库存不足
                    while True:
                        sku = SKU.objects.get(pk=sku_id)
                        count_redis = cart[sku_id]
                        if count_redis>sku.stock:
                            # 创建回滚点  发生异常则回滚到指定的原点
                            transaction.savepoint_rollback(save_id)
                            raise serializers.ValidationError('库存不足')
                        # # 判断商品库存是否充足
                        # sku.stock -= count_redis
                        # # 减少商品库存 增加商品销量
                        # sku.sales += count_redis
                        # sku.save()
                        # 使用乐观锁解决并发问题
                        old_stock = sku.stock
                        old_sales = sku.sales
                        new_stock = old_stock - count_redis
                        new_sales = old_sales + count_redis
                        result = SKU.objects.filter(id=sku.id,stock=old_stock).update(stock=new_stock,sales=new_sales)
                        if result==0:
                            continue
                        # 保存订单商品数据
                        order.total_count += count_redis
                        order.total_amount += (sku.price*count_redis)
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=count_redis,
                            price=sku.price
                        )
                        break
                order.save()
            except ValueError:
                raise
            except Exception:
                transaction.savepoint_rollback(save_id)
                raise serializers.ValidationError('下单失败')
            # 如果没有发生异常，则提交事务
            transaction.savepoint_commit(save_id)
            # 在redis购物车中删除已计算商品的数据
            pl = redis_conn.pipeline()
            pl.hdel('cart_%s' % user.id, *redis_sku_id)
            pl.srem('cart_selected_%s' % user.id, *redis_sku_id)
            pl.execute()

            # 返回响应
            return order


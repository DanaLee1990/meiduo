
from rest_framework import serializers

from goods.models import SKU


class CartSerializer(serializers.Serializer):

    sku_id = serializers.IntegerField(label='sku_id', required=True, min_value=1)

    count = serializers.IntegerField(label='商品数量', required=True, min_value=1)
    selected = serializers.BooleanField(label='是否被选中',required=False,default=True)

    def validate(self, attrs):

        # 判断商品是否存在
        sku_id = attrs['sku_id']
        try:
            sku = SKU.objects.get(pk=sku_id)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')

        # 判断库存是否充足
        count = attrs['count']
        if sku.stock<count:
            raise serializers.ValidationError('库存不足')

        return attrs


class CartSKUSerializer(serializers.ModelSerializer):

    count = serializers.IntegerField(label='购买商品的数量',required=True)
    selected = serializers.BooleanField(label='商品是否被选中',required=True)

    class Meta:
        model = SKU
        fields = ('id', 'count', 'name', 'default_image_url', 'price', 'selected')


class CartDeleteSerializer(serializers.Serializer):

    sku_id = serializers.IntegerField(label='sku_id',required=True)

    def validate(self, attrs):
        sku_id = attrs['sku_id']
        try:
            """ 判断商品是否存在 """
            SKU.objects.get(pk=sku_id)
        except Exception:
            raise serializers.ValidationError('商品不存在')

        return attrs

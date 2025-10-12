from rest_framework import serializers
from .models import Warehouse, StockItem

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta: model = Warehouse; fields = ['id','name','location','created_at','updated_at']

class StockItemSerializer(serializers.ModelSerializer):
    class Meta: model = StockItem; fields = ['id','product','warehouse','quantity','created_at','updated_at']

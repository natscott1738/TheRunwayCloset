from rest_framework import viewsets
from utils.permissions import InventoryPermission
from .models import Warehouse, StockItem
from .serializers import WarehouseSerializer, StockItemSerializer

class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all().order_by('name')
    serializer_class = WarehouseSerializer
    permission_classes = [InventoryPermission]

class StockItemViewSet(viewsets.ModelViewSet):
    queryset = StockItem.objects.select_related('product', 'warehouse')
    serializer_class = StockItemSerializer
    permission_classes = [InventoryPermission]
    filterset_fields = ['product', 'warehouse']

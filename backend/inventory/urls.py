from rest_framework.routers import DefaultRouter
from .views import WarehouseViewSet, StockItemViewSet
router = DefaultRouter()
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'stock-items', StockItemViewSet, basename='stockitem')
urlpatterns = router.urls

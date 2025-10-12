from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryViewSet, ProductImageViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'product-images', ProductImageViewSet, basename='product-image')

urlpatterns = router.urls

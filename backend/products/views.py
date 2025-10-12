from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Product, Category, ProductImage
from .serializers import ProductSerializer, CategorySerializer, ProductImageSerializer
from utils.permissions import ProductPermission, IsSellerOrAdmin

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['slug', 'name']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().select_related('category', 'seller').order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [ProductPermission]
    filterset_fields = ['category', 'is_published', 'currency']
    search_fields = ['title', 'description', 'slug']
    ordering_fields = ['created_at', 'price', 'title']

    def perform_create(self, serializer):
        # seller becomes owner of product
        serializer.save(seller=self.request.user)


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all().select_related('product')
    serializer_class = ProductImageSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [ProductPermission]
    filterset_fields = ['product']

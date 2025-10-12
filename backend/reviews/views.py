from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import Review
from .serializers import ReviewSerializer
from utils.permissions import IsOwnerOrAdmin

class ReviewViewSet(viewsets.ModelViewSet):
    """
    Provides: list, retrieve, create, update, partial_update, destroy
    - Read: anyone
    - Create: authenticated users
    - Update/Delete: only owner or staff
    """
    serializer_class = ReviewSerializer # ensures only owners/staff can edit/delete
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['product', 'user']
    search_fields = ['comment']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']

    # use select_related for performance (avoid N+1)
    queryset = Review.objects.select_related('product', 'user').all()

    def perform_create(self, serializer):
        # ensure created review is attached to request.user
        # serializer.create() also handles race conditions in your serializer
        serializer.save(user=self.request.user)

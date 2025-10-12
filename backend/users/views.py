from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CustomUser
from .serializers import UserSerializer, RegisterSerializer
from utils.permissions import IsSellerOrAdmin, IsSelfOrSellerOrAdmin

class UserViewSet(viewsets.ModelViewSet):
    """
    Handles:
    - list/retrieve users (seller/admin only for list; seller/admin retrieve any; customer retrieve own)
    - registration (anyone)
    - me (authenticated)
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        # registration endpoint (custom action)
        if self.action == "register":
            return [permissions.AllowAny()]
        # me endpoint
        if self.action == "me":
            return [permissions.IsAuthenticated()]
        # listing users: only sellers/admins
        if self.action == "list":
            return [IsSellerOrAdmin()]
        # retrieve: customers may retrieve own profile, sellers/admin can retrieve any
        if self.action == "retrieve":
            return [IsSelfOrSellerOrAdmin()]
        # default: require authentication and admin for unsafe ops
        return [permissions.IsAuthenticated(), IsSellerOrAdmin()]
        # Note: create() is handled by register() action above to allow open registration.

    @action(detail=False, methods=['post'], url_path='register', permission_classes=[permissions.AllowAny])
    def register(self, request):
        """
        Register a new user. Role is now respected from payload.
        """
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='me', permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """
        Get currently logged-in user's profile.
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

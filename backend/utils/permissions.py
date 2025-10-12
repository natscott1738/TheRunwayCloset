# utils/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS


def _is_staff(user):
    return bool(user and getattr(user, "is_staff", False))


def _role(user):
    return getattr(user, "role", None)


class IsAdmin(BasePermission):
    """Only staff/admin users."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and _is_staff(request.user))


class IsSeller(BasePermission):
    """Only seller users (or staff)."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (_is_staff(request.user) or _role(request.user) == "seller"))


class IsCustomer(BasePermission):
    """Only customer users."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and _role(request.user) == "customer")


class IsAdminOrReadOnly(BasePermission):
    """Staff can do anything; others can only read (GET, HEAD, OPTIONS)."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and _is_staff(request.user))


class IsSellerOrAdmin(BasePermission):
    """Allow sellers and staff (used when sellers or admins should have full access)."""
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (_is_staff(user) or _role(user) in ("seller", "admin", "superadmin")))


class IsSelfOrSellerOrAdmin(BasePermission):
    """
    Object-level permission for User objects:
    - Admins / sellers can view any user
    - A user may retrieve/update their own profile
    """
    def has_permission(self, request, view):
        # allow access to authenticated users for object-level checks; listing handled elsewhere
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if _is_staff(user) or _role(user) in ("seller", "admin", "superadmin"):
            return True
        # owner of the user object
        return obj == user

class IsSellerOrAdminOrReadOnly(BasePermission):
    """Sellers/Admins full CRUD; others (customers/anon) read-only."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and (_is_staff(user) or _role(user) in ("seller", "admin", "superadmin")))


class IsOwnerOrAdmin(BasePermission):
    """
    Generic object-level permission: owners (obj.user/obj.owner/obj.seller) or staff/admin can edit.
    Safe methods allowed for all authenticated users if caller wants to allow reads — caller may combine with other checks.
    """
    def has_permission(self, request, view):
        # require authentication
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if _is_staff(user) or _role(user) in ("admin", "superadmin"):
            return True
        owner = getattr(obj, "user", None) or getattr(obj, "owner", None) or getattr(obj, "seller", None)
        return owner == user


#
# Resource specific composite permissions
#


class ProductPermission(BasePermission):
    """
    Products:
      - SAFE_METHODS: allow any (public list/retrieve)
      - CREATE/UPDATE/DELETE: allowed for sellers (only their own objects) and admins
    Object-level:
      - sellers can modify only their own products (obj.seller == user)
      - admins/staff can modify any
    """
    def has_permission(self, request, view):
        # allow read to anyone (list/retrieve)
        if request.method in SAFE_METHODS:
            return True

        # must be authenticated and either seller or admin/staff
        user = request.user
        return bool(user and user.is_authenticated and (_is_staff(user) or _role(user) == "seller"))

    def has_object_permission(self, request, view, obj):
        # Read allowed to everyone
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if _is_staff(user) or _role(user) in ("admin", "superadmin"):
            return True
        return getattr(obj, "seller", None) == user


class OrderPermission(BasePermission):
    """
    Orders:
      - Customer: can POST (create) and SAFE_METHODS (list/retrieve) but only their own objects
      - Seller: can list/retrieve ALL orders (read-only)
      - Admin (staff): full access
    Object-level:
      - Customer: only owner (order.user) may access/modify their own order
      - Seller: read-only; cannot modify orders (unless admin)
    """
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False

        role = _role(user)
        # admin/staff: full access
        if _is_staff(user) or role in ("admin", "superadmin"):
            return True

        # seller: read-only access (list/retrieve)
        if role == "seller":
            return request.method in SAFE_METHODS

        # customer: create and read allowed
        if role == "customer":
            return request.method in SAFE_METHODS or request.method == "POST"

        # default deny
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        role = _role(user)

        # admin/staff can do anything
        if _is_staff(user) or role in ("admin", "superadmin"):
            return True

        # seller: only read
        if role == "seller":
            return request.method in SAFE_METHODS

        # customer: only owner can access (read or modify)
        if role == "customer":
            return getattr(obj, "user", None) == user

        return False


class PaymentPermission(BasePermission):
    """
    Payments:
      - Customer: can list/retrieve only their payments (SAFE_METHODS). Payment creation handled by dedicated endpoints.
      - Seller: can view (read-only) payments (for all orders).
      - Admin: full CRUD.
    """
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False

        if _is_staff(user) or _role(user) in ("admin", "superadmin"):
            return True

        if _role(user) == "seller":
            # sellers: read-only
            return request.method in SAFE_METHODS

        if _role(user) == "customer":
            # customers: read-only through this viewset; creation via MPesa/Bank endpoints
            return request.method in SAFE_METHODS

        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        if _is_staff(user) or _role(user) in ("admin", "superadmin"):
            return True
        if _role(user) == "seller":
            return request.method in SAFE_METHODS
        if _role(user) == "customer":
            return getattr(obj, "order", None) and getattr(obj.order, "user", None) == user
        return False


class InventoryPermission(BasePermission):
    """
    Inventory:
      - Customer: NO access
      - Seller: full CRUD on their own inventory items (owner/seller attribute)
      - Admin: full CRUD on all inventory items
    """
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False

        if _is_staff(user) or _role(user) in ("admin", "superadmin"):
            return True

        if _role(user) == "seller":
            return True

        # customers: no access
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        if _is_staff(user) or _role(user) in ("admin", "superadmin"):
            return True
        if _role(user) == "seller":
            owner = getattr(obj, "seller", None) or getattr(obj, "owner", None) or getattr(obj, "user", None)
            return owner == user
        return False

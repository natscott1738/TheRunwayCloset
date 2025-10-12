# payments/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentViewSet,
    MPesaSTKInitiateView,
    MPesaCallbackView,
    BankInitiateView,
)

app_name = "payments"

router = DefaultRouter()
router.register(r"payments", PaymentViewSet, basename="payment")

urlpatterns = [
    # M-Pesa endpoints
    path("mpesa/stk/initiate/", MPesaSTKInitiateView.as_view(), name="mpesa_initiate"),
    path("mpesa/stk/callback/", MPesaCallbackView.as_view(), name="mpesa_callback"),

    # Bank endpoints
    path("bank/initiate/", BankInitiateView.as_view(), name="bank_initiate"),

    # Default viewset (list/retrieve)
    path("", include(router.urls)),
]

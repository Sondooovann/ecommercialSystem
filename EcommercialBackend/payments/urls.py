from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, PaymentMethodView, PaymentWebhookView


urlpatterns = [
    path('payment-methods/', PaymentMethodView.as_view(), name='payment-methods'),
    path('webhook/<str:provider>/', PaymentWebhookView.as_view(), name='payment-webhook'),
]

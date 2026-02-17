from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet, ContactMessageViewSet, PaisViewSet,
    SyncPaisesView, MeView, PortafolioViewSet
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"contact-messages", ContactMessageViewSet, basename="contactmessage")
router.register(r"paises", PaisViewSet, basename="pais")
router.register(r"portafolios", PortafolioViewSet, basename="portafolio")  # ✅ ESTA LÍNEA

urlpatterns = [
    path("", include(router.urls)),
    path("sync/paises/", SyncPaisesView.as_view(), name="sync-paises"),
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
]
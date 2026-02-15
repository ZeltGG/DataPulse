from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, ContactMessageViewSet, PaisViewSet

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"contact-messages", ContactMessageViewSet, basename="contactmessage")
router.register(r"paises", PaisViewSet, basename="pais")

urlpatterns = [
    path("", include(router.urls)),
]
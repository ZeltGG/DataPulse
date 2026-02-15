from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, ContactMessageViewSet

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"contact-messages", ContactMessageViewSet, basename="contactmessage")

urlpatterns = router.urls
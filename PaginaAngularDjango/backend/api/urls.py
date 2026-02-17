from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AlertaViewSet,
    DashboardMapaView,
    DashboardResumenView,
    DashboardTendenciasView,
    EmailOrUsernameTokenObtainPairView,
    MeView,
    PaisViewSet,
    PortafolioViewSet,
    RegisterView,
    RiesgoCalcularView,
    RiesgoDetailView,
    RiesgoHistoricoView,
    RiesgoRankingView,
    SyncIndicadoresView,
    SyncPaisesView,
)

router = DefaultRouter()
router.register(r'paises', PaisViewSet, basename='pais')
router.register(r'portafolios', PortafolioViewSet, basename='portafolio')
router.register(r'alertas', AlertaViewSet, basename='alerta')

urlpatterns = [
    path('sync/paises/', SyncPaisesView.as_view(), name='sync-paises'),
    path('paises/sync-indicadores/', SyncIndicadoresView.as_view(), name='sync-indicadores'),
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', EmailOrUsernameTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
    path('riesgo/calcular/', RiesgoCalcularView.as_view(), name='riesgo-calcular'),
    path('riesgo/', RiesgoRankingView.as_view(), name='riesgo-ranking'),
    path('riesgo/<str:codigo_iso>/', RiesgoDetailView.as_view(), name='riesgo-detail'),
    path('riesgo/<str:codigo_iso>/historico/', RiesgoHistoricoView.as_view(), name='riesgo-historico'),
    path('dashboard/resumen/', DashboardResumenView.as_view(), name='dashboard-resumen'),
    path('dashboard/mapa/', DashboardMapaView.as_view(), name='dashboard-mapa'),
    path('dashboard/tendencias/', DashboardTendenciasView.as_view(), name='dashboard-tendencias'),
    path('', include(router.urls)),
]

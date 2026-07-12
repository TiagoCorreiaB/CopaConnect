from rest_framework.routers import DefaultRouter
from bolao.views import BolaoModelViewSet, PalpiteModelViewSet
from partidas.views import PartidaReadOnlyModelViewSet

router = DefaultRouter()

router.register(r'boloes', BolaoModelViewSet, basename='bolao')
router.register(r'palpites', PalpiteModelViewSet, basename='palpites')
router.register(r'partidas', PartidaReadOnlyModelViewSet, basename='partidas')

urlpatterns = router.urls
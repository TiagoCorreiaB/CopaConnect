from rest_framework.routers import DefaultRouter
from bolao.views import BolaoModelViewSet, PalpiteModelViewSet
from partidas.views import PartidaReadOnlyModelViewSet
from usuarios.views import UsuarioModelViewSet, PerfilReadUpdateModelViewSet, AmizadeModelViewSet

router = DefaultRouter()

router.register(r'boloes', BolaoModelViewSet, basename='bolao')
router.register(r'palpites', PalpiteModelViewSet, basename='palpites')
router.register(r'partidas', PartidaReadOnlyModelViewSet, basename='partidas')
router.register(r'usuarios', UsuarioModelViewSet, basename='usuarios')
router.register(r'perfis', PerfilReadUpdateModelViewSet, basename='perfis')
router.register(r'amizades', AmizadeModelViewSet, basename='amizades')

urlpatterns = router.urls
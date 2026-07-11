from rest_framework.routers import DefaultRouter
from bolao.views import BolaoModelViewSet, PalpiteModelViewSet

router = DefaultRouter()

router.register(r'boloes', BolaoModelViewSet, basename='bolao')
router.register(r'palpites', PalpiteModelViewSet, basename='palpites')

urlpatterns = router.urls
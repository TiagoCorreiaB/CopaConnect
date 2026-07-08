from django.urls import path, include
from rest_framework import routers
from .views import BolaoModelViewSet, PalpiteModelViewSet

router = routers.DefaultRouter()

router.register(r'boloes', BolaoModelViewSet, basename='bolao')
router.register(r'palpites', PalpiteModelViewSet, basename='palpites')

urlpatterns = [
    path('', include(router.urls)),
]
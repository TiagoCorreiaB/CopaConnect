"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

from partidas.views import PartidaViewSet
from bolao.views import BolaoModelViewSet, PalpiteModelViewSet

class ApiRootView(routers.APIRootView):
    """
    Abaixo você encontra todos os endpoints disponíveis para consumo.
    """
    def get_view_name(self):
        return 'API Copa Connect'

class MeuRouter(routers.DefaultRouter):
    APIRootView = ApiRootView

router = MeuRouter()
router.register(r'partidas', PartidaViewSet, basename='partida')
router.register(r'boloes', BolaoModelViewSet, basename='bolao')
router.register(r'palpites', PalpiteModelViewSet, basename='palpites')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/copaconnect/v1/', include(router.urls)),
]

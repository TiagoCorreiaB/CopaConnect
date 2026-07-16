from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import static
from django.conf import settings
from django.views.static import serve
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/copaconnect/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/copaconnect/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/copaconnect/v1/', include('core.api_router')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
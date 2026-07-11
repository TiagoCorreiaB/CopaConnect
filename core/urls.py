from django.contrib import admin
from django.urls import path, include

api_v1_patterns = [
    path('', include('bolao.urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/copaconnect/v1/', include(api_v1_patterns)),
]
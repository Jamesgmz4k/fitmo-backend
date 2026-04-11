from django.contrib import admin
from django.urls import path, include # <--- IMPORTANTE el 'include'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')), # <--- Esto activa tu carpeta api
]
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.admin.sites import site
from django.urls import include, path

urlpatterns = [
    path('admin/', site.urls),
    path('', include('django.contrib.auth.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

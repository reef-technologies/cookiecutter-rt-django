import debug_toolbar
from django.conf import settings
from django.contrib.admin.sites import site
from django.urls import include, path


urlpatterns = [
    path('admin/', site.urls),
    path('', include('django.contrib.auth.urls')),
]

if settings.DEBUG_TOOLBAR:
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

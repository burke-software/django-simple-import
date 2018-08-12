from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
import django

django_version = django.__version__.split('.')
if int(django_version[0]) < 2 and int(django_version[1]) < 10:
    urlpatterns = [url(r'^admin/', include(admin.site.urls)),
                   url(r'^simple_import/', include('simple_import.urls')),
                   ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns = [url(r'^admin/', admin.site.urls),
                   url(r'^simple_import/', include('simple_import.urls')),
                   ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

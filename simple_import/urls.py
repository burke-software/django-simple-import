from django.conf.urls.defaults import *
from simple_import import views

urlpatterns = patterns('',
    url('^start_import/$', views.start_import),
)

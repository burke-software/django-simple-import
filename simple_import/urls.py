from django.conf.urls.defaults import *
from simple_import import views

urlpatterns = patterns('',
    url('^start_import/$', views.start_import),
    url('^match_columns/(?P<import_log_id>\d+)/$', views.match_columns),
    url('^match_relations/(?P<import_log_id>\d+)/$', views.match_relations),
    url('^do_import/(?P<import_log_id>\d+)/$', views.do_import),
)

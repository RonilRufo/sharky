from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt

from graphql_extensions.views import GraphQLView


admin.site.site_title = admin.site.index_title = "sharky backend"
admin.site.site_header = mark_safe('<img src="{img}" alt="{alt}"/>'.format(
    img=settings.STATIC_URL + 'admin/img/logo-140x60.png',
    alt=admin.site.site_title,
))


urlpatterns = [

    path("graphql/", csrf_exempt(GraphQLView.as_view(graphiql=True))),

    # Administration
    path('admin/', admin.site.urls),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

"""pepup URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Impo rt the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny


urlpatterns = [

    # api
    path('admin/', admin.site.urls),
    # path('api/', include('api.urls')),
    # path('api/chat/', include('chat.urls')),
    path('accounts/', include('accounts.urls')),
    # path('accounts/', include('allauth.urls')),
    # path('api/', include('payment.urls')),
    # path('api/', include('user_activity.urls')),
    # path('api/', include('notice.urls')),
    #
    # path('api/', include('test.urls')),
    #
    # path('', include('landing.urls')),
    # ckeditor
    path('ckeditor/', include('ckeditor_uploader.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
    schema_view = get_schema_view(
        openapi.Info(
            title="SIIOT API",
            default_version='v1.0',
            description="Test description",
            terms_of_service="https://www.google.com/policies/terms/",
            contact=openapi.Contact(email="support@mondeique.com"),
            license=openapi.License(name="SIIOT License"),
        ),
        public=True,
        permission_classes=(AllowAny,),
    )
    urlpatterns += [
        path('swagger<str:format>', schema_view.without_ui(cache_timeout=0), name='schema-json'),
        path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        path('docs/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ]
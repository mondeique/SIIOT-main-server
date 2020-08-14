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

from core.views import download_link
from custom_manage.sites import staff_panel, superadmin_panel
from payment.views import pay_test

urlpatterns = [

    # api
    path('superadmin/', superadmin_panel.urls),
    path('staff/', staff_panel.urls, name='staff'),
    path('admin/', admin.site.urls),
    path('staff/', include('custom_manage.urls')),
    path('api/v1/', include('products.urls')),
    path('api/v1/', include('mypage.urls')),
    path('api/v1/', include('transaction.urls')),
    path('api/v1/', include('payment.urls')),
    path('api/v1/', include('chat.urls')),
    path('api/v1/', include('notice.urls')),
    path('api/v1/', include('notification.urls')),
    path('accounts/v1/', include('accounts.urls')),
    # path('chat/', include('chats.urls')),
    path('pay_test/', pay_test, name='paytest'),
    path('download/', download_link, name='download'),
    path('', include(('landing.urls'))),

    # ckeditor
    path('ckeditor/', include('ckeditor_uploader.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

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

if settings.DEBUG:
    import debug_toolbar
    print('---')
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

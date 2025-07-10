"""dtb URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import debug_toolbar
from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt

from . import views

#DRF
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r'incomejsons', views.IncomeJsonViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('__debug__/', include(debug_toolbar.urls)),
    path('', views.index, name="index"),
    path('super_secter_webhook/', csrf_exempt(views.TelegramBotWebhookView.as_view())),
    path('import/',views.recieve_json, name="recieve_json"),
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('data/',views.data_files, name="data_files"),
    path('orders/',views.orders_request, name="orders_request"),
    path('logs/', views.view_logs, name="view_logs"),
]






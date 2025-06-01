"""opentunity_django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from devices import views as device_views
from devices.views import activate


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # login/logout
    path('signup/', device_views.signup, name='signup'),
    path('add-device/', device_views.add_device, name='add_device'),
    path('', device_views.dashboard, name='dashboard'),  # homepage after login
    path('device/<int:pk>/',             device_views.asset_detail, name='asset_detail'),
    path('device/<int:pk>/edit/',        device_views.asset_edit,   name='asset_edit'),
    path("activate/<uidb64>/<token>/", activate, name="activate"),
    path('', include('devices.urls')),
    path('api/assets/<int:asset_id>/enter-api-key/', device_views.asset_api_key_entry, name='asset_api_key_entry'),


]

"""JSS URL Configuration

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
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls import url, include
from django.contrib.auth.models import User

from wx.views import mp_verify, minip_verify

urlpatterns = [
    path('admin/', admin.site.urls),
    path('s/', include('s.urls')),
    path('api/', include('api.urls')),
    path('wx/', include('wx.urls')),
    path('ai/', include('ai.urls')),
    path('statistic/', include('statistic.urls')),
    path('minip/', include('minip.urls')),
    path('robot/', include('robot.urls')),
    path('MP_verify_QiNbvMFQsmegMWio.txt', mp_verify, name='verify'),
    path('NvrFbr8lB7.txt', minip_verify, name='mini_verify')
]

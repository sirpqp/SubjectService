from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('auth',views.auth,name='auth'),
    path('reply',views.reply,name='reply'),
    path('location',views.location,name='location'),
]

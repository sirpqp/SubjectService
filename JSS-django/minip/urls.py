from django.urls import path

from . import views

urlpatterns = [
    # path('', views.index, name='index'),
    path('auth', views.auth, name='minip_auth'),
    # path('reply', views.reply, name='reply'),
    path('location', views.location, name='minip_location'),
    path('ask', views.ask),
    path('email_to', views.email_to),
    path('ask4ysys', views.ask4ysys),
    path('ask4open', views.ask4open)
]

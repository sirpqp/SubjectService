from django.conf.urls import url, include
from rest_framework import routers
from . import views
from django.urls import path

router = routers.DefaultRouter()
router.register('chatroom', views.ChatRoomViewSet)
router.register('buddy', views.BuddyViewSet)
router.register('dialog', views.DialogViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    path('easy_dialog', views.easy_dialog, name='easy'),
    path('have_a_sit/<str:room>/<str:buddy>', views.have_a_sit, name='sit'),
    path('is_received/<str:room>/<str:buddy>',
         views.is_received,
         name='received'),
    path('email_to', views.email_to),
    path('qqbot', views.qqbot, name='qqbot'),
    path('replyqq', views.replyQQ, name='replyqq'),
]

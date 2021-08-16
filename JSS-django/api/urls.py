from django.conf.urls import url, include
from rest_framework import routers
from . import views
from django.urls import path

router = routers.DefaultRouter()
router.register('users', views.UserViewSet)
# router.register('roles', views.RoleViewSet)
router.register('customers', views.CustomerViewSet)
router.register('organs', views.OrganViewSet)
router.register('groups', views.GroupViewSet)
router.register('requests', views.RequestViewSet)
router.register('tasks', views.TaskViewSet)
router.register('regions', views.RegionViewSet)
router.register('seller_regions', views.SellerRegionViewSet)
router.register('resources', views.ResourceViewSet)
router.register('zones', views.ZoneViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    # url(r'^users/<int:pk>/', views.UserViewSet)
    # url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]

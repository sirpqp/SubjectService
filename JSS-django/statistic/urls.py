from django.conf.urls import url, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register('d1', views.D1ViewSet)
router.register('d2', views.D2ViewSet)
router.register('d3', views.D3ViewSet)
router.register('d4', views.D4ViewSet)
router.register('user', views.UserViewSet, basename='user-list')
router.register('total', views.TotalViewSet, basename='total-list')
router.register('active/custom', views.CustomViewSet, basename='active-group')
router.register('active/group', views.GroupViewSet, basename='active-group')
router.register('res', views.ResViewSet)
router.register('report/organ', views.OrganViewSet, basename='organ-list')
router.register('report/dept', views.DeptViewSet, basename='dept-list')
router.register('report/success',
                views.SuccessViewSet,
                basename='success-list')
router.register('report/language',
                views.LanguageViewSet,
                basename='language-list')
router.register('report/type', views.TypeViewSet, basename='type-list')
router.register('report/custom',
                views.ReportCustomViewSet,
                basename='report-custom-list')

urlpatterns = [
    url(r'^', include(router.urls)),
    url('elder', views.ElderStatistic, name='elder'),
]

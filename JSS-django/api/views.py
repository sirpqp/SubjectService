from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, filters
from django_filters import rest_framework as myfilter
from api.serializers import *
from rest_framework.pagination import PageNumberPagination


class UnlimitedPagination(PageNumberPagination):
    page_size = None
    page_size_query_param = 'page_size'
    max_page_size = None


class UserViewSet(viewsets.ModelViewSet):
    """
    用户基本信息。
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

    filter_backends = (DjangoFilterBackend, )
    filter_fields = ('username', 'password', 'role')


# class RoleViewSet(viewsets.ModelViewSet):
#     """
#     权限角色/用户分组。
#     """
#     queryset = Role.objects.all()
#     serializer_class = RoleSerializer


class RegionViewSet(viewsets.ModelViewSet):
    """
    大区信息。
    """
    queryset = Region.objects.all()
    serializer_class = RegionSerializer


class SellerRegionFilter(myfilter.FilterSet):
    seller = myfilter.CharFilter(field_name='seller_id', lookup_expr='exact')
    region = myfilter.CharFilter(field_name='region_id', lookup_expr='exact')


class SellerRegionViewSet(viewsets.ModelViewSet):
    """
    大区-销售关系/销售分组。
    """
    queryset = SellerRegion.objects.all()
    serializer_class = SellerRegionSerializer

    filter_backends = (DjangoFilterBackend, )
    filter_class = SellerRegionFilter

    class Meta:
        model = SellerRegion
        fields = ['seller', 'region']


class OrganViewSet(viewsets.ModelViewSet):
    """
    机构信息。
    """
    queryset = Organ.objects.all().order_by('-date_joined')
    serializer_class = OrganSerializer

    filter_backends = (
        filters.SearchFilter,
        DjangoFilterBackend,
    )
    search_fields = ('name', )
    filter_fields = (
        'is_active',
        'name',
    )


class GroupViewSet(viewsets.ModelViewSet):
    """
    服务群信息。
    """
    queryset = Group.objects.all().order_by('-date_joined')
    serializer_class = GroupSerializer

    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    filter_fields = ('name', 'type', 'gid')
    search_fields = ('name', )


class CustomerViewSet(viewsets.ModelViewSet):
    """
    客户信息。
    """
    queryset = Customer.objects.all().order_by('-date_joined')
    serializer_class = CustomerSerializer

    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    filter_fields = ('nickname', 'qq', 'dept', 'wechat')
    search_fields = ('nickname', 'qq')


class RequestViewSet(viewsets.ModelViewSet):
    """
    客户请求（任务组）。
    """
    queryset = Request.objects.all().order_by('-date_registered')
    serializer_class = RequestSerializer


class TaskViewSet(viewsets.ModelViewSet):
    """
    任务信息。
    """
    class TaskFilter(myfilter.FilterSet):
        # status = myfilter.ChoiceFilter(field_name='status', lookup_expr='exact')
        customer = myfilter.CharFilter(
            field_name='request__customer__nickname')
        cid = myfilter.CharFilter(field_name='request__customer__id')
        group = myfilter.CharFilter(field_name='request__group__name')
        request = myfilter.CharFilter(field_name='request_id',
                                      lookup_expr='exact')

        class Meta:
            model = Task
            fields = ['title', 'status', 'customer', 'group', 'request']

    queryset = Task.objects.all().order_by('-id')
    serializer_class = TaskSerializer

    filter_backends = (DjangoFilterBackend, )
    # filter_fields = ('title', 'status')
    filter_class = TaskFilter


class PercentViewSet(viewsets.ModelViewSet):
    """
    任务完成百分比
    """
    pass


class ResourceViewSet(viewsets.ModelViewSet):
    """
    全文资源
    """
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer


class ZoneViewSet(viewsets.ModelViewSet):
    """
    机构扩展地区
    """
    queryset = Zone.objects.all()
    serializer_class = ZoneSerializer
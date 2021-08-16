from .models import *
from rest_framework import serializers
from robot.models import Dialog
from django.db.models import ObjectDoesNotExist


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


# class RoleSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Role
#         fields = '__all__'


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'


class SellerRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerRegion
        fields = '__all__'


class OrganSerializer(serializers.ModelSerializer):
    seller2 = serializers.SerializerMethodField()
    region2 = serializers.SerializerMethodField()

    @staticmethod
    def get_seller2(obj):
        return {'id': obj.seller.seller.id, 'name': obj.seller.seller.nickname}

    @staticmethod
    def get_region2(obj):
        return obj.seller.region.name

    class Meta:
        model = Organ
        fields = '__all__'


class GroupSerializer(serializers.ModelSerializer):
    organ2 = serializers.SerializerMethodField()

    @staticmethod
    def get_organ2(obj):
        return obj.organ.name

    class Meta:
        model = Group
        fields = '__all__'


class CustomerSerializer(serializers.ModelSerializer):
    ex = serializers.SerializerMethodField()

    @staticmethod
    def get_ex(obj):
        return {
            'organ': {
                'id': obj.organ.id,
                'name': obj.organ.name
            },
            'group': {
                'id': obj.group.id,
                'name': obj.group.name,
                'type': obj.group.type
            }
        }

    class Meta:
        model = Customer
        fields = '__all__'


class RequestSerializer(serializers.ModelSerializer):
    customer2 = serializers.SerializerMethodField()
    group2 = serializers.SerializerMethodField()
    registrar2 = serializers.SerializerMethodField()

    @staticmethod
    def get_customer2(obj):
        return obj.customer.nickname

    @staticmethod
    def get_group2(obj):
        return obj.group.name

    @staticmethod
    def get_registrar2(obj):
        return obj.registrar.nickname

    class Meta:
        model = Request
        fields = '__all__'


class TaskSerializer(serializers.ModelSerializer):
    ex = serializers.SerializerMethodField()

    @staticmethod
    def get_ex(obj):
        return {
            'group':
            '[%s]%s' % (obj.request.group.type, obj.request.group.name),
            'gid':
            obj.request.group.gid,
            'customer':
            obj.request.customer.nickname,
            'wechat':
            obj.request.customer.wechat,
            'email':
            obj.request.customer.email,
            'registrar':
            obj.request.registrar.nickname,
            'date_registered':
            obj.request.date_registered,
            'res_id':
            obj.resource.id if obj.resource else None,
            'resource': {
                'title': obj.resource.title,
                'attachment': {
                    'name': obj.resource.attachment.name,
                    'url': obj.resource.attachment.url,
                } if obj.resource.attachment else None,
                'size': obj.resource.size,
                'restype': obj.resource.restype.id,
                'cost': obj.resource.cost,
                'uid': obj.resource.uid,
                'source': obj.resource.source,
                'lang': obj.resource.lang,
                'short': obj.resource.short,
            } if obj.resource else None,
            'replier':
            obj.replier.nickname if obj.replier else None,
            'receiver':
            obj.receiver.nickname if obj.receiver else None,
            'need_received':
            TaskSerializer.chk_received(obj.request.group.gid,
                                        obj.request.customer.wechat)
            if obj.request.group.gid and obj.request.customer.wechat else False
        }

    @staticmethod
    def chk_received(room: str, buddy: str):
        dialogs = Dialog.objects.filter(room=room,
                                        buddy=buddy,
                                        role='custom',
                                        is_received=False)

        return len(dialogs) > 0

    class Meta:
        model = Task
        fields = '__all__'


class ResourceSerializer(serializers.ModelSerializer):
    # def get_path(self,obj):
    #     return obj.attachment.url

    # @action(methods=['post'])
    # def upload_file(request):
    #     form = ModelFormWithFileField(request.POST,request.FILES)
    #     form.save()
    #     return {
    #         'status':'ok',
    #         'size':request.FILES['file'].size,
    #         'url':request.FILES['file'].url,
    #     }

    class Meta:
        model = Resource
        fields = '__all__'


class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = '__all__'
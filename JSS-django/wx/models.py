from django.db import models
from api.models import *


class Auth(models.Model):
    Customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    openid = models.CharField('微信用户ID', max_length=28, unique=True)
    date_auth = models.DateTimeField('授权时间', auto_now_add=True)
    latitude = models.FloatField('授权地纬度', blank=True, default=0)
    longitude = models.FloatField('授权地经度', blank=True, default=0)
    is_active = models.BooleanField('是否激活', default=True)
    level =models.IntegerField('等级',default=0)#授权等级 0-试用 1-正式 2-个人（预留）
    free=models.IntegerField('免费篇数',default=5)#仅试用有效

    def __str__(self):
        return self.Customer.nickname


class Location(models.Model):
    openid = models.CharField('微信用户ID', max_length=28, unique=True)
    latitude = models.FloatField('授权地纬度')
    longitude = models.FloatField('授权地经度')
    date = models.DateTimeField('获取时间', auto_now_add=True)

    def __str__(self):
        return self.openid

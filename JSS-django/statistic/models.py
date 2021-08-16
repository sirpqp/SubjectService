from django.db import models


class User(models.Model):
    name = models.CharField('客服', max_length=255)
    total = models.PositiveIntegerField('总计')


class Total(models.Model):
    date = models.CharField('日期', max_length=10)
    total = models.PositiveIntegerField('需求')
    success = models.PositiveIntegerField('回复')


class D1(models.Model):
    """
    今日服务量模型
    """
    total = models.PositiveIntegerField('今日服务量')
    today = models.PositiveIntegerField('今日量')
    yesterday = models.PositiveIntegerField('昨日量')
    week = models.PositiveIntegerField('上周同期量')
    max = models.PositiveIntegerField('月最高量')
    days = models.PositiveIntegerField('服务天数')


class D2(models.Model):
    """
    分时需求量模型
    """
    date = models.CharField('日期', max_length=10)
    hour = models.PositiveSmallIntegerField('小时')
    total = models.PositiveIntegerField('总计')


class D3(models.Model):
    """
    总服务量模型
    """
    date = models.CharField('日期', max_length=10)
    total = models.PositiveIntegerField('总计')


class D4(models.Model):
    """
    成功回复率模型
    """
    total = models.PositiveIntegerField('今日服务量')
    today = models.PositiveIntegerField('今日量')
    yesterday = models.PositiveIntegerField('昨日量')
    week = models.PositiveIntegerField('上周同期量')


class Custom(models.Model):
    """
    客户活跃情况模型
    """
    date = models.CharField('日期', max_length=10)
    total = models.PositiveIntegerField('日活次数')


class Group(models.Model):
    """
    群活跃情况模型
    """
    name = models.CharField('群名称', max_length=64)
    total = models.PositiveIntegerField('需求量')


class Res(models.Model):
    """
    资源类型占比模型
    """
    res_type = models.CharField('资源名', max_length=32)
    total = models.PositiveIntegerField('总计')


class Organ(models.Model):
    """
    机构排名
    """
    name = models.CharField('机构名称', max_length=64)
    total = models.PositiveIntegerField('需求量')
    success = models.PositiveIntegerField('成功量')
    failed = models.PositiveIntegerField('失败量')


class Dept(models.Model):
    type = models.CharField('部门名称', max_length=32)
    value = models.PositiveIntegerField('需求量')


class Success(models.Model):
    success = models.FloatField()
    failed = models.FloatField()


class Language(models.Model):
    ZH = models.PositiveIntegerField()
    F = models.PositiveIntegerField()


class Type(models.Model):
    type = models.CharField(max_length=64)
    sales = models.PositiveIntegerField()


class ReportCustom(models.Model):
    name = models.CharField('显示名', max_length=64)
    dept = models.CharField('部门', max_length=32)
    total = models.PositiveIntegerField()

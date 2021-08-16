from django.db import models
from api.models import *

# class Catching(models.Model):
#     '''AI捕获表'''
#     task = models.ForeignKey(Task, on_delete=models.CASCADE)
#     # doi:10.1016/j.ajo.2020.04.019;PMID:5687458;etc.
#     labels = models.TextField('标识标签')
#     url_target = models.URLField('目标网址')
#     url_fulltext = models.URLField('全文链接')
#     status = models.CharField('状态', max_length=10, choices=(
#         ('unknow', '未知'),
#         ('useful', '有用'),
#         ('useless', '无用')
#     ), default='unknow')


class libgen_non_fiction(models.Model):
    """ libgen非虚构图书 """
    Identifier = models.TextField(null=True)
    Title = models.TextField(null=True)
    Authors = models.TextField(null=True)
    Year = models.CharField(max_length=4, null=True)
    Publisher = models.TextField(null=True)
    Libgenid = models.CharField(max_length=10, null=True)
    FileId = models.CharField(max_length=10, null=True)


class libgen_scimag(models.Model):
    """ libgen科学文章"""
    Doi = models.TextField(null=True)
    Title = models.TextField(null=True)
    Authors = models.TextField(null=True)
    Year = models.CharField(max_length=4, null=True)
    Journal = models.TextField(null=True)
    PubmedId = models.TextField(null=True)
    Libgenid = models.CharField(max_length=10, null=True)
    FileId = models.CharField(max_length=10, null=True)
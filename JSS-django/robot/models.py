from django.db import models
from api.models import *


class ChatRoom(models.Model):
    '''微信群'''
    wxid = models.CharField(max_length=64, primary_key=True)
    name = models.CharField('群名', max_length=128)

    def __str__(self):
        return self.name


class Buddy(models.Model):
    '''微信用户'''
    wxid = models.CharField(max_length=20, primary_key=True)
    name = models.CharField('群昵称', max_length=128)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


role_choices = [
    ('custom', '客户'),
    ('AI', 'AI'),
    ('CS', '客服'),
]


class Dialog(models.Model):
    '''聊天室对话记录'''
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    buddy = models.ForeignKey(Buddy, on_delete=models.CASCADE)
    role = models.CharField(choices=role_choices,
                            default='custom',
                            max_length=8)
    date = models.DateTimeField('时间', auto_now_add=True)
    content = models.TextField('内容')
    is_received = models.BooleanField('是否接单', default=False)
    request = models.ForeignKey(Request,
                                blank=True,
                                null=True,
                                on_delete=models.SET_NULL)
    state = models.IntegerField(choices=[(0, '未处理'), (1, '已处理'), (2, '转人工')],
                                default=0)

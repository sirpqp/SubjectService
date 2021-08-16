import base64
import logging
import re
import time
from datetime import datetime
import requests
from api.models import Resource, ResType, Task, User, short_url, Statistic
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.http import HttpResponse, JsonResponse
from ai.detroit import Detroit


def index(request, task_id):
    """ AI的HTTP协议接口 """
    task = Task.objects.get(pk=task_id)
    statistic = Statistic(create_time=datetime.now())
    statistic.task = task
    # openid = request.POST['openid']
    de = Detroit(task, statistic)
    # detroit.start(task, openid)
    return JsonResponse(de.startx(), safe=False)

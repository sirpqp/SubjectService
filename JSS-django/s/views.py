from django.shortcuts import render, redirect

from django.http import HttpResponse, StreamingHttpResponse, Http404
from django.utils.http import urlquote
import zipfile

from api.models import *
from django.conf import settings


def index(request, short):
    if len(short) == 6:
        try:
            res = Resource.objects.get(short=short)
        except Resource.DoesNotExist:
            raise Http404("没有此地址")
        if res.attachment:
            return redirect(str(res.attachment.url))
        elif res.download:
            return redirect(str(res.download))
        else:
            raise Http404("没有全文")
    else:
        return redirect(settings.MEDIA_URL + '/uploads/zip/' + short + '.zip')


def upload(request):
    return HttpResponse(status=204)


def zip(request, tasks):
    short = short_url(8)
    z = zipfile.ZipFile(
        settings.MEDIA_ROOT + r'\uploads\zip\\' + short + '.zip', 'w')
    for task in tasks.split(','):
        file = Task.objects.filter(pk=task)[0].resource.attachment
        z.write(file.path, file.name.split('/')[len(file.name.split('/')) - 1])
    z.close()
    return HttpResponse('压缩成功，下载链接：http://api.jlss.vip/s/' + short,
                        status=201)

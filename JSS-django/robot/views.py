import json
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from smtplib import SMTPException

import requests
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ai.detroit import Detroit
from api.models import *
from .models import *
from .serializers import *
from .words import tag


class ChatRoomViewSet(viewsets.ModelViewSet):
    """
    群信息
    """
    queryset = ChatRoom.objects.all().order_by('-id')
    serializer_class = ChatRoomSerializer


class BuddyViewSet(viewsets.ModelViewSet):
    """
    群用户
    """
    queryset = Buddy.objects.all().order_by('-id')
    serializer_class = BuddySerializer


class DialogViewSet(viewsets.ModelViewSet):
    """
    群对话
    """
    queryset = Dialog.objects.all().order_by('-id')
    serializer_class = DialogSerializer

    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('role', 'state')


@api_view(['GET', 'POST'])
def easy_dialog(request):
    """
    简单的群对话接口
    """
    if request.method == 'GET':
        queryset = Dialog.objects.filter(state=0).exclude(role='custom')
        serializer = DialogSerializer(queryset, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        # 检查群/人是否已登记
        try:
            theRoom = ChatRoom.objects.get(pk=request.data['room'])
            if theRoom.name != request.data['room_name']:
                theRoom.name = request.data['room_name']
                theRoom.save()
        except ChatRoom.DoesNotExist as err:
            newRoom = ChatRoom(wxid=request.data['room'],
                               name=request.data['room_name'])
            newRoom.save()
            theRoom = newRoom
        try:
            theBuddy = Buddy.objects.get(pk=request.data['buddy'])
        except Buddy.DoesNotExist as err:
            newBuddy = Buddy(wxid=request.data['buddy'],
                             name=request.data['buddy_name'],
                             room=theRoom)
            newBuddy.save()
            theBuddy = newBuddy

        serializer = DialogSerializer(data=request.data)
        if serializer.is_valid():
            # 保存dialog记录
            # serializer.save()
            # p = Process(target=DetroitHandle,
            #             args=(request.data, serializer.validated_data))
            # p.start()
            t = threading.Thread(target=DetroitHandle, args=(request,))
            t.start()
            # t.join()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


def DetroitHandle(request):
    serializer = DialogSerializer(data=request.data)
    if serializer.is_valid():
        # 检查群/人是否已登记
        try:
            theGroup = Group.objects.get(gid=request.data['room'])
            if theGroup.name != request.data['room_name']:
                theGroup.name = request.data['room_name']
                theGroup.save()
        except Group.DoesNotExist as err:
            newGroup = Group(name=request.data['room_name'],
                             type='微信',
                             gid=request.data['room'],
                             is_active=True,
                             organ=Organ.objects.get(pk=111))
            newGroup.save()
            theGroup = newGroup
        try:
            theCustomer = Customer.objects.get(wechat=request.data['buddy'],
                                               group=theGroup.id)
        except Customer.DoesNotExist as err:
            newCustomer = Customer(nickname=request.data['buddy_name'],
                                   wechat=request.data['buddy'],
                                   group=theGroup,
                                   organ=Organ.objects.get(pk=111))
            newCustomer.save()
            theCustomer = newCustomer

        statistic = Statistic(create_time=datetime.now())

        # 创建需求
        req = Request(customer=theCustomer,
                      group=theGroup,
                      description=str(serializer.validated_data['content']),
                      registrar=User.objects.get(pk=1))
        req.save()
        statistic.request = req
        tagged = tag(req.description)
        if tagged['公告'] > 0 or (len(req.description) > 0
                                and tagged['length'] <= 5):
            return '不需要处理'
        # 分解任务
        task = Task(request=req,
                    title=req.description,
                    status='progress',
                    data_received=datetime.now())
        task.save()
        statistic.task = task
        # if tagged['特需'] > 0:
        #    replyMsg = '您好！您的咨询已经受理，请您耐心等待。'
        #    reply = Dialog(role='AI',
        #                   content=replyMsg,
        #                   room=serializer.validated_data['room'],
        #                   buddy=serializer.validated_data['buddy'],
        #                   request=req)
        #    reply.save()
        #    return '无需调用AI'
        # 调用AI
        de = Detroit(task, statistic)
        result = de.startx()
        if result:
            serializer.save(state=1, is_received=True, request=req)
            task.status = 'success'
            task.data_replied = datetime.now()
            task.save()
            # 回复消息
            title = json.loads(result)['title']
            short = json.loads(result)['short']
            replyMsg = f'您需要的《{title}》已找到，下载链接：http://api.jlss.vip/s/{short}'
            reply = Dialog(role='AI',
                           content=replyMsg,
                           room=serializer.validated_data['room'],
                           buddy=serializer.validated_data['buddy'],
                           request=req)
            reply.save()
            statistic.result = 'SU'
        else:
            statistic.result = 'FA'
            statistic.channel = 'PE'
            task.status = 'waiting'
            task.data_received = None
            task.save()
            if de.CITATION and (de.CITATION.doi or de.CITATION.pmid):
                # 自动接单
                serializer.save(state=2, is_received=True, request=req)
                auto_reply = Dialog(role='AI',
                                    content='您好！您的咨询已经受理，请您耐心等待。',
                                    room=serializer.validated_data['room'],
                                    buddy=serializer.validated_data['buddy'],
                                    request=req)
                auto_reply.save()
            else:
                serializer.save(state=2, request=req)
            # 无人值守自动应答
            if time.localtime().tm_hour < 7:
                night_reply = Dialog(role='AI',
                                     content='您好！您需要的文献需要人工处理，客服人员上班后会第一时间为您服务！给您带来的不便敬请原谅！！ ',
                                     room=serializer.validated_data['room'],
                                     buddy=serializer.validated_data['buddy'],
                                     request=req)
                night_reply.save()

        statistic.finish_time = datetime.now()
        statistic.save()


@api_view(['PUT'])
def have_a_sit(request, room: str, buddy: str):
    try:
        dialogs = Dialog.objects.filter(room=room,
                                        buddy=buddy,
                                        role='custom',
                                        is_received=False)
        for d in dialogs:
            d.is_received = True
            d.save()

        return JsonResponse({'conut': len(dialogs)}, safe=False)
    except ObjectDoesNotExist:
        return JsonResponse({'error': str(ObjectDoesNotExist)}, safe=False)


@api_view(['GET'])
def is_received(request, room: str, buddy: str):
    try:
        dialogs = Dialog.objects.filter(room=room, buddy=buddy, role='custom', is_received=False)

        return JsonResponse({'is_received': len(dialogs) == 0}, safe=False)
    except ObjectDoesNotExist:
        return JsonResponse({'error': str(ObjectDoesNotExist)}, safe=False)


@api_view(['POST'])
def email_to(request):
    """回复邮件"""
    email = request.POST['email']
    replyMsg = request.POST['replyMsg']
    recipient_list = [email]
    try:
        send_mail('文献传递', replyMsg, 'jlss202101@vip.163.com', recipient_list, fail_silently=False)
        return JsonResponse({'msg': 'ok'})
    except SMTPException:
        # logging.error(SMTPException)
        email_to(email, replyMsg)


@api_view(['POST'])
def qqbot(request):
    def ignore(id: str):
        """屏蔽用户"""
        ignore_list = [
            2138241371, 3327627472, 2749134869, 2177238858, 1936360081,
            2423040846, 1774234761
        ]
        return id in ignore_list

    message = {
        'text': '',
        'buddy': {'id': 0, 'name': ''},
        'group': {'id': 0, 'name': ''}
    }

    statistic = Statistic(create_time=datetime.now())

    def reply(msg: dict, replyMsg: str):
        mirai_api = {
            'host': 'http://127.0.0.1:8080',
            'authKey': 'INITKEYcp7KhYss',
            'qq': '2138241371',
            'session': ''
        }
        headers = {'Content-Type': 'application/json'}
        try:
            auth = requests.post(mirai_api['host'] + '/auth',
                                 headers=headers,
                                 data=json.dumps(
                                     {"authKey": mirai_api['authKey']}))
            # Authorize
            if auth.status_code == 200 and auth.json()['code'] == 0:
                verify = requests.post(mirai_api['host'] + '/verify', headers=headers,
                                       data=json.dumps({"sessionKey": auth.json()['session'], "qq": mirai_api['qq']}))

                if verify.status_code == 200 and verify.json()['code'] == 0:
                    mirai_api['session'] = auth.json()['session']
                else:
                    print(verify.json()['msg'])
            else:
                print(auth.json()['msg'])
        except Exception as ex:
            print(f'验证失败:{ex}')
        try:
            sendGroupMessage = requests.post(mirai_api['host'] + '/sendGroupMessage',
                                             data=json.dumps({
                                                 "sessionKey": str(mirai_api['session']),
                                                 'target': msg['group']['id'],
                                                 'messageChain': [{'type': 'At', 'target': msg['buddy']['id']},
                                                                  {'type': 'Plain', 'text': str(replyMsg)}]
                                             }))
        except Exception as ex:
            print(f'发送失败:{ex}')

    def handleTask(msg: dict):
        """处理机器人采回的任务"""
        # 获取群，必要时创建
        (theGroup, created) = Group.objects.get_or_create(
            gid=msg['group']['id'],
            is_active=1,
            defaults={
                'name': msg['group']['name'],
                'type': 'QQ',
                'gid': msg['group']['id'],
                'organ': Organ.objects.get(pk=111)
            })
        # 判断是否需要更新群名
        if theGroup.name != msg['group']['name']:
            theGroup.name = msg['group']['name']
            theGroup.save()
        # 获取客户，必要时创建
        (theCustomer, created) = Customer.objects.get_or_create(
            qq=msg['buddy']['id'],
            is_active=1,
            group=theGroup,
            defaults={
                'nickname': msg['buddy']['name'],
                'qq': msg['buddy']['id'],
                'group': theGroup,
                'organ': theGroup.organ
            })
        # 创建需求
        req = Request(customer=theCustomer,
                      group=theGroup,
                      description=msg['text'],
                      registrar=User.objects.get(pk=1))
        req.save()
        statistic.request = req

        tagged = tag(req.description)
        if tagged['公告'] > 0 or (len(req.description) > 0
                                and tagged['length'] <= 5):
            statistic.category = 2
            statistic.result = 'TH'
            return '不需要处理'
        # 创建任务（暂不分解）
        task = Task(request=req, title=req.description)
        task.save()

        statistic.task = task

        if tagged['特需'] > 0:
            replyMsg = '您好！您的咨询已经受理，请您耐心等待。'
            reply(msg, replyMsg)

            statistic.category = 0
            statistic.channel = 'PE'

            return '无需调用AI'
        else:
            statistic.category = 1
            task.status = 'progress'
            task.data_received = datetime.now()
            task.save()
            # 调用AI
            de = Detroit(task, statistic)
            result = de.startx()
            if result:
                statistic.result = 'SU'
                # 有结果，自动查找成功
                task.status = 'success'
                task.data_replied = datetime.now()
                task.save()
                # 回复消息
                title = task.request
                short = result
                replyMsg = f'您需要的《{title}》已找到，下载链接：http://api.jlss.vip/s/{short}'
                reply(msg, replyMsg)
            else:
                statistic.channel = 'PE'
                statistic.result = 'FA'
                task.status = 'waiting'
                task.data_received = None
                # 自动动接单
                if (de.CITATION and (de.CITATION.doi or de.CITATION.pmid)) or \
                        (tagged['需求'] != 0 and tagged['需求'] >= tagged['答复'] + tagged['客套']):
                    replyMsg = '您好！您的咨询已经受理，请您耐心等待。'
                    reply(msg, replyMsg)
                # 无人值守自动应答
                if time.localtime().tm_hour < 7:
                    replyMsg = '您好！您需要的文献需要人工处理，客服人员上班后会第一时间为您服务！给您带来的不便敬请原谅！！'
                    reply(msg, replyMsg)
                task.save()

    if request.data['type'] == 'GroupMessage' and not ignore(
            request.data['sender']['id']):
        # 初始化message
        for msg in request.data['messageChain']:
            if msg['type'] == 'Xml':
                xml = ET.fromstring(msg['xml'])
                if xml.attrib['serviceID'] == '33':
                    message['text'] = xml.attrib['url']
            elif msg['type'] == 'Source':
                message['text'] += ''
            elif msg['type'] == 'At':
                message['text'] += msg['display']
            elif msg['type'] == 'Face':
                message['text'] += f"[{msg['name']}]"
            elif msg['type'] == 'Plain':
                message['text'] += msg['text']
            elif msg['type'] == 'Image':
                message['text'] += '[图片格式]'
            elif msg['type'] == 'File':
                message['text'] += '[文件格式]'
            else:
                message['text'] += '[无法识别格式' + msg['type'] + ']'
        message['buddy'] = {
            'id': request.data['sender']['id'],
            'name': request.data['sender']['memberName']
        }
        message['group'] = {
            'id': request.data['sender']['group']['id'],
            'name': request.data['sender']['group']['name']
        }
        # print(message)
        handleTask(message)

    statistic.finish_time = datetime.now()
    statistic.save()
    return JsonResponse({'msg': 'ok'})


@api_view(['POST'])
def replyQQ(request):
    """回复QQ消息"""
    task_id = request.data['tid']
    task = Task.objects.get(pk=task_id)
    replyMsg = request.data['content']
    mirai_api = {
        'host': 'http://127.0.0.1:8080',
        'authKey': 'INITKEYmIVot2km',
        'qq': '2177238858',
        'session': ''
    }
    headers = {'Content-Type': 'application/json'}
    try:
        auth = requests.post(mirai_api['host'] + '/auth', headers=headers,
                             data=json.dumps({"authKey": mirai_api['authKey']})
                             )
        # Authorize
        if auth.ok and auth.json()['code'] == 0:
            verify = requests.post(mirai_api['host'] + '/verify', headers=headers,
                                   data=json.dumps({"sessionKey": auth.json()['session'], "qq": mirai_api['qq']})
                                   )
            if verify.ok and verify.json()['code'] == 0:
                mirai_api['session'] = auth.json()['session']
            else:
                print(verify.json()['msg'])
        else:
            print(auth.json()['msg'])
    except Exception as ex:
        return HttpResponse(f'验证失败:{ex}', 401)
    try:
        sendGroupMessage = requests.post(mirai_api['host'] + '/sendGroupMessage',
                                         data=json.dumps(
                                             {"sessionKey": str(mirai_api['session']), 'target': task.request.group.gid,
                                              'messageChain': [{'type': 'At', 'target': task.request.customer.qq},
                                                               {'type': 'Plain', 'text': str(replyMsg)}]
                                              }))
        return HttpResponse('发送成功', 200)
    except Exception as ex:
        print(sendGroupMessage.request.body)
        return HttpResponse(f'发送失败:{ex}', 401)

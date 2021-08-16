import logging
import math
import time
import threading
from urllib.parse import quote
# import aiohttp
# import asyncio

from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.conf import settings
from wechatpy import parse_message, WeChatClient
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.oauth import WeChatOAuth
from wechatpy.replies import create_reply, ArticlesReply
from wechatpy.utils import check_signature
from wechatpy.client.api import WeChatJSAPI

from api.models import *
from .models import *
from ai.views import *

MATERIALS_FOR = {
    'welcome': 'aRGRZQzzMPvVvdIHVYUAg1wqAGjBEO8fgmFo7JN2DLM',
    'help': 'aRGRZQzzMPvVvdIHVYUAg239kv_uQodYBVarxo9d19U',
}

APP_ID = 'wx5c508e7ffd72e463'
SECRET = 'd02bc1b05564f24c403bfcc70dc37cda'
REDIRECT_URI = quote('http://api.jlss.vip/wx/auth', safe='')
CLIENT = WeChatClient(APP_ID, SECRET)
OAUTH_CLIENT = WeChatOAuth(APP_ID, SECRET, REDIRECT_URI)


def get_materials(m_type):
    """ 取得响应素材 """
    materials = CLIENT.material.get(MATERIALS_FOR[m_type])
    articles = []
    for item in materials:
        articles.append({
            "title": item['title'],
            "description": item['digest'],
            "url": item['url'],
            "image": item['thumb_url'],
        })
    return articles


def get_auth(openid):
    """获取已注册权限"""
    return Auth.objects.filter(openid=openid).first() if Auth.objects.filter(
        openid=openid).exists() else None


def index(request):
    """ 首页：微信验证(GET)/接收事件(POST) """
    def event_subscribe(msg):
        """订阅事件"""
        logging.info('触发订阅事件：%s', msg)
        user_auth = get_auth(msg.source)
        if user_auth:  # 重新激活老用户
            user_auth.is_active = True
            user_auth.save()
        # result = ArticlesReply(message=msg, articles=get_materials('welcome')) 图文回复被否决
        result = create_reply(
            '欢迎关注聚联搜索，我们可以帮助您查找所需的中外文文献，您只需在对话框里输入：文献题名、文献链接、文献DOI号或文献PMID号即可查询，查询结果直接私聊并以下载链接的形式回复到需求者。\n'
            + '我们服务时间为9:00-23:00，节假日（春节除外）时间为9:00-17:00。\n' +
            '详细使用说明请参考“帮助说明”，初次使用请允许获取地理位置。',
            message=msg)
        return HttpResponse(result.render())

    def even_unsubscribe(msg):
        """取消订阅"""
        # https://developers.weixin.qq.com/doc/offiaccount/Message_Management/Receiving_event_pushes.html
        logging.info('触发退订事件：%s', msg)
        user_auth = Auth.objects.filter(
            openid=msg.source).first() if Auth.objects.filter(
                openid=msg.source).exists() else None
        if user_auth:
            user_auth.is_active = False
            user_auth.save()

    # def event_location(msg):
    #     """发生地理位置事件"""
    #     logging.info('获取了地理信息：%s', str(msg))
    #     the_location = Location.objects.filter(openid=msg.source).first(
    #     ) if Location.objects.filter(openid=msg.source).exists() else None
    #     if the_location is None:  # 加入地址缓存
    #         Location.objects.create(
    #             openid=msg.source, latitude=msg.latitude, longitude=msg.longitude)
    #     else:  # 更新地址缓存
    #         the_location.latitude = msg.latitude
    #         the_location.longitude = msg.longitude
    #         the_location.save()
    #     return HttpResponse('success')

    def message_text(msg):
        """ 回复信息 """
        try:
            if len(msg.content) <= 5:  # 简单过滤 需求描述不足5字
                result = create_reply('您好！您的需求\n“{0}”\n过短，请详细描述'.format(
                    msg.content),
                                      message=msg)
                return HttpResponse(result.render())
            # TODO:有效期也要比较
            the_custom = Auth.objects.get(openid=msg.source,
                                          is_active=True).Customer  # 强断言必有账号
            req = Request(customer=the_custom,
                          group=the_custom.group,
                          description=str(msg.content),
                          registrar=User.objects.get(pk=1))
            req.save()
            logging.info('录入了需求：%s', msg)
            # 分解多任务
            for line in msg.content.split('\n'):
                line = line.lstrip().rstrip()
                if line:
                    task = Task(request=req, title=line)
                    task.save()
                    logging.info('分解了任务：%s', line)
                    # # 多线程调用AI
                    # detroit = Detroit()
                    # ai_task = threading.Thread(target=detroit.start,
                    #                            args=(task, msg.source))
                    # ai_task.start()
                    # # 异步调用AI

                    # logging.info('开启AI任务：%s', task)
            result = create_reply('您好！您的需求已受理，请稍后……', message=msg)
            return HttpResponse(result.render())
            # 转人工 已被否决
            # reply = TransferCustomerServiceReply(message=msg)
            # return HttpResponse(reply.render())
        except Exception as error:  # 任何错误将触发权限不足响应
            result = create_reply('您好！您未授权公众号服务或授权已过期，请先去个人中心授权\n{0}'.format(
                str(error)),
                                  message=msg)
            return HttpResponse(result.render())

    def event_click(msg):
        """菜单点击"""
        def click_help(m):
            """点击帮助文档"""
            result = ArticlesReply(message=m, articles=get_materials('help'))
            return HttpResponse(result.render())

        def click_service(m):
            """点击人工服务"""
            # result = TransferCustomerServiceReply(message=m) 转人工被否决
            result = create_reply('您好！请问有什么问题，请留言', message=m)
            return HttpResponse(result.render())

        click_handle_switch = {
            'help': lambda m: click_help(m),
            'service': lambda m: click_service(m),
        }
        return click_handle_switch[msg.key](msg)

    if request.method == 'GET' and request.GET:  # 微信验证通道
        try:
            token = 'bismarck'
            signature = request.GET['signature']
            timestamp = request.GET['timestamp']
            nonce = request.GET['nonce']
            echostr = request.GET['echostr']
            check_signature(token, signature, timestamp, nonce)
            logging.info('验证通过了' + echostr)
            return HttpResponse(echostr)
        except InvalidSignatureException:
            logging.info('验证失败')
            return HttpResponse('验证失败')
    elif request.method == 'POST' and request.body:
        msg = parse_message(request.body)
        msg_handle_switch = {
            'SubscribeEvent':
            lambda parameter_list: event_subscribe(parameter_list),
            'UnsubscribeEvent':
            lambda parameter_list: even_unsubscribe(parameter_list),
            # 'LocationEvent': event_location(msg),
            'TextMessage':
            lambda parameter_list: message_text(parameter_list),
            'ClickEvent':
            lambda parameter_list: event_click(parameter_list),
        }
        return msg_handle_switch[type(msg).__name__](msg)
    else:
        return HttpResponse(request.method + ' failed')


def geo_distance(lat1, lon1, lat2, lon2):
    """
    半正矢公式计算距离
    """
    radius = 6373  # m

    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) * math.sin(d_lat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) * math.sin(d_lon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c

    return d


def auth(request):
    """ 权限注册 http://docs.wechatpy.org/zh_CN/stable/CLIENT/jsapi.html """
    jsapi_client = WeChatJSAPI(CLIENT)
    jssdk_ticket = jsapi_client.get_jsapi_ticket()
    logging.info('jssdk_ticket：%s', jssdk_ticket)
    # https://developers.weixin.qq.com/doc/offiaccount/OA_Web_Apps/JS-SDK.html#62
    wx_config = {
        'debug':
        True,  # 开启调试模式,调用的所有api的返回值会在客户端alert出来，若要查看传入的参数，可以在pc端打开，参数信息会通过log打出，仅在pc端时才会打印。
        'appId': APP_ID,  # 必填，公众号的唯一标识
        'timestamp': int(time.time()),  # 必填，生成签名的时间戳
        'nonceStr': '342t5@#!~$fdghwer@#dsg',  # 必填，生成签名的随机串
        'signature': '',  # 必填，签名
        'jsApiList': ['openLocation', 'getLocation']  # 必填，需要使用的JS接口列表
    }
    wx_config['signature'] = jsapi_client.get_jsapi_signature(
        wx_config['nonceStr'], jssdk_ticket, wx_config['timestamp'],
        request.get_raw_uri())
    logging.info('WXConfig设置为：%s', wx_config)

    context = {
        'show_danger': 'display:none',
        'organs': '',
        'nickname': '',
        'openid': '',
        'location': '',
        'timestamp': wx_config['timestamp'],
        'signature': wx_config['signature'],
    }

    def get_group(organ):
        """获取/创建“公众号群”"""
        groups = Group.objects.filter(type='公众号', organ=organ)
        if len(groups) == 0:  # 机构未建公众号
            return Group.objects.create(name=organ.name + '公众号',
                                        type='公众号',
                                        organ=organ)
        else:
            return groups.first()

    def set_userinfo(user_info):
        """设置用户信息，另有位置信息通过JSSDK获取"""
        try:
            logging.info('获得用户信息：' + str(user_info))
            context['nickname'] = user_info['nickname']
            context['openid'] = user_info['openid']
        except Exception as error:
            logging.debug(error)
            return JsonResponse({'code': 911, 'msg': str(error)})

    if request.method == 'GET':  # 获取用户授权信息 参考url：https://blog.csdn.net/baidu_39416074/article/details/80923974
        code = request.GET['code'] if 'code' in request.GET else None
        if code:
            res = OAUTH_CLIENT.fetch_access_token(code)
            refresh_token = res['refresh_token']
            if OAUTH_CLIENT.check_access_token(
            ):  # 检查access_token 有效性 ， 如果无效则返回 4001， 拿着refresh_token 刷新access_token
                set_userinfo(OAUTH_CLIENT.get_user_info())
            else:
                res = OAUTH_CLIENT.refresh_access_token(refresh_token)
                set_userinfo(OAUTH_CLIENT.get_user_info())
        else:  # 如果code 不存在 则重定向到 之前的页面
            return HttpResponseRedirect(
                'https://open.weixin.qq.com/connect/oauth2/authorize?appid=wx5c508e7ffd72e463&REDIRECT_URI=http%3a%2f%2fapi.jlss.vip%2fwx%2fauth&response_type=code&scope=snsapi_userinfo&state=reg#wechat_redirect'
            )

        return render(request, 'auth.html', context)

    if request.method == 'POST' and request.POST:
        context['nickname'] = request.POST['nickname']
        context['openid'] = request.POST['openid']
        organ = Organ.objects.get(pk=request.POST['organ'])
        group = get_group(organ)
        context['dept'] = request.POST['dept']
        latitude = float(request.POST['latitude'])
        longitude = float(request.POST['longitude'])

        # 检查必填字段
        if (context['dept'] is None) or context['dept'] == '' or (
                context['nickname'] is None) or context['nickname'] == '':
            context['show_danger'] = ''
            return render(request, 'auth.html', context)
        # 验证位置
        if geo_distance(organ.latitude, organ.longitude, latitude,
                        longitude) > organ.range:
            context['show_danger'] = ''
            return render(request, 'auth.html', context)
        user_auth = Auth.objects.filter(
            openid=context['openid']).first() if Auth.objects.filter(
                openid=context['openid']).exists() else None
        # 已授权 更新资料&返回授权成功
        if user_auth:
            user_auth.date_auth = timezone.now()
            user_auth.is_active = True
            user_auth.Customer.dept = context['dept']
            user_auth.Customer.group = group
            user_auth.save()
            logging.info('更新用户资料：%s' % str(user_auth))
            return render(request, 'success.html', context)

        # 直接新增用户 新增权限 因为所有其他情况都已被排除
        the_custom = Customer(nickname=context['nickname'],
                              wechat=context['openid'],
                              dept=context['dept'],
                              group=group,
                              organ=group.organ)
        the_custom.save()
        the_auth = Auth(Customer=the_custom,
                        openid=context['openid'],
                        latitude=latitude,
                        longitude=longitude)
        the_auth.save()
        return render(request, 'success.html', context)


def reply(request):
    """ POST 传递消息给openid指定的客户 """
    client = WeChatClient(APP_ID, SECRET)
    logging.info('get post:%s' % request.POST['openid'])
    res = client.message.send_text(request.POST['openid'],
                                   request.POST['text'])
    return HttpResponse(status=200)


def mp_verify(request):
    """ 跳转静态目录下的验证文件 """
    return HttpResponseRedirect(settings.STATIC_URL +
                                'MP_verify_QiNbvMFQsmegMWio.txt')


def minip_verify(request):
    """ 跳转静态目录下的验证文件_小程序 """
    return HttpResponseRedirect(settings.STATIC_URL + 'NvrFbr8lB7.txt')


def location(request):
    """ GET 给定地理位置找相关机构 """
    def get_organ(latitude, longitude):
        organs = []
        for organ in Organ.objects.all():
            if geo_distance(organ.latitude, organ.longitude, latitude,
                            longitude) <= organ.range:
                organs.append(organ)
        if len(organs) == 0:  # 地理范围内没有找到任何机构则以试用机构身份注册
            organs.append(Organ.objects.get(pk=131))
        return organs

    organ = get_organ(float(request.GET['latitude']),
                      float(request.GET['longitude']))[0]
    return JsonResponse({'id': organ.id, 'name': organ.name})

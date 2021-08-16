from django.core.mail import send_mail

from rest_framework.decorators import api_view
from api.models import *
from .models import *
from ai.views import *
from wx.views import *
from smtplib import SMTPException
from datetime import datetime

MATERIALS_FOR = {
    'welcome': 'aRGRZQzzMPvVvdIHVYUAg1wqAGjBEO8fgmFo7JN2DLM',
    'help': 'aRGRZQzzMPvVvdIHVYUAg239kv_uQodYBVarxo9d19U',
}
APP_ID = 'wxd4597710cd1e0f38'
SECRET = '3a72f54a6e6ac13fb82de7bade45fa77'
REDIRECT_URI = quote('http://api.jlss.vip/wx/auth', safe='')
CLIENT = WeChatClient(APP_ID, SECRET)
OAUTH_CLIENT = WeChatOAuth(APP_ID, SECRET, REDIRECT_URI)
logging.config.fileConfig('log.conf')
logger = logging.getLogger('3rd')


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
            statistic = Statistic(create_time=datetime.now())
            if len(msg.content) <= 5:  # 简单过滤 需求描述不足5字
                result = create_reply('您好！您的需求\n“{0}”\n过短，请详细描述'.format(msg.content), message=msg)
                return HttpResponse(result.render())
            # TODO:有效期也要比较
            the_custom = Auth.objects.get(openid=msg.source, is_active=True).Customer  # 强断言必有账号
            req = Request(customer=the_custom,
                          group=the_custom.group,
                          description=str(msg.content),
                          registrar=User.objects.get(pk=1))
            req.save()
            statistic.request = req
            logging.info('录入了需求：%s', msg)
            # 分解多任务
            for line in msg.content.split('\n'):
                line = line.lstrip().rstrip()
                if line:
                    task = Task(request=req, title=line)
                    task.save()
                    statistic.task = task
                    logging.info('分解了任务：%s', line)
                    # 多线程调用AI
                    detroit = Detroit(task, statistic)
                    ai_task = threading.Thread(target=detroit.start, args=(task, msg.source))
                    ai_task.start()
                    # 异步调用AI

                    logging.info('开启AI任务：%s', task)
            result = create_reply('您好！您的需求已受理，请稍后……', message=msg)
            return HttpResponse(result.render())
            # 转人工 已被否决
            # reply = TransferCustomerServiceReply(message=msg)
            # return HttpResponse(reply.render())
        except Exception as error:  # 任何错误将触发权限不足响应
            result = create_reply('您好！您未授权公众号服务或授权已过期，请先去个人中心授权\n{0}'.format(str(error)),
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
            'SubscribeEvent': lambda parameter_list: event_subscribe(parameter_list),
            'UnsubscribeEvent': lambda parameter_list: even_unsubscribe(parameter_list),
            'TextMessage': lambda parameter_list: message_text(parameter_list),
            'ClickEvent': lambda parameter_list: event_click(parameter_list),
        }
        return msg_handle_switch[type(msg).__name__](msg)
    else:
        return HttpResponse(request.method + ' failed')


def ask(request):
    def reply(email: str, replyMsg: str, _statistic: Statistic, taskid: int = None, name: str = None):
        """ 回复邮件 """
        recipient_list = [email]
        try:
            send_mail('文献传递', replyMsg, 'jlss202101@vip.163.com', recipient_list, fail_silently=False)

        except SMTPException:
            logging.error(SMTPException)
            reply(email, replyMsg, _statistic)

        _statistic.finish_time = datetime.now()
        _statistic.save()

    if request.method == 'POST' and request.POST:
        statistic = Statistic(create_time=datetime.now())
        openid = request.POST['openid']
        content = request.POST['query']
        try:
            if len(content) <= 5:  # 简单过滤 需求描述不足5字
                return JsonResponse({'msg': '需求过短'})
            # TODO:有效期也要比较
            if not Auth.objects.filter(openid=openid, is_active=True).exists():
                return JsonResponse({'msg': '未授权或过期'})
            the_custom = Auth.objects.get(openid=openid, is_active=True).Customer  # 强断言必有账号
            req = Request(customer=the_custom,
                          group=the_custom.group,
                          description=str(content),
                          registrar=User.objects.get(pk=1))
            req.save()
            statistic.request = req
            logging.info('录入了需求：%s', content)
            # 分解多任务
            task = Task(request=req, title=content.lstrip().rstrip(), data_received=datetime.now(), status='progress')
            task.save()
            statistic.task = task
            logging.info('创建了任务：%s', task.title)
            # 多线程调用AI
            detroit = Detroit(task, statistic)
            ai_task = threading.Thread(target=detroit.start, args=(the_custom.email, task.id, reply))
            ai_task.start()
            # 异步调用AI
            logging.info('开启AI任务：%s', task)
            return JsonResponse({'msg': '需求已受理'})
        except Exception as error:  # 任何错误将触发权限不足响应
            return JsonResponse({'msg': '服务器错误'})


def geo_distance(lat1, lon1, lat2, lon2):
    """
    半正矢公式计算距离
    """
    radius = 6371000  # m

    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) * math.sin(d_lat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) * math.sin(d_lon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c

    return d


def auth(request):
    context = {
        'show_danger': 'display:none',
        'organs': '',
        'nickname': '',
        'openid': '',
        'location': '',
    }

    def get_group(organ):
        """获取/创建“公众号群”"""
        groups = Group.objects.filter(type='公众号', organ=organ)
        if len(groups) == 0:  # 机构未建公众号
            return Group.objects.create(name=organ.name + '公众号', type='公众号', organ=organ)
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

    if request.method == 'GET':
        code = request.GET['code'] if 'code' in request.GET else None
        # https://api.weixin.qq.com/sns/jscode2session?appid=APPID&secret=SECRET&js_code=JSCODE&grant_type=authorization_code
        result = requests.get('https://api.weixin.qq.com/sns/jscode2session',
                              params={'appid': APP_ID, 'secret': SECRET, 'js_code': code,
                                      'grant_type': 'authorization_code'}
                              ).json()
        return JsonResponse(result)

    if request.method == 'POST' and request.POST:
        try:
            context['nickname'] = request.POST['nickname']
            context['openid'] = request.POST['openid']
            context['email'] = request.POST['email']
            organ = Organ.objects.get(pk=request.POST['organ'])
            group = get_group(organ)
            context['dept'] = request.POST['dept']
            latitude = float(request.POST['latitude'])
            longitude = float(request.POST['longitude'])

            # 检查必填字段
            # if (context['dept'] is None) or context['dept'] == '' or (
            #         context['nickname'] is None) or context['nickname'] == '':
            #     context['show_danger'] = ''
            #     return render(request, 'auth.html', context)
            # 验证位置
            # if geo_distance(organ.latitude, organ.longitude, latitude,
            #                 longitude) <= organ.range:
            #     context['show_danger'] = ''
            #     return render(request, 'auth.html', context)
            user_auth = Auth.objects.filter(openid=context['openid']).first() \
                if Auth.objects.filter(openid=context['openid']).exists() else None
            # 已授权 更新资料&返回授权成功
            if user_auth:
                user_auth.date_auth = timezone.now()
                user_auth.is_active = True
                user_auth.save()
                user_customer = Customer.objects.filter(wechat=context['openid']).first() \
                    if Customer.objects.filter(wechat=context['openid']).exists() else None
                if user_customer:
                    # 更新用户信息 必有
                    user_customer.nickname = context['nickname']
                    user_customer.dept = context['dept']
                    user_customer.email = context['email']
                    user_customer.group = group
                    user_customer.save()
                logging.info('更新用户资料：%s' % context['openid'])
                return JsonResponse({'更新用户': user_auth.openid})

            # 直接新增用户 新增权限 因为所有其他情况都已被排除
            the_custom = Customer(nickname=context['nickname'], wechat=context['openid'], dept=context['dept'],
                                  email=context['email'], group=group, organ=group.organ)
            the_custom.save()
            the_auth = Auth(Customer=the_custom, openid=context['openid'], latitude=latitude, longitude=longitude)
            the_auth.save()
            return JsonResponse({'新增用户': the_auth.openid})
        except Exception as identifier:
            logging.error('授权错误:%s', identifier)
            return JsonResponse({'授权错误': identifier})

    return JsonResponse({'err': '没有匹配method=%s' % request.method})


def reply(request):
    """ POST 传递消息给openid指定的客户 """
    client = WeChatClient(APP_ID, SECRET)
    logging.info('get post:%s' % request.POST['openid'])
    res = client.message.send_text(request.POST['openid'],
                                   request.POST['text'])
    return HttpResponse(status=200)


def mp_verify(request):
    """ 跳转静态目录下的验证文件 """
    return HttpResponseRedirect(settings.STATIC_URL + 'MP_verify_QiNbvMFQsmegMWio.txt')


def minip_verify(request):
    """ 跳转静态目录下的验证文件_小程序 """
    return HttpResponseRedirect(settings.STATIC_URL + 'NvrFbr8lB7.txt')


def location(request):
    """ GET 给定地理位置找相关机构 """

    def get_organ(latitude, longitude):
        organs = []
        for organ in Organ.objects.all():
            if geo_distance(organ.latitude, organ.longitude, latitude, longitude) <= organ.range:
                organs.append(organ)
        if len(organs) == 0:  # 地理范围内没有找到任何机构则以试用机构身份注册
            organs.append(Organ.objects.get(pk=131))
        return organs

    organ = get_organ(float(request.GET['latitude']), float(request.GET['longitude']))[0]
    return JsonResponse({'id': organ.id, 'name': organ.name})


def email_to(request):
    """回复邮件"""
    email = request.POST['email']
    replyMsg = request.POST['replyMsg']
    taskid = request.POST['taskid']
    state = request.POST['state']
    channel = request.POST['channel']
    recipient_list = [email]
    try:
        send_mail('文献传递', replyMsg, 'jlss202101@vip.163.com', recipient_list, fail_silently=False)
        return JsonResponse({'msg': 'ok'})
    except SMTPException:
        logging.error(SMTPException)
        email_to(request)
    finally:
        if channel == '医生医事':
            r = requests.get(f'https://ysfwapp.juhe.com.cn/trans/result?taskid={taskid}&state={state}')
        if channel == 'KIS':
            r = requests.get(f'https://jksmed.juhe.com.cn/trans/result?taskid={taskid}&state={state}')


@api_view(['POST'])
def ask4ysys(request):
    def reply(email: str, replyMsg: str, _statistic: Statistic, taskid: int, name: str):
        """回复邮件"""
        recipient_list = [email]
        try:
            send_mail('文献传递', replyMsg, 'jlss202101@vip.163.com', recipient_list, fail_silently=False)
        except SMTPException:
            logging.error(SMTPException)
            reply(email, replyMsg, _statistic, taskid, name)
        finally:
            if taskid:
                r = requests.get(f'https://ysfwapp.juhe.com.cn/trans/result?taskid={taskid}&state=1')

        _statistic.finish_time = datetime.now()
        _statistic.save()

    if request.method == 'POST' and request.POST:
        openid = request.POST['openid']
        name = request.POST['name']
        email = request.POST['email']
        jid = request.POST['jid']
        content = request.POST['content']
        # if name == '医生医试':  #医生医事
        #     group = Group.objects.get(pk=419)
        #     organ = Organ.objects.get(pk=225)
        # else:
        #     return JsonResponse({'msg': '服务器错误', 'error': 'openid不可用'})
        group = Group.objects.get(pk=419)
        organ = Organ.objects.get(pk=225)
        try:
            if len(content) <= 5:  # 简单过滤 需求描述不足5字
                return JsonResponse({'msg': '需求过短'})

            the_custom, created = Customer.objects.update_or_create(wechat=openid, is_active=True,
                                                                    defaults={'nickname': name, 'email': email,
                                                                              'group': group, 'organ': organ}
                                                                    )
            statistic = Statistic(create_time=datetime.now())
            req = Request(customer=the_custom,
                          group=the_custom.group,
                          description=str(content),
                          registrar=User.objects.get(pk=1))
            req.save()
            statistic.request = req
            logging.info('录入了需求：%s', content)
            # 分解多任务
            task = Task(request=req,
                        title=content.lstrip().rstrip(),
                        status='progress')
            task.save()
            statistic.task = task
            logging.info('创建了任务：%s', task.title)
            # 多线程调用AI
            detroit = Detroit(task, statistic)
            ai_task = threading.Thread(target=detroit.start,
                                       args=(the_custom.email, task.id, reply, '')
                                       )
            ai_task.start()
            # # 异步调用AI
            # logging.info('开启AI任务：%s', task)
            return JsonResponse({'msg': '需求已受理', 'taskid': task.pk})
        except Exception as error:
            return JsonResponse({'msg': '服务器错误', 'error': str(error)})


@api_view(['POST'])
def ask4open(request):
    def reply(email: str, replyMsg: str, _statistic: Statistic, taskid: int, name: str):
        """回复邮件"""
        recipient_list = [email]
        try:
            send_mail('文献传递', replyMsg, 'jlss202101@vip.163.com', recipient_list, fail_silently=False)
        except SMTPException:
            logging.error(SMTPException)
            reply(email, replyMsg, _statistic, taskid, name)
        finally:
            if taskid:
                if name == '医生医事':
                    r = requests.get(f'https://ysfwapp.juhe.com.cn/trans/result?taskid={taskid}&state=1')
                if name == 'KIS':
                    r = requests.get(f'https://jksmed.juhe.com.cn/trans/result?taskid={taskid}&state=1')
        _statistic.finish_time = datetime.now()
        _statistic.save()

    if request.method == 'POST' and request.POST:
        logging.info('收到三方需求：%s', request.POST.__dict__)
        openid = request.POST['openid']
        name = request.POST['name']
        email = request.POST['email']
        jid = request.POST['jid']
        content = request.POST['content']
        if name == '医生医事':  # 医生医事
            group = Group.objects.get(pk=419)
            organ = Organ.objects.get(pk=225)
        elif name == 'FPD':  # FPD
            group = Group.objects.get(pk=457)
            organ = Organ.objects.get(pk=111)
        elif name == 'KIS':  # 整合系统
            group = Group.objects.get(pk=461)
            organ = Organ.objects.get(pk=111)
        elif name == 'CQVIP':  # 维普智立方
            group = Group.objects.get(pk=462)
            organ = Organ.objects.get(pk=244)
        else:
            logging.info('错误，返回错误：%s', {'msg': '服务器错误', 'error': 'openid不可用'})
            return JsonResponse({'msg': '服务器错误', 'error': 'openid不可用'})
        try:
            if len(content) <= 5:  # 简单过滤 需求描述不足5字
                logging.info('错误，返回错误：%s', {'msg': '需求过短'})
                return JsonResponse({'msg': '需求过短'})

            the_custom, created = Customer.objects.update_or_create(wechat=openid, is_active=True,
                                                                    defaults={'nickname': name, 'email': email,
                                                                              'group': group, 'organ': organ}
                                                                    )
            statistic = Statistic(create_time=datetime.now())
            req = Request(customer=the_custom,
                          group=the_custom.group,
                          description=str(content),
                          registrar=User.objects.get(pk=1))
            req.save()
            statistic.request = req
            logging.info('录入了需求：%s', content)
            # 分解多任务
            task = Task(request=req,
                        title=content.lstrip().rstrip(),
                        status='progress')
            task.save()
            statistic.task = task
            logging.info('创建了任务：%s', task.title)
            # 多线程调用AI
            detroit = Detroit(task, statistic)
            ai_task = threading.Thread(target=detroit.start,
                                       args=(the_custom.email, task.id, reply, name))
            ai_task.start()
            # # 异步调用AI
            # logging.info('开启AI任务：%s', task)
            logging.info('受理需求：%s', {'msg': '需求已受理', 'taskid': task.pk})
            return JsonResponse({'msg': '需求已受理', 'taskid': task.pk})
        except Exception as error:
            logging.info('错误，返回错误：%s', {'msg': '服务器错误', 'error': str(error)})
            return JsonResponse({'msg': '服务器错误', 'error': str(error)})

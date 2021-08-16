import random
import string

from django.db import models

# class Role(models.Model):
#     name = models.CharField('权限名', max_length=32, unique=True)

#     def __str__(self):
#         return self.name


class User(models.Model):
    username = models.CharField('用户名', max_length=255, unique=True)
    password = models.CharField('密码', max_length=128)
    avatar = models.ImageField('头像', upload_to='upload/avatar/', blank=True)
    nickname = models.CharField('显示名', max_length=255)
    # role = models.ForeignKey(Role, on_delete=models.PROTECT)
    role = models.CharField('权限组',
                            max_length=8,
                            choices=(
                                ('dev', '开发员'),
                                ('admin', '管理员'),
                                ('user', '客服员'),
                                ('seller', '销售员'),
                            ))
    date_joined = models.DateTimeField('加入时间', auto_now_add=True)
    is_active = models.BooleanField('是否激活', default=True)

    def __str__(self):
        return '%s(%s)' % (self.nickname, self.username)


class Region(models.Model):
    name = models.CharField('大区名', max_length=32, unique=True)
    money = models.DecimalField('余额',
                                max_digits=5,
                                decimal_places=2,
                                default=0.00)

    def __str__(self):
        return self.name


class SellerRegion(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.PROTECT)

    def __str__(self):
        return '%s:%s' % (self.region, self.seller)


class Organ(models.Model):
    name = models.CharField('机构名称', max_length=128)
    contact = models.CharField('联系人', blank=True, max_length=64)
    tel = models.CharField('联系电话', blank=True, max_length=32)
    seller = models.ForeignKey(SellerRegion, on_delete=models.CASCADE)
    memo = models.CharField('备注', blank=True, max_length=255)
    date_joined = models.DateTimeField('加入时间', auto_now_add=True)
    is_active = models.BooleanField('是否激活', default=True)
    vip = models.SmallIntegerField('VIP等级', default=0)
    latitude = models.FloatField('授权地纬度', default=0)
    longitude = models.FloatField('授权地经度', default=0)
    range = models.IntegerField('授权范围(m)', default=1000)
    expiry = models.IntegerField('授权有效期(天)', default=7)
    code = models.CharField('邀请码', max_length=6, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = short_url()
        super(Organ, self).save(*args, **kwargs)


class Group(models.Model):
    name = models.CharField('群名称', max_length=64)
    type = models.CharField('群类型', max_length=8)
    gid = models.CharField('群号码', blank=True, max_length=32)
    memo = models.CharField('备注', blank=True, max_length=255)
    date_joined = models.DateTimeField('加入时间', auto_now_add=True)
    is_active = models.BooleanField('是否激活', default=True)
    organ = models.ForeignKey(Organ, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Customer(models.Model):
    avatar = models.ImageField('头像', upload_to='upload/avatar/', blank=True)
    nickname = models.CharField('显示名', max_length=64)
    password = models.CharField('密码', max_length=128, blank=True, null=True)
    email = models.EmailField('邮箱', blank=True, null=True)
    work_id = models.CharField('工号', blank=True, null=True, max_length=32)
    dept = models.CharField('部门', blank=True, null=True, max_length=32)
    qq = models.CharField('QQ号', blank=True, null=True, max_length=32)
    wechat = models.CharField('微信号', blank=True, null=True, max_length=32)
    memo = models.CharField('备注', blank=True, null=True, max_length=255)
    date_joined = models.DateTimeField('加入时间', auto_now_add=True)
    is_active = models.BooleanField('是否激活', default=True)
    group = models.ForeignKey(Group, on_delete=models.PROTECT)
    organ = models.ForeignKey(Organ, on_delete=models.CASCADE)

    def __str__(self):
        return self.nickname


class ResType(models.Model):
    name = models.CharField('资源名', max_length=32, unique=True)

    def __str__(self):
        return self.name


class Journal(models.Model):
    name = models.CharField('刊名', max_length=255)
    year = models.CharField('年份', max_length=32)

    def __str__(self):
        return '%s(%s)' % (self.name, self.year)


languages = [
    ('ZH', '中文'),
    ('F', '洋文'),
]


def short_url(size=6, chars=string.digits + string.ascii_lowercase+r'!*-_'):
    result = ''
    while True:
        for _ in range(size):
            result += random.choice(chars)
        if not Resource.objects.filter(short=result):
            break
    return result


class Resource(models.Model):
    title = models.CharField('标题', max_length=2550)
    attachment = models.FileField('文件路径',
                                  max_length=2550,
                                  upload_to='uploads/res/%Y/%m/%d/',
                                  blank=True)
    download = models.URLField('第三方下载地址', max_length=1000, blank=True)
    size = models.PositiveIntegerField('文件大小', default=0)
    restype = models.ForeignKey(ResType, on_delete=models.PROTECT)
    lang = models.CharField('语种',
                            max_length=12,
                            choices=languages,
                            default='ZH')
    cost = models.DecimalField('花费',
                               max_digits=5,
                               decimal_places=2,
                               default=0.00)
    uid = models.CharField('唯一标准编号', max_length=64, blank=True, null=True)
    source = models.CharField('来源', max_length=1024, blank=True, null=True)
    short = models.CharField('短地址', max_length=6, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.short:
            self.short = short_url()
        super(Resource, self).save(*args, **kwargs)


class JournalRes(models.Model):
    res = models.ForeignKey(Resource, on_delete=models.CASCADE)
    journal = models.ForeignKey(Journal, on_delete=models.PROTECT)


server_status = [
    ('waiting', '等待中'),
    ('progress', '进行中'),
    ('success', '已成功'),
    ('failed', '已失败'),
]


class Request(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    group = models.ForeignKey(Group, on_delete=models.PROTECT)
    description = models.TextField('需求描述')
    registrar = models.ForeignKey(User, on_delete=models.PROTECT)
    date_registered = models.DateTimeField('录入时间', auto_now_add=True)
    status = models.CharField('服务状态',
                              max_length=32,
                              choices=server_status,
                              default='waiting')

    def __str__(self):
        return self.description


class Task(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    title = models.CharField('任务标题', max_length=2550)
    status = models.CharField('服务状态',
                              max_length=32,
                              choices=server_status,
                              default='waiting')
    receiver = models.ForeignKey(User,
                                 blank=True,
                                 null=True,
                                 on_delete=models.PROTECT,
                                 related_name='receiver_user')
    data_received = models.DateTimeField('响应时间', null=True, blank=True)
    replier = models.ForeignKey(User,
                                blank=True,
                                null=True,
                                on_delete=models.PROTECT,
                                related_name='replier_user')
    data_replied = models.DateTimeField('回复时间', null=True, blank=True)
    resource = models.ForeignKey(Resource,
                                 blank=True,
                                 null=True,
                                 on_delete=models.PROTECT)
    count = models.IntegerField('资源量', default=1)

    def __str__(self):
        return self.title


class Zone(models.Model):
    organ = models.ForeignKey(Organ, on_delete=models.CASCADE)
    latitude = models.FloatField('授权地纬度', default=0)
    longitude = models.FloatField('授权地经度', default=0)
    range = models.IntegerField('授权范围(m)', default=1000)


class Statistic(models.Model):
    request = models.ForeignKey(Request, on_delete=models.SET_NULL, null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True)
    create_time = models.DateTimeField('创建时间', default=None)
    finish_time = models.DateTimeField('完成时间', default=None)
    author = models.CharField('作者', max_length=2550, null=True, blank=True)
    last_author = models.CharField('最新作者', max_length=2550, null=True, blank=True)
    title = models.TextField('标题', null=True, blank=True)
    doi = models.CharField('doi', max_length=50, null=True, blank=True)
    pmid = models.CharField('pmid', max_length=50, null=True, blank=True)
    pii = models.CharField('pii', max_length=50, null=True, blank=True)
    pmc = models.CharField('pmc', max_length=50, null=True, blank=True)
    issn = models.CharField('issn', max_length=50, null=True, blank=True)
    year = models.CharField('年', max_length=10, null=True, blank=True)
    volume = models.CharField('卷', max_length=255, null=True, blank=True)
    pages = models.CharField('页码', max_length=500, null=True, blank=True)
    resource = models.ForeignKey(Resource, on_delete=models.SET_NULL, null=True, blank=True)
    result = models.CharField('任务结果', max_length=10, choices=(
        ('SU', '找到资源'),
        ('FA', '查找失败'),
        ('TH', '任务丢弃'),
    ))
    category = models.IntegerField('需求类型', choices=(
        (0, '特殊需求'),
        (1, '正常需求'),
        (2, '公告'),
        (3, '无效言论'),
    ))
    channel = models.CharField('任务途径', max_length=10, choices=(
        ('AI', 'AI查找'),
        ('PE', '人工查找'),
    ))
    re_lib = models.CharField('正则解析结果', max_length=10, null=True, blank=True)
    retrieval_str = models.CharField('正则提取的关键词类型', max_length=2550, null=True, blank=True)
    resource_lib = models.CharField('资源库', max_length=10, null=True, blank=True)

    class meta:
        db_table = 'api_statistic'


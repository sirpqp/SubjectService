import logging
import re
from datetime import datetime
from Sentry.SD import SingleDownload
import requests
from lxml import etree
import xml.etree.cElementTree as ET

from api.models import Resource, ResType, Task, User, Statistic
from .solr import Solr
from Bio import Entrez
import random
from requests.exceptions import Timeout
import json

Entrez.email = 'odinshaw@live.com'

logging.config.fileConfig('log.conf')
logger = logging.getLogger('ai')

"""
time: 2021-08-13
operator: quan
content: add statistic model
"""


class ReLibs:
    """ 正则库 """

    def __init__(self, text: str):
        self.text = text

    @staticmethod
    def doi(text: str):
        pattern = re.compile(r'\b10.\d{4}/\S+\b', re.I)
        _match = re.search(pattern, text)
        if _match:
            return _match.group()
        else:
            return None

    @staticmethod
    def pmid(text: str):
        pattern = re.compile(r'\b\d{7,8}\b', re.I)
        _match = re.search(pattern, text)
        if _match:
            return _match.group()
        else:
            return None

    def search(self):
        _doi = self.doi(self.text)
        _pmid = self.pmid(self.text)
        if _doi:
            return f'doi:{_doi}'
        elif _pmid:
            return f'pmid:{_pmid}'
        else:
            return 'title:"{}"'.format(self.text.replace('\"', ''))


class Cite:
    author_list = []
    last_author = ''
    title = ''
    doi = ''
    pmid = ''
    pii = ''
    pmc = ''
    issn = ''
    year = ''
    volume = ''
    issue = ''
    pages = ''
    source = ''
    fulltext = ''
    lang = 'F'

    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value
        self.search()

    def search(self):
        if self.key == 'pmid':
            self.pmid = self.value
            self.summary(self.pmid)
        elif self.key == 'doi':
            self.doi = self.value
            doi_handle = Entrez.esearch(term=f'{self.doi}[doi]', db='pubmed')
            doi_record = Entrez.read(doi_handle)
            if doi_record['Count'] == '1':
                self.pmid = doi_record['IdList'][0]
                self.summary(self.pmid)
            else:
                return None
        elif self.key == 'title':
            self.title = self.value
            title_handle = Entrez.esearch(term=f'{self.title}[title]', db='pubmed')
            title_record = Entrez.read(title_handle)
            if title_record['Count'] == '1':
                self.pmid = title_record['IdList'][0]
                self.summary(self.pmid)
            else:
                return None

    def summary(self, pmid: str):
        Detroit.log('KP', f'将在Pubmed查询{pmid}')
        handle = Entrez.esummary(db='pubmed', id=pmid)
        record = Entrez.read(handle)
        if len(record) == 1:
            Detroit.log('KP', f'查询到{len(record)}条结果：{record}')
            self.title = record[0].get('Title')
            self.author_list = record[0].get('AuthorList')
            self.last_author = record[0].get('LastAuthor')
            self.doi = record[0].get('DOI')
            self.source = record[0].get('Source')
            self.pmc = record[0].get('ArticleIds').get('pmc')
            self.pii = record[0].get('ArticleIds').get('pii')
            if record[0]['ISSN']:
                self.issn = record[0]['ISSN']
            elif record[0]['ESSN']:
                self.issn = record[0]['ESSN']
            if record[0]['PubDate']:
                self.year = record[0]['PubDate'].split(' ')[0]
            elif record[0]['EPubDate']:
                self.year = record[0]['EPubDate'].split(' ')[0]
            self.volume = record[0].get('Volume')
            self.issue = record[0].get('Issue')
            self.pages = record[0].get('Pages')
        else:
            return None


class Detroit:
    """ Detroit: Become human """
    RESULT = None
    EXP = None
    CITATION = None
    _Resource = None

    def __init__(self, task: Task, statistic: Statistic = None):
        self.task = task

    @staticmethod
    def log(speaker: str, msg: str):
        """ 记录日志 """
        logger.info(f'[{speaker}]{msg}')
        return

    @staticmethod
    def report(request: str):
        result = {'request': request, 'exp': None, 'solr': None}
        _re = ReLibs(request)
        result['exp'] = _re.search()
        if result['exp']:
            key = result['exp'].split(':')[0]
            value = result['exp'].split(':')[1]
            if key == 'pmid':
                c = Cite(key, value)
                _doi = c.doi
                if _doi:
                    result['exp'] = 'doi:' + _doi
            so = Solr()
            result['solr'] = so.search(result['exp'])
            return result
        else:
            return result

    def pmc(self, cit: Cite):
        self.log('PC', '检定PMC')
        if cit.pmc and cit.pii:
            pdf = f'https://www.ncbi.nlm.nih.gov/pmc/articles/{cit.pmc}/pdf/{cit.pii}.pdf'
            # TODO: ping pdf
            cit.fulltext = pdf
        return cit

    def jh(self, cit: Cite):
        """
        通过solr在聚合库中进行查找pdf全文
        :param cit: Cite
        :return: cit
        """
        self.log('SYS', '开始在jh中查询...')
        so = Solr()
        cate_map = {'doi': cit.doi, 'pmid': cit.pmid, 'title': cit.title}
        result = None
        for key, value in cate_map.items():
            if value:
                exp = f'{key}:{value}'
                self.log('JH', f'2.在solr中查询{key},表达式={exp}...')
                result = so.search(exp)
                self.log('JH', f'2.solr查询结果={result}')

            if result:
                if result['doi']:
                    cit.doi = result['doi']
                if result['title']:
                    cit.title = result['title']
                cit.lang = result['lang']
                cit.fulltext = result['download']

        return cit

    def sci(self, cit: Cite):
        """ 在sci中查找 """
        self.log('PC', '检定Scihub')
        if not cit.doi:
            self.log('SCI', '检定非法，Scihub只受理DOI')
            return cit
        domain_list = ['https://sci-hub.do', 'https://sci-hub.se', 'https://sci-hub.st']

        try:
            domain = domain_list[random.randint(0, len(domain_list) - 1)]
            Detroit.log('SCI', f'随机分配到域名{domain}')
        except Exception as identifier:
            Detroit.log('SCI', f'PING错误:{identifier}')
            return cit

        # 爬取全文地址
        try:
            # https://sci-hub.se/10.1001/archopht.1991.01080080021010
            headers = {
                'User-Agent':
                    'User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, '
                    'like Gecko) Chrome/56.0.2924.87 Safari/537.36 '
            }
            html = requests.get('%s/%s' % (domain, cit.doi),
                                headers=headers,
                                timeout=6.1).text
            if html:
                pdf = re.search(r'location.href=\'(\S+.pdf)', html).group(1)
                pdf = pdf.replace('\\', '')
                if not pdf.startswith('http'):
                    pdf = 'http:%s' % pdf
                Detroit.log('SCI', f'爬得全文地址:{pdf}')
                cit.fulltext = pdf
                cit.lang = 'F'
            return cit
        except Timeout as identifier:
            Detroit.log('SCI', f'超时重试')
            return self.sci(cit)
        except Exception as identifier:
            Detroit.log('SCI', f'爬取全文地址错误:{identifier}')
            return cit

    def sd(self, cit: Cite):
        """
        sd检索
        :param cit: Cite
        :return: Cite
        """
        self.log('PC', '检定单点下载')
        sd = SingleDownload()
        cate_map = {'pmc': cit.pmc, 'pmid': cit.pmid, 'doi': cit.doi, 'title': cit.title}
        for key, value in cate_map.items():
            if value:
                self.log('SD', f'查询{key}:{value}')
                cit.fulltext = sd.download(value)
                self.log('SD', f'查询{key}结果:{cit.fulltext}')

            if cit.fulltext:
                break
        self.log('SD', f'查找结果:{cit.__dict__}')
        return cit

    def resource(self, cit: Cite):
        """
        手动下载的全文检索
        :param cit: Cite
        :return: Cite
        """
        result = ''
        if cit.doi:
            result = Resource.objects.filter(uid=cit.doi).order_by('-id')
        if (not result) and cit.pmid:
            result = Resource.objects.filter(uid=cit.pmid).order_by('-id')
        if result:
            _Resource = result[0]
            resp = requests.get(f'http://api.jlss.vip/s/{_Resource.short}')
            if (resp.status_code == 200) and resp.text.strip() != '对不起,全文已丢失!':
                self._Resource = _Resource
                cit.fulltext = _Resource.download if _Resource.download else resp.url
            else:
                _Resource.uid = None
                _Resource.save()

        return cit

    def play_pmc(self, cit: Cite):
        """
        pmc检索
        :param cit: Cite
        :return: Cite
        """
        if not cit.pmc:
            return cit
        pmc_ = str(cit.pmc)
        if not(pmc_.startswith('PMC') or pmc_.startswith('pmc')):
            cit.pmc = 'PMC' + pmc_

        if cit.pmc and cit.pii:
            pdf = f'https://www.ncbi.nlm.nih.gov/pmc/articles/{cit.pmc}/pdf/{cit.pii}.pdf'
            # TODO: ping pdf
            cit.fulltext = pdf
            return cit

        url = f'https://www.ncbi.nlm.nih.gov/pmc/articles/{cit.pmc}/'
        headers = {
            'authority': 'www.ncbi.nlm.nih.gov',
            'cache-control': 'max-age=0',
            'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'sec-ch-ua-mobile': '?0',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cookie': 'ncbi_sid=5CBC70B4255B939A_9B1DSID; _ga=GA1.2.1144160845.1619407228; _gid=GA1.2.150053158.1629163631; pmc.article.report=; WebEnv=1lUMkn%405CBC70B4255B939A_9B1DSID; ncbi_pinger=N4IgDgTgpgbg+mAFgSwCYgFwgIIBYCcAHAAykCMA7AKxkBCAogML5WmkBMAImZwMz25enRr2IA6MmIC2cXCAA0IAMYAbZEoDWAOygAPAC6ZQxTCABmAVxUqAtPr36barRoDOT5K/3zL1mzGQoAHcfK1t7Aw8XV3lkLR0IGyCIAEMweTAUgHMoG1c0KAAjFIh5Ev11FVzMnIUQMlNyyursqDr2UzALQqkodEVeTu7e/pA5LBTCr1SlQ0UqU3aTLDwiNkoaBmZWNi4efkFhUQlpWXaGrC6evowrkYxJ6ZTZjAA5AHlX+naOy+G+sRaJSFZCAlRSQHIRBiLIAexgdV4+FM7AAbGQ5IpcMsQLxCNi6rhxso1JodAZCajTGYUipXG0sRRTGRREysYRTLh0YTkVhnBobMh7FJ5KKxeKJZKpZLUMhabCsjYzLClBZXHVWKZEPp9GBXBgAPQG1Cw0GwiBZA1kcTWvEG1y4MhUQiomzEdhkN14sieoIai4gDW/EAAHS0AAJI1Ho5GwzH41HXil9BZoOGAArdNSuFBaLLhgDiEFhFjAcYT0fLFbqqOJvhUEX05oAViWIFpaXB642a1SsNB9BBAjAGSBURysLxBIQyB65ABfRQWLQqWEpVDkwwYUDBsBSJSIzr7wmNCAVVSjhZYA1NC+uA3pgCyjAoREIU/wBprpmgSnNo3YHFCGwMhsF4VgZzoZ0ADEZzYeC2FoQDiCQ04OUUD0jyUW59weM9mkNW8qnvJ8XzfD8vww4MghowFgVBFcIS0KEYXhRFBiwGk6VHKdTEHCweInQMBl5Md8GICguTZMYcVRcT8GtaSiVMZdV3XTcNT7Md2GReYmSwExFG5LB8SpRdlFhKQpFheIHCMEAdOZfBAMRHFrRIREAzIZzDNxYNrQJLEOJAcRjkGLErxCjVgu8lz5mJfBeCZed5yAA==; ncbi_sid=5CBC70B4255B939A_9B1DSID; WebEnv=1VKIcc%405CBC70B4255B939A_9B1DSID; pmc.article.report='
        }
        resp = requests.get(url, headers=headers)
        if resp.status_code == requests.codes.ok:
            try:
                link = re.search(f'<a href="(/pmc/articles/{cit.pmc}/pdf.*?)">PDF \(\d+K\)</a>', resp.text, re.S).group(1)
            except Exception as e:
                return
            else:
                fulltext = 'https://www.ncbi.nlm.nih.gov'+link
                cit.fulltext = fulltext

        return cit

    def start(self, email: str, taskid: int, reply, name: str = None):
        """
        开始异步AI查找
        :param email: 发送的email
        :param taskid: 任务id
        :param reply: 回复邮件的函数
        :param name: 暂未启用
        :return: None
        """
        result = self.startx()
        if result:
            self.task.data_replied = datetime.now()
            self.task.save()
            title = self.task.request
            short = result
            replyMsg = f'老师，您需要的《{title}》已找到，下载链接：http://api.jlss.vip/s/{short}'
            reply(email, replyMsg, taskid, name)
        else:
            self.task.status = 'waiting'
            self.task.data_received = None
            self.task.save()

    def startx(self):
        statistic = Statistic(create_time=datetime.now())
        statistic.category = 1
        statistic.task = self.task
        statistic.request = self.task.request
        statistic.save()
        self.log('SYS', '进入人工智能查询>>>')
        self.log('KP', f'探索任务:{self.task}')
        # 正则匹配doi>pmid>title
        self.log('PC', '进行正则检定')
        _re = ReLibs(self.task.title)
        self.EXP = _re.search()  # TODO:支持多条检索
        self.log('KP', f'检定成功，分析出exp={self.EXP}')
        if not self.EXP:
            self.log('KP', '检定失败，查询表达式为空，GG')
            self.log('SYS', '退出人工智能查询<<<')
            statistic.channel = 'PE'
            statistic.result = 'FA'
            return None
        key = self.EXP.split(':')[0]
        value = self.EXP.split(':')[1].replace('\"', '')

        # 保存正则结果
        statistic.re_lib = key
        statistic.retrieval_str = value

        # 获取题录信息
        self.log('PC', '去PubMed查询citation')
        self.CITATION = Cite(key, value)

        # 接口查询结果
        statistic.author = self.CITATION.author_list
        statistic.last_author = self.CITATION.last_author
        statistic.title = self.CITATION.title
        statistic.doi = self.CITATION.doi
        statistic.pmid = self.CITATION.pmid
        statistic.pmc = self.CITATION.pmc
        statistic.pii = self.CITATION.pii
        statistic.issn = self.CITATION.issn
        statistic.year = self.CITATION.year
        statistic.volume = self.CITATION.volume
        statistic.pages = self.CITATION.pages

        # 查询途径标识
        sources_map = {
            0: 'manual',
            1: 'pmc',
            2: 'jh',
            3: 'sci',
            4: 'sd',
        }
        # 遍历查询各个源
        cur_sources = 0
        SOURCES = [self.resource, self.play_pmc, self.jh, self.sci, self.sd]
        while (not self.CITATION.fulltext) and cur_sources < len(SOURCES):
            self.CITATION = SOURCES[cur_sources](self.CITATION)
            self.log('KP', f'CITATION更新：{self.CITATION.__dict__}')
            if self.CITATION.fulltext:
                # 进行任务与源的绑定，生成短域名
                statistic = self.handleTask(self.CITATION, statistic)
                # 绑定查询的途径标识
                statistic.resource_lib = sources_map.get(cur_sources)
                break
            cur_sources += 1
        else:
            self.log('PC', f'所有源查找完，结果为{self.CITATION.__dict__}')
        # 退出AI
        self.log('SYS', '退出人工智能查询<<<')
        if not self.RESULT:
            statistic.channel = 'PE'
            statistic.result = 'FA'
        statistic.finish_time = datetime.now()
        statistic.save()
        return self.RESULT

    def handleTask(self, cit: Cite, statistic):
        try:
            # 受理任务
            self.log('PC', '受理任务')
            self.log('SYS', '受理任务>>>')
            self.task.status = 'progress'
            self.task.data_received = datetime.now()
            self.task.receiver = User.objects.get(pk=1)
            self.task.save()
            self.log(
                'KP',
                f'{self.task.receiver.nickname}于{self.task.data_received}受理任务,任务状态变为：{self.task.status}'
            )

            # 如果在人工收集的资源中找到全文
            if self._Resource:
                resource = self._Resource
            else:
                # 如果在人工收集的资源中没有找到全文，则生成资源（无附件）
                self.log('PC', '生成资源')
                self.log('SYS', '生成资源中...')
                resource = Resource(restype=ResType.objects.get(pk=7), download=cit.fulltext, title=cit.title,
                                    uid=cit.doi, lang=cit.lang)
                resource.save()
            statistic.resource = resource
            statistic.result = 'SU'
            statistic.channel = 'AI'
            self.log('KP', f'生成了资源:{resource}')
            # 关联资源，任务成功
            self.log('PC', '关联资源')
            self.task.resource = resource
            self.task.status = 'success'
            self.task.data_replied = datetime.now()
            self.task.replier = User.objects.get(pk=1)
            self.task.save()
            self.log('KP', f'{self.task.replier.nickname}于{self.task.data_replied}关联了资源{self.task.resource}，'
                           f'任务状态更新为:{self.task.status}')
            self.log('KP', '自动查找成功，任务完成<<<')
            self.RESULT = resource.short
            return statistic

        except Exception as identifier:
            self.log('SYS', f'任务失败：{identifier}')
            self.task.status = 'waiting'
            self.task.save()
            self.RESULT = None
            self.log('KP', f'任务结束,自动查询失败,等待人工处理')
            return statistic

import logging
import re
from datetime import datetime
from Sentry.SD import SingleDownload
import requests

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
        self.statistic = statistic

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
        self.log('SYS', '开始在jh中查询...')
        so = Solr()
        # 查询DOI
        exp = f'doi:{cit.doi}'
        self.log('JH', f'1.在solr中查询doi,表达式={exp}...')
        result = so.search(exp)
        self.log('JH', f'1.solr查询结果={result}')
        # 查询PMID
        if not result:
            exp = f'pmid:{cit.pmid}'
            self.log('JH', f'2.在solr中查询pmid,表达式={exp}...')
            result = so.search(exp)
            self.log('JH', f'2.solr查询结果={result}')
        # 查询标题
        if not result:
            exp = f'title:"{cit.title}"'
            self.log('JH', f'3.在solr中查询title,表达式={exp}...')
            result = so.search(exp)
            self.log('JH', f'3.solr查询结果={result}')
        # 查询年卷期，功能待开发
        # TODO:冻结 这是坑。卷没有值，页没有索引，sup没统一
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
        """ 在sci中查找 """
        self.log('PC', '检定单点下载')
        if not (cit.doi or cit.pmid or cit.pmc):
            self.log('SD', '检定非法，单点下载只支持doi、pmcid、pmid')
            return cit
        sd = SingleDownload()
        if cit.doi:
            self.log('SD', f'1.查询doi:{cit.doi}')
            cit.fulltext = sd.download(cit.doi)
            self.log('SD', f'1.查询doi结果:{cit.fulltext}')
        if not cit.fulltext and cit.pmc:
            self.log('SD', f'2.查询pmc:{cit.pmc}')
            cit.fulltext = sd.download(cit.pmc)
            self.log('SD', f'2.查询pmc结果:{cit.fulltext}')
        if not cit.fulltext and cit.pmid:
            self.log('SD', f'3.查询pmid:{cit.pmid}')
            cit.fulltext = sd.download(cit.pmid)
            self.log('SD', f'3.查询pmid结果:{cit.fulltext}')
        self.log('SD', f'查找结果:{cit.__dict__}')
        return cit

    def resource(self, cit: Cite):
        result = ''
        if cit.doi:
            result = Resource.objects.filter(uid=cit.doi).order_by('-id')
        if (not result) and cit.pmid:
            result = Resource.objects.filter(uid=cit.doi).order_by('-id')

        if result:
            _Resource = result[0]
            status = False
            while not status:
                resp = requests.get(f'http://api.jlss.vip/s/{_Resource.short}')
                if resp.text.strip() == '对不起,全文已丢失!':
                    _Resource.uid = None
                    _Resource.save()
                    break
                if resp.status_code == 200:
                    self._Resource = _Resource
                    status = True
                    self.statistic.resource_lib = 'jh'
                    self.statistic.channel = 'AI'
                else:
                    break

    def start(self, email: str, taskid: int, reply, name: str = None):
        """ 开始异步AI查找 """
        result = self.startx()
        if result:
            self.statistic.result = 'SU'
            self.task.status = 'success'
            self.task.data_replied = datetime.now()
            self.task.save()
            title = json.loads(result)['title']
            short = json.loads(result)['short']
            replyMsg = f'老师，您需要的《{title}》已找到，下载链接：http://api.jlss.vip/s/{short}'
            reply(email, replyMsg, self.statistic, taskid, name)
        else:
            self.statistic.result = 'FA'
            self.statistic.channel = 'PE'
            self.task.status = 'waiting'
            self.task.data_received = None
            self.task.save()
            self.statistic.finish_time = datetime.now()
            self.statistic.save()

    def startx(self):
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
            self.statistic.channel = 'PE'
            return None
        key = self.EXP.split(':')[0]
        value = self.EXP.split(':')[1].replace('\"', '')

        # 保存正则结果
        self.statistic.re_lib = key
        self.statistic.retrieval_str = value

        # 获取题录信息
        self.log('PC', '去PubMed查询citation')
        self.CITATION = Cite(key, value)

        # 首先查找人工源
        self.resource(self.CITATION)
        if self._Resource:
            self.handleTask(self.CITATION)

        # 接口查询结果
        self.statistic.author = self.CITATION.author_list
        self.statistic.last_author = self.CITATION.last_author
        self.statistic.title = self.CITATION.title
        self.statistic.doi = self.CITATION.doi
        self.statistic.pmid = self.CITATION.pmid
        self.statistic.pmc = self.CITATION.pmc
        self.statistic.pii = self.CITATION.pii
        self.statistic.issn = self.CITATION.issn
        self.statistic.year = self.CITATION.year
        self.statistic.volume = self.CITATION.volume
        self.statistic.pages = self.CITATION.pages

        sources_map = {
            0: 'jh',
            1: 'sci',
            2: 'sd',
        }
        if self.RESULT:
            return self.RESULT

        # 遍历查询各个源
        cur_sources = 0
        SOURCES = [self.jh, self.sci, self.sd]
        while (not self.CITATION.fulltext) and cur_sources < len(SOURCES):
            self.CITATION = SOURCES[cur_sources](self.CITATION)
            self.log('KP', f'CITATION更新：{self.CITATION.__dict__}')
            if self.CITATION.fulltext:
                self.handleTask(self.CITATION)
                self.statistic.result = 'SU'
                self.statistic.channel = 'AI'
                self.statistic.resource_lib = sources_map.get(cur_sources)
                break
            cur_sources += 1
        else:
            self.log('PC', f'所有源查找完，结果为{self.CITATION.__dict__}')
        # 退出AI
        self.log('SYS', '退出人工智能查询<<<')
        return self.RESULT

    def handleTask(self, cit: Cite):
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
            self.statistic.resource = resource
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

        except Exception as identifier:
            self.log('SYS', f'任务失败：{identifier}')
            self.task.status = 'waiting'
            self.task.save()
            self.RESULT = None
            self.log('KP', f'任务结束,自动查询失败,等待人工处理')

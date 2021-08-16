'''
单点下载功能，由李祖民提供
POST:http://119.28.55.26:8555/DownPdf.asmx/GetPdf
URL:http://119.28.55.26:8555/Default.aspx
Username:jh
Password:Jh123!
'''

import requests
import hashlib
import xml.etree.cElementTree as ET
from api.models import Task


class SingleDownload:
    # 李祖明(李祖明) 06-21 11:01:44
    # http://61.128.134.70:8555/Login.aspx，明天开始切换到这个上面使用
    domain = 'http://61.128.134.70:8555'

    def token(self, key: str):
        '''
        获取key值的token\n
        eg. 4444应编译为'3F51782A7DAD620A38B8AF14FD191C8A'
        '''
        return hashlib.md5(f'J{key}h'.encode()).hexdigest().upper()

    def download(self, key: str):
        '''
        单点下载全文，响应时间可能会很长
        '''
        r = requests.post(f'{self.domain}/DownPdf.asmx/GetPdf', {
            'key': key,
            'token': self.token(key)
        })
        if r.status_code == requests.codes.ok:
            data = ET.fromstring(r.text).text
            if data == '无规则' or data == '无权限':
                return None
            return f'{self.domain}{data}'
        else:
            return None

    def task(self):
        '''
        按规则获取任务
        '''
        # TODO: 制定规则
        task = Task.objects.filter(status='waiting').first()
        return task

    def main(self):
        task = self.task()
        if task:
            pdf = self.download(task.title)
            if pdf:
                pass

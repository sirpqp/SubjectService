import pysolr
import json
import xml.etree.ElementTree as ET
import urllib.parse


"""
Author: XIAOYAO
Create TIME: ??
UPDATE TIME: 20210804 10:25
UPDATE BY: QUAN
1-中刊，2-外刊，3-学位，4-会议，5-图书
"""


SOURCE_TYPE_MAP = {
    '1': r'中刊全文\\',
    '2': r'外刊全文\\',
    '3': r'学位\\',
    '4': r'会议\\',
    '5': r'图书\\',
}


class Solr(pysolr.Solr):
    """ 继承pysolr的轻量solr代理 """
    SOLRURL = r'http://129.28.159.224:8180/solr/jhpdf/'
    # BASEINDEXFILE = r'E:\SolrIndex\index\dbindex\jhres_dat_{datfilename}_db.dat'
    BASEINDEXFILE = r'\\192.168.0.201\ai-index\dbindex\jhres_{datfilename}_db.dat'
    FULLTEXT = r'http://61.128.134.70:5555//QQSearch/downloadpdf_new.jsp?resid={resid}&pdfpath={pdfpath}'

    def __init__(self, url=SOLRURL):
        super().__init__(url)

    def search(self, q):
        try:
            result = super().search(q, results_cls=dict)
            # 命中且唯一
            if (result.hits == 1):
                for item in result:
                    
                    # 判断是否存在全文，如无 直接返回
                    pdfpath = item.get('pdfpath_other') or item.get('pdfpath')
                    if not pdfpath:
                        return None
                    
                    # 文件路径
                    DatFile = self.BASEINDEXFILE.format(
                        datfilename=item['datpos'].split(':')[0])
                    # 打开二进制源 读取xml字符串
                    try:
                        with open(DatFile, 'rb') as fos_dat:
                            fos_dat.seek(int(item['datpos'].split(':')[1]) + 8)
                            strlen = int.from_bytes(fos_dat.read(4),
                                                    byteorder='big')
                            xml_str = str(fos_dat.read(strlen),
                                          encoding='utf-8')
                    except Exception as ex:
                        print(ex)
                    # 从xml中读取必要字段
                    xml = ET.fromstring(
                        f'<?xml version="1.0"?><record>{xml_str}</record>')
                    res = item.get('res') or xml.findtext('res')

                    record = {
                        'doi':
                        xml.findtext('doi'),
                        'pmid':
                        xml.findtext('pmid'),
                        'wos':
                        xml.findtext('wos'),
                        'journal':
                        xml.findtext('name_c') if res == '1'
                        else xml.findtext('name_e'),
                        'title':
                        xml.findtext('title_c') if res == '1'
                        else xml.findtext('title_e'),
                        'lang':
                        'ZH' if res == '1' else 'F',
                        'res': res,
                        # 'year': xml.findtext('year'),
                        # 'issn': xml.findtext('issn'),
                        # 'volume': xml.findtext('volume'),
                        # 'issue': xml.findtext('issue'),
                        'download':
                        self.FULLTEXT.format(
                            resid=res + xml.findtext('resid'),
                            pdfpath=urllib.parse.quote(
                                # xml.findtext('pdfpath')
                                # [xml.findtext('pdfpath').index('中刊全文' if res == '1' else '外刊全文'):]
                                pdfpath
                            )
                        )
                    }
                    return record

            # 未命中
            elif (result.hits == 0):
                return None
            # 命中不只一条
            else:
                return None
                # _list = list()
                # for item in result:
                #     _list.append(
                #         self.BASEINDEXFILE.format(
                #             datfilename=item['datpos'].split(':')[0]))
                # return _list
        except Exception as identifier:
            return None


class Solr_CMJD(pysolr.Solr):
    """ 继承pysolr的轻量solr代理 """
    SOLRURL = r'http://129.28.159.224:8280/solr/main/'
    # BASEINDEXFILE = r'E:\zhongkan\SolrIndex_CMJD_20210301\dbindex\main_dat_{datfilename}_db.dat'
    BASEINDEXFILE = r'\\192.168.0.201\ai-index\dbindex\jhres_{datfilename}_db.dat'
    FULLTEXT = r'http://61.128.134.70:5555//QQSearch/downloadpdf.jsp?resid={resid}&pdfpath={pdfpath}'

    def __init__(self, url=SOLRURL):
        super().__init__(url)

    def search(self, q):
        try:
            result = super().search(q, results_cls=dict)
            # 命中且唯一
            if (result.hits == 1):
                for item in result:
                    # 文件路径
                    DatFile = self.BASEINDEXFILE.format(
                        datfilename=item['datpos'].split(':')[0])
                    # 打开二进制源 读取xml字符串
                    with open(DatFile, 'rb') as fos_dat:
                        fos_dat.seek(int(item['datpos'].split(':')[1]) + 8)
                        strlen = int.from_bytes(fos_dat.read(4),
                                                byteorder='big')
                        xml_str = str(fos_dat.read(strlen), encoding='utf-8')
                        print(xml_str)
                    # 从xml中读取必要字段
                    xml = ET.fromstring(
                        f'<?xml version="1.0"?><record>{xml_str}</record>')
                    record = {
                        'doi':
                        xml.findtext('doi'),
                        'pmid':
                        xml.findtext('pmid'),
                        'wos':
                        xml.findtext('wos'),
                        'journal':
                        xml.findtext('name_c') if xml.findtext('res') == '1'
                        else xml.findtext('name_e'),
                        'title':
                        xml.findtext('title_c') if xml.findtext('res') == '1'
                        else xml.findtext('title_e'),
                        'lang':
                        'ZH' if xml.findtext('res') == '1' else 'F',
                        'res':
                        xml.findtext('res'),
                        # 'year': xml.findtext('year'),
                        # 'issn': xml.findtext('issn'),
                        # 'volume': xml.findtext('volume'),
                        # 'issue': xml.findtext('issue'),
                        'download':
                        self.FULLTEXT.format(
                            resid=xml.findtext('resid'),
                            pdfpath=urllib.parse.quote(
                                r'\\外刊全文\\' + xml.findtext('pdfpath')[22:]))
                    }
                    return record

            # 未命中
            elif (result.hits == 0):
                return None
            # 命中不只一条
            else:
                return None
                # _list = list()
                # for item in result:
                #     _list.append(
                #         self.BASEINDEXFILE.format(
                #             datfilename=item['datpos'].split(':')[0]))
                # return _list
        except Exception as identifier:
            print(identifier)
            return None

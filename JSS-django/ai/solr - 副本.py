import pysolr
import json
import xml.etree.ElementTree as ET
import urllib.parse


class Solr(pysolr.Solr):
    """ 继承pysolr的轻量solr代理 """
    SOLRURL = r'http://129.28.159.224:8180/solr/jhpdf/'
    BASEINDEXFILE = r'E:\SolrIndex\index\dbindex\jhpdf_dat_{datfilename}_db.dat'
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
                    try:
                        with open(DatFile, 'rb') as fos_dat:
                            fos_dat.seek(int(item['datpos'].split(':')[1]) + 8)
                            strlen = int.from_bytes(fos_dat.read(4),
                                                    byteorder='big')
                            xml_str = str(fos_dat.read(strlen),
                                          encoding='utf-8')
                            print(xml_str)
                    except Exception as ex:
                        print(ex)
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
                            resid=xml.findtext('res') + xml.findtext('resid'),
                            # pdfpath=urllib.parse.quote(
                            #     ('\\中刊全文\\' if xml.findtext('res') ==
                            #      '1' else '\\外刊全文\\') +
                            #     xml.findtext('pdfpath')[22:]))
                            pdfpath=urllib.parse.quote(
                                xml.findtext('pdfpath')
                                [xml.findtext('pdfpath').
                                 index('中刊全文' if xml.findtext('res') ==
                                       '1' else '外刊全文'):]))
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
    BASEINDEXFILE = r'E:\zhongkan\SolrIndex_CMJD_20210301\dbindex\main_dat_{datfilename}_db.dat'
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

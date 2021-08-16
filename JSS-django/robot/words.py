import string
# import zhon.hanzi
import re
import unicodedata

words = {
    '公告': ['@所有人'],
    '特需': ['补充材料', '检索', '相关文献', '的标准', '封面', '目录', '有关', '关键词'],
    '需求': [
        '文献', '文章', '求助', '求', '找下', '找一下', '麻烦', '麻烦了', '请', '请您', '一篇', '这篇',
        '这几篇', '这本', '这几本', '好的', '标题', '帮忙', '下载', 'DOI', 'ISBN', 'PMID'
    ],
    '答复': ['收到', '好的'],
    '客套': ['谢谢', '老师', '你好', '您好', '麻烦', '麻烦了', '多谢'],
}


def tag(target: str):
    ''' 标引需求字符串 '''
    # 中->英符号转换;全角->半角
    target = unicodedata.normalize('NFKC', target)
    # 去@xxx
    target = re.sub('@\S+[  ]', '', target)
    # 转换大写
    target = target.upper()

    result = {'答复': 0, '客套': 0, '特需': 0, '公告': 0, '需求': 0, 'length': 0}
    count_str = target
    for classtype in words:
        for key in words[classtype]:
            if key in target:
                count_str = count_str.replace(key, '')
                result[classtype] += 1
    # 去中英文符号
    for p in string.punctuation:
        count_str = count_str.replace(p, '')
    # for zp in zhon.hanzi.punctuation:
    #     count_str = count_str.replace(zp, '')
    result['length'] = len(count_str)
    return result

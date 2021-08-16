from django.test import TestCase, SimpleTestCase
from ai.solr import Solr, Solr_CMJD
from ai.detroit import ReLibs, Cite, Detroit
from api.models import Task

# class CiteTests(SimpleTestCase):
#     def test_pmid(self):
#         c = Cite()
#         print(c.get_cite_by_pmid('27741350'))


class SolrTests(SimpleTestCase):
    def test_ob_result(self):
        query = 'title_c:"GE ProSpeed AI型螺旋CT故障检修1例"'

        so = Solr_CMJD()
        print(so.search(query))


#     def test_ob_result(self):
#         query = 'title:"人细小病毒B19分子生物学研究进展"'

#         so = Solr_CMJD()
#         print(so.search(query))

# class DetroitTest(TestCase):
# def test_Cite(self):
#     c = Cite('pmid', '25773203')
#     print(c)

# def test_all(self):
#     # task = Task.objects.get(pk=63)
#     task = Task(title='PMID: 25143301')
#     print('将测试：', task)
#     de = Detroit(task)
#     print(de.startx())

# def test_report(self):
#     with open('ZH7.txt', 'r', encoding='gbk', errors='ignore') as r:
#         uc = r.readlines()
#     # uc = [
#     #     'doi:10.1001/archopht.1991.01080080021010',
#     #     'https://journals.sagepub.com/doi/10.5301/ejo.5000966',
#     #     '3. The handbook of Asian Englishes, 2020.',
#     #     '"工作坊"模式在风景园林设计与建造课程中的革新及应用'
#     # ]
#     with open('report.txt', 'a') as f:
#         for item in uc:
#             result = Detroit(None).report(item)
#             for value in result.values():
#                 f.write(str(value).replace('\n', '') + '\t')
#             f.write('\n')
# def test_log(self):
#     Detroit.log('SYS1', 'test log')

#     def test_ReLibs_uc(self):
#         uc = [
#             [
#                 'doi:10.1001/archopht.1991.01080080021010',
#                 'doi:10.1001/archopht.1991.01080080021010'
#             ],
#             ['DOI：10.1016/j.ajo.2020.04.019', 'doi:10.1016/j.ajo.2020.04.019'],
#             [
#                 'https://journals.sagepub.com/doi/10.5301/ejo.5000966',
#                 'doi:10.5301/ejo.5000966'
#             ],
#             [
#                 'https://onlinelibrary.wiley.com/doi/10.1002/anie.202010281',
#                 'doi:10.1002/anie.202010281'
#             ],
#             [
#                 'Oxygen Pathology and Oxygen-Functional Materials for Therapeutics. DOI: https://doi.org/10.1016/j.matt.2020.02.013',
#                 'doi:10.1016/j.matt.2020.02.013'
#             ],
#             [
#                 '5: Yamamoto T, Hasuike A, Koshi R, Ozawa Y, Ozaki M, Kubota T, Sato S.Influences of mechanical barrier permeability on guided bone augmentation in the rat calvarium. J Oral Sci. 2018 Sep 23;60(3):453-459. doi:10.2334/josnusd.17-0362. Epub 2018 Aug 12. PMID: 30101821.',
#                 'doi:10.2334/josnusd.17-0362'
#             ], ['32544574', 'pmid:32544574'],
#             [
#                 '3. The handbook of Asian Englishes, 2020.',
#                 'title:3. The handbook of Asian Englishes, 2020.'
#             ],
#             [
#                 '《一天搞懂区块链》ISBN: 9787556124336',
#                 'title:《一天搞懂区块链》ISBN: 9787556124336'
#             ],
#             ['求助:DOI: 10.1126/science.aah4439', 'doi:10.1126/science.aah4439'],
#             ['ISBN9787516182758', 'title:ISBN9787516182758']
#         ]
#         for text in uc:
#             r = ReLibs(text[0])
#             self.assertEqual(r.search(), text[1])

#     def test_ReLibs_db(self):
#         tasks = Task.objects.all()[:100]
#         for task in tasks:
#             r = ReLibs(task.title)
#             print(task.title)
#             print(r.search())
#             print('-' * 50)
